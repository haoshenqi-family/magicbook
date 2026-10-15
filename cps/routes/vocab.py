# cps/routes/vocab.py — vocab 域定制路由（R181，架构评审 B2 自 cps.web 迁出）。
# 装饰注册沿用原 web blueprint（endpoint 名不变）；依赖的辅助符号显式列于 import。

from cps.web import (
    _LLM_TASK_PATHS,
    _llm_task_admin_gate,
    _moonwell_proxy,
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
