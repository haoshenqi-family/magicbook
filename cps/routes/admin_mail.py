# cps/routes/admin_mail.py - administrator operation mail (R250, moon-well R230).
#
# Why a separate domain: operation mail has its own page, audience selection,
# campaign history and recall flow. Keeping it out of credit.py avoids
# reintroducing the old "free text only as a credit notification" coupling.

from flask import jsonify
from flask import request
from flask_babel import gettext as _

from cps.web import _moonwell_proxy
from cps.web import web
from ..admin import admin_required
from ..cw_login import current_user
from ..render_template import render_title_template
from ..usermanagement import user_login_required


MAX_RECIPIENTS = 5000
MAX_TITLE_LENGTH = 80
MAX_BODY_LENGTH = 500
MAX_USER_LIMIT = 500
MAX_PAGE_SIZE = 50
ACTION_PATHS = ("/credits", "/buddy", "/achievements", "/learning", "/mail")


def _admin_json_gate():
    """Return a readable JSON 403 instead of an HTML abort for fetch callers."""
    if not current_user.role_admin():
        return jsonify({"success": False, "message": _("Admin only")}), 403
    return None


def _positive_int(raw, default, maximum):
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return default
    if value <= 0:
        return default
    return min(value, maximum)


def _text(value):
    return value.strip() if isinstance(value, str) else ""


def _normalize_audience(payload):
    audience = _text(payload.get("audienceType")).upper()
    if audience not in ("SELECTED", "ALL"):
        return None
    return audience


def _normalize_selected_ids(raw):
    if not isinstance(raw, list):
        return None
    ids = []
    for value in raw:
        # bool is an int subclass in Python and must never become a user id.
        if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
            return None
        if value not in ids:
            ids.append(value)
    return ids


def _normalize_send_payload(payload):
    """Validate locally, then forward only the fields moon-well understands."""
    if not isinstance(payload, dict):
        return None, _("Invalid request")
    audience = _normalize_audience(payload)
    if audience is None:
        return None, _("Audience must be selected users or all users")

    user_ids = _normalize_selected_ids(payload.get("userIds"))
    if audience == "SELECTED":
        if not user_ids:
            return None, _("Select at least one user")
        if len(user_ids) > MAX_RECIPIENTS:
            return None, _("At most 5000 recipients per send")
    else:
        # ALL ignores client ids. Do not forward a caller-provided recipient list.
        user_ids = None

    title = _text(payload.get("title"))
    body = _text(payload.get("body"))
    if not title:
        return None, _("Title is required")
    if len(title) > MAX_TITLE_LENGTH:
        return None, _("Title must be at most 80 characters")
    if not body:
        return None, _("Message body is required")
    if len(body) > MAX_BODY_LENGTH:
        return None, _("Message body must be at most 500 characters")

    action_path = _text(payload.get("actionPath"))
    if action_path and action_path not in ACTION_PATHS:
        return None, _("Invalid destination")

    normalized = {
        "audienceType": audience,
        "title": title,
        "body": body,
        "actionPath": action_path,
    }
    if audience == "SELECTED":
        normalized["userIds"] = user_ids
    return normalized, None


@web.route("/admin/mail", methods=["GET"])
@user_login_required
@admin_required
def admin_mail_page():
    """Administrator-only operation mail composer and campaign history."""
    return render_title_template(
        "admin_mail.html", title=_("Admin Mail"), page="admin_mail")


@web.route("/ajax/admin-mail/users", methods=["GET"])
@user_login_required
def admin_mail_users():
    """Proxy the searchable moon-well user directory for the selected audience."""
    denied = _admin_json_gate()
    if denied:
        return denied
    keyword = _text(request.args.get("keyword"))[:MAX_TITLE_LENGTH]
    limit = _positive_int(request.args.get("limit"), default=100, maximum=MAX_USER_LIMIT)
    body, status, headers = _moonwell_proxy(
        "/mail/admin/users",
        {"keyword": keyword, "limit": limit},
        10,
        "admin mail users",
    )
    return body, status, headers


@web.route("/ajax/admin-mail/audience-count", methods=["GET"])
@user_login_required
def admin_mail_audience_count():
    """Return the current all-user count for an exact audience preview."""
    denied = _admin_json_gate()
    if denied:
        return denied
    body, status, headers = _moonwell_proxy(
        "/mail/admin/audience/count", {}, 10, "admin mail audience count")
    return body, status, headers


@web.route("/ajax/admin-mail/send", methods=["POST"])
@user_login_required
def admin_mail_send():
    """Validate the composer payload locally, then send one moon-well campaign."""
    denied = _admin_json_gate()
    if denied:
        return denied
    payload, error = _normalize_send_payload(request.get_json(silent=True))
    if error:
        return jsonify({"success": False, "message": error}), 400
    body, status, headers = _moonwell_proxy(
        "/mail/admin/send", payload, 30, "admin mail send")
    return body, status, headers


@web.route("/ajax/admin-mail/campaigns", methods=["GET"])
@user_login_required
def admin_mail_campaigns():
    """Proxy a newest-first page of operation mail campaigns."""
    denied = _admin_json_gate()
    if denied:
        return denied
    page_no = _positive_int(request.args.get("pageNo"), default=1, maximum=100000)
    page_size = _positive_int(
        request.args.get("pageSize"), default=20, maximum=MAX_PAGE_SIZE)
    body, status, headers = _moonwell_proxy(
        "/mail/admin/campaigns/page",
        {"pageNo": page_no, "pageSize": page_size},
        10,
        "admin mail campaigns",
    )
    return body, status, headers


@web.route("/ajax/admin-mail/recall", methods=["POST"])
@user_login_required
def admin_mail_recall():
    """Recall one whole campaign; only the positive campaign id crosses the proxy."""
    denied = _admin_json_gate()
    if denied:
        return denied
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        payload = {}
    campaign_id = payload.get("campaignId")
    if (not isinstance(campaign_id, int) or isinstance(campaign_id, bool)
            or campaign_id <= 0):
        return jsonify({"success": False, "message": _("Invalid campaign")}), 400
    body, status, headers = _moonwell_proxy(
        "/mail/admin/recall", {"campaignId": campaign_id}, 10,
        "admin mail recall")
    return body, status, headers
