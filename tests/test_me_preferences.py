"""R216: /me 偏好页、首页难度入口、成就锁态与伙伴文案的静态/渲染契约。

Why: 这轮改动的验收核心是「/me 能改且改得动、别的字段不陪葬」。旧 /me 复用
     user_edit.html 且 change_profile 是全量覆盖——删掉 Kindle/侧栏等勾选后，
     表单缺省字段会把 locale、书架视图等一并重置。这类回归不会报错，只会
     静默丢设置，所以用「局部更新只写两个字段」+「模板不再出现旧控件」锁住。
     难度入口的失败形态同样是静默的：读不到档位若显示假值，用户会以为设置生效。
"""
import json
import os
import re

import pytest
from werkzeug.security import generate_password_hash

from cps import ub

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_DIR = os.path.join(ROOT, "cps", "templates")
JS_DIR = os.path.join(ROOT, "cps", "static", "js")
CSS_DIR = os.path.join(ROOT, "cps", "static", "css")

SETTINGS = {"hardLevel": 3, "hardLevelName": "CET4", "usingDefault": True,
            "options": [{"code": i, "name": "L%d" % i} for i in range(10)]}


@pytest.fixture(autouse=True)
def no_calibre_library(monkeypatch):
    """测试环境没有 metadata.db：语言列表退化为空，页面结构仍可验证。"""
    from cps import calibre_db
    monkeypatch.setattr(calibre_db, "speaking_language", lambda *a, **k: [])


@pytest.fixture
def moonwell_settings(monkeypatch):
    """让 /me 的难度面板走假 moon-well：只关心页面结构，不联外网。"""
    from cps import constants
    import cps.web as w

    monkeypatch.setattr(constants, "MOON_WELL_READING_URL",
                        "https://moon-well.example.com/")

    def fake_proxy(path, payload, timeout, label, binary=False, method="POST",
                   system_identity=False, bearer_token=None):
        assert method == "GET" and path.endswith("/settings")
        return (json.dumps({"success": True, "result": SETTINGS}), 200,
                {"Content-Type": "application/json"})

    monkeypatch.setattr(w._moonwell_client, "proxy", fake_proxy)


@pytest.fixture
def me_user(app):
    user = ub.session.query(ub.User).filter(ub.User.name == "me-prefs-tester").first()
    if user is None:
        user = ub.User(name="me-prefs-tester", email="meprefs@example.com",
                       password=generate_password_hash("me-prefs-pass"))
        ub.session.add(user)
        ub.session.commit()
    user.locale = "en"
    user.default_language = "all"
    user.view_settings = {"sidebar": {"keep": True}, "random_books": True}
    ub.session.commit()

    client = app.test_client()
    rv = client.post("/login", data={"username": "me-prefs-tester",
                                     "password": "me-prefs-pass"})
    assert rv.status_code == 302
    from cps import config as cw_config
    cw_config.db_configured = True
    return client


def _template(name):
    with open(os.path.join(TEMPLATE_DIR, name), encoding="utf-8") as fh:
        return fh.read()


def _js(name):
    with open(os.path.join(JS_DIR, name), encoding="utf-8") as fh:
        return fh.read()


def test_me_renders_preference_controls(me_user, moonwell_settings):
    rv = me_user.get("/me")
    assert rv.status_code == 200
    html = rv.data.decode("utf-8")

    assert 'id="me-language"' in html and 'id="me-locale"' in html
    assert 'id="difficulty"' in html and 'id="me-hard-level"' in html
    assert html.count('name="reader-theme"') == 5
    assert 'id="me-buddy"' in html
    # 真按钮才能被键盘触发；旧页面是 div 靠 JS 转发 click
    assert re.search(r'<button type="submit" id="me-language-save"', html)
    assert re.search(r'<button type="submit" id="me-difficulty-save"', html)


def test_me_no_longer_exposes_kindle_and_sidebar_toggles(me_user, moonwell_settings):
    """R216 明确移除 Kindle 与 20+ 闲置勾选：它们既不能生效，又让页面像管理后台。"""
    html = me_user.get("/me").data.decode("utf-8")
    # 按控件标记查，不按文案查：i18n 种子会把「send straight to your Kindle」
    # 这类无关词条注入每个 layout 页面
    for legacy in ('name="kindle_mail"', 'id="config_create_kobo_token"',
                   'id="kobo_only_shelves_sync"', 'name="sidebar_view"',
                   'name="random_books"'):
        assert legacy not in html, "旧控件 %r 又回到 /me" % legacy
    me_src = _template("me.html")
    assert "user_edit.html" not in me_src
    assert 'id="user_submit"' not in me_src


def test_preferences_update_is_partial(me_user):
    """只写 locale/default_language；view_settings 等字段不得被缺省值覆盖。"""
    rv = me_user.post("/me/preferences",
                      data={"locale": "zh_Hans_CN", "default_language": "all",
                            "sidebar_view": "bad-value"})
    assert rv.status_code == 302

    user = ub.session.query(ub.User).filter(ub.User.name == "me-prefs-tester").first()
    ub.session.expire(user)
    assert user.locale == "zh_Hans_CN"
    assert user.default_language == "all"
    assert user.view_settings == {"sidebar": {"keep": True}, "random_books": True}


def test_preferences_rejects_unknown_locale(me_user):
    rv = me_user.post("/me/preferences",
                      data={"locale": "not-a-locale", "default_language": "all"})
    assert rv.status_code == 302
    user = ub.session.query(ub.User).filter(ub.User.name == "me-prefs-tester").first()
    ub.session.expire(user)
    assert user.locale == "en", "非法 locale 不应写入"


def test_admin_user_edit_save_is_a_real_button():
    """管理员用户编辑页共用 #user_submit：删掉 div+click 转发后必须是可提交按钮。"""
    src = _template("user_edit.html")
    assert re.search(r'<button type="submit" id="user_submit"', src)
    assert '<div class="btn btn-default" id="user_submit"' not in src
    assert '$("#user_submit").click' not in _js("main.js")


def test_difficulty_entry_is_reusable_and_fails_loud():
    partial = _template("difficulty_entry.html")
    assert 'id="difficulty-entry"' in partial
    assert "url_for('web.reading_settings_get')" in partial
    assert "url_for('web.profile') }}#difficulty" in partial
    assert partial.count("difficulty_entry.js") == 1

    js = _js("difficulty_entry.js")
    assert "data-settings-url" in js
    assert "usingDefault" in js and "hardLevelName" in js
    # 读不到就显示「点此设置」；绝不猜一个档位
    assert "data-label-fallback" in js and "catch" in js


def test_home_mounts_difficulty_entry_once():
    index = _template("index.html")
    assert "{% if page == 'newest' %}" in index
    assert index.count("include 'difficulty_entry.html'") == 1


def test_achievement_locked_state_is_not_a_gray_placeholder():
    """locked 曾用整卡 opacity+灰底，看起来像图片加载失败；现在保留 tier 色 + 锁标。"""
    css = open(os.path.join(CSS_DIR, "achievements.css"), encoding="utf-8").read()
    assert "opacity: 0.62" not in css
    assert "#f9f9f9" not in css and "#b8b8b8" not in css
    assert re.search(r"\.ach-card\.locked\s*\{[^}]*border-style:\s*dashed", css)
    assert ".ach-lock" in css

    js = _js("achievements.js")
    assert 'glyphicon-lock ach-lock' in js
    assert 'mbT("Locked")' in js
    assert ".ach-lock" in js


def test_buddy_copy_explains_it_is_the_ai_entry_face():
    copy = ("Your buddy is the face on the AI reading button. It is appearance only "
            "and never changes the AI's role as your English teacher.")
    escaped = copy.replace("'", "\\'")
    for name in ("buddy.html", "me.html"):
        src = _template(name)
        assert escaped in src or copy in src, "%s 缺少伙伴定位文案" % name

    js = _js("buddy.js")
    assert "function lockedLabel(b)" in js
    assert 'b.unlockType === "ACHIEVEMENT"' in js
    assert 'mbT("Unlocks with an achievement")' in js
    # 锁态不再一律写 Coming soon
    assert 'return mbT("Coming soon")' in js
