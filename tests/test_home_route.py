"""R213-C / MB-18：首页 `/home` 与登录落点的守卫测试。

覆盖：
  1. `/home` 登录门禁（匿名跳登录，不泄露数据）。
  2. 四块组装的空态——没有继续阅读/分级推荐/随机发现时，空块整段不渲染（AC C1）。
  3. 分级推荐的纯规则：书架名解析、同阶合并、**按阶号数字升序**（`阶10` 不排在 `阶2` 前）、
     已读完的书不进推荐、解析不出阶号归「未分级」尾组（AC C4）。
  4. 登录落点开关：默认 `true` 落 `/home`，置 `false` 回退 `/`（AC C6）。
  5. 模板守卫：`index.html` 与 `home.html` 共用同一张卡宏（防止以后又复制一份）。

Why 直接测函数而不整页渲染：测试环境没有 calibre `metadata.db`（`calibre_db.session`
为 None），凡是要取书的页面都渲染不起来——这是本仓既有约束（见
`tests/test_reading_progress.py` 的同类说明）。所以：属性路由测门禁与空态（不需要
取书），取数逻辑用桩替换 `calibre_db` 与 `recent_reading`。
"""

import re

import pytest

from cps import config
from cps import ub
from cps.landing import landing_endpoint
from cps.routes import home as home_mod


@pytest.fixture
def clean_shelves(app):
    """用例前后清掉测试建的「阶N」书架与关联行，避免污染共享库。"""
    def _wipe():
        try:
            rows = ub.session.query(ub.Shelf).filter(ub.Shelf.name.like("阶%")).all()
            for row in rows:
                ub.session.query(ub.BookShelf).filter(ub.BookShelf.shelf == row.id).delete()
                ub.session.delete(row)
            ub.session.commit()
        except Exception:
            ub.session.rollback()
    _wipe()
    yield
    _wipe()


@pytest.fixture
def landing_restore(app):
    """落点开关是共享的 settings 行，用例改完必须还原。"""
    original = config.config_home_landing
    yield
    config.config_home_landing = original
    try:
        ub.session.commit()
    except Exception:
        ub.session.rollback()


class _FakeBook:
    def __init__(self, book_id, title="书"):
        self.id = book_id
        self.title = title


class _FakeFormat:
    def __init__(self, fmt):
        self.format = fmt


class _FakeAuthor:
    def __init__(self, author_id, name="作者"):
        self.id = author_id
        self.name = name


class _FakeRating:
    def __init__(self, rating):
        self.rating = rating


class _RenderableBook:
    """能被 `_book_card.html` 真正渲染的假书。

    Why 造这个：宏里用到 `image.book_cover`（要 id + last_modified）、`main_format`
    / `music`（要 data[].format）、authors/series/ratings 关系——只测「页面 200」
    会漏掉宏本身的渲染错误，而这次重构的风险恰恰在宏里。
    """

    def __init__(self, book_id, title="哈利波特", fmt="EPUB"):
        from datetime import datetime, timezone
        self.id = book_id
        self.title = title
        self.data = [_FakeFormat(fmt)]
        self.authors = [_FakeAuthor(1)]
        self.series = []
        self.series_index = 1.0
        self.ratings = [_FakeRating(8)]
        self.last_modified = datetime(2026, 10, 24, tzinfo=timezone.utc)


class _FakeCalibreDb:
    def __init__(self, ids):
        self._ids = set(ids)

    def get_filtered_book(self, book_id):
        # 不在集合里 = 书已被删或不可见
        return _FakeBook(book_id) if book_id in self._ids else None


def _make_shelf(user_id, name, book_ids):
    shelf = ub.Shelf(name=name, user_id=user_id, is_public=0)
    ub.session.add(shelf)
    ub.session.commit()
    for book_id in book_ids:
        # 必须走 relationship（shelf.books.append）：ub.py 的 before_flush 监听器要读
        # BookShelf.ub_shelf 来推进 Shelf.last_modified，只填外键列会让它是 None。
        shelf.books.append(ub.BookShelf(shelf=shelf.id, book_id=book_id, order=1))
    ub.session.commit()
    return shelf


# ---------------------------------------------------------------- 门禁与空态

def test_home_requires_login(client):
    """AC C5：匿名访问跳登录页，不返回任何书目。"""
    resp = client.get("/home")
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]
    assert "Continue Reading" not in resp.headers["Location"]


def test_home_hides_empty_sections(admin_client, monkeypatch):
    """AC C1：空数据块整段不渲染（不留空白骨架）。

    桩掉三个取数函数：页面必须仍能 200，且只剩「今日计划」一块（它是异步的）。
    """
    monkeypatch.setattr(home_mod, "recent_reading", lambda *a, **kw: [])
    monkeypatch.setattr(home_mod, "level_recommendations", lambda *a, **kw: [])
    monkeypatch.setattr(home_mod, "random_discover_books", lambda *a, **kw: [])

    resp = admin_client.get("/home")
    assert resp.status_code == 200
    page = resp.get_data(as_text=True)
    assert 'id="home-plan"' in page
    assert 'id="home-recent"' not in page
    assert 'id="home-levels"' not in page
    assert 'id="home-discover"' not in page


# ---------------------------------------------------------------- 分级推荐规则

@pytest.mark.parametrize("name,expected", [
    ("阶1", 1),
    ("阶 2", 2),
    ("分级阶3", 3),
    ("阶10", 10),
    ("阶3 桥梁书", 3),          # 带副标题也算
    ("分级阶2（2025）", 2),
    ("第一阶段", None),          # 「第一」不是数字，不许误判成阶 1
    ("章节练习", None),
    ("", None),
    (None, None),
])
def test_level_of_shelf(name, expected):
    assert home_mod.level_of_shelf(name) == expected


def test_group_merges_same_level_and_keeps_unleveled():
    """同阶多书架合并；解析不出阶号的归 None（后续渲染成「未分级」尾组）。"""
    rows = [(1, "阶1", 10), (2, "分级阶1", 11), (3, "杂书架", 20), (1, "阶1", 10)]
    grouped = home_mod.group_book_ids_by_level(rows)
    assert grouped[1] == {10, 11}, "同阶书架没有合并或没有去重"
    assert grouped[None] == {20}


def test_level_picks_numeric_order_and_finished_excluded(admin_client, clean_shelves, monkeypatch):
    """AC C4：阶号按数字升序（阶2 在阶10 之前），已读完的书不进推荐。"""
    user_id = 1  # admin
    _make_shelf(user_id, "阶10", [101])
    _make_shelf(user_id, "阶2", [201, 202])

    # 202 标记为已读完
    ub.session.query(ub.ReadBook).filter(ub.ReadBook.book_id == 202).delete()
    ub.session.add(ub.ReadBook(user_id=user_id, book_id=202,
                               read_status=ub.ReadBook.STATUS_FINISHED))
    ub.session.commit()

    monkeypatch.setattr(home_mod, "calibre_db", _FakeCalibreDb({101, 201, 202}))

    groups = home_mod.level_recommendations(user_id, per_level=6)
    levels = [group["level"] for group in groups if group["level"] is not None]
    assert levels == sorted(levels), "阶号未按数字升序"
    assert levels == [2, 10], "阶10 被排到了阶2 前面（ASCII 序的坑）"

    picked = {book.id for group in groups for book in group["books"]}
    assert 202 not in picked, "已读完的书进了推荐"
    assert 201 in picked and 101 in picked

    ub.session.query(ub.ReadBook).filter(ub.ReadBook.book_id == 202).delete()
    ub.session.commit()


def test_level_picks_skips_missing_books(admin_client, clean_shelves, monkeypatch):
    """书已被删（get_filtered_book 返回 None）时跳过，不报错也不留空位。"""
    _make_shelf(1, "阶1", [301, 302])
    monkeypatch.setattr(home_mod, "calibre_db", _FakeCalibreDb({301}))
    groups = home_mod.level_recommendations(1, per_level=6)
    assert len(groups) == 1
    assert [book.id for book in groups[0]["books"]] == [301]


def test_level_picks_empty_when_no_level_shelf(admin_client, clean_shelves, monkeypatch):
    """全是无阶书架时返回空——首页据此整块不渲染，而不是抛错。"""
    _make_shelf(1, "杂书架", [401])
    monkeypatch.setattr(home_mod, "calibre_db", _FakeCalibreDb({401}))
    groups = home_mod.level_recommendations(1, per_level=6)
    # 无阶书架进「未分级」尾组，不隐藏（AC C4 尾组口径）
    assert len(groups) == 1
    assert groups[0]["level"] is None
    assert groups[0]["label"] == home_mod.UNLEVELED_LABEL


# ---------------------------------------------------------------- 落点开关

def test_landing_defaults_to_home(landing_restore):
    config.config_home_landing = True
    assert landing_endpoint() == "web.home"


def test_landing_falls_back_when_disabled(landing_restore):
    """AC C6：置 false 后回退原 `/` 发现页（可回退）。"""
    config.config_home_landing = False
    assert landing_endpoint() == "web.index"


def test_login_page_next_defaults_to_home(client, landing_restore):
    """登录页的 next 默认值跟随落点开关（本地登录与 OIDC 登录共用同一个 next）。"""
    config.config_home_landing = True
    page = client.get("/login").get_data(as_text=True)
    assert 'name="next" value="/home"' in page


def test_login_page_next_defaults_to_index_when_disabled(client, landing_restore):
    config.config_home_landing = False
    page = client.get("/login").get_data(as_text=True)
    assert re.search(r'name="next" value="/"', page), "关闭开关后 next 未回退到 /"


def test_login_post_lands_on_home(app, landing_restore):
    """AC C6 前半：登录成功直接进 /home。"""
    config.config_home_landing = True
    client = app.test_client()
    resp = client.post("/login", data={"username": "admin", "password": "admin123"})
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/home")


# ---------------------------------------------------------------- 模板守卫

def test_templates_use_shared_card_macro(app):
    """卡片只许有一份实现：index.html 与 home.html 都 import 同一个宏。"""
    for name in ("index.html", "home.html"):
        source = app.jinja_env.loader.get_source(app.jinja_env, name)[0]
        assert "_book_card.html" in source, "%s 没有复用共享卡片宏" % name
        assert "image.book_cover" not in source, "%s 里还留着自己画封面的副本" % name
    macro_source = app.jinja_env.loader.get_source(app.jinja_env, "partials/_book_card.html")[0]
    assert "cover-badge-format" in macro_source, "格式徽标没进共享宏（R213-A 的徽标会再丢）"


def test_home_template_compiles(app):
    assert app.jinja_env.get_template("home.html") is not None
    assert app.jinja_env.get_template("index.html") is not None


def test_home_js_passes_text_through_data_attributes(app):
    """文案走 data-*（模板 `_()`）而不是 mbT()：JS 里不该再有第二个取词入口。"""
    import os
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(root, "cps", "static", "js", "home.js"), encoding="utf-8") as fh:
        code_lines = [line for line in fh
                      if not line.strip().startswith(("//", "*", "/*"))]
    assert not any("mbT(" in line for line in code_lines), \
        "home.js 引入了 mbT，会给 i18n 种子留静默回退面"


def test_home_renders_cards_through_shared_macro(admin_client, monkeypatch):
    """真渲染一张卡：格式徽标、书名、作者链接都要出现在 HTML 里。

    Why 不满足于「200 + 空态」：宏是这次重构的共用件，`image.book_cover` /
    `main_format` 这类过滤器只在渲染时才暴露参数不匹配。
    """
    book = _RenderableBook(501)
    monkeypatch.setattr(home_mod, "recent_reading", lambda *a, **kw: [])
    monkeypatch.setattr(home_mod, "level_recommendations",
                        lambda *a, **kw: [{"level": 1, "label": "阶1", "books": [book]}])
    monkeypatch.setattr(home_mod, "random_discover_books", lambda *a, **kw: [])

    resp = admin_client.get("/home")
    assert resp.status_code == 200
    page = resp.get_data(as_text=True)
    assert 'id="home-levels"' in page
    assert "哈利波特" in page
    assert "/book/501" in page or "book_id=501" in page
    assert "author-name" in page, "作者行没渲染出来（宏里的关系遍历出错会静默成空）"


def test_index_renders_entry_through_shared_macro(app):
    """书库列表也走同一个宏：列表区不带格式徽标、带音乐图标（保持改造前观感）。"""
    from cps.render_template import render_title_template

    class _Entry:
        def __init__(self, book, read_flag):
            self.Books = book
            self._read = read_flag

        def __getitem__(self, index):
            return self.Books if index == 0 else (self._read if index == 2 else None)

    book = _RenderableBook(502, fmt="MP3")   # 纯音频：只有音频徽标，没有格式徽标
    with app.test_request_context("/"):
        with app.app_context():
            from flask import g
            from cps import constants
            # test_request_context 不走请求派发，admin 蓝图的 before_app_request
            # 不会跑，模板依赖的 g.* 得自己补齐
            g.constants = constants
            g.config_authors_max = 0
            html = render_title_template("index.html", random=[_Entry(book, True)],
                                         entries=[], pagination=None, title="Books",
                                         page="newest", order="new")
    assert "哈利波特" in html
    # 列表区不带格式徽标（改造前就是这个观感），但有音乐图标
    assert "cover-badge-format" not in html
    assert "glyphicon-music" in html


# ---------------------------------------------------------------- 迁移

def test_migration_is_idempotent(app):
    """迁移可重复执行：第二次跑不再 ALTER（否则每次启动都报错）。"""
    engine = ub.session.bind
    ub.migrate_home_landing_config(engine)
    ub.migrate_home_landing_config(engine)
    columns = {column["name"] for column in __import__("sqlalchemy").inspect(engine).get_columns("settings")}
    assert "config_home_landing" in columns
