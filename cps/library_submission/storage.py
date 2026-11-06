# -*- coding: utf-8 -*-

#  This file is part of the Magicbook (customized Calibre-Web).
#
#  R279 投稿 MinIO 暂存层：与 cps/nce/store.py 同一形态（惰性单例客户端、
#  env 读取、MINIO_* 三键齐备才可用），但只服务投稿前缀。
#
#  Why 不复用 nce.store：那边的 object_key 形制（nce-audio/bookN/…）与
#  缓存语义（manifest TTL）是课级音频专属的；投稿要写、要删、要按对象取流，
#  复用会把两条链路的状态耦合在一起。
#
#  安全面：暂存对象**绝不能**进入 MinIO 桶的匿名只读 Statement（现只放开
#  `buddy/` 与 `ted-audio/`，见 R201/R207）。本模块只做服务端签名读写，
#  不生成任何预签名 URL；匿名可读性由桶策略保证，仓库侧以守卫测试钉住
#  「本模块不产生公开直链」。

import os
import threading

SUBMISSION_PREFIX = "book-submissions"

# 单文件上限：与 Tornado 200MB 请求体硬顶（cps/server.py max_buffer_size）
# 之间留量；ePub 实际分布远小于此。
MAX_SUBMISSION_MB_ENV = "SUBMISSION_MAX_MB"
DEFAULT_MAX_MB = 100

# 单用户在途（未审/未入库）记录上限。Why 按条数不按字节：MinIO 桶没有
# 应用层配额，条数上限已足够防单人灌桶，字节口径反而诱导拼大文件。
MAX_PENDING_PER_USER_ENV = "SUBMISSION_MAX_PENDING"
DEFAULT_MAX_PENDING = 10


def _env_int(name, default):
    try:
        return int(os.environ.get(name, "") or default)
    except (TypeError, ValueError):
        return default


def max_submission_bytes():
    return _env_int(MAX_SUBMISSION_MB_ENV, DEFAULT_MAX_MB) * 1024 * 1024


def max_pending_per_user():
    return _env_int(MAX_PENDING_PER_USER_ENV, DEFAULT_MAX_PENDING)


_lock = threading.Lock()
_client = None


def minio_config():
    return {
        "endpoint": os.environ.get("MINIO_ENDPOINT", ""),
        "access_key": os.environ.get("MINIO_ACCESS_KEY", ""),
        "secret_key": os.environ.get("MINIO_SECRET_KEY", ""),
        "bucket": os.environ.get("SUBMISSION_BUCKET", "magicbook"),
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


def object_key_for(user_id, suffix, extension):
    """服务端生成的对象键：不含用户输入，杜绝路径拼接注入。

    extension 已在入口侧过白名单并转小写。
    """
    return "{}/{}/{}.{}".format(SUBMISSION_PREFIX, int(user_id), suffix,
                                extension)


def put_object(object_key, stream, length, content_type):
    return get_client().put_object(minio_config()["bucket"], object_key,
                                   stream, length, content_type=content_type)


def stat_object(object_key):
    return get_client().stat_object(minio_config()["bucket"], object_key)


def get_object(object_key):
    """Open the object -> urllib3 response; caller must close()."""
    return get_client().get_object(minio_config()["bucket"], object_key)


def remove_object(object_key):
    get_client().remove_object(minio_config()["bucket"], object_key)
