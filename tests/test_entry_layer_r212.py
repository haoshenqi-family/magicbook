"""R212 入口层：登录页价值主张/书墙、locale 初始化、顶栏语言入口。"""
import gettext
import os
import re
from datetime import datetime

import pytest
from babel.messages.pofile import read_po
from werkzeug.security import generate_password_hash

from cps import config, oidc, ub


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ZH_MESSAGES = os.path.join(ROOT, "cps", "translations", "zh_Hans_CN",
                           "LC_MESSAGES", "messages")
R212_MSGIDS = {
    "Your private reading room": "你的私人书房",
    "Read deeper. Learn while you read.": "读得更深，在阅读中学习。",
    "A personal library with instant translation, vocabulary help, and an AI reading companion — all in one quiet place.":
        "一座私人图书馆，集即时翻译、词汇帮助与 AI 阅读伙伴于一体，安放于一隅静好。",
    "Books in the library": "馆藏图书",
    "Sign in to your library": "登录你的书房",
    "Remember reading position across devices": "跨设备记住阅读位置",
}


def _template(name):
    with open(os.path.join(ROOT, "cps", "templates", name), encoding="utf-8") as fh:
        return fh.read()


class TestLoginEntry:
    def test_login_has_value_proposition(self, client):
        page = client.get("/login").data.decode("utf-8")
        assert 'id="login-value-proposition"' in page
        assert "Read deeper. Learn while you read." in page
        assert "instant translation" in page
        assert "AI reading companion" in page

    def test_login_book_wall_uses_visible_books(self, client, monkeypatch):
        class Book:
            def __init__(self, book_id):
                self.id = book_id
                self.title = "Book %d" % book_id
                self.name = self.title
                self.last_modified = datetime(2026, 1, 1)
                self.data = []
                self.authors = []
                self.series = []
                self.ratings = []

        books = [Book(book_id) for book_id in range(1, 6)]
        monkeypatch.setattr(config, "config_anonbrowse", 1, raising=False)
        monkeypatch.setattr("cps.routes.home.random_discover_books",
                            lambda limit=None: books[:limit])
        page = client.get("/login").data.decode("utf-8")
        wall = re.search(r'<div class="login-book-wall".*?</div>', page, re.S)
        assert wall, "有书时登录页应渲染书墙"
        assert wall.group(0).count('class="login-book-cover"') == 4
        assert "Book 5" not in wall.group(0)

    def test_login_hides_wall_when_library_empty(self, client, monkeypatch):
        monkeypatch.setattr(config, "config_anonbrowse", 1, raising=False)
        monkeypatch.setattr("cps.routes.home.random_discover_books",
                            lambda limit=None: [])
        page = client.get("/login").data.decode("utf-8")
        assert 'id="login-book-wall"' not in page
        assert 'id="login-value-proposition"' in page

    def test_login_hides_wall_when_query_fails(self, client, monkeypatch):
        def broken(limit=None):
            raise RuntimeError("calibre unavailable")

        monkeypatch.setattr(config, "config_anonbrowse", 1, raising=False)
        monkeypatch.setattr("cps.routes.home.random_discover_books", broken)
        rv = client.get("/login")
        assert rv.status_code == 200
        assert 'id="login-book-wall"' not in rv.data.decode("utf-8")

    def test_login_hides_wall_when_anonymous_browse_is_disabled(self, client, monkeypatch):
        """关闭匿名浏览时不取书，避免封面重定向破图和书名泄露。"""
        called = []

        monkeypatch.setattr(config, "config_anonbrowse", 0, raising=False)
        monkeypatch.setattr("cps.routes.home.random_discover_books",
                            lambda limit=None: called.append(limit) or [])

        page = client.get("/login").data.decode("utf-8")
        assert 'id="login-book-wall"' not in page
        assert called == []

    def test_book_wall_filters_are_delegated_once(self):
        """可见性必须走 common_filters；登录页不得另写一套 SQL 过滤。"""
        source = _template("login.html")
        assert "common_filters" not in source
        assert "random_discover_books" in open(
            os.path.join(ROOT, "cps", "web.py"), encoding="utf-8").read()

    def test_new_copy_has_chinese_translations_in_po_and_mo(self):
        """模板新增文案必须同时进 PO 和编译后的 MO，否则中文静默回退英文。"""
        with open(ZH_MESSAGES + ".po", "rb") as handle:
            po_catalog = read_po(handle)
        with open(ZH_MESSAGES + ".mo", "rb") as handle:
            mo_catalog = gettext.GNUTranslations(handle)

        for msgid, expected in R212_MSGIDS.items():
            entry = po_catalog.get(msgid)
            assert entry is not None and entry.string == expected, \
                "zh PO 缺少或写错 R212 文案：%s" % msgid
            assert mo_catalog.gettext(msgid) == expected, \
                "zh MO 未重新编译：%s" % msgid


class TestLocaleSelection:
    @pytest.mark.parametrize("raw,expected", [
        ("zh-CN", "zh_Hans_CN"),
        ("zh-Hans-CN", "zh_Hans_CN"),
        ("zh-TW", "zh_Hant_TW"),
        ("fr-FR", "fr_FR"),
        ("de", "de"),
        ("not-a-locale", None),
        ("", None),
    ])
    def test_normalize_locale(self, raw, expected):
        assert oidc._normalize_locale(raw) == expected

    def test_claim_wins_over_accept_language(self, app):
        with app.test_request_context("/", headers={"Accept-Language": "fr-FR"}):
            assert oidc.new_user_locale({"locale": "zh-CN"}) == "zh_Hans_CN"

    def test_invalid_claim_falls_back_to_accept_language(self, app):
        with app.test_request_context("/", headers={"Accept-Language": "zh-CN, en;q=0.5"}):
            assert oidc.new_user_locale({"locale": "xx-YY"}) == "zh_Hans_CN"

    def test_accept_language_quality_order(self, app):
        with app.test_request_context("/", headers={"Accept-Language": "en;q=0.4, fr;q=0.9"}):
            assert oidc.new_user_locale({}) == "fr"

    def test_site_default_is_last_fallback(self, app, monkeypatch):
        monkeypatch.setattr(config, "config_default_locale", "zh_Hans_CN", raising=False)
        with app.test_request_context("/"):
            assert oidc.new_user_locale({}) == "zh_Hans_CN"

    def test_only_new_user_creation_initializes_locale(self):
        """既有 OIDC / email 命中路径不得写 locale——那会覆盖用户偏好。

        R256 收拢后 locale= 只允许出现在 create_oidc_user（建号唯一入口）；
        回调内任何直写都意味着合并路径可能覆盖既有用户偏好。
        """
        callback_src = __import__("inspect").getsource(oidc.callback)
        assert "locale=" not in callback_src, "回调只应委托 create_oidc_user 建号"
        helper_src = __import__("inspect").getsource(oidc.create_oidc_user)
        assert helper_src.count("locale=new_user_locale(claims)") == 1


class TestTopNavLanguage:
    @pytest.fixture
    def language_user(self, app):
        from cps.cw_babel import babel

        # 测试 app 由 conftest 手工建，未走 create_app() 的 Babel 初始化；
        # 生产路径会注册，顶栏语言菜单依赖真实翻译目录，故这里补齐。
        if "babel" not in app.extensions:
            babel.init_app(app, locale_selector=lambda: "en")
        user = ub.session.query(ub.User).filter(ub.User.name == "r212-language").first()
        if user is None:
            user = ub.User(name="r212-language", email="r212@example.com",
                           password=generate_password_hash("r212-pass"))
            ub.session.add(user)
            ub.session.commit()
        user.locale = "en"
        user.default_language = "all"
        ub.session.commit()

        client = app.test_client()
        rv = client.post("/login", data={"username": "r212-language",
                                         "password": "r212-pass"})
        assert rv.status_code == 302
        config.db_configured = True
        return client

    def test_top_nav_has_language_entry(self, language_user):
        page = language_user.get("/reading/settings").data.decode("utf-8")
        block = re.search(
            r'<li class="dropdown" id="top_language">.*?(?=<li class="dropdown" id="top_mb_settings">)',
            page, re.S)
        assert block, "登录用户顶栏必须有语言入口"
        nav = block.group(0)
        assert 'action="/me/preferences"' in nav
        assert 'name="locale"' in nav
        assert 'name="default_language"' not in nav
        assert 'name="csrf_token"' in nav
        assert "中文 (简体, 中国)" in nav

    def test_top_nav_save_changes_only_locale(self, language_user):
        from cps import calibre_db

        original = calibre_db.speaking_language
        calibre_db.speaking_language = lambda *a, **k: []
        try:
            rv = language_user.post("/me/preferences", data={"locale": "zh_Hans_CN"})
        finally:
            calibre_db.speaking_language = original
        assert rv.status_code == 302
        user = ub.session.query(ub.User).filter(ub.User.name == "r212-language").first()
        ub.session.expire(user)
        assert user.locale == "zh_Hans_CN"
        assert user.default_language == "all"

    def test_top_nav_save_survives_stale_book_language(self, language_user):
        """书籍语言失效时，顶栏切界面语言不应被连带拒绝或改写。"""
        user = ub.session.query(ub.User).filter(ub.User.name == "r212-language").first()
        user.default_language = "legacy-lang"
        ub.session.commit()

        rv = language_user.post("/me/preferences", data={"locale": "zh_Hans_CN"})
        assert rv.status_code == 302
        ub.session.expire(user)
        assert user.locale == "zh_Hans_CN"
        assert user.default_language == "legacy-lang"

    def test_anonymous_has_no_language_entry(self, client):
        page = client.get("/login").data.decode("utf-8")
        assert 'id="top_language"' not in page
