"""R166：每日学习各页（中枢 + 七个子页面）的前端静态守卫。

Why 逐页配对而非全量并集：拆页后每页只渲染自己那批元素，某模块引用了别页的 id
就是运行时 undefined——正是 R155 漏注册 'sw-s-audio-status'、停止分支抛同步
TypeError、按钮永久停在「转写中…」且服务端零日志的那类错误（R158 立的两条锁，
本轮只是把「一份模板」换成「模块 ↔ 模板」配对）。

第三条锁是 R166 拆分带出来的新失效面：每个模块自己声明 `var urls =
window.learningUrls`。R153 的 learning.js 引用了从未声明的 `urls.week`，
ReferenceError 被计划头 promise 的 catch 静默吞掉，今日计划与四股周视图整块
不渲染，页面照常 200、单测照常绿，直到本轮排查才发现。
"""
import os
import re

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JS_DIR = os.path.join(ROOT, "cps", "static", "js")
TPL_DIR = os.path.join(ROOT, "cps", "templates")

# (JS 模块, 渲染该模块的模板)——learning-common.js 与 learning-voice.js 无 els
# 注册表（只提供工具与 attach 入口），不进配对表。
PAIRS = [
    ("learning-hub.js", "learning.html"),
    ("learning-review.js", "learning_review.html"),
    ("learning-story.js", "learning_story.html"),
    ("learning-match.js", "learning_match.html"),
    ("learning-writing.js", "learning_writing.html"),
    ("learning-speaking.js", "learning_speaking.html"),
    ("learning-retell.js", "learning_retell.html"),
    ("learning-reread.js", "learning_reread.html"),
    ("learning-dictation.js", "learning_dictation.html"),
]

REGISTRY_RE = re.compile(
    r"\[(?:\s*'[^']+',?\s*)+\]\.forEach\(function \(id\) \{ els\[id\] = \$\(id\); \}\);",
    re.S)


def _js(name):
    with open(os.path.join(JS_DIR, name), encoding="utf-8") as fh:
        return fh.read()


def _tpl(name):
    with open(os.path.join(TPL_DIR, name), encoding="utf-8") as fh:
        return fh.read()


def _registered(src):
    m = REGISTRY_RE.search(src)
    assert m, "els 注册表未找到（R158 约定的形态：['a','b'].forEach(...)）"
    return set(re.findall(r"'([^']+)'", m.group(0)))


def _referenced(src):
    return set(re.findall(r"els\['([^']+)'\]", src))


def _html_ids(src):
    return set(re.findall(r'id="([^"]+)"', src))


@pytest.mark.parametrize("js,tpl", PAIRS, ids=[p[0] for p in PAIRS])
def test_every_referenced_element_is_registered(js, tpl):
    src = _js(js)
    missing = _referenced(src) - _registered(src)
    assert not missing, "%s 引用了未注册的元素（运行时 undefined → 同步异常卡死）：%r" \
        % (js, sorted(missing))


@pytest.mark.parametrize("js,tpl", PAIRS, ids=[p[0] for p in PAIRS])
def test_every_registered_element_exists_in_its_own_page(js, tpl):
    absent = _registered(_js(js)) - _html_ids(_tpl(tpl))
    assert not absent, "%s 的注册表含 %s 里不存在的 id：%r" % (js, tpl, sorted(absent))


@pytest.mark.parametrize("js,tpl", PAIRS, ids=[p[0] for p in PAIRS])
def test_page_declares_its_url_snapshot(js, tpl):
    """引用 `urls.x` 的模块必须自己声明 `var urls = window.learningUrls || {}`。"""
    src = _js(js)
    if not re.search(r"\burls\.", src):
        pytest.skip("%s 不取端点" % js)
    assert re.search(r"var urls = window\.learningUrls \|\| \{\};", src), \
        "%s 引用了 urls.* 却没声明（R153 静默失效的复刻）" % js
    assert "window.learningUrls" in _tpl(tpl), "%s 没注入路由快照" % tpl


@pytest.mark.parametrize("js,tpl", PAIRS, ids=[p[0] for p in PAIRS])
def test_page_loads_common_before_its_module(js, tpl):
    html = _tpl(tpl)
    assert 'js/learning-common.js' in html, "%s 未载 common" % tpl
    assert html.index('js/learning-common.js') < html.index('js/' + js), \
        "%s 的模块先于 common 加载，window.MBLearning 还是 undefined" % tpl


def test_no_page_references_the_deleted_scripts():
    """死脚本引用防回流：learning.js / speaking_writing.js 已随拆分删除。"""
    for name in os.listdir(TPL_DIR):
        if not name.endswith(".html"):
            continue
        html = _tpl(name)
        for dead in ("js/learning.js", "js/speaking_writing.js"):
            assert "'%s'" % dead not in html and '"%s"' % dead not in html, \
                "%s 仍引用已删除的 %s（404 且功能静默失效）" % (name, dead)


def test_writing_uses_sse_and_keeps_json_fallback():
    """R192：批改主路径必须是 fetch+ReadableStream 的 SSE；旧 JSON 端点只作回退。

    R200 起读取原语下沉 learning-common.js（编故事复用同一份），反向锁跟着搬家：
    退回 EventSource（不能带 CSRF/POST body）或删掉回退分支都应报红。
    """
    src = _js("learning-writing.js")
    common = _js("learning-common.js")
    assert "function postSse(" in common
    assert "getReader()" in common
    assert "postSse = MB.postSse" in src
    assert "streamEndpoint()" in src
    assert "streamStarted" in src
    assert "new EventSource(" not in src and "new EventSource(" not in common
    assert "writingSubmitStream" in src and "writingReviseStream" in src
    tpl = _tpl("learning_writing.html")
    assert "writingSubmitStream" in tpl
    assert "writingReviseStream" in tpl


def test_story_uses_shared_sse_and_json_fallback():
    """R200：编故事与写作批改共用 SSE 原语，JSON 端点保留回退。"""
    src = _js("learning-story.js")
    assert "postSse = MB.postSse" in src
    assert "storyGenerateStream" in src and "storyGenerate" in src
    assert "streamStarted" in src
    assert "new EventSource(" not in src
    tpl = _tpl("learning_story.html")
    assert "storyGenerateStream" in tpl and "storyDetail" in tpl


def test_writing_workshop_never_caps_draft_submissions():
    """R190：两稿上限取消——提交按钮不得再按稿数置灰，也不能再有「两稿已完成」终态。

    这是用户报障的直接形态（恢复历史任务后按钮不可点）；上游 moon-well R192 已改为
    稿号顺延，前端若回退到按 lastDraftNo>=2 disable，本断言报红。
    """
    src = _js("learning-writing.js")
    assert "Both drafts finished" not in src
    assert "btn.disabled = done" not in src
    assert "lastDraftNo >= 2" not in src
    assert "Draft {{n}} reviewed · can keep revising" in src
