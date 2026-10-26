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


def test_quick_actions_post_pins_chat_first(admin_client):
    """R234：「AI 对话恒第一位且不可删」是服务端不变量，不只靠前端约定——
    不带 chat 由服务端补回首位，chat 错位自动前移；以归一后结果落库并在 GET 读回。"""
    rv = admin_client.post("/ajax/buddy/quick-actions",
                           json={"selected": ["learning", "library", "me"]})
    assert rv.status_code == 200
    assert rv.get_json()["result"]["selected"] == ["chat", "learning", "library", "me"]
    assert (admin_client.get("/ajax/buddy/quick-actions").get_json()["result"]["selected"]
            == ["chat", "learning", "library", "me"])

    rv = admin_client.post("/ajax/buddy/quick-actions",
                           json={"selected": ["bookmark", "tts-book", "chat", "me", "library"]})
    assert rv.status_code == 200
    assert rv.get_json()["result"]["selected"] == ["chat", "bookmark", "tts-book", "me", "library"]


def test_quick_actions_post_rejects_over_max_counting_pinned_chat(admin_client):
    """数量口径连 chat 一起算：5 个非 chat 动作＝6 个，400 且不落库（不静默截断用户选择）。"""
    before = admin_client.get("/ajax/buddy/quick-actions").get_json()["result"]["selected"]
    rv = admin_client.post("/ajax/buddy/quick-actions",
                           json={"selected": ["immersive-translate", "tts-book", "bookmark",
                                              "learning", "library"]})
    assert rv.status_code == 400
    after = admin_client.get("/ajax/buddy/quick-actions").get_json()["result"]["selected"]
    assert after == before


def test_quick_actions_read_normalizes_legacy_values(admin_client, ub_session):
    """R223 期服务端不校验 chat，存量 view_settings 可能缺 chat / chat 末位 / 连 chat 超 5：
    读回时钉首位并截到上限，气泡永远 4-5 个且对话在第一位；坏数据回落默认四项。"""
    from cps import ub
    from cps.routes.buddy import QUICK_ACTION_DEFAULTS

    admin = ub_session.query(ub.User).filter(ub.User.name == "admin").first()
    cases = [
        (["learning", "library", "me", "bookmark"],
         ["chat", "learning", "library", "me", "bookmark"]),
        (["learning", "library", "me", "chat"],
         ["chat", "learning", "library", "me"]),
        (["immersive-translate", "tts-book", "bookmark", "learning", "library"],
         ["chat", "immersive-translate", "tts-book", "bookmark", "learning"]),
    ]
    try:
        for legacy, expected in cases:
            admin.set_view_property("buddy", "quickActions", legacy)
            got = admin_client.get("/ajax/buddy/quick-actions").get_json()["result"]["selected"]
            assert got == expected, legacy
        admin.set_view_property("buddy", "quickActions", ["chat", "ghost-action"])
        got = admin_client.get("/ajax/buddy/quick-actions").get_json()["result"]["selected"]
        assert got == list(QUICK_ACTION_DEFAULTS)
    finally:
        admin.set_view_property("buddy", "quickActions", list(QUICK_ACTION_DEFAULTS))
