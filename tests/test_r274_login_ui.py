"""R274 登录/账号页表单 UI 的静态契约锁。

R274 起因是一张截图：验证码输入框的 placeholder 只露出下半截，还压在边框上。
根因是 input 自带高度 + `box-sizing: border-box` + 上下 padding 三者相减，
内容区接近 0。这类「样式被压塌」的 bug 单测抓不到、本机也没有开发者工具，
只能把约束钉在源码上：输入框高度必须显式给，竖向 padding 必须为 0。
"""

import os
import re

ROOT = "miniprogram"


def _read(relative):
    with open(os.path.join(ROOT, relative), encoding="utf-8") as handle:
        return handle.read()


def _block(source, selector):
    """取出某个简单选择器的声明块（够用即可，不做完整 CSS 解析）。"""
    match = re.search(re.escape(selector) + r"\s*\{([^}]*)\}", source)
    assert match, "找不到样式: %s" % selector
    return match.group(1)


def test_field_has_explicit_height_and_no_vertical_padding():
    app_wxss = _read("app.wxss")
    body = _block(app_wxss, ".field")
    assert "height: 92rpx" in body, "input 必须显式给 height，否则会被自带高度压塌"
    assert "box-sizing: border-box" in body
    # 竖向 padding 只要不是 0，就会从 height 里再切一块给内边距，文字又被挤出去
    assert "padding: 0 24rpx" in body, "竖向 padding 必须为 0，高度只由 height 决定"
    assert "line-height" in body, "没有 line-height 时文字可能贴顶"


def test_field_defined_once_globally():
    """登录页和账号页都曾各写一份 .field，两份都带同一个 bug。只允许 app.wxss 定义。"""
    for page in ("pages/login/login.wxss", "pages/account/account.wxss"):
        assert ".field {" not in _read(page), "%s 不应再自定义 .field（已上提到 app.wxss）" % page


def test_code_input_is_centered_and_easy_to_read():
    for page in ("pages/login/login.wxml", "pages/account/account.wxml"):
        wxml = _read(page)
        assert "field-code" in wxml, "%s 的验证码框应使用 .field-code" % page
        assert 'placeholder-class="field-ph"' in wxml, "%s 的 placeholder 应走 placeholder-class" % page
    code_style = _block(_read("app.wxss"), ".field-code")
    assert "text-align: center" in code_style
    assert "letter-spacing" in code_style, "6 位数字拉开字距才容易核对"


def test_resend_is_visibly_disabled_during_countdown():
    """倒计时期间不能长得跟可点一样：逻辑上已拦截，视觉上也要拦住点击欲望。"""
    for page in ("pages/login/login.wxml", "pages/account/account.wxml"):
        wxml = _read(page)
        assert "resend-wait" in wxml and "resend-ready" in wxml, "%s 缺少重发两态" % page
    app_wxss = _read("app.wxss")
    assert "resend-wait" in app_wxss and "resend-ready" in app_wxss
