"""R270：阅读器 bookUrl 必须小写化格式段。

Why 静态锁定：`serve_book` 在大小写敏感文件系统上按「URL 段原样」拼数据文件扩展名
（web.py `send_from_directory(..., data.name + "." + book_format)`），库内 Calibre
落盘的扩展名恒为小写（如 `Matilda - Roald Dahl.epub`）。而 /read/<id>/<book_format>
的入口里，首页继续阅读（home.html，R213-C）把阅读进度记录里的大写格式（EPUB）原样
透传，read.html 再透传给 `url_for('web.serve_book', ...)` → 请求 `/show/<id>/EPUB/…`
→ 文件按 `.EPUB` 查找 NotFound → epub.js 拿不到书文件、阅读器永久空白
（2026-11-02 截图会话实测：/show/145/EPUB 404、/show/145/epub 200）。
修复在 read.html 单点 `book_format|lower`；本用例锁住这条不再退化。
"""

import os

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _read(rel):
    with open(os.path.join(_ROOT, rel), encoding="utf-8") as handle:
        return handle.read()


def test_read_html_的_bookUrl_格式段必须小写():
    html = _read("cps/templates/read.html")
    needle = "bookUrl: \"{{ url_for('web.serve_book', book_id=bookid, book_format=book_format|lower, anyname='file.epub') }}\","
    assert needle in html, (
        "read.html 的 bookUrl 必须以 book_format|lower 生成——大写格式段会让 "
        "serve_book 在大小写敏感文件系统上找 <name>.EPUB 而 404，阅读器空白"
    )
    # 防回退：不允许再出现不带 |lower 的原样透传
    assert "book_format=book_format, anyname='file.epub'" not in html, (
        "不允许回退为大小写原样透传（R270 事故形态）"
    )
