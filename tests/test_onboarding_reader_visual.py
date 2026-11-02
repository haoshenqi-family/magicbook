"""R111: 阅读器段导览的视觉契约（用户反馈「图书内的导览太丑了」）。

Why: 这一轮的改动几乎全在 CSS 数值与 JS 的几何计算里，纯模板测试看不见。
     四个痛点各自对应一条会被后续「顺手改回来」破坏的不变量：
     1) 蒙层压住了正在读的书页 → reader 段必须比 main 段更轻；
     2) 高亮环用 2px 蓝色实描边，像截图标注工具 → 只允许内阴影 + 外柔影；
     3) 卡片是 Bootstrap 语汇，而 read.html 根本没引 bootstrap，`.btn` 会渲染成
        浏览器原生灰按钮 → 导览的样式必须自给自足；
     4) 深色主题下白卡刺眼 → 卡片配色随 #main 实际底色切换。
     另外锁两个实跑中修出来的几何 bug：环必须 position:fixed（否则画在 0,0），
     以及翻页箭头的透明 padding 热区不能进洞。
"""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSS_PATH = os.path.join(ROOT, "cps", "static", "css", "onboarding.css")
JS_PATH = os.path.join(ROOT, "cps", "static", "js", "onboarding.js")
READ_HTML = os.path.join(ROOT, "cps", "templates", "read.html")


def _css():
    with open(CSS_PATH, encoding="utf-8") as fh:
        return fh.read()


def _css_code():
    """去掉注释的 CSS：注释里会提到被禁止的旧写法（.btn / #4285f4），全文匹配会误判。"""
    return re.sub(r"/\*.*?\*/", "", _css(), flags=re.S)


def _js():
    with open(JS_PATH, encoding="utf-8") as fh:
        return fh.read()


def _rule(css, selector):
    """取某个选择器第一条规则的声明块（去掉注释再匹配，注释里会出现选择器名）。"""
    body = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    m = re.search(re.escape(selector) + r"\s*\{([^}]*)\}", body, re.S)
    assert m, f"CSS 缺少规则：{selector}"
    return m.group(1)


def _offset(css, selector):
    """规则在去注释后的 CSS 里的字节位置——级联同特异度时，后写的才赢。"""
    body = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    m = re.search(re.escape(selector) + r"\s*\{", body)
    assert m, f"CSS 缺少规则：{selector}"
    return m.start()


def _alpha(css, selector):
    m = re.search(r"rgba\(\s*\d+\s*,\s*\d+\s*,\s*\d+\s*,\s*([\d.]+)\s*\)", _rule(css, selector))
    assert m, f"{selector} 没有 rgba 蒙层色"
    return float(m.group(1))


def test_reader_mask_is_lighter_than_main():
    """书页是主角：reader 段的压暗必须严格轻于书库段，且都远低于改版前的 .62。"""
    css = _css()
    main = _alpha(css, "#onb-mask .onb-side")
    reader = _alpha(css, "body.onb-seg-reader #onb-mask .onb-side")
    assert reader < main <= 0.4, f"main={main} reader={reader}"


def test_dark_gauze_rule_wins_the_cascade_tie():
    """Why 位置而不是只测数值：chrome-dark 与 seg-reader 两条 .onb-dim 规则特异度相同
    （body.x #id.y），源码级断言看不出谁生效——写在前面的那条会静默失效，深色主题的
    居中卡又会变回黑压黑（本轮 review 抓到过）。chrome-dark 只可能在阅读器段出现，
    所以它必须排在段规则之后。"""
    css = _css()
    for base, dark in (("#onb-mask .onb-side", "body.onb-chrome-dark #onb-mask .onb-side"),
                       ("body.onb-seg-reader #onb-mask.onb-dim",
                        "body.onb-chrome-dark #onb-mask.onb-dim")):
        assert _offset(css, base) < _offset(css, dark), f"{dark} 被 {base} 覆盖"


def test_dark_theme_switches_to_gauze_not_blacker_overlay():
    """深色主题下黑压黑没有对比度，工具带会和书页糊成一片：改白纱。"""
    css = _css()
    side = _alpha(css, "body.onb-chrome-dark #onb-mask .onb-side")
    dim = _alpha(css, "body.onb-chrome-dark #onb-mask.onb-dim")
    assert side <= 0.15 and dim <= 0.15, f"side={side} dim={dim}"
    assert "rgba(255, 255, 255" in _rule(css, "body.onb-chrome-dark #onb-mask .onb-side")


def test_ring_is_soft_shadow_without_hard_border():
    """去掉 2px #4285f4 实描边；环靠 inset 描边 + 外柔影抬起目标。"""
    ring = _rule(_css(), "#onb-mask .onb-ring")
    assert "border:" not in ring and "border-width" not in ring
    assert "#4285f4" not in _css_code()
    assert "inset" in ring and "var(--onb-ring-edge)" in ring
    assert "box-shadow" in ring and "var(--onb-ring-glow)" in ring



def test_ring_is_fixed_and_click_through():
    """回归锁：漏掉 position:fixed 时环会画在 (0,0) 64×64（本轮实跑踩过）；
    pointer-events 不为 none 时环盖住自己圈住的那个可点控件。"""
    ring = _rule(_css(), "#onb-mask .onb-ring")
    assert "position: fixed" in ring
    assert "pointer-events: none" in ring


def test_reader_bubble_is_smaller():
    """卡片收小：越小越不像在打断阅读。只锁相对关系与上限（改版前 360px），
    具体像素留给后续微调，不做数值钉死。"""
    css = _css()
    main = int(re.search(r"width:\s*(\d+)px", _rule(css, "#onb-bubble")).group(1))
    reader = int(re.search(r"width:\s*(\d+)px", _rule(css, "body.onb-seg-reader #onb-bubble")).group(1))
    assert reader < main < 360, f"main={main} reader={reader}"


def test_mask_container_is_click_through_and_sides_intercept():
    """洞里的控件必须可点（容器 pointer-events:none），拦截由 4 块边负责；
    反过来写错会让高亮目标点不动。"""
    css = _css()
    assert "pointer-events: none" in _rule(css, "#onb-mask")
    assert "pointer-events: auto" in _rule(css, "#onb-mask .onb-side")


def test_card_colors_are_themable_variables():
    """卡片配色走 CSS 变量，深色主题只需覆盖变量；硬编码白字色就没法随主题切。"""
    css = _css()
    card = _rule(css, "#onb-bubble .onb-card")
    assert "var(--onb-card-bg)" in card and "var(--onb-fg)" in card
    dark = _rule(css, "body.onb-chrome-dark")
    for token in ("--onb-card-bg", "--onb-card-border", "--onb-fg", "--onb-fg-muted"):
        assert token in dark, f"深色主题没覆盖 {token}"


def test_reader_has_no_bootstrap_so_buttons_are_self_styled():
    """read.html 不引 bootstrap → 导览按钮必须自带样式，不能靠 .btn/.panel。"""
    with open(READ_HTML, encoding="utf-8") as fh:
        read = fh.read()
    assert "css/libs/bootstrap" not in read, "阅读器已引入 bootstrap，本用例的前提需复核"
    assert "css/onboarding.css" in read

    css = _css_code()
    btn = _rule(css, "#onb-bubble .onb-btn") if "#onb-bubble .onb-btn" in css else _rule(css, ".onb-btn")
    assert "background" in btn and "border-radius" in btn
    assert ".btn" not in css and ".panel" not in css

    js = _js()
    assert 'class="onb-btn' in js
    assert not re.search(r'class="btn\s|btn btn-', js), "导览里又出现了 bootstrap 按钮类"


def test_reader_hot_zone_is_the_whole_toolbar_band():
    """阅读器段亮区＝目标所在工具带（标题栏/侧栏/底部页码条），书页只吃薄纱。"""
    js = _js()
    m = re.search(r"function protectFor\(.*?\n  \}", js, re.S)
    assert m, "protectFor 不存在"
    body = m.group(0)
    closest = re.search(r'closest\("([^"]+)"\)', body)
    assert closest, "protectFor 没有按工具带取亮区"
    for anchor in ("#titlebar", "#sidebar", ".read-footer"):
        assert anchor in closest.group(1), f"closest 选择器缺 {anchor}"
    # 非工具带目标（翻页箭头、AI 悬浮球）退化为按元素外扩，不能整屏留亮
    assert 'if (segment !== "reader")' in body


def test_visual_rect_excludes_transparent_padding_hit_area():
    """翻页箭头 .arrow 有 160/80px 透明内边距（main.css:115-141），照 border-box 挖洞
    会圈出一大块空白；只在元素自身无背景时按 padding 内缩。"""
    js = _js()
    m = re.search(r"function visualRect\(.*?\n  \}", js, re.S)
    assert m, "visualRect 不存在"
    body = m.group(0)
    assert "getComputedStyle" in body and "paddingLeft" in body
    assert "backgroundImage" in body, "有背景的按钮不能内缩，否则控件高亮成几个字"
    assert "paintMask(el, visualRect(el))" in js


def test_segment_scope_set_on_start_and_cleared_on_teardown():
    """作用域类残留会让书库页沿用阅读器的轻蒙层（视觉不一致），teardown 必须清干净。"""
    js = _js()
    assert 'addClass(segment === "reader" ? "onb-seg-reader" : "onb-seg-main")' in js
    m = re.search(r"function teardown\(\) \{.*?\n  \}", js, re.S)
    assert m, "teardown 不存在"
    for cls in ("onboarding-active", "onb-seg-main", "onb-seg-reader", "onb-chrome-dark"):
        assert cls in m.group(0), f"teardown 没清理 {cls}"


def test_dark_theme_detection_probes_main_not_a_theme_table():
    """阅读器有 5 套主题 + 可任取颜色的 customTheme：查表必漏，按 #main 实际底色算亮度。"""
    js = _js()
    m = re.search(r"function applyChromePalette\(.*?\n  \}", js, re.S)
    assert m, "applyChromePalette 不存在"
    body = m.group(0)
    assert "isReaderPage()" in body, "书库页不该切暗卡（气泡浮在蒙层上，不压正文）"
    assert "0.299" in body and "onb-chrome-dark" in body
    bg = re.search(r"function pageBackground\(.*?\n  \}", js, re.S)
    assert bg and 'getElementById("main")' in bg.group(0)


def test_help_button_palette_is_recomputed_before_early_return():
    """常驻「?」用的是 var(--onb-card-bg)：teardown 摘掉 onb-chrome-dark 后若不重算，
    导览结束那一刻它会从暗色卡跳回白按钮浮在深色主题上（showReaderHelp 里有
    `if ($("#onb-help").length) return` 的提前返回，重算必须排在它之前）。"""
    js = _js()
    m = re.search(r"function showReaderHelp\(\) \{.*?\n  \}", js, re.S)
    assert m, "showReaderHelp 不存在"
    body = m.group(0)
    assert body.index("applyChromePalette()") < body.index(") return"), "重算排到了提前返回之后"


def test_bubble_stays_above_mask():
    """气泡 z 必须高于蒙层，否则卡片被自己的压暗层盖住（分层是显式声明的）。"""
    css = _css()
    mask = int(re.search(r"z-index:\s*(\d+)", _rule(css, "#onb-mask")).group(1))
    bubble = int(re.search(r"z-index:\s*(\d+)", _rule(css, "#onb-bubble")).group(1))
    assert bubble > mask
