import zipfile

from cps.reading_translation.parser import extract_epub_paragraphs, split_long_text, text_hash


def _write_epub(path):
    container = """<container xmlns='urn:oasis:names:tc:opendocument:xmlns:container'><rootfiles><rootfile full-path='OPS/content.opf'/></rootfiles></container>"""
    opf = """<package xmlns='http://www.idpf.org/2007/opf'><manifest>
      <item id='one' href='one.xhtml' media-type='application/xhtml+xml'/>
      <item id='two' href='two.xhtml' media-type='application/xhtml+xml'/>
    </manifest><spine><itemref idref='one'/><itemref idref='two'/></spine></package>"""
    one = "<html xmlns='http://www.w3.org/1999/xhtml'><head><title>Chapter One</title></head><body><div><p> First   paragraph. </p><p>Second.</p></div></body></html>"
    two = "<html xmlns='http://www.w3.org/1999/xhtml'><body><h1>Chapter Two</h1><p>Third.</p><script>ignore me</script></body></html>"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("META-INF/container.xml", container)
        archive.writestr("OPS/content.opf", opf)
        archive.writestr("OPS/one.xhtml", one)
        archive.writestr("OPS/two.xhtml", two)


def test_extracts_in_spine_order_and_skips_nested_or_script_nodes(tmp_path):
    path = tmp_path / "book.epub"
    _write_epub(path)

    assert extract_epub_paragraphs(path) == [
        ("Chapter One", "First paragraph."),
        ("Chapter One", "Second."),
        ("Chapter Two", "Third."),
    ]


def test_long_paragraph_prefers_sentence_boundaries_and_hash_is_trimmed():
    text = "A sentence. " * 300
    chunks = split_long_text(text)

    assert len(chunks) > 1
    assert all(0 < len(chunk) <= 2000 for chunk in chunks)
    assert text_hash("  hello  ") == text_hash("hello")


def test_publish_payload_carries_prompt_template_and_progress_reports_pending(tmp_path, monkeypatch):
    """R46 整本翻译修复：发布任务必须带 promptTemplate（否则 moon-well 执行器
    拿裸英文去调 LLM，只会复述原文而非翻译）；progress 必须暴露 pendingCount。"""
    import os
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from cps.reading_translation import service as svc
    from cps.reading_translation.models import TranslationJob, TranslationJobItem

    path = tmp_path / "book.epub"
    _write_epub(path)

    # -- 不触发真实 DB：桩掉 _ensure_tables / calibre_db / current_user ------
    monkeypatch.setattr(svc.WholeBookTranslationService, "_ensure_tables", lambda self: None)
    monkeypatch.setattr(svc, "extract_epub_paragraphs", lambda p: [("Ch.1", "Hello paragraph.")])

    class _Book:
        title = "Test Book"

    class _CalibreDB:
        @staticmethod
        def get_filtered_book(book_id):
            return _Book()

        @staticmethod
        def get_book_format(book_id, fmt):
            class _F:
                name = "book"
            return _F()

    class _Config:
        @staticmethod
        def get_book_path():
            return str(tmp_path)

    class _BookPath(__import__("types").SimpleNamespace):
        pass

    monkeypatch.setattr(svc, "calibre_db", _CalibreDB)
    monkeypatch.setattr(svc, "config", _Config)

    class _User:
        id = 1

    monkeypatch.setattr(svc, "current_user", _User, raising=False)

    # 直接为 book 补齐 .path，_book_file 真正解析文件路径（已存在的 epub）
    real_book = _Book()
    real_book.path = "."
    monkeypatch.setattr(_CalibreDB, "get_filtered_book", staticmethod(lambda book_id: real_book))
    # 让 data.name + 扩展名正好命中刚才写入的 book.epub
    book, file_path = svc.WholeBookTranslationService()._book_file(1, "EPUB")

    published = []

    def _publish(payload):
        published.append(payload)
        return {"result": {"taskId": 42}}

    # Column default 只在真实 flush 时生效；stub session 下手动补默认值
    import types

    class _Session:
        def __init__(self):
            self.adds = []
            self.committed = 0

        def add(self, obj):
            self.adds.append(obj)
            # 模拟 flush 落 Column 默认值（default 只在真实 flush 生效）
            if isinstance(obj, TranslationJob):
                for field, default in (("total_count", 0), ("cached_count", 0),
                                       ("published_count", 0), ("completed_count", 0),
                                       ("failed_count", 0)):
                    if getattr(obj, field) is None:
                        setattr(obj, field, default)
            if isinstance(obj, TranslationJobItem) and obj.attempt_count is None:
                obj.attempt_count = 0

        def commit(self):
            self.committed += 1

        def query(self, *a, **k):
            class _Q:
                def filter(self, *a, **k):
                    return self

                def order_by(self, *a, **k):
                    class _First:
                        def first(self):
                            return None
                    return _First()

                def filter_by(self, *a, **k):
                    return self

                def one_or_none(self):
                    return None

                def all(self):
                    return []

                def __iter__(self):
                    return iter([])
            return _Q()

    monkeypatch.setattr(svc.ub, "session", _Session(), raising=False)

    result = svc.WholeBookTranslationService().start(1, "EPUB", False, _publish, {})

    assert len(published) == 1
    # 核心断言 1：发布 payload 必须带翻译模板键
    assert published[0]["promptTemplate"] == "reading-paragraph-translate-plain"
    assert published[0]["parameters"]["bookName"] == "Test Book"
    # 核心断言 2：progress 返回 pendingCount（前端区分未完成与失败）
    assert "pendingCount" in result


def test_extract_is_deterministic_and_counts_all_paragraphs(tmp_path):
    """R47 回归：lxml 元素代理被 GC 后 id() 复用，曾导致同一本书三次抽取
    分别得到 759/78/78 段（生产 3177 个 <p> 只剩 128 段）。修复后必须：
    ① 抽取结果确定（多次运行一致）；② 所有顶层块级节点都被保留。"""
    body = "".join(f"<p>Paragraph {i} content.</p>" for i in range(300))
    container = """<container xmlns='urn:oasis:names:tc:opendocument:xmlns:container'><rootfiles><rootfile full-path='OPS/content.opf'/></rootfiles></container>"""
    opf = """<package xmlns='http://www.idpf.org/2007/opf'><manifest>
      <item id='one' href='one.xhtml' media-type='application/xhtml+xml'/>
    </manifest><spine><itemref idref='one'/></spine></package>"""
    # h1 优先作为章节名（Calibre 转换书的 <title> 恒为书名，不能作为章节）
    page = ("<html xmlns='http://www.w3.org/1999/xhtml'><head><title>Book Title</title></head>"
            f"<body><h1>Chapter One</h1>{body}</body></html>")
    path = tmp_path / "big.epub"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("META-INF/container.xml", container)
        archive.writestr("OPS/content.opf", opf)
        archive.writestr("OPS/one.xhtml", page)

    runs = [extract_epub_paragraphs(path) for _ in range(3)]
    counts = {len(r) for r in runs}
    assert len(counts) == 1, f"抽取结果不确定: {counts}"
    assert counts == {300}
    bad = sorted({chapter for chapter, _ in runs[0]})[:3]
    assert bad == ["Chapter One"], f"unexpected chapters: {bad}"
    assert runs[0][0][1] == "Paragraph 0 content."


def test_extract_skips_nested_blocks_and_empty_paragraphs(tmp_path):
    """blockquote 内的 p 不重复处理；全角空格空段不产出；script 内容不出现。"""
    container = """<container xmlns='urn:oasis:names:tc:opendocument:xmlns:container'><rootfiles><rootfile full-path='OPS/content.opf'/></rootfiles></container>"""
    opf = """<package xmlns='http://www.idpf.org/2007/opf'><manifest>
      <item id='one' href='one.xhtml' media-type='application/xhtml+xml'/>
    </manifest><spine><itemref idref='one'/></spine></package>"""
    page = ("<html xmlns='http://www.w3.org/1999/xhtml'><head><title>T</title></head><body>"
            "<blockquote><p>quoted line.</p></blockquote>"
            "<p>\u3000</p>"
            "<p>after empty.</p>"
            "<script>var x = 'nope';</script>"
            "</body></html>")
    path = tmp_path / "nested.epub"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("META-INF/container.xml", container)
        archive.writestr("OPS/content.opf", opf)
        archive.writestr("OPS/one.xhtml", page)

    paragraphs = extract_epub_paragraphs(path)
    texts = [text for _, text in paragraphs]
    assert texts == ["quoted line.", "after empty."]
