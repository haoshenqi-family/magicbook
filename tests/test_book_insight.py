"""R214 B：内容速览解析（cps/reading_insight/parser.py）单测。

Why: 详情页三区块与代价面板的量全部消费这一个 parse() 产物——章节/段数/词数/
     语言/摘录任一算错，代价面板给用户的「约 N 积分」就是错误结论（LLD §10）。
     反向变异示例：摘录预算改成「超限截半段」→ test_large_book_drops_excerpt 报红；
     nav 层级回退写死 1 → test_nav_nested_levels 报红。
"""
import os
import shutil
import tempfile
import zipfile

import pytest


@pytest.fixture
def tmp_dir(request):
    """pytest 自带 tmp_path 在本环境被沙箱 mkdir 拦截，改用 tempfile（conftest 同款）。"""
    d = tempfile.mkdtemp(prefix="r214_insight_")
    yield d
    shutil.rmtree(d, ignore_errors=True)


NS_CONTAINER = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">'
    '<rootfiles><rootfile full-path="OEBPS/content.opf" '
    'media-type="application/oebps-package+xml"/></rootfiles></container>'
)

NAV_XHTML = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<html xmlns="http://www.w3.org/1999/xhtml" '
    'xmlns:epub="http://www.idpf.org/2007/ops"><body>'
    '<nav epub:type="toc"><ol>'
    '<li><a href="c1.xhtml">Chapter 1</a><ol>'
    '<li><a href="c2.xhtml">Section 1.1</a></li>'
    '</ol></li>'
    '<li><a href="c3.xhtml">Chapter 2</a></li>'
    '</ol></nav></body></html>'
)

NCX = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1"><navMap>'
    '<navPoint id="n1"><navLabel><text>Chapter 1</text></navLabel>'
    '<content src="c1.xhtml"/>'
    '<navPoint id="n2"><navLabel><text>Section 1.1</text></navLabel>'
    '<content src="c2.xhtml"/></navPoint>'
    '</navPoint>'
    '<navPoint id="n3"><navLabel><text>Chapter 2</text></navLabel>'
    '<content src="c3.xhtml"/></navPoint>'
    '</navMap></ncx>'
)


def _opf(languages_xml, nav_item, filenames):
    items = "".join(
        '<item id="i{0}" href="{1}" media-type="application/xhtml+xml"/>'.format(n, f)
        for n, f in enumerate(filenames, 1))
    spine = "".join(
        '<itemref idref="i{0}"/>'.format(n) for n, _ in enumerate(filenames, 1))
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="uid">'
        '<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">'
        '<dc:title>Test Book</dc:title><dc:creator>Tester</dc:creator>'
        '<dc:identifier id="uid">test-insight</dc:identifier>'
        '{0}'
        '</metadata>'
        '<manifest>'
        '{1}'
        '{2}'
        '</manifest>'
        '<spine>{3}</spine>'
        '</package>'
    ).format(languages_xml, nav_item, items, spine)


def _chapter_xhtml(title, paragraphs):
    body = "".join("<p>%s</p>" % p for p in paragraphs)
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<html xmlns="http://www.w3.org/1999/xhtml"><head><title>%s</title></head>'
            '<body><h1>%s</h1>%s</body></html>' % (title, title, body))


def _make_epub(tmp_dir, languages_xml, nav_item="", files=None, spine=None, name="test.epub"):
    path = os.path.join(tmp_dir, name)
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("mimetype", "application/epub+zip")
        zf.writestr("META-INF/container.xml", NS_CONTAINER)
        zf.writestr("OEBPS/content.opf", _opf(languages_xml, nav_item, spine or []))
        for fname, content in (files or {}).items():
            zf.writestr("OEBPS/%s" % fname, content)
    return path


def _three_chapter_book(tmp_dir, languages_xml="<dc:language>eng</dc:language>",
                        with_nav=True, with_ncx=False):
    nav_item = ""
    files = {
        "c1.xhtml": _chapter_xhtml("Chapter 1", ["Hello world.", "Second paragraph of one."]),
        "c2.xhtml": _chapter_xhtml("Section 1.1", ["Nested section text here."]),
        "c3.xhtml": _chapter_xhtml("Chapter 2", ["Third chapter body text."]),
    }
    spine = ["c1.xhtml", "c2.xhtml", "c3.xhtml"]
    if with_nav:
        nav_item = ('<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" '
                    'properties="nav"/>')
        files["nav.xhtml"] = NAV_XHTML
    if with_ncx:
        nav_item += ('<item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>')
        files["toc.ncx"] = NCX
    return _make_epub(tmp_dir, languages_xml, nav_item, files, spine)


def _parse(path):
    from cps.reading_insight.parser import parse
    return parse(path)


def test_single_language_epub_stats(tmp_dir):
    """单语言 EPUB：章/段/字符/词数/摘录都要有，语言只报声明的那一个。"""
    result = _parse(_three_chapter_book(tmp_dir))
    assert result["declaredLanguages"] == ["eng"]
    assert len(result["chapters"]) == 3
    assert result["paragraphCount"] == 4
    assert result["charCount"] > 0
    assert result["englishWordCount"] > 0
    assert result["excerpt"], "首章起的摘录不应为空"
    assert result["excerpt"][0]["chapter"] == "Chapter 1"


def test_dual_language_epub_declares_both(tmp_dir):
    """双语 EPUB 的两个 dc:language 声明都要进 declaredLanguages（与 A 的导入回归同口径）。"""
    result = _parse(_three_chapter_book(
        tmp_dir,
        "<dc:language>eng</dc:language><dc:language>chi</dc:language>"))
    assert result["declaredLanguages"] == ["eng", "chi"]


def test_nav_nested_levels(tmp_dir):
    """nav 嵌套 <ol> 的层级要进 level（1 / 2 / 1），不是全部写死 1。"""
    result = _parse(_three_chapter_book(tmp_dir))
    levels = [(ch["title"], ch["level"]) for ch in result["chapters"]]
    assert ("Chapter 1", 1) in levels
    assert ("Section 1.1", 2) in levels
    assert ("Chapter 2", 1) in levels


def test_no_nav_fallback_per_file(tmp_dir):
    """无 nav/ncx 时按 spine 文件退化计章：level 全 1，标题退化到 h1/title。"""
    result = _parse(_three_chapter_book(tmp_dir, with_nav=False))
    assert [ch["title"] for ch in result["chapters"]] == ["Chapter 1", "Section 1.1", "Chapter 2"]
    assert all(ch["level"] == 1 for ch in result["chapters"])


def test_ncx_fallback(tmp_dir):
    """无 nav 但有 toc.ncx 时按 navPoint 深度取层级与标题。"""
    result = _parse(_three_chapter_book(tmp_dir, with_nav=False, with_ncx=True))
    levels = [(ch["title"], ch["level"]) for ch in result["chapters"]]
    assert ("Section 1.1", 2) in levels


def test_large_book_drops_excerpt(tmp_dir):
    """大书（解析量超限）只出 chapters + 统计，不出摘录（LLD §3）——预算截半段也算错。"""
    import cps.reading_insight.parser as parser_mod
    path = _three_chapter_book(tmp_dir)
    saved = parser_mod.MAX_PARSE_BYTES
    parser_mod.MAX_PARSE_BYTES = 10
    try:
        result = _parse(path)
    finally:
        parser_mod.MAX_PARSE_BYTES = saved
    assert result["excerpt"] == []
    assert len(result["chapters"]) == 3
    assert result["paragraphCount"] == 4


def test_excerpt_budget_capped(tmp_dir):
    """摘录总正文字符 ≤1200，且首段截断带省略号语义（firstParagraph ≤200+1）。"""
    import cps.reading_insight.parser as parser_mod
    result = _parse(_three_chapter_book(tmp_dir))
    total = sum(len(e["text"]) for e in result["excerpt"])
    assert total <= parser_mod.EXCERPT_MAX_CHARS
    for ch in result["chapters"]:
        assert len(ch["firstParagraph"]) <= parser_mod.FIRST_PARAGRAPH_MAX_CHARS + 1
    assert result["chapters"][0]["firstParagraph"] == "Hello world."


def test_first_paragraph_and_counts_per_chapter(tmp_dir):
    result = _parse(_three_chapter_book(tmp_dir))
    assert result["chapters"][0]["paragraphCount"] == 2
    assert result["chapters"][1]["paragraphCount"] == 1
    assert result["chapters"][2]["paragraphCount"] == 1
