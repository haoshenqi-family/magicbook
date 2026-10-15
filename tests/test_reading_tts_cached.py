"""R170 朗读缓存回读路由测试（伴读 agent 播放链路）。

核心守卫只有一条：本路由必须打到 moon-well 的**不计费**端点 `/tts/cached-audio`。
写成 `/tts/speak` 在功能上照样能播（缓存命中也返回音频），但 `/speak` 是「听=消费」——
每次请求含命中都扣 1 积分，而伴读工具 synthesize_tts 已经在工具内扣过一遍，
用户就会为同一次朗读被扣两分。这个偏差在界面上完全看不出来，只能由断言钉住。
"""

import pytest


@pytest.fixture
def moonwell_configured(monkeypatch):
    from cps import constants
    monkeypatch.setattr(constants, "MOON_WELL_READING_URL",
                        "https://moon-well.example.com/")
    return constants


@pytest.fixture
def stub_proxy(monkeypatch):
    """桩掉上游代理：路由层只测门禁、目标路径与入参清洗。"""
    import cps.web as w

    calls = []

    def fake_proxy(path, payload, timeout, label, binary=False, method="POST",
                   system_identity=False, bearer_token=None):
        calls.append({"path": path, "payload": payload, "timeout": timeout,
                      "label": label, "binary": binary, "method": method})
        return (b"FAKE-MP3-BYTES", 200, {"Content-Type": "audio/mpeg"})

    monkeypatch.setattr(w._moonwell_client, "proxy", fake_proxy)
    return calls


PARA = "It is a truth universally acknowledged"


def test_requires_login(client, moonwell_configured, stub_proxy):
    assert client.post("/ajax/reading-tts-cached", json={"text": PARA}).status_code == 302
    assert stub_proxy == []


def test_forwards_to_unbilled_cache_endpoint_not_speak(admin_client, moonwell_configured,
                                                     stub_proxy):
    rv = admin_client.post("/ajax/reading-tts-cached", json={"text": PARA})

    assert rv.status_code == 200
    assert len(stub_proxy) == 1
    call = stub_proxy[0]
    assert call["path"] == "/tts/cached-audio"
    assert call["path"] != "/tts/speak", "走 /speak 会把同一次朗读扣两遍积分"
    assert call["binary"] is True, "音频字节必须二进制透传，不能按文本解码"
    assert call["payload"] == {"text": PARA}


def test_passes_audio_bytes_and_content_type_through(admin_client, moonwell_configured,
                                                    stub_proxy):
    rv = admin_client.post("/ajax/reading-tts-cached", json={"text": PARA})

    assert rv.data == b"FAKE-MP3-BYTES"
    assert rv.headers["Content-Type"] == "audio/mpeg"


def test_blank_text_rejected_before_upstream(admin_client, moonwell_configured, stub_proxy):
    for payload in ({"text": ""}, {"text": "   "}, {}, {"text": None}):
        rv = admin_client.post("/ajax/reading-tts-cached", json=payload)
        assert rv.status_code == 400, payload
    assert stub_proxy == [], "空文本不该花一次上游调用"


def test_oversized_text_rejected_before_upstream(admin_client, moonwell_configured, stub_proxy):
    rv = admin_client.post("/ajax/reading-tts-cached", json={"text": "a" * 2001})

    assert rv.status_code == 400
    assert stub_proxy == []


def test_boundary_2000_chars_is_forwarded(admin_client, moonwell_configured, stub_proxy):
    text = "a" * 2000

    rv = admin_client.post("/ajax/reading-tts-cached", json={"text": text})

    assert rv.status_code == 200
    assert stub_proxy[0]["payload"]["text"] == text


def test_surrounding_whitespace_stripped_to_match_cache_key(admin_client, moonwell_configured,
                                                           stub_proxy):
    """缓存键是 trim 后原文的 SHA-256，所以发出去的必须是同一份 trim 结果。"""
    rv = admin_client.post("/ajax/reading-tts-cached", json={"text": "  " + PARA + "\n"})

    assert rv.status_code == 200
    assert stub_proxy[0]["payload"]["text"] == PARA


def test_miss_status_and_content_type_pass_through(admin_client, moonwell_configured,
                                                   monkeypatch):
    """moon-well 对未合成过的文本回 404（绝不就地合成），本层必须原样透传而不是转成 200 空音频。"""
    import cps.web as w

    def fake_proxy(path, payload, timeout, label, binary=False, method="POST",
                   system_identity=False, bearer_token=None):
        return (b"", 404, {"Content-Type": "application/json"})

    monkeypatch.setattr(w._moonwell_client, "proxy", fake_proxy)

    rv = admin_client.post("/ajax/reading-tts-cached", json={"text": PARA})

    assert rv.status_code == 404
    assert rv.data == b"", "404 不能被伪装成一段空音频播出去"
