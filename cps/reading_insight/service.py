# cps/reading_insight/service.py — R214 B：内容速览缓存 + AI 简介生成（LLD §2/§4）。
#
# Why 缓存表：详情页高频、EPUB 解析 O(全书)；(book_id, book_format) 唯一，
# fingerprint 失效自动重建（LLD §2）。
# Why AI 简介走 moon-well 的 book-intro ability（按正文入参、不吃 moon-well bookId）：
# 本仓 AI 对话通道已退役（/ai/chat 全 410），且两侧 bookId 不同源（R197/R200 踩过），
# 跨仓契约见 moon-well R207。上游不可用时失败可见透传，不静默变「暂无简介」（LLD §8）。
import json

from .. import calibre_db, logger, ub
from ..reading_job.service_base import JobServiceBase
from ..reading_translation.timeutil import now_utc
from . import parser as insight_parser
from .models import BookInsight

log = logger.create()

SCHEMA_VERSION = 1


def _ensure_tables():
    # 懒建（reading_job/service_base.py:73 同款）：app.db 由运行环境持有，不进版本库。
    bind = ub.session.get_bind()
    ub.Base.metadata.create_all(bind, tables=[BookInsight.__table__])


def _book_file(book_id, book_format):
    # 复用 job 基类的正文定位/指纹原语（LLD §2）：缓存键必须与三个 job 的
    # 「同一本书同一格式」口径逐字一致，否则两套指纹会对不上。_book_file 不触碰
    # 实例状态，以未绑定函数调用；_fingerprint 本就是 staticmethod。
    return JobServiceBase._book_file(None, book_id, book_format)


def _fingerprint(path):
    return JobServiceBase._fingerprint(path)


def _find_row(book_id, book_format):
    return (ub.session.query(BookInsight)
            .filter(BookInsight.book_id == int(book_id),
                    BookInsight.book_format == book_format)
            .first())


def _payload_of(row):
    payload = json.loads(row.payload_json)
    payload.setdefault("aiSummary", None)
    payload["builtAt"] = int(row.built_at.timestamp()) if row.built_at else None
    return payload


def get_or_build(book_id, book_format):
    """速览 payload：fingerprint 命中直接回缓存，否则解析重建并覆盖写。"""
    book_id = int(book_id)
    book_format = (book_format or "epub").lower()
    _book, path = _book_file(book_id, book_format)
    fingerprint = _fingerprint(path)
    _ensure_tables()
    row = _find_row(book_id, book_format)
    if row and row.fingerprint == fingerprint and row.last_error is None:
        payload = _payload_of(row)
        payload["bookId"] = book_id
        payload["bookFormat"] = book_format
        payload["fingerprint"] = fingerprint
        return payload

    try:
        payload = insight_parser.parse(path)
    except Exception as error:
        # 失败可见（LLD §8）：last_error 落库便于排查，向上传「解析失败: 原文」。
        if row is not None:
            row.last_error = str(error)
            ub.session.commit()
        raise ValueError("内容速览解析失败: %s" % error)

    # 正文指纹变化但管理员生成过简介 → 保留 aiSummary（拍板⑦无「重新生成」按钮，
    # 丢掉就再也拿不回来；简介以书目元数据+首章为主，正文小改不动摇它）。
    if row is not None:
        try:
            old = json.loads(row.payload_json)
            if old.get("aiSummary"):
                payload["aiSummary"] = old["aiSummary"]
        except (TypeError, ValueError):
            pass

    payload.setdefault("aiSummary", None)
    payload["bookId"] = book_id
    payload["bookFormat"] = book_format
    payload["fingerprint"] = fingerprint
    payload["builtAt"] = int(now_utc().timestamp())

    if row is None:
        row = BookInsight(book_id=book_id, book_format=book_format)
        ub.session.add(row)
    row.fingerprint = fingerprint
    row.payload_json = json.dumps(payload, ensure_ascii=False)
    row.schema_version = SCHEMA_VERSION
    row.built_at = now_utc()
    row.last_error = None
    ub.session.commit()
    return payload


def _save_ai_summary(book_id, book_format, ai_summary):
    """只 UPDATE payload_json 里的 aiSummary 键（LLD §2），不动其余内容。"""
    row = _find_row(book_id, book_format)
    if row is None:
        raise ValueError("book insight is unavailable")
    payload = json.loads(row.payload_json)
    payload["aiSummary"] = ai_summary
    row.payload_json = json.dumps(payload, ensure_ascii=False)
    ub.session.commit()


def _unwrap_result(response, label):
    """解 moon-well Result 包装取 result；失败抛带上游原文案的 ValueError。

    与 web._word_detail_unwrap 同一形态契约（三元组响应、透传 message）——
    接口故障若被降级成「没生成出来」，页面就把故障显示成「暂无简介」，
    用户报回来的永远是错误结论（LLD §8：禁止静默降级）。
    """
    if not isinstance(response, tuple) or len(response) < 2:
        raise ValueError("%s service unavailable" % label)
    body, status = response[0], response[1]
    try:
        data = json.loads(body)
    except (TypeError, ValueError):
        raise ValueError("%s returned unreadable response" % label)
    message = data.get("message") if isinstance(data, dict) else None
    if status >= 400 or (isinstance(data, dict) and data.get("success") is False):
        raise ValueError(message or "%s failed (HTTP %s)" % (label, status))
    result = data.get("result") if isinstance(data, dict) else None
    return result or {}


def generate_summary(book_id, book_format):
    """管理员触发的 AI 简介（拍板④不自动跑；拍板⑦已生成即定稿、无「重新生成」）。"""
    book_id = int(book_id)
    book_format = (book_format or "epub").lower()
    payload = get_or_build(book_id, book_format)
    if payload.get("aiSummary"):
        return payload["aiSummary"]

    book, _path = _book_file(book_id, book_format)
    authors = " & ".join(a.name for a in (book.authors or []))
    series = book.series[0].name if book.series else ""
    excerpt_text = "\n\n".join(e["text"] for e in payload.get("excerpt") or [])
    context = {
        "title": book.title or "",
        "author": authors,
        "series": series,
        "toc": [ch["title"] for ch in payload.get("chapters") or []],
        "excerpt": excerpt_text[:insight_parser.EXCERPT_MAX_CHARS],
    }

    # 延迟导入：web 模块加载末尾才挂路由，模块级互引会成环。
    from cps.web import _moonwell_proxy
    response = _moonwell_proxy("/book/ai/ability/book-intro", context, 60, "book intro")
    result = _unwrap_result(response, "book-intro")
    text = (result.get("content") or result.get("text") or "").strip()
    if not text:
        raise ValueError("book-intro returned empty content")
    ai_summary = {
        "text": text,
        "model": result.get("model") or "",
        "generatedAt": int(now_utc().timestamp()),
    }
    _save_ai_summary(book_id, book_format, ai_summary)
    return ai_summary
