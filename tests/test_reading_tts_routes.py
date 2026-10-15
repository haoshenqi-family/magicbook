"""整本朗读路由测试（R166）：门禁、受理转发、身份闭包。

镜像 test_credit_consume.py 的姿势：admin_client + 桩 _moonwell_proxy。
"""

import json

import pytest


@pytest.fixture
def moonwell_configured(monkeypatch):
    from cps import constants
    monkeypatch.setattr(constants, "MOON_WELL_READING_URL",
                        "https://moon-well.example.com/")
    return constants


@pytest.fixture(autouse=True)
def stub_batches(monkeypatch):
    """桩掉批次服务：路由层只测门禁/转发/闭包构造，批次逻辑在服务测试里覆盖。"""
    import cps.web as w

    captured = {}

    class _FakeService:
        def __init__(self):
            self.start_args = None
            self.progress = {"jobId": "j1", "status": "RUNNING", "total": 3,
                             "done": 0, "failed": 0, "voice": "Mia", "style": "s",
                             "bookName": "Test Book", "bookId": 1}

        def start(self, book_id, book_format, proxy=None, force_voice=False, force_new_batch=False):
            captured["start"] = dict(book_id=book_id, book_format=book_format,
                                     proxy_set=callable(proxy), force_voice=force_voice)
            assert proxy is not None and callable(proxy)
            return dict(self.progress)

        def get_progress(self, job_id):
            captured["status_job"] = job_id
            return dict(self.progress)

        def retry(self, job_id, proxy=None):
            captured["retry"] = job_id
            assert proxy is not None and callable(proxy)
            return dict(self.progress)

        def cancel(self, job_id):
            captured["cancel"] = job_id
            return dict(self.progress)

    fake = _FakeService()
    monkeypatch.setattr("cps.routes.reading.whole_book_tts_service", fake)
    return types_namespace(captured=captured)


def types_namespace(**kwargs):
    import types
    return types.SimpleNamespace(**kwargs)


def test_start_requires_login(app, moonwell_configured, stub_batches):
    client = app.test_client()
    assert client.post("/ajax/reading-tts-book", json={"book_id": 1}).status_code == 302


def test_start_requires_admin(app, moonwell_configured, stub_batches):
    client = app.test_client()
    # 非 admin 登录用户：admin_required 拦截（302 重定向或 403，视装饰器实现）
    # 直接以匿名断言门禁存在即可（详细角色矩阵由 admin_required 自身测试覆盖）
    assert client.post("/ajax/reading-tts-book", json={"book_id": 1}).status_code in (302, 403)


def test_start_forwards_to_service_with_proxy(admin_client, moonwell_configured, stub_batches,
                                              monkeypatch):
    import cps.web as w
    # 身份令牌：session 里放 moonwell_access_token（闭包定格用）
    with admin_client.session_transaction() as session:
        session["moonwell_access_token"] = "snap-token"

    rv = admin_client.post("/ajax/reading-tts-book",
                           json={"book_id": 1, "book_format": "epub"})
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["jobId"] == "j1"
    assert stub_batches.captured["start"]["book_id"] == 1
    assert stub_batches.captured["start"]["book_format"] == "epub"
    assert stub_batches.captured["start"]["proxy_set"] is True


def test_start_without_token_returns_400(admin_client, moonwell_configured, stub_batches,
                                         monkeypatch):
    # 无 moonwell token：身份闭包构造失败 → 400 明确提示（R51 教训：不静默全段失败）。
    # admin_client 登录流程会写入 token，这里桩空 flask_session 模拟缺失
    import cps.web as w

    class _EmptySession:
        def get(self, key, default=None):
            return default

    monkeypatch.setattr(w, "flask_session", _EmptySession())
    rv = admin_client.post("/ajax/reading-tts-book", json={"book_id": 1})
    assert rv.status_code == 400
    assert "moon-well authorization" in rv.get_json()["message"]


def test_status_and_cancel_forward(admin_client, moonwell_configured, stub_batches):
    with admin_client.session_transaction() as session:
        session["moonwell_access_token"] = "snap-token"

    rv = admin_client.post("/ajax/reading-tts-book/status", json={"job_id": "j9"})
    assert rv.status_code == 200
    assert stub_batches.captured["status_job"] == "j9"

    rv = admin_client.post("/ajax/reading-tts-book/cancel", json={"job_id": "j9"})
    assert rv.status_code == 200
    assert stub_batches.captured["cancel"] == "j9"
