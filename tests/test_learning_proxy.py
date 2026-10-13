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
import io
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
    assert client.post("/ajax/learning/strands/reading", json={}).status_code == 302


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
    """首屏零上游调用：数据由 learning-hub.js 异步取（成就页同模式）。

    R166：中枢只留 banner + 计划 + 复习摘要 + 周视图，三题型 DOM 迁到 /learning/review。
    """
    response = admin_client.get("/learning")
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert 'id="lh-banner"' in html
    assert "js/learning-hub.js" in html
    assert "web.learning_srs_queue" not in html  # url_for 已渲染成路径
    # 复习队列的题干/拼写输入不得残留在中枢（迁走即删，否则两处 DOM 会漂移）
    assert 'id="ln-stem"' not in html
    assert 'id="ln-spell-input"' not in html
    assert 'id="ln-spell-check"' not in html


def test_learning_review_subpage_renders_queue_dom(admin_client,
                                                   moonwell_configured):
    """R137 三题型契约：释义题干 + 拼写输入必须随子页面模板渲染（JS 才有得绑）。"""
    response = admin_client.get("/learning/review")
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert 'id="ln-card"' in html
    assert 'id="ln-stem"' in html
    assert 'id="ln-spell-input"' in html
    assert 'id="ln-spell-check"' in html
    assert "js/learning-review.js" in html
    assert '"/ajax/learning/srs/queue"' in html


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
    """登录态下 /learning 渲染完整 DOM：banner、摘要卡、脚本、URL 注入、导航入口。"""
    response = admin_client.get("/learning")
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert 'id="ln-review-summary"' in html
    assert 'id="ln-plan"' in html
    assert "js/learning-common.js" in html
    assert "window.learningUrls" in html
    assert '"/ajax/learning/plan/today"' in html
    # 导航入口（布局层，R154 起为左侧一级导航）；R166 起说与写并入中枢，一级项撤掉
    assert 'id="top_learning"' in html
    assert 'id="top_speaking_writing"' not in html
    # CSRF 注入（learning-common.js 按 #lh-csrf 读取）
    assert 'id="lh-csrf"' in html


def test_nav_dropdown_contains_daily_learning(admin_client, moonwell_configured):
    response = admin_client.get("/learning")
    html = response.data.decode("utf-8")
    assert "Daily Learning" in html


# ---------- 6. strands/reading 心跳（R151，moon-well R149 四股台账 INPUT 股）----------

def test_reading_heartbeat_forwards_valid_payload(admin_client, moonwell_configured,
                                                  monkeypatch):
    proxy = RecordingProxy({"/learning/strands/reading": (_envelope("ok"), 200)})
    monkeypatch.setattr("cps.web._moonwell_proxy", proxy)
    response = admin_client.post("/ajax/learning/strands/reading",
                                 json={"seconds": 300, "bookId": "97"})
    assert response.status_code == 200
    call = proxy.call_for("/learning/strands/reading")
    assert call["payload"] == {"seconds": 300, "bookId": "97"}


def test_reading_heartbeat_without_book_id_omits_field(admin_client,
                                                       moonwell_configured,
                                                       monkeypatch):
    proxy = RecordingProxy({"/learning/strands/reading": (_envelope("ok"), 200)})
    monkeypatch.setattr("cps.web._moonwell_proxy", proxy)
    response = admin_client.post("/ajax/learning/strands/reading",
                                 json={"seconds": 300})
    assert response.status_code == 200
    assert proxy.call_for("/learning/strands/reading")["payload"] == {"seconds": 300}


def test_reading_heartbeat_rejects_bad_seconds_locally(admin_client,
                                                       moonwell_configured,
                                                       monkeypatch):
    proxy = RecordingProxy({})
    monkeypatch.setattr("cps.web._moonwell_proxy", proxy)
    for seconds in (29, 601, 0, -300, True, False, "300", None, 2.5):
        response = admin_client.post("/ajax/learning/strands/reading",
                                     json={"seconds": seconds})
        assert response.status_code == 400, seconds
    assert not proxy.calls, "bad heartbeat must not reach moon-well"


def test_reading_heartbeat_rejects_bad_book_id_locally(admin_client,
                                                       moonwell_configured,
                                                       monkeypatch):
    proxy = RecordingProxy({})
    monkeypatch.setattr("cps.web._moonwell_proxy", proxy)
    for book_id in ("", "abc", "-1", "1.5", True):
        response = admin_client.post("/ajax/learning/strands/reading",
                                     json={"seconds": 300, "bookId": book_id})
        assert response.status_code == 400, book_id
    assert not proxy.calls


# ---------- 7. B1 输出训练代理（R152：写作工坊/口语陪练/复述训练）----------

B1_POSTS = [
    ("/ajax/learning/writing/task/generate", "/learning/writing/task/generate"),
    ("/ajax/learning/writing/submit", "/learning/writing/submit"),
    ("/ajax/learning/writing/revise", "/learning/writing/revise"),
    ("/ajax/learning/speaking/session", "/learning/speaking/session"),
    ("/ajax/learning/speaking/message", "/learning/speaking/message"),
    ("/ajax/learning/speaking/report", "/learning/speaking/report"),
    ("/ajax/learning/speaking/messages", "/learning/speaking/messages"),
    ("/ajax/learning/retell/start", "/learning/retell/start"),
    ("/ajax/learning/retell/submit-round", "/learning/retell/submit-round"),
    ("/ajax/learning/retell/finish", "/learning/retell/finish"),
]


def test_b1_endpoints_require_login(app, moonwell_configured):
    client = app.test_client()
    for local, _ in B1_POSTS:
        assert client.post(local, json={}).status_code == 302, local
    assert client.get("/ajax/learning/writing/history").status_code == 302
    assert client.get("/ajax/learning/speaking/history").status_code == 302
    assert client.get("/learning/speaking-writing").status_code == 302


def test_b1_submit_forwards_cleaned_payload(admin_client, moonwell_configured,
                                             monkeypatch):
    proxy = RecordingProxy({"/learning/writing/submit": (_envelope({}), 200)})
    monkeypatch.setattr("cps.web._moonwell_proxy", proxy)
    response = admin_client.post(
        "/ajax/learning/writing/submit",
        json={"taskId": "T-1", "text": "Hello world.", "evil": "x"},
        )
    assert response.status_code == 200
    call = proxy.call_for("/learning/writing/submit")
    # 白名单裁剪：未知键不透传；taskId 原样
    assert call["payload"] == {"taskId": "T-1", "text": "Hello world."}


def test_b1_rejects_missing_required_fields_locally(admin_client,
                                                     moonwell_configured,
                                                     monkeypatch):
    proxy = RecordingProxy({})
    monkeypatch.setattr("cps.web._moonwell_proxy", proxy)
    cases = [
        ("/ajax/learning/writing/task/generate", {}),                      # 缺 mode
        ("/ajax/learning/writing/submit", {"taskId": "T-1"}),              # 缺 text
        ("/ajax/learning/speaking/message", {"sessionId": "S-1"}),         # 缺 text
        ("/ajax/learning/retell/submit-round", {"retellId": "R-1"}),       # 缺 transcript
        ("/ajax/learning/retell/finish", {}),                              # 缺 retellId
    ]
    for local, body in cases:
        response = admin_client.post(local, json=body)
        assert response.status_code == 400, (local, body)
    assert not proxy.calls, "missing required fields must not reach moon-well"


def test_b1_rejects_oversized_text_locally(admin_client, moonwell_configured,
                                            monkeypatch):
    proxy = RecordingProxy({})
    monkeypatch.setattr("cps.web._moonwell_proxy", proxy)
    response = admin_client.post("/ajax/learning/writing/submit",
                                 json={"taskId": "T-1", "text": "x" * 20001})
    assert response.status_code == 400
    assert not proxy.calls


def test_b1_retell_round_keeps_int_fields(admin_client, moonwell_configured,
                                           monkeypatch):
    proxy = RecordingProxy({"/learning/retell/submit-round": (_envelope({}), 200)})
    monkeypatch.setattr("cps.web._moonwell_proxy", proxy)
    response = admin_client.post(
        "/ajax/learning/retell/submit-round",
        json={"retellId": "R-1", "round": 2, "durationMs": 153000,
              "transcript": "I retell the story."},
        )
    assert response.status_code == 200
    # 整数字段保类型透传（Jackson 语义一致）
    assert proxy.call_for("/learning/retell/submit-round")["payload"] == {
        "retellId": "R-1", "round": 2, "durationMs": 153000,
        "transcript": "I retell the story."}


def test_b1_rejects_bad_minutes_per_round_locally(admin_client,
                                                   moonwell_configured,
                                                   monkeypatch):
    proxy = RecordingProxy({})
    monkeypatch.setattr("cps.web._moonwell_proxy", proxy)
    for minutes in (["x"], [], [0], [31], "4,3,2", [True]):
        response = admin_client.post("/ajax/learning/retell/start",
                                     json={"paragraphText": "Once upon a time.",
                                           "minutesPerRound": minutes})
        assert response.status_code == 400, minutes
    assert not proxy.calls


def test_speaking_writing_page_redirects_to_hub(admin_client, moonwell_configured):
    """R166：旧五合一页 302 回中枢（书签与 R152 期文档链接不失效）。"""
    response = admin_client.get("/learning/speaking-writing")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/learning")


def test_writing_subpage_renders(admin_client, moonwell_configured):
    response = admin_client.get("/learning/writing")
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert 'id="lh-csrf"' in html
    assert "js/learning-writing.js" in html
    assert "window.learningUrls" in html
    assert '"/ajax/learning/writing/task/generate"' in html


# ---------- 8. P3 代理：计时重读 / 听写 / 周视图（R153）----------

def test_p3_endpoints_require_login(app, moonwell_configured):
    client = app.test_client()
    for local in ("/ajax/learning/listening/materials",
                  "/ajax/learning/rrr/trend", "/ajax/learning/rrr/recommend"):
        assert client.get(local).status_code == 302, local
    for local in ("/ajax/learning/listening/paragraphs",
                  "/ajax/learning/listening/dictation/check",
                  "/ajax/learning/rrr/record"):
        assert client.post(local, json={}).status_code == 302, local


def test_dictation_check_passes_bool_and_int(admin_client, moonwell_configured,
                                             monkeypatch):
    proxy = RecordingProxy({"/learning/listening/dictation/check": (_envelope({}), 200)})
    monkeypatch.setattr("cps.web._moonwell_proxy", proxy)
    response = admin_client.post("/ajax/learning/listening/dictation/check",
                                 json={"bookId": "97", "order": 3,
                                       "answer": "the quick brown fox",
                                       "addUnknown": True})
    assert response.status_code == 200
    assert proxy.call_for("/learning/listening/dictation/check")["payload"] == {
        "bookId": "97", "order": 3, "answer": "the quick brown fox",
        "addUnknown": True}


def test_dictation_check_rejects_bad_types_locally(admin_client,
                                                    moonwell_configured,
                                                    monkeypatch):
    proxy = RecordingProxy({})
    monkeypatch.setattr("cps.web._moonwell_proxy", proxy)
    for body in ({"bookId": "97", "order": "3", "answer": "hi"},        # order 非整数
                 {"bookId": "97", "order": 3, "answer": "hi", "addUnknown": "yes"},  # 布尔非法
                 {"bookId": "97", "order": 3, "answer": "x" * 20001}):  # 超长
        assert admin_client.post("/ajax/learning/listening/dictation/check",
                                 json=body).status_code == 400, body
    assert not proxy.calls


def test_rrr_record_keeps_int_fields(admin_client, moonwell_configured,
                                     monkeypatch):
    proxy = RecordingProxy({"/learning/rrr/record": (_envelope({}), 200)})
    monkeypatch.setattr("cps.web._moonwell_proxy", proxy)
    response = admin_client.post("/ajax/learning/rrr/record",
                                 json={"bookId": "97", "order": 5, "round": 2,
                                       "durationMs": 92000, "mode": "ALOUD"})
    assert response.status_code == 200
    assert proxy.call_for("/learning/rrr/record")["payload"] == {
        "bookId": "97", "order": 5, "round": 2, "durationMs": 92000, "mode": "ALOUD"}


def test_reread_and_dictation_subpages_render(admin_client, moonwell_configured):
    """R153 的 P3 DOM 契约随拆分搬到各自子页面（R166）。"""
    reread = admin_client.get("/learning/reread").data.decode("utf-8")
    assert 'id="sw-rr-panel"' in reread
    assert "listeningMaterials" in reread
    assert '"/ajax/learning/rrr/recommend"' in reread

    dictation = admin_client.get("/learning/dictation").data.decode("utf-8")
    assert 'id="sw-d-panel"' in dictation
    assert 'id="sw-d-add-unknown"' in dictation
    assert '"/ajax/learning/listening/dictation/check"' in dictation


def test_speaking_subpage_has_coach_tts_and_mic(admin_client, moonwell_configured):
    html = admin_client.get("/learning/speaking").data.decode("utf-8")
    assert 'id="sw-s-tts"' in html
    assert 'id="sw-s-mic"' in html
    assert "js/learning-voice.js" in html
    assert '"/ajax/learning/asr/transcribe"' in html


def test_learning_page_has_week_panel(admin_client, moonwell_configured):
    html = admin_client.get("/learning").data.decode("utf-8")
    assert 'id="ln-week"' in html
    assert "/ajax/learning/strands/summary" in html


# ---------- 9. 语音输入（R155：录音 multipart 直传转写）----------

def test_asr_transcribe_requires_login(app, moonwell_configured):
    client = app.test_client()
    assert client.post("/ajax/learning/asr/transcribe").status_code == 302


def test_asr_transcribe_rejects_missing_file_locally(admin_client,
                                                     moonwell_configured,
                                                     monkeypatch):
    monkeypatch.setattr("cps.web._moonwell_multipart",
                        lambda *a, **k: (_envelope({}), 200, {}))
    assert admin_client.post("/ajax/learning/asr/transcribe").status_code == 400


def test_asr_transcribe_rejects_oversized_recording_locally(
        admin_client, moonwell_configured, monkeypatch):
    calls = []
    monkeypatch.setattr("cps.web._moonwell_multipart",
                        lambda *a, **k: calls.append(a) or (_envelope({}), 200, {}))
    big = b"x" * (10 * 1024 * 1024 + 1)
    response = admin_client.post("/ajax/learning/asr/transcribe",
                                 data={"file": (io.BytesIO(big), "recording.wav", "audio/wav")})
    assert response.status_code == 400
    assert not calls, "oversized recording must not reach moon-well"


def test_asr_transcribe_forwards_file_bytes(admin_client, moonwell_configured,
                                            monkeypatch):
    seen = {}

    def fake_forward(path, file_bytes, filename, timeout, label):
        seen.update(path=path, file_bytes=file_bytes, filename=filename)
        return _envelope({"text": "hello from mic"}), 200

    monkeypatch.setattr("cps.web._moonwell_multipart", fake_forward)
    # Why 不手写 content_type：multipart 边界必须由 werkzeug 生成，
    # 手动指定会把 boundary 弄丢、files 解析为空
    response = admin_client.post(
        "/ajax/learning/asr/transcribe",
        data={"file": (io.BytesIO(b"RIFF...."), "recording.wav", "audio/wav")})
    assert response.status_code == 200
    assert seen["path"] == "/learning/asr/transcribe"
    assert seen["file_bytes"] == b"RIFF...."
    assert seen["filename"] == "recording.wav"


def test_mic_buttons_render_on_their_own_pages(admin_client, moonwell_configured):
    speaking = admin_client.get("/learning/speaking").data.decode("utf-8")
    assert 'id="sw-s-mic"' in speaking
    assert 'id="sw-s-audio-status"' in speaking
    assert "asrTranscribe" in speaking
    # 复述页只带自己的麦克风，不继承口语页的会话 DOM（R166 拆页的隔离断言）
    retell = admin_client.get("/learning/retell").data.decode("utf-8")
    assert 'id="sw-r-mic"' in retell
    assert 'id="sw-s-mic"' not in retell


# ---------- 10. 麦克风按钮可用性（R156：带标签/状态自更新/用法提示）----------

def test_mic_buttons_have_labels_and_hint(admin_client, moonwell_configured):
    html = admin_client.get("/learning/speaking").data.decode("utf-8")
    # 空白按钮修正：麦克风按钮有文字标签，且面板有用法提示
    assert html.count('sw-mic-label') >= 1
    assert "Voice input" in html
    assert "sw-mic-hint" in html


# ---------- 11. 麦克风设备选择器（R160）----------

def test_mic_device_selector_present(admin_client, moonwell_configured):
    speaking = admin_client.get("/learning/speaking").data.decode("utf-8")
    assert 'id="sw-s-mic-device"' in speaking
    assert "Microphone device" in speaking
    retell = admin_client.get("/learning/retell").data.decode("utf-8")
    assert 'id="sw-r-mic-device"' in retell
