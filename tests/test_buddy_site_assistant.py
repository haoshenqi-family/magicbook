"""Site-wide Buddy assistant wiring (R220)."""

from pathlib import Path


def test_layout_includes_assistant_for_authenticated_pages():
    layout = Path("cps/templates/layout.html").read_text(encoding="utf-8")
    assert "{% include 'ai_chat_panel.html' %}" in layout


def test_site_extractor_supplies_page_context():
    source = Path("cps/static/js/ai_page_extract.js").read_text(encoding="utf-8")
    assert "extractSitePage" in source
    assert 'return "site";' in source


def test_site_conversations_do_not_require_book_id():
    source = Path("cps/static/js/ai_chat.js").read_text(encoding="utf-8")
    assert 'BOOK_ID ? { bookId: BOOK_ID } : {}' in source
    assert 'BOOK_ID || "site"' in source
