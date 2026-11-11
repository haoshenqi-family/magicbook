"""R292 小程序移除 AI 伴读能力（微信上架合规）的静态锁。

背景：带 AI 对话能力的小程序过不了微信上架审核，用户要求整体移除。审核看的是
**代码包**而不只是界面入口，所以这里钉的是「包里没有」，不是「入口藏起来了」：

1. 对话页目录、页面注册与 tabBar 项全部消失，底栏收为「复习 / 词汇量 / 我」；
2. 请求层不再有 SSE 对话通道（chatStream / 分块解码 / 分帧）与对话专用超时；
3. 代码包内任何用户可见文案与工程描述都不再出现 AI 字样；
4. R280 一并下掉的生词本页不因本次改动复活（原 test_r280_ai_chat.py 的两条锁迁到这里，
   该文件其余断言都以对话页存在为前提，随对话页一起删除）。
"""

import json
import os
import re

ROOT = "miniprogram"

# 代码包 = 微信开发者工具会上传的文件；README.md 是给开发者看的工程说明，不进审核视野，
# 但也不应再把 AI 写成现役能力，单独一条锁管它。
PACKAGE_SUFFIXES = (".js", ".json", ".wxml", ".wxss")


def _read(relative):
    with open(os.path.join(ROOT, relative), encoding="utf-8") as handle:
        return handle.read()


def _package_files():
    for folder, _dirs, names in os.walk(ROOT):
        for name in names:
            if name.endswith(PACKAGE_SUFFIXES):
                yield os.path.relpath(os.path.join(folder, name), ROOT)


def test_chat_page_is_gone_and_tabbar_has_three_tabs():
    assert not os.path.exists(os.path.join(ROOT, "pages", "chat")), "对话页目录必须删除，不是只摘入口"
    app = json.loads(_read("app.json"))
    assert all("chat" not in page for page in app["pages"])
    tabs = app["tabBar"]["list"]
    assert [item["text"] for item in tabs] == ["复习", "词汇量", "我"]
    assert [item["pagePath"] for item in tabs] == [
        "pages/review/review", "pages/test/test", "pages/stats/stats"]


def test_request_layer_has_no_chat_channel():
    api = _read("utils/api.js")
    for removed in ("chatStream", "/ai/agent/chat", "enableChunked", "onChunkReceived",
                    "text/event-stream", "decodeUtf8", "parseSseBlock", "chatTimeout"):
        assert removed not in api, "请求层残留对话通道: " + removed
    assert "chatTimeout" not in _read("config.js")
    # 普通请求层不能被连带删坏
    for kept in ("request,", "refreshToken,", "function describeNetworkError", "toastError"):
        assert kept in api, "普通请求层缺件: " + kept


def test_package_has_no_ai_wording():
    # \bAI\b 之外再钉功能名与对话端点，防止换个说法留下来
    pattern = re.compile(r"\bAI\b|伴读|/ai/|agent-chat|智能对话|大模型")
    for relative in _package_files():
        hit = pattern.search(_read(relative))
        assert hit is None, "%s 仍含 AI 相关字样: %s" % (relative, hit.group(0))


def test_login_and_project_description_list_three_features():
    assert "每日复习 · 词汇量测试 · 学习数据" in _read("pages/login/login.wxml")
    description = json.loads(_read("project.config.json"))["description"]
    assert description == "MagicBook 工具型小程序：每日复习 / 词汇量测试 / 学习数据"


def test_readme_does_not_present_ai_as_a_live_feature():
    readme = _read("README.md")
    assert "R292" in readme, "README 必须交代 AI 伴读已移除及原因"
    for stale in ("pages/chat", "chatStream", "chatTimeout", "/ai/agent/chat"):
        assert stale not in readme, "README 仍把已删除的件写成现役: " + stale


def test_notebook_page_stays_removed():
    app = json.loads(_read("app.json"))
    assert all("notebook" not in page for page in app["pages"])
    assert not os.path.exists(os.path.join(ROOT, "pages", "notebook")), "生词本页目录必须删除"


def test_notebook_is_not_advertised_as_a_miniprogram_feature():
    assert "生词本" not in _read("app.json")
    assert "生词本" not in _read("project.config.json")
    assert "生词本" not in _read("pages/login/login.wxml")
    # 词汇量测试仍会写回网页端生词本，这里只允许出现「网页端生词本」这种去向说明
    assert "生词本" not in _read("pages/test/test.wxml").replace("网页端生词本", "")
