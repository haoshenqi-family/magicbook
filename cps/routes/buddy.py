# cps/routes/buddy.py — 伙伴（buddy）域路由（R206，承接 moon-well R201）。
# 薄代理透传：数据面全在 moon-well /buddy，本站只做入口页 + 代理 + 鉴权转发。
# 装饰注册沿用 web blueprint（endpoint 名 web.*）；依赖符号显式 import。

from cps.web import (
    _moonwell_proxy,
    web,
)
from ..render_template import render_title_template
from ..usermanagement import user_login_required
import json

from flask import jsonify
from flask import Response
from flask import request
from flask_babel import gettext
from flask_babel import gettext as _
from ..cw_login import current_user
import requests as http_requests


# R220 验收现场：个别浏览器环境（本机 Chrome 的拦截类扩展）会把跨站图片子资源
# 直接 ERR_BLOCKED_BY_CLIENT，MinIO 直链在页内全部裂图而 CSP 并未拦截。伙伴头像
# 属强感知 UI，改走同源代理：只放行 MinIO 公网两个入口下的 /magicbook/buddy/ 前缀，
# 防滥用（SSRF/开放代理）靠白名单 + 登录 + GET-only。
_BUDDY_IMAGE_HOSTS = ("https://minio.haoshenqi.top", "https://home.haoshenqi.top:9001")
_BUDDY_IMAGE_PATH_PREFIX = "/magicbook/buddy/"

# 伙伴悬浮球 hover 快捷动作（类 iPhone 悬浮球）。动作全集 = 阅读页顶栏工具 +
# 站点导航；「对话」固定占一位。配置存 view_settings['buddy']['quickActions']。
# R234：「AI 对话恒在第一位且不可删除」是服务端不变量，不只靠前端约定——写入与
# 读回都经 _pin_chat_first 归一，直连 API 存成 chat 缺失 / 错位的旧值一律被纠正。
QUICK_ACTION_IDS = (
    "chat", "immersive-translate", "tts-book", "bookmark",
    "learning", "library", "me",
    # R294 扩展专有三项（magiclens 悬浮球同源配置，真值在 moon-well R260 白名单）：
    # 宿主球不渲染（ai_chat.js 按 HOST_ACTION_IDS 过滤），buddy 页 chips 带「仅扩展」标
    "highlight", "page-translate", "review",
)
QUICK_ACTION_PINNED = "chat"
QUICK_ACTION_MIN = 4
QUICK_ACTION_MAX = 5
QUICK_ACTION_LABEL_IDS = {
    "chat": "Chat",
    "immersive-translate": "Translation",
    "tts-book": "Read aloud",
    "bookmark": "Bookmark",
    "learning": "Daily Learning",
    "library": "Library",
    "me": "Me",
    "highlight": "Word highlight",
    "page-translate": "Page translate",
    "review": "Review card",
}
# 仅扩展球存在的动作（buddy 页 chip 标「仅扩展」，宿主球未知 id 一律跳过）
QUICK_ACTION_EXT_ONLY = ("highlight", "page-translate", "review")
# 宿主球认识的动作全集（ai_chat.js 渲染过滤用；与扩展 registry 的交集语义在扩展侧）
HOST_ACTION_IDS = tuple(k for k in QUICK_ACTION_IDS if k not in QUICK_ACTION_EXT_ONLY)
QUICK_ACTION_DEFAULTS = ("chat", "immersive-translate", "tts-book", "bookmark")


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


@web.route("/ajax/buddy/image", methods=["GET"])
@user_login_required
def buddy_image_proxy():
    """Same-origin proxy for buddy art on MinIO (host whitelist, see note above)."""
    source = request.args.get("src", "")
    parsed = http_requests.utils.urlparse(source)
    base = parsed.scheme + "://" + parsed.netloc
    if base not in _BUDDY_IMAGE_HOSTS or not parsed.path.startswith(_BUDDY_IMAGE_PATH_PREFIX):
        return jsonify({"success": False, "message": "invalid buddy image url"}), 400
    try:
        upstream = http_requests.get(source, timeout=10)
    except http_requests.RequestException:
        return jsonify({"success": False, "message": "buddy image upstream unreachable"}), 502
    if upstream.status_code != 200:
        return jsonify({"success": False, "message": "buddy image upstream error"}), upstream.status_code
    return Response(upstream.content, mimetype=upstream.headers.get("Content-Type", "image/png"))


@web.route("/ajax/buddy/quick-actions", methods=["GET", "POST"])
@user_login_required
def buddy_quick_actions():
    """Hover 快捷气泡配置；GET 返回全集与当前选择，POST 覆写选择（4-5 个，chat 恒首位）。
    R294：真值迁 moon-well（user_ui_settings.buddy_quick_actions，R260 白名单含扩展专有三项），
    本路由降级为「薄代理 + 存量懒迁移 + 离线兜底」——moon-well javadoc 预留的形态。
    label 在请求期取词——gettext 依赖请求上下文，模块导入期只会缓存英文 msgid。"""
    if request.method == "GET":
        selected, stored = None, False
        body, status, _ = _moonwell_proxy("/buddy/quick-actions", {}, 10, "buddy quick-actions")
        mw = _quick_actions_json(body)
        if status == 200 and isinstance(mw, dict) and mw.get("success"):
            result = mw.get("result") or {}
            selected, stored = result.get("selected"), bool(result.get("stored"))
            # 存量懒迁移（幂等自愈，每用户首次访问触发，无批量脚本）：moon-well 从未保存
            # 而 view_settings 有真实存量选择 → 代用户回填一次，存量用户不丢配置；
            # 迁移成功后真值即在 moon-well，下次 GET 直读。raw 存在才迁——恰好存了
            # 默认四项的用户也迁移（有保存行为就该进真值源）。
            if not stored:
                raw = (current_user.view_settings or {}).get("buddy", {}).get("quickActions")
                if isinstance(raw, list) and raw:
                    legacy = _pin_chat_first(raw)[:QUICK_ACTION_MAX]
                    if QUICK_ACTION_MIN <= len(legacy) <= QUICK_ACTION_MAX:
                        save_body, save_status, _ = _moonwell_proxy(
                            "/buddy/quick-actions/save", {"selected": legacy}, 10,
                            "buddy quick-actions save")
                        mw_saved = _quick_actions_json(save_body)
                        if save_status == 200 and isinstance(mw_saved, dict) and mw_saved.get("success"):
                            selected = (mw_saved.get("result") or {}).get("selected") or legacy
                            stored = True
        if selected is None:
            # moon-well 不可用/登录态异常：退回本地 view_settings（R234 原语义），页面不瘫
            selected, stored = current_user_view_settings(), False
        return jsonify({
            "success": True,
            "result": {
                "available": [{"id": k, "label": gettext(v), "ext_only": k in QUICK_ACTION_EXT_ONLY}
                              for k, v in QUICK_ACTION_LABEL_IDS.items()],
                "selected": selected,
                "stored": stored,
            },
        })
    payload = request.get_json(silent=True) or {}
    selected = payload.get("selected")
    if (not isinstance(selected, list)
            or any(a not in QUICK_ACTION_IDS for a in selected)
            or len(set(selected)) != len(selected)):
        return jsonify({"success": False, "message": "invalid quick actions"}), 400
    # 数量口径按归一后算：chat 由服务端补位，不带 chat 发 3 个＝4 个合法；
    # 发 5 个非 chat 连 chat 共 6 个，超上限 400 而不是静默丢掉用户的选择。
    normalized = _pin_chat_first(selected)
    if not (QUICK_ACTION_MIN <= len(normalized) <= QUICK_ACTION_MAX):
        return jsonify({"success": False, "message": "invalid quick actions"}), 400
    save_body, save_status, _ = _moonwell_proxy(
        "/buddy/quick-actions/save", {"selected": normalized}, 10, "buddy quick-actions save")
    mw_saved = _quick_actions_json(save_body)
    if not (save_status == 200 and isinstance(mw_saved, dict) and mw_saved.get("success")):
        # 真值源拒绝/不可用不静默：透出真实原因（moon-well 会按同一白名单/数量口径二次兜底）
        message = mw_saved.get("message") if isinstance(mw_saved, dict) else None
        return jsonify({"success": False, "message": message or "quick actions save failed"}), 502
    # 本地 view_settings 以 moon-well 归一结果同步覆写为热兜底（moon-well 不可用时 GET 的回退源）
    normalized = (mw_saved.get("result") or {}).get("selected") or normalized
    current_user.set_view_property("buddy", "quickActions", normalized)
    return jsonify({"success": True, "result": {"selected": normalized, "stored": True}})


def _quick_actions_json(body):
    """moon-well client 回包是 response.text 字符串（binary=False）——统一解 JSON，
    非 JSON/坏包按 None（调用方走兜底或报错路径，不在代理边界抛异常）。"""
    if isinstance(body, dict):
        return body
    try:
        return json.loads(body)
    except (TypeError, ValueError):
        return None


def current_user_view_settings():
    """读取当前用户 quickActions：chat 钉回首位、截到上限；非法/缺失/不足回落默认四项。
    R223 期服务端不校验 chat，存量旧值可能缺 chat 或 chat 不在首位，读时一并纠正。"""
    raw = (current_user.view_settings or {}).get("buddy", {}).get("quickActions")
    if isinstance(raw, list):
        normalized = _pin_chat_first(raw)[:QUICK_ACTION_MAX]
        if len(normalized) >= QUICK_ACTION_MIN:
            return normalized
    return list(QUICK_ACTION_DEFAULTS)


def _pin_chat_first(actions):
    """白名单过滤 + 保序去重 + chat 钉到第一位；不做数量裁决，由调用方按场景定。"""
    others = []
    for action in actions:
        if (action in QUICK_ACTION_IDS and action != QUICK_ACTION_PINNED
                and action not in others):
            others.append(action)
    return [QUICK_ACTION_PINNED] + others
