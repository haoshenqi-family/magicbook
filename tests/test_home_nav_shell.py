"""R213-A：首页导航与外壳（MB-16，非侧边栏分组部分）的接线面守卫。

与 test_reading_progress_wiring.py 同口径：这些是纯模板/CSS 改动，端到端
渲染性价比低，文本面守卫钉住「接线存在」；行为验收走 AC 文档的人工两档
视口检查（1440×900 / 390×844）。

 R251 起侧边栏分组有守卫；分组仍是展示层规则，不改 `ub.Shelf` schema。
"""

from pathlib import Path

from cps import ub

_ROOT = Path(__file__).resolve().parent.parent
_TEMPLATES = _ROOT / "cps" / "templates"
_CSS = _ROOT / "cps" / "static" / "css" / "style.css"
_SHELL_CSS = _ROOT / "cps" / "static" / "css" / "magicbook.css"


def test_sort_chips_have_text_labels():
    """QA §三.4：11 个纯图标 chips 必须带文字标签（tooltip 不算，悬停才可见）。"""
    html = (_TEMPLATES / "index.html").read_text(encoding="utf-8")
    assert 'class="chip-label"' in html, "chips 文字标签缺失"
    # 每个排序按钮都有 label（hot 页 2 个 + 常规页 8~10 个，至少 9 处）
    assert html.count('class="chip-label"') >= 9, (
        "chip-label 数量不足：有排序按钮没配文字"
    )


def test_sort_chips_collapse_into_drawer_on_mobile():
    html = (_TEMPLATES / "index.html").read_text(encoding="utf-8")
    assert "filter-toggle" in html, "窄屏「筛选与排序」抽屉开关缺失"
    assert 'data-target="#sort-chips"' in html
    css = _CSS.read_text(encoding="utf-8")
    assert ".filter-chips.collapse" in css, (
        "桌面端强制展开 collapse 的媒体查询缺失——chips 会在桌面被隐藏"
    )


def test_cover_format_badges_present():
    """R213-C 起卡片主体搬进共享宏：徽标断言落在宏上，index.html 只保留调用。

    Why 改断言位置而不是删断言：徽标是 R213-A 的验收项，它现在只有一份实现
    （`partials/_book_card.html`）——断言必须跟着实现走，否则「index.html 里搜
    不到徽标」会被误判成徽标丢了。
    """
    html = (_TEMPLATES / "index.html").read_text(encoding="utf-8")
    card = (_TEMPLATES / "partials" / "_book_card.html").read_text(encoding="utf-8")
    assert "_book_card.html" in html, "index.html 没有复用共享卡片宏"
    assert "cover-badge-format" in card, "主格式徽标（EPUB/PDF）缺失"
    assert "cover-badge-audio" in card, "音频徽标缺失"
    assert "main_format" in card
    css = _CSS.read_text(encoding="utf-8")
    assert ".cover-badge" in css


def test_mobile_bottom_nav_present():
    html = (_TEMPLATES / "layout.html").read_text(encoding="utf-8")
    assert "mb-bottom-nav" in html, "移动端底部导航缺失"
    assert html.count("mb-bottom-item") >= 3, "底部导航少于三个入口"
    assert "web.learning_page" in html, "学习入口缺失"
    css = _CSS.read_text(encoding="utf-8")
    assert ".mb-bottom-nav" in css


def test_r251_primary_domains_use_one_navigation_layer():
    """R251：五个一级域共享同一层主导航，不再混入 Settings 下拉。"""
    html = (_TEMPLATES / "layout.html").read_text(encoding="utf-8")
    css = _SHELL_CSS.read_text(encoding="utf-8")
    for anchor in ("top_home", "top_library", "top_learning", "top_me", "top_admin"):
        assert f'id="{anchor}"' in html, f"一级域入口缺失：{anchor}"
    assert html.index('id="top_home"') < html.index('id="top_mb_settings"')
    assert '.nav.navbar-nav:not(.navbar-right)' in css


def test_r251_shelf_groups_never_drop_a_shelf():
    """R251：侧栏可按展示规则分组，但必须渲染原始书架集合的每个入口。"""
    html = (_TEMPLATES / "layout.html").read_text(encoding="utf-8")
    for label in ('{{_(\'Shelves\')}}', '{{_(\'Levels\')}}', '{{_(\'Media\')}}'):
        assert label in html, f"侧栏分组标题缺失：{label}"
    # 兜底组必须显式排除已分组 id，避免规则重叠或后续调整时丢书架。
    assert "rejectattr('id', 'in', level_ids + media_ids)" in html


def test_r251_sidebar_groups_render_without_dropping_shelves(admin_client, ub_session):
    """真实渲染路径的守卫：分类规则可调整，但入口数量必须守恒。"""
    for shelf in ub_session.query(ub.Shelf).all():
        ub_session.delete(shelf)
    ub_session.add_all([
        ub.Shelf(name="阶1", is_public=1, user_id=1),
        ub.Shelf(name="TED", is_public=1, user_id=1),
        ub.Shelf(name="我的书架", is_public=0, user_id=1),
    ])
    ub_session.commit()

    rv = admin_client.get("/reading/settings")
    assert rv.status_code == 200
    html = rv.data.decode("utf-8")
    assert html.count('href="/shelf/') == 4, (
        "三个书架 + Create a Shelf 入口都应存在；少一个即分组丢入口"
    )
    for label in ("Levels", "Media", "Shelves"):
        assert label in html, f"侧栏分组标题未渲染：{label}"


def test_create_shelf_cut_fix():
    """QA §三.2：「创建书架」在 900px 视口被裁切——侧栏需可滚动。"""
    css = _CSS.read_text(encoding="utf-8")
    assert ".navigation" in css and "overflow-y: auto" in css, (
        "侧栏滚动容器缺失：书架多了「创建书架」仍会被推出视口"
    )


def test_search_merged_into_single_entry():
    """QA §三.5：搜索与高级搜索两个入口去重。

    高级搜索并入搜索框输入组（保留 id，onboarding 引导步骤选中它），
    左侧主导航里不得再有独立的高级搜索项。
    """
    html = (_TEMPLATES / "layout.html").read_text(encoding="utf-8")
    assert 'id="advanced_search"' in html, "onboarding 依赖的锚点丢了"
    # 主导航 <ul class="nav navbar-nav "> 里不应再出现 advanced_search 的 <li>
    nav_start = html.find('<ul class="nav navbar-nav ">')
    nav_end = html.find("</ul>", nav_start)
    main_nav = html[nav_start:nav_end]
    assert "advanced_search" not in main_nav, (
        "高级搜索仍作为独立主导航项存在，未去重"
    )
