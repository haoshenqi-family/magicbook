# cps/routes/vocab.py — vocab 域定制路由（R181，架构评审 B2 自 cps.web 迁出）。
# 装饰注册沿用原 web blueprint（endpoint 名不变）；依赖的辅助符号显式列于 import。

from cps.web import (
    _LLM_TASK_PATHS,
    _llm_task_admin_gate,
    _moonwell_proxy,
    _READING_WORD_RE,
    _vt_positive_int,
    web,
)
from ..admin import admin_required
from ..render_template import render_title_template
from ..usermanagement import user_login_required
from flask import jsonify
from flask import request
from flask_babel import gettext as _


@web.route("/ajax/vocab-test/start", methods=["POST"])
@user_login_required
def vocab_test_start():
    """Proxy the vocab size test start: creates a session and returns the first question.

    R154 细筛：body {"refine": true} 透传为上游 start 的细筛开关；只认显式布尔 true，
    其余（缺省/其他类型）一律按标准测试转发空体——代理不替用户解释字段。
    旧客户端不带 body，行为不变。

    Why 原样 return 而不解包：_moonwell_proxy 的失败分支返回 (jsonify, 503) 二元组
    （未配置 / RequestException），解包三元组会抛 ValueError 变成 500 白页；
    Flask 视图对两种返回形态都能直接透传。
    """
    payload = request.get_json(silent=True) or {}
    body = {"refine": True} if payload.get("refine") is True else {}
    return _moonwell_proxy("/vocabulary/test/start", body, 10, "vocab test start")


@web.route("/ajax/vocab-test/answer", methods=["POST"])
@user_login_required
def vocab_test_answer():
    """Proxy one answer; payload {"sessionId": id, "seq": N, "answer": 0|1}.

    Why 必透传 seq：它是后端区分「同题重发（幂等回放）」与「跳题（50304）」的唯一依据，
    代理层丢掉它会让断网重试变成串序污染。请求体不含 word——题面由服务端按 seq 定位。
    """
    payload = request.get_json(silent=True) or {}
    session_id = _vt_positive_int(payload.get("sessionId"))
    seq = _vt_positive_int(payload.get("seq"))
    answer = payload.get("answer")
    if session_id is None:
        return jsonify({"success": False,
                        "message": "sessionId must be a positive integer"}), 400
    if seq is None:
        return jsonify({"success": False, "message": "seq must be a positive integer"}), 400
    if isinstance(answer, bool) or answer not in (0, 1):
        return jsonify({"success": False, "message": "answer must be 0 or 1"}), 400
    # 5s：答题是一次内存态机重放 + 单行 insert，短超时快失败（用户正等着下一题）
    return _moonwell_proxy("/vocabulary/test/answer",
                           {"sessionId": session_id, "seq": seq, "answer": answer},
                           5, "vocab test answer")


@web.route("/ajax/vocab-test/finish", methods=["POST"])
@user_login_required
def vocab_test_finish():
    """Proxy the submit; payload {"sessionId": id, "addUnknownToNotebook": bool}.

    Why 开关必填：它决定不认识词是否进生词本，允许缺省等于替用户决定（后端 DTO 同口径）。
    """
    payload = request.get_json(silent=True) or {}
    session_id = _vt_positive_int(payload.get("sessionId"))
    add_unknown = payload.get("addUnknownToNotebook")
    if session_id is None:
        return jsonify({"success": False,
                        "message": "sessionId must be a positive integer"}), 400
    if not isinstance(add_unknown, bool):
        return jsonify({"success": False,
                        "message": "addUnknownToNotebook must be true or false"}), 400
    return _moonwell_proxy("/vocabulary/test/finish",
                           {"sessionId": session_id, "addUnknownToNotebook": add_unknown},
                           10, "vocab test finish")


@web.route("/ajax/vocab-test/history", methods=["GET"])
@user_login_required
def vocab_test_history():
    """Proxy the recent finished sessions (backend already caps at 10, newest first).

    原样透传（同 vocab_test_start）：解包三元组会让上游不可达时变成 500 白页，
    而这份数据只是卡片摘要，前端拿到任何非 2xx 都静默降级为无历史态。
    """
    return _moonwell_proxy("/vocabulary/test/history", None, 10,
                           "vocab test history", method="GET")


@web.route("/llm-tasks", methods=["GET"])
@user_login_required
@admin_required
def llm_task_runner_page():
    return render_title_template("llm_tasks.html", title=(_("LLM Task Runner")), page="llm_tasks")


@web.route("/ajax/llm-task/options", methods=["POST"])
@user_login_required
def llm_task_options():
    """拉取面板初始数据：供应商/模型候选、并发与上限、队列现状、活跃 run。"""
    denied = _llm_task_admin_gate()
    if denied is not None:
        return denied
    return _moonwell_proxy(_LLM_TASK_PATHS["options"], {}, 15, "llm task options")


@web.route("/ajax/llm-task/run", methods=["POST"])
@user_login_required
def llm_task_run():
    """受理一批手动执行（moon-well 立即返回 runId，执行在其进程内异步进行）。

    Why 请求体原样透传不做字段映射：前端直接按 moon-well 的 DTO 命名
    （provider/model/concurrency/maxTasks/caller/taskType/replayFailed）提交，
    多一层 snake_case 映射只会让两边的契约漂移无人发现；范围校验由
    moon-well 服务端夹取（并发硬上限、上限夹取、taskType 白名单）。
    """
    denied = _llm_task_admin_gate()
    if denied is not None:
        return denied
    payload = request.get_json(silent=True) or {}
    return _moonwell_proxy(_LLM_TASK_PATHS["run"], payload, 15, "llm task run")


@web.route("/ajax/llm-task/status", methods=["POST"])
@user_login_required
def llm_task_status():
    denied = _llm_task_admin_gate()
    if denied is not None:
        return denied
    payload = request.get_json(silent=True) or {}
    return _moonwell_proxy(_LLM_TASK_PATHS["status"], payload, 10, "llm task status")


@web.route("/ajax/llm-task/stop", methods=["POST"])
@user_login_required
def llm_task_stop():
    denied = _llm_task_admin_gate()
    if denied is not None:
        return denied
    payload = request.get_json(silent=True) or {}
    return _moonwell_proxy(_LLM_TASK_PATHS["stop"], payload, 15, "llm task stop")


# --------------------------------------------------------------------
# R130（队列监控四区块，对齐 moon-well R118）：以下六个端点与上面四个同款薄代理。
# 请求体原样透传不做字段映射（caller/sinceHours/pageNo/confirm 等直接对齐 moon-well
# DTO 命名）；keyword 必须搭配 caller/status/errorCode/userId 之一的防全表扫约束在
# moon-well 服务端强制，前端只做提前提示。真正的白名单二检仍在 moon-well 侧。
# --------------------------------------------------------------------


@web.route("/ajax/llm-task/admin-overview", methods=["POST"])
@user_login_required
def llm_task_overview():
    """队列总览：全局计数、caller 分组、近 24h 吞吐、stale/reclaim 预警（无入参）。"""
    denied = _llm_task_admin_gate()
    if denied is not None:
        return denied
    return _moonwell_proxy(_LLM_TASK_PATHS["overview"], {}, 10, "llm task overview")


@web.route("/ajax/llm-task/admin-failures", methods=["POST"])
@user_login_required
def llm_task_failures():
    """失败原因分类：{caller?, sinceHours?}，sinceHours 默认 24、上限 168 由服务端夹取。"""
    denied = _llm_task_admin_gate()
    if denied is not None:
        return denied
    payload = request.get_json(silent=True) or {}
    return _moonwell_proxy(_LLM_TASK_PATHS["failures"], payload, 15, "llm task failures")


@web.route("/ajax/llm-task/admin-page", methods=["POST"])
@user_login_required
def llm_task_admin_page():
    """任务分页查询（瘦行）：过滤字段与分页参数透传，pageSize 由服务端夹 1-50。"""
    denied = _llm_task_admin_gate()
    if denied is not None:
        return denied
    payload = request.get_json(silent=True) or {}
    return _moonwell_proxy(_LLM_TASK_PATHS["admin_page"], payload, 10, "llm task admin page")


@web.route("/ajax/llm-task/detail", methods=["POST"])
@user_login_required
def llm_task_detail():
    """任务详情全文：{taskId}。归属校验在 moon-well 对管理员放行（R118），代理侧仍限 admin。"""
    denied = _llm_task_admin_gate()
    if denied is not None:
        return denied
    payload = request.get_json(silent=True) or {}
    return _moonwell_proxy(_LLM_TASK_PATHS["task_detail"], payload, 10, "llm task detail")


@web.route("/ajax/llm-task/admin-recovery-plan", methods=["POST"])
@user_login_required
def llm_task_recovery_plan():
    """恢复预案（只读）：{caller, errorCode?, category?, limit}——confirm 恒由前端不发，
    带不带都由 moon-well 兜底（非 true 只回 PLAN 零写库）。"""
    denied = _llm_task_admin_gate()
    if denied is not None:
        return denied
    payload = request.get_json(silent=True) or {}
    return _moonwell_proxy(_LLM_TASK_PATHS["recovery_plan"], payload, 20, "llm task recovery plan")


@web.route("/ajax/llm-task/admin-republish-failed", methods=["POST"])
@user_login_required
def llm_task_republish():
    """执行重发失败（唯一写路径，不可逆消耗模型配额）：前端二次确认后才带 confirm:true。"""
    denied = _llm_task_admin_gate()
    if denied is not None:
        return denied
    payload = request.get_json(silent=True) or {}
    return _moonwell_proxy(_LLM_TASK_PATHS["republish"], payload, 30, "llm task republish failed")


_DETAIL_CACHED_BATCH_MAX = 50  # 与 moon-well WordDetailService.CACHE_BATCH_CAP 同口径


@web.route("/ajax/vocabulary/detail-cached-batch", methods=["POST"])
@user_login_required
def vocabulary_detail_cached_batch():
    """滚动复习批量取「已缓存详解」（R289，对端 moon-well R248）：只读缓存，绝不触发生成。

    payload {"words": [...]} → moon-well POST /vocabulary/detail/cached-batch，
    result 键 = 归一请求词，未命中词不出现——前端对缺词降级为简卡。

    Why 不复用 /ajax/reading-word-detail（R123 逐词详解）：那个端点缓存 miss 会
    现场生成（计费 + 15~30s），滚动复习是无人操作的高频被动轮播，批量 20 词里
    每一个 miss 都是一次隐藏下单——所以这里只走只读批量端点，语义在路由名里钉死
    （detail-cached-batch，与计费链路 reading-word-detail 无公共前缀混淆）。
    Why 词形白名单照搬 _READING_WORD_RE：词会进 moon-well 的 ES term 查询，
    与 word_mark 同一防线；弯撇号归一后非法词直接丢弃而不是报错——轮播容错，
    个别脏词不值得让整批失败。
    """
    payload = request.get_json(silent=True) or {}
    words = payload.get("words")
    if not isinstance(words, list):
        return jsonify({"success": False, "message": "words must be a list"}), 400
    cleaned, seen = [], set()
    for raw in words:
        if not isinstance(raw, str):
            continue
        word = raw.strip().replace("\u2019", "'").lower()
        if not word or word in seen or len(word) > 64 or not _READING_WORD_RE.match(word):
            continue
        seen.add(word)
        cleaned.append(word)
        if len(cleaned) >= _DETAIL_CACHED_BATCH_MAX:
            break
    if not cleaned:
        return jsonify({"success": True, "result": {}})
    return _moonwell_proxy("/vocabulary/detail/cached-batch", {"words": cleaned}, 10,
                           "vocabulary detail cached batch")
