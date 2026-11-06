# -*- coding: utf-8 -*-

#  This file is part of the Magicbook (customized Calibre-Web).
#
#  R279 用户投稿：上传仅进 MinIO 暂存区，管理员审核后才解析入库。
#
#  Why: 书库（calibre metadata.db）是全局共享的，`books` 表没有归属字段；
#  直接放开既有 `/upload` 的 ROLE_UPLOAD 会让持权用户直写书库甚至覆盖任意
#  书目的格式文件。投稿链路因此完全不碰书库：文件只落在 MinIO 暂存前缀，
#  台账记在 app.db，管理员审核通过后由后台线程解析入库。
#
#  表懒建：沿用 book_insight / reading_translation_job 的先例——ub.Base +
#  `_ensure_tables()`（Base.metadata.create_all(bind, tables=[...])），
#  不改 init_db，也不给既有库写迁移。

from sqlalchemy import Column, DateTime, Integer, String, Text

from ..reading_translation.timeutil import now_utc
from .. import ub

# 状态机：PENDING（已上传待审）→ APPROVED（审核通过，入库中）→ INGESTED（已入库）
#                                  ↘ REJECTED（驳回）/ FAILED（入库失败，可重审）
STATUS_PENDING = "PENDING"
STATUS_APPROVED = "APPROVED"
STATUS_REJECTED = "REJECTED"
STATUS_INGESTED = "INGESTED"
STATUS_FAILED = "FAILED"


class BookSubmission(ub.Base):
    __tablename__ = "book_submission"

    id = Column(Integer, primary_key=True)
    # 提交人（app.db user.id）。Why 不放 calibre 侧：投稿记录是运营数据，
    # 不属于 Calibre 家族互操作契约（R78/R92 既定边界）。
    user_id = Column(Integer, nullable=False, index=True)
    # MinIO 对象键（bucket 内完整路径）。对象名由服务端生成（uuid），不含用户输入。
    object_key = Column(String(500), nullable=False, unique=True)
    # 用户原始文件名，仅展示与扩展名还原用，绝不用于拼路径。
    original_filename = Column(String(500), nullable=False, default="")
    size = Column(Integer, nullable=False, default=0)
    # 内容哈希：同一用户重复提交同一文件时直接复用已有记录，防灌桶。
    sha256 = Column(String(64), nullable=False, index=True)
    status = Column(String(24), nullable=False, default=STATUS_PENDING, index=True)
    reviewer_id = Column(Integer)
    reviewed_at = Column(DateTime(timezone=True))
    note = Column(Text, default="")
    # 审核通过入库后回填的书目 id，便于用户看到「我的投稿已成书」。
    book_id = Column(Integer, index=True)
    error_message = Column(Text, default="")
    created_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=now_utc, onupdate=now_utc,
                        nullable=False)
