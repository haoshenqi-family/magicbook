"""R158：speaking_writing.js 元素引用完整性静态检查。

Why: R155 注册表漏了 'sw-s-audio-status'，停止分支对 undefined 赋值抛同步
TypeError——按钮永远停在「转写中…」且无提示（用户实测）。这类错误 pytest
页面断言抓不到（只查 id 存在性），必须锁两条：①JS 引用的每个 els['x'] 都
已注册；②注册表里每个 id 都真实存在于模板。
"""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JS = os.path.join(ROOT, "cps", "static", "js", "speaking_writing.js")
HTML = os.path.join(ROOT, "cps", "templates", "speaking_writing.html")


def _registered_ids():
    src = open(JS, encoding="utf-8").read()
    m = re.search(r"\[(?:\s*'[^']+',?\s*)+\]\.forEach\(function \(id\) \{ els\[id\] = \$\(id\); \}\);", src, re.S)
    assert m, "els 注册表未找到"
    return set(re.findall(r"'([^']+)'", m.group(0)))


def _referenced_ids():
    src = open(JS, encoding="utf-8").read()
    return set(re.findall(r"els\['([^']+)'\]", src))


def _html_ids():
    html = open(HTML, encoding="utf-8").read()
    return set(re.findall(r'id="([^"]+)"', html))


def test_every_referenced_element_is_registered():
    missing = _referenced_ids() - _registered_ids()
    assert not missing, "JS 引用了未注册的元素（运行时 undefined → 同步异常卡死）：%r" % sorted(missing)


def test_every_registered_element_exists_in_template():
    absent = _registered_ids() - _html_ids()
    assert not absent, "注册表含模板中不存在的 id：%r" % sorted(absent)
