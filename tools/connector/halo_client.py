"""Halo 公开内容 API 客户端（免鉴权）。

事件回调只当触发器，正文一律按 slug 重新拉取最新发布版，防事件乱序覆盖。
"""
import requests


class HaloError(RuntimeError):
    pass


class HaloClient:
    def __init__(self, base_url, timeout=20):
        self.base = base_url.rstrip("/")
        self.timeout = timeout

    def _get(self, path, params=None):
        try:
            resp = requests.get(self.base + path, params=params, timeout=self.timeout)
        except requests.RequestException as exc:
            raise HaloError(f"halo api request failed: {exc}") from exc
        if resp.status_code != 200:
            raise HaloError(f"halo api {resp.status_code} for {path}")
        return resp.json()

    def find_post(self, slug):
        """按 spec.slug 翻页查找文章，返回 {name, title, slug, cover}。"""
        page = 1
        while page <= 50:
            data = self._get("/apis/api.content.halo.run/v1alpha1/posts",
                             params={"page": page, "size": 100})
            for item in data.get("items") or []:
                if (item.get("spec") or {}).get("slug") == slug:
                    return {
                        "name": item["metadata"]["name"],
                        "title": item["spec"]["title"],
                        "slug": slug,
                        "cover": item["spec"].get("cover") or "",
                    }
            if page * 100 >= (data.get("total") or 0):
                break
            page += 1
        raise HaloError(f"post with slug={slug!r} not found (or not published)")

    def get_markdown(self, name):
        data = self._get(f"/apis/api.content.halo.run/v1alpha1/posts/{name}")
        content = (data.get("content") or {}).get("raw")
        if not content:
            raise HaloError(f"post {name} has empty raw content")
        return content

    def download(self, url):
        if url.startswith("/"):
            url = self.base + url
        try:
            resp = requests.get(url, timeout=self.timeout)
            resp.raise_for_status()
        except requests.RequestException as exc:
            raise HaloError(f"download failed {url}: {exc}") from exc
        return resp.content
