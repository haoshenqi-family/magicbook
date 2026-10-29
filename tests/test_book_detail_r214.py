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


def test_whole_book_entry_admin_gated():
    """整本入口（C 轮合并为单个「整本任务」按钮）仍只给管理员（R214 拍板①）。

    反向变异：把按钮挪出 role_admin 块 → 外层条件里没有 role_admin → 报红。
    """
    gates = _enclosing_conditions(_read(), 'id="whole-book-panel-open"')
    assert any("role_admin" in g for g in gates), \
        "整本任务按钮不在 role_admin 门禁内: {0}".format(gates)


PANEL = os.path.join(ROOT, "cps", "templates", "partials", "whole_book_panel.html")


def _read_panel():
    with open(PANEL, encoding="utf-8") as fh:
        return fh.read()


def test_whole_book_panel_has_three_kinds():
    """面板三 tab 齐全（翻译/朗读/详解），且 partial 真的被详情页引入。"""
    panel = _read_panel()
    for kind in ("translate", "tts", "wordDetail"):
        assert 'data-kind="%s"' % kind in panel, "面板缺 {0} tab".format(kind)
    assert "whole_book_panel.html" in _read(), "detail.html 没 include 面板"


def test_whole_book_progress_slot_is_full_detail_only():
    """R248：进度条 slot 只在完整详情页的整本任务区出现。"""
    gates = _enclosing_conditions(_read(), 'id="whole-book-progress-slot"')
    assert any("role_admin" in gate for gate in gates), \
        "进度条 slot 不在管理员门禁内: {0}".format(gates)
    assert any("is_xhr" in gate for gate in gates), \
        "进度条 slot 没有排除 XHR 书卡弹层: {0}".format(gates)


def test_whole_book_partial_is_not_rendered_in_xhr_fragment():
    """R248：书卡弹层不加载面板/进度条 partial，避免跨页进度条。"""
    src = _read()
    include_idx = src.index("partials/whole_book_panel.html")
    prefix = src[:include_idx]
    assert "current_user.role_admin() and not is_xhr" in prefix.rsplit("{% if ", 1)[-1]


def test_legacy_whole_book_buttons_are_gone():
    """旧的三个并列按钮不许回来：它们是「点一下就下单」的形态，面板存在的理由就是替代它。"""
    src = _read()
    for marker in ('id="whole-book-translate"', 'id="whole-book-tts"'):
        assert marker not in src, "{0} 复活了".format(marker)


def test_panel_promises_no_original_mutation():
    """「不修改原书文件」是拍板口径，面板上必须看得见——不许只在后端返回值里。"""
    assert "不修改原书文件" in _read_panel()


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


def test_panel_template_compiles_and_endpoints_exist(app):
    """面板模板能编译 + 所有 url_for 端点真实存在。

    Why 单独一条：include/url_for 写错 endpoint 不会在导入时报错，只在用户点开面板那一
    刻 500——详情页其余部分照常渲染，最容易被验收漏掉。
    """
    from flask import url_for

    with app.test_request_context("/book/1"):
        app.jinja_env.get_template("partials/whole_book_panel.html")
        for endpoint in ("web.whole_book_estimate",
                         "web.reading_translate_book",
                         "web.reading_translate_book_status",
                         "web.reading_tts_book_start",
                         "web.reading_tts_book_status",
                         "web.reading_word_detail_progress"):
            assert url_for(endpoint), endpoint
        assert url_for("web.word_detail_batch_page", book_id=1, book_format="epub")


def test_estimate_endpoint_is_admin_gated_and_read_only():
    """估算端点：admin 门禁 + 只读（不出现 start/publish 调用）。

    Why 钉源码：estimate 一旦顺手调了 start，面板就从「报价」变成「下单」。
    """
    path = os.path.join(ROOT, "cps", "routes", "book_detail.py")
    with open(path, encoding="utf-8") as fh:
        src = fh.read()
    start = src.index("def whole_book_estimate(")
    body = src[start:src.index("@web.route", start) if "@web.route" in src[start:] else len(src)]
    assert '_llm_task_admin_gate()' in body
    for forbidden in ("_start(", "publish(", ".start("):
        assert forbidden not in body, "估算端点出现了写操作: {0}".format(forbidden)


def test_panel_renders_for_a_real_entry(app):
    """真渲染一次：tojson / data-* 文案 / csrf 属性任一处写错，详情页就是 500。

    Why 不满足于「模板能编译」：Jinja 编译期看不到 `entry.whole_book_active` 的形态、
    也看不到 `|tojson` 在无该属性时静默输出 undefined——渲染一次才拦得住。
    """
    from flask import render_template

    class _Entry(object):
        id = 337
        reader_list = ["epub"]
        whole_book_active = {"translate": {"jobId": "j1", "status": "RUNNING",
                                           "total": 10, "done": 4}}

    with app.test_request_context("/book/337"):
        html = render_template("partials/whole_book_panel.html", entry=_Entry())

    assert "整本任务" in html
    assert 'id="whole-book-panel-open"' not in html      # 入口按钮在 detail.html，不在 partial
    assert "whole-book-active" in html
    assert "j1" in html, "活跃批次 JSON 没渲染出来"
    assert "不修改原书文件" in html


PANEL_JS = os.path.join(ROOT, "cps", "static", "js", "whole-book-panel.js")


def _read_panel_js():
    with open(PANEL_JS, encoding="utf-8") as fh:
        return fh.read()


def test_entry_button_does_not_use_bootstrap_data_api():
    """入口按钮自己绑定事件，不再用 data-toggle / data-target。

    Why：data-api 靠选择器找目标，找不到就静默空转；验收现场的实际形态是「点整本任务，
    整页被套进另一个弹层」。反向变异：把 data-toggle="modal" 加回去 → 报红。
    """
    src = _read()
    idx = src.index('id="whole-book-panel-open"')
    # 只截这一个标签（往后遇到 ">" 即止）：400 字窗口会吃进下一个按钮的 data-toggle="dropdown"
    snippet = src[src.rindex("<button", 0, idx):src.index(">", idx) + 1]
    assert "data-toggle" not in snippet, "入口按钮又退回 data-api 了"
    assert "data-target" not in snippet, "入口按钮又退回 data-api 了"


def test_entry_button_hidden_in_xhr_fragment():
    """XHR 片段里不下发面板骨架，开面板按钮必须一起收掉（靠 is_xhr 门禁）。"""
    gates = _enclosing_conditions(_read(), 'id="whole-book-panel-open"')
    assert any("is_xhr" in g for g in gates), \
        "书卡弹层（XHR 片段）里仍会渲染开面板按钮: {0}".format(gates)


def test_xhr_modal_entry_is_full_page_link():
    """R236：XHR 片段（书卡弹层）里的整本任务入口必须是跳完整详情页的普通 <a>。

    Why：`not is_xhr` 门禁把入口收进完整详情页后，UI 里没有普通左键可达的路径
         （书卡链接全被 data-toggle 弹层截走），管理员入口事实上不可达。弹层内
         改为同门禁的链接——同 URL 不带 X-Requested-With 头即渲染完整页。
         反向变异：删链接 / 挪出 admin 块 / 挂回 data-toggle → 报红。
    """
    src = _read()
    link_idx = src.index('id="whole-book-panel-link"')
    tag = src[src.rindex("<a", 0, link_idx):src.index(">", link_idx) + 1]
    assert "url_for('web.show_book'" in tag, "弹层入口没有指向完整详情页"
    assert "data-toggle" not in tag, "弹层入口不得走 data-api（与详情弹层抢点击）"
    assert "data-target" not in tag, "弹层入口不得走 data-api（与详情弹层抢点击）"
    gates = _enclosing_conditions(src, 'id="whole-book-panel-link"')
    assert any("role_admin" in g for g in gates), \
        "弹层整本任务入口不在 role_admin 门禁内: {0}".format(gates)
    assert any("is_xhr" in g for g in gates), \
        "弹层整本任务入口不在 is_xhr 分支内: {0}".format(gates)


def test_panel_open_is_bound_explicitly():
    """JS 里显式绑定入口按钮并阻止默认行为（含 preventDefault / stopPropagation）。"""
    js = _read_panel_js()
    assert "$('#whole-book-panel-open').on('click'" in js
    assert "preventDefault" in js
    assert "stopPropagation" in js


def test_start_label_keys_are_lowercase():
    """`start-<kind>` 文案键必须全小写：HTML 属性名会被解析器小写化。

    反向变异：把 JS 里的 toLowerCase() 去掉 → 详解 tab 的按钮文案变空（验收实测）。
    """
    panel = _read_panel()
    assert 'data-t-start-worddetail=' in panel
    assert 'data-t-start-wordDetail=' not in panel, "属性名带大写，解析后取不到"
    assert "toLowerCase()" in _read_panel_js()


def test_progress_title_names_task_and_status():
    """R246：进度条必须明确标出任务类型与状态，不能只剩百分比。

    Why：详解任务的 kind 是 camelCase `wordDetail`，但 HTML 属性名解析后是
         `data-t-progress-kind-worddetail`。进度标题若直接拼 `start-<kind>`，
         不仅会取空，还会把动作文案（「打开详解页面」）误当成任务名。
    反向变异：改回 `t('start-' + kind)` 或去掉 toLowerCase() → 报红。
    """
    panel = _read_panel()
    for kind, label in (("translate", "整本翻译"),
                        ("tts", "整本朗读"),
                        ("worddetail", "全文单词详解")):
        assert 'data-t-progress-kind-{0}="{1}"'.format(kind, label) in panel
    for status in ("running", "done", "failed", "cancelled"):
        assert 'data-t-progress-{0}="{{task}}'.format(status) in panel

    js = _read_panel_js()
    render = js[js.index("function renderProgress"):js.index("function stopPoll")]
    assert "t('progress-kind-' + String(kind).toLowerCase())" in render
    assert "t(statusKey, {task: taskLabel})" in render
    assert "|| kind" in render and "|| taskLabel" in render, "文案缺键时必须回退，不能再次留空"
    assert "t('start-' + kind)" not in render


def test_stalled_tts_batch_has_a_frontend_resume_entry():
    """R237 验收缺陷：容器重启杀掉 worker 后，页面必须能原地续跑。

    Why 钉三件事：状态接口下发 canResume；进度条有「继续」按钮；点击后调用
    retry 而不是 start（start 在活跃批次下被禁用，正是本次卡死的入口）。
    """
    panel = _read_panel()
    js = _read_panel_js()
    assert "wb-progress-resume" in panel
    assert "data-url-tts-retry" in panel
    assert "canResume" in js
    assert "cfg.urls.ttsRetry" in js
    assert "'#whole-book-progress .wb-progress-resume'" in js


def test_progress_bar_is_appended_to_detail_task_slot():
    """R248：进度条必须挂在详情页整本任务 slot，而不是全局导航下方。"""
    js = _read_panel_js()
    assert "$progress.appendTo($progressSlot)" in js
    assert "$('#whole-book-progress-slot')" in js
    assert "$progress.insertAfter($nav)" not in js
    assert "$('body > .navbar')" not in js


def test_progress_close_stays_collapsed_during_polling():
    """收起进度条后轮询不能把它重新弹出来，否则用户无法在详情页阅读。"""
    js = _read_panel_js()
    assert "progressCollapsed" in js
    assert "state.progressCollapsed = true" in js
    assert "if (!state.progressCollapsed)" in js


def test_estimate_route_reports_instead_of_bare_500():
    """估算路由必须有兜底：落 traceback 并把异常类型回给前端。

    Why：面板拿到裸 500 只会显示「估算失败：500 」，管理员无从判断是解析失败还是库挂了。
    """
    path = os.path.join(ROOT, "cps", "routes", "book_detail.py")
    with open(path, encoding="utf-8") as fh:
        src = fh.read()
    body = src[src.index("def whole_book_estimate("):]
    assert "except Exception as error" in body
    assert "traceback.format_exc()" in body
    assert "type(error).__name__" in body
