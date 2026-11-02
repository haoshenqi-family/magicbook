# cps/routes/mail.py — 站内信（mail）域路由（R243）。
#
# Why 独立域：邮件产品入口归 companion，但 mail 的数据事实、分页与已读状态
# 都由 moon-well R228 提供；本仓只做页面入口和登录态薄代理，避免与伙伴/成就/
# 积分各自的业务路由耦合。

from flask import jsonify
from flask import request
from flask_babel import gettext as _

from cps.web import _moonwell_proxy
from cps.web import web
from ..render_template import render_title_template
from ..usermanagement import user_login_required


def _positive_int(raw, default, maximum):
    """把查询参数归一成正整数；非法值回默认，超上限截到上限。"""
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return default
    if value <= 0:
        return default
    return min(value, maximum)


@web.route("/mail", methods=["GET"])
@user_login_required
def mail_inbox_page():
    """完整收件箱页面；数据由 MBMail 经下方薄代理异步加载。"""
    return render_title_template("mail.html", title=_("Mail"))


@web.route("/ajax/mail/unread-count", methods=["GET"])
@user_login_required
def mail_unread_count():
    """Proxy the current user's unresolved unread count."""
    body, status, headers = _moonwell_proxy(
        "/mail/unread-count", None, 10, "mail unread count", method="POST")
    return body, status, headers


@web.route("/ajax/mail/page", methods=["GET"])
@user_login_required
def mail_page_proxy():
    """Proxy a newest-first mail page after normalizing client paging params."""
    page_no = _positive_int(request.args.get("pageNo"), default=1, maximum=100000)
    page_size = _positive_int(request.args.get("pageSize"), default=20, maximum=50)
    body, status, headers = _moonwell_proxy(
        "/mail/page", {"pageNo": page_no, "pageSize": page_size}, 10, "mail page")
    return body, status, headers


@web.route("/ajax/mail/read", methods=["POST"])
@user_login_required
def mail_read():
    """Mark one of the current user's mails read; ownership stays in moon-well."""
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        payload = {}
    mail_id = payload.get("id")
    # Why bool 单独排除：Python 的 bool 是 int 子类，True 不能当邮件 id。
    if not isinstance(mail_id, int) or isinstance(mail_id, bool) or mail_id <= 0:
        return jsonify({"success": False, "message": "id is required"}), 400
    body, status, headers = _moonwell_proxy(
        "/mail/read", {"id": mail_id}, 10, "mail read")
    return body, status, headers


@web.route("/ajax/mail/read-all", methods=["POST"])
@user_login_required
def mail_read_all():
    """Mark all currently unresolved unread mail read for the logged-in user."""
    body, status, headers = _moonwell_proxy(
        "/mail/read-all", {}, 10, "mail read all")
    return body, status, headers
