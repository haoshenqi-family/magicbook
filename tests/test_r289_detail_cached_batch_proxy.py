"""R289 滚动复习详情批量代理（/ajax/vocabulary/detail-cached-batch）守卫。

对端 moon-well R248 只读缓存批量端点。本代理的全部契约：
  1. 登录门槛；
  2. 词表归一（trim/弯撇号/小写/去重/词形白名单）后转发，非法词丢弃而非报错；
  3. 空/全非法词表在本地短路返回空 result，绝不打上游；
  4. 上游不可达返回 (jsonify, 503) 二元组必须原样透传（解包 = 500 白页，前端降级分支进不去）。

Why mock `_moonwell_client.proxy` 而不是 HTTP 层：代理契约是「哪个 path/what payload/
什么 method 出网、回来什么原样透传」；缓存命中语义由 moon-well R248 的单测兜。
"""
import json

import pytest


@pytest.fixture
def moonwell_configured(monkeypatch):
    from cps import constants
    monkeypatch.setattr(constants, "MOON_WELL_READING_URL",
                        "https://moon-well.example.com/")
    return constants


def _envelope(result):
    return json.dumps({"success": True, "code": 200, "message": "", "result": result})


def _json_headers():
    return {"Content-Type": "application/json"}


class RecordingProxy:
    def __init__(self, replies):
        self.replies = replies
        self.calls = []

    def __call__(self, path, payload, timeout, label, binary=False, method="POST",
                 system_identity=None, identity_headers=None, bearer_token=None):
        self.calls.append({"path": path, "payload": payload, "method": method,
                           "timeout": timeout})
        body, status = self.replies[path]
        return body, status, _json_headers()

    def call_for(self, path):
        return next(call for call in self.calls if call["path"] == path)


DETAILS = {"run": {"word": "run", "lemma": "run", "isVariant": False,
                   "meaning": [{"pos": "动词", "sense": "跑，奔跑"}],
                   "etymology": "源自古英语 rinnan。"}}


def test_endpoint_requires_login(app, moonwell_configured):
    client = app.test_client()
    assert client.post("/ajax/vocabulary/detail-cached-batch",
                       json={"words": ["run"]}).status_code == 302


def test_forwards_normalized_words(admin_client, moonwell_configured, monkeypatch):
    import cps.web as w

    proxy = RecordingProxy({
        "/vocabulary/detail/cached-batch": (_envelope(DETAILS), 200),
    })
    monkeypatch.setattr(w._moonwell_client, "proxy", proxy)

    response = admin_client.post("/ajax/vocabulary/detail-cached-batch",
                                 json={"words": [" Run ", "RUN", "run", "r\u2019un"]})
    assert response.status_code == 200
    assert response.get_json()["result"]["run"]["lemma"] == "run"

    call = proxy.call_for("/vocabulary/detail/cached-batch")
    assert call["method"] == "POST"
    assert call["timeout"] == 10
    # 归一 + 去重：空白/大小写折叠；弯撇号转直撇号后 r'un 变成合法词形保留
    assert call["payload"] == {"words": ["run", "r'un"]}


def test_invalid_words_are_dropped_not_fatal(admin_client, moonwell_configured,
                                             monkeypatch):
    """个别脏词不值得让整批失败：轮播是容错消费方，非法词静默丢弃。"""
    import cps.web as w

    proxy = RecordingProxy({
        "/vocabulary/detail/cached-batch": (_envelope({}), 200),
    })
    monkeypatch.setattr(w._moonwell_client, "proxy", proxy)

    response = admin_client.post("/ajax/vocabulary/detail-cached-batch",
                                 json={"words": ["ok-word", "bad word!", 42, None, "-x"]})
    assert response.status_code == 200
    call = proxy.call_for("/vocabulary/detail/cached-batch")
    assert call["payload"] == {"words": ["ok-word"]}


def test_word_cap_matches_upstream(admin_client, moonwell_configured, monkeypatch):
    """单次上限 50 与 moon-well WordDetailService.CACHE_BATCH_CAP 同口径，超出截断。"""
    import cps.web as w

    proxy = RecordingProxy({
        "/vocabulary/detail/cached-batch": (_envelope({}), 200),
    })
    monkeypatch.setattr(w._moonwell_client, "proxy", proxy)

    # 纯字母词（词形白名单只认字母，w00 这类带数字的会被拦）；长度 2..61 全部 ≤64
    words = ["wa" + "a" * i for i in range(60)]
    admin_client.post("/ajax/vocabulary/detail-cached-batch", json={"words": words})
    call = proxy.call_for("/vocabulary/detail/cached-batch")
    assert len(call["payload"]["words"]) == 50
    assert call["payload"]["words"][0] == "wa"
    assert call["payload"]["words"][-1] == "wa" + "a" * 49


@pytest.mark.parametrize("payload", [
    {"words": "run"},          # 字符串不是列表
    {"words": 42},
    {"words": None},           # 缺 words：与显式非法同判，words 必须是列表
])
def test_bad_payloads_are_rejected_locally(admin_client, moonwell_configured,
                                           monkeypatch, payload):
    import cps.web as w

    def exploding_proxy(*args, **kwargs):
        raise AssertionError("upstream must not be called")

    monkeypatch.setattr(w._moonwell_client, "proxy", exploding_proxy)
    response = admin_client.post("/ajax/vocabulary/detail-cached-batch", json=payload)
    assert response.status_code == 400


@pytest.mark.parametrize("words", [
    [],             # 空表：本地短路，不打上游
    ["   ", "!!"],  # 全非法：同样短路
])
def test_empty_word_lists_short_circuit(admin_client, moonwell_configured,
                                        monkeypatch, words):
    """空列表/全非法词在本地短路返回空 result，绝不打上游。"""
    import cps.web as w

    def exploding_proxy(*args, **kwargs):
        raise AssertionError("upstream must not be called")

    monkeypatch.setattr(w._moonwell_client, "proxy", exploding_proxy)
    response = admin_client.post("/ajax/vocabulary/detail-cached-batch",
                                 json={"words": words})
    assert response.status_code == 200
    assert response.get_json() == {"success": True, "result": {}}


def test_unreachable_upstream_returns_503_json_not_500(admin_client,
                                                       moonwell_configured,
                                                       monkeypatch):
    """_moonwell_proxy 失败分支是 (jsonify, 503) 二元组，必须原样透传；
    路由若按三元组解包会 ValueError → 500，前端连「回退简卡」分支都进不去。"""
    import cps.web as w
    from flask import jsonify

    def failing_proxy(path, payload, timeout, label, binary=False, method="POST",
                      **kwargs):
        return jsonify({"success": False, "message": label + " service unavailable"}), 503

    monkeypatch.setattr(w._moonwell_client, "proxy", failing_proxy)
    response = admin_client.post("/ajax/vocabulary/detail-cached-batch",
                                 json={"words": ["run"]})
    assert response.status_code == 503
    assert response.get_json()["success"] is False
