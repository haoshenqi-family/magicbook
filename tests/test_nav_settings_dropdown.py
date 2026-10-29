"""R102: 导航栏「设置 Settings」下拉框——magicbook 自有入口收纳与死链清理。

Why: magicbook 扩展入口（阅读设置/成就/积分/整本翻译）持续新增，导航栏平铺
放不下；且 /ai/admin 已随 agent 后端化退役（410），旧导航 AI 按钮是死链。
本测试锁定：下拉框渲染、入口按角色显隐、标签随 locale 单语言切换（R112）、
旧平铺项与死链不回流。
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


def test_help_dropdown_only_keeps_onboarding(settings_page):
    assert 'id="top_mb_settings"' in settings_page
    assert 'id="top_onboarding"' in settings_page
    for anchor in ("top_reading_settings", "top_achievements", "top_credits",
                   "top_buddy", "top_translate_all", "top_llm_tasks"):
        assert 'id="{0}"'.format(anchor) not in settings_page


def test_labels_single_language_for_en_admin(settings_page):
    # R112：标签走 Babel gettext，admin 账号 locale=en 只渲染英文 msgid；
    # 中文不得同时出现（防「中英双写」回流）。断言圈定在下拉框块内——
    # "Reading Settings" 也出现在 <title>，全文匹配是假信心
    block = _dropdown_block(settings_page)
    assert "Onboarding Tour" in block
    assert "使用引导" not in block


def test_labels_switch_to_chinese_for_zh_user(app):
    """R112：locale=zh_Hans_CN 的用户下拉框应显示中文词条（zh po 补齐后生效）。"""
    user = ub.session.query(ub.User).filter(ub.User.name == "zh-tester").first()
    if user is None:
        user = ub.User(name="zh-tester", email="zh@example.com",
                       password=generate_password_hash("zh-pass"))
        ub.session.add(user)
        ub.session.commit()
    user.locale = "zh_Hans_CN"
    ub.session.commit()

    client = app.test_client()
    rv = client.post("/login", data={"username": "zh-tester", "password": "zh-pass"})
    assert rv.status_code == 302

    from cps import config as cw_config
    cw_config.db_configured = True
    rv = client.get("/reading/settings")
    assert rv.status_code == 200
    block = _dropdown_block(rv.data.decode("utf-8"))
    assert "使用引导" in block
    assert "Onboarding Tour" not in block


def test_old_flat_entries_and_dead_link_removed(settings_page):
    # 旧 AI 导航按钮指向已退役的 /ai/admin（410），不得回流
    assert "top_ai_admin" not in settings_page
    # R251：账号/管理 L2 已迁出 Settings；这里只保留一次性引导入口。
    for anchor in ("top_reading_settings", "top_achievements", "top_credits",
                   "top_buddy", "top_translate_all", "top_llm_tasks"):
        assert settings_page.count('id="{0}"'.format(anchor)) == 0


def test_plain_user_sees_same_help_dropdown(app):
    """普通登录用户与管理员共享最小 Help 菜单，账号能力改走 L2 导航。"""
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
    assert 'id="top_onboarding"' in block
    assert "top_reading_settings" not in block
    assert "top_translate_all" not in block


def test_dropdown_hidden_for_anonymous(client):
    """匿名（未登录）不渲染下拉框。"""
    rv = client.get("/login")
    assert rv.status_code == 200
    assert "top_mb_settings" not in rv.data.decode("utf-8")


def test_learning_entries_are_top_level(settings_page):
    """R154：每日学习是一级使用入口，平铺在左侧主导航，不收进 Settings 下拉。

    R166：说与写并入每日学习中枢的功能 banner，一级项随之撤掉——这里同时锁
    「不回流」，防止后来者把它当漏项加回去。
    """
    assert settings_page.count('id="top_learning"') == 1
    assert "top_learning" not in _dropdown_block(settings_page)
    assert 'id="top_speaking_writing"' not in settings_page
