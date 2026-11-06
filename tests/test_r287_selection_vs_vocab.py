"""R287：划词翻译与生词划线是两条独立功能（口径守卫）。

Why 静态锁定：这两条功能此前被写成一件事，退化都不会报错，只会在界面上「看起来正常」：

1. 划词翻译被 `readingVocabularyEnabled`（生词开关）绑死——关掉生词就再也划不出译文；
2. 划词气泡对**任何**选区都自动送 LLM——用户框选长段/中文只是为了复制，token 白烧；
3. 生词悬停没有任何信息落点（R268 起 `span.title` 下线，只剩 `cursor:help` 的问号指针），
   R286 又为它另造了一张七按钮卡片，与划词气泡同页两套 UI。

R287 的收口口径（用户定义）：生词划线只负责标出波浪线（可选 R261 行内小字），
划词翻译负责「选中任何文本给译文」；生词悬停只是免去框选的第二触发方式，
复用同一个气泡。本用例把这四条钉住。
"""

import os

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _read(rel):
    with open(os.path.join(_ROOT, rel), encoding="utf-8") as handle:
        return handle.read()


def _fn_body(src, signature, stop="\n    }\n"):
    """取一个函数体的粗略切片（够做「不得出现某调用」这类断言）。"""
    head = src.index(signature)
    return src[head:src.index(stop, head) + len(stop)]


def test_划词翻译不再被生词开关绑死():
    js = _read("cps/static/js/reading/reader-selection.js")
    body = js[js.index("function translateSelection(content)"):]
    body = body[:body.index("\n    }\n")]
    code = [line for line in body.splitlines() if not line.lstrip().startswith("//")]
    assert not any("readingVocabularyEnabled" in line for line in code), \
        "划词翻译与生词开关必须解耦：关掉生词也要能划词查词（注释里可以提，代码里不行）"
    assert "calibre.readingTranslationUrl" in body


def test_只有单个英文单词自动翻译_其余等用户点译():
    js = _read("cps/static/js/reading/reader-selection.js")
    body = _fn_body(js, "function openTranslationFor(text, context, rect)")
    auto, manual = body.split("非单词：气泡先出原文预览")
    # 单词分支：自动发请求
    assert "requestTranslation(" in auto, "单个英文单词应在气泡打开后自动翻译"
    # 非单词分支：只挂按钮，绝不在这里发请求
    assert "requestTranslation(" not in manual, \
        "非英文单词（短语/句子/中文）不得自动发请求——框选常常只是为了复制"
    assert "appendTranslateButton(" in manual and "appendAskAiButton(" in manual
    assert "clearTimeout(popoverHideTimer)" in manual, \
        "等用户操作的气泡不能启动自动隐藏倒计时"


def test_非单词气泡给出译与AI两个显式入口():
    js = _read("cps/static/js/reading/reader-selection.js")
    css = _read("cps/static/css/reader.css")
    assert "btn.textContent = '译';" in js, "非单词选区必须有显式「译」按钮"
    assert "btn.textContent = 'AI';" in js, "非单词选区应可把内容带进 AI 伴读"
    assert ".reading-translation-popover .translation-action" in css
    assert "translation-ask" in css, "单词气泡里的 AI 与 🔊/＋/－/详 要同一排"


def test_悬停生词复用划词气泡而不是另造卡片():
    js = _read("cps/static/js/reading/reader-selection.js")
    css = _read("cps/static/css/reader.css")
    body = _fn_body(js, "function bindVocabHover(content)")
    assert "openTranslationFor(" in body, "悬停生词应直接喂给划词链路（同一条请求、同一个气泡）"
    assert "closest('.reading-vocabulary-unknown')" in body
    assert "setTimeout(" in body and "140" in body, "悬停需 140ms 确认，扫过一行字不该触发"
    # R286 的独立卡片已下线
    assert "reading-vocab-card" not in css, "R286 的独立卡片样式应已下线"
    assert "reading-vocab-card" not in js
    assert "bindVocabHover(content);" in js, "bindFrame 未挂上悬停绑定"


def test_生词指针不再退回问号():
    css = _read("cps/static/css/reader.css")
    core = _read("cps/static/js/reading/reader-core.js")
    rule = css.split(".reading-vocabulary-unknown {")[1].split("}")[0]
    assert "cursor: pointer;" in rule, "生词 span 用可交互指针，不得是 help（问号）"
    assert "cursor:pointer}" in core, "注入 iframe 的样式也要用 pointer（父页规则不跨文档）"
    for name, src in (("reader.css", css), ("reader-core.js", core)):
        live = [line for line in src.splitlines()
                if "cursor" in line and not line.lstrip().startswith(("//", "/*", "*"))]
        assert not any("help" in line for line in live), f"{name} 里仍有 cursor:help"


def test_台账通道真的接上_host():
    js = _read("cps/static/js/reading/reader-selection.js")
    set_host = js.split("setHost: function (next) {")[1].split("},")[0]
    for key in ("markVocabulary", "buildSpeechUtterance", "getWordRecord", "applyWordRecord"):
        assert f"next.{key}" in set_host, f"setHost 漏接 {key}：装配层的实参会被静默丢弃"


def test_气泡关闭路径覆盖翻页_ESC_滚动():
    epub = _read("cps/static/js/reading/epub.js")
    js = _read("cps/static/js/reading/reader-selection.js")
    assert "RS.closePopover();" in epub.split("reader.rendition.on('relocated'")[1][:400], \
        "翻页后气泡坐标失效，必须关闭"
    assert "event.key === 'Escape'" in js and "closeTranslationPopover();" in js
    assert "content.window.addEventListener('scroll', closeTranslationPopover" in js, \
        "连续滚动模式下气泡会脱锚，必须收走"
