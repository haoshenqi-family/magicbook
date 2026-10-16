"""reader 模块 API 表面守卫（R183 架构评审 B4 批次 4 引入）。

Why：B4 把 epub.js 按域拆成多文件后，跨文件调用（RC./RD./AN./RS.）是纯运行时的——
`node --check` 只看语法，按源码文本断言的静态锁也看不见「拼错一个方法名」。这类错误的
表现是用户侧「点了没反应」，正是家族根纪律⑦说的「静默降级把故障伪装成数据不存在」。
本用例把「调用面 ⊆ 导出面」做成机械检查：任何一侧改名或漏导出，立刻报红。

同时锁住载入顺序：导出者必须排在调用者之前（reader-core → word-detail → annotations
→ selection → epub.js），否则模块顶层的 window.X 别名取到 undefined。
"""

import re

from tests.reader_js_modules import reader_blob, reader_module_order

ALIASES = {
    "RC": "ReaderCore",
    "RD": "ReaderWordDetail",
    "AN": "ReaderAnnotations",
    "RAn": "ReaderAnnotations",
    "RS": "ReaderSelection",
    "RI": "ReaderImmersive",
}
_ALIAS_RE = re.compile(r"\b(RC|RD|AN|RAn|RS)\.([A-Za-z_]\w*)")
_EXPORT_RE = {alias: re.compile(r"window\.%s\s*=\s*\{(.*?)\n    \};" % re.escape(obj), re.S)
              for alias, obj in ALIASES.items()}


def test_每个跨模块调用都在导出面上():
    blob = reader_blob()
    exported = {}
    for alias, pattern in _EXPORT_RE.items():
        m = pattern.search(blob)
        assert m, "找不到 window.%s 的导出块（导出形制变了？）" % alias
        exported[alias] = set(re.findall(r"([A-Za-z_]\w*)\s*:", m.group(1)))

    missing = []
    for alias, member in set(re.findall(r"\b(RC|RD|AN|RAn|RS|RI)\.([A-Za-z_]\w*)", blob)):
        if member not in exported[alias]:
            missing.append("%s.%s" % (alias, member))
    assert not missing, "调用了模块未导出的成员：%s" % ", ".join(sorted(missing))


def test_模块载入顺序保证导出先于使用():
    order = reader_module_order()
    for name in ("reader-core.js", "reader-word-detail.js", "reader-annotations.js",
                 "reader-selection.js"):
        assert name in order, "read.html 未载入 %s（拆分后的模块漏挂载）" % name
    assert order.index("reader-core.js") < order.index("reader-selection.js")
    assert order.index("reader-word-detail.js") < order.index("reader-selection.js")
    assert order.index("reader-annotations.js") < order.index("reader-selection.js")
    assert order.index("reader-selection.js") < order.index("reader-immersive.js")
    assert order.index("reader-immersive.js") < order.index("epub.js"), \
        "epub.js 顶层就读 window.Reader* 别名，模块必须排在它之前"


def test_声明_init_的模块必须被显式调用():
    """带宿主回调的模块不能在 IIFE 里跑载入期副作用——那一刻 setHost 还没执行，
    静默空操作在界面上的表现只是「第一次有点慢」，没人会当成 bug 报上来（批次 5 实例）。
    因此这类模块一律把副作用收进 init()，由 epub.js 在 setHost 之后显式调用。"""
    blob = reader_blob()
    declared = set()
    for m in re.finditer(r"window\.(Reader\w+)\s*=\s*\{(.*?)\n    \};", blob, re.S):
        if re.search(r"^\s*init: init,$", m.group(2), re.M):
            declared.add(m.group(1))
    assert declared == {"ReaderImmersive"}, \
        "带 init 的模块集合变了（%s）——本用例与 setHost 时序约定要一起复核" % sorted(declared)
    alias_of = {}
    for alias, obj in ALIASES.items():
        alias_of.setdefault(obj, []).append(alias)
    for obj in declared:
        names = sorted(set([obj] + alias_of.get(obj, [])))
        pattern = r"\b(?:%s)\.init\(\);" % "|".join(re.escape(n) for n in names)
        assert re.search(pattern, blob), \
            "%s 声明了 init 却没有调用点（模块内不能自跑：那一刻 setHost 还没执行）" % obj


def test_气泡状态只有模块一份归属():
    """划词气泡与右键菜单的状态在批次 4 归 reader-selection.js。

    若其他文件再出现 `translationPopover =` / `selectionMenu =` 的赋值，就是第二份真相
    （外部只能经 RS.isPopoverOpen()/closePopover() 观察与关闭，不能自己改）。
    """
    import os

    from tests.reader_js_modules import _READING_DIR

    for name in reader_module_order():
        if name == "reader-selection.js":
            continue
        with open(os.path.join(_READING_DIR, name), encoding="utf-8") as fh:
            src = fh.read()
        for state in ("translationPopover", "popoverHideTimer", "selectionMenu"):
            assert not re.search(r"\b%s\s*=\s*[^=]" % state, src), \
                "%s 里出现了气泡/菜单状态的赋值：归属必须只在 reader-selection.js" % name
