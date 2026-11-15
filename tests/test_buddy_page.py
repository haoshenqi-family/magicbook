"""R206 伙伴页服务端渲染冒烟：只验模板能出页面，不验 JS 行为。

Why: /buddy 由前端异步拉 catalog，既有全量用例一个都不覆盖它；本仓 layout.html 的
     渲染错误会让所有 extends layout 的页面一起 500，必须有断言站住这条路。
"""

from pathlib import Path

import pytest


def test_buddy_page_renders(admin_client):
    rv = admin_client.get("/buddy")
    assert rv.status_code == 200
    body = rv.data.decode("utf-8")
    assert 'id="buddy-roster"' in body
    assert 'id="buddy-csrf"' in body


def test_buddy_nav_entry_present_once(admin_client):
    body = admin_client.get("/buddy").data.decode("utf-8")
    assert body.count('id="account-buddy"') == 1
    assert 'id="account-buddy"\n           class="mb-l2-link active"' in body
    assert 'id="buddy-open-chat"' in body
    assert "window.AICompanion.openChat" in (
        Path(__file__).resolve().parents[1] / "cps/static/js/buddy.js"
    ).read_text(encoding="utf-8")


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


@pytest.fixture
def moonwell_quick_actions(monkeypatch):
    """R294：quick-actions 真值在 moon-well——测试内建内存真值源（stored=None=从未保存），
    验薄代理/懒迁移/读回；归一口径（白名单/钉首/数量）模拟 moon-well R260 侧。"""
    import json as _json
    import cps.web as w

    WHITELIST = {"chat", "immersive-translate", "tts-book", "bookmark",
                 "learning", "library", "me", "highlight", "page-translate", "review"}
    state = {"stored": None}

    def fake_proxy(path, payload, timeout, label, binary=False, method="POST",
                   system_identity=False, bearer_token=None):
        if path == "/buddy/quick-actions":
            if state["stored"] is None:
                return (_json.dumps({"success": True, "result": {
                    "selected": ["chat", "immersive-translate", "tts-book", "bookmark"],
                    "stored": False}}), 200, {"Content-Type": "application/json"})
            return (_json.dumps({"success": True, "result": {
                "selected": list(state["stored"]), "stored": True}}), 200,
                {"Content-Type": "application/json"})
        if path == "/buddy/quick-actions/save":
            selected = (payload or {}).get("selected") or []
            if (any(a not in WHITELIST for a in selected)
                    or len(set(selected)) != len(selected)):
                return (_json.dumps({"success": False, "message": "invalid quick actions"}), 500,
                        {"Content-Type": "application/json"})
            ordered = ["chat"] + [a for a in selected if a != "chat"]
            if not 4 <= len(ordered) <= 5:
                return (_json.dumps({"success": False, "message": "invalid quick actions"}), 500,
                        {"Content-Type": "application/json"})
            state["stored"] = ordered
            return (_json.dumps({"success": True, "result": {
                "selected": ordered, "stored": True}}), 200, {"Content-Type": "application/json"})
        raise AssertionError("unexpected moonwell path: %s" % path)

    monkeypatch.setattr(w._moonwell_client, "proxy", fake_proxy)
    return state


@pytest.fixture
def moonwell_down(monkeypatch):
    """moon-well 不可用（503）：GET 走本地 view_settings 兜底、POST 透 502。"""
    import cps.web as w

    def fake_proxy(path, payload, timeout, label, binary=False, method="POST",
                   system_identity=False, bearer_token=None):
        return ({"success": False, "message": "service unavailable"}, 503,
                {"Content-Type": "application/json"})

    monkeypatch.setattr(w._moonwell_client, "proxy", fake_proxy)


def test_quick_actions_get_returns_catalog_and_defaults(admin_client, moonwell_quick_actions):
    """R294：GET 返回动作全集（10 项，含扩展专有三项 ext_only=True）与默认四项；label
    必须非空——gettext 依赖请求上下文，导入期冻结的 label 只会回吐英文 msgid。
    moon-well 未保存（stored=False）且本地无存量 → 回落默认四项、stored=False。"""
    rv = admin_client.get("/ajax/buddy/quick-actions")
    assert rv.status_code == 200
    result = rv.get_json()["result"]
    by_id = {a["id"]: a for a in result["available"]}
    assert set(by_id) == {"chat", "immersive-translate", "tts-book", "bookmark",
                          "learning", "library", "me",
                          "highlight", "page-translate", "review"}
    assert all(a["label"] for a in by_id.values())
    assert by_id["highlight"]["ext_only"] is True
    assert by_id["page-translate"]["ext_only"] is True
    assert by_id["review"]["ext_only"] is True
    assert by_id["chat"]["ext_only"] is False
    assert result["selected"] == ["chat", "immersive-translate", "tts-book", "bookmark"]
    assert result["stored"] is False


def test_quick_actions_post_persists_selection(admin_client, moonwell_quick_actions):
    """合法选择（含 chat、4-5 个）写入 moon-well 真值源并在 GET 读回；本地 view_settings
    同步覆写为热兜底（R294：moon-well 不可用时 GET 的回退源）。"""
    from cps import ub
    chosen = ["chat", "learning", "library", "me"]
    rv = admin_client.post("/ajax/buddy/quick-actions", json={"selected": chosen})
    assert rv.status_code == 200
    assert rv.get_json()["result"]["selected"] == chosen
    assert rv.get_json()["result"]["stored"] is True
    rv = admin_client.get("/ajax/buddy/quick-actions")
    assert rv.get_json()["result"]["selected"] == chosen
    assert rv.get_json()["result"]["stored"] is True
    admin = ub.session.query(ub.User).filter(ub.User.name == "admin").first()
    assert admin.view_settings["buddy"]["quickActions"] == chosen


def test_quick_actions_post_persists_extension_ids(admin_client, moonwell_quick_actions):
    """R294：扩展专有三项与宿主项混选合法（moon-well R260 白名单）；宿主球渲染时会
    跳过不认识的 id，配置面照常持久化。"""
    chosen = ["chat", "highlight", "page-translate", "review"]
    rv = admin_client.post("/ajax/buddy/quick-actions", json={"selected": chosen})
    assert rv.status_code == 200
    assert rv.get_json()["result"]["selected"] == chosen
    assert (admin_client.get("/ajax/buddy/quick-actions").get_json()["result"]["selected"]
            == chosen)


def test_quick_actions_post_validates(admin_client, moonwell_quick_actions):
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


def test_quick_actions_post_pins_chat_first(admin_client, moonwell_quick_actions):
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


def test_quick_actions_post_rejects_over_max_counting_pinned_chat(admin_client, moonwell_quick_actions):
    """数量口径连 chat 一起算：5 个非 chat 动作＝6 个，400 且不落库（不静默截断用户选择）。"""
    before = admin_client.get("/ajax/buddy/quick-actions").get_json()["result"]["selected"]
    rv = admin_client.post("/ajax/buddy/quick-actions",
                           json={"selected": ["immersive-translate", "tts-book", "bookmark",
                                              "learning", "library"]})
    assert rv.status_code == 400
    after = admin_client.get("/ajax/buddy/quick-actions").get_json()["result"]["selected"]
    assert after == before


def test_quick_actions_get_migrates_legacy_to_moonwell(admin_client, moonwell_quick_actions,
                                                       ub_session):
    """R294 存量懒迁移：moon-well 从未保存（stored=False）而 view_settings 有真实存量
    选择 → GET 代用户回填一次，返回迁移结果且 moon-well 真值源就位（幂等自愈，
    存量用户不丢配置）。恰好存过默认四项也算保存行为，照迁。"""
    from cps import ub
    admin = ub_session.query(ub.User).filter(ub.User.name == "admin").first()
    admin.set_view_property("buddy", "quickActions", ["chat", "learning", "library", "me"])
    rv = admin_client.get("/ajax/buddy/quick-actions")
    result = rv.get_json()["result"]
    assert result["selected"] == ["chat", "learning", "library", "me"]
    assert result["stored"] is True
    assert moonwell_quick_actions["stored"] == ["chat", "learning", "library", "me"]
    # 二次 GET 直读 moon-well，不再走迁移分支
    rv = admin_client.get("/ajax/buddy/quick-actions")
    assert rv.get_json()["result"]["stored"] is True


def test_quick_actions_get_falls_back_to_local_when_moonwell_down(
        admin_client, moonwell_down, ub_session):
    """moon-well 不可用：GET 退回本地 view_settings（R234 原归一语义），页面不瘫；
    POST 透出 502 真实原因而非静默假成功。"""
    from cps import ub
    from cps.routes.buddy import QUICK_ACTION_DEFAULTS
    admin = ub_session.query(ub.User).filter(ub.User.name == "admin").first()
    admin.set_view_property("buddy", "quickActions", ["learning", "library", "me", "chat"])
    rv = admin_client.get("/ajax/buddy/quick-actions")
    result = rv.get_json()["result"]
    assert result["selected"] == ["chat", "learning", "library", "me"]
    assert result["stored"] is False
    admin.set_view_property("buddy", "quickActions", ["chat", "ghost-action"])
    result = admin_client.get("/ajax/buddy/quick-actions").get_json()["result"]
    assert result["selected"] == list(QUICK_ACTION_DEFAULTS)
    rv = admin_client.post("/ajax/buddy/quick-actions",
                           json={"selected": ["chat", "learning", "library", "me"]})
    assert rv.status_code == 502
    assert rv.get_json()["success"] is False


def test_quick_actions_read_normalizes_legacy_values(admin_client, moonwell_down, ub_session):
    """R234 读回归一随迁 moon-well 后落在「moon-well 不可用的本地兜底」路径（真值迁移
    见 test_quick_actions_get_migrates_legacy_to_moonwell）：缺 chat / chat 末位 /
    连 chat 超 5 读回时钉首位并截到上限；坏数据回落默认四项。"""
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
