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
}
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
    label 在请求期取词——gettext 依赖请求上下文，模块导入期只会缓存英文 msgid。"""
    current = current_user_view_settings()
    if request.method == "GET":
        return jsonify({
            "success": True,
            "result": {
                "available": [{"id": k, "label": gettext(v)}
                              for k, v in QUICK_ACTION_LABEL_IDS.items()],
                "selected": current,
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
    current_user.set_view_property("buddy", "quickActions", normalized)
    return jsonify({"success": True, "result": {"selected": normalized}})


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
