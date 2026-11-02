import io
import zipfile

import pytest

import builder
from builder import EpubBuilder, sanitize_html, split_chapters


class FakeHalo:
    def __init__(self):
        self.downloads = {}

    def download(self, url):
        return self.downloads[url]


MD = """前言段落。

![图](https://note.haoshenqi.top/upload/pic.png)

# 第一章 开始

正文一。

## 小节 A

# 第二章 进阶

```text
# 这不是标题
```

<script>alert(1)</script>
<p onclick="evil()">带事件属性</p>
"""


def test_split_chapters_ignores_h1_in_code_fence():
    sections = split_chapters(MD)
    titles = [t for t, _ in sections]
    assert titles == [None, "第一章 开始", "第二章 进阶"]
    assert "# 这不是标题" in sections[2][1]


def test_sanitize_strips_script_and_on_attributes():
    out = sanitize_html('<p onclick="x()">hi</p><script>bad()</script>')
    assert "onclick" not in out and "script" not in out


def test_build_epub_structure(tmp_path, monkeypatch):
    css = tmp_path / "templates/magicbook/style.css"
    css.parent.mkdir(parents=True)
    css.write_text("body{}")
    monkeypatch.setattr(builder, "_style_css", lambda: "body{}")

    halo = FakeHalo()
    halo.downloads["https://note.haoshenqi.top/upload/pic.png"] = \
        b"\x89PNG\r\n\x1a\n" + b"0" * 20

    meta = {"title": "T", "creator": "C", "lang": "en",
            "identifier": "urn:uuid:x", "date": "2026-09-30",
            "modified": "2026-09-30T00:00:00Z", "slug": "s"}
    out = tmp_path / "out/ab12.epub"
    sha = EpubBuilder(meta).build(MD, str(out), halo, source_ref="halo:s@sha256:x")

    assert sha.isalnum() and len(sha) == 64
    with zipfile.ZipFile(out) as zf:
        names = zf.namelist()
        assert names[0] == "mimetype"
        assert zf.read("mimetype") == b"application/epub+zip"
        assert zf.getinfo("mimetype").compress_type == zipfile.ZIP_STORED
        assert "META-INF/container.xml" in names
        for required in ["OEBPS/preface.xhtml", "OEBPS/ch1.xhtml",
                         "OEBPS/ch2.xhtml", "OEBPS/colophon.xhtml",
                         "OEBPS/nav.xhtml", "OEBPS/toc.ncx",
                         "OEBPS/content.opf", "OEBPS/images/img1.png"]:
            assert required in names
        preface = zf.read("OEBPS/preface.xhtml").decode()
        assert 'src="images/img1.png"' in preface
        ch2 = zf.read("OEBPS/ch2.xhtml").decode()
        assert "<script" not in ch2 and "onclick" not in ch2
        assert "第二章 进阶" in ch2
        opf = zf.read("OEBPS/content.opf").decode()
        assert 'href="images/img1.png"' in opf  # 图片必须进 manifest
        assert 'media-type="application/xhtml+xml"' in opf
        nav = zf.read("OEBPS/nav.xhtml").decode()
        assert nav.index("ch1.xhtml") < nav.index("ch2.xhtml")
