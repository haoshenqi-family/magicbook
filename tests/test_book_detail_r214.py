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


# ---- 内容速览 B：简介三级回退 / 目录 / 试读 ------------------------------
def test_ai_summary_badge_required():
    """AI 简介必须带「由 AI 生成」标注（拍板④）——标注被删要报红，不许冒充书目简介。"""
    assert "由 AI 生成" in _read()


def test_summary_three_level_fallback_structure():
    """简介三级回退顺序：书目 comments → insight.aiSummary → 暂无简介（指向目录/试读）。"""
    src = _read()
    comments_at = src.index("entry.comments|length > 0")
    ai_at = src.index("aiSummary")
    fallback_at = src.index("no-description")
    assert comments_at < ai_at < fallback_at, "三级回退顺序被打乱"
    assert "首章试读" in src and "暂无简介" in src


def test_generate_summary_button_admin_gated():
    """「生成简介」按钮仅管理员（拍板①同源）；挪出 admin 块 → 报红。"""
    gates = _enclosing_conditions(_read(), 'id="generate-book-summary"')
    assert any("role_admin" in g for g in gates), "生成简介按钮不在 role_admin 门禁内: {0}".format(gates)


def test_no_regenerate_button():
    """拍板⑦：AI 简介无「重新生成」按钮——模板（剥掉 Jinja 注释后）不许出现该字样。

    Why 剥注释：设计注释里合理提到「无重新生成按钮」，A 轮「全文单词详解」同款
    误伤（标记文字出现在注释里被误判）；守卫要看的是可渲染内容。
    """
    src = re.sub(r"\{#.*?#\}", "", _read(), flags=re.S)
    assert "重新生成" not in src


def test_toc_and_preview_blocks_present():
    src = _read()
    assert "book-toc" in src and "toc-expand" in src
    assert "book-preview" in src and "继续阅读" in src
    assert "entry.insight.chapters" in src and "entry.insight.excerpt" in src


def test_book_insight_js_included():
    assert 'filename=\'js/book-insight.js\'' in _read()


def test_insight_error_is_visible_not_silent():
    """解析失败要在页面上可见（LLD §8 禁止静默降级）——警示块不得被删。"""
    src = _read()
    assert "book-insight-error" in src and "entry.insight_error" in src
# ---- 缺陷修复（子项 A 验收）：书架名解析吃到了 shelf id → /book/<id> 整页 500 --
SHELF_LEVEL_NAME = "英文分级·阶5（6500–9000词）"
WEB = os.path.join(ROOT, "cps", "web.py")


def _read_web():
    with open(WEB, encoding="utf-8") as fh:
        return fh.read()


@pytest.fixture
def shelf_rows(app):
    """真 ORM 造一个「阶N」书架 + 一条书-书架关联，用例后拆除。"""
    from cps import ub
    admin = ub.session.query(ub.User).filter(ub.User.name == "admin").one()
    shelf = ub.Shelf(name=SHELF_LEVEL_NAME, user_id=admin.id)
    ub.session.add(shelf)
    ub.session.commit()
    link = ub.BookShelf(book_id=900001)
    # 必须经关系挂载：ub.py 的 before_flush 钩子要写 change.ub_shelf.last_modified，
    # 只填外键列会让 backref 停在 None，commit 直接抛 AttributeError。
    shelf.books.append(link)
    ub.session.commit()
    yield shelf, link
    ub.session.delete(link)
    ub.session.delete(shelf)
    ub.session.commit()


def test_shelf_names_converts_ids_to_names(webmod, shelf_rows):
    """入参是 id、出参必须是名称——原缺陷正是拿 id 当对象取 `.name`。"""
    assert webmod._shelf_names_for_book([shelf_rows[1].shelf]) == [SHELF_LEVEL_NAME]


def test_shelf_names_empty_for_unshelved_book(webmod):
    """不在任何书架的书：空 id 列表直接回空，不发 SQL、不抛错（这条路径原本没炸，
    所以「有的书能打开、有的 500」——必须钉住空集行为）。"""
    assert webmod._shelf_names_for_book([]) == []


def test_difficulty_resolves_from_shelf_name_chain(webmod, shelf_rows):
    """接线口径：id → 名 → 解析器，「阶5」书架要解析成 (5, "shelf")。"""
    from cps.reading_insight.difficulty import resolve_difficulty
    names = webmod._shelf_names_for_book([shelf_rows[1].shelf])
    assert resolve_difficulty([], names, "") == (5, "shelf")


def test_show_book_wiring_uses_shelf_name_helper():
    """调用点守卫：show_book 的 shelf_names 必须走 _shelf_names_for_book。

    Why: 上三条只证明「转换器 + 解析器各自正确」，而 500 出在调用点把 id 列表
         当对象列表用——参数形制在调用点错位，只有钉住调用点源码才拦得住。
         反向变异：把该行换回 `[s.name for s in book_in_shelves]` 必须报红。
    """
    src = _read_web()
    m = re.search(r"def show_book\(.+?(?=\n@web\.route|\ndef |\Z)", src, re.S)
    assert m, "web.py 里找不到 show_book 函数体"
    body = m.group(0)
    assert "shelf_names=_shelf_names_for_book(book_in_shelves)" in body
    assert "[s.name for s in book_in_shelves]" not in src


# ---- 弹窗失败可见性（同一缺陷的第二半：500 不得静默成「这本书没详情」）--------
LAYOUT = os.path.join(ROOT, "cps", "templates", "layout.html")
MAIN_JS = os.path.join(ROOT, "cps", "static", "js", "main.js")


def _details_modal_handler():
    with open(MAIN_JS, encoding="utf-8") as fh:
        js = fh.read()
    start = js.index('$("#bookDetailsModal")')
    return js[start:js.index('$("#modal_kobo_token")')]


def test_details_modal_has_visible_failure_state():
    """模板预置失败节点 + JS 有 .fail 分支把它显示出来。

    Why: 弹窗正文靠 AJAX 填充，原先只挂 `.done()`——`/book/<id>` 一 500 就停在
         模板占位符字面量 "..."，把接口故障伪装成「这本书没有详情」，用户报回来的
         永远是「我的书打不开」。ops 准则⑦点名的正是这种静默降级。
    """
    with open(LAYOUT, encoding="utf-8") as fh:
        layout = fh.read()
    assert 'class="alert alert-danger book-details-error"' in layout
    assert "_('Failed to load')" in layout, "失败文案必须走 _()，不许硬编码中文/英文"
    handler = _details_modal_handler()
    assert ".fail(function" in handler, "详情弹窗 AJAX 没有失败分支"
    assert "$loadError.show()" in handler


def test_details_modal_fail_branch_releases_prefilter():
    """失败分支必须同样摘掉 useCache preFilter，否则它永久挂在 jQuery 上。"""
    handler = _details_modal_handler()
    assert handler.count("preFilters.remove(useCache)") == 2, "成功/失败两条路径各摘一次"
