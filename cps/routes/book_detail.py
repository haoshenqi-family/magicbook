# cps/routes/book_detail.py — R214 书籍详情速览端点（子项 B）。
# 装饰注册沿用 web 蓝图（R181 形制，与 routes/reading.py 同款，endpoint 名不变）。
import traceback
import zipfile

from flask import jsonify
from flask import request

from cps.web import _credit_billing_rates
from cps.web import _llm_task_admin_gate
from cps.web import _whole_book_closures
from cps.web import _word_detail_closures
from cps.web import web
from .. import logger
from ..reading_insight import service as insight_service
from ..usermanagement import user_login_required

log = logger.create()


@web.route("/ajax/book-insight", methods=["GET"])
@user_login_required
def book_insight():
    """速览 payload（LLD §4.1）：详情页三区块与后续代价面板共用的一次解析结果。

    Why 既有详情页也走同一入口：服务端渲染与 ajax 拉取只有一个真源，
    「面板的量」与「页面上的目录」永远不可能对不上。
    """
    try:
        book_id = int(request.args.get("book_id"))
        book_format = (request.args.get("book_format") or "epub").lower()
        return jsonify({"success": True,
                        "result": insight_service.get_or_build(book_id, book_format)})
    except (TypeError, ValueError, OSError, zipfile.BadZipFile) as error:
        return jsonify({"success": False, "message": str(error)}), 400


@web.route("/ajax/book-summary", methods=["POST"])
@user_login_required
def book_summary():
    """AI 简介生成（LLD §4.2）：admin + _llm_task_admin_gate，拍板⑦无「重新生成」。

    Why 门禁双层：这里只挡 UI 入口（JSON 形态返回可读文案），真正的白名单
    在 moon-well 侧二检（ai.llm.task-manual-run.admin-user-ids），纵深防御同 R126。
    """
    denied = _llm_task_admin_gate()
    if denied is not None:
        return denied
    payload = request.get_json(silent=True) or {}
    try:
        book_id = int(payload.get("book_id"))
        book_format = str(payload.get("book_format") or "epub").lower()
        result = insight_service.generate_summary(book_id, book_format)
        return jsonify({"success": True, "result": result})
    except insight_service.UpstreamServiceError as error:
        # Why 502 而不是 400：请求本身合法，是 moon-well/Magpie 未能完成生成。
        # 透传上游 message（LLD §8），同时让浏览器与监控看到依赖故障。
        log.warning("book summary upstream failed: book=%s status=%s message=%s",
                    payload.get("book_id"), error.status, error)
        return jsonify({"success": False, "message": str(error)}), 502
    except (TypeError, ValueError, OSError, zipfile.BadZipFile) as error:
        # 仅本地可判定的入参/文件问题才回 400；上游故障由上一分支处理。
        return jsonify({"success": False, "message": str(error)}), 400


@web.route("/ajax/whole-book-estimate", methods=["POST"])
@user_login_required
def whole_book_estimate():
    """整本任务代价估算（LLD §4.3）：**只读**，绝不建批次、不 publish、不写缓存。

    Why 闭包在路由层造：lookup / check 都要在请求线程内定格 moon-well 令牌快照，
    service 因此不认识 HTTP（与整本翻译 start 同一形制）。
    Why 仍要 admin 门禁：三个整本入口本就管理员专属（R214 拍板①），
    面板只是它们的调用方，不能变成绕过门禁的旁路。
    """
    denied = _llm_task_admin_gate()
    if denied is not None:
        return denied
    payload = request.get_json(silent=True) or {}
    try:
        book_id = int(payload.get("book_id"))
        book_format = str(payload.get("book_format") or "epub").lower()
        kind = str(payload.get("kind") or "translate")
        lookup = check = None
        if kind == "translate":
            _, lookup = _whole_book_closures()
        elif kind == "wordDetail":
            # 只取 check：预览路径没有 publish 能力（R176 的结构约束）。
            check, _ = _word_detail_closures()
        elif kind != "tts":
            raise ValueError("unsupported estimate kind: %s" % kind)
        result = insight_service.estimate(book_id, book_format, kind,
                                          lookup=lookup, check=check,
                                          rates=_credit_billing_rates())
        return jsonify({"success": True, "result": result})
    except (TypeError, ValueError, OSError, zipfile.BadZipFile) as error:
        return jsonify({"success": False, "message": str(error)}), 400
    except Exception as error:      # noqa: BLE001 — 兜底只为「让失败可读」，不是为了吞掉它
        # Why 兜底而不是让它 500：面板拿到裸 500 时只会显示「估算失败：500 」，管理员
        # 既不知道是解析失败还是库挂了，也不知道该不该重试；排查只能靠捞容器日志。
        # 这里既落 traceback（服务端可查），又把异常类型与消息透给前端（界面可读）。
        log.error("whole-book estimate failed: book=%s kind=%s\n%s",
                  payload.get("book_id"), payload.get("kind"), traceback.format_exc())
        return jsonify({"success": False,
                        "message": "{0}: {1}".format(type(error).__name__, error)}), 500
