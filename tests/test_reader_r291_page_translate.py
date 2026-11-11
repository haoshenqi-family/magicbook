"""R291 整页翻译排版修复的静态守卫。

用户实测（dev，/read/487/epub，2026-11-11）：点右上角「译」后——
  ① 「可见页」判据拿 iframe 的 win.innerWidth（= 整章多栏宽，实测 2310px），
     全章 25 段全进队列、20 段封顶截断章尾，等待约 90s 才一次性渲染；
  ② 整章插入把分栏 scrollWidth 2291 → 3215，所有页边界后移，正在读的段落被挤走；
  ③ 译文块被页边界切成两截（本页底部一截 + 下页顶部一截）；
  ④ 译文 ~5s 自动消失（per100 默认 5），再触发一次整章回弹。

修复拍板（同日，用户确认）：可见性按外层 .epub-container 裁切区间判定 +
点击时快照当前页；严格按序逐段（一段落位再发起下一段，不并发，不二路并发）；
整页译文常驻（关开关才移除，段落级按钮维持 5s 自动隐藏）；译文块
break-inside: avoid。本文件只钉形制；真机验证记 response.md。
"""

import os
import re


_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _read(rel):
    with open(os.path.join(_ROOT, rel), encoding="utf-8") as handle:
        return handle.read()


def test_可见性判定必须基于外层容器裁切区间():
    """iframe 是整章宽（win.innerWidth 恒真），可见页只能由外层 .epub-container
    的裁切框相对 .epub-view 的偏移求出。"""
    js = _read("cps/static/js/reading/reader-immersive.js")
    assert "function visibleSliceFor" in js, "缺少可见区间计算"
    assert ".epub-container" in js, "裁切视口必须取 .epub-container"
    fn = js.split("function isElementVisible", 1)[1].split("\n    function", 1)[0]
    assert "slice" in fn, "isElementVisible 必须接收裁切区间"
    assert "rect.right > slice.left && rect.left < slice.right" in fn, \
        "水平判定必须与裁切区间求交"
    assert "if (!slice)" in fn, "slice 拿不到时必须有显式回退分支（不静默翻零段）"
    # 调用点必须先算 slice 再判定：可见性收集不得退回无区间调用
    apply_fn = js.split("function applyImmersiveTranslation()", 1)[1].split(
        "\n    // 工具栏「译」", 1)[0]
    assert "var slice = visibleSliceFor(content)" in apply_fn
    assert "isElementVisible(el, win, slice)" in apply_fn


def test_整页翻译严格按序且逐段落位():
    """用户拍板：一段落位再发起下一段，不并发（明确不要二路并发）；
    取代 R226 的「全部返回后一次渲染」批量终渲染。"""
    js = _read("cps/static/js/reading/reader-immersive.js")
    apply_fn = js.split("function applyImmersiveTranslation()", 1)[1].split(
        "\n    // 工具栏「译」", 1)[0]
    assert "runConcurrent(" not in js, "R291 拍板严格按序：并发池必须移除"
    assert "function step()" in apply_fn, "按序驱动器（step 链）缺失"
    assert "renderTranslationBatch" not in js, "整批终渲染已被逐段落位取代"
    assert "isConnected" in apply_fn, \
        "落位前必须查段落脱附（换章后 el.parentNode 为 null，insertBefore 直接 TypeError）"
    # 每段落位即重读缓存：划词气泡翻译同样写此缓存，整对象旧值会覆盖它
    assert "var fresh = loadTranslationCache()" in apply_fn
    assert "saveTranslationCache(fresh)" in apply_fn


def test_整页译文常驻_段落级仍自动隐藏():
    """整页模式译文不自动隐藏（关开关才移除）；段落级「译」按钮维持原计时语义。"""
    js = _read("cps/static/js/reading/reader-immersive.js")
    insert_fn = js.split("function insertTranslation", 1)[1].split("\n    }\n", 1)[0]
    assert "persist" in insert_fn, "insertTranslation 必须有 persist 形参"
    assert "div._noHide = true" in insert_fn, "整页模式必须标记常驻"
    resched = js.split("function rescheduleVisibleTranslations", 1)[1].split("\n    }\n", 1)[0]
    assert "_noHide" in resched, "改配置重排计时必须跳过常驻译文"
    # 三个整页来源（缓存命中 / 回填 / 按序落位）都传 persist=true
    assert js.count("insertTranslation(el, cached, null, true)") == 2, \
        "缓存命中与整页回填两处都应常驻"
    assert "insertTranslation(finishedJob.el, translation, null, true)" in js, \
        "按序落位结果应常驻"
    # 段落按钮路径（translateSingleParagraph）不带 persist → 默认仍走计时
    single = js.split("function translateSingleParagraph", 1)[1].split(
        "\n    // 段落级「译」按钮", 1)[0]
    assert "insertTranslation(el, translation, null, persist)" in single
    assert "insertTranslation(el, translation, null, true)" not in single


def test_译文块禁止跨栏断裂():
    core = _read("cps/static/js/reading/reader-core.js")
    m = re.search(r"\.reading-translation\{([^}]*)\}", core)
    assert m, "reader-core 注入样式缺少 .reading-translation 规则"
    rule = m.group(1)
    assert "break-inside:avoid" in rule, "译文块必须禁止跨栏断裂（R291）"
    assert "-webkit-column-break-inside:avoid" in rule, "旧 WebKit 前缀同步保留"
