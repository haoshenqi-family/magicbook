"""R212-B 品牌资产同源代理守卫：白名单、缓存与 fail-loud 三件事不许静默退化。

Why: 代理是「MinIO 单一真源」与「CSP img-src 'self' + 扩展不裂图」之间的唯一桥梁。它若退化成
开放代理（任意 src/任意对象名）就是 SSRF 面；若静默吞掉上游失败把裂图伪装成「本来就没图」，
下一次排查会从「图没了」变成「样式怪」。三条都用形制断言钉住。
"""
import pytest
import requests as http_requests

from cps.routes import brand


class _FakeUpstream:
    def __init__(self, status=200, content=b"FAKEPNG", ctype="image/png"):
        self.status_code = status
        self.content = content
        self.headers = {"Content-Type": ctype}


@pytest.fixture
def clean_cache():
    brand._cache.clear()
    yield
    brand._cache.clear()


def test_whitelist_rejects_non_brand_objects(client, clean_cache, monkeypatch):
    calls = []
    monkeypatch.setattr(brand.http_requests, "get", lambda *a, **k: calls.append(a) or _FakeUpstream())
    # logo.png 在 MinIO 真实存在但不在白名单：代理不得透传白名单外对象
    assert client.get("/brand/logo.png").status_code == 404
    assert client.get("/brand/evil.png").status_code == 404
    assert calls == [], "白名单外的对象名不应触达上游"


def test_serves_bytes_same_origin_with_cache_header(client, clean_cache, monkeypatch):
    monkeypatch.setattr(brand.http_requests, "get", lambda *a, **k: _FakeUpstream())
    resp = client.get("/brand/favicon.png")
    assert resp.status_code == 200
    assert resp.data == b"FAKEPNG"
    assert resp.mimetype == "image/png"
    assert "public, max-age=%d" % brand._TTL in resp.headers["Cache-Control"]


def test_ttl_cache_does_not_refetch_upstream(client, clean_cache, monkeypatch):
    calls = []
    monkeypatch.setattr(brand.http_requests, "get", lambda *a, **k: calls.append(a) or _FakeUpstream())
    client.get("/brand/favicon.png")
    client.get("/brand/favicon.png")
    assert len(calls) == 1, "TTL 内第二次请求不应再打上游"


def test_upstream_failure_is_loud(client, clean_cache, monkeypatch):
    def boom(*a, **k):
        raise http_requests.RequestException("down")
    monkeypatch.setattr(brand.http_requests, "get", boom)
    assert client.get("/brand/favicon.png").status_code == 502

    monkeypatch.setattr(brand.http_requests, "get", lambda *a, **k: _FakeUpstream(status=500))
    brand._cache.clear()
    assert client.get("/brand/favicon.png").status_code == 500
