"""Markdown → EPUB 构建器。

产物沿用 book #89 已验证结构（OEBPS/ + nav.xhtml + toc.ncx + content.opf，
mimetype 首位不压缩）。文章按 H1 切章，首个 H1 之前的内容进前言。
"""
import hashlib
import html as html_mod
import io
import mimetypes
import os
import re
import zipfile

import markdown

XHTML_NS = ('xmlns="http://www.w3.org/1999/xhtml" '
            'xmlns:epub="http://www.idpf.org/2007/ops"')

_SCRIPT_STRIP_RE = re.compile(
    r"<(script|iframe|object|embed|form)\b.*?</\1>", re.S | re.I)
_SCRIPT_SELF_RE = re.compile(r"<(script|iframe|object|embed|form)\b[^>]*/?>", re.I)
_ONATTR_RE = re.compile(r"\son\w+\s*=\s*(\"[^\"]*\"|'[^']*'|[^\s>]+)", re.I)
_JS_HREF_RE = re.compile(r"(href|src)\s*=\s*(\"|')\s*javascript:[^\"']*(\"|')", re.I)
_IMG_SRC_RE = re.compile(r"<img\b[^>]*?src=\"([^\"]+)\"[^>]*>", re.I)
_H1_RE = re.compile(r"^# (.*\S)\s*$")


def _style_css():
    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, "templates", "magicbook", "style.css"),
              encoding="utf-8") as f:
        return f.read()


def sanitize_html(body):
    body = _SCRIPT_STRIP_RE.sub("", body)
    body = _SCRIPT_SELF_RE.sub("", body)
    body = _ONATTR_RE.sub("", body)
    body = _JS_HREF_RE.sub(r'\1=""', body)
    return body


def split_chapters(md_text):
    """返回 [(标题或 None, 正文 markdown)]；首个 H1 之前为前言。"""
    sections = []
    current_title, lines = None, []
    in_fence = False
    for line in md_text.splitlines():
        if line.strip().startswith("```"):
            in_fence = not in_fence
        m = None if in_fence else _H1_RE.match(line)
        if m:
            sections.append((current_title, "\n".join(lines)))
            current_title, lines = m.group(1), []
        else:
            lines.append(line)
    sections.append((current_title, "\n".join(lines)))
    return sections


def _render(md_text):
    body = markdown.markdown(
        md_text, extensions=["extra", "sane_lists", "fenced_code", "tables"])
    return sanitize_html(body)


def _ext(url, content):
    guess = mimetypes.guess_type(url.split("?")[0])[0]
    ext_map = {"image/jpeg": ".jpg", "image/png": ".png",
               "image/gif": ".gif", "image/webp": ".webp"}
    if guess in ext_map:
        return ext_map[guess]
    if content[:8] == b"\x89PNG\r\n\x1a\n":
        return ".png"
    if content[:3] == b"\xff\xd8\xff":
        return ".jpg"
    return ".png"


def _process_images(body, halo_client, images):
    """下载正文图片到 images/ 并重写 src；失败保留原 URL（阅读器联网可读）。"""
    def repl(match):
        whole, src = match.group(0), match.group(1)
        if src.startswith("images/") or not re.match(r"^(https?:)?/", src):
            return whole
        try:
            content = halo_client.download(src)
        except Exception:
            return whole
        suffix = _ext(src, content)
        name = "images/img%d%s" % (len(images) + 1, suffix)
        images[name] = content
        return whole.replace(src, name)
    return _IMG_SRC_RE.sub(repl, body)


def _nav_point(order, text, href):
    return ('    <navPoint id="np%d" playOrder="%d">\n'
            '      <navLabel><text>%s</text></navLabel>\n'
            '      <content src="%s"/>\n    </navPoint>\n'
            % (order, order, text, href))


class EpubBuilder:
    def __init__(self, meta):
        self.meta = meta
        self.lang = meta.get("lang", "en")
        self.images = {}

    def _xhtml(self, title, body):
        esc = html_mod.escape(title, quote=True)
        return ("<?xml version=\"1.0\" encoding=\"utf-8\"?>\n<!DOCTYPE html>\n"
                f"<html {XHTML_NS} xml:lang=\"{self.lang}\" lang=\"{self.lang}\">\n"
                "<head><meta charset=\"utf-8\"/><title>"
                f"{esc}</title><link rel=\"stylesheet\" type=\"text/css\" "
                'href="style.css"/></head>\n'
                f"<body>\n{body}\n</body>\n</html>\n")

    def _chapter(self, md_text, title):
        body = _process_images(_render(md_text), self.halo, self.images)
        return f"<h1>{html_mod.escape(title)}</h1>\n{body}"

    def build(self, md_text, out_path, halo_client, source_ref=None):
        self.halo = halo_client
        sha = hashlib.sha256(md_text.encode("utf-8")).hexdigest()
        sections = [s for s in split_chapters(md_text) if s[1].strip() or s[0]]
        if sections and sections[0][0] is None:
            preface_md, rest = sections[0][1], sections[1:]
        else:
            preface_md, rest = "", sections

        chapters = []
        if preface_md.strip():
            title = self.meta.get("preface_title", "Preface")
            chapters.append(("preface.xhtml",
                             self._chapter(preface_md, title), title))
        for i, (title, md) in enumerate(rest, 1):
            if not title:
                continue
            chapters.append((f"ch{i}.xhtml", self._chapter(md, title), title))

        colophon_title = self.meta.get("colophon_title", "About This Book")
        slug = self.meta.get("slug", "")
        colophon_body = (
            f"<h1>{html_mod.escape(colophon_title)}</h1>"
            f"<p>Source of truth: Halo blog post <code>{html_mod.escape(slug)}</code>.</p>"
            + (f'<p class="source-ref">{html_mod.escape(source_ref)}</p>'
               if source_ref else ""))

        files = {"style.css": _style_css().encode("utf-8")}
        for name, content in self.images.items():
            files[name] = content

        title_page = self._xhtml(self.meta["title"], (
            '<div class="titlepage">'
            f'<h1>{html_mod.escape(self.meta["title"])}</h1>'
            f'<p class="author">{html_mod.escape(self.meta.get("creator", ""))}'
            "</p></div>"))
        files["title.xhtml"] = title_page.encode("utf-8")

        nav_items = "\n".join(
            f'<li><a href="{h}">{html_mod.escape(t)}</a></li>'
            for h, _, t in chapters)
        files["nav.xhtml"] = self._xhtml("Contents", (
            '<nav epub:type="toc" id="toc"><h1>Contents</h1><ol>'
            f"{nav_items}</ol></nav>")).encode("utf-8")

        for href, body, title in chapters:
            files[href] = self._xhtml(title, body).encode("utf-8")
        files["colophon.xhtml"] = self._xhtml(
            colophon_title, colophon_body).encode("utf-8")

        manifest = ['    <item id="nav" href="nav.xhtml" '
                    'media-type="application/xhtml+xml" properties="nav"/>',
                    '    <item id="ncx" href="toc.ncx" '
                    'media-type="application/x-dtbncx+xml"/>',
                    '    <item id="css" href="style.css" media-type="text/css"/>',
                    '    <item id="title" href="title.xhtml" '
                    'media-type="application/xhtml+xml"/>',
                    '    <item id="colophon" href="colophon.xhtml" '
                    'media-type="application/xhtml+xml"/>']
        spine = ["    <itemref idref=\"title\"/>", "    <itemref idref=\"nav\"/>"]
        ncx = [_nav_point(1, "Cover", "title.xhtml"),
               _nav_point(2, "Contents", "nav.xhtml")]
        for i, (href, _, title) in enumerate(chapters):
            item_id = os.path.splitext(href)[0]
            manifest.append(f'    <item id="{item_id}" href="{href}" '
                            'media-type="application/xhtml+xml"/>')
            spine.append(f'    <itemref idref="{item_id}"/>')
            ncx.append(_nav_point(i + 3, html_mod.escape(title), href))
        spine.append("    <itemref idref=\"colophon\"/>")
        for i, name in enumerate(sorted(self.images)):
            mime = mimetypes.guess_type(name)[0] or "image/png"
            manifest.append(f'    <item id="img{i}" href="{name}" '
                            f'media-type="{mime}"/>')

        opf = ("<?xml version=\"1.0\" encoding=\"utf-8\"?>\n"
               '<package xmlns="http://www.idpf.org/2007/opf" version="3.0" '
               f'unique-identifier="bookid" xml:lang="{self.lang}">\n'
               '  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">\n'
               f'    <dc:identifier id="bookid">{self.meta["identifier"]}</dc:identifier>\n'
               f'    <dc:title>{html_mod.escape(self.meta["title"])}</dc:title>\n'
               f'    <dc:creator>{html_mod.escape(self.meta.get("creator", ""))}</dc:creator>\n'
               f"    <dc:language>{self.lang}</dc:language>\n"
               f'    <dc:date>{self.meta.get("date", "")}</dc:date>\n'
               f'    <meta property="dcterms:modified">{self.meta.get("modified", "")}</meta>\n'
               "  </metadata>\n  <manifest>\n"
               + "\n".join(manifest) + "\n  </manifest>\n  <spine toc=\"ncx\">\n"
               + "\n".join(spine) + "\n  </spine>\n"
               '  <guide><reference type="cover" title="Cover" href="title.xhtml"/></guide>\n'
               "</package>\n")
        files["content.opf"] = opf.encode("utf-8")

        ncx_doc = ("<?xml version=\"1.0\" encoding=\"utf-8\"?>\n"
                   '<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1" '
                   f'xml:lang="{self.lang}">\n  <head>\n'
                   f'    <meta name="dtb:uid" content="{self.meta["identifier"]}"/>\n'
                   '    <meta name="dtb:depth" content="1"/>\n'
                   '    <meta name="dtb:totalPageCount" content="0"/>\n'
                   '    <meta name="dtb:maxPageNumber" content="0"/>\n  </head>\n'
                   f'  <docTitle><text>{html_mod.escape(self.meta["title"])}</text></docTitle>\n'
                   "  <navMap>\n" + "\n".join(ncx) + "\n  </navMap>\n</ncx>\n")
        files["toc.ncx"] = ncx_doc.encode("utf-8")

        container = ('<?xml version="1.0" encoding="UTF-8"?>\n'
                     '<container version="1.0" '
                     'xmlns="urn:oasis:names:tc:opendocument:xmlns:container">\n'
                     "  <rootfiles>\n"
                     '    <rootfile full-path="OEBPS/content.opf" '
                     'media-type="application/oebps-package+xml"/>\n'
                     "  </rootfiles>\n</container>\n")

        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            info = zipfile.ZipInfo("mimetype")
            info.compress_type = zipfile.ZIP_STORED
            zf.writestr(info, "application/epub+zip")
            zf.writestr("META-INF/container.xml", container)
            for name in sorted(files):
                zf.writestr("OEBPS/" + name, files[name])
        with open(out_path, "wb") as f:
            f.write(buf.getvalue())
        return sha
