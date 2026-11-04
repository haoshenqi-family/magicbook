# -*- coding: utf-8 -*-

# cps/routes/library_submission.py — R279 用户投稿域路由。
# 装饰注册沿用 web 蓝图（R181 形制，与 routes/buddy.py 同款）。
#
# Why 不动 editbooks：投稿与上游 `/upload` 是两条权限模型（登录即可 vs
# ROLE_UPLOAD），混在同一个蓝图里会让「谁能上传」的判定出现两个真源。
# 限流（防灌桶）挂在 submit 上：limiter 在生产可用，测试环境可能未初始化，
# 经 _rate_limit() 条件包装。

from urllib.parse import quote

from flask import Response, jsonify, request
from flask_babel import gettext as _

from cps.web import web
from cps import limiter
from .. import logger
from ..cw_login import current_user
from ..library_submission import service, storage
from ..library_submission.service import SubmissionError
from ..render_template import render_title_template
from ..usermanagement import user_login_required
from ..admin import admin_required

log = logger.create()

_SUBMIT_RATE = "5/hour"


def _user_id():
    return int(current_user.id)


def _rate_limit(view):
    """条件限流：limiter 未初始化（测试环境）时原样返回视图。"""
    if limiter is None:
        return view
    from flask_limiter.util import get_remote_address
    return limiter.limit(_SUBMIT_RATE, key_func=get_remote_address)(view)


@web.route("/ajax/library/submit", methods=["POST"])
@user_login_required
@_rate_limit
def library_submit():
    """用户投稿：multipart file，落 MinIO 暂存 + PENDING 台账，不入书库。"""
    try:
        upload = request.files.get("file")
        if upload is None or not upload.filename:
            return jsonify({"success": False, "message": "file is required"}), 400
        # 声明必勾：审核通过即站点发布，版权责任要用户先自认。
        if (request.form.get("declaration") or "").lower() not in ("1", "true", "yes"):
            return jsonify({"success": False,
                            "message": _("You must confirm you have the right to share this file.")}), 400
        row, created = service.create_submission(_user_id(), upload)
        return jsonify({"success": True, "result": dict(row, created=created)})
    except SubmissionError as error:
        return jsonify({"success": False, "message": error.message}), error.status
    except Exception as unexpected:  # noqa: BLE001 —— 存储故障必须可见
        log.error("library submit failed: %s", unexpected)
        return jsonify({"success": False,
                        "message": _("Submission storage is temporarily unavailable.")}), 503


@web.route("/ajax/library/submissions/mine", methods=["GET"])
@user_login_required
def library_my_submissions():
    """我的投稿列表（用户侧状态查询）。"""
    return jsonify({"success": True,
                    "result": service.list_submissions_of_user(_user_id())})


# ---- 管理侧 ----------------------------------------------------------------

@web.route("/admin/submissions", methods=["GET"])
@user_login_required
@admin_required
def admin_submissions_page():
    """审核页：列表 + 预览 + 通过/驳回。"""
    return render_title_template("admin_submissions.html",
                                 title=_("Book Submissions"),
                                 page="admin_submissions")


@web.route("/ajax/admin/submissions", methods=["GET"])
@user_login_required
@admin_required
def admin_submissions_list():
    return jsonify({"success": True, "result": service.list_submissions()})


@web.route("/ajax/admin/submissions/<int:submission_id>/preview", methods=["GET"])
@user_login_required
@admin_required
def admin_submission_preview(submission_id):
    """同源代理预览：管理员在审核页直接下载暂存对象核验内容。

    Why 同源代理而不是 MinIO 直链：暂存前缀绝不能加进匿名只读 Statement
    （R201/R207 只放开 buddy/ 与 ted-audio/），预览必须走服务端签名读。
    """
    try:
        resp, row = service.preview_stream(submission_id)
    except SubmissionError as error:
        return jsonify({"success": False, "message": error.message}), error.status
    except Exception as upstream_error:  # noqa: BLE001
        log.error("submission preview failed: %s", upstream_error)
        return jsonify({"success": False,
                        "message": _("Submission storage is temporarily unavailable.")}), 503

    filename = row.original_filename or "submission.bin"
    def _stream():
        try:
            for chunk in resp.stream(64 * 1024):
                yield chunk
        finally:
            resp.close()
            resp.release_conn()
    response = Response(_stream())
    response.headers["Content-Type"] = "application/octet-stream"
    response.headers["Content-Disposition"] = (
        u"attachment; filename*=UTF-8''{}".format(quote(filename)))
    response.headers["Cache-Control"] = "no-store"
    return response


@web.route("/ajax/admin/submissions/<int:submission_id>/review", methods=["POST"])
@user_login_required
@admin_required
def admin_submission_review(submission_id):
    payload = request.get_json(silent=True) or {}
    approve = payload.get("approve")
    if not isinstance(approve, bool):
        return jsonify({"success": False, "message": "approve must be boolean"}), 400
    note = str(payload.get("note") or "")[:2000]
    try:
        row = service.review(submission_id, _user_id(), approve, note)
    except SubmissionError as error:
        return jsonify({"success": False, "message": error.message}), error.status
    return jsonify({"success": True, "result": row})
