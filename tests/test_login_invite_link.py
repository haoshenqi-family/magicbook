"""R103: 登录页邀请制注册入口。

Why: magicbook 统一经 Authentik OIDC 登录（本地密码登录已禁用），新用户注册
走 Authentik 邀请制 enrollment。注册链接由 .env 的
AUTHENTIK_ENROLLMENT_INVITE_URL 注入（邀请默认 30 天过期，轮换只改环境变量），
未配置时不渲染——保留邀请过期轮换期间的关闭能力。游客首页即登录页
（匿名浏览关闭时 / 302 到 /login），因此登录入口与注册入口同页。
"""
import pytest


INVITE_URL = "https://authentik.example/if/flow/invitation-enrollment/?itoken=test-token"


def test_invite_link_rendered_when_configured(app, client, monkeypatch):
    # conftest 已注册 oidc 蓝图；这里只打开分支开关（monkeypatch 保证还原，
    # 不污染依赖本地登录分支的其他用例）
    monkeypatch.setitem(app.config, "AUTHENTIK_OIDC_ENABLED", True)
    monkeypatch.setenv("AUTHENTIK_ENROLLMENT_INVITE_URL", INVITE_URL)
    rv = client.get("/login")
    assert rv.status_code == 200
    page = rv.data.decode("utf-8")
    # 入口存在、指向配置的邀请链接、新窗口打开（不打断登录页）
    assert 'id="authentik_invite_signup"' in page
    assert 'href="{0}"'.format(INVITE_URL) in page
    assert 'target="_blank"' in page
    assert "注册账号" in page
    assert "Sign up (invite)" in page
    assert "Log in with Authentik" in page


def test_invite_link_absent_when_not_configured(app, client, monkeypatch):
    monkeypatch.setitem(app.config, "AUTHENTIK_OIDC_ENABLED", True)
    monkeypatch.delenv("AUTHENTIK_ENROLLMENT_INVITE_URL", raising=False)
    rv = client.get("/login")
    assert rv.status_code == 200
    page = rv.data.decode("utf-8")
    assert "Log in with Authentik" in page  # 登录按钮本身不受影响
    assert "authentik_invite_signup" not in page


def test_local_login_branch_ignores_invite_url(app, client, monkeypatch):
    """本地登录分支（OIDC 关闭）下，即使配置了邀请 URL 也不渲染——
    注册入口只在 Authentik 分支有意义。"""
    monkeypatch.setitem(app.config, "AUTHENTIK_OIDC_ENABLED", False)
    monkeypatch.setenv("AUTHENTIK_ENROLLMENT_INVITE_URL", INVITE_URL)
    rv = client.get("/login")
    assert rv.status_code == 200
    assert "authentik_invite_signup" not in rv.data.decode("utf-8")
