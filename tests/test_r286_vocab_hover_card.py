"""R286：生词悬停释义卡（去掉「问号指针」，悬停即出释义）。

Why 静态锁定：用户连续两轮反馈「阅读器里只有一个问号，没有释义」。根因有两层，
且两层都不会报错、只会在界面上静默退化：

1. `.reading-vocabulary-unknown` 的 `cursor:help` 把鼠标变成问号指针，而 `span.title`
   自 R268 起已下线——悬停既没有提示也没有任何释义落点；
2. `ReaderSelection.setHost` 只接了 `markVocabulary` / `buildSpeechUtterance` 两个回调，
   装配层一直在传的 `getWordRecord` / `applyWordRecord` 被静默丢弃，于是台账读不到
   （`record.gloss` 永远是 undefined，卡片只能显示「暂无译文」）、＋/－ 标记也不回写波浪线。

两条都是「看着正常、实际没数据」的失效模式，所以用源码级断言钉住：
指针不许退回 help、卡片构建与悬停绑定不许消失、台账通道必须真的接上。
"""

import os

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _read(rel):
    with open(os.path.join(_ROOT, rel), encoding="utf-8") as handle:
        return handle.read()


def test_生词不再使用问号指针():
    css = _read("cps/static/css/reader.css")
    core = _read("cps/static/js/reading/reader-core.js")
    # 父页样式与注入 iframe 的样式必须同口径：正文在 iframe 内，只改一处等于没改
    assert "cursor: pointer;" in css.split(".reading-vocabulary-unknown {")[1].split("}")[0], \
        "reader.css 的生词 span 必须用可交互指针（cursor:pointer），不得退回 help 问号"
    assert "cursor:pointer}" in core, \
        "注入 iframe 的 READER_TOOLS_STYLE 里生词 span 也要用 pointer"
    # 注释里会写到历史写法，只看实际生效的声明
    for name, src in (("reader.css", css), ("reader-core.js", core)):
        live = [line for line in src.splitlines()
                if "cursor" in line and not line.lstrip().startswith(("//", "/*", "*"))]
        assert not any("help" in line for line in live), f"{name} 里仍有 cursor:help（问号指针）"


def test_悬停卡构建与悬停绑定存在():
    js = _read("cps/static/js/reading/reader-selection.js")
    assert "function openVocabCard(" in js, "悬停卡构建函数缺失"
    assert "function bindVocabCard(" in js, "悬停卡绑定函数缺失"
    assert "bindVocabCard(content);" in js, "bindFrame 未挂上悬停绑定，正文里永远不会出卡"
    # 悬停判定锚在生词 span 上，且要读台账里的词典首义项
    assert "closest('.reading-vocabulary-unknown')" in js, "悬停目标必须是生词 span"
    assert "record.gloss" in js, "卡片释义应取台账里的词典首义项（零请求零计费）"
    # 悬停不主动发翻译请求：单词未命中词典会走 LLM 计费，不能由「划过」触发
    assert "悬停不能悄悄扣积分" in js


def test_卡片按钮与第一张参考图同形制():
    js = _read("cps/static/js/reading/reader-selection.js")
    css = _read("cps/static/css/reader.css")
    for label in ("'译'", "'详'", "'🔊'", "'认识'", "'生词'", "'AI'", "'✕'"):
        assert f"addBtn({label}" in js, f"卡片缺少按钮 {label}"
    assert ".reading-vocab-card" in css and ".reading-vocab-card .rvc-btn" in css, \
        "卡片样式缺失（白卡 + 胶囊按钮）"
    assert "cursor: pointer;" in css.split(".reading-vocab-card .rvc-btn {")[1].split("}")[0]
    # 卡片与划词气泡同层：开卡必须收气泡，两个浮层不能叠在同一处
    assert "if (translationPopover) closeTranslationPopover();" in js


def test_台账通道真的接上_host():
    js = _read("cps/static/js/reading/reader-selection.js")
    set_host = js.split("setHost: function (next) {")[1].split("},")[0]
    for key in ("markVocabulary", "buildSpeechUtterance", "getWordRecord", "applyWordRecord"):
        assert f"next.{key}" in set_host, f"setHost 漏接 {key}：装配层的实参会被静默丢弃"


def test_气泡与悬停卡共用一条标记路径():
    js = _read("cps/static/js/reading/reader-selection.js")
    assert "function markWord(word, unknown, btn, onDone)" in js, \
        "标记实现必须收敛成单个函数，避免气泡与卡片各写一份请求/回写逻辑"
    # 气泡的 ＋/－ 与卡片的 认识/生词 都只能经 markWord
    assert js.count("markWord(word, ") >= 3


def test_关闭路径覆盖翻页_点外_Esc():
    epub = _read("cps/static/js/reading/epub.js")
    assert "RS.closeVocabCard();" in epub.split("reader.rendition.on('relocated'")[1][:600], \
        "翻页后悬停卡锚点失效，必须随 relocated 关闭"
    assert "RS.isVocabCardOpen() && !RS.vocabCardContainsNode(event.target)" in epub, \
        "点卡片外部应关闭悬停卡"
    assert "RS.isVocabCardOpen() && !RD.isOpen()" in epub, \
        "Esc 分层退出：详解面板从卡片打开时，Esc 先收面板再收卡片"
    js = _read("cps/static/js/reading/reader-selection.js")
    assert "content.window.addEventListener('scroll', closeVocabCard" in js, \
        "连续滚动模式下正文滑动会让卡片脱锚，必须收走"
