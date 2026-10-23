"""R166：每日学习中枢的功能 banner 卡片契约。

Why 单独一份：banner 是「八个学习功能」的唯一入口，卡片文案/配图/链接三样
只要有一样对不上（改了路由忘了改卡、图路径打错、描述漏译），页面照样 200、
点进去才发现 404 或英文串。这些都能在渲染产物上静态断言，不必等真机。

zh 无缺串的判据下沉到编译产物 .mo（vocab-size-test AC-C8 同口径）：po 改了
忘了 pybabel compile 是最典型的「看起来完好、运行时英文」失效。
"""
import gettext
import os
import re

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG_DIR = os.path.join(ROOT, "cps", "static", "img", "learning")
MO = os.path.join(ROOT, "cps", "translations", "zh_Hans_CN",
                  "LC_MESSAGES", "messages.mo")

# (data-key, 标题 msgid, 端点, 归属股)；股别 'none' = 不占四股（选书是决策不是练习）
CARDS = [
    ("writing", "Writing Workshop", "web.learning_writing_page", "output"),
    ("speaking", "AI Speaking Coach", "web.learning_speaking_page", "output"),
    ("retell", "Retell Drill (4-3-2)", "web.learning_retell_page", "output"),
    ("reread", "Timed rereading", "web.learning_reread_page", "fluency"),
    ("dictation", "Dictation", "web.learning_dictation_page", "language"),
    ("review", "Review Queue", "web.learning_review_page", "language"),
    ("story", "Word Story", "web.learning_story_page", "language"),
    ("match", "Book Difficulty Match", "web.learning_match_page", "none"),
]


@pytest.fixture
def hub_html(admin_client):
    response = admin_client.get("/learning")
    assert response.status_code == 200
    return response.data.decode("utf-8")


@pytest.fixture(scope="module")
def zh_catalog():
    with open(MO, "rb") as fh:
        return gettext.GNUTranslations(fh)


def _card_block(html, key):
    m = re.search(r'<a class="lh-card[^"]*"[^>]*data-key="%s".*?</a>' % key,
                  html, re.S)
    assert m, "banner 缺卡片 data-key=%s" % key
    return m.group(0)


def test_all_cards_render_in_order(hub_html):
    # R208 起 data-key 也出现在管理抽屉的复选框上，锚定 <a class="lh-card"> 只数功能卡；
    # 顺序契约本身不变（卡片顺序即用户指定的展示顺序，八卡含 story）。
    keys = re.findall(r'<a class="lh-card[^"]*"[^>]*data-key="([a-z]+)"', hub_html)
    assert keys == [c[0] for c in CARDS], "卡片顺序即用户指定的展示顺序，不得漂成别的"


@pytest.mark.parametrize("key,title,endpoint,strand", CARDS,
                         ids=[c[0] for c in CARDS])
def test_card_has_title_image_description_and_link(hub_html, key, title, endpoint,
                                                   strand):
    block = _card_block(hub_html, key)
    assert title in block, "%s 卡缺标题" % key
    assert 'img/learning/%s.webp' % key in block, "%s 卡配图路径与 data-key 不一致" % key
    assert "lh-card-desc" in block and len(block.split('class="lh-card-desc">')[1]) > 80, \
        "%s 卡描述太短，起不到「进子页面前先讲清楚」的作用" % key
    assert 'data-strand="%s"' % strand in block, "%s 卡股别漂移" % key
    assert 'href="' in block, "%s 卡没有链接" % key


@pytest.mark.parametrize("key,title,endpoint,strand", CARDS,
                         ids=[c[0] for c in CARDS])
def test_card_links_resolve_to_real_routes(admin_client, key, title, endpoint, strand):
    """卡片 href 必须是真实路由：写死路径的卡会在改路由后静默 404。"""
    from flask import url_for
    with admin_client.application.test_request_context():
        href = url_for(endpoint)
    html = admin_client.get("/learning").data.decode("utf-8")
    assert 'href="%s"' % href in _card_block(html, key), "%s 卡链接与路由表不符" % key
    assert admin_client.get(href).status_code == 200, "%s 卡指向 %s 打不开" % (key, href)


@pytest.mark.parametrize("key,title,endpoint,strand", CARDS,
                         ids=[c[0] for c in CARDS])
def test_card_image_file_exists(key, title, endpoint, strand):
    path = os.path.join(IMG_DIR, key + ".webp")
    assert os.path.isfile(path), "缺配图 %s" % path
    assert os.path.getsize(path) < 200 * 1024, "%s 图过大（banner 七张要控总量）" % key


def test_banner_wires_carousel_controls(hub_html):
    for anchor in ("lh-banner", "lh-dots", "lh-prev", "lh-next"):
        assert 'id="%s"' % anchor in hub_html, "轮播缺 %s" % anchor
    assert 'js/learning-hub.js' in hub_html


def test_hub_no_longer_hosts_queue_and_match_panels(hub_html):
    """迁走即删：中枢留着旧面板会出现两处入口、两份 DOM 漂移。"""
    assert 'id="ln-card"' not in hub_html
    assert 'id="ln-match-root"' not in hub_html


def test_old_speaking_writing_url_redirects_to_hub(admin_client):
    response = admin_client.get("/learning/speaking-writing")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/learning")


def test_banner_copy_is_translated(hub_html, zh_catalog):
    """七段描述 + 股别行必须能在 .mo 里取到中文（漏译=中文用户看英文长段）。"""
    msgids = set(re.findall(r'class="lh-card-(?:title|desc|meta)">([^<]+)</', hub_html))
    assert len(msgids) >= 24, "卡片文案数量异常：%d" % len(msgids)
    untranslated = []
    for msg in msgids:
        text = msg.replace("&amp;", "&").replace("&#39;", "'")
        got = zh_catalog.gettext(text)
        if got == text and not any("\u4e00" <= ch <= "\u9fff" for ch in text):
            untranslated.append(text[:60])
    assert not untranslated, "以下卡片文案在 .mo 里取不到中文（po 漏译或忘了 compile）：%r" \
        % untranslated
