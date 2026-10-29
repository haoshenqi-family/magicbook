"""R245 guards: task-based credit page layout and promotion time submission."""
import pathlib
import re

import cps


def _login_plain(app):
    from cps import ub
    from werkzeug.security import generate_password_hash

    user = ub.session.query(ub.User).filter(ub.User.name == "credit-page-plain").first()
    if user is None:
        user = ub.User(name="credit-page-plain", email="credit-page@example.com",
                       password=generate_password_hash("credit-page-pass"))
        ub.session.add(user)
        ub.session.commit()
    assert not user.role_admin()
    client = app.test_client()
    assert client.post("/login", data={
        "username": "credit-page-plain",
        "password": "credit-page-pass",
    }).status_code == 302
    from cps import config as cw_config
    cw_config.db_configured = True
    return client


def test_user_credit_page_contains_only_user_tasks(admin_client):
    html = admin_client.get("/credits").data.decode("utf-8")

    for pane in ("credit-pane-recharge", "credit-pane-cards", "credit-pane-details"):
        assert 'id="%s"' % pane in html

    assert 'data-credit-mode="user"' in html
    for admin_pane in ("credit-pane-admin", "credit-admin-adjust",
                       "credit-admin-promotion", "credit-admin-cards"):
        assert 'id="%s"' % admin_pane not in html

    assert html.count('id="credit-packages"') == 1
    assert html.count('id="credit-card-redeem"') == 1
    assert html.count('id="credit-consume-table"') == 1


def test_admin_credit_page_is_its_own_l2(admin_client):
    html = admin_client.get("/admin/credits").data.decode("utf-8")

    assert 'data-credit-mode="admin"' in html
    for admin_pane in ("credit-admin-adjust", "credit-admin-promotion",
                       "credit-admin-cards"):
        assert 'id="%s"' % admin_pane in html
    assert html.count('id="credit-card-admin-panel"') == 1
    assert 'id="credit-pane-recharge"' not in html
    assert 'id="account-credits"' not in html
    assert 'id="admin-credits"\n           class="mb-l2-link active"' in html


def test_non_admin_credit_page_hides_management(app):
    html = _login_plain(app).get("/credits").data.decode("utf-8")

    assert 'id="credit-pane-recharge"' in html
    assert 'id="credit-pane-cards"' in html
    assert 'id="credit-pane-details"' in html
    assert 'id="credit-pane-admin"' not in html
    assert 'id="credit-admin-panel"' not in html


def test_promotion_submit_normalizes_datetime_local_and_reports_inline():
    js = (pathlib.Path(cps.__file__).parent / "static" / "js" / "credits.js").read_text(
        encoding="utf-8")

    assert "function promotionWireTime(value)" in js
    assert re.search(
        r"var start = promotionWireTime\(\$\('#credit-promo-start'\)\.val\(\)\);", js)
    assert re.search(
        r"var end = promotionWireTime\(\$\('#credit-promo-end'\)\.val\(\)\);", js)
    assert "startTime: start, endTime: end, multiplier: multiplier" in js
    assert "feedback.removeClass('is-error').addClass('is-success').text('活动已发布。')" in js
    assert "feedback.removeClass('is-success').addClass('is-error')" in js

    promotion_section = js[js.index("function submitPromotion()"):js.index("function resetConsumePage()")]
    assert "$.ajax(" not in promotion_section
    assert "window.alert(" not in promotion_section


def test_consume_rows_use_high_contrast_classes_instead_of_inline_colors():
    root = pathlib.Path(cps.__file__).parent
    html = (root / "static" / "css" / "credits.css").read_text(encoding="utf-8")
    js = (root / "static" / "js" / "credits.js").read_text(encoding="utf-8")

    assert ".credit-type-badge.consume { background: #f3cf7a; color: #5c3500;" in html
    assert ".credit-type-badge.income { background: #d4ead9; color: #185c31;" in html
    assert ".credit-amount.consume { color: #8a3b12; }" in html
    assert ".credit-amount.income { color: #216a3a; }" in html
    assert "text-right credit-amount ' + (isIncome ? 'income' : 'consume')" in js
    assert ".css('color', isIncome" not in js
