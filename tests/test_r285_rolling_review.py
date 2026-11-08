"""R285/R289 Buddy 头顶滚动复习守卫：纯文字词卡、零计费；R289 起正文为详情分页。

为什么是源码断言而不是只跑页面：这一轮的失效模式全都是静默的——
(1) init() 忘了调 initRollingReview()，页面完全没卡片却没有任何报错；
(2) 卡片挂进 fab-wrap 会被 hover 快捷气泡遮住、抢走拖拽命中区；
(3) 为了凑「例句」去调 /vocabulary/detail/{word}，缓存 miss 会现场生成（计费 + 15~30s）；
    R289 详情分页只能走只读缓存批量端点（detail-cached-batch，miss 不出现在结果里），
    逐词详解代理（/ajax/reading-word-detail）与逐词上游路径仍然全是禁区；
(4) 把「认识」接到 /learning/srs/answer 会重排 FSRS，越过「只做被动展示」；
(5) 标记请求跨过一个 8s tick 后按回来时的 index 删词 → 删错词；
(6) pagehide 清掉 timer 但 bfcache 返回不重建 → 轮播永久停摆；
(7) 失败时把词从本地队列移除，用户以为标记成功，实际后端拒绝了；
(8) 新词条走 t() 但没进种子/PO/MO，中文用户静默拿到英文；
(9) R289 分页越过「每页 ≤3 行」或详情失败装成有详情——前者是用户明定的口径，
    后者会让「没有缓存」伪装成「卡片坏了」。
这些都不会让页面报错，只能在源码/词表层锁住。
"""
import gettext
import os
import re

from babel.messages.pofile import read_po

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PANEL = os.path.join(ROOT, "cps", "templates", "ai_chat_panel.html")
CHAT_JS = os.path.join(ROOT, "cps", "static", "js", "ai_chat.js")
CHAT_CSS = os.path.join(ROOT, "cps", "static", "css", "ai_chat.css")
SEED = os.path.join(ROOT, "cps", "templates", "i18n_seed.html")
PO = os.path.join(ROOT, "cps", "translations", "zh_Hans_CN", "LC_MESSAGES", "messages.po")
MO = os.path.join(ROOT, "cps", "translations", "zh_Hans_CN", "LC_MESSAGES", "messages.mo")

NEW_STRINGS = [
    "Rolling review", "Pause review", "Resume review", "Collapse review",
    "Show review", "Next word", "I know this", "Loading review words…",
    "No words to review right now", "This word cannot be marked here",
    "Could not load review words", "Could not mark this word as known",
    # R289 详情模块标签（Etymology/Synonyms/Antonyms 是存量词条，复用不新增）
    "Collocations", "Word forms", "Slang", "Fun facts",
]


def _read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def _r285_block():
    """R285 代码段：从标题注释到下一个既有函数，避免把 R227 的 TTS 代码算进来。"""
    src = _read(CHAT_JS)
    start = src.index("// R285 滚动复习")
    end = src.index("  function clearLetterBadge()", start)
    return src[start:end]


def _code_only(block):
    """去掉注释行：Why 段里会写出被禁止的端点名，不能拿来当调用证据。"""
    return "\n".join(line for line in block.splitlines()
                     if not line.strip().startswith(("//", "*", "/*")))


def _function_body(name):
    src = _read(CHAT_JS)
    start = src.index("function " + name)
    rest = src[start + 1:]
    nxt = re.search(r"\n  function ", rest)
    return src[start:] if not nxt else src[start:start + 1 + nxt.start()]


def test_panel_mounts_review_card_outside_fab_wrap(admin_client):
    """卡片是 root 的独立子元素（在 restore 与 drawer 之间），且登录/匿名有守卫。"""
    body = admin_client.get("/buddy").data.decode("utf-8")
    assert 'id="ai-companion-review"' in body
    for el in ("ai-review-known", "ai-review-next", "ai-review-peek",
               "ai-review-error", "ai-review-retry"):
        assert 'id="%s"' % el in body
    assert (body.index('id="ai-companion-restore"')
            < body.index('id="ai-companion-review"')
            < body.index('id="ai-companion-drawer"')), \
        "卡片必须挂在 fab-wrap 之外，否则 hover 快捷气泡与拖拽会互相打架"
    panel = _read(PANEL)
    assert "current_user.is_authenticated and not current_user.is_anonymous" in panel
    assert "if (!root) return;" in _r285_block(), "无容器（匿名页）时不得发任何请求"


def test_init_actually_wires_rolling_review():
    """删掉 init() 里这一行功能全停，但其余源码断言仍会全绿——必须单独钉住。"""
    src = _read(CHAT_JS)
    start = src.index("  function init() {")
    end = src.index("\n  function ", start + 1)
    assert "initRollingReview();" in src[start:end]


def test_review_reads_due_queue_without_new_or_billed_calls():
    """只拉既有 SRS 到期队列；20 个词前端洗牌；不碰 TTS / 计费详解 / 评分端点。"""
    code = _code_only(_r285_block())
    m = re.search(r'var REVIEW_QUEUE_URL\s*=\s*"([^"]+)"', code)
    assert m and m.group(1) == "/ajax/learning/srs/queue", \
        "代理不透传 ?limit=，只能靠上游默认 20，不得自己拼 query"
    assert "REVIEW_MAX = 20" in code
    assert "reviewShuffled" in code
    # R289：详情只允许走只读缓存批量端点；任何「逐词详解」形态（计费链路）都禁止。
    m2 = re.search(r'var REVIEW_DETAILS_URL\s*=\s*"([^"]+)"', code)
    assert m2 and m2.group(1) == "/ajax/vocabulary/detail-cached-batch", \
        "详情数据源必须是 moon-well R248 只读缓存批量端点"
    for forbidden in ("/tts", "/ajax/reading-tts", "/vocabulary/detail/",
                      "/ajax/reading-word-detail", "/learning/srs/answer",
                      "AudioContext", "decodeAudioData"):
        assert forbidden not in code, "R285/R289 不得触碰 %s（不出声、不计费、不改 SRS）" % forbidden


def test_r289_detail_pages_only_show_a_slice_per_tick():
    """R289：同词连翻多页、翻完才换词；页内容钳 3 行；详情失败回退简卡不装死。"""
    code = _code_only(_r285_block())
    css = _read(CHAT_CSS)
    # 翻页优先于换词：tick 里先看当前词还有没有下一页
    tick = _function_body("reviewTick")
    assert "reviewPagesFor(reviewCurrent())" in tick
    assert tick.index("review.page += 1") < tick.index("review.index = (review.index + 1)"), \
        "有下一页时必须先翻页，不能每 tick 都跳词"
    # 换词/下一词/移除词都要把页下标归零，防止页码溢出串页
    assert "review.page = 0" in _function_body("reviewAdvance")
    assert "review.page = 0" in _function_body("reviewLoad")
    assert "delete review.pages[reviewWordKey(item.word)]" in _function_body("reviewMarkKnown")
    # 页面装配：基本意思 + 一个随机模块，每词页数有上限
    assert "pages.length < 2" in _function_body("reviewDetailPages"), "义项最多取前 2 条"
    assert "pool[Math.floor(Math.random() * pool.length)]" in _function_body("reviewDetailPages")
    # 渲染钳制：详情正文 -webkit-line-clamp: 3（用户口径「每次显示不超过3行」的硬保证）
    detail_css = css[css.index(".ai-review-detail {"):css.index(".ai-review-detail:empty")]
    assert "-webkit-line-clamp: 3" in detail_css
    assert "white-space: pre-line" in detail_css
    # 详情拿不到时的回退是简卡（义项+原句+出处照常渲染），且详情 fetch 失败必须清空页表
    assert "review.pages = {}" in _function_body("reviewLoadDetails")
    assert "reviewSetText(\"ai-review-detail\", \"\")" in _function_body("reviewRender")
    assert "item.meaning" in _function_body("reviewRender")
    assert "item.contextSentence" in _function_body("reviewRender")


def test_known_reuses_existing_word_mark_endpoint():
    """「认识」＝划词气泡已有的 known/{word}，不组合评分端点、不重排 FSRS。"""
    code = _code_only(_r285_block())
    assert '"/ajax/reading-word-mark"' in code
    assert "unknown: false" in code
    assert "srs/answer" not in code
    assert "grade" not in code
    assert "scheduleId" not in code
    assert "api.unwrapStrict(resp.data)" in code, "解包必须委托 MBApi（R177 单点）"


def test_review_pauses_when_page_or_buddy_is_inactive():
    """页面不可见/不活跃、伙伴隐藏、快捷气泡、抽屉/邮件弹层、暂停/收起、请求在途都要停。"""
    body = _function_body("reviewShouldPause")
    for token in ("reviewPageActive()", "review.inFlight", "buddy-hidden",
                  "bubbles-open", "review.paused", "review.collapsed",
                  "review.failed", "review.loading", "drawer", "buddy-mail-popover"):
        assert token in body, "缺少暂停条件 %s" % token
    # EPUB 正文在 iframe 内，焦点进去时顶层 hasFocus() 会误判为不活跃。
    active = _function_body("reviewPageActive")
    for token in ("visibilityState", "hasFocus", "activeElement", "IFRAME"):
        assert token in active, "缺少页面活跃判据 %s" % token
    code = _code_only(_r285_block())
    assert "setInterval(reviewTick, REVIEW_INTERVAL_MS)" in code
    assert "clearInterval" in code


def test_bfcache_return_restarts_timer():
    """pagehide 清 timer 后，bfcache 返回必须由 pageshow 重建，否则轮播永久停摆。"""
    code = _code_only(_r285_block())
    assert "pageshow" in code
    assert "event.persisted" in code
    assert "reviewStartTimer()" in code
    assert "clearInterval" in code


def test_mark_known_uses_click_time_index():
    """POST 在途时 tick 不得推进，且删词必须按点击瞬间的下标。"""
    code = _code_only(_r285_block())
    assert "var markedIndex = review.index;" in code
    assert "review.items.splice(markedIndex, 1)" in code
    assert "review.items.splice(review.index" not in code
    assert "review.inFlight" in _function_body("reviewShouldPause")
    assert "review.markError = \"\"" in _function_body("reviewTick"), \
        "换词要清掉上一条的失败原因"


def test_server_text_is_rendered_as_text_not_html():
    """词/释义/例句来自上游 ES，只能用 textContent 渲染。"""
    code = _code_only(_r285_block())
    assert "textContent" in code
    assert "innerHTML" not in code
    assert "item.meaning" in code and "item.contextSentence" in code
    assert "item.contextBook" in code


def test_mark_failure_keeps_card_and_surfaces_reason():
    """失败时不得把词从本地队列移除，上游原因要留在状态行。"""
    code = _code_only(_r285_block())
    assert code.count("review.items.splice") == 1, "移除只允许发生在成功分支"
    assert code.index("if (!resp.ok)") < code.index("review.items.splice")
    assert "review.markError" in code
    assert "is-error" in code


def test_empty_and_error_states_are_visible():
    """队列为空 / 加载失败都必须有可见文案与重试入口，不伪装成「没有词」。"""
    code = _r285_block()
    assert 't("No words to review right now")' in code
    assert "ai-review-error" in code and "ai-review-retry" in code
    assert "reviewShowError" in code
    assert "jsonMessage" in code, "上游 Result.message 要带出来"


def test_css_keeps_card_clear_of_bubbles_and_respects_hidden():
    css = _read(CHAT_CSS)
    assert ".ai-review[hidden]" in css, "all:initial 会盖掉 UA 的 [hidden] 样式"
    assert "#ai-companion-fab-wrap.bubbles-open ~ .ai-review" in css
    assert "position: fixed" in css
    assert "is-collapsed" in css and "is-below" in css and "is-left" in css
    assert ".ai-review-btn { min-height: 44px" in css, "移动端触达盒对齐 R215 硬指标"
    assert "transitionend" in _code_only(_r285_block()), "拖拽吸附过渡后要重算位置"


def test_r285_strings_are_seeded_and_translated():
    """t() 新词条与 reviewMessage 的兜底文案都必须在 种子 + PO + MO 三方齐全。"""
    src = _r285_block()
    literals = set(re.findall(r'\bt\(\s*"([^"]+)"\s*\)', src))
    for s in NEW_STRINGS:
        assert s in literals, "词条 %r 未出现在 R285 代码里" % s
    # reviewMessage(resp.raw, "XXX") 的兜底文案是动态取词，t() 正则抓不到。
    fallbacks = set(re.findall(r'reviewMessage\([^,]+,\s*"([^"]+)"\s*\)', src))
    assert fallbacks and fallbacks <= set(NEW_STRINGS), \
        "兜底文案漏进 i18n 词条集合：%r" % sorted(fallbacks - set(NEW_STRINGS))
    seed = _read(SEED)
    for s in NEW_STRINGS:
        assert '"%s": _("%s")' % (s, s) in seed, "词条 %r 未进 i18n_seed.html" % s
    with open(PO, "rb") as fh:
        catalog = read_po(fh)
    for s in NEW_STRINGS:
        assert catalog.get(s) and catalog.get(s).string, \
            "词条 %r 在 zh po 里缺失或译文为空" % s
    with open(MO, "rb") as fh:
        mo = gettext.GNUTranslations(fh)
    for s in NEW_STRINGS:
        assert mo.gettext(s) != s, "词条 %r 未编译进 .mo" % s
