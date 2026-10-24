"""R217：注册后自动回 magicbook（`/oidc/signup`）。

Why：R103 起注册按钮直连 Authentik 邀请 flow（``target="_blank"``），用户注册完
    停在 Authentik 侧，必须切回 magicbook 再点一次「Log in」——注册与登录断开
    两步。R217 把两者串成一条链：magicbook 侧先生成 OIDC 授权 URL（state 存
    session），再把它作为 ``next`` 挂在邀请 flow 后面；用户在 Authentik 完成
    注册后，flow 直接跳到授权端点静默签发 code，回到 magicbook 时已是登录态。

这些用例把三条「不能退化的硬约束」钉死：
  1. ``next`` **必须是相对路径**——Authentik 的 ``executor._flow_done()`` 用
     ``is_url_absolute()`` 判定，带 netloc 会被拒为 "Invalid next URL"；
  2. ``next`` 必须指向 Authentik **同域的授权端点** ``/application/o/authorize/``，
     否则 flow 结束后跳不到能签发 code 的地方；
  3. ``next`` 里的 ``state`` 必须与写进 Flask session 的一致，否则
     ``/oidc/callback`` 取不回 state_data，回调直接失败。
"""
from urllib.parse import parse_qs, quote, urlsplit

import pytest

from cps.oidc import _invite_token


ISSUER = "https://account.example/application/o/magicbook/"
CLIENT_ID = "test-client"
CLIENT_SECRET = "test-secret"
REDIRECT_URI = "https://magicbook.example/oidc/callback"
INVITE_URL = (
    "https://account.example/if/flow/invitation-enrollment/"
    "?query=itoken%3Dtest-token"
)


def _register_authentik_client(app):
    """注册一个 authentik OAuth 客户端，预置 server_metadata（避免真实网络请求）。

    授权端点刻意用与现网同构的 ``/application/o/authorize/``——用例 2 要断言
    next 指向它。
    """
    import time

    from authlib.integrations.flask_client import OAuth

    from cps.oidc import AuthentikOAuth2App

    oauth = OAuth()
    oauth.init_app(app)
    oauth.register(
        name="authentik",
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        server_metadata_url=ISSUER + ".well-known/openid-configuration",
        client_kwargs={"scope": "openid profile email"},
        client_cls=AuthentikOAuth2App,
    )
    client = oauth.create_client("authentik")
    client.server_metadata.update({
        "_loaded_at": time.time(),
        "issuer": ISSUER,
        "authorization_endpoint": "https://account.example/application/o/authorize/",
        "token_endpoint": "https://account.example/application/o/token/",
    })
    return oauth


@pytest.fixture
def signup_env(app, monkeypatch):
    """配置好 OIDC + 邀请链接的环境，并注册可用的 authentik 客户端。"""
    monkeypatch.setitem(app.config, "AUTHENTIK_OIDC_ENABLED", True)
    monkeypatch.setenv("AUTHENTIK_ISSUER", ISSUER)
    monkeypatch.setenv("AUTHENTIK_MAGICBOOK_CLIENT_ID", CLIENT_ID)
    monkeypatch.setenv("AUTHENTIK_MAGICBOOK_CLIENT_SECRET", CLIENT_SECRET)
    monkeypatch.setenv("AUTHENTIK_MAGICBOOK_REDIRECT_URI", REDIRECT_URI)
    monkeypatch.setenv("AUTHENTIK_ENROLLMENT_INVITE_URL", INVITE_URL)
    oauth = _register_authentik_client(app)
    # cps.oidc 模块级 oauth 实例也要能拿到客户端，否则端点内 create_authorization_url 会失败
    monkeypatch.setattr("cps.oidc.oauth", oauth)
    return oauth


def _signup_location(client, path="/oidc/signup"):
    """调用 /oidc/signup 并返回 (status, Location 头)。"""
    rv = client.get(path)
    return rv.status_code, rv.headers.get("Location", "")


def _nested_flow_query(location):
    """取 Authentik flow 外壳里的内层 query，模拟 executor 的解析方式。"""
    outer_query = parse_qs(urlsplit(location).query)
    return parse_qs(outer_query["query"][0])


class TestInviteToken:
    def test_parses_itoken_from_nested_query(self, monkeypatch):
        """R219：Authentik 只读外层 query 里的嵌套 itoken。"""
        monkeypatch.setenv("AUTHENTIK_ENROLLMENT_INVITE_URL", INVITE_URL)
        assert _invite_token() == "test-token"

    def test_parses_legacy_top_level_itoken(self, monkeypatch):
        """老部署仍可启动，但只用于兼容已有 env，不再生成这种链接。"""
        monkeypatch.setenv(
            "AUTHENTIK_ENROLLMENT_INVITE_URL",
            "https://account.example/if/flow/invitation-enrollment/?itoken=legacy-token",
        )
        assert _invite_token() == "legacy-token"

    def test_nested_token_wins_over_legacy_outer_token(self, monkeypatch):
        """嵌套 query 是现行契约，冲突时不能退回旧值。"""
        monkeypatch.setenv(
            "AUTHENTIK_ENROLLMENT_INVITE_URL",
            "https://account.example/if/flow/invitation-enrollment/"
            "?itoken=outer-token&query=itoken%3Dnested-token",
        )
        assert _invite_token() == "nested-token"

    def test_parses_token_alias_in_nested_query(self, monkeypatch):
        monkeypatch.setenv(
            "AUTHENTIK_ENROLLMENT_INVITE_URL",
            "https://account.example/if/flow/invitation-enrollment/?query=token%3Dalias-token",
        )
        assert _invite_token() == "alias-token"

    def test_returns_none_when_env_missing(self, monkeypatch):
        monkeypatch.delenv("AUTHENTIK_ENROLLMENT_INVITE_URL", raising=False)
        assert _invite_token() is None

    def test_returns_none_when_url_has_no_token(self, monkeypatch):
        """URL 形态被改（无 itoken）时必须返回 None，而不是跳一个坏链接。"""
        monkeypatch.setenv("AUTHENTIK_ENROLLMENT_INVITE_URL",
                           "https://account.example/if/flow/invitation-enrollment/")
        assert _invite_token() is None


class TestSignupRedirect:
    def test_redirects_to_invitation_flow(self, app, client, signup_env):
        """/oidc/signup 返回 302，且 Location 指向 Authentik 邀请 flow。"""
        status, location = _signup_location(client)
        assert status == 302
        assert location.startswith("https://account.example/if/flow/invitation-enrollment/")
        assert _nested_flow_query(location)["itoken"] == ["test-token"]

    def test_itoken_and_next_are_nested_under_query(self, app, client, signup_env):
        """R219：二者必须在内层 query，顶层只留 Authentik 认识的 query 外壳。"""
        status, location = _signup_location(client)
        assert status == 302
        outer_query = parse_qs(urlsplit(location).query)
        assert set(outer_query) == {"query"}
        assert set(_nested_flow_query(location)) == {"itoken", "next"}

    def test_next_is_relative_path(self, app, client, signup_env):
        """硬约束 1：next 必须是相对路径。

        Authentik 的 ``executor._flow_done()`` 对带 netloc 的 next 报
        "Invalid next URL"，flow 无法完成跳转 → 用户注册完卡住。
        """
        status, location = _signup_location(client)
        assert status == 302
        next_value = _nested_flow_query(location)["next"][0]
        parts = urlsplit(next_value)
        assert not parts.scheme, "next 不得带 scheme（Authentik 只接受相对路径）"
        assert not parts.netloc, "next 不得带 netloc（Authentik 只接受相对路径）"
        assert next_value.startswith("/")

    def test_next_points_to_authorize_endpoint(self, app, client, signup_env):
        """硬约束 2：next 指向同域授权端点——那里才能静默签发 code。"""
        status, location = _signup_location(client)
        next_value = _nested_flow_query(location)["next"][0]
        assert next_value.startswith("/application/o/authorize/")

    def test_next_carries_client_id_and_redirect_uri(self, app, client, signup_env):
        """next 内必须带 client_id 与 redirect_uri，否则授权端点无法签发 code。"""
        status, location = _signup_location(client)
        next_query = parse_qs(urlsplit(_nested_flow_query(location)["next"][0]).query)
        assert next_query["client_id"] == [CLIENT_ID]
        assert next_query["redirect_uri"] == [REDIRECT_URI]
        assert next_query["response_type"] == ["code"]
        assert "openid" in next_query["scope"][0].split()

    def test_next_state_matches_session(self, app, client, signup_env):
        """硬约束 3：next 里的 state 必须与 Flask session 里的一致。

        authlib 把 state/nonce/code_verifier 写进 session（``save_authorize_data``），
        ``/oidc/callback`` 凭 state 取回 state_data 校验 nonce。state 对不上，
        回调必然失败。
        """
        from flask import session

        with client:
            status, location = _signup_location(client)
            assert status == 302
            next_query = parse_qs(urlsplit(_nested_flow_query(location)["next"][0]).query)
            state = next_query["state"][0]
            # authlib 存 session 的键形如 _state_authentik_<state>
            assert any(state in key for key in session.keys()), \
                "state 未写入 session，回调将取不回 state_data"

    def test_open_redirect_rejected(self, app, client, signup_env):
        """用户指定的「注册完回哪个页面」不得跳到站外。"""
        with client:
            _signup_location(client, "/oidc/signup?next=https://evil.example/x")
            from flask import session
            assert not session.get("oidc_next", "").startswith("http")

    def test_next_page_kept_when_internal(self, app, client, signup_env):
        """站内相对路径的 next 应当被保留（注册完回到用户本来想去的地方）。"""
        with client:
            _signup_location(client, "/oidc/signup?next=/book/1")
            from flask import session
            assert session.get("oidc_next") == "/book/1"

    def test_redirect_uri_falls_back_to_url_for(self, app, client, signup_env, monkeypatch):
        """未配置 AUTHENTIK_MAGICBOOK_REDIRECT_URI 时回退到 url_for 生成。"""
        monkeypatch.delenv("AUTHENTIK_MAGICBOOK_REDIRECT_URI", raising=False)
        status, location = _signup_location(client)
        assert status == 302
        next_query = parse_qs(urlsplit(_nested_flow_query(location)["next"][0]).query)
        assert next_query["redirect_uri"][0].endswith("/oidc/callback")

    def test_no_redirect_when_invite_not_configured(self, app, client, signup_env, monkeypatch):
        """邀请链接未配置 → 不跳 Authentik，回登录页并提示（沿用 R103 的关闭能力）。"""
        monkeypatch.delenv("AUTHENTIK_ENROLLMENT_INVITE_URL", raising=False)
        status, location = _signup_location(client)
        assert status == 302
        assert "/login" in location
        assert "account.example" not in location

    def test_no_redirect_when_oidc_disabled(self, app, client, signup_env, monkeypatch):
        """OIDC 未启用 → 回登录页，不跳 Authentik。"""
        monkeypatch.setitem(app.config, "AUTHENTIK_OIDC_ENABLED", False)
        status, location = _signup_location(client)
        assert status == 302
        assert "/login" in location
        assert "account.example" not in location


class TestLoginPageSignupLink:
    def test_login_page_points_to_signup_endpoint(self, app, client, signup_env):
        """登录页注册按钮指向 /oidc/signup（不再是裸邀请链接）。"""
        rv = client.get("/login")
        assert rv.status_code == 200
        page = rv.data.decode("utf-8")
        assert 'id="authentik_invite_signup"' in page
        assert "/oidc/signup" in page

    def test_login_page_signup_has_no_target_blank(self, app, client, signup_env):
        """同窗口连续体验：不再 target=_blank（那正是「注册完在哪」的断点）。"""
        rv = client.get("/login")
        page = rv.data.decode("utf-8")
        assert 'id="authentik_invite_signup"' in page
        # 整页不应再有 target="_blank" 的注册入口
        assert 'id="authentik_invite_signup"' in page
        assert 'target="_blank" rel="noopener"\n       class="btn btn-default btn-block"' \
            not in page

    def test_signup_link_absent_when_invite_not_configured(self, app, client, signup_env, monkeypatch):
        """邀请链接未配置 → 登录页不渲染注册入口。"""
        monkeypatch.delenv("AUTHENTIK_ENROLLMENT_INVITE_URL", raising=False)
        rv = client.get("/login")
        page = rv.data.decode("utf-8")
        assert "Log in" in page
        assert "authentik_invite_signup" not in page
