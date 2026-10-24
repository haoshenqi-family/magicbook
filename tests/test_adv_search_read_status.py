"""高级搜索「阅读状态」的语义与呈现（R213-A / PJM MB-16）。

背景：这个下拉原样继承自 Calibre-Web，取值是布尔三态的直译
（Any / Empty / Yes / No → 任何 / 空 / 确认 / 没有），在中文语境里
不可理解；且「空」与「没有」在未配置自定义阅读列时落到**同一个**
SQL 条件，等于给了两个名字不同、行为相同的选项。

这里钉两件事：
1. 界面上只出现互斥且穷尽的三态（未读 / 在读 / 已读）+ 说明文字；
2. 三种取值生成的筛选条件确实不同，`unread` 必须能命中「没有任何
   ReadBook 记录」的书（等值匹配会把它们全漏掉）。
"""
import gettext
import os

import pytest

from cps import search, ub

_TEMPLATE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                         "cps", "templates", "search_form.html")
_MO = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "cps", "translations", "zh_Hans_CN", "LC_MESSAGES", "messages.mo")


class _StubUser:
    id = 1


def _template_source():
    with open(_TEMPLATE, encoding="utf-8") as handle:
        return handle.read()


def _expr(value, monkeypatch, app):
    """生成某个取值对应的 SQL 表达式（不进 DB，只看条件结构）。

    必须带 literal_binds：否则各自命名相同的绑定参数会让三种状态编译出
    一模一样的字符串，断言就失去意义。
    """
    monkeypatch.setattr(search, "current_user", _StubUser())
    with app.app_context():
        cond = search.adv_search_read_status(value)
        return str(cond.compile(compile_kwargs={"literal_binds": True}))


# ---------------------------------------------------------------------------
# 界面：中文措辞
# ---------------------------------------------------------------------------
def test_advanced_search_form_uses_plain_chinese_states():
    src = _template_source()

    # 三个明确状态 + 「不限」
    for value in ('value="unread"', 'value="in_progress"', 'value="finished"', 'value="Any"'):
        assert value in src, "缺少状态选项 %s" % value

    # 提供一句说明兜住边界，避免「未读」被理解成「没读完」
    assert "never opened" in src and "opened but not finished" in src


def test_advanced_search_form_drops_unreadable_translations():
    src = _template_source()
    read_status_block = src.split('id="read_status"')[1].split("</select>")[0]

    # 旧直译的三个词条（Yes/No/Empty → 确认/没有/空）不应再出现在这个下拉里。
    # 注意只断言 msgid：value="True"/"False" 在「自定义阅读列」分支里仍是合法值，
    # 那里只是一个布尔字段的是/否，措辞已换成 Set to yes/no。
    for msgid in ("_('Empty')", "_('Yes')", "_('No')"):
        assert msgid not in read_status_block, "下拉里仍有直译词条 %s" % msgid


def test_chinese_catalog_has_the_new_labels():
    """词条必须真的编译进 .mo——只写 .po 不编译，页面仍是英文。"""
    with open(_MO, "rb") as handle:
        catalog = gettext.GNUTranslations(handle)

    assert catalog.gettext("Reading Status") == "阅读状态"
    assert catalog.gettext("Unread") == "未读"
    assert catalog.gettext("In progress") == "在读"
    # 「未设置」是 R216 /me 偏好页已有的同名词条，两处共用一个 msgid，
    # 这里断言它仍在——重复追加会让 .po 出现同 id 两条（后者静默覆盖前者）。
    assert catalog.gettext("Not set") == "未设置"


# ---------------------------------------------------------------------------
# 语义：三种状态互斥且穷尽
# ---------------------------------------------------------------------------
def test_three_states_produce_distinct_filters(app, monkeypatch):
    finished = _expr("finished", monkeypatch, app)
    in_progress = _expr("in_progress", monkeypatch, app)
    unread = _expr("unread", monkeypatch, app)

    assert len({finished, in_progress, unread}) == 3, "三种状态必须生成不同的筛选条件"
    assert str(ub.ReadBook.STATUS_FINISHED) in finished
    assert str(ub.ReadBook.STATUS_IN_PROGRESS) in in_progress


def test_unread_includes_books_without_any_record(app, monkeypatch):
    """从未打开过的书没有 ReadBook 行，必须用 NOT EXISTS 才能命中。"""
    unread = _expr("unread", monkeypatch, app)
    assert "NOT (EXISTS" in unread.upper(), "unread 应为反存在子查询，否则会漏掉从未打开的书"
    assert "read_book.read_status =" not in unread.lower(), \
        "unread 不能退化成等值匹配（会排除没有记录的书）"


def test_legacy_values_still_work(app, monkeypatch):
    """旧链接里的 True / False / 空值不能 500，且语义保持可解释。"""
    assert _expr("True", monkeypatch, app) == _expr("finished", monkeypatch, app)
    assert _expr("", monkeypatch, app) == _expr("unread", monkeypatch, app)
    # 「False」的历史语义是「未读完」，保留原行为（不等于任何单一新状态）
    legacy_false = _expr("False", monkeypatch, app)
    assert str(ub.ReadBook.STATUS_FINISHED) in legacy_false


def test_any_is_not_filtered_by_caller(app, monkeypatch):
    """Any 由调用方判断（read_status != 'Any'），这里只确认不会误判成某种状态。"""
    monkeypatch.setattr(search, "current_user", _StubUser())
    with app.app_context():
        assert search.adv_search_read_status("Any") is not None
