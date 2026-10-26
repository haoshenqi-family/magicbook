"""Unit tests for the user-export proxy endpoints (R230).

Covers:
  1. All three endpoints require login.
  2. create: password length is validated locally (400 without touching
     moon-well); valid passwords are forwarded as {password} only.
  3. tasks: GET passthrough without payload.
  4. download: 200 streams ZIP bytes with attachment headers; upstream
     errors pass through with their status.

Why mock `_moonwell_proxy` (via the moon-well client): the proxy contract is
"which path/payload/method goes upstream and what comes back" (same approach
as test_learning_proxy.py).
"""
import json
from pathlib import Path

import pytest
from cps.moonwell.client import client as _mb_client

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def moonwell_configured(monkeypatch):
    from cps import constants
    monkeypatch.setattr(constants, "MOON_WELL_READING_URL",
                        "https://moon-well.example.com/")
    return constants


def _envelope(result):
    return json.dumps({"success": True, "code": 200, "message": "", "result": result})


class RecordingProxy:
    """记录转发出去的目标，并按 path 返回预设响应。

    replies 值支持 (body, status) 或 (body, status, headers)——下载透传测试用第三元。
    """

    def __init__(self, replies):
        self.replies = replies
        self.calls = []

    def __call__(self, path, payload, timeout, label, binary=False, method="POST",
                 system_identity=None, identity_headers=None, bearer_token=None):
        self.calls.append({"path": path, "payload": payload, "method": method,
                           "timeout": timeout, "binary": binary})
        reply = self.replies[path]
        body, status = reply[0], reply[1]
        headers = reply[2] if len(reply) > 2 else {"Content-Type": "application/json"}
        return body, status, headers

    def call_for(self, path):
        return next(call for call in self.calls if call["path"] == path)


TASK = {"id": 7, "status": "SUCCESS", "exportType": "LEARNING_DATA",
        "fileSize": 2048, "downloadable": True}


# ---------- 1. 鉴权 ----------

def test_endpoints_require_login(app, moonwell_configured):
    client = app.test_client()
    assert client.post("/ajax/user-export/create", json={}).status_code == 302
    assert client.get("/ajax/user-export/tasks").status_code == 302
    assert client.get("/ajax/user-export/tasks/7/download").status_code == 302


# ---------- 2. create 参数域 ----------

def test_create_rejects_short_password_locally(admin_client, moonwell_configured,
                                               monkeypatch):
    proxy = RecordingProxy({})
    monkeypatch.setattr(_mb_client, "proxy", proxy)
    response = admin_client.post("/ajax/user-export/create",
                                 json={"password": "abc"})
    assert response.status_code == 400
    assert proxy.calls == [], "短密码必须本地拒绝，不得触达 moon-well"


def test_create_rejects_non_string_password_locally(admin_client, moonwell_configured,
                                                    monkeypatch):
    """R230 修订后：缺密码=不加密导出（合法）；只有非字符串类型仍本地 400。"""
    proxy = RecordingProxy({})
    monkeypatch.setattr(_mb_client, "proxy", proxy)
    assert admin_client.post("/ajax/user-export/create", json={"password": 123456}).status_code == 400
    assert admin_client.post("/ajax/user-export/create", json={"password": ["a"]}).status_code == 400
    assert proxy.calls == []


def test_create_forwards_password_only(admin_client, moonwell_configured, monkeypatch):
    proxy = RecordingProxy({"/export/learning-data": (_envelope(
        {"id": 7, "status": "PENDING"}), 200)})
    monkeypatch.setattr(_mb_client, "proxy", proxy)
    response = admin_client.post("/ajax/user-export/create",
                                 json={"password": "long-enough"})
    assert response.status_code == 200
    call = proxy.call_for("/export/learning-data")
    assert call["method"] == "POST"
    assert call["payload"] == {"password": "long-enough"}


def test_create_without_password_forwards_empty_payload(admin_client, moonwell_configured,
                                                        monkeypatch):
    """R230 修订：密码可选——空/缺省时转发空 payload（不加密导出），不本地拒绝。"""
    proxy = RecordingProxy({"/export/learning-data": (_envelope(
        {"id": 8, "status": "PENDING", "encrypted": False}), 200)})
    monkeypatch.setattr(_mb_client, "proxy", proxy)
    response = admin_client.post("/ajax/user-export/create", json={"password": ""})
    assert response.status_code == 200
    assert proxy.call_for("/export/learning-data")["payload"] == {}


# ---------- 3. tasks 透传 ----------

def test_tasks_forwards_get_without_payload(admin_client, moonwell_configured,
                                            monkeypatch):
    proxy = RecordingProxy({"/export/learning-data/tasks": (_envelope([TASK]), 200)})
    monkeypatch.setattr(_mb_client, "proxy", proxy)
    response = admin_client.get("/ajax/user-export/tasks")
    assert response.status_code == 200
    call = proxy.call_for("/export/learning-data/tasks")
    assert call["method"] == "GET"
    assert call["payload"] is None


# ---------- 4. download ----------

def test_download_streams_zip_with_attachment_header(admin_client, moonwell_configured,
                                                      monkeypatch):
    upstream_cd = 'attachment; filename="my-learning-data-20261026-2119-7.zip"'
    proxy = RecordingProxy({"/export/learning-data/tasks/7/download": (
        b"PK-zip-bytes", 200, {"Content-Type": "application/zip",
                               "Content-Disposition": upstream_cd})})
    monkeypatch.setattr(_mb_client, "proxy", proxy)
    response = admin_client.get("/ajax/user-export/tasks/7/download")
    assert response.status_code == 200
    assert response.data == b"PK-zip-bytes"
    # 2026-10-26 用户修订：文件名透传上游（moon-well 生成带任务创建时间的文件名）
    assert response.headers.get("Content-Disposition") == upstream_cd
    call = proxy.call_for("/export/learning-data/tasks/7/download")
    assert call["binary"] is True, "下载必须按字节透传，文本解码会损坏 ZIP"


def test_download_falls_back_to_default_disposition_without_upstream(admin_client,
                                                                      moonwell_configured,
                                                                      monkeypatch):
    proxy = RecordingProxy({"/export/learning-data/tasks/9/download": (
        b"PK-zip-bytes", 200, {"Content-Type": "application/zip"})})
    monkeypatch.setattr(_mb_client, "proxy", proxy)
    response = admin_client.get("/ajax/user-export/tasks/9/download")
    assert response.status_code == 200
    assert response.headers.get("Content-Disposition") == \
        'attachment; filename="my-learning-data-9.zip"'


def test_download_passes_through_upstream_error(admin_client, moonwell_configured,
                                                monkeypatch):
    proxy = RecordingProxy({"/export/learning-data/tasks/8/download": (
        json.dumps({"success": False, "code": 50604, "message": "已过期"}).encode(), 500)})
    monkeypatch.setattr(_mb_client, "proxy", proxy)
    response = admin_client.get("/ajax/user-export/tasks/8/download")
    assert response.status_code == 500
    assert b"50604" in response.data, "上游 Result 错误应原样透传给前端展示"
