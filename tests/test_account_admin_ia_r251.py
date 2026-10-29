"""R251: account/admin L2 navigation and task-page boundaries."""

from pathlib import Path

import pytest
from werkzeug.security import generate_password_hash

from cps import ub
from cps.ui_ia import (
    ACCOUNT_L2_GROUPS,
    ADMIN_L2_GROUPS,
    l2_nav_groups,
    nav_domain,
)


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def no_calibre_library(monkeypatch):
    """The test app has no metadata.db; page structure still renders."""
    from cps import calibre_db

    monkeypatch.setattr(calibre_db, "speaking_language", lambda *args, **kwargs: [])


def _items(groups):
    return [item for _, items in groups for item in items]


def _login_plain(app, name="r251-plain"):
    user = ub.session.query(ub.User).filter(ub.User.name == name).first()
    if user is None:
        user = ub.User(
            name=name,
            email=name + "@example.com",
            password=generate_password_hash("r251-plain-pass"),
        )
        ub.session.add(user)
        ub.session.commit()
    assert not user.role_admin()

    client = app.test_client()
    response = client.post(
        "/login",
        data={"username": name, "password": "r251-plain-pass"},
    )
    assert response.status_code == 302
    from cps import config as cw_config

    cw_config.db_configured = True
    return client


def test_account_and_admin_l2_have_one_task_per_page():
    account_items = _items(ACCOUNT_L2_GROUPS)
    admin_items = _items(ADMIN_L2_GROUPS)

    assert len(account_items) == 7
    assert len(admin_items) == 13
    assert len({item["id"] for item in account_items}) == len(account_items)
    assert len({item["id"] for item in admin_items}) == len(admin_items)


def test_l2_navigation_has_exactly_one_active_item_on_owned_routes():
    routes = {
        "account": (
            "/me", "/buddy", "/mail", "/reading/settings", "/credits",
            "/achievements", "/me/export",
        ),
        "admin": (
            "/admin/usertable", "/admin/config", "/translate-all",
            "/word-detail-batch", "/llm-tasks", "/admin/credits",
            "/admin/mail", "/admin/viewconfig", "/admin/dbconfig",
            "/admin/mailsettings", "/admin/scheduledtasks", "/admin/logfile",
            "/admin/debug",
        ),
    }

    for domain, paths in routes.items():
        for path in paths:
            active = [
                item["id"]
                for _, items in l2_nav_groups(domain, path)
                for item in items
                if item["active"]
            ]
            assert len(active) == 1, (domain, path, active)


def test_account_pages_are_split_by_user_task(admin_client):
    me = admin_client.get("/me")
    assert me.status_code == 200
    me_html = me.data.decode("utf-8")
    for moved in ("difficulty", "vt-root", "reading-theme", "me-export-page"):
        assert 'id="{}"'.format(moved) not in me_html
    assert 'id="account-profile"\n           class="mb-l2-link active"' in me_html

    reading = admin_client.get("/reading/settings")
    assert reading.status_code == 200
    reading_html = reading.data.decode("utf-8")
    for task in ("difficulty", "vt-root", "reading-theme"):
        assert 'id="{}"'.format(task) in reading_html
    assert 'id="account-reading"\n           class="mb-l2-link active"' in reading_html

    export = admin_client.get("/me/export")
    assert export.status_code == 200
    export_html = export.data.decode("utf-8")
    assert 'id="me-export-page"' in export_html
    assert 'id="account-export"\n           class="mb-l2-link active"' in export_html


def test_buddy_is_the_account_entry_to_ai_reading(admin_client):
    body = admin_client.get("/buddy").data.decode("utf-8")
    assert 'id="buddy-open-chat"' in body
    assert body.count('class="mb-l2-link active"') == 1
    assert 'id="account-buddy"\n           class="mb-l2-link active"' in body


def test_legacy_admin_landing_redirects_to_users(admin_client):
    response = admin_client.get("/admin/view")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/admin/usertable")

    body = admin_client.get("/me").data.decode("utf-8")
    assert (
        'id="top_admin" data-text="Admin" href="/admin/usertable"'
        in body
    )


def test_user_and_admin_credit_pages_are_physically_separate(
        app, admin_client):
    user_html = admin_client.get("/credits").data.decode("utf-8")
    assert 'data-credit-mode="user"' in user_html
    for governance in (
            "credit-admin-tabs", "credit-admin-adjust",
            "credit-admin-promotion", "credit-admin-cards"):
        assert 'id="{}"'.format(governance) not in user_html

    admin_response = admin_client.get("/admin/credits")
    assert admin_response.status_code == 200
    admin_html = admin_response.data.decode("utf-8")
    assert 'data-credit-mode="admin"' in admin_html
    assert 'id="credit-admin-tabs"' in admin_html

    plain = _login_plain(app)
    assert plain.get("/credits").status_code == 200
    assert plain.get("/admin/credits").status_code == 403


def test_magicbook_admin_tools_are_owned_by_admin_domain():
    for path in ("/translate-all", "/word-detail-batch", "/llm-tasks"):
        assert nav_domain(path, "") == "admin"


def test_word_detail_batch_admin_entry_has_a_book_picker_landing(admin_client):
    response = admin_client.get("/word-detail-batch")
    assert response.status_code == 200
    body = response.data.decode("utf-8")
    assert "从书籍详情进入" in body
    assert 'href="/"' in body
    assert response.status_code != 400
