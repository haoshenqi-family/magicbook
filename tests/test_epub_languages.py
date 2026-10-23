"""R214 子项 A：EPUB 多语言导入回归。

Why: 「双语书只标 English」的机制性根因是 get_epub_info 只取第一条 dc:language
     （QA §四）。反向变异：把语言收集改回 tmp[0] → 双语用例立即报红。

注意：cps.epub / cps.web 的 import 链经 helper→gdriveutils 需 app 初始化
（test_book_import 同款教训），因此按需延迟 import，不在模块级导入。
"""
import os
import shutil
import tempfile
import zipfile

import pytest


@pytest.fixture
def tmp_dir(request):
    """pytest 自带 tmp_path 在本环境被沙箱 mkdir 拦截，改用 tempfile（conftest 同款）。"""
    d = tempfile.mkdtemp(prefix="r214_epub_")
    yield d
    shutil.rmtree(d, ignore_errors=True)

NS_CONTAINER = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">'
    '<rootfiles><rootfile full-path="OEBPS/content.opf" '
    'media-type="application/oebps-package+xml"/></rootfiles></container>'
)


def _opf(languages_xml):
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="uid">'
        '<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">'
        '<dc:title>Test Book</dc:title><dc:creator>Tester</dc:creator>'
        '<dc:identifier id="uid">test-r214</dc:identifier>'
        '{0}'
        '</metadata>'
        '<manifest><item id="c1" href="chapter.xhtml" media-type="application/xhtml+xml"/></manifest>'
        '<spine><itemref idref="c1"/></spine>'
        '</package>'
    ).format(languages_xml)


def _make_epub(tmp_dir, languages_xml):
    path = os.path.join(tmp_dir, "test.epub")
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("mimetype", "application/epub+zip")
        zf.writestr("META-INF/container.xml", NS_CONTAINER)
        zf.writestr("OEBPS/content.opf", _opf(languages_xml))
        zf.writestr("OEBPS/chapter.xhtml", "<html><body><p>hello</p></body></html>")
    return path


def _info(path):
    from cps.epub import get_epub_info
    return get_epub_info(path, "test.epub", ".epub", True)


def test_dual_language_epub_exports_both(tmp_dir):
    """双语 EPUB（eng+chi）两个声明都要落库，一个都不能丢。"""
    path = _make_epub(tmp_dir, "<dc:language>eng</dc:language><dc:language>chi</dc:language>")
    codes = _info(path).languages.split(",")
    assert codes == ["eng", "chi"]


def test_single_language_epub(tmp_dir):
    path = _make_epub(tmp_dir, "<dc:language>en-US</dc:language>")
    assert _info(path).languages == "eng"


def test_missing_language_epub_returns_empty(tmp_dir):
    path = _make_epub(tmp_dir, "")
    assert _info(path).languages == ""


def test_duplicate_language_deduped(tmp_dir):
    path = _make_epub(tmp_dir, "<dc:language>eng</dc:language><dc:language>en-GB</dc:language>")
    assert _info(path).languages == "eng"
