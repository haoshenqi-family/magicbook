"""Unit tests for the credit consume detail proxies (R64).

Covers:
  1. POST /ajax/credit/consume-page forwards payload to moon-well /credit/consume/page.
  2. POST /ajax/credit/consume-summary forwards payload to moon-well /credit/consume/summary.
  3. Credits page renders the consumption detail section.
  4. Unauthenticated access is rejected.
"""
import json
import pathlib

import pytest

import cps


@pytest.fixture
def moonwell_configured(monkeypatch):
    from cps import constants
    monkeypatch.setattr(constants, "MOON_WELL_READING_URL",
                        "https://moon-well.example.com/")
    return constants


def test_requires_login(app, moonwell_configured):
    """Anonymous requests must be redirected to the login page."""
    client = app.test_client()
    assert client.post("/ajax/credit/consume-page", json={}).status_code == 302
    assert client.post("/ajax/credit/consume-summary", json={}).status_code == 302


def test_consume_page_forwards_payload(admin_client, moonwell_configured, monkeypatch):
    import cps.web as w

    captured = {}

    def fake_proxy(path, payload, timeout, label, binary=False, method="POST", system_identity=False, bearer_token=None):
        captured["path"] = path
        captured["payload"] = payload
        return (json.dumps({"success": True, "result": {"records": [], "total": 0}}), 200,
                {"Content-Type": "application/json"})

    monkeypatch.setattr(w._moonwell_client, "proxy", fake_proxy)

    payload = {"pageNo": 2, "pageSize": 10, "caller": "book-reader",
               "model": "deepseek-v4-flash", "startDate": "2026-09-01", "endDate": "2026-09-20"}
    rv = admin_client.post("/ajax/credit/consume-page", json=payload)
    assert rv.status_code == 200
    assert captured["path"] == "/credit/consume/page"
    assert captured["payload"] == payload


def test_consume_summary_forwards_payload(admin_client, moonwell_configured, monkeypatch):
    import cps.web as w

    captured = {}

    def fake_proxy(path, payload, timeout, label, binary=False, method="POST", system_identity=False, bearer_token=None):
        captured["path"] = path
        captured["payload"] = payload
        return (json.dumps({"success": True, "result": {"totalAmount": 0}}), 200,
                {"Content-Type": "application/json"})

    monkeypatch.setattr(w._moonwell_client, "proxy", fake_proxy)

    rv = admin_client.post("/ajax/credit/consume-summary", json={"caller": "book-reader"})
    assert rv.status_code == 200
    assert captured["path"] == "/credit/consume/summary"
    assert captured["payload"] == {"caller": "book-reader"}


def test_credits_page_renders_consume_section(admin_client, moonwell_configured):
    rv = admin_client.get("/credits")
    assert rv.status_code == 200
    html = rv.data.decode("utf-8")
    # 模板包含明细区结构（R49：类型 Tab + 原因列）；AJAX 端点在外部 credits.js 中引用
    assert "credit-consume-summary" in html
    assert "credit-consume-rows" in html
    assert "credit-consume-pager" in html
    assert "credit-type-btn" in html
    assert "{{_('Reason')}}" in html or "Reason" in html
    js = pathlib.Path(cps.__file__).parent / "static" / "js" / "credits.js"
    assert "/ajax/credit/consume-page" in js.read_text(encoding="utf-8")
    assert "/ajax/credit/consume-summary" in js.read_text(encoding="utf-8")


def test_admin_adjust_requires_login(app, moonwell_configured):
    """Anonymous requests must be redirected to the login page."""
    client = app.test_client()
    assert client.post("/ajax/credit/admin-adjust", json={}).status_code == 302


def test_admin_adjust_forwards_payload(admin_client, moonwell_configured, monkeypatch):
    """Admin client's adjust payload is forwarded to moon-well /credit/admin/adjust."""
    import cps.web as w

    captured = {}

    def fake_proxy(path, payload, timeout, label, binary=False, method="POST", system_identity=False, bearer_token=None):
        captured["path"] = path
        captured["payload"] = payload
        return (json.dumps({"success": True,
                            "result": {"userId": 1, "balance": 94}}), 200,
                {"Content-Type": "application/json"})

    monkeypatch.setattr(w._moonwell_client, "proxy", fake_proxy)

    payload = {"userId": 1, "amount": 2215, "reason": "R53 计费口径冲正"}
    rv = admin_client.post("/ajax/credit/admin-adjust", json=payload)
    assert rv.status_code == 200
    assert captured["path"] == "/credit/admin/adjust"
    assert captured["payload"] == payload


def test_admin_users_requires_login(app, moonwell_configured):
    """Anonymous requests must be redirected to the login page."""
    client = app.test_client()
    assert client.post("/ajax/credit/admin-users", json={}).status_code == 302


def test_admin_users_forwards_and_gates(admin_client, moonwell_configured, monkeypatch):
    """admin-users 转发 /credit/admin/users；非管理员 403（moon-well 白名单再校验）。"""
    import cps.web as w

    captured = {}

    def fake_proxy(path, payload, timeout, label, binary=False, method="POST", system_identity=False, bearer_token=None):
        captured["path"] = path
        captured["payload"] = payload
        return (json.dumps({"success": True,
                            "result": [{"userId": 1, "username": "admin", "nickname": None, "email": None}]}),
                200, {"Content-Type": "application/json"})

    monkeypatch.setattr(w._moonwell_client, "proxy", fake_proxy)

    rv = admin_client.post("/ajax/credit/admin-users", json={})
    assert rv.status_code == 200
    assert captured["path"] == "/credit/admin/users"
    assert captured["payload"] == {}

    body = json.loads(rv.data.decode("utf-8"))
    assert body["success"] is True
    assert body["result"][0]["userId"] == 1


def test_credits_page_renders_admin_user_dropdown(admin_client, moonwell_configured):
    """调整表单的目标用户必须是下拉（同源防打错人），不再是手填数字输入。"""
    rv = admin_client.get("/credits")
    assert rv.status_code == 200
    html = rv.data.decode("utf-8")
    assert '<select id="credit-admin-user"' in html
    assert 'type="number" id="credit-admin-user"' not in html
    js = pathlib.Path(cps.__file__).parent / "static" / "js" / "credits.js"
    js_text = js.read_text(encoding="utf-8")
    assert "/ajax/credit/admin-users" in js_text
    # 划线原价文案不再带「原到账」前缀（验收微调：baseTitle 服务端文案直接展示）
    assert "'原到账 '" not in js_text
    assert "pkg-base" in js_text


def test_credits_page_renders_admin_panel_for_admin(admin_client, moonwell_configured):
    rv = admin_client.get("/credits")
    assert rv.status_code == 200
    assert "credit-admin-panel" in rv.data.decode("utf-8")
    js = pathlib.Path(cps.__file__).parent / "static" / "js" / "credits.js"
    assert "/ajax/credit/admin-adjust" in js.read_text(encoding="utf-8")
