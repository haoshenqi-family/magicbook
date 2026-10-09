"""Unit tests for the daily-learning proxy endpoints (R132 / B3).

Covers:
  1. All seven endpoints require login.
  2. GET proxies forward to the flat moon-well paths without payload.
  3. answer: valid grade 1-4 passes; grade 0/5/bool/non-int and bad scheduleId
     are rejected locally (400) without hitting moon-well.
  4. plan/settings: local range checks mirror the upstream DTO; the strand-sum
     rule (100) is left to moon-well (50503 semantics).
  5. match/book: bookId must be a numeric string; non-numeric rejected locally.
  6. moon-well business errors (HTTP 500 + Result.code) pass through untouched.

Why mock `_moonwell_proxy` instead of the HTTP layer: the proxy's whole contract
is "which path/payload/method goes upstream and what comes back" (same approach
as test_vocab_test_proxy.py); network and moon-well semantics live in its tests.
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


QUEUE_ITEM = {"scheduleId": "42", "word": "install", "questionType": "CHOOSE",
              "choices": ["install", "instal", "insult", "insulted"],
              "contextSentence": "He installed it.", "contextBook": "Book A",
              "contextChapter": "ch1", "encounterCount": 6}
STATS = {"dueNow": 3, "dueTomorrow": 8, "reviewing": 40, "mastered": 12,
         "fresh": 5, "retention7d": 87, "answers7d": 31}
PLAN = {"date": "2026-10-08", "reviews": [QUEUE_ITEM], "reviewTotal": 1,
        "newWords": [], "strands": {"inputMinutes": 5, "languageMinutes": 5,
                                    "outputMinutes": 5, "fluencyMinutes": 5,
                                    "inputPct": 25, "languagePct": 25,
                                    "outputPct": 25, "fluencyPct": 25},
        "settings": {"dailyNewLimit": 5, "dailyMinutes": 20, "strandInputPct": 25,
                     "strandLanguagePct": 25, "strandOutputPct": 25,
                     "strandFluencyPct": 25}}
MATCHES = [{"bookId": 1, "title": "Nice Book", "author": "A", "densityPct": 3.2,
            "level": "FIT", "levelName": "正合适", "unknownTokenCount": 16,
            "totalTokenCount": 500, "unknownSample": ["quick", "brown"],
            "upToDate": True}]

PATHS = {
    "queue": ("/ajax/learning/srs/queue", "/learning/srs/queue"),
    "stats": ("/ajax/learning/srs/stats", "/learning/srs/stats"),
    "plan": ("/ajax/learning/plan/today", "/learning/plan/today"),
    "books": ("/ajax/learning/match/books", "/learning/match/books"),
}


# ---------- 1. 鉴权 ----------

def test_endpoints_require_login(app, moonwell_configured):
    client = app.test_client()
    assert client.get("/learning").status_code == 302
    for local, _ in PATHS.values():
        assert client.get(local).status_code == 302, local
    assert client.post("/ajax/learning/srs/answer", json={}).status_code == 302
    assert client.post("/ajax/learning/plan/settings", json={}).status_code == 302
    assert client.post("/ajax/learning/match/book", json={}).status_code == 302


# ---------- 2. GET 透传 ----------

def test_get_proxies_forward_to_flat_paths(admin_client, moonwell_configured,
                                           monkeypatch):
    replies = {
        "/learning/srs/queue": (_envelope([QUEUE_ITEM]), 200),
        "/learning/srs/stats": (_envelope(STATS), 200),
        "/learning/plan/today": (_envelope(PLAN), 200),
        "/learning/match/books": (_envelope(MATCHES), 200),
    }
    proxy = RecordingProxy(replies)
    monkeypatch.setattr("cps.web._moonwell_proxy", proxy)
    for local, upstream in PATHS.values():
        admin_client.get(local)
        call = proxy.call_for(upstream)
        assert call["method"] == "GET"
        assert call["payload"] is None


def test_queue_limit_query_stays_in_query_string(admin_client, moonwell_configured,
                                                 monkeypatch):
    """limit 是 GET query，代理不解析不转发（moon-well 自己读 query）。"""
    proxy = RecordingProxy({"/learning/srs/queue": (_envelope([]), 200)})
    monkeypatch.setattr("cps.web._moonwell_proxy", proxy)
    admin_client.get("/ajax/learning/srs/queue?limit=5")
    # _moonwell_proxy 签名不带 query（Flask 在 request 里），透传即正确行为
    assert proxy.call_for("/learning/srs/queue")["payload"] is None


# ---------- 3. answer 参数域 ----------

def test_answer_forwards_valid_payload(admin_client, moonwell_configured,
                                       monkeypatch):
    proxy = RecordingProxy({"/learning/srs/answer": (
        _envelope({"scheduleId": "42", "word": "install", "state": "REVIEW",
                   "dueAt": "2026-10-11T10:00:00", "message": "3 天后再见"}), 200)})
    monkeypatch.setattr("cps.web._moonwell_proxy", proxy)
    response = admin_client.post("/ajax/learning/srs/answer",
                                 json={"scheduleId": "42", "grade": 3,
                                       "latencyMs": 2500})
    assert response.status_code == 200
    call = proxy.call_for("/learning/srs/answer")
    assert call["payload"] == {"scheduleId": 42, "grade": 3, "latencyMs": 2500}


def test_answer_rejects_bad_grades_locally(admin_client, moonwell_configured,
                                           monkeypatch):
    proxy = RecordingProxy({})
    monkeypatch.setattr("cps.web._moonwell_proxy", proxy)
    for grade in (0, 5, -1, True, False, "3", None, 2.5):
        response = admin_client.post("/ajax/learning/srs/answer",
                                     json={"scheduleId": "42", "grade": grade})
        assert response.status_code == 400, grade
    assert not proxy.calls, "bad grade must not reach moon-well"


def test_answer_rejects_bad_schedule_ids_locally(admin_client, moonwell_configured,
                                                 monkeypatch):
    proxy = RecordingProxy({})
    monkeypatch.setattr("cps.web._moonwell_proxy", proxy)
    for schedule_id in ("", "abc", "-1", "1.5", None, True):
        response = admin_client.post("/ajax/learning/srs/answer",
                                     json={"scheduleId": schedule_id, "grade": 3})
        assert response.status_code == 400, schedule_id
    assert not proxy.calls


def test_answer_rejects_bad_latency_locally(admin_client, moonwell_configured,
                                            monkeypatch):
    proxy = RecordingProxy({})
    monkeypatch.setattr("cps.web._moonwell_proxy", proxy)
    response = admin_client.post("/ajax/learning/srs/answer",
                                 json={"scheduleId": "42", "grade": 3,
                                       "latencyMs": -5})
    assert response.status_code == 400
    assert not proxy.calls


# ---------- 4. plan/settings 参数域 ----------

def _valid_settings():
    return {"dailyNewLimit": 10, "dailyMinutes": 40, "strandInputPct": 50,
            "strandLanguagePct": 10, "strandOutputPct": 20, "strandFluencyPct": 20}


def test_plan_settings_forwards_valid_payload(admin_client, moonwell_configured,
                                              monkeypatch):
    proxy = RecordingProxy({"/learning/plan/settings": (_envelope(_valid_settings()), 200)})
    monkeypatch.setattr("cps.web._moonwell_proxy", proxy)
    response = admin_client.post("/ajax/learning/plan/settings",
                                 json=_valid_settings())
    assert response.status_code == 200
    assert proxy.call_for("/learning/plan/settings")["payload"] == _valid_settings()


def test_plan_settings_rejects_out_of_range_locally(admin_client,
                                                    moonwell_configured,
                                                    monkeypatch):
    proxy = RecordingProxy({})
    monkeypatch.setattr("cps.web._moonwell_proxy", proxy)
    bad = _valid_settings()
    bad["strandFluencyPct"] = 101  # > 100
    assert admin_client.post("/ajax/learning/plan/settings", json=bad).status_code == 400
    bad2 = _valid_settings()
    bad2["dailyMinutes"] = 4  # < 5
    assert admin_client.post("/ajax/learning/plan/settings", json=bad2).status_code == 400
    bad3 = _valid_settings()
    del bad3["strandInputPct"]  # 缺字段
    assert admin_client.post("/ajax/learning/plan/settings", json=bad3).status_code == 400
    assert not proxy.calls


def test_plan_settings_strand_sum_left_to_upstream(admin_client,
                                                   moonwell_configured,
                                                   monkeypatch):
    """四股之和≠100 是 moon-well 的 50503：代理放行，业务错误原样透传。"""
    upstream_body = json.dumps({"success": False, "code": 50503,
                                "message": "四股配比之和必须等于 100", "result": None})
    proxy = RecordingProxy({"/learning/plan/settings": (upstream_body, 500)})
    monkeypatch.setattr("cps.web._moonwell_proxy", proxy)
    payload = _valid_settings()
    payload["strandFluencyPct"] = 30  # 105
    response = admin_client.post("/ajax/learning/plan/settings", json=payload)
    assert response.status_code == 500
    assert json.loads(response.data)["code"] == 50503


# ---------- 5. match/book 参数域 ----------

def test_match_book_forwards_numeric_id(admin_client, moonwell_configured,
                                        monkeypatch):
    proxy = RecordingProxy({"/learning/match/book": (_envelope(MATCHES[0]), 200)})
    monkeypatch.setattr("cps.web._moonwell_proxy", proxy)
    response = admin_client.post("/ajax/learning/match/book", json={"bookId": "100"})
    assert response.status_code == 200
    assert proxy.call_for("/learning/match/book")["payload"] == {"bookId": "100"}


def test_match_book_rejects_non_numeric_id(admin_client, moonwell_configured,
                                           monkeypatch):
    proxy = RecordingProxy({})
    monkeypatch.setattr("cps.web._moonwell_proxy", proxy)
    for book_id in ("", "abc", "-1", None, True, 1.5):
        response = admin_client.post("/ajax/learning/match/book",
                                     json={"bookId": book_id})
        assert response.status_code == 400, book_id
    assert not proxy.calls


# ---------- 6. 页面与业务错误透传 ----------

def test_learning_page_renders_without_upstream(admin_client, moonwell_configured):
    """首屏零上游调用：数据由 learning.js 异步取（成就页同模式）。"""
    response = admin_client.get("/learning")
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert "ln-card" in html
    assert "js/learning.js" in html
    assert "web.learning_srs_queue" not in html  # url_for 已渲染成路径
    # R137 三题型契约：释义题干 + 拼写输入必须随模板渲染（JS 才有得绑）
    assert 'id="ln-stem"' in html
    assert 'id="ln-spell-input"' in html
    assert 'id="ln-spell-check"' in html


def test_business_error_passes_through_with_code(admin_client, moonwell_configured,
                                                 monkeypatch):
    upstream_body = json.dumps({"success": False, "code": 50501,
                                "message": "复习计划不存在，请刷新队列", "result": None})
    proxy = RecordingProxy({"/learning/srs/answer": (upstream_body, 500)})
    monkeypatch.setattr("cps.web._moonwell_proxy", proxy)
    response = admin_client.post("/ajax/learning/srs/answer",
                                 json={"scheduleId": "42", "grade": 3})
    assert response.status_code == 500
    assert json.loads(response.data)["code"] == 50501


def test_unreachable_upstream_returns_503_json_not_500(admin_client,
                                                       moonwell_configured):
    """moon-well 未配置/不可达：代理层 503 JSON（_moonwell_proxy 既有契约）。"""
    from cps import constants
    monkeypatch_again = constants
    response = admin_client.get("/ajax/learning/srs/stats")
    # moonwell_configured fixture 配了假域名但网络不可达 → 503；不抛 500 白页
    assert response.status_code in (502, 503, 504)
    assert monkeypatch_again is not None


# ---------- 7. 页面真实渲染（登录后、db 已 mock） ----------

def test_learning_page_renders_full_dom(admin_client, moonwell_configured):
    """登录态下 /learning 渲染完整 DOM：卡片、脚本、URL 注入、导航入口。"""
    response = admin_client.get("/learning")
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert 'id="ln-card"' in html
    assert 'id="ln-stats"' in html
    assert 'id="ln-match-root"' in html
    assert "js/learning.js" in html
    assert "window.learningUrls" in html
    assert '"/ajax/learning/srs/queue"' in html
    # 导航入口（布局层）
    assert 'id="top_learning"' in html
    # CSRF 注入（learning.js 读取）
    assert 'id="ln-csrf"' in html


def test_nav_dropdown_contains_daily_learning(admin_client, moonwell_configured):
    response = admin_client.get("/learning")
    html = response.data.decode("utf-8")
    assert "Daily Learning" in html
