"""R243 mail proxy contract: auth, parameter normalization and three-tuples."""

import json

import pytest


@pytest.fixture
def proxy_calls(monkeypatch):
    import cps.routes.mail as mail_routes

    calls = []

    def fake_proxy(path, payload, timeout, label, binary=False, method="POST",
                   system_identity=False, bearer_token=None):
        calls.append({
            "path": path,
            "payload": payload,
            "timeout": timeout,
            "label": label,
            "method": method,
        })
        return (json.dumps({"success": True, "result": {"ok": True}}), 200,
                {"Content-Type": "application/json", "X-Upstream": "moon-well"})

    monkeypatch.setattr(mail_routes, "_moonwell_proxy", fake_proxy)
    return calls


def test_mail_routes_have_distinct_page_and_proxy_endpoints(app):
    endpoints = {rule.endpoint for rule in app.url_map.iter_rules()}
    assert "web.mail_inbox_page" in endpoints
    assert "web.mail_page_proxy" in endpoints
    assert "web.mail_page" not in endpoints


@pytest.mark.parametrize(
    "method,path,kwargs",
    [
        ("get", "/ajax/mail/unread-count", {}),
        ("get", "/ajax/mail/page", {}),
        ("post", "/ajax/mail/read", {"json": {"id": 1}}),
        ("post", "/ajax/mail/read-all", {"json": {}}),
    ],
)
def test_all_mail_proxies_require_login(client, monkeypatch, method, path, kwargs):
    import cps.routes.mail as mail_routes

    touched = []
    monkeypatch.setattr(mail_routes, "_moonwell_proxy",
                        lambda *args, **kw: touched.append((args, kw)))
    response = getattr(client, method)(path, **kwargs)
    assert response.status_code == 302
    assert touched == []


def test_unread_count_uses_post_upstream_and_keeps_three_tuple(admin_client, proxy_calls):
    response = admin_client.get("/ajax/mail/unread-count")
    assert response.status_code == 200
    assert response.headers["X-Upstream"] == "moon-well"
    assert proxy_calls == [{
        "path": "/mail/unread-count",
        "payload": None,
        "timeout": 10,
        "label": "mail unread count",
        "method": "POST",
    }]


@pytest.mark.parametrize(
    "query,expected",
    [
        ("", {"pageNo": 1, "pageSize": 20}),
        ("?pageNo=2&pageSize=7", {"pageNo": 2, "pageSize": 7}),
        ("?pageNo=0&pageSize=-4", {"pageNo": 1, "pageSize": 20}),
        ("?pageNo=nope&pageSize=bad", {"pageNo": 1, "pageSize": 20}),
        ("?pageNo=999999&pageSize=999", {"pageNo": 100000, "pageSize": 50}),
        ("?pageNo=1.5&pageSize=2.5", {"pageNo": 1, "pageSize": 20}),
    ],
)
def test_page_proxy_normalizes_query(admin_client, proxy_calls, query, expected):
    response = admin_client.get("/ajax/mail/page" + query)
    assert response.status_code == 200
    call = proxy_calls[-1]
    assert call["path"] == "/mail/page"
    assert call["payload"] == expected
    assert call["method"] == "POST"


def test_read_forwards_only_valid_positive_integer(admin_client, proxy_calls):
    response = admin_client.post("/ajax/mail/read", json={"id": 42, "userId": 999})
    assert response.status_code == 200
    assert proxy_calls[-1]["path"] == "/mail/read"
    assert proxy_calls[-1]["payload"] == {"id": 42}


@pytest.mark.parametrize("payload", [{}, {"id": 0}, {"id": -1}, {"id": "4"},
                                     {"id": True}, {"id": 2.5}, [], [1],
                                     "4", True, None])
def test_read_rejects_invalid_id_before_upstream(admin_client, proxy_calls, payload):
    response = admin_client.post("/ajax/mail/read", json=payload)
    assert response.status_code == 400
    assert response.get_json() == {"success": False, "message": "id is required"}
    assert proxy_calls == []


def test_read_rejects_malformed_json_before_upstream(admin_client, proxy_calls):
    response = admin_client.post(
        "/ajax/mail/read", data="{", content_type="application/json")
    assert response.status_code == 400
    assert proxy_calls == []


def test_read_all_forwards_empty_payload(admin_client, proxy_calls):
    response = admin_client.post("/ajax/mail/read-all", json={"ignored": True})
    assert response.status_code == 200
    assert proxy_calls[-1]["path"] == "/mail/read-all"
    assert proxy_calls[-1]["payload"] == {}


def test_upstream_failure_body_status_and_headers_pass_through(admin_client, monkeypatch):
    import cps.routes.mail as mail_routes

    body = json.dumps({"success": False, "message": "mail upstream down"})
    headers = {"Content-Type": "application/json", "X-Trace-Id": "trace-503"}
    monkeypatch.setattr(mail_routes, "_moonwell_proxy",
                        lambda *args, **kwargs: (body, 503, headers))

    response = admin_client.get("/ajax/mail/page?pageNo=1&pageSize=20")
    assert response.status_code == 503
    assert response.get_data(as_text=True) == body
    assert response.headers["X-Trace-Id"] == "trace-503"


def test_credit_admin_adjust_still_forwards_notification_fields(admin_client, monkeypatch):
    import cps.web as web

    captured = {}

    def fake_client_proxy(path, payload, timeout, label, binary=False, method="POST",
                          system_identity=False, bearer_token=None):
        captured.update(path=path, payload=payload)
        return (json.dumps({"success": True, "result": {"balance": 500}}), 200,
                {"Content-Type": "application/json"})

    monkeypatch.setattr(web._moonwell_client, "proxy", fake_client_proxy)
    payload = {
        "userId": 7,
        "amount": 500,
        "reason": "campaign grant",
        "notify": True,
        "notificationMessage": "Thanks for joining.",
    }
    response = admin_client.post("/ajax/credit/admin-adjust", json=payload)
    assert response.status_code == 200
    assert captured["path"] == "/credit/admin/adjust"
    assert captured["payload"] == payload
