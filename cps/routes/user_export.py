# cps/routes/user_export.py — 个人学习数据导出代理（R230，数据主体在 moon-well R220）。
# 装饰注册沿用 web blueprint；产物为密码加密 ZIP，MinIO 保留 7 天（详见 moon-well LLD）。

from cps.web import (
    _moonwell_proxy,
    web,
)
from ..usermanagement import user_login_required
from flask import Response
from flask import jsonify
from flask import request

# 发起/列表都是轻量 JSON；下载是 MinIO 流式聚合的 ZIP（含译文级大字段），放宽到 120s。
_DOWNLOAD_TIMEOUT = 120


@web.route("/ajax/user-export/create", methods=["POST"])
@user_login_required
def user_export_create():
    """发起导出：body {password}。密码只透传 moon-well，本仓不落任何存储。"""
    payload = request.get_json(silent=True) or {}
    password = payload.get("password")
    if not isinstance(password, str) or not 6 <= len(password) <= 128:
        return jsonify(success=False, message="password must be 6-128 characters"), 400
    return _moonwell_proxy("/export/learning-data", {"password": password},
                           30, "user export create")


@web.route("/ajax/user-export/tasks", methods=["GET"])
@user_login_required
def user_export_tasks():
    """近 30 天导出任务列表（状态/大小/过期时间），供 /me 页轮询。"""
    return _moonwell_proxy("/export/learning-data/tasks", None,
                           30, "user export tasks", method="GET")


@web.route("/ajax/user-export/tasks/<int:task_id>/download", methods=["GET"])
@user_login_required
def user_export_download(task_id):
    """代理流式下载加密 ZIP；非 200 时透传后端错误 JSON（Result 包装，前端可读 message）。"""
    result = _moonwell_proxy("/export/learning-data/tasks/%d/download" % task_id, None,
                             _DOWNLOAD_TIMEOUT, "user export download",
                             binary=True, method="GET")
    body, status = result[0], result[1]
    if status != 200:
        return body, status
    response = Response(body, status=200, mimetype="application/zip")
    response.headers["Content-Disposition"] = \
        'attachment; filename="my-learning-data-%d.zip"' % task_id
    return response
