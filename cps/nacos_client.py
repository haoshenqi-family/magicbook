# -*- coding: utf-8 -*-
"""Nacos 服务注册与发现（moon-well 互调）。

magicbook 自身注册进 Nacos，供 moon-well 回调发现；同时后台刷新解析
moon-well 实例地址，替代硬编码 MOON_WELL_READING_URL。全部走后台
daemon 线程，不阻塞 Flask/gevent 主线程。
"""

import os
import socket
import threading
import time

try:
    import logging
    _LOG = logging.getLogger("nacos_discovery")

    def _log(msg):
        _LOG.warning(msg)
except Exception:  # pragma: no cover
    def _log(msg):
        print("nacos_discovery: %s" % msg)


class NacosDiscovery(object):
    def __init__(self):
        self._client = None
        self._moonwell_base = None
        self._lock = threading.Lock()
        self._started = False

    def enabled(self):
        return (os.environ.get("NACOS_DISCOVERY_ENABLED", "true").strip().lower() == "true"
                and bool(os.environ.get("NACOS_SERVER_ADDR", "").strip()))

    def start(self):
        if self._started or not self.enabled():
            return
        self._started = True
        try:
            from nacos import NacosClient
        except Exception as exc:
            _log("nacos sdk unavailable: %s" % exc)
            return
        try:
            self._client = NacosClient(
                os.environ.get("NACOS_SERVER_ADDR", ""),
                namespace=os.environ.get("NACOS_NAMESPACE", "") or "public",
                username=os.environ.get("NACOS_USERNAME", "") or None,
                password=os.environ.get("NACOS_PASSWORD", "") or None,
            )
            service = os.environ.get("NACOS_SERVICE_NAME", "magicbook")
            ip = os.environ.get("NACOS_REGISTER_IP", "").strip() or self._detect_ip()
            port = int(os.environ.get("NACOS_REGISTER_PORT", "8083"))
            self._client.add_naming_instance(service, ip, port)
            threading.Thread(target=self._refresh_loop, daemon=True).start()
        except Exception as exc:
            _log("nacos register failed: %s" % exc)

    def _refresh_loop(self):
        if self._client is None:
            return
        while True:
            try:
                instances = self._client.select_instances("moon-well", healthy_only=True) or []
                if instances:
                    inst = instances[0]
                    scheme = os.environ.get("MOON_WELL_DISCOVERY_SCHEME", "http")
                    base = "%s://%s:%s" % (scheme, inst["ip"], inst["port"])
                    with self._lock:
                        self._moonwell_base = base
            except Exception as exc:
                _log("nacos refresh failed: %s" % exc)
            time.sleep(int(os.environ.get("NACOS_REFRESH_SECONDS", "15")))

    @property
    def moonwell_base(self):
        with self._lock:
            return self._moonwell_base

    @staticmethod
    def _detect_ip():
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # 不需真发包，仅用 connect 探测本机出网网卡地址
            sock.connect(("192.168.31.9", 80))
            return sock.getsockname()[0]
        except Exception:
            return socket.gethostbyname(socket.gethostname())
        finally:
            sock.close()


nacos = NacosDiscovery()