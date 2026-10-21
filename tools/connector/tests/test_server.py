import json
import os
import types

import pytest

import server
from mapping import Mapping


@pytest.fixture
def env(tmp_path, monkeypatch):
    monkeypatch.setattr(server, "HOOK_TOKEN", "test-token")
    monkeypatch.setattr(server, "BOOK_IMPORT_KEY", "import-key")
    monkeypatch.setattr(server, "BARK_KEY", "")
    monkeypatch.setattr(server, "DATA_DIR", str(tmp_path))
    monkeypatch.setattr(server, "STATE_PATH", str(tmp_path / "state.json"))
    monkeypatch.setattr(server, "OUT_DIR", str(tmp_path / "out"))
    mapping_file = tmp_path / "mapping.yaml"
    mapping_file.write_text(
        "books:\n  - slug: guide\n    book_id: 89\n    title: Guide\n")
    monkeypatch.setattr(server, "mapping", Mapping(str(mapping_file)))
    monkeypatch.setattr(server, "notify", lambda *a, **k: None)
    return types.SimpleNamespace(client=server.app.test_client(),
                                 data_dir=str(tmp_path))


def post_event(env, body, token="test-token"):
    return env.client.post("/hooks/halo", json=body,
                           headers={"X-Hook-Token": token})


def read_state(env):
    with open(os.path.join(env.data_dir, "state.json"), encoding="utf-8") as f:
        return json.load(f)


class FakeHalo:
    md = "# Ch1\n\nHello."

    def __init__(self, base):
        pass

    def find_post(self, slug):
        return {"name": "n1", "title": "Guide", "slug": slug, "cover": ""}

    def get_markdown(self, name):
        return self.md

    def download(self, url):
        return b"img"


def test_rejects_wrong_or_missing_token(env):
    assert post_event(env, {"eventType": "NEW_POST"}, token="nope"
                      ).status_code == 401
    assert post_event(env, {"eventType": "NEW_POST"}, token=""
                      ).status_code == 401


def test_fail_closed_when_token_unset(env, monkeypatch):
    monkeypatch.setattr(server, "HOOK_TOKEN", "")
    assert post_event(env, {"eventType": "NEW_POST"}).status_code == 401


def test_ignores_other_events_and_unmapped_slugs(env):
    r = post_event(env, {"eventType": "NEW_COMMENT", "data": {}})
    assert r.status_code == 200 and r.get_json()["result"] == "ignored"
    r = post_event(env, {"eventType": "NEW_POST",
                         "data": {"slug": "other-post"}})
    assert r.status_code == 200 and r.get_json()["result"] == "no-mapping"


def test_full_pipeline_and_debounce(env, monkeypatch):
    imported = []

    class RecordingMB:
        def __init__(self, *a, **k):
            pass

        def import_book(self, book_id, path, **kw):
            assert os.path.exists(path)  # EPUB 已真实落盘
            imported.append((book_id, path, kw))
            return {"bookId": book_id, "translationJobId": 77}

    monkeypatch.setattr(server, "HaloClient", FakeHalo)
    monkeypatch.setattr(server, "MagicbookClient", RecordingMB)

    event = {"eventType": "NEW_POST", "data": {"slug": "guide"}}
    r = post_event(env, event)
    assert r.status_code == 200 and r.get_json()["result"] == "imported"
    assert imported[0][0] == 89
    assert imported[0][2]["trigger_translation"] is True
    assert read_state(env)["guide"]["last_job_id"] == 77

    # 同内容重复事件 → no-op（防抖）
    r = post_event(env, event)
    assert r.get_json()["result"] == "no-op"
    assert len(imported) == 1

    # 内容变化 → 再次导入
    monkeypatch.setattr(FakeHalo, "md", "# Ch1\n\nHello again.")
    r = post_event(env, event)
    assert r.get_json()["result"] == "imported"
    assert len(imported) == 2


def test_translation_502_marks_state_and_degrades(env, monkeypatch):
    from magicbook_client import MagicbookError

    class FakeMB:
        def __init__(self, *a, **k):
            pass

        def import_book(self, book_id, path, **kw):
            raise MagicbookError("translation failed", status=502,
                                 payload={"bookId": 89})

    monkeypatch.setattr(server, "HaloClient", FakeHalo)
    monkeypatch.setattr(server, "MagicbookClient", FakeMB)
    r = post_event(env, {"eventType": "NEW_POST", "data": {"slug": "guide"}})
    assert r.status_code == 200
    assert r.get_json()["result"] == "imported-translation-failed"
    assert "translation_error" in read_state(env)["guide"]


# ---------- R195：state.json 读写必须在全局锁内（gunicorn --threads 4） ----------

def test_state_updates_are_serialized_across_slugs(env, monkeypatch):
    """并发写不同 slug 时不得互相覆盖（旧实现整份读-改-写、无全局锁）。"""
    import threading
    import time

    real_load = server._load_state

    def slow_load():
        data = real_load()
        time.sleep(0.02)  # 放大读-写窗口：无锁时后写者会覆盖前者
        return data

    monkeypatch.setattr(server, "_load_state", slow_load)

    threads = [threading.Thread(target=server._state_update,
                                kwargs={"slug": "s%d" % i, "last_sha": "sha%d" % i})
               for i in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    state = read_state(env)
    assert sorted(state) == ["s0", "s1", "s2", "s3", "s4"]
    assert state["s4"]["last_sha"] == "sha4"


def test_state_update_removes_translation_error(env, monkeypatch):
    monkeypatch.setattr(server, "HaloClient", FakeHalo)
    monkeypatch.setattr(server, "MagicbookClient", lambda *a, **k: types.SimpleNamespace(
        import_book=lambda *a, **k: {"bookId": 89, "translationJobId": 9}))
    server._state_update("guide", translation_error="old failure")
    post_event(env, {"eventType": "NEW_POST", "data": {"slug": "guide"}})
    assert "translation_error" not in read_state(env)["guide"]


# ---------- R196：事件白名单（修订/重新发布也要进书） ----------

def test_update_post_event_is_processed(env, monkeypatch):
    imported = []
    monkeypatch.setattr(server, "HaloClient", FakeHalo)
    monkeypatch.setattr(server, "MagicbookClient", lambda *a, **k: types.SimpleNamespace(
        import_book=lambda book_id, path, **kw: imported.append(book_id) or
        {"bookId": book_id, "translationJobId": None}))

    r = post_event(env, {"eventType": "UPDATE_POST", "data": {"slug": "guide"}})
    assert r.status_code == 200
    assert r.get_json()["result"] == "imported"
    assert imported == [89]


def test_events_can_be_overridden_by_env(env, monkeypatch):
    monkeypatch.setenv("CONNECTOR_EVENTS", "NEW_POST")
    r = post_event(env, {"eventType": "UPDATE_POST", "data": {"slug": "guide"}})
    assert r.get_json()["result"] == "ignored"


def test_delete_events_stay_ignored(env, monkeypatch):
    r = post_event(env, {"eventType": "DELETE_POST", "data": {"slug": "guide"}})
    assert r.get_json()["result"] == "ignored"


# ---------- R197：/resync 手动补账 ----------

def _stub_import(monkeypatch):
    imported = []

    class MB:
        def __init__(self, *a, **k):
            pass

        def import_book(self, book_id, path, **kw):
            imported.append(book_id)
            return {"bookId": book_id, "translationJobId": None}

    monkeypatch.setattr(server, "HaloClient", FakeHalo)
    monkeypatch.setattr(server, "MagicbookClient", MB)
    return imported


def resync(env, body=None, token="test-token"):
    return env.client.post("/resync", json=body or {},
                           headers={"X-Hook-Token": token})


def test_resync_requires_token(env):
    assert resync(env, token="nope").status_code == 401
    assert resync(env, token="").status_code == 401


def test_resync_full_run_then_idempotent(env, monkeypatch):
    imported = _stub_import(monkeypatch)

    r = resync(env)
    assert r.status_code == 200
    body = r.get_json()
    assert body["total"] == 1 and body["imported"] == 1 and body["failed"] == 0
    assert body["results"][0]["slug"] == "guide"
    assert imported == [89]

    # 第二次：sha 未变 → 全 no-op，不再打 magicbook
    r = resync(env)
    body = r.get_json()
    assert body["imported"] == 0
    assert body["results"][0]["result"] == "no-op"
    assert imported == [89]


def test_resync_reports_unknown_slug_without_failing(env, monkeypatch):
    _stub_import(monkeypatch)
    r = resync(env, {"slugs": ["guide", "not-mapped"]})
    body = r.get_json()
    assert r.status_code == 200
    assert body["total"] == 2 and body["imported"] == 1
    results = {x["slug"]: x for x in body["results"]}
    assert results["not-mapped"]["result"] == "no-mapping"


def test_resync_keeps_going_when_one_slug_fails(env, monkeypatch):
    class BoomHalo(FakeHalo):
        def find_post(self, slug):
            if slug == "bad":
                raise server.HaloError("boom")
            return super().find_post(slug)

    monkeypatch.setattr(server, "HaloClient", BoomHalo)
    monkeypatch.setattr(server, "MagicbookClient", lambda *a, **k: types.SimpleNamespace(
        import_book=lambda book_id, path, **kw: {"bookId": book_id, "translationJobId": None}))
    mapping_file = os.path.join(env.data_dir, "mapping2.yaml")
    with open(mapping_file, "w", encoding="utf-8") as f:
        f.write("books:\n  - slug: bad\n    book_id: 90\n  - slug: guide\n    book_id: 89\n")
    server.mapping = Mapping(mapping_file)

    body = resync(env).get_json()
    results = {x["slug"]: x for x in body["results"]}
    assert body["failed"] == 1
    assert "boom" in results["bad"]["error"]
    assert results["guide"]["result"] == "imported"
