"""reading_translation 时间口径工具：全模块唯一的 UTC aware 时间来源。

R75 缺陷背景：TranslationJob(Item).created_at/updated_at 原为 naive DateTime
列 + aware 默认值。aware 值写入 DB 再读回 tzinfo=None（SQLite 与 MySQL 的
DATETIME 均不带时区），service 里 ``_now() - existing.updated_at`` 触发
``TypeError: can't subtract offset-naive and offset-aware datetimes``，
被路由 except TypeError 捕获后把原文返回给前端（点「整本译」直接报这句）。

口径约定：
- 内存中一律持有 aware UTC datetime（``now_utc``）。
- 从 DB 读回的值可能是 naive（存量行、或 SQLite/MySQL DATETIME 丢弃 tzinfo），
  统一经 ``as_utc`` 归一为 aware UTC 后再参与运算/比较。
"""
from datetime import datetime, timezone


def now_utc() -> datetime:
    """当前时间：aware UTC，模块内一切「当前时间」的唯一来源。"""
    return datetime.now(timezone.utc)


def as_utc(value: datetime) -> datetime:
    """把 DB 读回的时间归一为 aware UTC。

    naive 值按 UTC 解释（写入侧一直是 UTC，墙钟没有换过）；aware 值原样返回
    （DateTime(timezone=True) + SQLite 生效时读回即 aware）。
    """
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value
