"""R279 用户投稿链路守卫：MinIO 暂存 + 管理员审核 + 入库。

Why 单独成文件：投稿链路把「谁能写」从书库挪到了 MinIO 暂存区，安全边界
（匿名不可读、角色不查 upload、审核是唯一入库口）一旦被后来的重构打破，
症状是静默的。这里钉可执行行为，storage/MinIO 用桩，路由与状态机走真实代码。
"""
import io
import os
import types

import pytest

from cps import constants

SUBMIT_URL = "/ajax/library/submit"
MINE_URL = "/ajax/library/submissions/mine"
LIST_URL = "/ajax/admin/submissions"
PREVIEW_URL = "/ajax/admin/submissions/{id}/preview"
REVIEW_URL = "/ajax/admin/submissions/{id}/review"

EPUB_BYTES = b"PK\x03\x04fake-epub-payload"


@pytest.fixture
def sub(app):
    import cps.library_submission.service as submission_service
    import cps.library_submission.models as submission_models
    submission_service.ensure_tables()
    # 隔离：app.db 在测试会话内共享，投稿行会跨用例累积（测「重复投稿去重」
    # 时会命中别的用例留下的行）。每个用例开始前清空台账。
    session = submission_service._submission_session()
    try:
        session.query(submission_models.BookSubmission).delete()
        session.commit()
    finally:
        session.remove()
    return submission_service


@pytest.fixture(autouse=True)
def _reset_limiter(app):
    """每个用例前后清空内存限流计数：投稿接口 5/hour 会跨用例累积。"""
    from cps import limiter
    if limiter is None:
        yield
        return
    def _clear():
        try:
            with app.app_context():
                limiter.reset()
        except Exception:
            pass
    _clear()
    yield
    _clear()


@pytest.fixture
def stub_storage(sub, monkeypatch, tmp_path):
    """MinIO 桩：对象落 tmp_path，读写可断言；匿名读路径不存在。"""
    import cps.library_submission.storage as storage
    objects = {}

    def put_object(key, stream, length, content_type):
        objects[key] = stream.read()
        return types.SimpleNamespace(key=key)

    def stat_object(key):
        if key not in objects:
            raise KeyError(key)
        return types.SimpleNamespace(size=len(objects[key]))

    def get_object(key):
        if key not in objects:
            raise KeyError(key)
        payload = objects[key]

        class _FakeResponse:
            def stream(self, amt=8192):
                yield payload

            def read(self, amt=None):
                return payload

            def close(self):
                pass

            def release_conn(self):
                pass

        return _FakeResponse()

    def remove_object(key):
        objects.pop(key, None)

    monkeypatch.setattr(storage, "put_object", put_object)
    monkeypatch.setattr(storage, "stat_object", stat_object)
    monkeypatch.setattr(storage, "get_object", get_object)
    monkeypatch.setattr(storage, "remove_object", remove_object)
    monkeypatch.setattr(storage, "configured", lambda: True)
    return objects


@pytest.fixture
def stub_ingest(sub, monkeypatch, tmp_path):
    """入库桩：不碰 calibre，直接返回假 book id 并吃掉临时文件。"""
    calls = {}

    def fake_extract_meta(temp_path, original_filename, extension):
        return types.SimpleNamespace(
            file_path=temp_path, extension="." + extension.lower(),
            title="Submitted Book", author="Submitter", cover=None,
            description="desc", tags="", series="", series_id="",
            languages="", publisher="", pubdate="", identifiers=[])

    def fake_ingest(meta, temp_path):
        calls["ingested"] = calls.get("ingested", 0) + 1
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        return types.SimpleNamespace(id=777), None

    monkeypatch.setattr(sub, "extract_meta", fake_extract_meta)
    monkeypatch.setattr(sub, "ingest_book_from_meta", fake_ingest)
    # 测试环境无 calibre 库：临时目录落在 tmp_path
    monkeypatch.setattr(sub.config, "get_book_path", lambda: str(tmp_path))
    return calls


def _login_plain(app, name="sub-user"):
    from cps import ub
    from werkzeug.security import generate_password_hash
    user = ub.session.query(ub.User).filter(ub.User.name == name).first()
    if user is None:
        user = ub.User(name=name, email=name + "@example.com",
                       password=generate_password_hash("plain-pass"))
        ub.session.add(user)
        ub.session.commit()
    client = app.test_client()
    assert client.post("/login", data={"username": name,
                                       "password": "plain-pass"}).status_code == 302
    from cps import config as cw_config
    cw_config.db_configured = True
    return client


def _epub_part(name="my-book.epub"):
    return (io.BytesIO(EPUB_BYTES), name, "application/epub+zip")


def _submission_id(client):
    data = client.get(MINE_URL).get_json()
    return data["result"][0]["id"]


class TestUserSubmit:
    def test_plain_user_can_submit_without_upload_role(self, app, client, sub,
                                                       stub_storage, monkeypatch):
        client = _login_plain(app, "sub-user")
        rv = client.post(SUBMIT_URL, data={
            "declaration": "1", "file": _epub_part()},
            content_type="multipart/form-data")
        assert rv.status_code == 200
        body = rv.get_json()
        assert body["success"] is True
        assert body["result"]["status"] == "PENDING"
        assert body["result"]["created"] is True

    def test_declaration_is_required(self, app, client, sub, stub_storage):
        client = _login_plain(app, "sub-user")
        rv = client.post(SUBMIT_URL, data={"file": _epub_part()},
                         content_type="multipart/form-data")
        assert rv.status_code == 400

    def test_disallowed_extension_rejected(self, app, client, sub, stub_storage):
        client = _login_plain(app, "sub-user")
        rv = client.post(SUBMIT_URL, data={
            "declaration": "1",
            "file": (io.BytesIO(b"MZ exe"), "virus.exe", "application/x-msdownload")},
            content_type="multipart/form-data")
        assert rv.status_code == 400

    def test_audio_formats_rejected(self, app, client, sub, stub_storage):
        """投稿只收书：mp4/mp3 等音视频不入投稿白名单。"""
        client = _login_plain(app, "sub-user")
        rv = client.post(SUBMIT_URL, data={
            "declaration": "1",
            "file": (io.BytesIO(b"\x00\x00\x00 ftyp"), "song.mp4", "video/mp4")},
            content_type="multipart/form-data")
        assert rv.status_code == 400

    def test_anonymous_rejected(self, client, sub, stub_storage):
        rv = client.post(SUBMIT_URL, data={"declaration": "1", "file": _epub_part()},
                         content_type="multipart/form-data")
        assert rv.status_code in (302, 401)

    def test_duplicate_upload_reuses_record_without_second_object(
            self, app, client, sub, stub_storage):
        client = _login_plain(app, "sub-user")
        first = client.post(SUBMIT_URL, data={
            "declaration": "1", "file": _epub_part()},
            content_type="multipart/form-data").get_json()
        second = client.post(SUBMIT_URL, data={
            "declaration": "1", "file": _epub_part()},
            content_type="multipart/form-data").get_json()
        assert second["result"]["created"] is False
        assert second["result"]["id"] == first["result"]["id"]
        assert len(stub_storage) == 1


class TestAdminReview:
    def test_plain_user_cannot_list_or_review(self, app, sub, stub_storage):
        client = _login_plain(app, "sub-user")
        assert client.get(LIST_URL).status_code == 403
        assert client.post(REVIEW_URL.format(id=1), json={"approve": True}).status_code == 403

    def test_admin_page_and_list_require_admin(self, app, sub, stub_storage):
        assert app.test_client().get("/admin/submissions").status_code == 302
        admin = app.test_client()
        assert admin.post("/login", data={"username": "admin",
                                          "password": "admin123"}).status_code == 302
        assert admin.get("/admin/submissions").status_code == 200
        assert admin.get(LIST_URL).status_code == 200

    def test_approve_ingests_and_clears_object(self, app, sub, stub_storage,
                                               stub_ingest, monkeypatch):
        client = _login_plain(app, "sub-user")
        client.post(SUBMIT_URL, data={"declaration": "1", "file": _epub_part()},
                    content_type="multipart/form-data")
        submission_id = _submission_id(client)
        assert len(stub_storage) == 1
        sub.review(submission_id, 1, True, "")
        for _ in range(100):
            row = sub.get_submission(submission_id)
            if row["status"] == "INGESTED":
                break
            import time
            time.sleep(0.05)
        assert row["status"] == "INGESTED"
        assert row["bookId"] == 777
        assert len(stub_storage) == 0
        assert stub_ingest.get("ingested") == 1

    def test_reject_removes_object_and_marks_rejected(self, app, sub, stub_storage):
        client = _login_plain(app, "sub-user")
        client.post(SUBMIT_URL, data={"declaration": "1", "file": _epub_part()},
                    content_type="multipart/form-data")
        submission_id = _submission_id(client)
        row = sub.review(submission_id, 1, False, "not a book")
        assert row["status"] == "REJECTED"
        assert row["note"] == "not a book"
        assert len(stub_storage) == 0

    def test_rejected_cannot_be_reviewed_again(self, app, sub, stub_storage):
        client = _login_plain(app, "sub-user")
        client.post(SUBMIT_URL, data={"declaration": "1", "file": _epub_part()},
                    content_type="multipart/form-data")
        submission_id = _submission_id(client)
        sub.review(submission_id, 1, False, "")
        row = sub.review(submission_id, 1, True, "")
        assert row["status"] == "REJECTED"


class TestStorageSafety:
    def test_submission_prefix_is_not_in_public_origins(self):
        """核心安全面：投稿前缀绝不能出现在任何公开直链源里。"""
        import cps.web as web_module
        sources = " ".join(web_module.MINIO_PUBLIC_ORIGINS)
        assert "book-submissions" not in sources

    def test_no_presigned_urls_in_submission_layer(self):
        """本模块不得产生预签名/公开直链：只有服务端签名读写。"""
        from cps.library_submission import storage
        source = open(storage.__file__, encoding="utf-8").read()
        assert "presigned" not in source
        assert "get_presigned" not in source

    def test_ingest_registers_calibre_udfs_before_insert(self):
        """E2E 实测：calibre 的 INSERT 触发器依赖 title_sort/uuid4，未注册会直接失败。"""
        from cps.library_submission import ingest
        source = open(ingest.__file__, encoding="utf-8").read()
        assert "create_functions(config)" in source

    def test_ingest_worker_uses_request_context_for_gettext(self):
        """E2E 实测：uploader 链路会走 flask_babel.get_locale() → request.accept_languages。"""
        from cps.library_submission import service
        source = open(service.__file__, encoding="utf-8").read()
        assert "test_request_context" in source

    def test_ingest_helpers_do_not_use_merge(self):
        """E2E 实测：session.merge 返回托管副本，原对象再 append 会撞 authors.name UNIQUE。"""
        from cps.library_submission import ingest
        source = open(ingest.__file__, encoding="utf-8").read()
        assert ".merge(" not in source

    def test_object_key_never_contains_user_input(self):
        from cps.library_submission import storage
        key = storage.object_key_for(42, "abc123", "epub")
        assert key.startswith("book-submissions/42/")
        assert key.endswith(".epub")


class TestAdminNav:
    def test_admin_nav_has_submissions_entry(self):
        from cps import ui_ia
        flat = [item for _, items in ui_ia.ADMIN_L2_GROUPS for item in items]
        assert any(item["id"] == "admin-submissions" for item in flat)

    def test_admin_path_prefix_contains_submissions(self):
        from cps import ui_ia
        assert "/admin/submissions" in ui_ia.ADMIN_PATH_PREFIXES

    def test_nav_domain_routes_submissions_to_admin(self):
        from cps import ui_ia
        assert ui_ia.nav_domain("/admin/submissions", "") == "admin"
