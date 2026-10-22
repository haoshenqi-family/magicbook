"""WSGI 容器的 SSE 流式行为（R204 缺陷回归锁）。

背景：R194 上线后真机表现为「点批改后 2.5min 无任何数据、最后超时」。根因不在代理与
前端，而在 ``cps/tornado_wsgi.py`` 直接把请求交给了 tornado>=6.3 的
``WSGIContainer.handle_request`` —— 它会把 WSGI 应用的全部 chunk 收齐后 ``b"".join``
一次写出并补 ``Content-Length``，SSE 因此被整体缓冲，``status``/``ping`` 一帧都到不了
浏览器。

本文件用真实 socket 起一个同款 HTTPServer + MyWSGIContainer，按「首帧到达时刻」判定
是否真流式：缓冲实现下响应头要到流结束才出现，流式实现下应立刻出现。
"""
import asyncio
import http.client
import socket
import threading
import time

import pytest

from cps.tornado_wsgi import MyWSGIContainer
from tornado.httpserver import HTTPServer

FRAME_GAP = 0.5
FRAMES = 3


class _ServerThread:
    """在独立线程跑一个 tornado HTTPServer，事件循环不与 pytest 主线程争用。"""

    def __init__(self, app):
        self.port = self._free_port()
        self.loop = asyncio.new_event_loop()
        self.ready = threading.Event()
        self._thread = threading.Thread(target=self._run, args=(app,), daemon=True)

    @staticmethod
    def _free_port():
        probe = socket.socket()
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
        probe.close()
        return port

    def _run(self, app):
        asyncio.set_event_loop(self.loop)
        server = HTTPServer(MyWSGIContainer(app))
        server.listen(self.port, "127.0.0.1")
        self.ready.set()
        self.loop.run_forever()

    def __enter__(self):
        self._thread.start()
        assert self.ready.wait(5), "server thread did not start"
        return self

    def __exit__(self, *_):
        self.loop.call_soon_threadsafe(self.loop.stop)
        self._thread.join(timeout=5)
        self.loop.close()
        return False

    def get(self, path="/"):
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=15)
        connection.request("GET", path)
        return connection, connection.getresponse()


def _sse_app(environ, start_response):
    """start_response 在返回前调用（Flask Response 的实际形态）。"""
    start_response("200 OK", [("Content-Type", "text/event-stream"),
                              ("Cache-Control", "no-cache")])
    for index in range(FRAMES):
        yield b"event: ping\ndata: {\"i\": %d}\n\n" % index
        time.sleep(FRAME_GAP)


def _lazy_sse_app(environ, start_response):
    """裸生成器：start_response 在首次 next() 里才调用。"""
    def generate():
        start_response("200 OK", [("Content-Type", "text/event-stream")])
        for index in range(FRAMES):
            yield b"event: ping\ndata: {\"i\": %d}\n\n" % index
            time.sleep(FRAME_GAP)

    return generate()


def _plain_app(environ, start_response):
    start_response("200 OK", [("Content-Type", "text/plain; charset=utf-8")])
    return [b"hello", b"world"]


def _mixed_app(environ, start_response):
    """同一进程里同时提供 SSE 与普通响应，用来验证互不阻塞。"""
    if environ.get("PATH_INFO") == "/plain":
        return _plain_app(environ, start_response)
    return _sse_app(environ, start_response)


@pytest.mark.parametrize("app", [_sse_app, _lazy_sse_app],
                         ids=["start_response-eager", "start_response-lazy"])
def test_sse_frames_reach_client_incrementally(app):
    """首帧必须在流结束前到达，且响应不得带 Content-Length。"""
    with _ServerThread(app) as server:
        started = time.time()
        connection, response = server.get()
        headers_at = time.time() - started
        try:
            assert response.status == 200
            # 缓冲实现会在这里补上定长头，浏览器读完即关，后续 ping 全丢
            assert response.getheader("Content-Length") is None

            first_line = response.readline()
            first_frame_at = time.time() - started
            assert first_line.startswith(b"event: ping")

            # 关键判据：整条流要 FRAMES*FRAME_GAP≈1.5s 才结束；
            # 首帧若被缓冲，只能出现在 1.5s 之后。
            assert headers_at < FRAME_GAP, \
                "响应头 %.2fs 才到，说明整段 body 被缓冲（R204 根因复现）" % headers_at
            assert first_frame_at < FRAME_GAP, \
                "首帧 %.2fs 才到，说明 chunk 没有被 flush" % first_frame_at

            while response.readline():
                pass
            finished_at = time.time() - started
            assert finished_at >= FRAME_GAP * (FRAMES - 0.5), \
                "整条流应在 %.1fs 左右结束，实测 %.2fs" % (FRAME_GAP * FRAMES, finished_at)
        finally:
            connection.close()


def test_plain_response_keeps_content_length():
    """非 SSE 走原缓冲分支：仍然一次性给出完整 body 与 Content-Length。"""
    with _ServerThread(_plain_app) as server:
        connection, response = server.get()
        try:
            assert response.status == 200
            assert response.getheader("Content-Length") == "10"
            assert response.read() == b"helloworld"
        finally:
            connection.close()


def test_streaming_does_not_block_other_requests():
    """SSE 连接挂起期间，其它请求必须照常返回（阻塞读不能占住事件循环）。"""
    with _ServerThread(_mixed_app) as server:
        stream_conn, stream_response = server.get("/stream")
        try:
            assert stream_response.readline().startswith(b"event: ping")
            started = time.time()
            plain_conn, plain_response = server.get("/plain")
            elapsed = time.time() - started
            try:
                assert plain_response.status == 200
                assert plain_response.read() == b"helloworld"
            finally:
                plain_conn.close()
            assert elapsed < FRAME_GAP, \
                "SSE 在途时普通请求被卡了 %.2fs，说明阻塞读占住了事件循环" % elapsed
        finally:
            stream_conn.close()
