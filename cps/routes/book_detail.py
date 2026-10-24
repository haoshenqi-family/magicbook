# cps/routes/book_detail.py — R214 书籍详情速览端点（子项 B）。
# 装饰注册沿用 web 蓝图（R181 形制，与 routes/reading.py 同款，endpoint 名不变）。
import zipfile

from flask import jsonify
from flask import request

from cps.web import _llm_task_admin_gate
from cps.web import web
from ..reading_insight import service as insight_service
from ..usermanagement import user_login_required


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
    except (TypeError, ValueError, OSError, zipfile.BadZipFile) as error:
        # 透传上游 message（LLD §8）：失败在区块内红字显示，不静默变「暂无简介」。
        return jsonify({"success": False, "message": str(error)}), 400
