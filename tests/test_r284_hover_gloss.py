"""R284 静态守卫：生词 hover 释义恢复 + 页面引导入口下线。

Why 两条都要锁：
  1. R42 下线 span.title 后，R268 把 cursor:help 注入 iframe 让「问号光标」
     重新可见，却仍没有释义；这个「只有问号、没有内容」的组合很容易被
     后续顺手改回去（尤其 R261 的 gloss 开关与 R139 移除的 translation 死字段）。
  2. 引导入口曾三处并存（阅读器右下胶囊 / /me 阅读设置 / 自动邀请卡），
     用户拍板只留右上角 Help；任何一处复活都会重新挡住阅读区。
"""
import os

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _read(rel):
    with open(os.path.join(_ROOT, rel), encoding="utf-8") as handle:
        return handle.read()


def test_生词悬停释义用_gloss_且不含冗长历史文案():
    js = _read("cps/static/js/reading/epub.js")
    marker = js.split("function markVocabulary(records)", 1)[1].split(
        "function inspectVocabulary()", 1
    )[0]
    assert "var hoverGloss = cleanGloss(record.gloss);" in marker
    assert "if (hoverGloss) span.title = hoverGloss;" in marker
    assert "上次：" not in marker, "R42 下线的「释义 + 上次：书·章节」长串不得复活"
    assert "record.translation" not in marker, "R139 已移除 translation 死字段"
    # 波浪线仍在，但问号光标已下线（R284 验收缺陷修复）
    core = _read("cps/static/js/reading/reader-core.js")
    assert "reading-vocabulary-unknown{text-decoration:underline wavy" in core
    assert "cursor:pointer" in core and "cursor:help" not in core


def test_问号光标下线且_hover_即时卡片与翻译兜底齐备():
    """R284 验收缺陷：只补 span.title 时，hover 仍只有 cursor:help 的问号光标；
       原生 tooltip 要等约 1 秒且 gloss=null 时不生成。改为立即弹卡 + 划词翻译兜底。"""
    import re

    js = _read("cps/static/js/reading/epub.js")
    for token in (
        "function cleanGloss(", "function showVocabHoverCard(", "function lookupVocabHover(",
        "function bindVocabHover(", "bindVocabHover(doc);", "reading-vocab-hover-card",
        "calibre.readingTranslationUrl", "hoverTranslation", "cleanGloss(record.gloss)",
    ):
        assert token in js, f"hover 释义卡链路缺 {token}"
    assert "cursor: help" not in js

    css = re.sub(r"/\*.*?\*/", "", _read("cps/static/css/reader.css"), flags=re.S)
    assert ".reading-vocab-hover-card" in css
    assert "cursor: help" not in css and "cursor:help" not in css
    core = _read("cps/static/js/reading/reader-core.js")
    assert "cursor:help" not in core


def test_gloss_开关不联动_hover_释义():
    js = _read("cps/static/js/reading/epub.js")
    marker = js.split("function remarkVocabularyForGlossToggle()", 1)[1].split(
        "// ===== R284 验收缺陷修复", 1
    )[0]
    assert "span.title" not in marker, "开关只管行内小字，不该清掉 hover 释义"


def test_页面引导入口只剩右上角_Help():
    settings = _read("cps/templates/reading_settings.html")
    assert "reading-onboarding-start" not in settings
    assert "reading-onboarding" not in settings
    prefs = _read("cps/static/js/reading-preferences.js")
    assert "reading-onboarding-start" not in prefs

    js = _read("cps/static/js/onboarding.js")
    run = js.split("function runSegment(segment)", 1)[1].split("\n  }", 1)[0]
    assert "showInvite(" not in run and "showReaderHelp()" not in run
    again = js.split("function showEntryAgainIfNeeded(segment)", 1)[1].split("\n  }", 1)[0]
    assert "showReaderHelp()" not in again

    layout = _read("cps/templates/layout.html")
    assert layout.count('id="top_onboarding"') == 1
    assert "Help" in layout


def test_i18n_收尾文案与右上角入口同源():
    text = "Open Help in the top-right corner to replay this tour."
    seed = _read("cps/templates/i18n_seed.html")
    js = _read("cps/static/js/onboarding.js")
    assert text in seed and text in js
    assert "bottom-right" not in seed and "bottom-right" not in js
    po = _read("cps/translations/zh_Hans_CN/LC_MESSAGES/messages.po")
    assert text in po and "使用引导" in po
