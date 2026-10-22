# cps/routes/buddy.py — 伙伴（buddy）域路由（R206，承接 moon-well R201）。
# 薄代理透传：数据面全在 moon-well /buddy，本站只做入口页 + 代理 + 鉴权转发。
# 装饰注册沿用 web blueprint（endpoint 名 web.*）；依赖符号显式 import。

from cps.web import (
    _moonwell_proxy,
    web,
)
from ..render_template import render_title_template
from ..usermanagement import user_login_required
from flask import jsonify
from flask import request
from flask_babel import gettext as _


@web.route("/buddy", methods=["GET"])
@user_login_required
def buddy_page():
    """伙伴页：花名册 + 领取/切换，数据经 /ajax/buddy/* 异步加载。"""
    return render_title_template("buddy.html", title=_("Buddies"))


@web.route("/ajax/buddy/catalog", methods=["GET"])
@user_login_required
def buddy_catalog():
    """Proxy the buddy catalog (moon-well POST /buddy/catalog).
    含全部伙伴 + 当前用户 owned/equipped/claimable；首次访问触发默认伙伴懒发放。"""
    body, status, headers = _moonwell_proxy("/buddy/catalog", None, 10,
                                            "buddy catalog", method="POST")
    return body, status, headers


@web.route("/ajax/buddy/mine", methods=["GET"])
@user_login_required
def buddy_mine():
    """Proxy the user's owned buddies (moon-well POST /buddy/mine)."""
    body, status, headers = _moonwell_proxy("/buddy/mine", None, 10,
                                            "buddy mine", method="POST")
    return body, status, headers


@web.route("/ajax/buddy/claim", methods=["POST"])
@user_login_required
def buddy_claim():
    """Proxy a buddy claim (moon-well POST /buddy/claim); payload {"code": "..."}."""
    payload = request.get_json(silent=True) or {}
    code = payload.get("code")
    if not code:
        return jsonify({"success": False, "message": "code is required"}), 400
    return _moonwell_proxy("/buddy/claim", {"code": code}, 10, "buddy claim")


@web.route("/ajax/buddy/equip", methods=["POST"])
@user_login_required
def buddy_equip():
    """Proxy equipping a buddy (moon-well POST /buddy/equip); payload {"code": "..."}."""
    payload = request.get_json(silent=True) or {}
    code = payload.get("code")
    if not code:
        return jsonify({"success": False, "message": "code is required"}), 400
    return _moonwell_proxy("/buddy/equip", {"code": code}, 10, "buddy equip")
