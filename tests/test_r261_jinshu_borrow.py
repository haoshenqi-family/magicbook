"""R261 Jinshu 借鉴三件套的静态契约锁。

Why 静态锁：三件套都是「JS 运行时才生效」的前端行为（gloss 渲染 / chip 显隐 /
badge 注入），node --check 看不见逻辑，静态断言把关键决策点钉在源码文本上——
任何一侧把开关守卫、镜像键或降级分支删掉，立刻报红（家族根纪律⑦：静默降级
不许把功能失效伪装成「没数据」）。
"""

import re


def _read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


# ---------- A：阅读器行内小字释义（可选，默认关） ----------

def test_read_html_有vocabGloss开关且默认无勾选():
    html = _read("cps/templates/read.html")
    m = re.search(r'<input type="checkbox" id="vocabGloss"[^>]*>', html)
    assert m, "设置弹窗缺少 vocabGloss checkbox"
    assert "checked" not in m.group(0), "可选功能默认关：模板不得预勾选"
    assert 'Show short gloss above vocabulary words' in html


def test_epub_js_gloss挂属性走开关与词典双守卫():
    js = _read("cps/static/js/reading/epub.js")
    # 开关读 localStorage（默认关范式），键名与 read.html 的设置写入一致
    assert 'calibre.reader.vocabGloss' in js
    assert 'vocabGlossEnabled() && record.gloss' in js, \
        "gloss 属性必须同时受开关与词典文档双守卫（缺失任一即降级仅波浪线）"
    # 设置弹窗切换后的重标桥必须暴露（read.html 只认 window.ReaderVocabGloss）
    assert 'window.ReaderVocabGloss' in js
    assert 'remark: remarkVocabularyForGlossToggle' in js
    # 重标必须走已缓存的 records（无新请求）且能摘掉属性（关掉即消失）
    assert 'delete span.dataset.gloss' in js


def test_reader_core样式用attr渲染且不占文档流():
    css = _read("cps/static/js/reading/reader-core.js")
    assert '.reading-vocabulary-unknown[data-gloss]::after' in css
    assert 'content:attr(data-gloss)' in css
    assert 'position:absolute' in css, "小字必须绝对定位浮在词头（占流会推动分栏重排）"


# ---------- B：选书 Book Fit 话术 ----------

def test_learning_match_重复词数行只在字段在手时渲染():
    js = _read("cps/static/js/learning-match.js")
    assert 'repeated above-level words to learn' in js
    assert 'item.repeatedUnknownCount != null' in js, \
        "存量画像未重算时字段为 null，整行必须隐藏（不得显示 0 误导）"
    # 样例词放宽到 FIT/HARD：黄金区的书同样值得预览要面对的词
    assert "item.level === 'FIT'" in js


# ---------- C：复习小件（可选，默认关） ----------

def test_review_chip_镜像判开关且只亮书名():
    js = _read("cps/static/js/learning-review.js")
    assert 'ln-review-source-chip-v1' in js, "chip 必须走学习抽屉写入的镜像键"
    assert 'current.contextBook' in js, "无遇见记录（null）不显示"
    assert 'ln-source-chip' in js
    # 只拼书名，不拼 contextChapter / contextSentence（那两个走 post-reveal 原门控）
    chip_block = re.search(r"function renderSourceChip.*?\n  \}", js, re.S)
    assert chip_block, "renderSourceChip 函数缺失"
    block = chip_block.group(0)
    assert 'contextChapter' not in block and 'contextSentence' not in block


def test_layout_badge_镜像判关零请求且stats带缓存():
    html = _read("cps/templates/layout.html")
    assert 'id="ln-due-badge-top"' in html and 'id="ln-due-badge-mobile"' in html
    assert "ln-hub-due-badge-v1" in html, "镜像判关：开关关闭/未配置时不得发 stats 请求"
    assert '/ajax/learning/srs/stats' in html
    assert 'ln-due-badge-cache' in html, "会话内缓存避免每页一拉"
    assert 'window.MBDueBadge' in html, "学习抽屉保存后的即时刷新钩子"


def test_learning_drawer_两个小开关存在():
    html = _read("cps/templates/learning.html")
    assert 'id="lh-review-source-chip"' in html
    assert 'id="lh-hub-due-badge"' in html


def test_hub_保存显式携带两开关并落镜像():
    js = _read("cps/static/js/learning-hub.js")
    assert 'reviewSourceChip' in js and 'hubDueBadge' in js
    assert 'ln-review-source-chip-v1' in js and 'ln-hub-due-badge-v1' in js
    assert 'window.MBDueBadge' in js, "保存角标开关后即时刷新导航"


# ---------- R266：角标 hidden 失效（红横杠缺陷）的样式契约 ----------

def test_badge_css_基准态隐藏且非hidden才显示():
    """角标是作者 display 元素：作者规则会顶掉 HTML hidden 的 UA 隐藏（R140 同款坑），
    基准态必须 display:none、非 hidden 才恢复显示——否则默认关闭的角标渲染成空红胶囊。"""
    css = _read("cps/static/css/magicbook.css")
    block = re.search(r"\.ln-due-badge \{[^}]*\}", css, re.S)
    assert block, "magicbook.css 缺少 .ln-due-badge 规则块"
    assert "display: none" in block.group(0), (
        "基准态必须 display:none：作者 display 会顶掉 [hidden] 的 UA 隐藏"
    )
    assert re.search(r"\.ln-due-badge:not\(\[hidden\]\) \{[^}]*display: inline-block", css), (
        "非 hidden 态才恢复 inline-block：显示路径由 JS 同步 hidden 属性"
    )
    assert "display: inline-block" not in block.group(0), (
        "基准规则不得直接写 inline-block：那是 R266 红横杠缺陷的根因"
    )
