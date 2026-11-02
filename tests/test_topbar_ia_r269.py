"""R269：顶栏信息架构收敛。

用户口径（原话）：「搜索只在书库有就可以了其他四个主入口不要。同样的上传书籍
也是。最右边的用户跟主用户重复了，是相同的功能，还有注销按钮，和语言按钮，
只放到账号中。任务列表只放到管理权限中。右上角只留帮助按钮。」

契约（按域判定，不按页面白名单）：
- 顶栏搜索框与上传书籍只在书库域（`current_domain == 'library'`）渲染；
- 顶栏不再有 任务列表 / 语言 / 用户名 / 注销 四个入口，右上只留帮助；
- 语言与注销归「账号」域（/me 的 me-language、me-logout）；
- 任务列表归「管理权限」域（ui_ia.ADMIN_L2_GROUPS 的 admin-tasks，/tasks 属管理域）。
"""

from pathlib import Path

import pytest
from werkzeug.security import generate_password_hash

from cps import ub

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "cps" / "templates"

# 书库域取一个不查 metadata.db 的稳定页面（R251 同姿势）
LIBRARY_PATH = "/shelf/create"


@pytest.fixture(autouse=True)
def no_calibre_library(monkeypatch):
    from cps import calibre_db, config

    monkeypatch.setattr(calibre_db, "speaking_language", lambda *args, **kwargs: [])
    # 测试库默认 config_uploading=0（上传入口不渲染）；本文件要验「只在书库域出现」，
    # 必须把上传打开，否则两边都空、断言不成立。
    monkeypatch.setattr(config, "config_uploading", 1, raising=False)


def _plain_client(app, name="r269-plain"):
    user = ub.session.query(ub.User).filter(ub.User.name == name).first()
    if user is None:
        user = ub.User(name=name, email=name + "@example.com",
                       password=generate_password_hash("r269-plain-pass"))
        ub.session.add(user)
        ub.session.commit()
    assert not user.role_admin()

    client = app.test_client()
    rv = client.post("/login", data={"username": name, "password": "r269-plain-pass"})
    assert rv.status_code == 302
    from cps import config as cw_config

    cw_config.db_configured = True
    return client


def _html(client, path):
    rv = client.get(path)
    assert rv.status_code == 200, (path, rv.status_code)
    return rv.data.decode("utf-8")


class TestSearchAndUploadAreLibraryOnly:
    def test_library_domain_keeps_search_box(self, admin_client):
        html = _html(admin_client, LIBRARY_PATH)
        assert 'id="query"' in html, "书库页必须保留顶栏搜索"
        assert 'id="advanced_search"' in html, "高级搜索是搜索输入组的一部分"

    def test_library_domain_keeps_upload(self, admin_client):
        assert 'id="form-upload"' in _html(admin_client, LIBRARY_PATH)

    @pytest.mark.parametrize("path", ["/me", "/admin/credits", "/learning"])
    def test_other_primary_domains_drop_search_and_upload(self, admin_client, path):
        html = _html(admin_client, path)
        assert 'id="query"' not in html, "{0} 不该出现顶栏搜索".format(path)
        assert 'id="form-upload"' not in html, "{0} 不该出现上传书籍".format(path)
        assert 'id="btn-upload"' not in html


class TestTopRightHoldsOnlyHelp:
    @pytest.mark.parametrize("path", ["/me", LIBRARY_PATH])
    def test_logged_in_topbar_has_no_duplicate_entries(self, admin_client, path):
        html = _html(admin_client, path)
        assert 'id="top_mb_settings"' in html, "右上必须保留帮助"
        for gone in ('id="top_tasks"', 'id="top_language"', 'id="logout"'):
            assert gone not in html, "{0} 应已从顶栏撤下".format(gone)
        # 用户名入口（默认皮肤的 top_user）只对匿名访客保留登录用途
        assert 'id="top_user"' not in html

    def test_anonymous_keeps_login_entry(self, client):
        """匿名访客的登录入口留在源码分支里（登录页本身不渲染顶栏导航）。"""
        src = (TEMPLATES / "layout.html").read_text(encoding="utf-8")
        assert '{% if g.current_theme == 0 and current_user.is_anonymous %}' in src
        assert 'id="top_user"' in src
        page = client.get("/login").data.decode("utf-8")
        assert 'id="top_mb_settings"' not in page, "匿名不渲染帮助下拉"
        for gone in ('id="top_language"', 'id="top_tasks"'):
            assert gone not in page

    def test_layout_source_has_no_flat_task_or_language_item(self):
        src = (TEMPLATES / "layout.html").read_text(encoding="utf-8")
        for gone in ("top_tasks", "top_language"):
            assert gone not in src, "{0} 已迁出顶栏".format(gone)


class TestAccountOwnsLanguageAndLogout:
    def test_account_page_has_logout_button(self, admin_client):
        html = _html(admin_client, "/me")
        assert 'id="me-logout"' in html
        assert 'href="/logout"' in html

    def test_account_page_owns_language_panel(self, admin_client):
        html = _html(admin_client, "/me")
        assert 'id="me-language"' in html
        assert 'action="/me/preferences"' in html

    def test_language_and_logout_have_no_second_entry_elsewhere(self):
        layout = (TEMPLATES / "layout.html").read_text(encoding="utf-8")
        assert "url_for('web.logout'" not in layout, "注销只允许出现在账号域"
        assert 'id="top_language"' not in layout


class TestTaskListBelongsToAdminDomain:
    def test_admin_sees_task_entry_in_admin_l2(self, admin_client):
        html = _html(admin_client, "/tasks")
        assert 'id="admin-tasks"' in html, "管理员在任务页应看到管理域 L2 入口"
        assert 'class="mb-l2-link active"' in html
        assert ('id="top_admin" data-text="Admin" href="/admin/usertable" '
                'aria-current="page"') in html, "任务页应点亮「管理权限」"

    def test_plain_user_gets_no_admin_links_on_tasks(self, app):
        """普通用户仍可看自己的任务（/tasks 未改权限），但看不到管理域链接。"""
        html = _html(_plain_client(app), "/tasks")
        for admin_link in ("admin-users", "admin-tasks", "admin-ui", "/admin/usertable"):
            assert admin_link not in html, "非管理员不该拿到 {0}".format(admin_link)
