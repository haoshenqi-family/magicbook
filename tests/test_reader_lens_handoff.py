"""R141/R143：阅读器内与 MagicLens 重叠的 UI 下线，其余能力保持可用。

Why 静态锁定：本项能力全在前端（epub.js），没有可跑的浏览器测试；边界语义是
「**只下线 magiclens 已经做出来的部分**，避免同页两套实现重复、打架」，最容易
被无意改写（改开关值、或把未重复的段落翻译也顺手收掉——R141 初版就划错过一次，
见 R143）。故对开关值、两处闸门、以及必须留在阅读器里的能力各设断言。

恢复内置形态 = 把 epub.js 的 LENS_OVERLAP_UI_ENABLED 置 true，本文件同步改成
断言「开启」，并在 magiclens 侧确认双实现不再冲突。
"""

import os

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EPUB_JS = os.path.join(_ROOT, "cps", "static", "js", "reading", "epub.js")


def _source():
    with open(EPUB_JS, encoding="utf-8") as fh:
        return fh.read()


def test_switch_is_declared_off():
    assert "var LENS_OVERLAP_UI_ENABLED = false;" in _source()


def test_selection_popover_is_off():
    """magiclens 已有划词气泡（README：划词翻译 ✅），内置的不再弹出。"""
    source = _source()
    assert ("function translateSelection(content) {\n"
            "        if (!LENS_OVERLAP_UI_ENABLED) return;" in source)


def test_vocabulary_marks_off_but_page_report_still_runs():
    """波浪线标注下线，但 inspectVocabulary 的上报必须保留。

    它是 moon-well 阅读事件流（学情、成就）与 AI 伴读「当前页生词」的数据源，
    连带停掉会把两类与翻译无关的能力一起打断。
    """
    source = _source()
    body = source.split("function markVocabulary(records) {", 1)[1].split("\n    }", 1)[0]
    assert "if (!LENS_OVERLAP_UI_ENABLED) return;" in body

    inspect = source.split("function inspectVocabulary() {", 1)[1].split("\n    }", 1)[0]
    assert "LENS_OVERLAP_UI_ENABLED" not in inspect
    assert "calibre.readingVocabularyUrl" in inspect


def test_paragraph_translate_button_not_gated():
    """R143：段落「译」按钮留在阅读器——magiclens 的段落/整页翻译仍是规划 P1。

    断言反向锁定：注入条件里不得出现开关名，否则段落翻译会在阅读器内消失，
    而扩展侧还没有等价实现（该缺陷正是 R141 初版踩过的）。
    """
    source = _source()
    line = "if (!el.querySelector(':scope > .reading-translate-btn'))"
    assert line in source
    assert "LENS_OVERLAP_UI_ENABLED && !el.querySelector(':scope > .reading-translate-btn')" not in source


def test_non_conflicting_tools_stay_injected():
    """朗读/批注/伴读按钮与整页「译」「整本译」未受下线影响。"""
    source = _source()
    for cls in ("reading-tts-btn", "reading-annotation-btn", "reading-companion-btn"):
        assert ("if (!el.querySelector(':scope > .%s'))" % cls) in source
    assert "getElementById('immersive-translate')" in source
    assert "getElementById('whole-book-translate')" in source
