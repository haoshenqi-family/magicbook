"""R244 伙伴消失/收信动画守卫：动画资产、可逆入口、降级与钩子四件事不许静默丢失。

Why: 这类纯前端动效没有断言就极易「改了个类名/删了段 keyframes，页面照跑但动画没了」，
     或「reduced-motion 忘了关，晕动用户全程被强放动画」。全部落源码级形制断言（本仓对
     JS/CSS 的既有做法），钉住关键面而非逐帧像素。
"""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CPS = os.path.join(ROOT, "cps")
CSS = open(os.path.join(CPS, "static", "css", "ai_chat.css"), encoding="utf-8").read()
JS = open(os.path.join(CPS, "static", "js", "ai_chat.js"), encoding="utf-8").read()
PANEL = open(os.path.join(CPS, "templates", "ai_chat_panel.html"), encoding="utf-8").read()


def test_keyframes_present():
    for name in ("buddy-vanish", "buddy-poof", "buddy-appear",
                 "buddy-letter-fly", "buddy-peek"):
        assert "@keyframes %s" % name in CSS, "缺 @keyframes " + name


def test_reduced_motion_disables_all_new_animations():
    """prefers-reduced-motion 段必须把五个动画全关掉——漏一个就是晕动用户的回归。

    仓里有多个 reduced-motion 块（R206 头像 + R244 动效），取所有块的并集判定，
    否则 re.search 只会命中第一个小块、误判 R244 未降级。
    """
    blocks = re.findall(r"@media \(prefers-reduced-motion: reduce\) \{", CSS)
    assert blocks, "未找到任何 reduced-motion 媒体块"
    joined = "\n".join(re.findall(r"@media \(prefers-reduced-motion: reduce\) \{(.*?)\n\}", CSS, re.S))
    for sel in ("buddy-vanishing", "buddy-appearing", "buddy-lettering"):
        assert sel in joined, "reduced-motion 未覆盖 ." + sel
    assert "animation: none" in joined


def test_letter_base_is_not_visibility_hidden():
    """信封靠 opacity 显隐：base 若写 visibility:hidden 而动画不置 visible，飞入永远看不见（实测踩过）。"""
    m = re.search(r"#ai-companion-letter \{(.*?)\}", CSS, re.S)
    assert m, "未找到 #ai-companion-letter 基础规则"
    assert "visibility: hidden" not in m.group(1), "信封基础态不得 visibility:hidden，否则动画期不可见"


def test_panel_has_hide_restore_and_letter_hooks():
    for el in ("ai-companion-hide", "ai-companion-restore", "ai-companion-letter"):
        assert el in PANEL, "面板缺元素 " + el


def test_js_exposes_letter_hook_and_reversible_visibility():
    assert "window.AICompanion.showLetter = showLetter" in JS, "未暴露站内信可调用的 showLetter 钩子"
    assert "'mb:buddy-letter'" in JS, "未监听 mb:buddy-letter 自定义事件"
    assert 'BUDDY_HIDDEN_KEY = "calibre.ai.buddy.hidden"' in JS, "隐藏态未落 localStorage（跨页不可逆）"
    # 消失/复原都要有 animationend 之外的兜底，防 animationend 丢失导致球永久隐藏
    assert JS.count("BUDDY_ANIM_MS") >= 3, "动画兜底超时缺失（animationend 不触发时会永久隐藏）"


def test_no_new_gettext_msgid_introduced():
    """本轮刻意复用既有 msgid（AI Companion / Close），不新增词条，免动 i18n 种子/po/mo。"""
    new_strings = re.findall(r"mbT\(\"([^\"]+)\"\)", JS)
    assert "Hide companion" not in new_strings and "Show AI companion" not in new_strings, \
        "引入了新 JS 词条，需同步 i18n 种子/po/mo 或改回复用既有 msgid"
