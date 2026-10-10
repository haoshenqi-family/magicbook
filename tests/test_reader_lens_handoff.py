"""R141/R143/R146：阅读器只在 MagicLens 真正接管处让位（运行时探测，非写死）。

Why 静态锁定：这套让位逻辑全在前端（epub.js），没有可跑的浏览器测试，而它的两种失效
方向都很贵——写死让位 = 没装扩展的人在阅读器里没划词（R141 初版踩过，见 R143）；
完全不让位 = 同页双气泡、一个词两条波浪线（R141 的起因）。R146 改成读 magiclens
v0.8.6 留在 DOM 上的接管标记，本文件锁的就是「探测存在、粒度正确、别退化成开关」。

粒度是两个而不是一个：划词属主是帧内中继（受该 frame 能否注入影响），波浪线属主是
顶层高亮引擎（受 Alt+U / 域名禁用 / 登录态影响）。
"""

import os

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EPUB_JS = os.path.join(_ROOT, "cps", "static", "js", "reading", "epub.js")


def _source():
    with open(EPUB_JS, encoding="utf-8") as fh:
        return fh.read()


def test_probes_read_the_handoff_markers():
    """两个探测函数各读各的标记：帧级 selection、页面级 highlight。"""
    source = _source()
    assert "function lensOwnsSelection(contentDoc) {" in source
    assert "contentDoc.documentElement.dataset.magiclensSelection" in source
    assert "function lensOwnsHighlight() {" in source
    assert "document.documentElement.dataset.magiclensHighlight" in source


def test_no_static_switch_left():
    """R146：写死的开关必须彻底消失，否则探测只是第二套真相源。"""
    assert "LENS_OVERLAP_UI_ENABLED" not in _source()


def test_selection_defers_per_frame():
    source = _source()
    assert ("function translateSelection(content) {\n"
            "        // 扩展正在接管本帧的拖选时不出内置气泡" in source)
    assert "if (lensOwnsSelection(content.document)) return;" in source


def test_highlight_defers_page_level_but_page_report_still_runs():
    """波浪线按顶层标记让位；inspectVocabulary 的上报必须照常——它是 moon-well 阅读
    事件流（学情、成就）与 AI 伴读「当前页生词」的数据源，连带停掉会打断两块无关能力。"""
    source = _source()
    body = source.split("function markVocabulary(records) {", 1)[1].split("\n    }", 1)[0]
    assert "if (lensOwnsHighlight()) return;" in body

    inspect = source.split("function inspectVocabulary() {", 1)[1].split("\n    }", 1)[0]
    assert "lensOwns" not in inspect
    assert "calibre.readingVocabularyUrl" in inspect


def test_paragraph_translate_button_not_gated():
    """段落「译」按钮不门控：magiclens 的段落/整页翻译仍是规划 P1，没有等价实现。"""
    source = _source()
    assert "if (!el.querySelector(':scope > .reading-translate-btn'))" in source
    assert "lensOwns" not in source.split("function injectParagraphTools(content) {", 1)[1] \
        .split("\n    }", 1)[0]


def test_non_taken_over_tools_stay_injected():
    """朗读/批注/伴读按钮与整页「译」「整本译」不受探测影响。"""
    source = _source()
    for cls in ("reading-tts-btn", "reading-annotation-btn", "reading-companion-btn"):
        assert ("if (!el.querySelector(':scope > .%s'))" % cls) in source
    assert "getElementById('immersive-translate')" in source
    assert "getElementById('whole-book-translate')" in source
