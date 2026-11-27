"""R295：/oidc/callback 失败必须回登录页，不能甩 500 白页。

Why：``authorize_access_token()`` 在 state 取不回（换浏览器 / 无痕 / App 内嵌
    webview、两个标签页同时登录）、授权码过期或被复用、Authentik 直接回
    ``?error=``、token 端点不可达时会抛 ``OAuthError`` / ``RequestException``。
    线上实测：``/oidc/callback?code=fake&state=fake``、``?code=&state=``、
    ``?error=access_denied`` 三种全部返回 500（R295 复现记录）。
How：这组用例把「任何失败都 302 回登录页」钉死，并断言日志里带着
    error/description 与 state 是否存在，便于下一次线上排查不用再猜。
"""
import pytest
from authlib.integrations.base_client.errors import OAuthError

import cps.oidc as oidc_module


class _FakeAuthentik:
    """最小 authentik 客户端替身：只实现 callback 用到的两个方法。"""

    def __init__(self, error=None, token=None, userinfo=None):
        self._error = error
        self._token = token or {}
        self._userinfo = userinfo
        self.userinfo_calls = 0

    def authorize_access_token(self):
        if self._error is not None:
            raise self._error
        return self._token

    def userinfo(self):
        self.userinfo_calls += 1
        if isinstance(self._userinfo, Exception):
            raise self._userinfo
        return self._userinfo


class _FakeOAuth:
    def __init__(self, authentik):
        self.authentik = authentik


def _use(monkeypatch, authentik):
    monkeypatch.setattr(oidc_module, "oauth", _FakeOAuth(authentik))


def test_oauth_error_redirects_instead_of_500(client, monkeypatch):
    """state 失效 / code 过期或复用：authlib 抛 OAuthError，必须回登录页。"""
    _use(monkeypatch, _FakeAuthentik(
        error=OAuthError(error="invalid_grant", description="Code not valid")))

    rv = client.get("/oidc/callback?code=stale&state=stale")

    assert rv.status_code == 302, "回调失败不能是 500"
    assert "/login" in rv.headers["Location"]


def test_authentik_error_parameter_redirects(client, monkeypatch):
    """Authentik 直接回 ?error=access_denied（用户取消授权）同样回登录页。"""
    _use(monkeypatch, _FakeAuthentik(
        error=OAuthError(error="access_denied", description="user cancelled")))

    rv = client.get("/oidc/callback?error=access_denied&error_description=user+cancelled")

    assert rv.status_code == 302
    assert "/login" in rv.headers["Location"]


def test_unexpected_transport_error_redirects(client, monkeypatch):
    """token 端点 TLS/超时等非 OAuth 异常也要兜底，不能变成 500。"""
    _use(monkeypatch, _FakeAuthentik(error=RuntimeError("SSL: CERTIFICATE_VERIFY_FAILED")))

    rv = client.get("/oidc/callback?code=x&state=y")

    assert rv.status_code == 302
    assert "/login" in rv.headers["Location"]


def test_userinfo_failure_redirects(client, monkeypatch):
    """id_token 里没有 userinfo、userinfo 请求又失败时不能 AttributeError→500。"""
    _use(monkeypatch, _FakeAuthentik(
        token={"id_token": "jwt"}, userinfo=RuntimeError("userinfo 502")))

    rv = client.get("/oidc/callback?code=x&state=y")

    assert rv.status_code == 302
    assert "/login" in rv.headers["Location"]


def test_empty_userinfo_redirects(client, monkeypatch):
    """userinfo 为空字典（缺 sub）走既有「没有 subject」分支，仍是 302。"""
    _use(monkeypatch, _FakeAuthentik(token={"id_token": "jwt"}, userinfo={}))

    rv = client.get("/oidc/callback?code=x&state=y")

    assert rv.status_code == 302
    assert "/login" in rv.headers["Location"]


def test_oauth_failure_logs_state_presence(client, monkeypatch, caplog):
    """排查口径：warning 里必须带 error/description，并说明 state 还在不在。"""
    _use(monkeypatch, _FakeAuthentik(
        error=OAuthError(error="mismatching_state", description="CSRF warning")))

    with caplog.at_level("WARNING"):
        client.get("/oidc/callback?code=x&state=y")

    joined = "\n".join(record.getMessage() for record in caplog.records)
    assert "OIDC callback: authorization failed" in joined
    assert "mismatching_state" in joined
    assert "state_present=" in joined
