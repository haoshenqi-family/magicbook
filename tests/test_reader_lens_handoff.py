"""R141：阅读器内置划词类 AI 能力下线、由 MagicLens 扩展单独承担。

Why 静态锁定：本项能力全在前端（epub.js），没有可跑的浏览器测试；下线语义
是「暂时只留一份实现」，最容易被无意改写（改开关值、或后续给段落按钮加新的
注入点）。故对开关值、三处闸门与必须保留的能力各设断言。

恢复内置形态 = 把 epub.js 的 READER_BUILTIN_AI_UI_ENABLED 置 true，本文件
同步改成断言「开启」，并在 magiclens 侧确认双实现不再冲突。
"""

import os

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EPUB_JS = os.path.join(_ROOT, "cps", "static", "js", "reading", "epub.js")


def _source():
    with open(EPUB_JS, encoding="utf-8") as fh:
        return fh.read()


def test_switch_is_declared_off():
    source = _source()
    assert "var READER_BUILTIN_AI_UI_ENABLED = false;" in source


def test_selection_popover_is_off():
    source = _source()
    assert ("function translateSelection(content) {\n"
            "        if (!READER_BUILTIN_AI_UI_ENABLED) return;" in source)


def test_vocabulary_marks_off_but_page_report_still_runs():
    """波浪线标注下线，但 inspectVocabulary 的上报必须保留。

    它是 moon-well 阅读事件流（学情、成就）与 AI 伴读「当前页生词」的数据源，
    连带停掉会把两类与翻译无关的能力一起打断。
    """
    source = _source()
    assert ("function markVocabulary(records) {\n" in source)
    body = source.split("function markVocabulary(records) {", 1)[1].split("\n    }", 1)[0]
    assert "if (!READER_BUILTIN_AI_UI_ENABLED) return;" in body

    inspect = source.split("function inspectVocabulary() {", 1)[1].split("\n    }", 1)[0]
    assert "READER_BUILTIN_AI_UI_ENABLED" not in inspect
    assert "calibre.readingVocabularyUrl" in inspect


def test_paragraph_translate_button_not_injected():
    source = _source()
    assert ("if (READER_BUILTIN_AI_UI_ENABLED && "
            "!el.querySelector(':scope > .reading-translate-btn'))" in source)


def test_non_conflicting_tools_stay_injected():
    """朗读/批注/伴读按钮与整页「译」「整本译」未受本次下线影响。"""
    source = _source()
    for cls in ("reading-tts-btn", "reading-annotation-btn", "reading-companion-btn"):
        assert ("if (!el.querySelector(':scope > .%s'))" % cls) in source
    assert "getElementById('immersive-translate')" in source
    assert "getElementById('whole-book-translate')" in source
