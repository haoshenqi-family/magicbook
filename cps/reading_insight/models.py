# cps/reading_insight/models.py — R214 B：内容速览缓存表（一次解析、多处消费）。
#
# Why 缓存而不是每次详情页现解析：详情页是高频入口，EPUB 解析是 O(全书) 操作；
# (book_id, book_format) 唯一 + fingerprint 失效（LLD §2）——文件重新导入后
# 指纹变化即重建覆盖，不追加历史。payload_json 里 aiSummary 键单独可写：
# 生成简介只 UPDATE 该键，不动整条 payload。
from sqlalchemy import Column, DateTime, Integer, String, Text, UniqueConstraint

from .. import ub
from ..reading_translation.timeutil import now_utc


class BookInsight(ub.Base):
    __tablename__ = "book_insight"

    id = Column(Integer, primary_key=True)
    book_id = Column(Integer, nullable=False, index=True)
    book_format = Column(String(20), nullable=False)
    fingerprint = Column(String(64), nullable=False)
    payload_json = Column(Text, nullable=False)
    schema_version = Column(Integer, nullable=False, default=1)
    built_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)
    last_error = Column(Text)
    __table_args__ = (UniqueConstraint("book_id", "book_format", name="uq_book_insight"),)
