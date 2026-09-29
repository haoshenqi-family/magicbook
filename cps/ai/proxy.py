"""AI agent 薄代理（moon-well 宿主，设计文档 magicbook 侧 §4）。

伴读 agent 完全后端化到 moon-well（家族决策 D1）后，magicbook 的角色收敛为：
阅读上下文采集（前端注入）+ drawer UI + 本模块的 /ai/agent/* 端点透传。

设计要点（对应设计 §4.2）：
- JSON 端点复用 cps.web._moonwell_proxy（身份头 + Bearer JWT + 401 自动刷新一次），
  形制适配：moon-well 全部 POST + RequestBody，本模块暴露 GET（会话列表/历史/记忆/
  学情）并转换成 POST body 转发。
- SSE（/ai/agent/chat）是新的流式变体：requests stream=True 逐 chunk yield，不缓冲
  整段；token 刷新前置到连接建立阶段——流开始后 401 无法重放（无法回滚已发事件），
  连接建立的 401 可以安全丢弃重连一次。响应头禁缓存 + X-Accel-Buffering: no，
  read timeout 300s 对齐 moon-well 侧 agent 最长运行预算。
- 客户端断开时 finally 关闭上游连接（moon-well SseEmitter 的 onError/onTimeout
  回调会感知并发送失败事件，循环侧有界，无泄漏）。

数据形态：moon-well JSON 响应是全局 Result 包装 ``{"success": bool, "result": ...}``，
本模块原样透传（前端统一解包）；SSE 事件体不经包装（event: delta/tool_call/...）。

Why 不走 cps/ai/routes.py 的旧代理：旧模块随 ai_companion.db 退役（设计 §3/§4.3），
本模块是新前端唯一入口；旧端点保留只读直到迁移验证完成。
"""
import logging

import requests
from flask import Blueprint, Response, jsonify, request, stream_with_context
from flask import session as flask_session

log = logging.getLogger("cps.ai.proxy")

aiagent = Blueprint("aiagent", __name__)

#: SSE 上游读取超时（秒）：连接 10s、单 chunk idle 300s——对齐 moon-well agent
#: 最长运行预算（设计 §8.2：极端 300s 封顶）
_SSE_CONNECT_TIMEOUT = 10
_SSE_IDLE_TIMEOUT = 300


def _web_helpers():
    """运行时取 cps.web 的代理基础设施（身份头/JWT 刷新/base url）。

    Why 延迟导入：cps.web 是巨型模块且互相注册顺序敏感，模块级导入会在
    部分部署路径（如仅加载 AI blueprint 的测试）造成循环依赖。
    """
    from cps.web import (_MOONWELL_NO_PROXY, _moonwell_base_url,
                         _moonwell_identity_headers,
                         _moonwell_refresh_session_token)
    return (_MOONWELL_NO_PROXY, _moonwell_base_url,
            _moonwell_identity_headers, _moonwell_refresh_session_token)


def _relay_json(path, payload, label, timeout=20):
    """POST + body 转发 moon-well JSON 端点，原样透传 body 与状态码。

    Why 原样透传不解包：前端统一处理 moon-well Result 包装（{success, result}），
    代理保持「薄」——任何一层自作主张解包都会让错误路径（success=false）变形。
    """
    from cps.web import _moonwell_proxy
    body, status, headers = _moonwell_proxy(path, payload, timeout, label)
    return Response(body, status=status, headers={
        "Content-Type": headers.get("Content-Type", "application/json")})


def _body():
    return request.get_json(silent=True) or {}


@aiagent.route("/ai/agent/chat", methods=["POST"])
def agent_chat():
    """SSE 流式透传 moon-well /ai/agent/chat（分型事件协议，设计 §8）。

    请求体即 moon-well 契约（conversationId/message/bookContext{...}），
    本模块只补身份，不改写业务字段。
    """
    no_proxy, base_url, identity_headers, refresh_token = _web_helpers()
    base = base_url()
    if not base:
        return jsonify({"success": False,
                        "message": "moon-well is not configured"}), 503

    payload = _body()
    headers = identity_headers()
    token = flask_session.get("moonwell_access_token")

    def _connect(bearer):
        hdrs = dict(headers)
        if bearer:
            hdrs["authorization"] = "Bearer " + bearer
        return requests.post(
            base + "/ai/agent/chat", json=payload, headers=hdrs,
            stream=True, timeout=(_SSE_CONNECT_TIMEOUT, _SSE_IDLE_TIMEOUT),
            proxies=no_proxy)

    # 连接建立阶段的 401 可以安全重试（流未开始）；开始转发后不再重试
    response = _connect(token)
    if response.status_code == 401 and token:
        refreshed = refresh_token()
        if refreshed:
            response.close()
            response = _connect(refreshed)

    if response.status_code >= 400:
        # 非 SSE 错误（moon-well 网关异常/agent 未开启）：JSON 原样透传，前端走错误条
        body = response.text
        status = response.status_code
        response.close()
        log.warning("moon-well agent chat -> HTTP %s: %s", status, body[:300])
        return Response(body, status=status,
                        headers={"Content-Type": "application/json"})

    def generate():
        try:
            for chunk in response.iter_content(chunk_size=None):
                if chunk:
                    yield chunk
        finally:
            # 客户端断开（GeneratorExit）或转发结束都及时关上游，
            # moon-well 侧 emitter 回调感知后终止有界循环
            response.close()

    return Response(stream_with_context(generate()),
                    mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache",
                             "X-Accel-Buffering": "no",
                             "Connection": "keep-alive"})


@aiagent.route("/ai/agent/conversations", methods=["GET"])
def conversations():
    """会话列表（GET ?bookId= → moon-well POST {bookId}）。"""
    book_id = request.args.get("bookId", type=int)
    return _relay_json("/ai/agent/conversations", {"bookId": book_id},
                       "agent conversations")


@aiagent.route("/ai/agent/history", methods=["GET"])
def history():
    """会话历史（GET ?conversationId= → moon-well POST）。"""
    conversation_id = request.args.get("conversationId", type=int)
    if conversation_id is None:
        return jsonify({"success": False, "message": "conversationId is required"}), 400
    return _relay_json("/ai/agent/history", {"conversationId": conversation_id},
                       "agent history")


@aiagent.route("/ai/agent/conversation/rename", methods=["POST"])
def conversation_rename():
    return _relay_json("/ai/agent/conversation/rename", _body(), "agent conversation rename")


@aiagent.route("/ai/agent/conversation/delete", methods=["POST"])
def conversation_delete():
    return _relay_json("/ai/agent/conversation/delete", _body(), "agent conversation delete")


@aiagent.route("/ai/agent/memory", methods=["GET"])
def memory_list():
    """本人记忆列表（GET ?bookId= 可选 → moon-well POST /ai/agent/memory/list）。"""
    return _relay_json("/ai/agent/memory/list", {"bookId": request.args.get("bookId", type=int)},
                       "agent memory list")


@aiagent.route("/ai/agent/memory/save", methods=["POST"])
def memory_save():
    return _relay_json("/ai/agent/memory/save", _body(), "agent memory save")


@aiagent.route("/ai/agent/memory/delete", methods=["POST"])
def memory_delete():
    return _relay_json("/ai/agent/memory/delete", _body(), "agent memory delete")


@aiagent.route("/ai/agent/book-profile", methods=["GET"])
def book_profile():
    """book 学情摘要（懒计算入口；GET ?bookId= → moon-well POST）。"""
    book_id = request.args.get("bookId", type=int)
    if book_id is None:
        return jsonify({"success": False, "message": "bookId is required"}), 400
    return _relay_json("/ai/agent/book-profile", {"bookId": book_id},
                       "agent book profile")
