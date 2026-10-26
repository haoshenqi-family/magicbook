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


def test_quick_actions_get_returns_catalog_and_defaults(admin_client):
    """R223：GET 返回动作全集（chat 固定在列）与默认四项；label 必须非空——
    gettext 依赖请求上下文，导入期冻结的 label 只会回吐英文 msgid。"""
    rv = admin_client.get("/ajax/buddy/quick-actions")
    assert rv.status_code == 200
    result = rv.get_json()["result"]
    by_id = {a["id"]: a for a in result["available"]}
    assert set(by_id) == {"chat", "immersive-translate", "tts-book", "bookmark",
                          "learning", "library", "me"}
    assert all(a["label"] for a in by_id.values())
    assert result["selected"] == ["chat", "immersive-translate", "tts-book", "bookmark"]


def test_quick_actions_post_persists_selection(admin_client):
    """合法选择（含 chat、4-5 个）写入 view_settings 并在 GET 读回。"""
    chosen = ["chat", "learning", "library", "me"]
    rv = admin_client.post("/ajax/buddy/quick-actions", json={"selected": chosen})
    assert rv.status_code == 200
    assert rv.get_json()["result"]["selected"] == chosen
    rv = admin_client.get("/ajax/buddy/quick-actions")
    assert rv.get_json()["result"]["selected"] == chosen


def test_quick_actions_post_validates(admin_client):
    """少于 4 个、含未知动作、重复动作均 400，不落库。"""
    assert admin_client.post("/ajax/buddy/quick-actions",
                             json={"selected": ["chat", "me"]}).status_code == 400
    assert admin_client.post("/ajax/buddy/quick-actions",
                             json={"selected": ["chat", "nonsense", "learning", "me"]}).status_code == 400
    assert admin_client.post("/ajax/buddy/quick-actions",
                             json={"selected": ["chat", "me", "me", "learning"]}).status_code == 400
    # 400 一律不落库：GET 读回的选择与发送前的持久值一致（前面用例可能已写过）。
    before = admin_client.get("/ajax/buddy/quick-actions").get_json()["result"]["selected"]
    admin_client.post("/ajax/buddy/quick-actions",
                      json={"selected": ["chat", "nonsense", "learning", "me"]})
    after = admin_client.get("/ajax/buddy/quick-actions").get_json()["result"]["selected"]
    assert after == before
