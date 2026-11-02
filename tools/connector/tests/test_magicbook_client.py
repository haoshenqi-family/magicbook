import requests

import magicbook_client
from magicbook_client import MagicbookClient, MagicbookError


class Resp:
    def __init__(self, status, body="{}"):
        self.status_code = status
        self.text = body

    def json(self):
        import json
        return json.loads(self.text)


def make_env(monkeypatch, responses):
    """替换 requests.post 与 sleep，记录每次调用读到的文件体。"""
    calls = []

    def fake_post(url, headers=None, files=None, data=None, timeout=None):
        calls.append(files["file"][1].read())
        return responses.pop(0)

    monkeypatch.setattr(requests, "post", fake_post)
    monkeypatch.setattr(magicbook_client.time, "sleep", lambda s: None)
    return calls


def test_retries_on_5xx_each_attempt_sends_full_body(tmp_path, monkeypatch):
    epub = tmp_path / "b.epub"
    epub.write_bytes(b"zipzip")
    client = MagicbookClient("http://mb:8083", "secret")
    calls = make_env(monkeypatch, [Resp(500), Resp(503),
                                   Resp(200, '{"translationJobId": 42}')])
    result = client.import_book(89, str(epub))
    assert result == {"translationJobId": 42}
    assert calls == [b"zipzip"] * 3  # 句柄未耗尽：每次重试都带完整文件


def test_4xx_no_retry(tmp_path, monkeypatch):
    epub = tmp_path / "b.epub"
    epub.write_bytes(b"x")
    client = MagicbookClient("http://mb:8083", "secret")
    calls = make_env(monkeypatch, [Resp(401, '{"error": "bad key"}')])
    try:
        client.import_book(89, str(epub))
        assert False
    except MagicbookError as exc:
        assert exc.status == 401
    assert len(calls) == 1


def test_502_raises_immediately_with_payload(tmp_path, monkeypatch):
    epub = tmp_path / "b.epub"
    epub.write_bytes(b"x")
    client = MagicbookClient("http://mb:8083", "secret")
    body = '{"bookId": 89, "error": "translation trigger failed"}'
    calls = make_env(monkeypatch, [Resp(502, body)])
    try:
        client.import_book(89, str(epub))
        assert False
    except MagicbookError as exc:
        assert exc.status == 502
        assert exc.payload["bookId"] == 89
    assert len(calls) == 1


def test_timeout_retries_until_exhausted(tmp_path, monkeypatch):
    epub = tmp_path / "b.epub"
    epub.write_bytes(b"x")
    client = MagicbookClient("http://mb:8083", "secret", retries=2)

    def boom(*a, **k):
        raise requests.RequestException("timeout")

    monkeypatch.setattr(requests, "post", boom)
    monkeypatch.setattr(magicbook_client.time, "sleep", lambda s: None)
    try:
        client.import_book(89, str(epub))
        assert False
    except MagicbookError as exc:
        assert "timeout" in str(exc)
