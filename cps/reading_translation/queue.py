"""整本翻译任务队列（批量登记，逐本激活执行）。

Why: 「一键登记全部英文书」与逐本执行是两个解耦的动作——登记只是待办
指针（不发 moon-well、不消耗积分），激活时才物化真实批次并发布缺失段。
不预写 job/item：批次以 book_fingerprint 关联数千段落 item，预建会产生
大量空批次并与僵尸判定/复用通道互相干扰。
"""
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Integer, String, UniqueConstraint

from .. import ub
from .timeutil import now_utc


class TranslationQueue(ub.Base):
    __tablename__ = "reading_translation_queue"
    __table_args__ = (UniqueConstraint("book_id", name="uq_translation_queue_book"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    book_id = Column(Integer, nullable=False, index=True)
    book_format = Column(String(20), nullable=False, default="EPUB")
    book_name = Column(String(500), nullable=False, default="")
    book_fingerprint = Column(String(64), nullable=False, default="")
    # QUEUED=待执行（只登记）；ACTIVATED=已转入真实批次（job_id 回填）；
    # SKIPPED=登记时书不可用被跳过；ERROR=激活时失败（message 记原因）
    status = Column(String(24), nullable=False, default="QUEUED", index=True)
    job_id = Column(String(64))
    message = Column(String(500), default="")
    queued_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)
    activated_at = Column(DateTime(timezone=True))

    def __repr__(self):
        return "TranslationQueue(book_id=%s, status=%s)" % (self.book_id, self.status)
