from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint

from .. import ub


def _now():
    return datetime.now(timezone.utc)


class TranslationJob(ub.Base):
    __tablename__ = "reading_translation_job"

    id = Column(String(64), primary_key=True)
    user_id = Column(Integer, nullable=False, index=True)
    book_id = Column(Integer, nullable=False, index=True)
    book_format = Column(String(20), nullable=False)
    book_name = Column(String(500), nullable=False, default="")
    book_fingerprint = Column(String(64), nullable=False)
    status = Column(String(24), nullable=False, default="PENDING", index=True)
    total_count = Column(Integer, nullable=False, default=0)
    cached_count = Column(Integer, nullable=False, default=0)
    published_count = Column(Integer, nullable=False, default=0)
    completed_count = Column(Integer, nullable=False, default=0)
    failed_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=_now, nullable=False)
    updated_at = Column(DateTime, default=_now, onupdate=_now, nullable=False)


class TranslationJobItem(ub.Base):
    __tablename__ = "reading_translation_job_item"
    __table_args__ = (UniqueConstraint("job_id", "text_hash", name="uq_translation_job_text"),)

    id = Column(String(64), primary_key=True)
    job_id = Column(String(64), ForeignKey("reading_translation_job.id"), nullable=False, index=True)
    paragraph_index = Column(Integer, nullable=False)
    chapter = Column(String(200), default="")
    text = Column(Text, nullable=False)
    text_hash = Column(String(64), nullable=False)
    task_id = Column(String(64), index=True)
    status = Column(String(24), nullable=False, default="PENDING", index=True)
    translation = Column(Text)
    error_message = Column(Text)
    attempt_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=_now, nullable=False)
    updated_at = Column(DateTime, default=_now, onupdate=_now, nullable=False)
