# cps/routes/learning.py — learning 域定制路由（R181，架构评审 B2 自 cps.web 迁出）。
# 装饰注册沿用原 web blueprint（endpoint 名不变）；依赖的辅助符号显式列于 import。

from cps.moonwell.client import NO_PROXY
from cps.moonwell.client import client as moonwell_client
from cps.web import (
    _PROXY_LIMITS,
    _b1_payload,
    _b1_proxy,
    _moonwell_multipart,
    _moonwell_proxy,
    data,
    web,
)
from ..render_template import render_title_template
from ..usermanagement import user_login_required
from flask import Response
from flask import jsonify
from flask import redirect
from flask import request
from flask import stream_with_context
from flask import url_for
from flask import session as flask_session
from flask_babel import gettext as _
import logging
import re
import requests

log = logging.getLogger(__name__)

# 写作批改是同步 LLM（moon-well magpie 单次预算 150s，见 Nacos moon-well-ai.yaml）。
# R191：原先 90s 会在后端仍成功时先超时——实测 revise 104s 返回 200，前端却只拿到
# 503 service unavailable，用户重试还会再生成一稿。210s = 后端 150s + 落库/网络余量；
# 调大前先确认上游反代（Traefik/Caddy）与浏览器都不会先掐断。
_WRITING_LLM_TIMEOUT = 210

# SSE 建连 10s；单 chunk idle 300s。后端每 5s 发 ping，300s 只是兜底——比「整段
# 请求 210s」更耐用：心跳期间即使批改超过 150s，代理也不会先掐断连接。
_LLM_SSE_CONNECT_TIMEOUT = 10
_LLM_SSE_IDLE_TIMEOUT = 300

# 编故事实测 10-25s，按写作同档给 120s（JSON 回退用；SSE 走心跳兜底）。
_STORY_LLM_TIMEOUT = 120


@web.route("/learning", methods=["GET"])
@user_login_required
def learning_page():
    """每日学习中枢（R166）：功能卡片 banner + 今日计划 + 复习摘要 + 四股周视图。

    R166 起本页不再内嵌复习队列与难度匹配面板（搬入各自子页面），只留
    「今日复习 x/20 · 到期 n 词」摘要卡。数据全部由 learning-hub.js 异步经
    /ajax/learning-* 拉取——页面本身零上游调用，moon-well 慢/重启不拖首屏。
    """
    return render_title_template("learning.html", title=_("Daily Learning"))


@web.route("/learning/review", methods=["GET"])
@user_login_required
def learning_review_page():
    """复习队列子页面（R166）：SRS 到期卡逐张作答，逻辑自 learning.js 迁入。"""
    return render_title_template("learning_review.html", title=_("Review Queue"))


@web.route("/learning/match", methods=["GET"])
@user_login_required
def learning_match_page():
    """选书难度匹配子页面（R166）：选架→估算→推荐，后台补算时前端轮询。"""
    return render_title_template("learning_match.html", title=_("Book Difficulty Match"))


@web.route("/learning/writing", methods=["GET"])
@user_login_required
def learning_writing_page():
    """写作工坊子页面（R166，原说与写页 tab 1）：出题/写稿/AI 批改/二稿进步。"""
    return render_title_template("learning_writing.html", title=_("Writing Workshop"))


@web.route("/learning/speaking", methods=["GET"])
@user_login_required
def learning_speaking_page():
    """AI 口语陪练子页面（R166，原 tab 2）：场景会话 + 逐轮反馈 + 会话报告。"""
    return render_title_template("learning_speaking.html", title=_("AI Speaking Coach"))


@web.route("/learning/retell", methods=["GET"])
@user_login_required
def learning_retell_page():
    """复述训练子页面（R166，原 tab 3）：4-3-2 递减时限三轮 + 指标解读。"""
    return render_title_template("learning_retell.html", title=_("Retell Drill (4-3-2)"))


@web.route("/learning/reread", methods=["GET"])
@user_login_required
def learning_reread_page():
    """计时重读子页面（R166，原 tab 4）：同段朗读三遍实测 WPM 与趋势。"""
    return render_title_template("learning_reread.html", title=_("Timed rereading"))


@web.route("/learning/dictation", methods=["GET"])
@user_login_required
def learning_dictation_page():
    """听写子页面（R166，原 tab 5）：播放段落 + 词级 diff + 漏词入队。"""
    return render_title_template("learning_dictation.html", title=_("Dictation"))


@web.route("/learning/story", methods=["GET"])
@user_login_required
def learning_story_page():
    """单词编故事子页面（R200）：到期词/粘贴词表 → AI 微故事 + 词表卡。"""
    return render_title_template("learning_story.html", title=_("Word Story"))


@web.route("/learning/speaking-writing", methods=["GET"])
@user_login_required
def speaking_writing_page():
    """旧「说与写」五合一页（R152）→ 中枢（R166）。

    Why 保留路由而非删除：导航项、用户书签与 R152 期间的文档链接都指向它，
    302 回中枢比 404 诚实——五个面板各自成页后这里已无对应实体。
    """
    return redirect(url_for("web.learning_page"))


@web.route("/ajax/learning/writing/task/generate", methods=["POST"])
@user_login_required
def learning_writing_generate():
    """Proxy writing task generation（LLM 出题，可结合在读的书）。"""
    return _b1_proxy("/learning/writing/task/generate",
                     ("mode", "cefrLevel", "prompt", "bookId", "bookTitle", "chapter"),
                     required=("mode",), timeout=90)


@web.route("/ajax/learning/writing/submit", methods=["POST"])
@user_login_required
def learning_writing_submit():
    """Proxy writing submission（LLM 批改：总体+逐句+升级+四维评分）。"""
    return _b1_proxy("/learning/writing/submit", ("taskId", "text"),
                     required=("taskId", "text"), timeout=_WRITING_LLM_TIMEOUT)


@web.route("/ajax/learning/writing/revise", methods=["POST"])
@user_login_required
def learning_writing_revise():
    """Proxy writing revision（同 submit 契约，多进步确认）。"""
    return _b1_proxy("/learning/writing/revise", ("taskId", "text"),
                     required=("taskId", "text"), timeout=_WRITING_LLM_TIMEOUT)


@web.route("/ajax/learning/writing/submit/stream", methods=["POST"])
@user_login_required
def learning_writing_submit_stream():
    """SSE 透传初稿批改（R194）：status/ping/result/error 分型事件。"""
    return _llm_sse_proxy(
        "/learning/writing/submit/stream", "learning writing submit stream",
        lambda: _b1_payload(("taskId", "text"), ("taskId", "text")))


@web.route("/ajax/learning/writing/revise/stream", methods=["POST"])
@user_login_required
def learning_writing_revise_stream():
    """SSE 透传修订稿批改（R194），契约同 submit/stream。"""
    return _llm_sse_proxy(
        "/learning/writing/revise/stream", "learning writing revise stream",
        lambda: _b1_payload(("taskId", "text"), ("taskId", "text")))


def _llm_sse_proxy(path, label, payload_builder):
    """LLM 长任务 SSE 的薄代理（写作 R194 / 编故事 R200）：只补 trace/Bearer，不改写事件体。

    Why 不复用 _b1_proxy：后者按 ``response.text`` 整段读取，会把 SSE 缓冲到任务
    结束才返回，等于没流式。这里 ``stream=True`` 逐 chunk yield，并在建连阶段完成
    401 刷新（流开始后无法回滚已发事件，不能重放）。

    payload_builder 返回 None 表示本地校验失败（400），此时不打扰 moon-well。

    断线语义：客户端关闭时 Flask 生成器退出，finally 关闭上游 requests 连接；
    moon-well 侧的任务线程不取消，结果继续落库，用户刷新历史可取回。
    """
    payload = payload_builder()
    if payload is None:
        return jsonify({"success": False, "message": "invalid request body"}), 400

    base = moonwell_client.base_url()
    if not base:
        return jsonify({"success": False, "message": "moon-well is not configured"}), 503

    token = flask_session.get("moonwell_access_token")
    if not token:
        # R145 全 token 化：无 token 直接 401，不降级成匿名请求
        return jsonify({"success": False,
                        "message": "moon-well 登录已失效，请重新登录"}), 401

    def _connect(bearer):
        headers = {
            "X-Trace-Id": moonwell_client.trace_id(),
            "authorization": "Bearer " + bearer,
            "Accept": "text/event-stream",
        }
        return requests.post(
            base + path, json=payload, headers=headers, stream=True,
            timeout=(_LLM_SSE_CONNECT_TIMEOUT, _LLM_SSE_IDLE_TIMEOUT),
            proxies=NO_PROXY,
        )

    try:
        upstream = _connect(token)
    except requests.RequestException as error:
        log.warning("moon-well %s SSE connect failed: %s", path, error)
        return jsonify({"success": False, "message": label + " service unavailable"}), 503

    if upstream.status_code == 401:
        refreshed = moonwell_client.refresh_session_token()
        if refreshed:
            upstream.close()
            try:
                upstream = _connect(refreshed)
            except requests.RequestException as error:
                log.warning("moon-well %s SSE reconnect failed: %s", path, error)
                return jsonify({"success": False,
                                "message": label + " service unavailable"}), 503

    if upstream.status_code != 200:
        status_code = upstream.status_code
        body = upstream.text
        content_type = upstream.headers.get("Content-Type", "application/json")
        upstream.close()
        return Response(body, status=status_code, content_type=content_type)

    def _generate():
        try:
            for chunk in upstream.iter_content(chunk_size=None):
                if chunk:
                    yield chunk
        except requests.RequestException as error:
            # 连接中断后不再补发 JSON（流已开始，状态码已发出）；前端按「结果可能已保存」
            # 处理，避免把它误判成一次新的批改请求。
            log.warning("moon-well %s SSE stream interrupted: %s", path, error)
        finally:
            upstream.close()

    response = Response(stream_with_context(_generate()), status=200,
                        content_type="text/event-stream")
    response.headers["Cache-Control"] = "no-cache"
    response.headers["X-Accel-Buffering"] = "no"
    response.headers["Connection"] = "keep-alive"
    return response


@web.route("/ajax/learning/writing/history", methods=["GET"])
@user_login_required
def learning_writing_history():
    """Proxy writing history; ?limit=1..50（越界上游收敛）。"""
    return _moonwell_proxy("/learning/writing/history", None, 15,
                           "learning writing history", method="GET")


@web.route("/ajax/learning/writing/task", methods=["GET"])
@user_login_required
def learning_writing_task():
    """Proxy one writing task with its drafts (R168 续写).

    Why 单独取详情而不是让 history 带正文：草稿上限 4000 字符、每任务可多稿、列表
    默认 20 条，带正文的最坏情况是几百 KB 的列表响应，而续写一次只用其中一条。
    超时给 20s：详情本身是纯读，但要与同族 LLM 端点同档，避免上游冷启动时前端
    先超时。taskId 只认数字（防把任意串拼进转发路径），越权/不存在由上游按 50512 回。
    """
    task_id = (request.args.get("taskId") or "").strip()
    if not task_id.isdigit() or len(task_id) > _PROXY_LIMITS["taskId"]:
        return jsonify({"success": False, "message": "taskId must be a numeric id"}), 400
    return _moonwell_proxy("/learning/writing/task?taskId=" + task_id, None, 20,
                           "learning writing task", method="GET")


@web.route("/ajax/learning/story/generate", methods=["POST"])
@user_login_required
def learning_story_generate():
    """Proxy word-story generation（JSON 回退，SSE 不可用时走这里）。"""
    payload = _story_payload()
    if payload is None:
        return jsonify({"success": False, "message": "invalid request body"}), 400
    return _moonwell_proxy("/learning/story/generate", payload, _STORY_LLM_TIMEOUT,
                           "learning word story")


@web.route("/ajax/learning/story/generate/stream", methods=["POST"])
@user_login_required
def learning_story_generate_stream():
    """SSE 透传编故事（R200）：status/ping/result/error 分型事件。"""
    return _llm_sse_proxy("/learning/story/generate/stream",
                          "learning word story stream", _story_payload)


@web.route("/ajax/learning/story/history", methods=["GET"])
@user_login_required
def learning_story_history():
    """Proxy word-story history; ?limit=1..50（越界上游收敛）。"""
    return _moonwell_proxy("/learning/story/history", None, 15,
                           "learning word story history", method="GET")


@web.route("/ajax/learning/story/detail", methods=["GET"])
@user_login_required
def learning_story_detail():
    """Proxy one story by id（历史回看）。id 只认数字，越权/不存在由上游 50524 回。"""
    story_id = (request.args.get("id") or "").strip()
    if not story_id.isdigit() or len(story_id) > _PROXY_LIMITS["storyId"]:
        return jsonify({"success": False, "message": "id must be a numeric id"}), 400
    return _moonwell_proxy("/learning/story/" + story_id, None, 15,
                           "learning word story detail", method="GET")


def _story_payload():
    """编故事请求白名单：due 只带 count，manual 的整段词表折成单元素 list。

    Why 不复用 _b1_payload：它只认字符串/少量整数字段，而本端点有 words 数组。
    manual 前端只发一个「整段粘贴」字符串；服务端按逗号/分号/换行切分与校验——
    代理只做长度与类型护栏，词法判断留在 moon-well（一个口径）。
    """
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return None
    source = str(payload.get("source") or "due").strip().lower()
    if source not in ("due", "manual"):
        return None
    cleaned = {"source": source}
    if source == "manual":
        words = payload.get("words")
        if not isinstance(words, list) or not words:
            return None
        text = "\n".join(item.strip() for item in words
                         if isinstance(item, str) and item.strip())
        if not text or len(text) > _PROXY_LIMITS["storyWords"]:
            return None
        cleaned["words"] = [text]
    else:
        count = payload.get("count", 6)
        if isinstance(count, bool) or not isinstance(count, int) or not 1 <= count <= 8:
            return None
        cleaned["count"] = count
    cefr = payload.get("cefrLevel")
    if cefr is not None:
        if not isinstance(cefr, str) or cefr not in ("A2", "B1", "B2", "C1"):
            return None
        cleaned["cefrLevel"] = cefr
    return cleaned


@web.route("/ajax/learning/speaking/session", methods=["POST"])
@user_login_required
def learning_speaking_session():
    """Proxy speaking session start（场景+教练风格；greeting 同步返回）。"""
    return _b1_proxy("/learning/speaking/session",
                     ("scenario", "scenarioLabel", "coachStyle", "bookId", "bookTitle"),
                     required=("scenario",), timeout=90)


@web.route("/ajax/learning/speaking/message", methods=["POST"])
@user_login_required
def learning_speaking_message():
    """Proxy one speaking turn（用户文本 → coach 回应+分层反馈；LLM 密集）。"""
    return _b1_proxy("/learning/speaking/message", ("sessionId", "text", "audioUrl"),
                     required=("sessionId", "text"), timeout=90)


@web.route("/ajax/learning/speaking/report", methods=["POST"])
@user_login_required
def learning_speaking_report():
    """Proxy session report（LLM 解读整场对话）。"""
    return _b1_proxy("/learning/speaking/report", ("sessionId",),
                     required=("sessionId",), timeout=90)


@web.route("/ajax/learning/speaking/messages", methods=["POST"])
@user_login_required
def learning_speaking_messages():
    """Proxy message replay of one past session（POST+body 规范，sessionId 防路径注入）。"""
    return _b1_proxy("/learning/speaking/messages", ("sessionId",),
                     required=("sessionId",), timeout=15)


@web.route("/ajax/learning/speaking/history", methods=["GET"])
@user_login_required
def learning_speaking_history():
    """Proxy speaking history; ?limit=1..50。"""
    return _moonwell_proxy("/learning/speaking/history", None, 15,
                           "learning speaking history", method="GET")


@web.route("/ajax/learning/retell/start", methods=["POST"])
@user_login_required
def learning_retell_start():
    """Proxy retell start（素材=用户粘贴段落；时限默认 4/3/2）。"""
    return _b1_proxy("/learning/retell/start",
                     ("paragraphText", "bookId", "chapter", "minutesPerRound"),
                     required=("paragraphText",), timeout=15)


@web.route("/ajax/learning/retell/submit-round", methods=["POST"])
@user_login_required
def learning_retell_round():
    """Proxy one retell round（纯指标计算：WPM/填充词/词汇多样性，无 LLM）。"""
    return _b1_proxy("/learning/retell/submit-round",
                     ("retellId", "round", "durationMs", "transcript"),
                     required=("retellId", "transcript"), timeout=15)


@web.route("/ajax/learning/retell/finish", methods=["POST"])
@user_login_required
def learning_retell_finish():
    """Proxy retell summary（LLM 解读指标变化）。"""
    return _b1_proxy("/learning/retell/finish", ("retellId",),
                     required=("retellId",), timeout=90)


@web.route("/ajax/learning/listening/materials", methods=["GET"])
@user_login_required
def learning_listening_materials():
    """Proxy listening materials; ?source=ted|tts（默认 ted，越界上游报错）。"""
    return _moonwell_proxy("/learning/listening/materials", None, 15,
                           "learning listening materials", method="GET")


@web.route("/ajax/learning/listening/paragraphs", methods=["POST"])
@user_login_required
def learning_listening_paragraphs():
    """Proxy paragraph list of one material（RRR 与听写共用段落源）。"""
    return _b1_proxy("/learning/listening/paragraphs", ("bookId",),
                     required=("bookId",), timeout=15)


@web.route("/ajax/learning/listening/dictation/check", methods=["POST"])
@user_login_required
def learning_listening_dictation():
    """Proxy dictation check（词级 diff；addUnknown=true 时错/漏词入生词本）。"""
    return _b1_proxy("/learning/listening/dictation/check",
                     ("bookId", "order", "answer", "addUnknown"),
                     required=("bookId", "order", "answer"), timeout=15)


@web.route("/ajax/learning/rrr/record", methods=["POST"])
@user_login_required
def learning_rrr_record():
    """Proxy one timed-rereading round（durationMs 实测直入流利度股）。"""
    return _b1_proxy("/learning/rrr/record",
                     ("bookId", "order", "round", "durationMs", "mode"),
                     required=("bookId", "order", "round", "durationMs"), timeout=15)


@web.route("/ajax/learning/rrr/trend", methods=["GET"])
@user_login_required
def learning_rrr_trend():
    """Proxy same-paragraph rounds trend; ?bookId&order（30 分钟切会话语义在上游）。"""
    return _moonwell_proxy("/learning/rrr/trend", None, 10,
                           "learning rrr trend", method="GET")


@web.route("/ajax/learning/strands/summary", methods=["GET"])
@user_login_required
def learning_strands_summary():
    """Proxy per-day strand ledger for the weekly panel; ?days=1..30（默认 7）。"""
    return _moonwell_proxy("/learning/strands/summary", None, 10,
                           "learning strands summary", method="GET")


@web.route("/ajax/learning/rrr/recommend", methods=["GET"])
@user_login_required
def learning_rrr_recommend():
    """Proxy due-word paragraph recommendations; ?limit=1..20。"""
    return _moonwell_proxy("/learning/rrr/recommend", None, 15,
                           "learning rrr recommend", method="GET")


@web.route("/ajax/learning/srs/queue", methods=["GET"])
@user_login_required
def learning_srs_queue():
    """Proxy the due review queue; ?limit=1..50（moon-well 上限 50，越界自动收敛）。"""
    return _moonwell_proxy("/learning/srs/queue", None, 10,
                           "learning srs queue", method="GET")


@web.route("/ajax/learning/srs/answer", methods=["POST"])
@user_login_required
def learning_srs_answer():
    """Proxy one review answer; payload {"scheduleId": id, "grade": 1-4,
    "latencyMs": ms?, "questionType": "CHOOSE"|...}.

    Why scheduleId 校验为纯数字：moon-well 实体是自增 Long，前端 VO 已转字符串；
    代理只挡明显非法（空/负/非数字），归属校验在上游。
    Why questionType 必须透传（R167）：辨析题在混出带里随机出现，服务端事后重算会与
    用户实际所做约一半不一致，而该字段是四技能统计与保持率的底座。本代理逐字段重建
    body，漏抄一个字段就是**静默丢弃**——前端发了、后端收不到、页面不报错，所以这里
    显式收并补一条透传断言。取值合法性与回落由上游白名单负责。
    """
    payload = request.get_json(silent=True) or {}
    schedule_id = payload.get("scheduleId")
    grade = payload.get("grade")
    if isinstance(schedule_id, bool) or not schedule_id:
        return jsonify({"success": False, "message": "scheduleId is required"}), 400
    if not re.match(r"^\d+$", str(schedule_id)):
        return jsonify({"success": False, "message": "scheduleId must be a positive integer"}), 400
    if isinstance(grade, bool) or not isinstance(grade, int) or not 1 <= grade <= 4:
        return jsonify({"success": False, "message": "grade must be an integer 1-4"}), 400
    latency = payload.get("latencyMs")
    if latency is not None and (isinstance(latency, bool) or not isinstance(latency, int) or latency < 0):
        return jsonify({"success": False, "message": "latencyMs must be a non-negative integer"}), 400
    question_type = payload.get("questionType")
    if question_type is not None and (not isinstance(question_type, str)
                                       or not question_type.strip()):
        return jsonify({"success": False,
                        "message": "questionType must be a non-empty string"}), 400
    body = {"scheduleId": int(schedule_id), "grade": grade}
    if latency is not None:
        body["latencyMs"] = latency
    if question_type:
        body["questionType"] = question_type.strip().upper()
    return _moonwell_proxy("/learning/srs/answer", body, 5, "learning srs answer")


@web.route("/ajax/learning/srs/stats", methods=["GET"])
@user_login_required
def learning_srs_stats():
    """Proxy the SRS stats snapshot (due counts / retention)."""
    return _moonwell_proxy("/learning/srs/stats", None, 10,
                           "learning srs stats", method="GET")


@web.route("/ajax/learning/plan/today", methods=["GET"])
@user_login_required
def learning_plan_today():
    """Proxy today's plan (reviews + new words + strand budget).

    首次访问会在上游自动落默认设置行；15s 容忍首建超时。
    """
    return _moonwell_proxy("/learning/plan/today", None, 15,
                           "learning plan today", method="GET")


@web.route("/ajax/learning/plan/settings", methods=["POST"])
@user_login_required
def learning_plan_settings():
    """Proxy the plan settings update; payload 为 moon-well DTO 的同构子集。

    代理域校验：数值型且在 UI 允许范围内（与后端 @Min/@Max 对齐）；四股之和
    的 100 校验留在上游（50503 语义归它）。
    """
    payload = request.get_json(silent=True) or {}

    def _int_in(name, lo, hi):
        value = payload.get(name)
        if isinstance(value, bool) or not isinstance(value, int) or not lo <= value <= hi:
            return None
        return value

    daily_new = _int_in("dailyNewLimit", 0, 50)
    daily_minutes = _int_in("dailyMinutes", 5, 240)
    strands = [_int_in("strandInputPct", 0, 100), _int_in("strandLanguagePct", 0, 100),
               _int_in("strandOutputPct", 0, 100), _int_in("strandFluencyPct", 0, 100)]
    if daily_new is None or daily_minutes is None or any(s is None for s in strands):
        return jsonify({"success": False, "message": "invalid plan settings"}), 400
    return _moonwell_proxy("/learning/plan/settings", {
        "dailyNewLimit": daily_new, "dailyMinutes": daily_minutes,
        "strandInputPct": strands[0], "strandLanguagePct": strands[1],
        "strandOutputPct": strands[2], "strandFluencyPct": strands[3],
    }, 10, "learning plan settings")


@web.route("/ajax/learning/match/books", methods=["GET"])
@user_login_required
def learning_match_books():
    """Proxy the graded-shelf recommendation (R147: 词汇量选阶 → 阶窗口书画像).

    响应 result = {vocabSize, stage, books}；books[].bookId 是本站 Calibre 书 id
    （moon-well 只读直读 metadata.db，与站内同源）。未算/过期的画像上游异步补算、
    立即返回 null 密度，前端按 estimating 展示并轮询。
    """
    return _moonwell_proxy("/learning/match/books", None, 15,
                           "learning match books", method="GET")


@web.route("/ajax/learning/strands/reading", methods=["POST"])
@user_login_required
def learning_strands_reading():
    """Proxy the reading-time heartbeat (R151，moon-well R150 四股台账 INPUT 股).

    payload {"seconds": 30..600, "bookId": "123"?}——阅读器每满 5 分钟批量上报，
    卸载时补发尾巴。域校验与 srs/answer 同款；上游再钳一次并做槽位幂等。
    心跳语义：失败静默不重试（前端已兜底），代理超时给短（5s）避免拖阅读器。
    """
    payload = request.get_json(silent=True) or {}
    seconds = payload.get("seconds")
    if isinstance(seconds, bool) or not isinstance(seconds, int) or not 30 <= seconds <= 600:
        return jsonify({"success": False, "message": "seconds must be an integer 30-600"}), 400
    book_id = payload.get("bookId")
    body = {"seconds": seconds}
    if book_id is not None:
        if isinstance(book_id, bool) or not re.match(r"^\d+$", str(book_id)):
            return jsonify({"success": False, "message": "bookId must be a positive integer"}), 400
        body["bookId"] = str(book_id)
    return _moonwell_proxy("/learning/strands/reading", body, 5, "learning strands reading")


@web.route("/ajax/learning/match/book", methods=["POST"])
@user_login_required
def learning_match_book():
    """Proxy a single-book difficulty profile; payload {"bookId": str}.

    bookId 即本站 Calibre 书 id（R147 起两端同源，moon-well 按 metadata.db 校验）；
    60s：缺失/过期画像走同步计算（分词+词族比对，秒级）。
    """
    payload = request.get_json(silent=True) or {}
    book_id = payload.get("bookId")
    if isinstance(book_id, bool) or not book_id or not re.match(r"^\d+$", str(book_id)):
        return jsonify({"success": False, "message": "bookId must be a positive integer"}), 400
    return _moonwell_proxy("/learning/match/book", {"bookId": str(book_id)}, 60,
                           "learning match book")


@web.route("/ajax/learning/asr/transcribe", methods=["POST"])
@user_login_required
def learning_asr_transcribe():
    """Proxy voice-input transcription（R155 语音输入：录音 multipart 直传转写）。

    浏览器 WebAudio 采集端已编码 16k 单声道 wav（≈32KB/s，3 分钟 <6MB）；
    上限 10MB 与 moon-well maxAudioBytes 对齐，超限本地 400 不打上游。
    """
    upload = request.files.get("file")
    if upload is None or not upload.filename:
        return jsonify({"success": False, "message": "file is required"}), 400
    data = upload.read()
    if not data:
        return jsonify({"success": False, "message": "录音内容为空"}), 400
    if len(data) > 10 * 1024 * 1024:
        return jsonify({"success": False, "message": "录音超过大小上限（10MB）"}), 400
    filename = upload.filename if "." in upload.filename else "recording.wav"
    return _moonwell_multipart("/learning/asr/transcribe", data, filename, 60,
                               "语音转写")
