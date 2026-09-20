"""Unit tests for the toggleread -> moon-well book bridge (R64/R65).

Covers:
  1. POST /ajax/toggleread still succeeds after bridging (no regression).
  2. Marking a book read triggers _moonwell_book_finished_bridge with read_status=True.
  3. Un-marking (unread) does NOT trigger the bridge.
  4. The bridge worker itself: page-miss -> create -> update FINISHED flow.
  5. The bridge worker reuses an existing moon-well book when page search hits.
  6. Bridge failures never break the main toggleread path.
"""
import json
from unittest.mock import patch, MagicMock

import pytest


@pytest.fixture
def moonwell_configured(monkeypatch):
    from cps import constants
    monkeypatch.setattr(constants, "MOON_WELL_READING_URL",
                        "https://moon-well.example.com/")
    return constants



def _run_bridge_sync(web_mod, monkeypatch, fn_name="_moonwell_book_finished_bridge", *args, **kwargs):
    """桥接用 Thread 启动 worker；测试里 patch Thread 为立即执行，保证确定性。"""
    import threading as _t
    original = _t.Thread
    def fake_thread(target=None, name=None, daemon=None):
        class Immediate:
            def start(self):
                target()
        return Immediate()
    monkeypatch.setattr(web_mod.threading, "Thread", fake_thread)
    getattr(web_mod, fn_name)(*args, **kwargs)

def test_toggle_read_still_ok(admin_client, moonwell_configured):
    """桥接加入后 toggleread 主链路无回归。"""
    rv = admin_client.post("/ajax/toggleread/1", headers={"X-Requested-With": "XMLHttpRequest"})
    assert rv.status_code == 200


def test_mark_read_triggers_bridge(admin_client, monkeypatch, moonwell_configured):
    """置已读必须调桥接且 read_status=True。"""
    from cps import web as web_mod
    import threading as _t
    def fake_thread(target=None, name=None, daemon=None):
        class Immediate:
            def start(self):
                target()
        return Immediate()
    monkeypatch.setattr(web_mod.threading, "Thread", fake_thread)
    # 确保从已读状态开始 toggling 到未读，再测置已读触发
    admin_client.post("/ajax/toggleread/1", headers={"X-Requested-With": "XMLHttpRequest"})
    with patch("cps.web._moonwell_book_finished_bridge") as mock_bridge:
        admin_client.post("/ajax/toggleread/1", headers={"X-Requested-With": "XMLHttpRequest"})
        mock_bridge.assert_called_once()
        args, _ = mock_bridge.call_args
        assert args[0] == 1
        assert args[1] is True


def test_unmark_read_does_not_bridge(admin_client, moonwell_configured):
    """取消已读不触发桥接（成就不回退语义）。"""
    with patch("cps.web._moonwell_book_finished_bridge") as mock_bridge:
        # 预置：把 book 1 置为已读（bridge mock 掉，不影响状态）
        admin_client.post("/ajax/toggleread/1", headers={"X-Requested-With": "XMLHttpRequest"})
        # 当前为已读，toggle 到未读
        admin_client.post("/ajax/toggleread/1", headers={"X-Requested-With": "XMLHttpRequest"})
        # 再 toggle 到已读（应触发）
        admin_client.post("/ajax/toggleread/1", headers={"X-Requested-With": "XMLHttpRequest"})
        calls = mock_bridge.call_args_list
        # 只有第三次 toggle（置已读）触发
        assert len(calls) == 1
        assert calls[0].args[1] is True


def test_bridge_worker_create_then_update(moonwell_configured, app, monkeypatch):
    monkeypatch.setattr("cps.web._moonwell_identity_headers",
                        lambda: {"X-User-Subject": "test-user"})
    """page 未命中 -> create 登记 -> update 置 FINISHED 的完整流程。"""
    from cps import web as web_mod

    responses = [
        # page: miss
        (json.dumps({"success": True, "result": {"records": []}}), 200, {}),
        # create: ok
        (json.dumps({"success": True, "result": {"id": "42"}}), 200, {}),
        # update: ok
        (json.dumps({"success": True, "result": {}}), 200, {}),
    ]
    calls = []

    def fake_proxy(path, payload, timeout, label, **kwargs):
        calls.append((path, payload))
        return responses.pop(0)

    with patch.object(web_mod, "_moonwell_proxy", side_effect=fake_proxy):
        with app.app_context():
            _run_bridge_sync(web_mod, monkeypatch, "_moonwell_book_finished_bridge",
                             89, True, title="魔法书使用指南", authors="Magicbook 家族团队")

    paths = [c[0] for c in calls]
    assert paths == ["/book/page", "/book/create", "/book/update"], paths
    assert calls[1][1]["title"] == "魔法书使用指南"
    assert calls[2][1]["id"] == "42"
    assert calls[2][1]["readingStatus"] == "FINISHED"


def test_bridge_worker_reuses_existing_book(moonwell_configured, app, monkeypatch):
    monkeypatch.setattr("cps.web._moonwell_identity_headers",
                        lambda: {"X-User-Subject": "test-user"})
    """page 命中同名书 -> 直接 update，不重复登记。"""
    from cps import web as web_mod

    responses = [
        (json.dumps({"success": True, "result": {"records": [
            {"id": 7, "title": "魔法书使用指南"}]}}), 200, {}),
        (json.dumps({"success": True, "result": {}}), 200, {}),
    ]
    calls = []

    def fake_proxy(path, payload, timeout, label, **kwargs):
        calls.append((path, payload))
        return responses.pop(0)

    with patch.object(web_mod, "_moonwell_proxy", side_effect=fake_proxy):
        with app.app_context():
            _run_bridge_sync(web_mod, monkeypatch, "_moonwell_book_finished_bridge",
                             89, True, title="魔法书使用指南", authors="Magicbook 家族团队")

    paths = [c[0] for c in calls]
    assert paths == ["/book/page", "/book/update"], paths
    assert calls[1][1]["id"] == "7"


def test_bridge_worker_failure_is_silent(moonwell_configured, app, monkeypatch):
    monkeypatch.setattr("cps.web._moonwell_identity_headers",
                        lambda: {"X-User-Subject": "test-user"})
    """桥接全程失败只记日志，不抛异常。"""
    from cps import web as web_mod

    with patch.object(web_mod, "_moonwell_proxy",
                      side_effect=Exception("moon-well exploded")):
        with app.app_context():
            # 不应抛出
            web_mod._moonwell_book_finished_bridge(89, True, title="魔法书使用指南",
                                                   authors="Magicbook")


def test_bridge_skips_when_not_read(moonwell_configured, app, monkeypatch):
    """read_status=False 直接返回，不发任何请求。"""
    from cps import web as web_mod

    with patch.object(web_mod, "_moonwell_proxy") as mock_proxy:
        web_mod._moonwell_book_finished_bridge(89, False, title="t")
        mock_proxy.assert_not_called()
