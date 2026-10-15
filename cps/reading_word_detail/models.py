from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint

from .. import ub
from ..reading_translation.timeutil import now_utc


class WordDetailJob(ub.Base):
    """一本书的一次「补缺单词详解」批次。

    Why 只存计数不存词：全量词表在 item.words_json 里，job 只留台账级数字，
    否则同书上万词的 JSON 在每个批次行里重复一遍。
    """

    __tablename__ = "reading_word_detail_job"

    id = Column(String(64), primary_key=True)
    user_id = Column(Integer, nullable=False, index=True)
    book_id = Column(Integer, nullable=False, index=True)
    book_format = Column(String(20), nullable=False)
    book_name = Column(String(500), nullable=False, default="")
    book_fingerprint = Column(String(64), nullable=False)
    status = Column(String(24), nullable=False, default="PENDING", index=True)
    # 正文去重词数 / 预览时已缓存词数 / 本次待生成词数（覆盖率的分母）
    distinct_words = Column(Integer, nullable=False, default=0)
    cached_words = Column(Integer, nullable=False, default=0)
    target_words = Column(Integer, nullable=False, default=0)
    published_words = Column(Integer, nullable=False, default=0)
    covered_words = Column(Integer, nullable=False, default=0)
    skipped_not_word_like = Column(Integer, nullable=False, default=0)
    failed_batches = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=now_utc, onupdate=now_utc, nullable=False)


class WordDetailJobItem(ub.Base):
    """台账明细：**一行 = 一批 200 词**，不是一词一行。

    Why 批粒度：一本书上万词逐词建行只会把进度页变成滚动条坟场，而 moon-well 侧
    本来就是按批返回计数（scanned/published/skipped*）；需要逐词时现查
    cached-check，不必为它养一张万行表。
    Why 批内词表落库（words_json）：覆盖率回收必须知道「这批要盯哪些词」，
    重抽正文再比对会让每次轮询都变成一次 EPUB 解析。
    """

    __tablename__ = "reading_word_detail_job_item"
    __table_args__ = (UniqueConstraint("job_id", "batch_seq", name="uq_word_detail_job_batch"),)

    id = Column(String(64), primary_key=True)
    job_id = Column(String(64), ForeignKey("reading_word_detail_job.id"), nullable=False, index=True)
    batch_seq = Column(Integer, nullable=False)
    words_json = Column(Text, nullable=False)
    word_count = Column(Integer, nullable=False, default=0)
    status = Column(String(24), nullable=False, default="PENDING", index=True)
    published_count = Column(Integer, nullable=False, default=0)
    skipped_cached = Column(Integer, nullable=False, default=0)
    skipped_in_flight = Column(Integer, nullable=False, default=0)
    skipped_invalid = Column(Integer, nullable=False, default=0)
    skipped_not_word_like = Column(Integer, nullable=False, default=0)
    # 已有详解缓存的词数：发布回执里的 skipped_cached 即首批覆盖，之后由进度轮询累加
    covered_count = Column(Integer, nullable=False, default=0)
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=now_utc, onupdate=now_utc, nullable=False)
