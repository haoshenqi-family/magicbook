"""R215 阅读器与 AI 伴读面板的形制守卫（MB-14）。

Why：本轮改的是「可见性 / 停靠 / 状态反馈 / 翻译承载形态」四类体验问题，
其中三条最容易在后续重构里被无意改回去：
  1. 译文重新插回正文流 → 分页列重排抖动回归；
  2. 「思考中」重新挪回 streamChat → PDF 又出现十几秒空白；
  3. QAF 顶栏/段尾控件重新缩回 10px 图标 → 触屏不可点。
本用例按源码形制钉住这些契约，不依赖浏览器运行。
"""

import os

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _read(rel):
    with open(os.path.join(_ROOT, rel), encoding="utf-8") as handle:
        return handle.read()


def test_顶栏有文字标签与更多菜单():
    html = _read("cps/templates/read.html")
    assert 'id="title-more"' in html, "窄屏「更多」入口缺失"
    assert 'id="title-more-menu"' in html, "「更多」菜单容器缺失"
    assert html.count('class="tb-label"') >= 6, "顶栏文字标签未铺开"
    for anchor in ('id="immersive-translate"', 'id="tts-book"', 'id="bookmark"',
                   'id="setting"', 'id="fullscreen"'):
        assert anchor in html, "既有工具锚点丢失：%s" % anchor
    css = _read("cps/static/css/reader.css")
    assert ".reader-main #titlebar a.tb-tool" in css
    assert "min-width: 44px" in css and "min-height: 44px" in css, "触屏触达盒未到 44px"
    assert ".reader-main #titlebar a.tb-tool .tb-label { display: none; }" in css, \
        "窄屏未隐藏文字标签"


def test_顶栏节点搬家不克隆():
    js = _read("cps/static/js/reading/reader-toolbar.js")
    assert "menu.appendChild(el)" in js, "窄屏未把工具节点搬进菜单"
    assert "more.parentNode.insertBefore(el, more)" in js, "宽屏未把节点搬回原位"
    assert "cloneNode" not in js and "innerHTML" not in js, \
        "禁止复制节点：会重复 ID 并丢事件监听"


def test_译文恢复段内内联():
    """2026-10-23 验收回滚：译文回到段落下方，接受重分页。"""
    html = _read("cps/templates/read.html")
    assert "translation-rail" not in html, "右栏 DOM 应已删除"
    immersive = _read("cps/static/js/reading/reader-immersive.js")
    for required in ("insertTranslation", "applyImmersiveTranslation",
                     "restoreCachedTranslations", "translationEnabled"):
        assert required in immersive, "译文段内实现缺失：%s" % required
    assert "RAIL_MODE_KEY" not in immersive and "bindContent" not in immersive
    assert "reader:panel-open" not in immersive
    core = _read("cps/static/js/reading/reader-core.js")
    assert ".reading-translation" in core, "段内译文样式未恢复"
    assert ".reading-para-selected" not in core, "点段选中样式应已删除"


def test_AI面板恢复覆盖式抽屉():
    """2026-10-23 验收回滚：桌面 420px 浮层、移动全屏；不再缩正文。"""
    css = _read("cps/static/css/ai_chat.css")
    assert "width: 420px" in css and "max-width: 100vw" in css, "桌面未恢复 420px 覆盖式抽屉"
    assert "height: 55vh" not in css, "移动端仍是底部 55vh 抽屉（应回滚为全屏）"
    assert "width: 50vw" not in css, "桌面仍是 50vw 停靠（应回滚）"
    assert "width: 100vw; max-width: 100vw; height: 100vh" in css, "移动端未恢复全屏"
    assert "#ai-companion-fab-label" not in css, "R223 后 FAB 文字标签应已删除"
    assert "#ai-companion-fab-wrap" in css, "FAB 定位包裹层缺失"
    assert "#ai-companion-bubbles" in css, "R223 气泡容器缺失"
    assert ".ai-bubble" in css, "R223 hover 快捷气泡样式缺失"
    reader_css = _read("cps/static/css/reader.css")
    assert 'body[data-side-panel="ai"]' not in reader_css, "AI 面板不应再参与正文缩宽"
    assert 'body[data-side-panel="translation"] #main' not in reader_css, \
        "译文栏不应再缩正文（2026-10-23 验收回滚为覆盖式）"
    assert "--side-panel-width" not in reader_css, "侧栏宽度变量应已删除"


def test_AI面板FAB标签状态与覆盖式生命周期():
    js = _read("cps/static/js/ai_chat.js")
    assert 'calibre.ai.fabLabelSeen' in js
    assert "function openDrawer" in js and "function closeDrawer" in js
    assert "data-side-panel" not in js, "AI 面板不应再维护侧栏布局状态"
    assert "reader:panel-open" not in js and "reader:panel-close" not in js


def test_FAB拖拽捕获延迟到拖动开始():
    """R223 回归守卫：wrap 统一接收 pointerdown 后，pointerdown 即 setPointerCapture
    会把 click 重定向到 wrap——点 FAB 开不了抽屉、点气泡无反应（真机实测）。"""
    js = _read("cps/static/js/ai_chat.js")
    down = js.split('button.addEventListener("pointerdown"', 1)[1].split('pointermove"', 1)[0]
    assert "setPointerCapture" not in down, "pointerdown 即捕获会吞掉 FAB/气泡的 click"
    move = js.split('button.addEventListener("pointermove"', 1)[1].split('pointerup"', 1)[0]
    assert "setPointerCapture" in move and "moved = true" in move, "捕获必须延迟到拖动开始"


def test_朗读气泡播放中变为停止():
    """R223 验收反馈：气泡点一次起播后无法停止。

    状态唯一源必须是顶栏 #tts-book（active）/ #tts-book-stop（display），
    播放中点击走停止按钮而不是再次转发 ▶（▶ 在播放中是暂停，不能停）。
    """
    js = _read("cps/static/js/ai_chat.js")
    assert "function readingAloudActive()" in js and "#tts-book-stop" in js
    dispatch = js.split("function dispatchBubbleAction", 1)[1].split("function renderBubbles", 1)[0]
    assert 'id === "tts-book" && readingAloudActive()' in dispatch, "播放中未走停止分支"
    assert "stopBtn.click()" in dispatch, "播放中点击必须触发停止"
    sync = js.split("function syncTtsBubble", 1)[1].split("function dispatchBubbleAction", 1)[0]
    assert '"■"' in sync and '"▶"' in sync, "气泡未在播放/停止两态间切换图标"
    assert 'classList.toggle("is-playing"' in sync, "播放态样式未切换"
    css = _read("cps/static/css/ai_chat.css")
    assert ".ai-bubble.is-playing" in css, "停止态缺少视觉区分"


def test_思考中先于页面上下文():
    js = _read("cps/static/js/ai_chat.js")
    body = js.split("function sendMessage()", 1)[1].split("function streamChat", 1)[0]
    assert "beginThinking()" in body, "发送未同步出思考中"
    assert body.index("beginThinking()") < body.index("getPageContextAsync"), \
        "思考中仍在页面上下文之后才出现"
    assert "1200" in body, "页面上下文未加超时竞速"
    assert "Promise.race" in body
    assert "ai-thinking-elapsed" in js, "思考中缺计时"
    assert "stopThinking(thinking)" in js, "事件到达未停表"


def test_placeholder按阅读格式分口径():
    js = _read("cps/static/js/ai_chat.js")
    assert "detectFormat" in js
    for key in ("Ask about the current page...", "Ask about this text...",
                "Ask about this chapter..."):
        assert key in js, "placeholder 缺口径：%s" % key
    html = _read("cps/templates/ai_chat_panel.html")
    assert "Ask about this chapter..." in html, "EPUB 默认 placeholder 未改"


def test_段尾触屏菜单与图标放大():
    core = _read("cps/static/js/reading/reader-core.js")
    assert ".reading-para-menu-btn" in core
    tools_rule = core.split(".reading-para-tools{", 1)[1].split("}", 1)[0]
    toolbar_rule = core.split(".reading-para-toolbar{", 1)[1].split("}", 1)[0]
    menu_rule = core.split(".reading-para-menu-btn{", 1)[1].split("}", 1)[0]
    assert "display:inline-flex" in tools_rule and "display:inline-flex" in toolbar_rule
    for rule in (tools_rule, toolbar_rule, menu_rule):
        assert "position:absolute" not in rule, "段尾工具不得用浮层压字（用户验收否决）"
    assert "font-size:1.5em" not in core, "满幅字形不应再统一 1.5em"
    assert ".reading-tts-btn{font-size:.95em}" in core
    assert ".reading-translate-btn{font-size:.9em;font-weight:600}" in core
    assert ".reading-annotation-btn{font-size:1.15em}" in core
    assert ".reading-companion-btn{font-size:1.05em}" in core
    tts = _read("cps/static/js/reading/reader-tts.js")
    assert "function openParagraphMenu" in tts
    assert "reading-para-menu-btn" in tts
    assert "target.click()" in tts, "菜单项应复用既有按钮实现"
    # 字形必须走 CSS，否则「⋯」会进 paragraphSpeechText，污染翻译/TTS 缓存键
    assert "menuBtn.textContent" not in tts
    assert '.reading-para-menu-btn::after{content:"⋯"}' in core
    # R215 实现坑：ttsButtonsRender 不能写 btn.textContent，否则抹掉「朗读」标签
    assert "querySelector('.tb-icon')" in tts
    assert "btn.textContent = '▶'" not in tts
    assert ".reading-para-menu button" in _read("cps/static/css/reader.css")
    assert "min-height: 44px" in _read("cps/static/css/reader.css")


def test_幽灵问号避让页码():
    css = _read("cps/static/css/onboarding.css")
    block = css.split("#onb-help {", 1)[1].split("#onb-help:hover", 1)[0]
    assert "right: 16px" in block and "left: auto" in block
    assert "bottom: 88px" in block, "未移到 FAB 上方"
    assert "bottom: 76px" in css, "窄屏避让未同步"


def test_i18n词条已进种子():
    seed = _read("cps/templates/i18n_seed.html")
    for key in ("Translation mode", "Click a paragraph to see its translation",
                "Translation mode disabled", "Paragraph tools",
                "The selected paragraph is no longer on this page"):
        assert '"%s"' % key in seed, "i18n 种子缺词条：%s" % key
