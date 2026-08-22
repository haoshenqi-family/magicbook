# -*- coding: utf-8 -*-

# 回归测试：gevent_wsgi.MyWSGIHandler.format_request 在解析异常路径下不应崩溃。
#
# 背景（Why）：网关注扇按 HTTPS 探测本服务 8085 明文端口时，会直接把 TLS 握手
# 字节（ClientHello）发送到明文 HTTP 端口。此时 WSGIHandler 在 get_environ() 之前
# 即进入 log_request 路径，self.environ 仍为 None。修复前 format_request 直接调用
# self.environ.get() 抛 AttributeError，导致处理该连接（含正常日志请求）的 greenlet
# 整体崩溃，并在日志中刷屏。修复后对 None 兜底为空字典，仅影响日志格式，不再抛异常。
from cps.gevent_wsgi import MyWSGIHandler


def _build_handler(environ=None, client_address=("1.2.3.4", 12345)):
    handler = MyWSGIHandler.__new__(MyWSGIHandler)
    handler.environ = environ
    handler.client_address = client_address
    handler.response_length = 21
    handler.time_finish = None
    handler.time_start = 0
    handler.requestline = "GET / HTTP/1.1"
    handler._orig_status = "200 OK"
    handler.status = "200 OK"
    return handler


def test_format_request_with_none_environ_does_not_crash():
    # 解析异常路径（如 TLS 探测字节）下 self.environ 为 None，不应抛异常
    line = _build_handler(environ=None).format_request()
    # 拿不到 X-Forwarded-For 时回退到 client_address
    assert "1.2.3.4" in line
    assert "200" in line


def test_format_request_uses_forwarded_for_when_present():
    line = _build_handler(environ={"HTTP_X_FORWARDED_FOR": "9.9.9.9"}).format_request()
    assert "9.9.9.9" in line
    assert "1.2.3.4" not in line


def test_format_request_with_empty_environ_does_not_crash():
    line = _build_handler(environ={}).format_request()
    assert "1.2.3.4" in line
