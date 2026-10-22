# -*- coding: utf-8 -*-

#  This file is part of the Calibre-Web (https://github.com/janeczku/calibre-web)
#    Copyright (C) 2022 OzzieIsaacs
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program. If not, see <http://www.gnu.org/licenses/>.

from tornado.wsgi import WSGIContainer
import tornado

from tornado import escape
from tornado import httputil
from tornado.ioloop import IOLoop
from tornado.iostream import StreamClosedError
from tornado.log import access_log

import concurrent.futures
from typing import List, Tuple, Optional, Callable, Any, Dict, Text
from types import TracebackType
import typing

if typing.TYPE_CHECKING:
    from typing import Type  # noqa: F401
    from wsgiref.types import WSGIApplication as WSGIAppType  # noqa: F4

# SSE 生成器阻塞在「等上游下一帧」上（写作批改 70–150s），因此流式分支必须放在独立
# 线程池里拉取 chunk：tornado 6.3 起 WSGIContainer 默认用 dummy_executor，即在事件循环
# 线程里跑 WSGI 应用；一旦在这里阻塞，整站所有请求都会跟着卡住。
# 一个活跃 SSE 连接长期占用一个 worker，16 个并发封顶，超出后新连接排队。
_STREAM_EXECUTOR = concurrent.futures.ThreadPoolExecutor(
    max_workers=16, thread_name_prefix="wsgi-stream")

_SSE_CONTENT_TYPE = "text/event-stream"


def _next_chunk(iterator):
    """取下一块；StopIteration 不能穿过 run_in_executor，转成 None。"""
    try:
        return next(iterator)
    except StopIteration:
        return None


async def _drain(write_result):
    """tornado 6.4+ 的 write 返回 Future（写完才完成），6.3 返回 None。"""
    if write_result is not None:
        await write_result


class MyWSGIContainer(WSGIContainer):

    def __call__(self, request: httputil.HTTPServerRequest) -> None:
        if tornado.version_info < (6, 3, 0, -99):
            self._handle_request_legacy(request)
        else:
            IOLoop.current().spawn_callback(self.handle_request, request)

    def _handle_request_legacy(self, request: httputil.HTTPServerRequest) -> None:
        """tornado < 6.3 的老路径，保持上游原样（该版本没有 executor 概念）。"""
        data = {}  # type: Dict[str, Any]
        response = []  # type: List[bytes]

        def start_response(
            status: str,
            headers: List[Tuple[str, str]],
            exc_info: Optional[
                Tuple[
                    "Optional[Type[BaseException]]",
                    Optional[BaseException],
                    Optional[TracebackType],
                ]
            ] = None,
        ) -> Callable[[bytes], Any]:
            data["status"] = status
            data["headers"] = headers
            return response.append

        app_response = self.wsgi_application(
            MyWSGIContainer.environ(self, request), start_response
        )
        try:
            response.extend(app_response)
            body = b"".join(response)
        finally:
            if hasattr(app_response, "close"):
                app_response.close()  # type: ignore
        if not data:
            raise Exception("WSGI app did not call start_response")
        self._finish_response(request, data, body)

    async def handle_request(self, request: httputil.HTTPServerRequest) -> None:
        """tornado >= 6.3 的请求入口。

        Why 覆写而不是直接用上游：上游 ``WSGIContainer.handle_request`` 先把 WSGI 应用
        产出的所有 chunk 收进列表（``response.append``）再 ``b"".join`` 一次写出，并补
        ``Content-Length``。对普通响应没问题，对 ``text/event-stream`` 是致命的：全部事件
        会被缓冲到批改结束才一起到达浏览器，整个等待期看不到任何 ``status``/``ping``，
        表现为「请求挂死」（R204 根因；容器内实测 4 帧 1s 间隔的流，响应头在 4.00s 才出现
        且带 ``Content-Length: 108``）。

        这里只让 SSE 走流式分支；非 SSE 仍保持上游的整段缓冲语义（含 Content-Length），
        避免改动其余用例依赖的响应形态。
        """
        data = {}  # type: Dict[str, Any]
        response = []  # type: List[bytes]

        def start_response(
            status: str,
            headers: List[Tuple[str, str]],
            exc_info: Optional[
                Tuple[
                    "Optional[Type[BaseException]]",
                    Optional[BaseException],
                    Optional[TracebackType],
                ]
            ] = None,
        ) -> Callable[[bytes], Any]:
            data["status"] = status
            data["headers"] = headers
            return response.append

        loop = IOLoop.current()
        app_response = await loop.run_in_executor(
            self.executor,
            self.wsgi_application,
            MyWSGIContainer.environ(self, request),
            start_response,
        )
        try:
            iterator = iter(app_response)
            if not data:
                # 裸生成器应用、start_response 在首次 next() 内才调用：先拉首块，
                # 拿到响应头后才能判断是否 SSE。
                first = await loop.run_in_executor(self.executor, _next_chunk, iterator)
                if first is not None:
                    response.append(first)
            if self._is_event_stream(data):
                await self._stream_response(request, data, iterator, response)
            else:
                await self._buffered_response(request, data, iterator, response)
        finally:
            if hasattr(app_response, "close"):
                app_response.close()  # type: ignore

    # ---- 分流 -------------------------------------------------------------

    @staticmethod
    def _is_event_stream(data: Dict[str, Any]) -> bool:
        for name, value in data.get("headers") or []:
            if name.lower() == "content-type":
                return _SSE_CONTENT_TYPE in (value or "").lower()
        return False

    async def _buffered_response(self, request, data, iterator, chunks):
        """与上游一致：收齐全部 chunk，补 Content-Length，一次写出。"""
        loop = IOLoop.current()
        while True:
            chunk = await loop.run_in_executor(self.executor, _next_chunk, iterator)
            if chunk is None:
                break
            chunks.append(chunk)
        if not data:
            raise Exception("WSGI app did not call start_response")
        self._finish_response(request, data, b"".join(chunks))

    async def _stream_response(self, request, data, iterator, chunks):
        """SSE：先发头（无 Content-Length → chunked），再逐块写出。

        ``HTTP1Connection.write``/``write_headers`` 在 torrent 6.4+ 返回可等待的
        Future（写完即落到 socket），6.3 返回 None；两种都兼容，await 到 Future
        就等价于显式 flush —— 这正是 SSE 需要的语义。
        """
        status_code, reason, headers = self._prepare_headers(data)
        connection = request.connection
        assert connection is not None
        start_line = httputil.ResponseStartLine("HTTP/1.1", status_code, reason)
        header_obj = httputil.HTTPHeaders()
        for key, value in headers:
            header_obj.add(key, value)
        try:
            await _drain(connection.write_headers(start_line, header_obj, chunk=b""))
            for chunk in chunks:  # 拿到响应头之前就已取出的首块
                if chunk:
                    await _drain(connection.write(chunk))
            loop = IOLoop.current()
            while True:
                # 阻塞读放专用线程池：这里可能一等 5s（心跳间隔）甚至更久，
                # 绝不能占住事件循环线程。
                chunk = await loop.run_in_executor(_STREAM_EXECUTOR, _next_chunk, iterator)
                if chunk is None:
                    break
                if chunk:
                    await _drain(connection.write(chunk))
        except StreamClosedError:
            # 浏览器关页/断网：停止推送即可；上游批改不取消，结果仍会落库。
            self._log(status_code, request)
            return
        except Exception as error:  # noqa: BLE001 - 生成器异常不能让连接悬着
            access_log.error("streaming response failed: %s", error)
        try:
            connection.finish()
        except StreamClosedError:
            pass
        self._log(status_code, request)

    # ---- 响应头 -----------------------------------------------------------

    def _prepare_headers(self, data: Dict[str, Any]):
        status_code_str, reason = data["status"].split(" ", 1)
        status_code = int(status_code_str)
        # 流式响应绝不能带 Content-Length：上游若给了也必须丢掉，否则浏览器按定长
        # 读完即关闭，后面的 ping 全部丢失。
        headers = [(k, v) for (k, v) in data["headers"] if k.lower() != "content-length"]
        header_set = {k.lower() for (k, v) in headers}
        if "server" not in header_set:
            headers.append(("Server", "TornadoServer/%s" % tornado.version))
        return status_code, reason, headers

    def _finish_response(self, request: httputil.HTTPServerRequest, data: Dict[str, Any],
                         body: bytes) -> None:
        status_code, reason, headers = self._prepare_headers(data)
        if status_code != 304:
            header_set = {k.lower() for (k, v) in headers}
            if "content-length" not in header_set:
                headers.append(("Content-Length", str(len(body))))
            if "content-type" not in header_set:
                headers.append(("Content-Type", "text/html; charset=UTF-8"))
        body = escape.utf8(body)
        start_line = httputil.ResponseStartLine("HTTP/1.1", status_code, reason)
        header_obj = httputil.HTTPHeaders()
        for key, value in headers:
            header_obj.add(key, value)
        assert request.connection is not None
        request.connection.write_headers(start_line, header_obj, chunk=body)
        request.connection.finish()
        self._log(status_code, request)

    # ---- 环境与日志（保持上游原样） ---------------------------------------

    def environ(self, request: httputil.HTTPServerRequest) -> Dict[Text, Any]:
        try:
            environ = WSGIContainer.environ(self, request)
        except TypeError as e:
            environ = WSGIContainer.environ(request)
        environ['RAW_URI'] = request.path
        self.env = environ
        return environ

    def _log(self, status_code: int, request: httputil.HTTPServerRequest) -> None:
        if status_code < 400:
            log_method = access_log.info
        elif status_code < 500:
            log_method = access_log.warning
        else:
            log_method = access_log.error
        request_time = 1000.0 * request.request_time()
        assert request.method is not None
        assert request.uri is not None
        ip = self.env.get("HTTP_FORWARD_FOR", None) or request.remote_ip
        summary = (
            request.method  # type: ignore[operator]
            + " "
            + request.uri
            + " ("
            + ip
            + ")"
        )
        log_method("%d %s %.2fms", status_code, summary, request_time)
