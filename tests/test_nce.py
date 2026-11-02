"""课级音频播放测试（nce-audio R116③，LLD §4/§9 US1）。

Strategy: 测试环境无 MinIO 亦无 calibre 库——calibre_db 用桩（沿用
test_book_import 范式），store 的 MinIO 读写函数全部 monkeypatch 替换；
映射函数与 Range 解析走真实代码。蓝图在 conftest 无条件注册，
fail-closed 判定（main.py env）不在本文件覆盖范围。
"""
import json
import types

import pytest

from cps.nce.series import resolve_nce_book_no

MANIFEST = {
    "book": 2,
    "generated": "2026-10-04T00:00:00Z",
    "lessons": [
        {"num": "01", "slug": "excuse_me", "title": "Excuse Me",
         "audio": "01-excuse_me.mp3", "lyric": "01-excuse_me.lrc",
         "duration_sec": 61, "size": 3000},
        {"num": "02", "slug": "sit_down", "title": "Sit Down, Please",
         "audio": "02-sit_down.mp3", "lyric": None,
         "duration_sec": 55, "size": 2000},
    ],
}


class FakeObj:
    def __init__(self, data=b"ABCDEFGHIJ" * 300):
        self.data = data

    def stream(self, amt):
        for i in range(0, len(self.data), amt):
            yield self.data[i:i + amt]

    def read(self):
        return self.data

    def close(self):
        pass

    def release_conn(self):
        pass


def _book(series_name="新概念英语", series_index="2.0", book_id=93):
    return types.SimpleNamespace(
        id=book_id, title="新概念英语 2 实践与进步",
        series=[types.SimpleNamespace(name=series_name)],
        series_index=series_index)


@pytest.fixture
def nce_routes(app):
    from cps.nce import routes
    return routes


@pytest.fixture
def stub_db(nce_routes, monkeypatch):
    books = {93: _book(),
             94: _book(series_name="其他系列", book_id=94),
             95: _book(series_index="9.0", book_id=95)}
    stub = types.SimpleNamespace(get_book=lambda bid: books.get(bid))
    monkeypatch.setattr(nce_routes, "calibre_db", stub)
    return books


@pytest.fixture
def stub_store(monkeypatch):
    from cps.nce import store

    def fake_manifest(book_no):
        if book_no == 2:
            return MANIFEST
        raise RuntimeError("minio down")

    monkeypatch.setattr(store, "get_manifest", fake_manifest)
    calls = {}

    def fake_range(book_no, name, start=None, length=None):
        calls["args"] = (book_no, name, start, length)
        data = b"ABCDEFGHIJ" * 300
        if start is not None:
            end = start + (length or len(data))
            return FakeObj(data[start:end])
        return FakeObj(data)

    def fake_text(book_no, name):
        calls["text"] = (book_no, name)
        return "[00:01.00]hello\n"

    monkeypatch.setattr(store, "get_object_range", fake_range)
    monkeypatch.setattr(store, "get_object_text", fake_text)
    return calls


# ---------- 映射纯函数 ----------

def test_resolve_matches_series_and_index():
    assert resolve_nce_book_no(_book()) == 2

def test_resolve_other_series_none():
    assert resolve_nce_book_no(_book(series_name="其他")) is None

def test_resolve_index_out_of_range():
    assert resolve_nce_book_no(_book(series_index="9.0")) is None

def test_resolve_no_series():
    assert resolve_nce_book_no(types.SimpleNamespace(series=[], series_index="1.0")) is None

def test_resolve_bad_index_string():
    assert resolve_nce_book_no(_book(series_index="abc")) is None


# ---------- Range 解析 ----------

def test_parse_range_none_or_absent():
    from cps.nce.routes import _parse_range
    assert _parse_range(None, 1000) is None
    assert _parse_range("bytes=", 1000) is None
    assert _parse_range("garbage", 1000) is None

def test_parse_range_open_end():
    from cps.nce.routes import _parse_range
    assert _parse_range("bytes=100-", 1000) == (100, 999)

def test_parse_range_suffix():
    from cps.nce.routes import _parse_range
    assert _parse_range("bytes=-500", 1000) == (500, 999)

def test_parse_range_exact():
    from cps.nce.routes import _parse_range
    assert _parse_range("bytes=0-99", 1000) == (0, 99)

def test_parse_range_unsatisfiable():
    from cps.nce.routes import _parse_range
    assert _parse_range("bytes=2000-", 1000) == "unsatisfiable"


# ---------- 路由行为 ----------

def test_anonymous_redirected(client, stub_db, stub_store):
    rv = client.get("/nce/93")
    assert rv.status_code == 302
    assert "/login" in rv.headers["Location"]

def test_unknown_book_404(admin_client, stub_db, stub_store):
    assert admin_client.get("/nce/999").status_code == 404

def test_non_nce_book_404(admin_client, stub_db, stub_store):
    assert admin_client.get("/nce/94").status_code == 404
    assert admin_client.get("/nce/94/audio/01").status_code == 404

def test_503_when_manifest_raises(admin_client, stub_db, monkeypatch):
    from cps.nce import store
    def boom(book_no):
        raise RuntimeError("minio down")
    monkeypatch.setattr(store, "get_manifest", boom)
    assert admin_client.get("/nce/93").status_code == 503

def test_player_page_renders_lesson_list(admin_client, stub_db, stub_store):
    rv = admin_client.get("/nce/93")
    assert rv.status_code == 200
    html = rv.get_data(as_text=True)
    assert 'id="nce-list"' in html
    assert "Excuse Me" in html
    assert "02-excuse" not in html  # 列表按 num 精确，不误串

def test_audio_full_stream_200(admin_client, stub_db, stub_store):
    rv = admin_client.get("/nce/93/audio/01")
    assert rv.status_code == 200
    assert rv.headers["Content-Type"] == "audio/mpeg"
    assert rv.headers["Accept-Ranges"] == "bytes"
    assert rv.headers["Content-Length"] == str(MANIFEST["lessons"][0]["size"])
    body = b"".join(rv.iter_encoded())
    assert len(body) == 3000

def test_audio_range_206(admin_client, stub_db, stub_store):
    rv = admin_client.get("/nce/93/audio/01", headers={"Range": "bytes=100-199"})
    assert rv.status_code == 206
    assert rv.headers["Content-Range"] == "bytes 100-199/3000"
    assert rv.headers["Content-Length"] == "100"
    body = rv.get_data()
    assert body == (b"ABCDEFGHIJ" * 300)[100:200]
    assert len(body) == 100

def test_audio_range_416(admin_client, stub_db, stub_store):
    rv = admin_client.get("/nce/93/audio/01", headers={"Range": "bytes=99999-"})
    assert rv.status_code == 416
    assert rv.headers["Content-Range"] == "bytes */3000"

def test_audio_unknown_num_404(admin_client, stub_db, stub_store):
    assert admin_client.get("/nce/93/audio/99").status_code == 404

def test_lessons_json(admin_client, stub_db, stub_store):
    rv = admin_client.get("/nce/93/lessons")
    assert rv.status_code == 200
    data = rv.get_json()
    assert data["book"] == 2
    assert [x["num"] for x in data["lessons"]] == ["01", "02"]

def test_lyric_text(admin_client, stub_db, stub_store):
    rv = admin_client.get("/nce/93/lyric/01")
    assert rv.status_code == 200
    assert "charset=utf-8" in rv.headers["Content-Type"]
    assert rv.get_data(as_text=True) == "[00:01.00]hello\n"

def test_lyric_missing_404(admin_client, stub_db, stub_store):
    assert admin_client.get("/nce/93/lyric/02").status_code == 404
