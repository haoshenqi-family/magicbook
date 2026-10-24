"""R206 伙伴页服务端渲染冒烟：只验模板能出页面，不验 JS 行为。

Why: /buddy 由前端异步拉 catalog，既有全量用例一个都不覆盖它；本仓 layout.html 的
     渲染错误会让所有 extends layout 的页面一起 500，必须有断言站住这条路。
"""


def test_buddy_page_renders(admin_client):
    rv = admin_client.get("/buddy")
    assert rv.status_code == 200
    body = rv.data.decode("utf-8")
    assert 'id="buddy-roster"' in body
    assert 'id="buddy-csrf"' in body


def test_buddy_nav_entry_present_once(admin_client):
    body = admin_client.get("/buddy").data.decode("utf-8")
    assert body.count('id="top_buddy"') == 1


def test_buddy_image_proxy_whitelist(admin_client, monkeypatch):
    """R220 头像改走同源代理：白名单外一律 400，前端三处头像已切代理。"""
    import cps.routes.buddy as buddy_routes

    rv = admin_client.get("/ajax/buddy/image?src=https://evil.example.com/x.png")
    assert rv.status_code == 400

    rv = admin_client.get(
        "/ajax/buddy/image?src=https://minio.haoshenqi.top/other-bucket/x.png")
    assert rv.status_code == 400

    class FakeUpstream:
        status_code = 200
        content = b"png-bytes"
        headers = {"Content-Type": "image/png"}

    seen = {}

    def fake_get(url, timeout):
        seen["url"] = url
        return FakeUpstream()

    monkeypatch.setattr(buddy_routes.http_requests, "get", fake_get)
    rv = admin_client.get(
        "/ajax/buddy/image?src=https://minio.haoshenqi.top/magicbook/buddy/hedwig-full.png")
    assert rv.status_code == 200
    assert rv.content_type.startswith("image/png")
    assert rv.data == b"png-bytes"
    assert seen["url"] == "https://minio.haoshenqi.top/magicbook/buddy/hedwig-full.png"
