# cps/routes/credit.py — credit 域定制路由（R181，架构评审 B2 自 cps.web 迁出）。
# 装饰注册沿用原 web blueprint（endpoint 名不变）；依赖的辅助符号显式列于 import。

from cps.web import (
    _moonwell_proxy,
    web,
)
from ..cw_login import current_user
from ..render_template import render_title_template
from ..usermanagement import user_login_required
from flask import jsonify
from flask import redirect
from flask import request
from flask import url_for
from flask_babel import gettext as _
from flask_limiter.util import get_remote_address
from cps import limiter


@web.route("/ajax/achievements-summary", methods=["GET"])
@user_login_required
def achievements_summary():
    """Proxy the achievement summary (level / XP / badge counts / streak)."""
    body, status, headers = _moonwell_proxy("/achievements/summary", None, 10,
                                            "achievements summary", method="POST")
    return body, status, headers


@web.route("/ajax/achievements-detail", methods=["GET"])
@user_login_required
def achievements_detail():
    """Proxy the achievement detail list; query param category=READ|VOCAB|STREAK."""
    category = request.args.get("category", "")
    payload = {"category": category} if category else {}
    body, status, headers = _moonwell_proxy("/achievements/detail", payload, 10,
                                            "achievements detail")
    return body, status, headers


@web.route("/ajax/achievements-pending", methods=["GET"])
@user_login_required
def achievements_pending():
    """Proxy the pending (unlocked but unclaimed) achievements for polling."""
    body, status, headers = _moonwell_proxy("/achievements/pending", None, 10,
                                            "achievements pending", method="POST")
    return body, status, headers


@web.route("/ajax/achievements-claim", methods=["POST"])
@user_login_required
def achievements_claim():
    """Proxy the achievement claim; payload {"code": "..."}."""
    payload = request.get_json(silent=True) or {}
    code = payload.get("code")
    if not code:
        return jsonify({"success": False, "message": "code is required"}), 400
    return _moonwell_proxy("/achievements/claim", {"code": code}, 10,
                           "achievements claim")


@web.route("/subscription", methods=["GET"])
@user_login_required
def subscription_page():
    """Deprecated: 订阅页已由积分充值页取代（套餐暂时隐藏），重定向保兼容。"""
    return redirect(url_for("web.credits_page"))


@web.route("/ajax/subscription/plans", methods=["GET"])
@user_login_required
def subscription_plans():
    """Proxy the purchasable plan list (moon-well /api/saas/plan/list)."""
    body, status, headers = _moonwell_proxy("/api/saas/plan/list", None, 10,
                                            "subscription plans", method="GET")
    return body, status, headers


@web.route("/ajax/subscription/current", methods=["GET"])
@user_login_required
def subscription_current():
    """Proxy the user's current subscription (moon-well /api/saas/subscription/current)."""
    body, status, headers = _moonwell_proxy("/api/saas/subscription/current", None, 10,
                                            "subscription status", method="GET")
    return body, status, headers


@web.route("/ajax/subscription/order", methods=["POST"])
@user_login_required
@limiter.limit("10/minute", key_func=get_remote_address)
def subscription_create_order():
    """Proxy order creation (moon-well /api/saas/order/create); payload {"planId": N}."""
    payload = request.get_json(silent=True) or {}
    plan_id = payload.get("planId")
    # Why: 上游 CreateOrderRequest.planId 是 Long，非正整数直接拒绝，避免打到 moon-well 才报错
    if not isinstance(plan_id, int) or isinstance(plan_id, bool) or plan_id <= 0:
        return jsonify({"success": False, "message": "planId is required"}), 400
    return _moonwell_proxy("/api/saas/order/create", {"planId": plan_id}, 10,
                           "subscription order")


@web.route("/ajax/subscription/pay", methods=["POST"])
@user_login_required
@limiter.limit("10/minute", key_func=get_remote_address)
def subscription_pay():
    """Proxy Alipay precreate (moon-well /api/saas/payment/alipay/precreate);
    payload {"orderNo": "..."} -> result.qrCode 为二维码内容串。"""
    payload = request.get_json(silent=True) or {}
    order_no = payload.get("orderNo")
    if not order_no:
        return jsonify({"success": False, "message": "orderNo is required"}), 400
    # Why: 预下单在 moon-well 侧同步调用支付宝网关，超时给足外呼预算
    return _moonwell_proxy("/api/saas/payment/alipay/precreate", {"orderNo": order_no}, 15,
                           "subscription payment")


@web.route("/ajax/subscription/order-status", methods=["POST"])
@user_login_required
def subscription_order_status():
    """Proxy order polling (moon-well /api/saas/payment/alipay/query);
    moon-well 侧对待支付订单主动查支付宝补偿落账，返回最新订单体。"""
    payload = request.get_json(silent=True) or {}
    order_no = payload.get("orderNo")
    if not order_no:
        return jsonify({"success": False, "message": "orderNo is required"}), 400
    return _moonwell_proxy("/api/saas/payment/alipay/query", {"orderNo": order_no}, 15,
                           "subscription order status")


@web.route("/credits", methods=["GET"])
@user_login_required
def credits_page():
    """积分充值页：余额 + 档位 + 支付宝扫码收银台，数据经 /ajax/credit-* 异步加载。"""
    return render_title_template("credits.html", title=_("Credits"))


@web.route("/ajax/credit/account", methods=["POST"])
@user_login_required
def credit_account():
    """Proxy the user's credit balance (moon-well POST /credit/account)."""
    body, status, headers = _moonwell_proxy("/credit/account", None, 10,
                                            "credit account", method="POST")
    return body, status, headers


@web.route("/ajax/credit/packages", methods=["GET"])
@user_login_required
def credit_packages():
    """Proxy the recharge package list (moon-well GET /credit/recharge/packages)."""
    body, status, headers = _moonwell_proxy("/credit/recharge/packages", None, 10,
                                            "credit packages", method="GET")
    return body, status, headers


@web.route("/ajax/credit/recharge-order", methods=["POST"])
@user_login_required
@limiter.limit("10/minute", key_func=get_remote_address)
def credit_recharge_order():
    """Proxy recharge order creation (moon-well POST /credit/recharge/order);
    payload {"packageId": "..."}，金额/积分由 moon-well 按档位决定。"""
    payload = request.get_json(silent=True) or {}
    package_id = payload.get("packageId")
    if not package_id:
        return jsonify({"success": False, "message": "packageId is required"}), 400
    return _moonwell_proxy("/credit/recharge/order", {"packageId": package_id}, 10,
                           "credit recharge order")


@web.route("/ajax/credit/recharge-pay", methods=["POST"])
@user_login_required
@limiter.limit("10/minute", key_func=get_remote_address)
def credit_recharge_pay():
    """Proxy Alipay precreate (moon-well POST /credit/recharge/pay);
    payload {"orderNo": "..."} -> result.qrCode 为二维码内容串。"""
    payload = request.get_json(silent=True) or {}
    order_no = payload.get("orderNo")
    if not order_no:
        return jsonify({"success": False, "message": "orderNo is required"}), 400
    # Why: 预下单在 moon-well 侧同步调用支付宝网关，超时给足外呼预算
    return _moonwell_proxy("/credit/recharge/pay", {"orderNo": order_no}, 15,
                           "credit recharge payment")


@web.route("/ajax/credit/recharge-status", methods=["POST"])
@user_login_required
def credit_recharge_status():
    """Proxy recharge polling (moon-well POST /credit/recharge/status);
    moon-well 侧对待支付充值单主动查支付宝补偿发放，返回最新充值单体。"""
    payload = request.get_json(silent=True) or {}
    order_no = payload.get("orderNo")
    if not order_no:
        return jsonify({"success": False, "message": "orderNo is required"}), 400
    return _moonwell_proxy("/credit/recharge/status", {"orderNo": order_no}, 15,
                           "credit recharge status")


@web.route("/ajax/credit/admin-adjust", methods=["POST"])
@user_login_required
def credit_admin_adjust():
    """Proxy admin credit adjustment (moon-well POST /credit/admin/adjust, R54).

    Front-end gate: only admins see the entry; moon-well re-checks its own
    admin whitelist server-side (defense in depth).
    """
    if not current_user.role_admin():
        return jsonify({"success": False, "message": "admin only"}), 403
    payload = request.get_json(silent=True) or {}
    return _moonwell_proxy("/credit/admin/adjust", payload, 10,
                           "credit admin adjust")


@web.route("/ajax/credit/consume-page", methods=["POST"])
@user_login_required
def credit_consume_page():
    """Proxy the user's credit consume detail page (moon-well POST /credit/consume/page);
    payload {pageNo,pageSize,caller,model,startDate,endDate}，全部可选。"""
    payload = request.get_json(silent=True) or {}
    return _moonwell_proxy("/credit/consume/page", payload, 10,
                           "credit consume page")


@web.route("/ajax/credit/consume-summary", methods=["POST"])
@user_login_required
def credit_consume_summary():
    """Proxy the user's credit consume summary (moon-well POST /credit/consume/summary);
    payload 与 consume-page 相同的过滤条件，返回合计 + 按模块/按模型分组。"""
    payload = request.get_json(silent=True) or {}
    return _moonwell_proxy("/credit/consume/summary", payload, 10,
                           "credit consume summary")
