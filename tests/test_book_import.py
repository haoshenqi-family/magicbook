"""内部书籍导入 API 测试（halo-book-connector R107，LLD §8 magicbook 侧）。

Strategy: 测试环境无真实 calibre 库，calibre_db/config/validate_mime_type 用桩
替换（沿用 test_reading_translation.py 的 monkeypatch 范式）；鉴权与参数校验走
真实路由。cps.book_import 必须在 app 初始化后延迟 import——模块级 import 会经
helper→gdriveutils 触发 cli_param 未初始化的 TypeError（collection 期即崩）。
"""
import io
import os
import types

import pytest

KEY_ENV = "BOOK_IMPORT_KEY"
MAX_MB_ENV = "BOOK_IMPORT_MAX_MB"
URL = "/api/internal/book-import"


@pytest.fixture
def bi(app):
    import cps.book_import as book_import
    return book_import


@pytest.fixture(autouse=True)
def _key(monkeypatch):
    monkeypatch.setenv(KEY_ENV, "s3cret-connector-key")


def _hdr(key="s3cret-connector-key"):
    return {"X-Connector-Key": key} if key else {}


def _epub_part(name="book.epub"):
    return (io.BytesIO(b"fake-epub-bytes"), name, "application/epub+zip")


@pytest.fixture
def stub_library(bi, monkeypatch, tmp_path):
    """桩掉 calibre_db/config/validate_mime_type，EPUB 落盘到 tmp_path。"""
    book = types.SimpleNamespace(id=5, path="Author/Fake Book", title="Fake Book",
                                 last_modified=None)
    session = types.SimpleNamespace(
        add=lambda obj: None,
        merge=lambda obj: None,
        commit=lambda: None)
    stub_db = types.SimpleNamespace(
        get_book=lambda book_id: book if book_id == 5 else None,
        get_book_format=lambda book_id, fmt: types.SimpleNamespace(name="Fake Book"),
        session=session,
        set_metadata_dirty=lambda book_id: None,
        create_functions=lambda cfg: None)
    stub_config = types.SimpleNamespace(get_book_path=lambda: str(tmp_path))
    monkeypatch.setattr(bi, "calibre_db", stub_db)
    monkeypatch.setattr(bi, "config", stub_config)
    monkeypatch.setattr(bi, "validate_mime_type",
                        lambda f, exts: os.path.splitext(f.filename)[1].lstrip(".").lower() in exts)
    bi._locks.pop(5, None)
    return tmp_path, book


def test_disabled_without_env_key_returns_404(client, bi, monkeypatch, stub_library):
    monkeypatch.delenv(KEY_ENV)
    rv = client.post(URL, data={"book_id": "5", "file": _epub_part()},
                     content_type="multipart/form-data", headers=_hdr())
    assert rv.status_code == 404


def test_wrong_key_returns_401(client, stub_library):
    rv = client.post(URL, data={"book_id": "5", "file": _epub_part()},
                     content_type="multipart/form-data", headers=_hdr("wrong"))
    assert rv.status_code == 401


def test_missing_key_returns_401(client, stub_library):
    rv = client.post(URL, data={"book_id": "5", "file": _epub_part()},
                     content_type="multipart/form-data")
    assert rv.status_code == 401


def test_missing_file_returns_400(client, stub_library):
    rv = client.post(URL, data={"book_id": "5"},
                     content_type="multipart/form-data", headers=_hdr())
    assert rv.status_code == 400


def test_bad_book_id_returns_400(client, stub_library):
    rv = client.post(URL, data={"book_id": "abc", "file": _epub_part()},
                     content_type="multipart/form-data", headers=_hdr())
    assert rv.status_code == 400


def test_unknown_book_returns_404(client, stub_library):
    rv = client.post(URL, data={"book_id": "999", "file": _epub_part()},
                     content_type="multipart/form-data", headers=_hdr())
    assert rv.status_code == 404


def test_non_epub_rejected_415(client, stub_library):
    rv = client.post(URL, data={"book_id": "5", "file": (io.BytesIO(b"x"), "book.pdf")},
                     content_type="multipart/form-data", headers=_hdr())
    assert rv.status_code == 415


def test_import_replaces_epub_and_touches_metadata(client, stub_library):
    tmp_path, book = stub_library
    rv = client.post(URL,
                     data={"book_id": "5", "trigger_translation": "false",
                           "source_ref": "halo:book5@sha256:aa", "file": _epub_part()},
                     content_type="multipart/form-data", headers=_hdr())
    assert rv.status_code == 200, rv.get_json()
    body = rv.get_json()
    assert body["bookId"] == 5
    assert body["format"] == "EPUB"
    assert body["translationJobId"] is None
    assert body["fingerprint"]

    saved = tmp_path / "Author/Fake Book/Fake Book.epub"
    assert saved.exists()
    assert saved.read_bytes() == b"fake-epub-bytes"
    assert book.last_modified is not None  # 元数据脏标记路径已走


def test_size_limit_returns_413_and_keeps_previous_epub(client, stub_library, monkeypatch):
    """评审阻断项：超限导入必须保住线上上一版，不得毁掉生效文件。"""
    tmp_path, _ = stub_library
    book_dir = tmp_path / "Author/Fake Book"
    book_dir.mkdir(parents=True, exist_ok=True)
    saved = book_dir / "Fake Book.epub"
    saved.write_bytes(b"OLD-GOOD-EPUB")
    monkeypatch.setenv(MAX_MB_ENV, "0")
    rv = client.post(URL, data={"book_id": "5", "trigger_translation": "false", "file": _epub_part()},
                     content_type="multipart/form-data", headers=_hdr())
    assert rv.status_code == 413
    assert saved.read_bytes() == b"OLD-GOOD-EPUB"
    assert not list(book_dir.glob("*.tmp"))  # 临时文件已清理


def test_cover_success_path(client, stub_library, monkeypatch, bi):
    calls = {}
    monkeypatch.setattr(bi.helper, "save_cover",
                        lambda f, path: calls.update(saved=path) or (True, "ok"))
    monkeypatch.setattr(bi.helper, "replace_cover_thumbnail_cache",
                        lambda book_id: calls.update(thumbs=book_id))
    rv = client.post(URL,
                     data={"book_id": "5", "trigger_translation": "false",
                           "file": _epub_part(),
                           "cover": (io.BytesIO(b"img"), "cover.jpg")},
                     content_type="multipart/form-data", headers=_hdr())
    assert rv.status_code == 200
    assert calls == {"saved": "Author/Fake Book", "thumbs": 5}


def test_success_response_carries_no_session_cookie(client, stub_library):
    """login_user 的管理员会话键不得随响应下发（评审实锤泄露面）。"""
    rv = client.post(URL, data={"book_id": "5", "trigger_translation": "false", "file": _epub_part()},
                     content_type="multipart/form-data", headers=_hdr())
    assert rv.status_code == 200
    assert "session" not in rv.headers.get("Set-Cookie", "")


def test_concurrent_import_same_book_returns_409(client, bi, stub_library):
    lock = bi._book_lock(5)
    assert lock.acquire(blocking=False)
    try:
        rv = client.post(URL,
                         data={"book_id": "5", "trigger_translation": "false", "file": _epub_part()},
                         content_type="multipart/form-data", headers=_hdr())
        assert rv.status_code == 409
    finally:
        lock.release()


def test_translation_trigger_success_returns_job_id(client, bi, stub_library, monkeypatch):
    monkeypatch.setattr(bi, "_trigger_translation", lambda book_id: ("job-abc", None))
    rv = client.post(URL, data={"book_id": "5", "file": _epub_part()},
                     content_type="multipart/form-data", headers=_hdr())
    assert rv.status_code == 200
    assert rv.get_json()["translationJobId"] == "job-abc"


def test_translation_trigger_failure_returns_502_after_file_saved(client, bi, stub_library,
                                                                  monkeypatch):
    tmp_path, _ = stub_library
    monkeypatch.setattr(bi, "_trigger_translation", lambda book_id: (None, "moon-well unreachable"))
    rv = client.post(URL, data={"book_id": "5", "file": _epub_part()},
                     content_type="multipart/form-data", headers=_hdr())
    assert rv.status_code == 502
    body = rv.get_json()
    assert body["translationJobId"] is None
    assert "moon-well unreachable" in body["translationError"]
    # LLD §7：翻译失败不回滚文件
    assert (tmp_path / "Author/Fake Book/Fake Book.epub").exists()


def test_bad_cover_rejected_before_epub_write(client, stub_library):
    tmp_path, _ = stub_library
    rv = client.post(URL,
                     data={"book_id": "5", "trigger_translation": "false",
                           "file": _epub_part(),
                           "cover": (io.BytesIO(b"x"), "cover.gif")},
                     content_type="multipart/form-data", headers=_hdr())
    assert rv.status_code == 415
    assert not (tmp_path / "Author/Fake Book/Fake Book.epub").exists()
