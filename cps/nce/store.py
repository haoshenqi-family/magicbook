# -*- coding: utf-8 -*-

#  MinIO 读取层（R116③ LLD §4.1/§4.2）：客户端单例、manifest 缓存、Range 流式读。
#  Why: bucket magicbook 为私有（与 ted-audio/reading-tts 共用、前缀隔离），
#  服务端签名内网直读，浏览器只见 magicbook 域名，不用预签名、不暴露 MinIO；
#  课表用静态 manifest.json（一次读 + 进程缓存 TTL），不做逐请求 listObjects。
#  minio SDK 延迟导入：蓝图 fail-closed（未配 MINIO_* 不注册），测试经 monkeypatch
#  替换本模块函数，均不要求运行环境安装 minio 包。

import json
import logging
import os
import threading
import time

log = logging.getLogger("cps.nce")

MANIFEST_TTL = 300

_lock = threading.Lock()
_client = None
_manifests = {}


def minio_config():
    return {
        "endpoint": os.environ.get("MINIO_ENDPOINT", ""),
        "access_key": os.environ.get("MINIO_ACCESS_KEY", ""),
        "secret_key": os.environ.get("MINIO_SECRET_KEY", ""),
        "bucket": os.environ.get("NCE_AUDIO_BUCKET", "magicbook"),
        "prefix": os.environ.get("NCE_AUDIO_PREFIX", "nce-audio").strip("/"),
        "secure": os.environ.get("MINIO_SECURE", "").lower() in ("1", "true", "yes"),
    }


def configured():
    cfg = minio_config()
    return bool(cfg["endpoint"] and cfg["access_key"] and cfg["secret_key"])


def get_client():
    global _client
    with _lock:
        if _client is None:
            from minio import Minio
            cfg = minio_config()
            _client = Minio(cfg["endpoint"],
                            access_key=cfg["access_key"],
                            secret_key=cfg["secret_key"],
                            secure=cfg["secure"])
        return _client


def object_key(book_no, name):
    return "{}/book{}/{}".format(minio_config()["prefix"], book_no, name)


def get_manifest(book_no):
    """manifest.json as dict, process-cached with TTL; stale cache serves on refetch failure."""
    now = time.time()
    cached = _manifests.get(book_no)
    if cached and now - cached[0] < MANIFEST_TTL:
        return cached[1]
    key = object_key(book_no, "manifest.json")
    resp = get_client().get_object(minio_config()["bucket"], key)
    try:
        data = json.loads(resp.read().decode("utf-8"))
    finally:
        resp.close()
        resp.release_conn()
    _manifests[book_no] = (now, data)
    return data


def find_lesson(manifest, num):
    for lesson in manifest.get("lessons", []):
        if lesson.get("num") == num:
            return lesson
    return None


def get_object_range(book_no, name, start=None, length=None):
    """Open MinIO object (optionally a byte window) -> urllib3 response; caller closes."""
    if length is not None:
        return get_client().get_object(minio_config()["bucket"], object_key(book_no, name),
                                       offset=start, length=length)
    if start:
        return get_client().get_object(minio_config()["bucket"], object_key(book_no, name),
                                       offset=start)
    return get_client().get_object(minio_config()["bucket"], object_key(book_no, name))


def get_object_text(book_no, name):
    resp = get_client().get_object(minio_config()["bucket"], object_key(book_no, name))
    try:
        return resp.read().decode("utf-8", errors="replace")
    finally:
        resp.close()
        resp.release_conn()


def invalidate_cache():
    """Test/hotfix hook: drop cached client and manifests."""
    global _client
    with _lock:
        _client = None
        _manifests.clear()
