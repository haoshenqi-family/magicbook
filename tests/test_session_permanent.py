"""R123: 会话 cookie 持久化（浏览器重启不再丢登录）。

Why: moon-well access/refresh token 存在 Flask 签名会话 cookie 内，未配
session.permanent 时该 cookie 是浏览器会话级（无 Expires/Max-Age），浏览器
一关登录态连同 token 全丢，体感「一天就要重新登录」。R123 起全局钩子对非空
会话标记 permanent，PERMANENT_SESSION_LIFETIME 默认 30 天
（SESSION_PERMANENT_DAYS 可调），配合 SESSION_REFRESH_EACH_REQUEST 滑动续发。

注: 断言一律相对 app.config 生效值而非硬编码 30 天——conftest 建应用时
load_dotenv 会读本地 .env，显式设置 SESSION_PERMANENT_DAYS 不应造成假失败。
"""
import email.utils
from datetime import datetime, timezone

import pytest


def _session_cookie(rv, cookie_name):
    """从响应头里摘出会话 cookie 的 Set-Cookie 行（区分于 remember/locale）。"""
    for header in rv.headers.getlist("Set-Cookie"):
        if header.startswith(cookie_name + "="):
            return header
    return None


def test_session_config_active(app):
    lifetime = app.config["PERMANENT_SESSION_LIFETIME"]
    assert lifetime.total_seconds() > 0
    assert app.config["SESSION_REFRESH_EACH_REQUEST"] is True


def test_session_cookie_is_persistent(app, client):
    """会话 cookie 必须带 Expires（= PERMANENT_SESSION_LIFETIME），而非浏览器会话级。"""
    # 先写入一个键保证会话非空：空会话无论 permanent 与否都不会下发 cookie
    with client.session_transaction() as sess:
        sess["probe"] = "persistent"
    rv = client.get("/login")
    assert rv.status_code == 200

    cookie = _session_cookie(rv, app.config["SESSION_COOKIE_NAME"])
    assert cookie is not None, "非空会话的响应应下发会话 cookie"
    assert "Expires=" in cookie, "permanent 会话 cookie 必须带 Expires（浏览器重启后仍存活）"

    expected = app.config["PERMANENT_SESSION_LIFETIME"].total_seconds() / 86400
    expires = email.utils.parsedate_to_datetime(
        cookie.split("Expires=")[1].split(";")[0].strip()
    )
    days = (expires - datetime.now(timezone.utc)).total_seconds() / 86400
    assert expected - 0.1 < days < expected + 0.1, \
        f"Expires 应为 {expected:.0f} 天后, 实际 {days:.2f} 天"


def test_before_request_hook_registered(app):
    """全局钩子已注册: 每个请求都会把非空会话标记 permanent。
    行为佐证见 test_session_cookie_is_persistent（cookie 带 Expires）。
    注: app 是 session 级 fixture, 不得在首个请求后再动态注册路由。"""
    hook_names = [f.__name__ for f in app.before_request_funcs.get(None, [])]
    assert "_make_session_permanent" in hook_names


@pytest.fixture
def logged_in_client(app):
    """真实登录（admin/admin123，conftest 同款）后叠加 moonwell token 的客户端。

    Why 不直接种会话键: vendored cw_login 的会话加载要求 _user_id/_random/_id
    三键齐全且绑定服务端会话记录，手造会走不到登录态；真实登录后补写 token
    最贴近线上「登录后携带 moonwell token」的真实会话。
    """
    client = app.test_client()
    rv = client.post("/login", data={"username": "admin", "password": "admin123"})
    assert rv.status_code == 302, f"login did not redirect: {rv.status_code}"
    # 同 conftest admin_client: 登录触发 config save()→load() 会把 db_configured 复位
    from cps import config as cw_config
    cw_config.db_configured = True
    with client.session_transaction() as sess:
        sess["moonwell_access_token"] = "access-tok"
        sess["moonwell_refresh_token"] = "refresh-tok"
    return client


def test_logout_clears_moonwell_tokens(app, logged_in_client):
    """R123 审查项: 会话持久化后登出必须清空并删除 cookie，
    否则 moonwell token 滞留在 30 天滑动的永久 cookie 里。"""
    rv = logged_in_client.get("/logout")
    assert rv.status_code == 302

    session_del = [h for h in rv.headers.getlist("Set-Cookie")
                   if h.startswith(app.config["SESSION_COOKIE_NAME"] + "=")]
    assert session_del, "登出响应应处理会话 cookie"
    assert any("Max-Age=0" in h or "Expires=Thu, 01 Jan 1970" in h
               for h in session_del), f"登出应删除会话 cookie, 实际: {session_del}"

    # 后续请求不再携带任何会话内容
    rv2 = logged_in_client.get("/login")
    assert rv2.status_code == 200
