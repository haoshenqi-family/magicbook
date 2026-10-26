# cps/moonwell/client.py — moon-well 防腐层（R178，架构评审 B1）。
#
# Why 独立包：防腐层本体此前长在 cps/web.py（1483-1977 行），7 个模块反向
# import web 才能用到它——web.py 是「原版蓝图 + 定制路由 + 防腐层宿主」三重
# 身份，上游 merge 冲突面随定制量增长（评审 §3.2 🟠）。迁出后 web.py 只留
# 薄委托（原函数名不变，web.py 内 ~70 处调用点零改动），其余模块直接 import
# 本包，不再触碰 cps.web。
#
# 返回形态契约（重要）：proxy/multipart 一律返回**三元组**
#   (body_str, status, {"Content-Type": ...})
# 失败分支（未配置/未登录/网络失败）同样是三元组（手拼 JSON，不用 jsonify——
# 本包会被裸 daemon 线程调用，无 Flask 上下文时 jsonify 抛 RuntimeError，
# R78 生产事故同类）。原先「失败二元组 / 成功三元组」的隐式契约（66+ 处调用
# 靠「原样 return 不解包」才不炸，解包即 ValueError→500）就此消灭：
# return 透传与解包消费两种形态都恒定成立。
#
# 鉴权口径（R145 全 token 化，未变）：
#   - 用户身份：bearer_token 快照（后台线程）或 session 的 moonwell_access_token
#     （请求线程），401 自动刷新重试一次（仅请求线程）；
#   - 系统身份：system_identity=True 用 magicbook-system 服务账号 mk- key
#     （MOONWELL_SYSTEM_TOKEN，无用户会话的内部调用）。
import json
import logging
import os
import uuid

import requests
from flask import request
from flask import session as flask_session

log = logging.getLogger(__name__)

# moon-well 走内网直连（fnos:8082）。进程可能因封面下载等功能携带 http_proxy
# 环境变量，requests 默认信任它，内网域名会被代理断连导致 503，必须显式绕过。
NO_PROXY = {"http": None, "https": None}

_JSON_HEADERS = {"Content-Type": "application/json"}


def _error_tuple(status, message):
    """统一失败三元组（手拼 JSON：daemon 线程无 Flask 上下文时 jsonify 会炸）。"""
    return (json.dumps({"success": False, "message": message}), status, dict(_JSON_HEADERS))


class MoonWellClient:
    """moon-well 内网直连客户端：URL/trace/凭证/代理/刷新的唯一出口。"""

    def base_url(self):
        """Return the configured moon-well internal endpoint."""
        from cps import constants

        url = constants.MOON_WELL_READING_URL
        return url.rstrip("/") if url else None

    def trace_id(self):
        """当前请求的 trace-id：优先沿用上游 X-Trace-Id（全链路同一 ID），缺失时生成。

        Why: moon-well 侧 TraceIdFilter 优先透传该头；两端日志已入 ES（app-log-*），
        同一 traceId 可在 Kibana 一次拉出 magicbook→moon-well 全链路日志。
        恢复线程/后台线程无 flask 上下文时 request 会抛 RuntimeError，返回新生成 ID。
        """
        try:
            upstream = request.headers.get("X-Trace-Id")
        except RuntimeError:
            upstream = None
        return upstream or uuid.uuid4().hex

    def system_token(self):
        """系统身份凭证（R145 全 token 化）：magicbook-system 服务账号的 mk- API key。

        Why: 启动恢复线程、连接器闭包、toggleread 桥接没有用户会话，token 化后
        改用服务账号静态 key 调 moon-well（拦截器 mk- 分支按 user.token 查库校验，
        任务归属 magicbook-system 账号）。key 只存 fnOS .env 的 MOONWELL_SYSTEM_TOKEN。
        """
        return os.environ.get("MOONWELL_SYSTEM_TOKEN", "")

    def exchange_id_token(self, id_token):
        """用 Authentik id_token 换 moon-well 的 (access_token, refresh_token)。

        Why 收编（B1）：原先 oidc.py 直连 /auth/oidc/exchange——URL、no-proxy、
        结果键名（accessToken/refreshToken 双口径）的解析口径是防腐层职责，
        回调页不应各自为政。失败/未配置返回 (None, None)。
        """
        base = self.base_url()
        if not base or not id_token:
            return None, None
        try:
            exchange_body = {}
            exchange_body["idToken"] = id_token
            resp = requests.post(
                base + "/auth/oidc/exchange",
                json=exchange_body,
                timeout=8,
                proxies=NO_PROXY,
            )
            data = resp.json() if resp.ok else {}
            result = data.get("result") or {}
            access = result.get("accessToken") or result.get("access_token")
            refresh = result.get("refreshToken") or result.get("refresh_token")
            if not resp.ok or not access:
                log.warning("moon-well token exchange failed: status=%s body=%s",
                            resp.status_code, resp.text[:300])
                return None, None
            return access, refresh
        except requests.RequestException as error:
            log.warning("moon-well token exchange request failed: %s", error)
            return None, None

    def refresh_session_token(self):
        """用 session 中的 refresh_token 换取新的 access_token，失败则清空。"""
        refresh_token = flask_session.get("moonwell_refresh_token")
        if not refresh_token:
            return None
        base = self.base_url()
        if not base:
            return None
        try:
            resp = requests.post(
                base + "/auth/refreshToken",
                headers={"X-Trace-Id": self.trace_id()},
                json={"refreshToken": refresh_token},
                timeout=8,
                proxies=NO_PROXY,
            )
            if resp.ok:
                data = resp.json()
                result = data.get("result") or {}
                new_access = result.get("accessToken") or result.get("access_token")
                new_refresh = result.get("refreshToken") or result.get("refresh_token")
                if new_access:
                    flask_session["moonwell_access_token"] = new_access
                    if new_refresh:
                        flask_session["moonwell_refresh_token"] = new_refresh
                    return new_access
        except Exception:
            pass
        flask_session.pop("moonwell_access_token", None)
        flask_session.pop("moonwell_refresh_token", None)
        return None

    def proxy(self, path, payload, timeout, label, binary=False, method="POST",
              system_identity=False, bearer_token=None):
        """转发 JSON 请求到 moon-well（R145 全 token 化：只认凭证，不发身份头）。

        鉴权方式：Authorization=Bearer JWT
          - 用户身份：bearer_token 快照（后台线程）或 session 中的 moonwell_access_token
            （请求线程），任务归属该用户；401 时自动刷新重试一次（仅请求线程调用方）。
          - 系统身份：system_identity=True 时用 magicbook-system 服务账号的 mk- API key。
        用户会话无 token：互信头机制已废（R145），不再降级，直接 401 提示重新登录。
        binary=True 时按原始字节透传响应体（音频），而非解码为文本。
        method="GET" 时以 GET 转发且不带请求体（known/unknown 标记是 path 参数式 GET）。
        bearer_token：请求线程定格的令牌快照，供整本翻译等 daemon 后台线程使用——
        传入快照后本方法不再触碰任何请求态，401 自动刷新也跳过。

        返回统一三元组 (body, status, headers)——失败分支同样是三元组，见模块头注释。
        """
        base = self.base_url()
        if not base:
            return _error_tuple(503, "moon-well is not configured")

        from_request_session = False
        if system_identity:
            token = self.system_token()
            if not token:
                log.error("moon-well %s: MOONWELL_SYSTEM_TOKEN 未配置，系统身份调用不可用", path)
                return _error_tuple(503, label + " service unavailable")
        elif bearer_token is not None:
            # 后台线程快照：调用线程同样没有 Flask 上下文，令牌只认显式传入值
            token = bearer_token
        else:
            token = flask_session.get("moonwell_access_token")
            from_request_session = True
            if not token:
                return _error_tuple(401, "moon-well 登录已失效，请重新登录")

        headers = {
            "X-Trace-Id": self.trace_id(),
            "authorization": "Bearer " + token,
        }

        def _send():
            if method == "GET":
                return requests.get(base + path, headers=headers,
                                    timeout=timeout, proxies=NO_PROXY)
            return requests.post(base + path, json=payload, headers=headers,
                                 timeout=timeout, proxies=NO_PROXY)

        try:
            response = _send()
            # 会话令牌过期时自动刷新并重试一次（仅请求线程调用方：刷新要读请求会话，
            # 系统身份/后台快照调用方没有上下文，也不该持有可刷新的用户令牌）
            if response.status_code == 401 and from_request_session:
                refreshed = self.refresh_session_token()
                if refreshed:
                    headers["authorization"] = "Bearer " + refreshed
                    response = _send()
            body = response.content if binary else response.text
            # Why: moon-well 的全局异常处理器不落日志，业务异常（HTTP 500）在服务端
            # 无任何痕迹；代理透传失败响应时必须在此留痕（状态码 + 响应体摘要），
            # 否则线上偶发 500 只能靠猜。
            if response.status_code >= 400:
                log.warning("moon-well %s -> HTTP %s: %s",
                            path, response.status_code, body[:300])
            return (body, response.status_code,
                    {"Content-Type": response.headers.get("Content-Type", "application/json")})
        except requests.RequestException as error:
            log.warning("moon-well %s request failed: %s", path, error)
            return _error_tuple(503, label + " service unavailable")

    def multipart(self, path, file_bytes, filename, timeout, label, fields=None):
        """转发 multipart 录音到 moon-well（R155 语音输入专用）。

        Why 独立小转发器而非扩展 proxy：后者契约是 JSON payload；
        转写是「文件进、文本出」的一次性消费。鉴权同口径（会话 bearer + trace id，
        直连禁代理）；401 透传由前端提示重登，不做静默刷新重试（重录成本低）。
        返回统一三元组（失败分支同样手拼 JSON，见模块头注释）。
        """
        base = self.base_url()
        if not base:
            return _error_tuple(503, "moon-well is not configured")
        token = flask_session.get("moonwell_access_token")
        if not token:
            return _error_tuple(401, "moon-well 登录已失效，请重新登录")
        headers = {
            "X-Trace-Id": self.trace_id(),
            "authorization": "Bearer " + token,
        }
        form = dict(fields or {})
        try:
            response = requests.post(base + path,
                                     data=form,
                                     files={"file": (filename, file_bytes)},
                                     headers=headers, timeout=timeout,
                                     proxies=NO_PROXY)
        except requests.RequestException as exc:
            log.error("moon-well %s: multipart forward failed: %s", path, exc)
            return _error_tuple(502, label + " 网络失败，请重试")
        try:
            body = response.json()
        except ValueError:
            return _error_tuple(502, label + " 上游响应异常")
        status = 200 if body.get("success") else 502
        return (json.dumps(body), status, dict(_JSON_HEADERS))

    def settings_fetch(self):
        """服务端拉取阅读设置（reading_settings 页面首屏渲染）；失败返回 (None, 提示文案)。"""
        try:
            body, status, _headers = self.proxy("/vocabulary/reading/settings", None, 10,
                                                "reading settings", method="GET")
            if 200 <= status < 300:
                data = json.loads(body)
                # moon-well Result 包装: {"success": bool, "result": {...}}
                if data.get("success") and data.get("result") is not None:
                    return data["result"], None
                return None, (data.get("message") or "settings unavailable")
            return None, "reading settings service unavailable (HTTP %d)" % status
        except (ValueError, TypeError) as error:
            log.warning("reading settings parse failed: %s", error)
            return None, "reading settings service unavailable"


# 模块级单例：Flask 无 DI 容器，全仓共用同一出口（web.py 薄委托与其余消费方
# 引用同一实例，口径天然一致）。
client = MoonWellClient()
