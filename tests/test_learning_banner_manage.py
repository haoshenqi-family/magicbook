"""R208：banner 管理抽屉与引导卡的前端静态契约。

Why 单独一份：勾选管理是「banner 只显示用户要的卡」的唯一入口，抽屉七个
复选框必须与功能卡一一对应（data-key 漂移 = 勾了存不上），引导卡是全不勾
的兜底回入口——都能在渲染产物上静态断言，不必等真机。i18n 判据与
test_learning_hub_cards 同口径：zh 取词下沉到编译产物 .mo。
"""
import gettext
import os
import re

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MO = os.path.join(ROOT, "cps", "translations", "zh_Hans_CN",
                  "LC_MESSAGES", "messages.mo")

# 顺序与 test_learning_hub_cards.CARDS 对齐：抽屉行序 = 卡片模板序（八卡含 story）
MANAGE_KEYS = ["writing", "speaking", "retell", "reread", "dictation",
               "review", "story", "match"]


@pytest.fixture
def hub_html(admin_client):
    response = admin_client.get("/learning")
    assert response.status_code == 200
    return response.data.decode("utf-8")


@pytest.fixture(scope="module")
def zh_catalog():
    with open(MO, "rb") as fh:
        return gettext.GNUTranslations(fh)


def test_drawer_renders_all_checkboxes_in_card_order(hub_html):
    keys = re.findall(r'<input type="checkbox" data-key="([a-z]+)" checked>', hub_html)
    assert keys == MANAGE_KEYS, "抽屉复选框与功能卡必须一一对应且顺序一致"

def test_drawer_and_gear_wired(hub_html):
    assert 'id="lh-manage"' in hub_html, "缺管理抽屉"
    assert 'id="lh-manage-btn"' in hub_html, "缺齿轮入口"
    assert 'aria-controls="lh-manage"' in hub_html, "齿轮未关联抽屉"
    assert 'id="lh-manage-save"' in hub_html and 'id="lh-manage-close"' in hub_html
    assert 'js/learning-hub.js' in hub_html


def test_drawer_defaults_all_checked(hub_html):
    """服务端渲染默认全勾=默认全显（未配置用户零变化）；真实勾选态由 JS 回填。"""
    start = hub_html.index('id="lh-manage"')
    end = hub_html.index('id="lh-manage-save"')
    assert hub_html[start:end].count(" checked") == len(MANAGE_KEYS), "抽屉出厂态应全勾"


def test_guide_card_renders_hidden(hub_html):
    assert re.search(r'<div id="lh-guide"[^>]*hidden', hub_html), "引导卡应默认隐藏"
    assert 'id="lh-guide-open"' in hub_html, "引导卡缺「选择功能」回入口"


def test_settings_url_injected_for_save(hub_html):
    assert re.search(r"settings:\s*\"/ajax/learning/plan/settings\"", hub_html), \
        "保存走 /ajax/learning/plan/settings，路由注入缺失会让保存静默打空"


def test_manage_copy_is_translated(zh_catalog):
    for msgid in ("Manage banner cards", "Choose activities",
                  "Could not save your selection — please retry.",
                  "Save", "Close"):
        got = zh_catalog.gettext(msgid)
        assert got != msgid, "「%s」在 .mo 里取不到中文（po 漏译或忘了 compile）" % msgid
