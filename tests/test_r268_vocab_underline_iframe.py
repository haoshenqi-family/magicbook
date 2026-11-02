"""R268：阅读器生词波浪线样式必须注入 EPUB iframe。

Why 静态锁定：EPUB 正文由 epub.js 渲染在同源 iframe 内，父页 `reader.css` 的规则
**不会**跨文档作用到 iframe。此前 `.reading-vocabulary-unknown` 只写在父页
`reader.css`，`markVocabulary` 虽把词包成 span，iframe 内却没有下划线规则，
线上表现为「/ajax/reading-vocabulary 正常返回生词、页面却不显示，刷新也不恢复，
只有 MagicLens 重新扫描才出现」。修复把基础样式放进 `READER_TOOLS_STYLE`，由
`injectReaderToolsStyle(doc)` 注入每个正文 iframe；本用例锁住这条注入链不再退化。
"""

import os

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _read(rel):
    with open(os.path.join(_ROOT, rel), encoding="utf-8") as handle:
        return handle.read()


def test_iframe_style_包含生词波浪线基础规则():
    css = _read("cps/static/js/reading/reader-core.js")
    # 波浪下划线基础规则（父页 reader.css 不跨 iframe，必须在注入样式里再声明一次）
    assert ".reading-vocabulary-unknown{text-decoration:underline wavy" in css, \
        "生词波浪线基础规则必须随 READER_TOOLS_STYLE 注入正文 iframe"
    assert ".reading-vocabulary-unknown:hover{" in css, \
        "悬停高亮规则同样需注入 iframe，否则父页规则在正文内无效"


def test_注入工具样式仍由_rendered_链路写入每个正文文档():
    core = _read("cps/static/js/reading/reader-core.js")
    tts = _read("cps/static/js/reading/reader-tts.js")
    # reader-core 暴露单点注入，reader-tts 在 rendered 时对每个 content.document 调用
    assert "injectToolsStyle: injectReaderToolsStyle" in core
    assert "injectReaderToolsStyle(doc)" in tts
    assert "style.id = 'reading-tools-style'" in core
