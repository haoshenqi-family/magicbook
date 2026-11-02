"""R222：书籍简介上游故障不得伪装成客户端 400。"""
import json

import pytest


def _summary_payload():
    return {
        "bookId": 337,
        "bookFormat": "epub",
        "chapters": [{"title": "Chapter 1"}],
        "excerpt": [{"text": "Hello world."}],
        "aiSummary": None,
    }


class _Book:
    title = "Test Book"
    authors = []
    series = []


@pytest.fixture
def summary_ready(monkeypatch):
    """隔离书籍解析与落库，只留下 moon-well 响应这一条变量。"""
    from cps.reading_insight import service

    monkeypatch.setattr(service, "get_or_build", lambda *_args: _summary_payload())
    monkeypatch.setattr(service, "_book_file", lambda *_args: (_Book(), "/tmp/test.epub"))
    monkeypatch.setattr(service, "_save_ai_summary", lambda *_args: None)
    return service


def test_upstream_500_maps_to_502_with_readable_message(admin_client, monkeypatch,
                                                       summary_ready):
    """moon-well 500 是依赖故障，不是浏览器发错请求。"""
    from cps import web

    monkeypatch.setattr(web, "_moonwell_proxy", lambda *_args, **_kwargs: (
        json.dumps({"success": False, "message": "Magpie call failed: HTTP 403"}),
        500,
        {"Content-Type": "application/json"},
    ))

    response = admin_client.post("/ajax/book-summary",
                                 json={"book_id": 337, "book_format": "epub"})

    assert response.status_code == 502
    assert response.get_json() == {
        "success": False,
        "message": "Magpie call failed: HTTP 403",
    }


def test_upstream_success_still_returns_summary(admin_client, monkeypatch,
                                               summary_ready):
    """状态码映射不能误伤成功分支。"""
    from cps import web

    monkeypatch.setattr(web, "_moonwell_proxy", lambda *_args, **_kwargs: (
        json.dumps({"success": True, "result": {
            "content": "A concise introduction.",
            "model": "test-model",
        }}),
        200,
        {"Content-Type": "application/json"},
    ))

    response = admin_client.post("/ajax/book-summary",
                                 json={"book_id": 337, "book_format": "epub"})

    assert response.status_code == 200
    assert response.get_json()["result"]["text"] == "A concise introduction."


def test_upstream_redirect_is_not_treated_as_success(admin_client, monkeypatch,
                                                      summary_ready):
    """3xx 不是有效 Result；否则空 result 会被误判为「生成成功」。"""
    from cps import web

    monkeypatch.setattr(web, "_moonwell_proxy", lambda *_args, **_kwargs: (
        json.dumps({"success": True, "result": {}}),
        302,
        {"Content-Type": "application/json"},
    ))

    response = admin_client.post("/ajax/book-summary",
                                 json={"book_id": 337, "book_format": "epub"})

    assert response.status_code == 502
    assert response.get_json()["message"] == "book-intro failed (HTTP 302)"


def test_invalid_book_id_still_maps_to_400(admin_client):
    """真正的客户端入参错误仍必须是 400。"""
    response = admin_client.post("/ajax/book-summary",
                                 json={"book_id": "not-an-int", "book_format": "epub"})

    assert response.status_code == 400
    assert response.get_json()["success"] is False
