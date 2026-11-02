# -*- coding: utf-8 -*-

#  书 ↔ 音频册映射（R116③ LLD §3.3）：不加 Calibre 字段、不建新表，
#  以 series=新概念英语 + series_index(1.0–4.0) 唯一确定 nce-audio/book{N}/。
#  纯函数、零重依赖，供 web.py 详情页与 nce 蓝图共用。

NCE_SERIES_NAMES = {"新概念英语", "New Concept English"}
NCE_BOOK_COUNT = 4


def resolve_nce_book_no(entry):
    """Return audio book number 1–4 for an NCE series book, else None."""
    series_list = getattr(entry, "series", None) or []
    if not any(getattr(s, "name", None) in NCE_SERIES_NAMES for s in series_list):
        return None
    idx = getattr(entry, "series_index", None)
    if idx is None:
        return None
    try:
        book_no = int(round(float(idx)))
    except (TypeError, ValueError):
        return None
    return book_no if 1 <= book_no <= NCE_BOOK_COUNT else None
