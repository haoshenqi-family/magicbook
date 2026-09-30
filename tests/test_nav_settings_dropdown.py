"""R102: 导航栏「设置 Settings」下拉框——magicbook 自有入口收纳与死链清理。

Why: magicbook 扩展入口（阅读设置/成就/积分/整本翻译）持续新增，导航栏平铺
放不下；且 /ai/admin 已随 agent 后端化退役（410），旧导航 AI 按钮是死链。
本测试锁定：下拉框渲染、入口按角色显隐、双语标签、旧平铺项与死链不回流。
"""
import re

import pytest
from werkzeug.security import generate_password_hash

from cps import constants, ub


@pytest.fixture
def settings_page(admin_client):
    """Why: /reading/settings 无需 calibre 书库（moon-well 不可达时走 load_error
    分支照常渲染 layout），是测试环境里最稳的 layout 载体页。"""
    rv = admin_client.get("/reading/settings")
    assert rv.status_code == 200
    return rv.data.decode("utf-8")


def _dropdown_block(page):
    """圈定下拉框块文本，避免断言被页面其他区域（如 <title>）误满足。"""
    m = re.search(r'<li class="dropdown" id="top_mb_settings">.*?</ul>\s*</li>',
                  page, re.S)
    assert m, "下拉框 #top_mb_settings 未渲染"
    return m.group(0)


def test_dropdown_present_with_all_admin_entries(settings_page):
    assert 'id="top_mb_settings"' in settings_page
    for anchor in ("top_reading_settings", "top_achievements",
                   "top_credits", "top_translate_all"):
        assert 'id="{0}"'.format(anchor) in settings_page


def test_bilingual_labels(settings_page):
    # 中文为主 + 英文辅助，双写不依赖账号 locale（admin 账号 locale=en）；
    # 断言圈定在下拉框块内——"Reading Settings" 也出现在 <title>，全文匹配是假信心
    block = _dropdown_block(settings_page)
    assert "阅读设置" in block and "Reading Settings" in block
    assert "整本翻译" in block and "Book Translation" in block


def test_old_flat_entries_and_dead_link_removed(settings_page):
    # 旧 AI 导航按钮指向已退役的 /ai/admin（410），不得回流
    assert "top_ai_admin" not in settings_page
    # 平铺入口已收进下拉框，每个入口 id 全页只出现一次
    for anchor in ("top_reading_settings", "top_achievements", "top_credits"):
        assert settings_page.count('id="{0}"'.format(anchor)) == 1


def test_plain_user_sees_dropdown_without_admin_entries(app):
    """普通登录用户：下拉框与三个用户入口可见，admin 专属整本翻译隐藏。"""
    user = ub.session.query(ub.User).filter(ub.User.name == "plain-tester").first()
    if user is None:
        user = ub.User(name="plain-tester", email="plain@example.com",
                       password=generate_password_hash("plain-pass"))
        ub.session.add(user)
        ub.session.commit()
    assert not user.role_admin()

    client = app.test_client()
    rv = client.post("/login", data={"username": "plain-tester",
                                     "password": "plain-pass"})
    assert rv.status_code == 302

    from cps import config as cw_config
    cw_config.db_configured = True
    rv = client.get("/reading/settings")
    assert rv.status_code == 200
    block = _dropdown_block(rv.data.decode("utf-8"))
    for anchor in ("top_reading_settings", "top_achievements", "top_credits"):
        assert 'id="{0}"'.format(anchor) in block
    assert "top_translate_all" not in block
    assert "divider" not in block


def test_dropdown_hidden_for_anonymous(client):
    """匿名（未登录）不渲染下拉框。"""
    rv = client.get("/login")
    assert rv.status_code == 200
    assert "top_mb_settings" not in rv.data.decode("utf-8")
