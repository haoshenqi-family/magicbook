"""R109: 前端引导模式（onboarding tour）挂载点与状态契约。

Why: 引导模式刻意做成「零 Python 改动」——状态复用既有 POST /ajax/view 写进
     User.view_settings['onboarding']，读取直接在模板里取 current_user.view_settings。
     这两个都是间接依赖：上游一改，引导就静默失效（要么页面 500，要么永远邀请）。
     本测试锁住：挂载点存在且不重复、三种 view_settings 形态都能渲染、
     手动入口随角色显隐、以及 /ajax/view 这条写入通道对本用例确实可用。
"""
import json
import os
import re

import pytest
from werkzeug.security import generate_password_hash

from cps import ub

TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cps", "templates")


@pytest.fixture
def settings_page(admin_client):
    """Why: /reading/settings 无需 calibre 书库，是测试环境里最稳的 layout 载体页
    （沿用 tests/test_nav_settings_dropdown.py 的姿势）。"""
    rv = admin_client.get("/reading/settings")
    assert rv.status_code == 200
    return rv.data.decode("utf-8")


@pytest.fixture
def tour_user(app):
    """独立账号，避免与并行用例争用同一 view_settings。"""
    user = ub.session.query(ub.User).filter(ub.User.name == "tour-tester").first()
    if user is None:
        user = ub.User(name="tour-tester", email="tour@example.com",
                       password=generate_password_hash("tour-pass"))
        ub.session.add(user)
        ub.session.commit()
    user.view_settings = {}
    ub.session.commit()

    client = app.test_client()
    rv = client.post("/login", data={"username": "tour-tester", "password": "tour-pass"})
    assert rv.status_code == 302
    from cps import config as cw_config
    cw_config.db_configured = True
    return client


def _dropdown_block(page):
    m = re.search(r'<li class="dropdown" id="top_mb_settings">.*?</li>\s*</ul>\s*</li>', page, re.S)
    assert m, "下拉框 #top_mb_settings 未渲染"
    return m.group(0)


def _seen_of(page):
    """取模板注入的 window.MagicbookOnboarding.seen 种子值。"""
    m = re.search(r"seen: (\{.*?\}),", page, re.S)
    assert m, "MagicbookOnboarding.seen 种子未渲染"
    return json.loads(m.group(1))


def test_mount_present_once(settings_page):
    assert settings_page.count('css/onboarding.css') == 1
    assert settings_page.count('js/onboarding.js') == 1
    assert "window.MagicbookOnboarding" in settings_page
    # 挂载点在 jQuery 之后：否则 onboarding.js 里的 $ 未定义
    assert settings_page.index("js/libs/jquery.min.js") < settings_page.index("js/onboarding.js")


def test_seen_seed_false_for_fresh_user(tour_user):
    rv = tour_user.get("/reading/settings")
    assert rv.status_code == 200
    assert _seen_of(rv.data.decode("utf-8")) == {}


def test_seen_seed_reflects_view_settings(tour_user):
    """服务端状态是权威：写入 onboarding.main 后种子必须带过来（跨设备记忆的前提）。"""
    user = ub.session.query(ub.User).filter(ub.User.name == "tour-tester").first()
    user.view_settings = {"onboarding": {"main": True, "reader": False}}
    ub.session.commit()

    rv = tour_user.get("/reading/settings")
    seen = _seen_of(rv.data.decode("utf-8"))
    assert seen.get("main") is True
    assert seen.get("reader") is False


def test_null_view_settings_renders(tour_user):
    """view_settings 为 NULL（老账号/列空）不能抛 UndefinedError。"""
    user = ub.session.query(ub.User).filter(ub.User.name == "tour-tester").first()
    user.view_settings = None
    ub.session.commit()

    rv = tour_user.get("/reading/settings")
    assert rv.status_code == 200
    assert _seen_of(rv.data.decode("utf-8")) == {}


def test_anonymous_seed_is_marked_and_page_ok(client):
    """匿名（current_user 无 view_settings 属性）：页面必须正常渲染，
    且 anonymous:true 让前端知道只能用 localStorage，不能写共享的匿名用户行。"""
    rv = client.get("/login")
    assert rv.status_code == 200
    page = rv.data.decode("utf-8")
    assert "anonymous: true" in page
    assert _seen_of(page) == {}


def test_manual_entry_bilingual_and_role_scoped(settings_page):
    block = _dropdown_block(settings_page)
    assert 'id="top_onboarding"' in block
    # 中文为主 + 英文辅助双写（R102 惯例），不走 Babel
    assert "使用引导" in block and "Onboarding Tour" in block
    assert settings_page.count('id="top_onboarding"') == 1


def test_manual_entry_hidden_for_anonymous(client):
    rv = client.get("/login")
    assert "top_onboarding" not in rv.data.decode("utf-8")


def test_state_write_reuses_ajax_view_channel(tour_user):
    """锁住外部契约：/ajax/view 必须能落 onboarding 命名空间，否则「零 Python 改动」
    的前提消失（引导会在每台设备每次访问都重弹邀请卡）。"""
    page = tour_user.get("/reading/settings").data.decode("utf-8")
    token = re.search(r'name="csrf_token" value="([^"]+)"', page).group(1)

    rv = tour_user.post("/ajax/view",
                       data=json.dumps({"onboarding": {"main": True, "reader": True}}),
                       content_type="application/json",
                       headers={"X-CSRFToken": token})
    assert rv.status_code == 200

    user = ub.session.query(ub.User).filter(ub.User.name == "tour-tester").first()
    ub.session.expire(user)
    assert user.view_settings["onboarding"] == {"main": True, "reader": True}


def test_reader_page_mounts_tour():
    """read.html 独立于 layout，必须自带挂载点（先例：ai_chat_panel.html 的 include）。"""
    with open(os.path.join(TEMPLATE_DIR, "read.html"), encoding="utf-8") as fh:
        src = fh.read()
    assert "onboarding_mount.html" in src
    # 必须在 jQuery 之后
    assert src.index("js/libs/jquery.min.js") < src.index("onboarding_mount.html")


def test_reader_step_anchors_exist_in_template():
    """导览步骤表指向的阅读器控件不得改名失联（尤其 AI 伴读入口）。"""
    with open(os.path.join(TEMPLATE_DIR, "read.html"), encoding="utf-8") as fh:
        src = fh.read()
    for anchor in ('id="show-Toc"', 'id="next"', 'id="setting"',
                   'id="immersive-translate"', 'id="bookmark"', 'id="fullscreen"'):
        assert anchor in src, "{0} 已从阅读器模板消失，需同步 onboarding.js".format(anchor)

    with open(os.path.join(TEMPLATE_DIR, "ai_chat_panel.html"), encoding="utf-8") as fh:
        assert 'id="ai-companion-fab"' in fh.read()


def test_browse_step_anchors_exist_in_templates():
    with open(os.path.join(TEMPLATE_DIR, "layout.html"), encoding="utf-8") as fh:
        src = fh.read()
    for anchor in ('id="query"', 'id="advanced_search"', 'id="scnd-nav"'):
        assert anchor in src, "{0} 已从 layout 消失，需同步 onboarding.js".format(anchor)

    # index.html 同时服务首页（discover）与各浏览页；封面与排序条是导览锚点
    with open(os.path.join(TEMPLATE_DIR, "index.html"), encoding="utf-8") as fh:
        src = fh.read()
    for anchor in ('class="col-sm-3 col-lg-2 col-xs-6 book session', 'class="filterheader'):
        assert anchor in src

    with open(os.path.join(TEMPLATE_DIR, "detail.html"), encoding="utf-8") as fh:
        src = fh.read()
    for anchor in ('id="detailcover"', 'id="btnGroupDrop1"', 'id="shelf-actions"',
                   'id="have_read_cb"', 'id="read-in-browser"', 'id="readbtn"'):
        assert anchor in src
