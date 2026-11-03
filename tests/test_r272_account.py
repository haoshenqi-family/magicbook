"""R272 账号体系（自动建号 + 邮箱归并）的静态契约锁。

R240 把「首次必须输密码」改成「自动建号 + 绑邮箱认领」之后，前后端之间多了几条
只靠约定维持的口径，本机没有开发者工具、也无法在 pytest 里跑小程序，只能在源码层钉住：

1. 登录页的主按钮必须走「自动建号」路径（doLogin(false)），
   老用户入口才是 doLogin(true) —— 两者写反了，新用户会被挡在密码表单前；
2. 邮箱接口路径必须与 moon-well `/auth/email/*` 完全一致；
3. 50512（临时账号有数据）必须有二次确认，不允许直接丢弃用户已背的词；
4. 归并后必须用后端返回的新 token（userId 已变），不能沿用旧 token；
5. 临时账号提示条与账号页入口都在，否则用户无从得知自己用的是孤立账号。
"""

import json
import os

ROOT = "miniprogram"


def _read(relative):
    with open(os.path.join(ROOT, relative), encoding="utf-8") as handle:
        return handle.read()


def _json(relative):
    return json.loads(_read(relative))


def test_account_page_registered_and_complete():
    pages = _json("app.json")["pages"]
    assert "pages/account/account" in pages, "账号页必须在 app.json 注册，否则 navigateTo 失败"
    for suffix in (".js", ".json", ".wxml", ".wxss"):
        path = os.path.join(ROOT, "pages/account/account" + suffix)
        assert os.path.isfile(path), "账号页缺少文件: %s" % path


def test_login_defaults_to_auto_signup():
    """主按钮走建号，次按钮走认领：写反会让新用户面对一张他没密码可填的表单。"""
    login_js = _read("pages/login/login.js")
    assert "onTapLogin" in login_js
    assert "this.doLogin(false)" in login_js, "主按钮必须是自动建号路径"
    assert "this.startEmailLogin()" in login_js, "「我已有账号」走邮箱验证路径"
    assert "auth.login(true)" in login_js, "邮箱入口必须只要票据、不建号"


def test_auth_helper_passes_link_existing_flag():
    auth_js = _read("utils/auth.js")
    assert "linkExisting" in auth_js, "登录请求必须能表达「别帮我建号」"
    assert "/auth/wx/login" in auth_js
    assert "/auth/wx/email/send-code" in auth_js, "未登录态发码端点"
    assert "/auth/wx/email/verify" in auth_js, "未登录态验证端点"


def test_email_endpoints_match_backend():
    account_js = _read("pages/account/account.js")
    assert "/auth/email/send-code" in account_js, "发码路径必须与 moon-well 一致"
    assert "/auth/email/verify" in account_js, "校验路径必须与 moon-well 一致"


def test_merge_with_data_requires_explicit_confirmation():
    """50512 是「临时账号里已经有数据」：必须先弹确认，用户点了才带 discardShadowData。"""
    account_js = _read("pages/account/account.js")
    assert "50512" in account_js, "必须专门处理 50512，否则用户看不到自己会丢什么"
    assert "confirmDiscard" in account_js
    assert "discardShadowData" in account_js
    # 只有确认分支才允许把 discardShadowData 置真
    assert "this.submit(this.data.code.trim(), true)" in account_js


def test_merge_replaces_local_token():
    """归并后 userId 变了，本地必须整份替换 token，否则一直用着指向已删账号的旧 token。"""
    account_js = _read("pages/account/account.js")
    assert "auth.persist(result)" in account_js, "归并成功必须落盘后端返回的新 token"


def test_shadow_hint_visible_on_notebook():
    notebook_wxml = _read("pages/notebook/notebook.wxml")
    notebook_js = _read("pages/notebook/notebook.js")
    assert "wechatShadow" in notebook_wxml, "临时账号必须有可见提示，否则用户不知道账号是临时的"
    assert "onTapAccount" in notebook_js
    assert "/pages/account/account" in notebook_js


def test_account_entry_on_stats_page():
    stats_wxml = _read("pages/stats/stats.wxml")
    assert "onTapAccount" in stats_wxml, "数据页页尾要有账号入口"
