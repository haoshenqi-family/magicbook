"""R216: 阅读主题的账号级同步（/me 选择 → 各设备打开书时生效）。

Why: 主题原本只存 localStorage（`calibre.reader.theme`），换设备就丢。R216 把 5 个
     内置主题存到账号（moon-well user_ui_settings.reader_theme），自定义颜色仍只留本机。
     同步链路有三处会静默失效：head 早载失败被吞、账号值晚到却没人切、用户手选后
     又被迟到的账号值覆盖。它们在页面上都不报错，只表现为「设置没生效」。
"""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_DIR = os.path.join(ROOT, "cps", "templates")
JS_DIR = os.path.join(ROOT, "cps", "static", "js")

BUILTIN = ["lightTheme", "darkTheme", "sepiaTheme", "amberTheme", "blackTheme"]


def _template(name):
    with open(os.path.join(TEMPLATE_DIR, name), encoding="utf-8") as fh:
        return fh.read()


def _js(name):
    with open(os.path.join(JS_DIR, name), encoding="utf-8") as fh:
        return fh.read()


def test_reader_head_loads_ui_prefs_before_reader_scripts():
    src = _template("read.html")
    assert src.count("js/ui-prefs.js") == 1
    assert src.index("ui-prefs.js") < src.index("</head>")
    assert src.index("ui-prefs.js") < src.index("js/libs/jquery.min.js")
    # mbT 依赖 i18n 种子，必须先于阅读器脚本
    assert src.index("i18n_seed.html") < src.index("js/reading/epub.js")


def test_ui_prefs_only_applies_account_value_before_user_pick():
    js = _js("ui-prefs.js")
    assert 'fetch(base + "/ajax/ui-settings"' in js
    assert "window.__mbReaderThemePicked" in js
    assert js.index("if (window.__mbReaderThemePicked) { return; }") < js.index("window.__mbReaderTheme = theme")
    assert "dispatchEvent(new CustomEvent(\"magicbook:reader-theme\"" in js
    assert "localStorage.setItem(KEY, theme)" in js
    # 失败只降级到本机主题，不阻塞阅读
    assert "console.warn" in js and "catch" in js
    # 非内置值（账号未设置/未来新增主题）不得覆盖本机
    assert "BUILTIN.indexOf(theme) < 0" in js


def test_ui_prefs_resolves_app_base_for_subpath_deployments():
    js = _js("ui-prefs.js")
    assert "document.currentScript" in js
    assert "window.__mbBasePath = base" in js
    assert "script.src.indexOf(\"/static/js/ui-prefs.js\")" in js


def test_all_builtin_theme_buttons_sync_on_click():
    src = _template("read.html")
    for theme in BUILTIN:
        assert re.search(r'id="%s"[^>]*onclick="selectTheme\(this\.id, true\)"' % theme, src), \
            "%s 按钮未接账号同步" % theme
    assert src.count("onclick=\"selectTheme(this.id, true)\"") == 5

    assert "function syncThemeToAccount(id)" in src
    assert "window.__mbBasePath" in src
    assert '"/ajax/ui-settings/reader-theme"' in src
    assert '"X-CSRFToken"' in src
    # 用户手选后打标记，迟到的账号值不再覆盖
    assert "window.__mbReaderThemePicked = true" in src
    # 自定义颜色只留本机
    assert 'localStorage.setItem("calibre.reader.theme", "customTheme")' in src


def test_reader_starts_with_account_theme_and_reacts_to_late_sync():
    js = _js("reading/epub.js")
    assert "window.__mbReaderTheme || localStorage.getItem(\"calibre.reader.theme\")" in js
    m = re.search(r'window\.addEventListener\("magicbook:reader-theme".*?\n    \}\);', js, re.S)
    assert m, "缺 magicbook:reader-theme 监听（账号值晚到时不会切主题）"
    assert "selectTheme(synced)" in m.group(0)


def test_me_offers_only_builtin_themes_and_syncs_choice():
    me = _template("me.html")
    for theme in BUILTIN:
        assert 'value="%s"' % theme in me
    assert 'value="customTheme"' not in me, "自定义色只存本机，不能出现在账号偏好里"

    js = _js("me.js")
    assert 'getJson("/ajax/ui-settings")' in js
    assert 'postJson("/ajax/ui-settings/reader-theme", { theme: value })' in js
    assert "if (!touched && BUILTIN_THEMES.indexOf(settings.readerTheme) >= 0)" in js
    assert "writeLocal(saved)" in js
    # 失败必须可见
    assert 'mbT("Theme saved")' in js
    assert 'mbT("Could not load your saved theme; showing this device\'s last choice.")' in js
