"""Tests for CSP headers that enable blob: media playback in the reader.

The reader plays AI TTS audio from a URL.createObjectURL(blob) URL. That is a
"media" load, governed by the CSP media-src directive. If media-src is not set
it falls back to default-src ('self' ...), which excludes blob:, so the browser
blocks playback: "Loading media from 'blob:...' violates ... CSP". The reader
page must therefore explicitly allow media-src 'self' blob:.
"""
from unittest.mock import patch

import pytest

from cps import config as cw_config

# keep a known, stable base of default-src hosts (trustedhosts may be empty)
_original_trustedhosts = None


def _set_html_desired(config_module, value):
    """Force config_trustedhosts to a known value regardless of DB config."""
    from cps import config as cps_config

    return patch.object(cps_config, "config_trustedhosts", value)


@pytest.fixture
def make_response_headers(app):
    """Return a callable that runs add_security_headers for a given endpoint."""

    def _run(endpoint_name):
        from cps import web

        # Simulate a request whose url_rule resolves to the given endpoint.
        # add_security_headers reads request.endpoint from url_rule.endpoint.
        with app.test_request_context("/read/1/epub"):
            from flask import request

            # Build a fake rule whose endpoint matches what flask gives us.
            rule = type("Rule", (), {"endpoint": endpoint_name, "methods": {"GET"}, "arguments": {"book_id", "book_format"}})()
            request.url_rule = rule
            # after_request hooks expect a response to decorate
            from flask import make_response

            resp = make_response("ok")
            resp = web.add_security_headers(resp)
            return resp

    return _run


def test_reader_page_allows_blob_media(app, make_response_headers):
    """Reader (/read/...) must allow media-src 'self' blob: so TTS audio plays.

    Before the fix no media-src was emitted, so media loads (blob: audio from
    URL.createObjectURL) fell back to default-src and were blocked: the reader
    showed the TTS call succeeding but no sound.
    """
    with _set_html_desired(cw_config, "'self' 'unsafe-inline' 'unsafe-eval'"):
        resp = make_response_headers("web.read_book")

    csp = resp.headers.get("Content-Security-Policy")
    assert csp, "reader page must set a Content-Security-Policy"

    # Find the media-src directive and ensure blob: is allowed.
    media_directive = [d.strip() for d in csp.split(";") if d.strip().startswith("media-src")]
    assert media_directive, (
        "reader page CSP must explicitly set media-src; currently falls back "
        "to default-src which blocks blob: audio playback. CSP was: " + csp
    )
    assert "blob:" in media_directive[0], (
        "media-src must allow blob: for TTS audio; directive was: " + media_directive[0]
    )
    assert "'self'" in media_directive[0]


def test_non_reader_pages_still_block_blob_media(app, make_response_headers):
    """Any non-reader page keeps the stricter (no blob) CSP default.

    blob: should stay blocked outside the reader so we do not widen the
    security surface globally.
    """
    with _set_html_desired(cw_config, "'self' 'unsafe-inline' 'unsafe-eval'"):
        resp = make_response_headers("web.index")

    csp = resp.headers.get("Content-Security-Policy")
    assert csp

    media_directive = [d.strip() for d in csp.split(";") if d.strip().startswith("media-src")]
    # Non-reader pages have no reason to emit media-src at all.
    assert not media_directive, "non-reader pages should not emit media-src: " + csp