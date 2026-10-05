"""R112: JS 层 i18n 种子（i18n_seed.html）的三条一致性契约。

Why: epub.js / ai_chat.js / onboarding.js 是静态 JS，拿不到 Jinja 的 `_()`，
     R112 新增 window.MB_I18N 种子 + mbT(msgid) 取词通道。这条链路有两个
     纯静态可检的失效模式，都是 Code Review 实测踩到的：
     (1) 字典 key 与 `_()` 实参不一致（尾点差一个字符）→ po 里查不到，
         zh 用户静默拿到英文；
     (2) JS 里用了 mbT("X") 但种子/po 没有 X → 同样是静默英文回退，
         而且是相对收编前的本地化倒退。
     两者都不会让页面报错，运行时也不易察觉，所以用源码级断言锁住。
"""
import ast
import os
import re

from babel.messages.pofile import read_po

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEED_PATH = os.path.join(ROOT, "cps", "templates", "i18n_seed.html")
PO_PATH = os.path.join(ROOT, "cps", "translations", "zh_Hans_CN",
                       "LC_MESSAGES", "messages.po")
JS_FILES = [
    os.path.join(ROOT, "cps", "static", "js", "onboarding.js"),
    os.path.join(ROOT, "cps", "static", "js", "reading", "epub.js"),
    os.path.join(ROOT, "cps", "static", "js", "ai_chat.js"),
    # R116/US4：词汇量测试状态机的文案全部走 mbT，不列入清单则它的本地化无人守（AC-C8 假绿）
    os.path.join(ROOT, "cps", "static", "js", "vocab-test.js"),
]


def _seed_pairs():
    """把 {% set mb_i18n = {...} %} 当 AST 解析，返回 [(key, _() 实参 msgid)]。

    Why: 用 AST 而非 eval——需要同时拿到 key 和 `_()` 的实参才能比对二者；
         字符串转义形态由 Python 字面量语义还原，和 Jinja 渲染结果一致。"""
    with open(SEED_PATH, encoding="utf-8") as fh:
        src = fh.read()
    m = re.search(r"\{%\s*set\s+mb_i18n\s*=\s*(\{.*?\})\s*%\}", src, re.S)
    assert m, "i18n_seed.html 里的 mb_i18n 字典未找到"
    tree = ast.parse(m.group(1), mode="eval").body
    assert isinstance(tree, ast.Dict)
    pairs = []
    for key, value in zip(tree.keys, tree.values):
        assert isinstance(key, ast.Constant) and isinstance(key.value, str)
        assert (isinstance(value, ast.Call) and getattr(value.func, "id", None) == "_"
                and len(value.args) == 1), "每个词条的值必须是 _(msgid) 调用"
        assert isinstance(value.args[0], ast.Constant)
        pairs.append((key.value, value.args[0].value))
    return pairs


def _unescape_js(raw):
    """按 JS 字面量语义还原转义，只处理实际出现的 \\\\n 等控制转义。

    Why: 不用 codecs 的 unicode_escape——它按字节解释非 ASCII，会把词条里的
         「“ ” … 」等字符弄乱（本文件的 msgid 全是 UTF-8）。"""
    return (raw.replace("\\\\", "\\")
               .replace("\\n", "\n")
               .replace("\\t", "\t")
               .replace('\\"', '"')
               .replace("\\'", "'"))


def _mbt_literals():
    """收集三个 JS 里 mbT('...') / mbT("...") 的字符串字面量实参（跳过注释行）。

    Why: 源码里的 \\n 是字面转义，而 seed/po 存的是真换行（Jinja 渲染后写入 JSON），
         比对前必须先还原转义。"""
    pattern = re.compile(r"""mbT\(\s*(['"])((?:\\.|(?!\1).)*)\1""")
    found = set()
    for path in JS_FILES:
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                stripped = line.strip()
                if stripped.startswith(("//", "*", "/*")):
                    continue
                for m in pattern.finditer(line):
                    found.add(_unescape_js(m.group(2)))
    return found


def test_seed_key_equals_msgid():
    """契约 1：字典 key 必须与 `_()` 实参逐字符相同（JS 按 key 取词，po 按 msgid 查）。"""
    mismatches = [(k, mid) for k, mid in _seed_pairs() if k != mid]
    assert not mismatches, "seed key 与 msgid 不一致，zh 用户会拿到英文：%r" % mismatches


def test_js_mbT_literals_are_seeded():
    """契约 2：JS 用到的每个 mbT 字面量词条都必须在种子里，否则静默回退英文。"""
    keys = {k for k, _ in _seed_pairs()}
    missing = sorted(_mbt_literals() - keys)
    assert not missing, "mbT 词条不在 i18n_seed.html：%r" % missing


def test_seed_msgids_have_zh_translation():
    """契约 3：每个种子 msgid 在 zh_Hans_CN po 里必须有非空译文——
    否则 pybabel 链路断了，页面渲染时 `_()` 回退 msgid（英文）。"""
    with open(PO_PATH, "rb") as fh:
        catalog = read_po(fh)
    missing, empty = [], []
    for _, msgid in _seed_pairs():
        entry = catalog.get(msgid)
        if entry is None:
            missing.append(msgid)
        elif not entry.string:
            empty.append(msgid)
    assert not missing, "msgid 不在 zh_Hans_CN po：%r" % missing
    assert not empty, "msgid 在 po 里译文为空：%r" % empty


def test_onboarding_step_strings_are_seeded():
    """契约 4：引导步骤表的 title/body 走 mbT(step.title) 动态取词，正则抓不到，
    单独抽出来比对——R112 的尾点缺陷正是出在这一类词条上。"""
    with open(JS_FILES[0], encoding="utf-8") as fh:
        src = fh.read()
    strings = re.findall(r'^\s*(?:title|body):\s*"((?:\\.|[^"\\])*)"', src, re.M)
    assert len(strings) >= 20, "步骤表文案抽取异常，正则需同步更新"
    keys = {k for k, _ in _seed_pairs()}
    missing = sorted(s for s in map(_unescape_js, strings) if s not in keys)
    assert not missing, "引导步骤文案不在 i18n_seed.html：%r" % missing
