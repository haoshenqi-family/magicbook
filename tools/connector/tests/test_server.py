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
