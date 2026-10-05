"""Unit tests for the vocabulary-size-test proxy endpoints (R116 / US4).

Covers:
  1. All four endpoints require login.
  2. start/answer/finish forward to the *flat* moon-well paths; `seq` is not dropped.
  3. Parameter-domain validation returns 400 from the proxy without hitting moon-well.
  4. moon-well business errors (HTTP 500 + Result.code) pass through byte-for-byte.
  5. First screen stays a single upstream call (history is loaded by vocab-test.js),
     and a settings fetch failure never takes the test card down with it.

Why mock `_moonwell_proxy` instead of the HTTP layer: the proxy's whole contract is
"which path/payload/method goes upstream and what comes back"; the network and
moon-well's own semantics are covered by moon-well's US3 tests.
"""
import json

import pytest


@pytest.fixture
def moonwell_configured(monkeypatch):
    from cps import constants
    monkeypatch.setattr(constants, "MOON_WELL_READING_URL",
                        "https://moon-well.example.com/")
    return constants


SETTINGS = {"hardLevel": 3, "hardLevelName": "CET4", "usingDefault": False,
            "options": [{"code": i, "name": "L%d" % i} for i in range(10)]}

REPORT = {"sessionId": 42, "status": 1, "startedAt": "2026-10-05 01:10:00",
          "finishedAt": "2026-10-05 01:13:40", "questionCount": 24, "knownCount": 15,
          "estimatedSize": 8600, "ciLow": 7200, "ciHigh": 10000, "capped": False,
          "finishReason": "CONVERGED", "addUnknown": True,
          "bandResults": [{"band": 3, "questions": 6, "known": 4, "rate": 0.6667,
                           "contribution": 500}],
          "addedToNotebook": 3}


def _envelope(result):
    return json.dumps({"success": True, "code": 200, "message": "", "result": result})


def _json_headers():
    return {"Content-Type": "application/json"}


class RecordingProxy:
    """记录转发出去的目标，并按 path 返回预设响应。"""

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


def _settings_reply():
    return _envelope(SETTINGS), 200


# ---------- 1. 鉴权 ----------

def test_endpoints_require_login(app, moonwell_configured):
    client = app.test_client()
    assert client.post("/ajax/vocab-test/start").status_code == 302
    assert client.post("/ajax/vocab-test/answer",
                       json={"sessionId": 1, "seq": 1, "answer": 1}).status_code == 302
    assert client.post("/ajax/vocab-test/finish",
                       json={"sessionId": 1,
                             "addUnknownToNotebook": True}).status_code == 302
    assert client.get("/ajax/vocab-test/history").status_code == 302


# ---------- 2. 转发目标 ----------

def test_start_forwards_empty_body_to_flat_path(admin_client, moonwell_configured,
                                                 monkeypatch):
    import cps.web as w

    proxy = RecordingProxy({
        "/vocabulary/test/start": (_envelope(
            {"sessionId": 42, "question": {"word": "example", "sentence": "An example.",
                                           "seq": 1, "band": 3},
             "progress": {"answered": 0, "known": 0, "band": 3}}), 200),
    })
    monkeypatch.setattr(w, "_moonwell_proxy", proxy)

    response = admin_client.post("/ajax/vocab-test/start")
    assert response.status_code == 200
    assert response.get_json()["result"]["question"]["word"] == "example"

    call = proxy.call_for("/vocabulary/test/start")
    assert call["method"] == "POST" and call["payload"] == {}
    assert call["timeout"] == 10


def test_answer_forwards_session_seq_and_value(admin_client, moonwell_configured,
                                                monkeypatch):
    """seq 是后端的幂等锚点：代理层丢掉它，断网重试就会变成串序污染。"""
    import cps.web as w

    proxy = RecordingProxy({
        "/vocabulary/test/answer": (_envelope(
            {"question": {"word": "next", "sentence": "The next one.", "seq": 2,
                          "band": 3},
             "finished": False, "progress": {"answered": 1, "known": 1, "band": 3},
             "estimation": None}), 200),
    })
    monkeypatch.setattr(w, "_moonwell_proxy", proxy)

    response = admin_client.post("/ajax/vocab-test/answer",
                                 json={"sessionId": 42, "seq": 1, "answer": 0})
    assert response.status_code == 200
    assert response.get_json()["result"]["question"]["seq"] == 2

    call = proxy.call_for("/vocabulary/test/answer")
    assert call["payload"] == {"sessionId": 42, "seq": 1, "answer": 0}
    assert call["timeout"] == 5


def test_finish_forwards_switch(admin_client, moonwell_configured, monkeypatch):
    import cps.web as w

    proxy = RecordingProxy({"/vocabulary/test/finish": (_envelope(REPORT), 200)})
    monkeypatch.setattr(w, "_moonwell_proxy", proxy)

    response = admin_client.post("/ajax/vocab-test/finish",
                                 json={"sessionId": 42, "addUnknownToNotebook": True})
    assert response.status_code == 200
    assert response.get_json()["result"]["addedToNotebook"] == 3

    call = proxy.call_for("/vocabulary/test/finish")
    assert call["payload"] == {"sessionId": 42, "addUnknownToNotebook": True}


def test_history_uses_get_without_payload(admin_client, moonwell_configured, monkeypatch):
    import cps.web as w

    proxy = RecordingProxy({"/vocabulary/test/history": (_envelope([REPORT]), 200)})
    monkeypatch.setattr(w, "_moonwell_proxy", proxy)

    response = admin_client.get("/ajax/vocab-test/history")
    assert response.status_code == 200
    assert response.get_json()["result"][0]["estimatedSize"] == 8600

    call = proxy.call_for("/vocabulary/test/history")
    assert call["method"] == "GET" and call["payload"] is None


# ---------- 3. 参数域校验（不打到上游） ----------

@pytest.mark.parametrize("payload", [
    {},
    {"sessionId": 42, "answer": 1},                      # 缺 seq
    {"sessionId": 0, "seq": 1, "answer": 1},             # 非正整数
    {"sessionId": True, "seq": 1, "answer": 1},          # bool 是 int 子类，不能当成 id
    {"sessionId": "42", "seq": 1, "answer": 1},          # 字符串 id
    {"sessionId": 42, "seq": 1, "answer": 2},            # 业务域
    {"sessionId": 42, "seq": 1, "answer": True},         # bool 不是 0/1
])
def test_bad_answer_payloads_are_rejected_locally(admin_client, moonwell_configured,
                                                  monkeypatch, payload):
    import cps.web as w

    def exploding_proxy(*args, **kwargs):  # 校验必须在出网之前
        raise AssertionError("upstream must not be called")

    monkeypatch.setattr(w, "_moonwell_proxy", exploding_proxy)
    assert admin_client.post("/ajax/vocab-test/answer", json=payload).status_code == 400


@pytest.mark.parametrize("payload", [
    {},
    {"sessionId": 42},                                   # 开关必填：缺省等于替用户决定
    {"sessionId": 42, "addUnknownToNotebook": "yes"},
])
def test_bad_finish_payloads_are_rejected_locally(admin_client, moonwell_configured,
                                                  monkeypatch, payload):
    import cps.web as w

    def exploding_proxy(*args, **kwargs):
        raise AssertionError("upstream must not be called")

    monkeypatch.setattr(w, "_moonwell_proxy", exploding_proxy)
    assert admin_client.post("/ajax/vocab-test/finish", json=payload).status_code == 400


# ---------- 4. 业务错误透传 ----------

def test_business_error_passes_through_with_code(admin_client, moonwell_configured,
                                                  monkeypatch):
    """后端业务错误是 HTTP 500 + Result.code；代理不翻译、不降级成 200。"""
    import cps.web as w

    failure = json.dumps({"success": False, "code": 50302,
                          "message": "会话已超时，请重新开始", "result": None})
    proxy = RecordingProxy({"/vocabulary/test/answer": (failure, 500)})
    monkeypatch.setattr(w, "_moonwell_proxy", proxy)

    response = admin_client.post("/ajax/vocab-test/answer",
                                 json={"sessionId": 42, "seq": 3, "answer": 1})
    assert response.status_code == 500
    assert response.get_json()["code"] == 50302
    # 上游 message 原样透传（代理不翻译、不改写文案）——前端只按 code 分支，不读它
    assert response.get_json()["message"] == "会话已超时，请重新开始"


# ---------- 5. 首屏渲染与独立降级 ----------

def test_page_renders_card_with_single_upstream_call(admin_client, moonwell_configured,
                                                     monkeypatch):
    """首屏只拉档位：测试历史交给 vocab-test.js 异步取，服务端多串一次调用就多背一个上游超时预算。"""
    import cps.web as w

    def proxy(path, payload, timeout, label, binary=False, method="POST", **kwargs):
        assert path == "/vocabulary/reading/settings", \
            "unexpected first-paint upstream call: %s" % path
        body, status = _settings_reply()
        return body, status, _json_headers()

    monkeypatch.setattr(w, "_moonwell_proxy", proxy)

    html = admin_client.get("/reading/settings").get_data(as_text=True)
    assert 'id="vt-root"' in html
    assert "Vocabulary Size Test" in html
    for attr in ("data-start-url", "data-answer-url", "data-finish-url", "data-history-url"):
        assert attr in html
    # 历史容器渲染为空/隐藏态，等 JS 填充；不再有服务端注入的 data-last
    assert 'id="vt-history-list"' in html
    assert "data-last" not in html
    assert "2026-10-05" not in html


def test_card_survives_settings_load_failure(admin_client, moonwell_configured,
                                             monkeypatch):
    """档位读不到只影响档位卡片：测试卡片仍可发起（AC-C1 的降级方向）。
    同时守住 _moonwell_proxy 的网络失败分支返回 (jsonify, 503) 而非三元组——解包必须被兜住，
    否则首屏变 500 白页。
    """
    import cps.web as w
    from flask import jsonify

    def failing_proxy(path, payload, timeout, label, binary=False, method="POST",
                      **kwargs):
        return jsonify({"success": False, "message": label + " service unavailable"}), 503

    monkeypatch.setattr(w, "_moonwell_proxy", failing_proxy)

    html = admin_client.get("/reading/settings").get_data(as_text=True)
    assert "Failed to load reading settings" in html
    assert 'id="vt-root"' in html


@pytest.mark.parametrize("method,url", [
    ("post", "/ajax/vocab-test/start"),
    ("post", "/ajax/vocab-test/answer"),
    ("post", "/ajax/vocab-test/finish"),
    ("get", "/ajax/vocab-test/history"),
])
def test_unreachable_upstream_returns_503_json_not_500(admin_client, moonwell_configured,
                                                       monkeypatch, method, url):
    """四条路由都必须原样透传 _moonwell_proxy 的返回值。

    Why：上游不可达/未配置时它返回的是 (jsonify, 503) 二元组，路由若按三元组解包会抛
    ValueError → 500 白页；答题/历史这类调用一旦白页，前端连降级分支都进不去。
    """
    import cps.web as w
    from flask import jsonify

    def failing_proxy(path, payload, timeout, label, binary=False, method="POST",
                      **kwargs):
        return jsonify({"success": False, "message": label + " service unavailable"}), 503

    monkeypatch.setattr(w, "_moonwell_proxy", failing_proxy)

    kwargs = {"json": {"sessionId": 42, "seq": 1, "answer": 1,
                       "addUnknownToNotebook": True}}
    response = getattr(admin_client, method)(url, **kwargs)
    assert response.status_code == 503
    assert response.get_json()["success"] is False
