"""R273 登录页改用邮箱验证的静态契约锁。

R273 把「我已有账号」从密码绑定换成邮箱验证码绑定。这类改动最容易出的错不是语法，
而是**两套入口串了**：主按钮去拿票据（新用户被挡在表单前）、或邮箱入口顺手建了号
（用户以为登进老账号，实际拿着空账号）。本机没有开发者工具，用静态锁钉住这几条。
"""

import os

ROOT = "miniprogram"


def _read(relative):
    with open(os.path.join(ROOT, relative), encoding="utf-8") as handle:
        return handle.read()


def test_login_page_has_no_password_form():
    """登录页不得再出现用户名/密码输入：R273 之后认身份只靠邮箱验证码。"""
    login_wxml = _read("pages/login/login.wxml")
    assert "用户名" not in login_wxml, "登录页不应再要求用户名"
    assert 'password="{{true}}"' not in login_wxml, "登录页不应再有密码输入框"
    login_js = _read("pages/login/login.js")
    assert "onPasswordInput" not in login_js, "密码相关处理应已移除"


def test_email_login_three_phase():
    login_js = _read("pages/login/login.js")
    for phase in ("'idle'", "'email'", "'code'", "verify"):
        assert phase in login_js, "邮箱登录状态机缺少: %s" % phase
    assert "onSendCode" in login_js
    assert "onVerify" in login_js


def test_email_login_never_creates_account():
    """邮箱入口必须先拿票据（linkExisting=true），否则会顺手建出空账号。"""
    login_js = _read("pages/login/login.js")
    assert "auth.login(true)" in login_js
    assert "auth.login(false)" not in login_js.split("startEmailLogin")[-1].split("onEmailInput")[0], \
        "邮箱入口不得走自动建号分支"


def test_email_endpoints_and_error_code():
    login_js = _read("pages/login/login.js")
    auth_js = _read("utils/auth.js")
    assert "/auth/wx/email/send-code" in auth_js
    assert "/auth/wx/email/verify" in auth_js
    # 50514 = 邮箱没有账号：必须回到 idle 并告诉用户去建号，不能原地重试
    assert "50514" in login_js
    assert "50403" in login_js, "票据过期要回 idle，否则用户会拿着废票据一直点"
