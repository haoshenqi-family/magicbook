"""R226 阅读器验收缺陷的静态守卫。

Why：这三处都是「结构上看似正确、真机上仍然坏」的回归：
  1. 伙伴 FAB 同特异度规则后写白底，覆盖 R223 的透明头像契约；
  2. 阅读器里的 ``?`` 只有图标，用户不知道它是什么；
  3. 整页翻译逐段插正文，每段都触发 iframe 重排；请求期占位还会
     额外插入再删除二十个节点。

本用例只钉必须保持的形制，不依赖真实浏览器；真机截图另在 response.md 记证。
"""

import os
import re


_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _read(rel):
    with open(os.path.join(_ROOT, rel), encoding="utf-8") as handle:
        return handle.read()


def _css_rule(css, selector, first=False):
    body = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    matches = re.findall(
        r"(?<![-\w])" + re.escape(selector) + r"\s*\{([^}]*)\}", body, re.S
    )
    assert matches, "CSS 缺少规则：%s" % selector
    return matches[0 if first else -1]


def test_伙伴头像态保持透明无白圆底():
    css = _read("cps/static/css/ai_chat.css")
    base = _css_rule(css, "#ai-companion-fab.has-buddy", first=True)
    later = css.split("R206 伙伴头像", 1)[1]
    owner = _css_rule(later, "#ai-companion-fab.has-buddy")
    assert "background: transparent" in base, "头像态透明底线被删除"
    assert "background" not in owner, (
        "R206 区块再次给 .has-buddy 写 background，会覆盖透明头像态"
    )
    assert "box-shadow: none" in base


def test_阅读器导览入口带明确文案():
    js = _read("cps/static/js/onboarding.js")
    body = js.split("function showReaderHelp()", 1)[1].split(
        "\n  }", 1
    )[0]
    assert "var label = mbT(\"Onboarding Tour\")" in body
    assert "+ esc(label) + '</button>'" in body, "按钮可见文本必须使用同一本地化文案"
    assert ">?</button>" not in body, "幽灵问号入口不得回流"

    css = _read("cps/static/css/onboarding.css")
    help = css.split("\n#onb-help {", 1)[1].split("}", 1)[0]
    assert "width: auto" in help and "padding: 0 14px" in help
    assert "border-radius: 999px" in help

    for text in (
        "Use the “Onboarding Tour” button at the bottom-right any time to replay the tour.",
        "bottom-right",
    ):
        assert text in js, "导览收尾文案仍指向旧的左下角问号"


def test_整页翻译请求期不插占位且完成后一次渲染():
    js = _read("cps/static/js/reading/reader-immersive.js")
    apply_fn = js.split("function applyImmersiveTranslation()", 1)[1].split(
        "\n    // 工具栏「译」", 1
    )[0]
    assert "insertTranslation(job.el, mbT('Translating…'), 'is-loading')" not in apply_fn, (
        "请求期逐段插占位会让正文高度连续变化"
    )
    assert "renderTranslationBatch(results, cache)" in apply_fn
    completion = apply_fn.split("if (remaining) return;", 1)[1]
    assert completion.index("setTranslationLoading(false)") < completion.index(
        "renderTranslationBatch(results, cache)"
    ), "必须先结束加载态，再一次性写入整批译文"
    batch = js.split("function renderTranslationBatch(results, cache)", 1)[1].split(
        "\n    function applyImmersiveTranslation", 1
    )[0]
    assert "results.forEach" in batch
    assert "saveTranslationCache(cache)" in batch, "缓存写入应合并为一次"

    css = _read("cps/static/css/reader.css")
    assert "#immersive-translate.is-loading .tb-icon" in css
    assert "prefers-reduced-motion: reduce" in css
