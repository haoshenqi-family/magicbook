"""R260: AI companion self-introduction editor (static source contracts)."""
import os

from babel.messages.pofile import read_po


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PANEL = os.path.join(ROOT, "cps", "templates", "ai_chat_panel.html")
JS = os.path.join(ROOT, "cps", "static", "js", "ai_chat.js")
CSS = os.path.join(ROOT, "cps", "static", "css", "ai_chat.css")
SEED = os.path.join(ROOT, "cps", "templates", "i18n_seed.html")
PO = os.path.join(ROOT, "cps", "translations", "zh_Hans_CN", "LC_MESSAGES", "messages.po")


def read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def test_panel_has_bounded_profile_editor_and_privacy_warning():
    html = read(PANEL)

    assert 'id="ai-user-profile-input"' in html
    assert 'maxlength="2000"' in html
    assert 'id="ai-user-profile-save"' in html
    assert 'id="ai-user-profile-clear"' in html
    assert 'id="ai-user-profile-count"' in html
    assert "Do not include passwords, keys, ID numbers" in html


def test_profile_js_uses_dynamic_i18n_and_safe_text_rendering():
    source = read(JS)
    start = source.index("function loadUserProfile()")
    end = source.index("function loadBookProfile()", start)
    block = source[start:end]

    assert '/ai/agent/profile"' in block
    assert '/ai/agent/profile/save' in block
    assert 'JSON.stringify({ selfIntroduction: text })' in block
    assert 'JSON.stringify({ selfIntroduction: "" })' in block
    assert "t(" in block
    assert "mbT(" not in block, "new copy must resolve translations at call time via t()"
    assert "$input.val(profile.selfIntroduction" in block
    assert '$("#ai-user-profile-input").val("")' in block
    assert ".html(" not in block, "user-controlled profile text must never be rendered as HTML"


def test_profile_i18n_copy_is_seeded_and_translated():
    seed = read(SEED)
    required = [
        "What AI knows about me",
        "This profile is sent to AI with every question. Do not include passwords, keys, ID numbers, or other sensitive information.",
        "Save profile",
        "Loading your profile…",
        "Profile saved",
        "Clear your AI profile? AI will no longer use this background.",
        "Profile cleared",
    ]
    for msgid in required:
        assert msgid in seed, msgid

    with open(PO, "rb") as handle:
        catalog = read_po(handle)
    for msgid in required:
        entry = catalog.get(msgid)
        assert entry is not None and entry.string, msgid


def test_mobile_profile_controls_meet_touch_target_contract():
    css = read(CSS)
    assert ".ai-user-profile-actions button { min-height: 44px; font-size: 15px; }" in css
