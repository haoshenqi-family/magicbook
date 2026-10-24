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

    def _run(endpoint_name, accept="text/html,application/xhtml+xml"):
        from cps import web

        # Simulate a request whose url_rule resolves to the given endpoint.
        # add_security_headers reads request.endpoint from url_rule.endpoint.
        with app.test_request_context("/read/1/epub"):
            from flask import request

            # Build a fake rule whose endpoint matches what flask gives us.
            rule = type("Rule", (), {"endpoint": endpoint_name, "methods": {"GET"}, "arguments": {"book_id", "book_format"}})()
            request.url_rule = rule
            request.environ["HTTP_ACCEPT"] = accept
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


def test_reader_page_allows_youdao_word_audio(app, make_response_headers):
    """Reader must allow media-src https://dict.youdao.com for word pronunciation.

    The selection popover plays single-word pronunciation directly from
    Youdao's free dictvoice mp3 (browser speechSynthesis sounds robotic).
    That is a cross-origin media load, so the reader CSP must explicitly
    allow the origin or playback is blocked (fallback would silently degrade
    every word back to synthetic speech).
    """
    with _set_html_desired(cw_config, "'self' 'unsafe-inline' 'unsafe-eval'"):
        resp = make_response_headers("web.read_book")

    csp = resp.headers.get("Content-Security-Policy")
    assert csp, "reader page must set a Content-Security-Policy"

    media_directive = [d.strip() for d in csp.split(";") if d.strip().startswith("media-src")]
    assert media_directive, (
        "reader page CSP must explicitly set media-src; CSP was: " + csp
    )
    assert "https://dict.youdao.com" in media_directive[0], (
        "media-src must allow https://dict.youdao.com for word audio; "
        "directive was: " + media_directive[0]
    )


def test_reader_page_allows_ted_audio_minio_origin(app, make_response_headers):
    """Reader must allow media-src the MinIO public origin for TED audio (R210: 双入口并列).

    TED-type books (R172 "原声伴听") play one continuous native recording whose
    URL moon-well returns as a MinIO *public* HTTPS direct link, e.g.
    https://home.haoshenqi.top:9001/magicbook/ted-audio/<slug>.aac. The browser
    loads that cross-origin media directly (it is not proxied through magicbook),
    so the reader CSP must explicitly allow that origin; otherwise playback is
    blocked with "Loading media from '...' violates ... media-src" and the book
    stays silent (R181 field retest). Only the reader page needs this — keep the
    surface narrow.
    """
    with _set_html_desired(cw_config, "'self' 'unsafe-inline' 'unsafe-eval'"):
        resp = make_response_headers("web.read_book")

    csp = resp.headers.get("Content-Security-Policy")
    assert csp, "reader page must set a Content-Security-Policy"

    media_directive = [d.strip() for d in csp.split(";") if d.strip().startswith("media-src")]
    assert media_directive, (
        "reader page CSP must explicitly set media-src; CSP was: " + csp
    )
    # R210：MinIO 对外入口由 home:9001 迁到 minio.haoshenqi.top（后端同一份对象，实测
    # Content-Length/ETag 全同）。过渡期两源并列——moon-well 的 minio.public-url 翻转后
    # 只产出新源；旧源待确认无任何响应再产出时，随单独一笔收窄一并从本断言里删掉。
    for origin in ("https://minio.haoshenqi.top", "https://home.haoshenqi.top:9001"):
        assert origin in media_directive[0], (
            "media-src must allow the MinIO public origin " + origin +
            " for TED native audio; directive was: " + media_directive[0]
        )


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

# R210：MinIO 对外入口迁移 home:9001 → minio.haoshenqi.top，过渡期两源并列。
MINIO_NEW_ORIGIN = "https://minio.haoshenqi.top"
MINIO_LEGACY_ORIGIN = "https://home.haoshenqi.top:9001"
MINIO_ORIGINS = (MINIO_NEW_ORIGIN, MINIO_LEGACY_ORIGIN)


def _img_directive(csp):
    return [d.strip() for d in csp.split(";") if d.strip().startswith("img-src")]


@pytest.mark.parametrize("endpoint", ["web.read_book", "web.buddy_page"])
def test_img_src_stays_same_origin_after_buddy_proxy(app, make_response_headers, endpoint):
    """伙伴头像改走同源代理 /ajax/buddy/image（R220），img-src 不再放行 MinIO。

    R220 验收现场：个别浏览器扩展拦跨站图片子资源（ERR_BLOCKED_BY_CLIENT），
    MinIO 直链在页内全裂图且 CSP 无报错。头像改走本站同源代理后，img-src 收窄，
    媒体面（media-src）仍按阅读页口径放行 MinIO——MINIO_PUBLIC_ORIGINS 继续单点共用。
    """
    with _set_html_desired(cw_config, "'self' 'unsafe-inline' 'unsafe-eval'"):
        resp = make_response_headers(endpoint)

    img = _img_directive(resp.headers.get("Content-Security-Policy"))
    assert img, "img-src must stay explicit; CSP was: " + resp.headers.get("Content-Security-Policy")
    for origin in MINIO_ORIGINS:
        assert origin not in img[0], (
            "%s img-src must NOT re-open MinIO origins after the buddy proxy; got: %s"
            % (endpoint, img[0])
        )


def test_buddy_image_origin_not_opened_for_non_html(app, make_response_headers):
    """非 HTML 响应维持 img-src 'self' … data:，不放行 MinIO（代理后全站同口径）。"""
    with _set_html_desired(cw_config, "'self' 'unsafe-inline' 'unsafe-eval'"):
        resp = make_response_headers("web.index", accept="application/json")

    img = _img_directive(resp.headers.get("Content-Security-Policy"))
    assert img, "index page must keep an explicit img-src"
    for origin in MINIO_ORIGINS:
        assert origin not in img[0], "non-buddy page leaked %s: %s" % (origin, img[0])


def test_csp_allows_no_unrelated_origin(app, make_response_headers):
    """放行面只能是我们自己的两个入口，不得被顺手放宽成通配。"""
    with _set_html_desired(cw_config, "'self' 'unsafe-inline' 'unsafe-eval'"):
        csp = make_response_headers("web.buddy_page").headers.get("Content-Security-Policy")

    img = _img_directive(csp)[0]
    assert " *" not in img + ";", "img-src 被放宽成通配: " + img
    assert "evil.example.com" not in csp

