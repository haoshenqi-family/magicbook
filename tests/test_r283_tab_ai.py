"""R283 修改意见（挂 R280）：tabBar 第二项文案「伴读」→「AI」的静态锁。

范围经用户拍板为「只改 tabBar」：页面标题、登录页品牌副标题以及文档 / 代码注释里的
功能名仍叫「AI 伴读」。所以这个锁同时钉住两件事——**改了该改的**，以及**没越界改**
（防止后续有人顺手把页面标题也改掉，造成产品口径漂移）。
"""

import json
import os

ROOT = "miniprogram"


def _read(relative):
    with open(os.path.join(ROOT, relative), encoding="utf-8") as handle:
        return handle.read()


def _app():
    return json.loads(_read("app.json"))


def test_second_tab_text_is_ai_and_others_untouched():
    tabs = _app()["tabBar"]["list"]
    assert [item["text"] for item in tabs] == ["复习", "AI", "词汇量", "我"]
    assert tabs[1]["pagePath"] == "pages/chat/chat", "只改文案，不换页面路径"
    assert '"text": "伴读"' not in _read("app.json"), "旧 tab 文案必须消失"


def test_only_tabbar_label_changed():
    # 用户选择「只改 tabBar」：其余用户可见功能名保持「AI 伴读」。
    assert '"navigationBarTitleText": "AI 伴读"' in _read("pages/chat/chat.json")
    assert '<view class="chat-title">AI 伴读</view>' in _read("pages/chat/chat.wxml")
    assert "AI 伴读 · 每日复习" in _read("pages/login/login.wxml")
