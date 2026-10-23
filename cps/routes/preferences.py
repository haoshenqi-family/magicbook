# cps/routes/preferences.py — 账号级 UI 偏好代理（R216，承接 moon-well R207）。
# 引导已读与阅读器主题存 moon-well user_ui_settings，本站只做鉴权转发；
# 失败原样透传（401/503/业务错误），不包装成「数据不存在」。

from flask import jsonify, request

from cps.web import _moonwell_proxy, web
from ..usermanagement import user_login_required

# 与 moon-well UserUiSettingsService.READER_THEMES 同源；customTheme 只存本机。
_READER_THEMES = {"lightTheme", "darkTheme", "sepiaTheme", "amberTheme", "blackTheme"}


@web.route("/ajax/ui-settings", methods=["GET"])
@user_login_required
def ui_settings_get():
    """读取账号级 UI 偏好（引导已读 / 内置主题）。"""
    return _moonwell_proxy("/user/ui-settings", None, 8,
                           "ui settings", method="GET")


@web.route("/ajax/ui-settings/onboarding/close", methods=["POST"])
@user_login_required
def ui_settings_close_onboarding():
    """关闭/结束引导（幂等）。"""
    return _moonwell_proxy("/user/ui-settings/onboarding/close", None, 8,
                           "ui settings onboarding close")


@web.route("/ajax/ui-settings/reader-theme", methods=["POST"])
@user_login_required
def ui_settings_update_reader_theme():
    """保存内置阅读主题；非法值在代理层挡成 400，不送上游。"""
    payload = request.get_json(silent=True) or {}
    theme = payload.get("theme")
    if theme not in _READER_THEMES:
        return jsonify({"success": False, "message": "unsupported reader theme"}), 400
    return _moonwell_proxy("/user/ui-settings/reader-theme", {"theme": theme}, 8,
                           "ui settings reader theme")
