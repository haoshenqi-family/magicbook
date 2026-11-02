"""R250 admin operation mail: permissions, proxy contract, UI and i18n guards."""

import gettext
import json
import os
import re
import shutil
import subprocess

import pytest
from babel.messages.pofile import read_po


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JS = os.path.join(ROOT, "cps", "static", "js", "admin_mail.js")
MAIL_JS = os.path.join(ROOT, "cps", "static", "js", "mail.js")
TEMPLATE = os.path.join(ROOT, "cps", "templates", "admin_mail.html")
SEED = os.path.join(ROOT, "cps", "templates", "i18n_seed.html")
PO = os.path.join(ROOT, "cps", "translations", "zh_Hans_CN", "LC_MESSAGES", "messages.po")
MO = os.path.join(ROOT, "cps", "translations", "zh_Hans_CN", "LC_MESSAGES", "messages.mo")


def _read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


@pytest.fixture
def proxy_calls(monkeypatch):
    import cps.routes.admin_mail as admin_mail

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

    monkeypatch.setattr(admin_mail, "_moonwell_proxy", fake_proxy)
    return calls


def _login_plain(app, name="admin-mail-plain"):
    from cps import ub
    from werkzeug.security import generate_password_hash

    user = ub.session.query(ub.User).filter(ub.User.name == name).first()
    if user is None:
        user = ub.User(name=name, email=name + "@example.com",
                       password=generate_password_hash("plain-pass"))
        ub.session.add(user)
        ub.session.commit()
    assert not user.role_admin()
    client = app.test_client()
    assert client.post(
        "/login", data={"username": name, "password": "plain-pass"}
    ).status_code == 302
    from cps import config as cw_config
    cw_config.db_configured = True
    return client


def test_admin_mail_page_permissions(app, admin_client):
    assert app.test_client().get("/admin/mail").status_code == 302
    plain = _login_plain(app)
    assert plain.get("/admin/mail").status_code == 403
    assert admin_client.get("/admin/mail").status_code == 200


@pytest.mark.parametrize(
    "method,path,kwargs",
    [
        ("get", "/ajax/admin-mail/users", {}),
        ("get", "/ajax/admin-mail/audience-count", {}),
        ("post", "/ajax/admin-mail/send", {"json": {}}),
        ("get", "/ajax/admin-mail/campaigns", {}),
        ("post", "/ajax/admin-mail/recall", {"json": {"campaignId": 1}}),
    ],
)
def test_proxies_reject_non_admin_before_upstream(app, monkeypatch,
                                                  method, path, kwargs):
    import cps.routes.admin_mail as admin_mail

    hits = []
    monkeypatch.setattr(
        admin_mail, "_moonwell_proxy",
        lambda *args, **kw: hits.append((args, kw)),
    )
    response = getattr(_login_plain(app), method)(path, **kwargs)
    assert response.status_code == 403
    assert response.get_json()["success"] is False
    assert hits == []


def test_users_proxy_normalizes_and_keeps_three_tuple(admin_client, proxy_calls):
    response = admin_client.get(
        "/ajax/admin-mail/users?keyword=%20hao%20&limit=999")
    assert response.status_code == 200
    assert response.headers["X-Upstream"] == "moon-well"
    assert proxy_calls == [{
        "path": "/mail/admin/users",
        "payload": {"keyword": "hao", "limit": 500},
        "timeout": 10,
        "label": "admin mail users",
        "method": "POST",
    }]


def test_audience_count_proxy_is_admin_only_and_forwards_empty_payload(
        admin_client, proxy_calls):
    response = admin_client.get("/ajax/admin-mail/audience-count")
    assert response.status_code == 200
    assert proxy_calls[-1] == {
        "path": "/mail/admin/audience/count",
        "payload": {},
        "timeout": 10,
        "label": "admin mail audience count",
        "method": "POST",
    }


def test_send_proxy_forwards_only_whitelisted_fields(admin_client, proxy_calls):
    response = admin_client.post("/ajax/admin-mail/send", json={
        "audienceType": "selected",
        "userIds": [7, 8, 7],
        "title": "  Maintenance  ",
        "body": "  Tonight at 22:00.  ",
        "actionPath": "/mail",
        "operator": 99,
        "unexpected": "drop",
    })
    assert response.status_code == 200
    assert proxy_calls[-1] == {
        "path": "/mail/admin/send",
        "payload": {
            "audienceType": "SELECTED",
            "userIds": [7, 8],
            "title": "Maintenance",
            "body": "Tonight at 22:00.",
            "actionPath": "/mail",
        },
        "timeout": 30,
        "label": "admin mail send",
        "method": "POST",
    }


def test_send_all_ignores_client_recipient_list(admin_client, proxy_calls):
    response = admin_client.post("/ajax/admin-mail/send", json={
        "audienceType": "ALL",
        "userIds": [7, 8],
        "title": "Everyone",
        "body": "Hello.",
        "actionPath": "",
    })
    assert response.status_code == 200
    payload = proxy_calls[-1]["payload"]
    assert payload == {
        "audienceType": "ALL",
        "title": "Everyone",
        "body": "Hello.",
        "actionPath": "",
    }
    assert "userIds" not in payload


@pytest.mark.parametrize("payload,message", [
    ([], "Invalid request"),
    ({"audienceType": "NOPE"}, "Audience must be selected users or all users"),
    ({"audienceType": "SELECTED"}, "Select at least one user"),
    ({"audienceType": "SELECTED", "userIds": [0]}, "Select at least one user"),
    ({"audienceType": "SELECTED", "userIds": [True]}, "Select at least one user"),
    ({"audienceType": "SELECTED", "userIds": [7]}, "Title is required"),
    ({"audienceType": "SELECTED", "userIds": [7], "title": "x" * 81},
     "Title must be at most 80 characters"),
    ({"audienceType": "SELECTED", "userIds": [7], "title": "T"},
     "Message body is required"),
    ({"audienceType": "SELECTED", "userIds": [7], "title": "T", "body": "x" * 501},
     "Message body must be at most 500 characters"),
    ({"audienceType": "SELECTED", "userIds": [7], "title": "T", "body": "B",
      "actionPath": "https://evil.example/"}, "Invalid destination"),
])
def test_send_rejects_invalid_payload_before_upstream(
        admin_client, proxy_calls, payload, message):
    response = admin_client.post("/ajax/admin-mail/send", json=payload)
    assert response.status_code == 400
    assert response.get_json() == {"success": False, "message": message}
    assert proxy_calls == []


def test_send_rejects_more_than_5000_before_upstream(admin_client, proxy_calls):
    response = admin_client.post("/ajax/admin-mail/send", json={
        "audienceType": "SELECTED",
        "userIds": list(range(1, 5002)),
        "title": "T",
        "body": "B",
    })
    assert response.status_code == 400
    assert proxy_calls == []


@pytest.mark.parametrize(
    "query,expected",
    [
        ("", {"pageNo": 1, "pageSize": 20}),
        ("?pageNo=2&pageSize=7", {"pageNo": 2, "pageSize": 7}),
        ("?pageNo=0&pageSize=-4", {"pageNo": 1, "pageSize": 20}),
        ("?pageNo=nope&pageSize=bad", {"pageNo": 1, "pageSize": 20}),
        ("?pageNo=999999&pageSize=999", {"pageNo": 100000, "pageSize": 50}),
    ],
)
def test_campaign_proxy_normalizes_paging(admin_client, proxy_calls, query, expected):
    response = admin_client.get("/ajax/admin-mail/campaigns" + query)
    assert response.status_code == 200
    assert proxy_calls[-1]["path"] == "/mail/admin/campaigns/page"
    assert proxy_calls[-1]["payload"] == expected


def test_recall_proxy_forwards_only_campaign_id(admin_client, proxy_calls):
    response = admin_client.post(
        "/ajax/admin-mail/recall", json={"campaignId": 42, "operator": 99})
    assert response.status_code == 200
    assert proxy_calls[-1]["path"] == "/mail/admin/recall"
    assert proxy_calls[-1]["payload"] == {"campaignId": 42}


@pytest.mark.parametrize("payload", [
    {}, {"campaignId": 0}, {"campaignId": -1}, {"campaignId": "4"},
    {"campaignId": True}, {"campaignId": 2.5}, [], None,
])
def test_recall_rejects_invalid_campaign_before_upstream(
        admin_client, proxy_calls, payload):
    response = admin_client.post("/ajax/admin-mail/recall", json=payload)
    assert response.status_code == 400
    assert response.get_json() == {"success": False, "message": "Invalid campaign"}
    assert proxy_calls == []


def test_upstream_failure_body_status_and_headers_pass_through(
        admin_client, monkeypatch):
    import cps.routes.admin_mail as admin_mail

    body = json.dumps({"success": False, "message": "upstream down"})
    headers = {"Content-Type": "application/json", "X-Trace-Id": "trace-503"}
    monkeypatch.setattr(
        admin_mail, "_moonwell_proxy",
        lambda *args, **kwargs: (body, 503, headers),
    )
    response = admin_client.get("/ajax/admin-mail/campaigns")
    assert response.status_code == 503
    assert response.get_data(as_text=True) == body
    assert response.headers["X-Trace-Id"] == "trace-503"


def test_page_contains_composer_preview_history_and_recall(admin_client):
    body = admin_client.get("/admin/mail").get_data(as_text=True)
    page_start = body.index('id="admin-mail-page"')
    page_end = body.index("</div>", body.index('id="admin-mail-history-next"'))
    page_body = body[page_start:page_end]
    for node_id in (
            "admin-mail-page", "admin-mail-form", "admin-mail-user-search",
            "admin-mail-title", "admin-mail-body", "admin-mail-action",
            "admin-mail-preview", "admin-mail-send", "admin-mail-history-list",
            "admin-mail-history-prev", "admin-mail-history-next"):
        assert 'id="{}"'.format(node_id) in body
    assert 'name="admin-mail-audience" value="SELECTED"' in body
    assert 'name="admin-mail-audience" value="ALL"' in body
    assert 'maxlength="80"' in body
    assert 'maxlength="500"' in body
    assert "All users includes every account, including administrator accounts." in body
    assert 'href="/admin/view"' not in page_body
    assert 'id="admin-mail-back"' not in page_body
    assert 'id="admin-mail"\n           class="mb-l2-link active"' in body


def test_admin_entry_is_single_and_targets_new_page():
    source = _read(os.path.join(ROOT, "cps", "templates", "admin.html"))
    assert source.count('id="admin_operation_mail"') == 1
    assert "url_for('web.admin_mail_page')" in source


def test_mail_js_renders_admin_announcement_as_plain_text():
    source = _read(MAIL_JS)
    assert 'mail.mailType === "ADMIN_ANNOUNCEMENT"' in source
    assert "text(mail.title).trim()" in source
    assert "text(mail && mail.customMessage).trim()" in source
    for path in ("/credits", "/buddy", "/achievements", "/learning", "/mail"):
        assert '{}:'.format('"' + path + '"') in source


def test_admin_mail_js_has_no_persistent_composer_state():
    source = _read(JS)
    code = re.sub(r"^\s*(?:\*|/\*|\*/|//).*$", "", source, flags=re.M)
    assert "localStorage" not in code
    assert "sessionStorage" not in code
    assert "innerHTML" not in source
    assert "textContent" in source
    assert "MAX_RECIPIENTS = 5000" in source
    assert "MAX_TITLE = 80" in source
    assert "MAX_BODY = 500" in source


def test_admin_mail_js_translations_are_in_seed_po_and_mo():
    literals = set(match.group(2) for match in re.finditer(
        r"""(?<![\w.])t\(\s*(["'])((?:\\.|(?!\1).)*?)\1""", _read(JS)))
    labels = re.search(r"var ACTION_LABELS = \{(.*?)\n  \};", _read(JS), re.S)
    assert labels
    literals.update(re.findall(r':\s*"([^"]+)"', labels.group(1)))

    seed = _read(SEED)
    seeded = set(re.findall(r'"((?:[^"\\]|\\.)*)":\s*_\(', seed))
    seeded = {value.replace('\\"', '"').replace("\\'", "'")
              .replace("\\\\", "\\") for value in seeded}
    assert not sorted(literals - seeded)

    with open(PO, "rb") as fh:
        catalog = read_po(fh)
    missing = sorted(msgid for msgid in literals
                     if not (catalog.get(msgid) and catalog.get(msgid).string))
    assert not missing

    with open(MO, "rb") as fh:
        translations = gettext.GNUTranslations(fh)
    still_english = sorted(msgid for msgid in literals
                           if translations.gettext(msgid) == msgid)
    assert not still_english


def test_send_confirmation_does_not_claim_the_send_is_irreversible():
    source = _read(JS)
    assert "This cannot be undone." not in source
    assert ("Send this announcement to {audience}? You can recall the whole "
            "batch later, but recipients may already see it.") in source


def test_admin_mail_template_msgids_are_translated():
    template = _read(TEMPLATE)
    msgids = {match.group(2) for match in re.finditer(
        r"""_\s*\(\s*(["'])((?:\\.|(?!\1).)*?)\1""", template)}
    with open(PO, "rb") as fh:
        catalog = read_po(fh)
    missing = sorted(msgid for msgid in msgids
                     if not (catalog.get(msgid) and catalog.get(msgid).string))
    assert not missing
    with open(MO, "rb") as fh:
        translations = gettext.GNUTranslations(fh)
    assert not sorted(msgid for msgid in msgids
                      if translations.gettext(msgid) == msgid)


@pytest.mark.skipif(shutil.which("node") is None, reason="node is required")
def test_admin_mail_js_checks_syntax():
    subprocess.run(["node", "--check", JS], check=True, timeout=20)


@pytest.mark.skipif(shutil.which("node") is None, reason="node is required")
def test_admin_mail_js_dedupes_and_rejects_over_limit():
    script = r"""
const fs = require("fs");
const source = fs.readFileSync(process.argv[1], "utf8");
global.window = {
  mbT: id => id,
  confirm: () => true,
  MBApi: { csrfToken: () => "csrf", httpJson: () => Promise.resolve({
    ok: true, status: 200,
    data: { success: true, result: { records: [], total: 0, pageNo: 1, pageSize: 20 } }
  }) }
};
global.document = {
  readyState: "loading",
  addEventListener: () => {},
  querySelectorAll: () => [],
  createElement: tag => ({
    tagName: tag, className: "", textContent: "", children: [],
    appendChild(child) { this.children.push(child); return child; },
    setAttribute() {}, addEventListener() {}
  }),
  getElementById: () => null
};
eval(source);
const api = window.AdminMail;
api.addRecipient({ userId: 7, username: "seven" });
api.addRecipient({ userId: 7, username: "seven-again" });
api.addRecipient({ userId: 8, username: "eight" });
process.stdout.write(JSON.stringify({
  maxRecipients: api.MAX_RECIPIENTS,
  maxTitle: api.MAX_TITLE,
  maxBody: api.MAX_BODY,
  actionPaths: Object.keys(api.ACTION_LABELS),
  selected: api.getSelectedUserIds()
}));
"""
    result = subprocess.run(
        ["node", "-e", script, JS],
        capture_output=True, check=True, text=True, timeout=20,
    )
    data = json.loads(result.stdout)
    assert data["maxRecipients"] == 5000
    assert data["maxTitle"] == 80
    assert data["maxBody"] == 500
    assert data["actionPaths"] == [
        "/credits", "/buddy", "/achievements", "/learning", "/mail"
    ]
    assert data["selected"] == [7, 8]


@pytest.mark.skipif(shutil.which("node") is None, reason="node is required")
def test_admin_mail_js_rejects_the_five_thousand_and_first_recipient():
    script = r"""
const fs = require("fs");
const source = fs.readFileSync(process.argv[1], "utf8");
const alert = {
  id: "admin-mail-alert", hidden: false, disabled: false,
  textContent: "", value: "", children: [],
  appendChild(child) { this.children.push(child); return child; },
  setAttribute() {}, addEventListener() {}
};
global.window = {
  mbT: id => id,
  confirm: () => true,
  MBApi: { csrfToken: () => "csrf", httpJson: () => Promise.resolve({
    ok: true, status: 200,
    data: { success: true, result: { records: [], total: 0, pageNo: 1, pageSize: 20 } }
  }) }
};
global.document = {
  readyState: "complete",
  addEventListener: () => {},
  querySelectorAll: () => [],
  createElement: tag => ({
    tagName: tag, className: "", textContent: "", children: [],
    appendChild(child) { this.children.push(child); return child; },
    setAttribute() {}, addEventListener() {}
  }),
  getElementById: id => id === "admin-mail-alert" ? alert : null
};
eval(source);
const api = window.AdminMail;
for (let id = 1; id <= 5001; id += 1) {
  api.addRecipient({ userId: id, username: "reader" + id });
}
process.stdout.write(JSON.stringify({
  selected: api.getSelectedUserIds(),
  alert: alert.textContent
}));
"""
    result = subprocess.run(
        ["node", "-e", script, JS],
        capture_output=True, check=True, text=True, timeout=20,
    )
    data = json.loads(result.stdout)
    assert data["selected"] == list(range(1, 5001))
    assert data["alert"] == "At most 5000 recipients per send"


@pytest.mark.skipif(shutil.which("node") is None, reason="node is required")
def _run_admin_mail_audience_count(count):
    script = r"""
const fs = require("fs");
const source = fs.readFileSync(process.argv[1], "utf8");
const elements = {};
function node(id) {
  return elements[id] || (elements[id] = {
    id, hidden: false, disabled: false, textContent: "", value: "", children: [],
    appendChild(child) { this.children.push(child); return child; },
    setAttribute() {}, addEventListener() {}
  });
}
const audienceCount = Number(process.argv[2]);
global.window = {
  mbT: id => id,
  confirm: message => { global.confirmMessage = message; return true; },
  MBApi: { csrfToken: () => "csrf", httpJson: () => Promise.resolve({
    ok: true, status: 200,
    data: { success: true, result: audienceCount }
  }) }
};
global.document = {
  readyState: "complete",
  addEventListener: () => {},
  querySelectorAll: () => [],
  createElement: tag => ({
    tagName: tag, className: "", textContent: "", children: [],
    appendChild(child) { this.children.push(child); return child; },
    setAttribute() {}, addEventListener() {}
  }),
  getElementById: id => node(id)
};
eval(source);
const api = window.AdminMail;
node("admin-mail-title").value = "Maintenance";
node("admin-mail-body").value = "Tonight.";

(async () => {
  api.setAudience("ALL");
  await new Promise(resolve => setTimeout(resolve, 0));
  api.invalidatePreview();
  const exactPill = node("admin-mail-preview-audience").textContent;
  process.stdout.write(JSON.stringify({
    exactPill,
    preview: api.buildPreview(),
    audienceCount: api.getAudienceCount(),
    confirmMessage: global.confirmMessage || null
  }));
})().catch(error => { console.error(error); process.exit(1); });
"""
    result = subprocess.run(
        ["node", "-e", script, JS, str(count)],
        capture_output=True, check=True, text=True, timeout=20,
    )
    return json.loads(result.stdout)


@pytest.mark.skipif(shutil.which("node") is None, reason="node is required")
def test_admin_mail_js_keeps_exact_all_user_count_after_edit():
    data = _run_admin_mail_audience_count(5000)
    assert data["exactPill"] == "5000 recipients"
    assert data["preview"]["audienceType"] == "ALL"
    assert data["audienceCount"] == 5000


@pytest.mark.skipif(shutil.which("node") is None, reason="node is required")
def test_admin_mail_js_blocks_all_audience_over_5000():
    data = _run_admin_mail_audience_count(5001)
    assert data["exactPill"] == "5001 recipients"
    assert data["preview"] == {
        "error": "At most 5000 recipients per send"}
