"""reader 模块源读取（R183 架构评审 B4 批次 1 引入）。

Why：B4 把 `epub.js` 按功能域拆成多文件后，原先「读单文件做静态锁」的守卫会随
搬迁集体失效。本 helper 按 `read.html` 里真实的 `<script src>` 顺序拼接
`js/reading/*.js`，静态锁改读拼接后的整体源码——顺带把「装配顺序」也纳入锁定：
新文件漏插、插错位置（如 reader-core.js 落到 epub.js 之后）都会让断言取不到目标。
"""

import os
import re

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_READING_DIR = os.path.join(_ROOT, "cps", "static", "js", "reading")
_READ_HTML = os.path.join(_ROOT, "cps", "templates", "read.html")

_SCRIPT_RE = re.compile(r"js/reading/([A-Za-z0-9_.-]+\.js)")


def reader_module_order():
    """read.html 中 js/reading/*.js 的出现顺序（去重、保持首次出现）。"""
    with open(_READ_HTML, encoding="utf-8") as handle:
        html = handle.read()
    ordered = []
    for name in _SCRIPT_RE.findall(html):
        if name not in ordered:
            ordered.append(name)
    return ordered


def reader_source(name):
    path = os.path.join(_READING_DIR, name)
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def reader_blob():
    """全部 reader 模块按载入顺序拼接后的源码。"""
    names = reader_module_order()
    assert names, "read.html 未找到任何 js/reading/*.js 载入项"
    assert "epub.js" in names, "read.html 未载入 epub.js（装配层丢失）"
    return "\n".join(reader_source(name) for name in names)
