"""R214 书籍详情：结构守卫 + 元数据判定单测（子项 A）。

Why: R214 核出的第一急点是「在线阅读」被误关在 role_admin() 门禁里（detail.html:80
     一个条件同时包住阅读入口与三个整本入口），R211 后普通读者详情页连阅读入口都没有。
     这类「模板条件块归属」回归不会 500、不会报错，只会静默少按钮——必须由结构断言
     钉住，且反向变异（把阅读入口移回 admin 块）必须报红。
"""
import datetime
import os
import re

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DETAIL = os.path.join(ROOT, "cps", "templates", "detail.html")

_IF_RE = re.compile(r"\{%-?\s*(if|else|elif|endif)\b")


def _read():
    with open(DETAIL, encoding="utf-8") as fh:
        return fh.read()


def _enclosing_conditions(src, marker):
    """取 marker 处所有外层 `{% if %}` 的条件文本（栈式扫描）。

    else/elif 不弹栈：断言只看「这一层的条件里有没有 role_admin」，
    分支取反不改变 admin 字样的存在性。
    """
    idx = src.find(marker)
    assert idx != -1, "模板里找不到标记 {0}".format(marker)
    stack = []
    for m in _IF_RE.finditer(src):
        if m.start() >= idx:
            break
        kind = m.group(1)
        if kind == "if":
            end = src.find("%}", m.end())
            stack.append(src[m.end():end])
        elif kind == "endif":
            if stack:
                stack.pop()
    return stack


def test_read_entry_gate_is_viewer_not_admin():
    """阅读入口（readbtn）的门禁链必须含 role_viewer、不得含 role_admin。

    反向变异：把阅读入口挪回 role_admin() 块 → 外层条件出现 role_admin → 报红。
    """
    gates = _enclosing_conditions(_read(), 'id="readbtn"')
    assert any("role_viewer" in g for g in gates), "阅读入口不在 role_viewer 门禁内: {0}".format(gates)
    assert not any("role_admin" in g for g in gates), "阅读入口仍被 role_admin 包住: {0}".format(gates)


def test_read_entry_dropdown_also_unadmin_gated():
    """多格式下拉形态的阅读入口（read-in-browser）同样不得被 admin 包住。"""
    gates = _enclosing_conditions(_read(), 'id="read-in-browser"')
    assert any("role_viewer" in g for g in gates)
    assert not any("role_admin" in g for g in gates)


def test_whole_book_buttons_admin_gated():
    """三个整本入口保持管理员专属（R214 拍板①）。"""
    for marker in ('id="whole-book-translate"', 'id="whole-book-tts"', "url_for('web.word_detail_batch_page'"):
        gates = _enclosing_conditions(_read(), marker)
        assert any("role_admin" in g for g in gates), "{0} 丢了 admin 门禁".format(marker)


def test_old_combined_gate_is_gone():
    """旧的 role_viewer() and current_user.role_admin() 合并门禁不得复活。"""
    assert "role_viewer() and current_user.role_admin()" not in _read()


# ---- 伪出版日判定（R214 元数据不伪造）------------------------------------
# cps.web 的 import 链需 app 初始化（test_book_import 同款教训），延迟 import。
@pytest.fixture
def webmod(app):
    import cps.web as web
    return web


def test_pubdate_near_timestamp_is_import_date(webmod):
    ts = datetime.datetime(2026, 10, 10, 9, 0, 0)
    assert webmod._pubdate_is_import_date(ts + datetime.timedelta(hours=3), ts) is True


def test_pubdate_far_from_timestamp_is_real(webmod):
    ts = datetime.datetime(2026, 10, 10, 9, 0, 0)
    assert webmod._pubdate_is_import_date(ts - datetime.timedelta(days=300), ts) is False


def test_pubdate_handles_tz_aware_and_missing(webmod):
    utc = datetime.timezone.utc
    ts = datetime.datetime(2026, 10, 10, 9, 0, tzinfo=utc)
    naive_same = datetime.datetime(2026, 10, 10, 9, 30)  # 混搭 tz 也不许炸
    assert webmod._pubdate_is_import_date(naive_same, ts) is True
    assert webmod._pubdate_is_import_date(None, ts) is False
    assert webmod._pubdate_is_import_date(ts, None) is False


def test_template_renders_imported_label_when_flagged():
    """模板在伪出版日分支显示「导入于」，不显示 Published。"""
    src = _read()
    assert "导入于" in src and "entry.pubdate_is_import_date" in src


# ---- 难度阶四级兜底（与 R213 共用解析器）---------------------------------
def test_difficulty_prefers_tag_then_shelf_then_series():
    from cps.reading_insight.difficulty import resolve_difficulty as r

    assert r(["英文分级", "阶2"], ["英文分级·阶5（6500–9000词）"], "书虫·第6级") == (2, "tag")
    assert r([], ["英文分级·阶5（6500–9000词）"], "书虫·第6级") == (5, "shelf")
    assert r([], ["书虫·牛津英汉双语读物"], "书虫·第6级") == (3, "series")
    assert r([], [], "") == (None, None)


def test_difficulty_series_map_is_annotated_as_series():
    """系列映射必须带 series 来源，UI 才能标注「粗映射」——不允许伪装成书目事实。"""
    from cps.reading_insight.difficulty import resolve_difficulty as r

    level, source = r([], [], "书虫·第1级")
    assert (level, source) == (1, "series")


def test_template_shows_unrated_when_no_difficulty():
    src = _read()
    assert "难度: 未分级" in src and "book-difficulty" in src


# ---- 视觉分层（QA §四：已加入书架 vs 加入书架 不可分辨）--------------------
def test_shelf_chip_distinguished_from_add_button():
    """已加入的书架必须是 chip（label shelf-chip），不是与「加入书架」同款 btn。"""
    src = _read()
    remove_zone = src[src.index('id="remove-from-shelves"'):src.index('id="shelf-action-errors"')]
    assert "shelf-chip" in remove_zone
    assert "btn btn-sm btn-default" not in remove_zone, "移除芯片又变回与加入按钮同款"


def test_admin_tools_grouped_and_gated():
    src = _read()
    assert "admin-tools" in src and "管理员工具" in src
