"""整本朗读批次的数据模型（R166 设计 §3.1，镜像 reading_translation/models.py）。

差异点：无 task_id（/tts/speak 同步无任务号）、无产物列（音频在 moon-well 永久
缓存，本仓不落任何音频）；无探测端点后计数简化为 total/done/failed（不区分
cached/synthesized，「省了多少」由发起者积分流水反映）；voice/style 留档整本
选角结果（批次页展示与排查用）。
"""

import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint

from .. import ub
from ..reading_translation.timeutil import now_utc


def new_id():
    return uuid.uuid4().hex


class ReadingTtsJob(ub.Base):
    __tablename__ = "reading_tts_job"

    id = Column(String(64), primary_key=True, default=new_id)
    user_id = Column(Integer, nullable=False, index=True)
    book_id = Column(Integer, nullable=False, index=True)
    book_format = Column(String(20), nullable=False)
    book_name = Column(String(500), nullable=False, default="")
    book_author = Column(String(300), nullable=False, default="")
    book_summary = Column(Text)
    book_fingerprint = Column(String(64), nullable=False)
    status = Column(String(24), nullable=False, default="RUNNING", index=True)
    total_count = Column(Integer, nullable=False, default=0)
    done_count = Column(Integer, nullable=False, default=0)
    failed_count = Column(Integer, nullable=False, default=0)
    voice = Column(String(64))
    style = Column(String(512))
    created_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=now_utc, onupdate=now_utc, nullable=False)


class ReadingTtsJobItem(ub.Base):
    __tablename__ = "reading_tts_job_item"
    __table_args__ = (UniqueConstraint("job_id", "text_hash", name="uq_reading_tts_job_text"),)

    id = Column(String(64), primary_key=True, default=new_id)
    job_id = Column(String(64), ForeignKey("reading_tts_job.id"), nullable=False, index=True)
    paragraph_index = Column(Integer, nullable=False)
    chapter = Column(String(200), default="")
    text = Column(Text, nullable=False)
    text_hash = Column(String(64), nullable=False)
    status = Column(String(24), nullable=False, default="PENDING", index=True)
    error_message = Column(Text)
    attempt_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=now_utc, onupdate=now_utc, nullable=False)


ACTIVE_STATUSES = ("RUNNING", "PARTIAL_FAILED")
