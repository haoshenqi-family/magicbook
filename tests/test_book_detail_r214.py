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
