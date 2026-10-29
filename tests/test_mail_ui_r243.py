"""R243 mail UI guards: wiring, routing, safe rendering and admin notification."""

import gettext
import json
import os
import re
import shutil
import subprocess

import pytest
from babel.messages.pofile import read_po
from flask import render_template


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAIL_JS = os.path.join(ROOT, "cps", "static", "js", "mail.js")
CHAT_JS = os.path.join(ROOT, "cps", "static", "js", "ai_chat.js")
CREDITS_JS = os.path.join(ROOT, "cps", "static", "js", "credits.js")
SEED = os.path.join(ROOT, "cps", "templates", "i18n_seed.html")
PO = os.path.join(ROOT, "cps", "translations", "zh_Hans_CN",
                  "LC_MESSAGES", "messages.po")
MO = os.path.join(ROOT, "cps", "translations", "zh_Hans_CN",
                  "LC_MESSAGES", "messages.mo")


def _read(*parts):
    with open(os.path.join(ROOT, *parts), encoding="utf-8") as fh:
        return fh.read()


def _function(source, name, next_name):
    start = source.index("function " + name)
    end = source.index("function " + next_name, start)
    return source[start:end]


def test_mail_page_renders_only_for_logged_in_user(client, admin_client):
    template = _read("cps", "templates", "mail.html")
    assert template.startswith('{% extends "layout.html" %}')
    assert client.get("/mail").status_code == 302
    response = admin_client.get("/mail")
    assert response.status_code == 200
    body = response.get_data(as_text=True)
    for node_id in ("mail-page", "mail-page-loading", "mail-page-empty",
                    "mail-page-error", "mail-page-list", "mail-page-pager",
                    "mail-mark-all"):
        assert 'id="{}"'.format(node_id) in body
    assert 'id="mail-csrf"' not in body


def test_settings_mail_entry_is_logged_in_only(admin_client, client):
    body = admin_client.get("/reading/settings").get_data(as_text=True)
    assert body.count('id="top_mail"') == 1
    assert 'id="top-mail-badge"' in body
    anonymous = client.get("/login").get_data(as_text=True)
    assert 'id="top_mail"' not in anonymous
    assert "js/mail.js" not in anonymous


def test_layout_loads_mail_after_api_and_before_buddy_panel():
    source = _read("cps", "templates", "layout.html")
    api = source.index("js/common/api.js")
    mail = source.index("js/mail.js")
    panel = source.index("ai_chat_panel.html")
    assert api < mail < panel


def test_panel_has_fab_envelope_tabs_and_mail_skeleton(admin_client):
    body = admin_client.get("/buddy").get_data(as_text=True)
    assert 'id="ai-companion-mail-badge"' in body
    assert 'id="ai-companion-tabs"' in body
    assert 'id="ai-tab-chat"' in body
    assert 'id="ai-tab-mail"' in body
    assert 'id="ai-chat-pane"' in body
    assert 'id="ai-mail-pane"' in body
    assert 'id="ai-mail-mark-all"' in body
    assert 'id="ai-mail-view-all"' in body
    assert 'role="tab"' in body and 'aria-selected="true"' in body
    assert 'aria-controls="ai-mail-pane"' in body

    css = _read("cps", "static", "css", "mail.css")
    fab_rule = css.split("#ai-companion-mail-badge {", 1)[1].split("}", 1)[0]
    assert "pointer-events: none" in fab_rule
    assert "position: absolute" in fab_rule
    assert 'tabindex="-1"' in body


def test_fab_mail_state_maps_to_hidden_buddy_without_duplicate_badge():
    """R243/R244 交界：可见 FAB 只用自己的信封，隐藏后才映射到唤回药丸。"""
    chat = _read("cps", "static", "js", "ai_chat.js")
    mail = _read("cps", "static", "js", "mail.js")
    mail_css = _read("cps", "static", "css", "mail.css")
    sync_start = chat.index("function syncLetterBadge")
    sync = chat[sync_start:chat.index("window.AICompanion.showLetter", sync_start)]
    opener = _function(chat, "openDrawer", "closeDrawer")
    fab_rule = mail_css.split("#ai-companion-mail-badge {", 1)[1].split("}", 1)[0]

    assert "window.AICompanion.syncLetterBadge()" in mail
    assert 'wrap.classList.contains("buddy-hidden")) showLetter();' in sync
    assert "clearLetterBadge();" in opener
    # R244 的隐藏 ✕ 在右上；R243 信封让到左上，两个提示不互相遮挡。
    assert "left: -5px" in fab_rule
    assert "right: -5px" not in fab_rule


def test_shared_panel_omits_mail_surfaces_for_anonymous(app):
    with app.test_request_context("/"):
        body = render_template("ai_chat_panel.html", ai_context_title="")
    assert 'id="ai-companion-fab"' in body
    assert 'id="ai-companion-mail-badge"' not in body
    assert 'id="ai-companion-tabs"' not in body
    assert 'id="ai-tab-mail"' not in body
    assert 'id="ai-mail-pane"' not in body


@pytest.mark.parametrize("template", ["read.html", "readtxt.html", "readpdf.html"])
def test_all_buddy_readers_load_api_mail_before_panel(template):
    source = _read("cps", "templates", template)
    assert re.search(
        r"{% if current_user\.is_authenticated %}\s*<link[^>]+mail\.css",
        source, re.S,
    )
    assert re.search(
        r"{% if current_user\.is_authenticated %}\s*(?:{#.*?#}\s*)?"
        r"<script[^>]+js/mail\.js",
        source, re.S,
    )
    api = source.index("js/common/api.js")
    mail = source.index("js/mail.js")
    panel = source.index("ai_chat_panel.html")
    assert api < mail < panel
    assert "css/mail.css" in source


def test_readcbr_is_not_expanded_in_this_round():
    source = _read("cps", "templates", "readcbr.html")
    assert "js/mail.js" not in source
    assert "ai_chat_panel.html" not in source


def test_mail_state_surface_and_refresh_triggers():
    source = _read("cps", "static", "js", "mail.js")
    for member in ("refreshUnread", "loadPage", "markRead", "markAllRead",
                   "openInbox", "subscribe", "getState", "getUnreadForRouting"):
        assert re.search(r"\b{}\s*:".format(member), source)
    assert "window.MBApi.csrfToken()" in source
    assert "X-CSRFToken" in source
    assert "visibilitychange" in source
    assert 'window.addEventListener("focus"' in source
    assert 'window.addEventListener("pageshow"' in source
    assert "setInterval" not in source
    assert "localStorage" not in source and "sessionStorage" not in source
    assert "innerHTML" not in source


@pytest.mark.skipif(shutil.which("node") is None, reason="node is required")
def test_mail_state_keeps_last_known_count_and_uses_csrf():
    source = _read("cps", "static", "js", "mail.js")
    script = r"""
const source = process.argv[1];
global.window = {
  mbT: id => id,
  location: { href: "" },
  addEventListener: () => {},
  __mbBasePath: ""
};
global.document = {
  readyState: "loading",
  addEventListener: () => {},
  createElement: tag => ({ tagName: tag }),
  getElementById: () => null,
  hidden: false
};
let postOptions = null;
let postCalls = [];
window.MBApi = {
  csrfToken: () => "csrf-r243",
  httpJson: (url, options) => {
    if (url.indexOf("/unread-count") >= 0) {
      return Promise.resolve({
        ok: true, status: 200,
        data: { success: true, result: { count: 3 } }, raw: ""
      });
    }
    if (url.indexOf("/page") >= 0) {
      return Promise.resolve({
        ok: false, status: 503,
        data: { success: false, message: "mail list unavailable" }, raw: ""
      });
    }
    postCalls.push({ url, options });
    if (url.indexOf("/read-all") >= 0) {
      return Promise.resolve({
        ok: true, status: 200,
        data: { success: true, result: { affected: 1, unreadCount: 0 } },
        raw: ""
      });
    }
    postOptions = options;
    return Promise.resolve({
      ok: true, status: 200,
      data: { success: true, result: { id: 9, readAt: 123, unreadCount: 1 } },
      raw: ""
    });
  }
};
eval(source);
(async () => {
  const api = window.MBMail;
  await api.refreshUnread();
  let afterSuccess = api.getState();
  let listError = "";
  try { await api.loadPage(1, 20); } catch (error) { listError = error.message; }
  const afterError = api.getState();
  const routingAfterError = api.getUnreadForRouting();
  await api.markRead(9);
  const afterRead = api.getState();
  await api.markAllRead();
  process.stdout.write(JSON.stringify({
    afterSuccess,
    listError,
    afterError,
    routingAfterError,
    afterRead,
    afterAllRead: api.getState(),
    postMethod: postOptions && postOptions.method,
    postCsrf: postOptions && postOptions.headers["X-CSRFToken"],
    postBody: postOptions && postOptions.body,
    postUrls: postCalls.map(call => call.url)
  }));
})().catch(error => {
  console.error(error.stack || error);
  process.exit(1);
});
"""
    result = subprocess.run(
        ["node", "-e", script, source],
        capture_output=True, check=True, text=True, timeout=20,
    )
    data = json.loads(result.stdout)
    assert data["afterSuccess"]["status"] == "ready"
    assert data["afterSuccess"]["unreadCount"] == 3
    assert data["listError"] == "mail list unavailable"
    assert data["afterError"]["status"] == "ready"
    assert data["afterError"]["unreadCount"] == 3
    assert data["afterError"]["lastKnownUnreadCount"] == 3
    assert data["routingAfterError"] == 3
    assert data["afterRead"]["status"] == "ready"
    assert data["afterRead"]["unreadCount"] == 1
    assert data["postMethod"] == "POST"
    assert data["postCsrf"] == "csrf-r243"
    assert json.loads(data["postBody"]) == {"id": 9}
    assert data["afterAllRead"]["status"] == "ready"
    assert data["afterAllRead"]["unreadCount"] == 0
    assert data["postUrls"] == ["/ajax/mail/read", "/ajax/mail/read-all"]


@pytest.mark.skipif(shutil.which("node") is None, reason="node is required")
def test_latest_mail_request_wins_over_stale_unread_response():
    source = _read("cps", "static", "js", "mail.js")
    script = r"""
const source = process.argv[1];
global.window = {
  mbT: id => id,
  location: { href: "" },
  addEventListener: () => {},
  __mbBasePath: ""
};
global.document = {
  readyState: "loading",
  addEventListener: () => {},
  createElement: tag => ({ tagName: tag }),
  getElementById: () => null,
  hidden: false
};
let resolveUnread;
let resolvePage;
window.MBApi = {
  csrfToken: () => "csrf-r243",
  httpJson: url => new Promise(resolve => {
    if (url.indexOf("/unread-count") >= 0) resolveUnread = resolve;
    else resolvePage = resolve;
  })
};
eval(source);
(async () => {
  const unread = window.MBMail.refreshUnread();
  const page = window.MBMail.loadPage(1, 5);
  resolvePage({
    ok: true, status: 200,
    data: { success: true, result: {
      records: [], total: 0, pageNo: 1, pageSize: 5, unreadCount: 4
    } },
    raw: ""
  });
  await page;
  resolveUnread({
    ok: true, status: 200,
    data: { success: true, result: { count: 9 } },
    raw: ""
  });
  await unread;
  process.stdout.write(JSON.stringify(window.MBMail.getState()));
})().catch(error => {
  console.error(error.stack || error);
  process.exit(1);
});
"""
    result = subprocess.run(
        ["node", "-e", script, source],
        capture_output=True, check=True, text=True, timeout=20,
    )
    data = json.loads(result.stdout)
    assert data["status"] == "ready"
    assert data["unreadCount"] == 4
    assert data["lastKnownUnreadCount"] == 4


def test_opening_mail_tab_does_not_mark_read():
    source = _read("cps", "static", "js", "ai_chat.js")
    activate = _function(source, "activateDrawerTab", "showMailPeekState")
    load = _function(source, "loadMailPeek", "markAllDrawerMailRead")
    assert "loadMailPeek" in activate
    assert "markRead" not in activate
    assert "markRead" not in load
    render = _function(source, "renderMailPeek", "loadMailPeek")
    assert "onOpen" in render and "MBMail.markRead" in render


def test_mail_page_marks_read_only_after_item_expand():
    source = _read("cps", "static", "js", "mail.js")
    render = _function(source, "renderPageData", "loadInboxPage")
    load = _function(source, "loadInboxPage", "initPage")
    assert "onOpen" in render and "markRead" in render
    assert "markRead" not in load


def test_chat_bubble_always_explicitly_opens_chat():
    source = _read("cps", "static", "js", "ai_chat.js")
    dispatch = _function(source, "dispatchBubbleAction", "renderBubbles")
    chat_branch = dispatch.split('if (id === "chat")', 1)[1].split("return;", 1)[0]
    assert 'openDrawer("chat")' in chat_branch
    assert 'trigger("click")' not in chat_branch


def test_credits_admin_notification_form_and_payload():
    template = _read("cps", "templates", "credits.html")
    assert 'id="credit-admin-notify"' in template
    assert 'id="credit-admin-notification-message"' in template
    assert 'maxlength="500"' in template

    source = _read("cps", "static", "js", "credits.js")
    sync = _function(source, "syncAdminNotificationState", "resetAdminNotification")
    assert "amount > 0" in sync
    assert "prop('checked', false)" in sync
    assert "message.val('')" in sync
    assert "notify.prop('disabled'" in sync
    assert "message.prop('disabled'" in sync
    assert "notify: notify" in source
    assert "payload.notificationMessage = notificationMessage" in source
    assert "t('Send an arrival notification too.')" in source
    assert "t('Do not send an arrival notification.')" in source
    assert "resetAdminNotification();" in source


@pytest.mark.skipif(shutil.which("node") is None, reason="node is required")
def test_credit_notification_toggle_executes_production_helper():
    source = _read("cps", "static", "js", "credits.js")
    sync = _function(source, "syncAdminNotificationState", "resetAdminNotification")
    script = r"""
const body = process.argv[1];
const fields = {
  "#credit-admin-amount": { value: "" },
  "#credit-admin-notify": { checked: false, disabled: false },
  "#credit-admin-notification-message": { value: "", disabled: false }
};
function $(selector) {
  const node = fields[selector];
  return {
    val(value) {
      if (arguments.length) node.value = String(value);
      return node.value;
    },
    prop(name, value) {
      if (arguments.length > 1) node[name] = value;
      return node[name];
    }
  };
}
eval(body);
syncAdminNotificationState();
const empty = JSON.parse(JSON.stringify(fields));
fields["#credit-admin-amount"].value = "-5";
fields["#credit-admin-notify"].checked = true;
fields["#credit-admin-notification-message"].value = "stale";
syncAdminNotificationState();
const negative = JSON.parse(JSON.stringify(fields));
fields["#credit-admin-amount"].value = "10";
syncAdminNotificationState();
const positiveUnchecked = JSON.parse(JSON.stringify(fields));
fields["#credit-admin-notify"].checked = true;
syncAdminNotificationState();
const positiveChecked = JSON.parse(JSON.stringify(fields));
process.stdout.write(JSON.stringify({
  empty, negative, positiveUnchecked, positiveChecked
}));
"""
    result = subprocess.run(
        ["node", "-e", script, sync],
        capture_output=True, check=True, text=True, timeout=20,
    )
    data = json.loads(result.stdout)
    empty = data["empty"]
    negative = data["negative"]
    positive_unchecked = data["positiveUnchecked"]
    positive_checked = data["positiveChecked"]
    assert empty["#credit-admin-notify"]["disabled"] is True
    assert empty["#credit-admin-notification-message"]["disabled"] is True
    assert negative["#credit-admin-notify"] == {"checked": False, "disabled": True}
    assert negative["#credit-admin-notification-message"] == {
        "value": "", "disabled": True,
    }
    assert positive_unchecked["#credit-admin-notify"]["disabled"] is False
    assert positive_unchecked["#credit-admin-notification-message"]["disabled"] is True
    assert positive_checked["#credit-admin-notification-message"]["disabled"] is False


@pytest.mark.skipif(shutil.which("node") is None, reason="node is required")
def test_fab_routing_executes_production_helper():
    source = _read("cps", "static", "js", "ai_chat.js")
    body = _function(source, "chooseFabTab", "initDrawerTabs")
    script = """
const body = process.argv[1];
eval(body);
const cases = [[false, 0], [false, 3], [true, 0], [true, 8]];
process.stdout.write(JSON.stringify(cases.map(([open, n]) => chooseFabTab(open, n))));
"""
    result = subprocess.run(
        ["node", "-e", script, body],
        capture_output=True, check=True, text=True, timeout=20,
    )
    assert json.loads(result.stdout) == ["chat", "mail", None, None]


@pytest.mark.skipif(shutil.which("node") is None, reason="node is required")
def test_mail_action_whitelist_executes_production_helper():
    source = _read("cps", "static", "js", "mail.js")
    labels_start = source.index("var ACTION_LABELS")
    labels_end = source.index("};", labels_start) + 2
    labels = source[labels_start:labels_end]
    helper = _function(source, "safeActionPath", "replaceTokens")
    script = """
eval(process.argv[1]);
eval(process.argv[2]);
const paths = ["/buddy", "/achievements", "/credits", "/me",
               "//evil.example/buddy", "https://evil.example/credits",
               "javascript:alert(1)"];
process.stdout.write(JSON.stringify(paths.map(safeActionPath)));
"""
    result = subprocess.run(
        ["node", "-e", script, labels, helper],
        capture_output=True, check=True, text=True, timeout=20,
    )
    assert json.loads(result.stdout) == [
        "/buddy", "/achievements", "/credits", "", "", "", "",
    ]


@pytest.mark.skipif(shutil.which("node") is None, reason="node is required")
def test_mail_body_uses_text_nodes_and_blocks_unsafe_action():
    source = _read("cps", "static", "js", "mail.js")
    script = r"""
const source = process.argv[1];
class FakeNode {
  constructor(tag) {
    this.tagName = String(tag).toUpperCase();
    this.children = [];
    this.className = "";
    this.hidden = false;
    this.attributes = {};
    this.listeners = {};
    this._text = "";
    this.classList = {
      toggle: (name, on) => {
        const parts = new Set(this.className.split(/\s+/).filter(Boolean));
        if (on) parts.add(name); else parts.delete(name);
        this.className = Array.from(parts).join(" ");
      },
      remove: (name) => {
        this.className = this.className.split(/\s+/).filter(x => x && x !== name).join(" ");
      }
    };
  }
  set textContent(value) { this._text = String(value); this.children = []; }
  get textContent() {
    return this._text + this.children.map(child => child.textContent).join("");
  }
  appendChild(child) { this.children.push(child); child.parentNode = this; return child; }
  setAttribute(name, value) { this.attributes[name] = String(value); }
  removeAttribute(name) { delete this.attributes[name]; }
  addEventListener(name, fn) { this.listeners[name] = fn; }
  querySelector(selector) {
    const wanted = selector.replace(/^\./, "");
    for (const child of this.children) {
      if (child.className.split(/\s+/).includes(wanted)) return child;
      const nested = child.querySelector(selector);
      if (nested) return nested;
    }
    return null;
  }
}
global.window = {
  mbT: id => id,
  location: { href: "" },
  addEventListener: () => {},
  __mbBasePath: ""
};
global.document = {
  readyState: "loading",
  addEventListener: () => {},
  createElement: tag => new FakeNode(tag),
  getElementById: () => null,
  hidden: false
};
eval(source);
const malicious = '<img src=x onerror="alert(1)"><script>alert(2)<\/script>';
const bad = window.MBMail.buildMailItem({
  id: 1,
  mailType: "CREDIT_GRANTED",
  customMessage: malicious,
  actionPath: "javascript:alert(3)",
  params: {},
  readAt: null,
  resolvedAt: null,
  createdAt: 1
}).element;
const good = window.MBMail.buildMailItem({
  id: 2,
  mailType: "BUDDY_CLAIMABLE",
  actionPath: "/buddy",
  params: {},
  readAt: null,
  resolvedAt: null,
  createdAt: 2
}).element;
function tags(node, out = []) {
  out.push(node.tagName);
  node.children.forEach(child => tags(child, out));
  return out;
}
const badTags = tags(bad), goodTags = tags(good);
process.stdout.write(JSON.stringify({
  badHasHtmlTag: badTags.includes("IMG") || badTags.includes("SCRIPT"),
  badHasAction: badTags.includes("A"),
  badTextIncludesPayload: bad.textContent.includes(malicious),
  goodHasAction: goodTags.includes("A"),
  goodActionHref: (function find(node) {
    if (node.tagName === "A") return node.href;
    for (const child of node.children) {
      const found = find(child);
      if (found) return found;
    }
    return "";
  })(good)
}));
"""
    result = subprocess.run(
        ["node", "-e", script, source],
        capture_output=True, check=True, text=True, timeout=20,
    )
    assert json.loads(result.stdout) == {
        "badHasHtmlTag": False,
        "badHasAction": False,
        "badTextIncludesPayload": True,
        "goodHasAction": True,
        "goodActionHref": "/buddy",
    }


def test_mail_js_translations_are_in_seed_po_and_mo():
    literals = set()
    for path in (MAIL_JS, CHAT_JS, CREDITS_JS):
        with open(path, encoding="utf-8") as fh:
            source = fh.read()
        literals.update(match.group(2) for match in re.finditer(
            r"""(?<![\w.])t\(\s*(["'])((?:\\.|(?!\1).)*?)\1""", source))
    mail_source = _read("cps", "static", "js", "mail.js")
    labels_start = mail_source.index("var ACTION_LABELS")
    labels_end = mail_source.index("};", labels_start)
    literals.update(re.findall(r':\s*"([^"]+)"', mail_source[labels_start:labels_end]))

    seed = _read("cps", "templates", "i18n_seed.html")
    seeded = set(re.findall(r'"([^"\n]+)":\s*_\(', seed))
    missing = sorted(literals - seeded)
    assert not missing, "t() 词条不在 i18n_seed.html：{!r}".format(missing)

    with open(PO, "rb") as fh:
        catalog = read_po(fh)
    untranslated = sorted(msgid for msgid in literals
                          if not (catalog.get(msgid) and catalog.get(msgid).string))
    assert not untranslated, "t() 词条在 zh po 缺失或为空：{!r}".format(untranslated)

    with open(MO, "rb") as fh:
        translations = gettext.GNUTranslations(fh)
    still_english = sorted(msgid for msgid in literals
                           if translations.gettext(msgid) == msgid)
    assert not still_english, "t() 词条在编译后的 mo 没有译文：{!r}".format(still_english)
