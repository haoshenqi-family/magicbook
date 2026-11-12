"""R275 首页改复习、数据页改「我」、新增主站入口的静态契约锁。

这三件事都容易「改一半」：tabBar 换了但登录后仍 switchTab 到生词本（用户登录完
落在第二屏）；tab 改名了但账号入口还埋在页尾（新用户找不到换绑）；主站链接写死在
两个地方（改域名只改了一处）。本机没有开发者工具，只能在源码层钉住。
"""

import json
import os

ROOT = "miniprogram"


def _read(relative):
    with open(os.path.join(ROOT, relative), encoding="utf-8") as handle:
        return handle.read()


def _app():
    return json.loads(_read("app.json"))


def test_review_is_the_first_tab():
    tabs = [item["pagePath"] for item in _app()["tabBar"]["list"]]
    assert tabs[0] == "pages/review/review", "首页必须是复习，不是生词本"
    # R280 起第二 tab 由「生词本」换成 AI 对话页；R292 为上架合规把对话页整体移除，
    # 底栏收为三项，第二项顺位成词汇量测试
    assert tabs[1] == "pages/test/test"


def test_tab_renamed_to_me():
    texts = [item["text"] for item in _app()["tabBar"]["list"]]
    assert "我" in texts, "「数据」tab 应改名为「我」"
    assert "数据" not in texts


def test_login_lands_on_review():
    login_js = _read("pages/login/login.js")
    assert "/pages/review/review" in login_js, "登录成功后应落到复习页（tabBar 第一项）"
    assert "/pages/notebook/notebook" not in login_js, "登录后不应再跳到生词本"


def test_me_page_has_account_and_site_entry():
    stats_wxml = _read("pages/stats/stats.wxml")
    assert "onTapAccount" in stats_wxml, "「我」页必须有账号入口"
    assert "onOpenSite" in stats_wxml, "「我」页必须有主站入口"
    assert "退出登录" in stats_wxml
    stats_js = _read("pages/stats/stats.js")
    assert "onOpenSite" in stats_js
    assert "setClipboardData" in stats_js, "小程序无法调起浏览器，只能复制链接"


def test_site_url_comes_from_config_only():
    """主站域名只允许出现在 config.js：写死在页面里，改环境时必漏一处。"""
    assert "siteUrl" in _read("config.js")
    assert "magicbook.haoshenqi.top" in _read("config.js")
    for page in ("pages/stats/stats.js", "pages/stats/stats.wxml", "pages/login/login.wxml"):
        assert "magicbook.haoshenqi.top" not in _read(page), "%s 不应硬编码主站域名" % page
