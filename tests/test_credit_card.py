"""R242: credit-card redemption, gifting purchase and admin proxies."""
import json
import pathlib

import pytest

import cps


@pytest.fixture
def moonwell_configured(monkeypatch):
    from cps import constants
    monkeypatch.setattr(constants, "MOON_WELL_READING_URL",
                        "https://moon-well.example.com/")
    return constants


def _proxy_capture(monkeypatch, result=None, body=None, status=200):
    import cps.web as w
    captured = {}

    def fake_proxy(path, payload, timeout, label, binary=False, method="POST",
                   system_identity=False, bearer_token=None):
        captured.update(path=path, payload=payload, binary=binary, method=method)
        data = body if body is not None else json.dumps(
            {"success": True, "result": result})
        return data, status, {"Content-Type": "application/json"}

    monkeypatch.setattr(w._moonwell_client, "proxy", fake_proxy)
    return captured


def test_card_endpoints_require_login(app, moonwell_configured):
    client = app.test_client()
    assert client.get("/ajax/credit/card/packages").status_code == 302
    assert client.post("/ajax/credit/card/redeem", json={"key": "x"}).status_code == 302
    assert client.post("/ajax/credit/card/purchase-list", json={}).status_code == 302


def test_card_share_page_is_public_and_safe(app):
    rv = app.test_client().get("/credit-card/share")

    assert rv.status_code == 200
    assert rv.headers["Cache-Control"] == "no-store"
    assert rv.headers["Referrer-Policy"] == "no-referrer"
    assert rv.headers["X-Robots-Tag"] == "noindex, nofollow"
    html = rv.data.decode("utf-8")
    for token in ("有人送你一张积分卡", "使用方法", "登录 MagicBook 账号", "复制卡密",
                  "粘贴到「兑换积分卡」输入框", "每张卡密只能兑换一次",
                  "credit-card-share.js"):
        assert token in html


def test_redeem_forwards_key(admin_client, moonwell_configured, monkeypatch):
    captured = _proxy_capture(monkeypatch, {"credits": 1000, "balanceAfter": 2000})
    rv = admin_client.post("/ajax/credit/card/redeem", json={"key": " mb-abcd efgh ijkl mnop "})
    assert rv.status_code == 200
    assert captured["path"] == "/credit/card/redeem"
    assert captured["payload"] == {"key": " mb-abcd efgh ijkl mnop "}


def test_redeem_rejects_empty_key(admin_client, moonwell_configured):
    rv = admin_client.post("/ajax/credit/card/redeem", json={"key": "  "})
    assert rv.status_code == 400
    assert json.loads(rv.data)["success"] is False


def test_purchase_order_and_list_forward(admin_client, moonwell_configured, monkeypatch):
    captured = _proxy_capture(monkeypatch, [])
    assert admin_client.get("/ajax/credit/card/packages").status_code == 200
    assert captured["path"] == "/credit/card/packages"
    assert captured["method"] == "GET"

    admin_client.post("/ajax/credit/card/purchase-order", json={"packageId": "CARD_5000"})
    assert captured["path"] == "/credit/card/purchase/order"
    assert captured["payload"] == {"packageId": "CARD_5000"}

    admin_client.post("/ajax/credit/card/purchase-list", json={})
    assert captured["path"] == "/credit/card/purchase/list"


def test_admin_card_routes_gate_non_admin(client, moonwell_configured, monkeypatch):
    # Anonymous requests are stopped by the login gate before the admin gate.
    assert client.post("/ajax/credit/card/admin-issue", json={}).status_code == 302


def _login_plain(app):
    from cps import ub
    from werkzeug.security import generate_password_hash

    user = ub.session.query(ub.User).filter(ub.User.name == "card-plain").first()
    if user is None:
        user = ub.User(name="card-plain", email="card@example.com",
                       password=generate_password_hash("card-pass"))
        ub.session.add(user)
        ub.session.commit()
    assert not user.role_admin()
    client = app.test_client()
    assert client.post("/login", data={"username": "card-plain",
                                       "password": "card-pass"}).status_code == 302
    from cps import config as cw_config
    cw_config.db_configured = True
    return client


@pytest.mark.parametrize("url", [
    "/ajax/credit/card/admin-issue",
    "/ajax/credit/card/admin-batches",
    "/ajax/credit/card/admin-cards",
    "/ajax/credit/card/admin-void",
    "/ajax/credit/card/admin-export",
])
def test_admin_card_routes_reject_logged_in_non_admin(app, moonwell_configured,
                                                      monkeypatch, url):
    hits = []

    def spy(path, payload, timeout, label, **kwargs):
        hits.append(path)
        raise AssertionError("upstream must not be called for a non-admin")

    from cps import web
    monkeypatch.setattr(web._moonwell_client, "proxy", spy)

    rv = _login_plain(app).post(url, json={"batchId": "3", "cardId": "9"})

    assert rv.status_code == 403
    assert rv.get_json()["success"] is False
    assert not hits


def test_admin_card_routes_forward_for_admin(admin_client, moonwell_configured, monkeypatch):
    captured = _proxy_capture(monkeypatch, {"id": "3"})
    payload = {"credits": 1000, "count": 2, "validityDays": 30,
               "longTerm": False, "reason": "家人", "unexpected": "ignored"}
    assert admin_client.post("/ajax/credit/card/admin-issue", json=payload).status_code == 200
    assert captured["path"] == "/credit/card/admin/batches"
    assert captured["payload"] == {"credits": 1000, "count": 2, "validityDays": 30,
                                   "longTerm": False, "reason": "家人"}

    admin_client.post("/ajax/credit/card/admin-batches", json={})
    assert captured["path"] == "/credit/card/admin/batches/list"

    admin_client.post("/ajax/credit/card/admin-cards", json={"batchId": "3"})
    assert captured["path"] == "/credit/card/admin/cards"

    admin_client.post("/ajax/credit/card/admin-void",
                      json={"cardId": "9", "reason": "发错", "unexpected": "ignored"})
    assert captured["path"] == "/credit/card/admin/void"
    assert captured["payload"] == {"cardId": "9", "reason": "发错"}


def test_export_is_binary_proxy(admin_client, moonwell_configured, monkeypatch):
    captured = _proxy_capture(monkeypatch, body="MB-AAAA-BBBB-CCCC-DDDD\n")
    rv = admin_client.post("/ajax/credit/card/admin-export", json={"batchId": "3"})
    assert rv.status_code == 200
    assert captured["path"] == "/credit/card/admin/export"
    assert captured["binary"] is True
    assert rv.headers["Content-Disposition"] == \
        'attachment; filename="credit-cards-batch-3.txt"'


def test_credit_page_contains_user_card_sections(admin_client, moonwell_configured):
    rv = admin_client.get("/credits")
    html = rv.data.decode("utf-8")
    for token in ("credit-card-redeem", "credit-card-packages",
                  "credit-card-purchased"):
        assert token in html
    for admin_token in ("credit-card-admin-panel", "credit-card-admin-issue-form",
                        "credit-card-admin-long-term"):
        assert admin_token not in html
    assert 'class="modal fade" id="credit-checkout"' in html
    assert 'id="credit-checkout-title"' in html
    assert 'id="credit-checkout-help"' in html
    assert 'data-card-share-url="/credit-card/share"' in html

    admin_html = admin_client.get("/admin/credits").data.decode("utf-8")
    for admin_token in ("credit-card-admin-panel", "credit-card-admin-issue-form",
                        "credit-card-admin-long-term"):
        assert admin_token in admin_html
    assert admin_html.count("credit-card-admin-panel") == 1
    assert admin_html.count("credit-card-admin-cards-rows") == 1
    assert admin_html.index("credit-card-admin-cards-rows") > \
        admin_html.index("credit-card-admin-batches-rows")
    js = pathlib.Path(cps.__file__).parent / "static" / "js" / "credits.js"
    text = js.read_text(encoding="utf-8")
    for endpoint in ("/ajax/credit/card/redeem", "/ajax/credit/card/purchase-order",
                     "/ajax/credit/card/purchase-list", "/ajax/credit/card/admin-issue",
                     "/ajax/credit/card/admin-batches", "/ajax/credit/card/admin-cards",
                     "/ajax/credit/card/admin-void", "/ajax/credit/card/admin-export"):
        assert endpoint in text
    assert "navigator.clipboard" in text or "execCommand('copy')" in text
    assert "if (document.execCommand('copy'))" in text
    assert ".pkg-buy-btn, .credit-card-buy-btn" in text
    assert "复制卡密" in text
    assert "复制并分享" in text
    assert "cardShareUrl(card)" in text
    assert "URLSearchParams" in text
    assert "creditCardPendingRedeem" in text
    assert "$('#credit-checkout').modal('show')" in text
    assert "triggerButton.text('正在创建订单...')" in text
    assert "showError('创建支付订单失败：" in text
    assert "CARD_REDEEM: '积分卡兑换'" in text
    assert "purchaseOrderNo" in text

    share_js = pathlib.Path(cps.__file__).parent / "static" / "js" / "credit-card-share.js"
    share_text = share_js.read_text(encoding="utf-8")
    assert "never redeems automatically" in share_text
    assert "URLSearchParams" in share_text
    assert "sessionStorage.setItem(PENDING_KEY" in share_text
