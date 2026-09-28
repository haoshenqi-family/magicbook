# -*- coding: utf-8 -*-
"""R88: metadata provider 出口路由（仅谷歌走代理）与超时强制。

背景（R87）：内网无法直连 Google，裸 requests.get 无超时曾把元数据搜索的
执行线程永久挂起，进而拖死 Tornado 事件循环，整站假死。这里的测试保证：

1. 域名路由：googleapis.com / books.google.com / scholar.google.com 等
   谷歌域名走 METADATA_GOOGLE_PROXY，其余域名显式直连；
2. 超时不可绕过：outbound 层 timeout=None 会被重置为默认值；
3. /metadata/search 视图有整体等待上限：单个 provider 卡死不再拖死全站。
"""
import dataclasses
import time

import pytest

from cps.metadata_provider import outbound


class TestDomainRouting:
    def test_google_hosts(self):
        for url in (
            "https://www.googleapis.com/books/v1/volumes?q=x",
            "https://books.google.com/books?id=1",
            "https://scholar.google.com/scholar?q=x",
            "https://accounts.google.com/o/oauth2/auth",
        ):
            assert outbound.is_google_url(url), url

    def test_non_google_hosts(self):
        for url in (
            "https://www.douban.com/search?q=x",
            "https://www.amazon.com/s?k=x",
            "https://comicvine.gamespot.com/api/search?api_key=x",
            "https://lubimyczytac.pl/szukaj/ksiazki?q=x",
            "https://notgoogle.com/",  # 后缀必须完整匹配，不能是子串
        ):
            assert not outbound.is_google_url(url), url

    def test_google_url_uses_proxy_when_configured(self, monkeypatch):
        proxy = "http://192.168.31.11:12811"
        monkeypatch.setenv(outbound.GOOGLE_PROXY_ENV, proxy)
        proxies = outbound._proxies_for("https://www.googleapis.com/x")
        assert proxies == {"http": proxy, "https": proxy}

    def test_google_url_direct_when_unset(self, monkeypatch):
        monkeypatch.delenv(outbound.GOOGLE_PROXY_ENV, raising=False)
        assert outbound._proxies_for(
            "https://www.googleapis.com/x") == outbound.DIRECT_PROXIES

    def test_non_google_always_direct_even_if_env_leaked(self, monkeypatch):
        # 为什么必须有这条：容器里若泄漏了 http_proxy/https_proxy 环境变量，
        # requests 默认会信任它；非谷歌域名必须被显式钉死为直连。
        monkeypatch.setenv(outbound.GOOGLE_PROXY_ENV, "http://192.168.31.11:12811")
        monkeypatch.setenv("http_proxy", "http://192.168.31.11:12811")
        monkeypatch.setenv("https_proxy", "http://192.168.31.11:12811")
        assert outbound._proxies_for(
            "https://www.douban.com/search") == outbound.DIRECT_PROXIES


class TestTimeoutEnforced:
    def test_request_passes_timeout_and_proxies(self, monkeypatch):
        captured = {}

        def fake_request(method, url, timeout=None, proxies=None, **kw):
            captured.update(method=method, url=url, timeout=timeout,
                            proxies=proxies)

            class R:
                status_code = 200

            return R()

        monkeypatch.setattr(outbound.requests, "request", fake_request)
        monkeypatch.setenv(outbound.GOOGLE_PROXY_ENV, "http://192.168.31.11:12811")
        outbound.get("https://www.googleapis.com/x", timeout=(5, 20))
        assert captured["timeout"] == (5, 20)
        assert captured["proxies"] == {
            "http": "http://192.168.31.11:12811",
            "https": "http://192.168.31.11:12811",
        }
        outbound.get("https://www.douban.com/search")
        assert captured["proxies"] == outbound.DIRECT_PROXIES
        assert captured["timeout"] == outbound.DEFAULT_TIMEOUT

    def test_none_timeout_is_reset_to_default(self, monkeypatch):
        # 回归护栏：谁传 timeout=None 都不允许重新打开 R87 的无界等待窗口。
        captured = {}

        def fake_request(method, url, timeout=None, proxies=None, **kw):
            captured["timeout"] = timeout

            class R:
                status_code = 200

            return R()

        monkeypatch.setattr(outbound.requests, "request", fake_request)
        outbound.get("https://www.douban.com/x", timeout=None)
        assert captured["timeout"] == outbound.DEFAULT_TIMEOUT


class TestGoogleBooksProvider:
    def test_search_uses_outbound_with_timeout(self, monkeypatch):
        from cps.metadata_provider.google import Google

        captured = {}

        def fake_get(url, timeout=None, **kw):
            captured["url"] = url
            captured["timeout"] = timeout

            class R:
                status_code = 200

                def raise_for_status(self):
                    pass

                def json(self):
                    return {"items": []}

            return R()

        monkeypatch.setattr(outbound, "get", fake_get)
        result = Google().search("dummy query")
        assert result == []
        assert captured["url"].startswith(Google.SEARCH_URL)
        assert captured["timeout"] == (5, 20)

    def test_search_returns_empty_on_error(self, monkeypatch):
        from cps.metadata_provider.google import Google

        def boom(url, timeout=None, **kw):
            raise TimeoutError("connect timed out")

        monkeypatch.setattr(outbound, "get", boom)
        assert Google().search("dummy query") == []


@dataclasses.dataclass
class _Rec:
    name: str


class _FastProvider:
    __id__ = "fast"

    def __init__(self):
        self.active = True

    def search(self, query, generic_cover="", locale="en"):
        return [_Rec(name="fast-result")]


class _HangingProvider:
    __id__ = "hanging"

    def __init__(self):
        self.active = True

    def search(self, query, generic_cover="", locale="en"):
        # 模拟 R87：外呼永不返回（但用可退出的循环避免测试进程被拖住）
        deadline = time.time() + 15
        while time.time() < deadline:
            time.sleep(0.1)
        return []


class TestSearchViewBounded:
    def test_hanging_provider_cannot_block_view(self, monkeypatch, admin_client):
        """R87 回归：单个 provider 卡死时，视图必须在等待上限内返回，
        且已完成 provider 的结果照常返回。"""
        from cps import search_metadata as sm

        monkeypatch.setattr(sm, "cl", [_FastProvider(), _HangingProvider()])
        monkeypatch.setenv("METADATA_SEARCH_TIMEOUT", "1")

        start = time.time()
        rv = admin_client.post("/metadata/search", data={"query": "x"})
        elapsed = time.time() - start

        assert rv.status_code == 200
        assert rv.get_json() == [{"name": "fast-result"}]
        assert elapsed < 10, "视图仍被卡死的 provider 无界阻塞"

    def test_bad_timeout_env_falls_back(self, monkeypatch, admin_client):
        from cps import search_metadata as sm

        monkeypatch.setattr(sm, "cl", [_FastProvider()])
        monkeypatch.setenv("METADATA_SEARCH_TIMEOUT", "not-a-number")
        rv = admin_client.post("/metadata/search", data={"query": "x"})
        assert rv.status_code == 200
        assert rv.get_json() == [{"name": "fast-result"}]
