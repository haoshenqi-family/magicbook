"""整本朗读口径提取器的契约与行为测试（R166 设计 §3.3）。

双锁：
1. 静态锁——epub.js 的 PARAGRAPH_SELECTOR / BOOK_TTS_MAX / BLOCK_CHILD_SELECTOR
   与 extractor 常量逐字对照，前端口径漂移即红；
2. 行为锁——样例 EPUB 上的提取序列（嵌套双收、DIV 容器跳过、切块句读口径、
   章标题、spine 顺序），任何一条变化都意味着缓存键口径变化，必须同步评审。
"""

import re
import zipfile

from cps.reading_tts.extractor import (
    BLOCK_CHILD_TAGS,
    BOOK_TTS_MAX,
    PARAGRAPH_TAGS,
    chunk_long_text,
    extract_epub_paragraphs,
)

EPUB_JS = "cps/static/js/reading/epub.js"


def _read_epub_js():
    with open(EPUB_JS, encoding="utf-8") as handle:
        return handle.read()


# ---------- 静态锁：前端口径常量 ↔ extractor 常量 ----------

def test_static_lock_paragraph_selector_matches_epub_js():
    js = _read_epub_js()
    match = re.search(r"PARAGRAPH_SELECTOR = '([^']+)'", js)
    assert match, "epub.js PARAGRAPH_SELECTOR 常量找不到——前端可能改了口径定义位置"
    selector = match.group(1)
    js_tags = {t.strip() for t in selector.split(",")}
    assert js_tags == PARAGRAPH_TAGS, "前端朗读段落元素集漂移：extractor 必须同步（缓存键=段落原文）"


def test_static_lock_block_child_selector_matches_epub_js():
    js = _read_epub_js()
    match = re.search(r"BLOCK_CHILD_SELECTOR = '([^']+)'", js)
    assert match, "epub.js BLOCK_CHILD_SELECTOR 常量找不到"
    selector = match.group(1)
    js_tags = {t.strip() for t in selector.split(",")}
    assert js_tags == BLOCK_CHILD_TAGS, "前端 DIV 容器判定集漂移：extractor 必须同步"


def test_static_lock_book_tts_max_matches_epub_js():
    js = _read_epub_js()
    match = re.search(r"BOOK_TTS_MAX = (\d+)", js)
    assert match, "epub.js BOOK_TTS_MAX 常量找不到"
    assert int(match.group(1)) == BOOK_TTS_MAX, "单请求上限漂移：切块口径必须同步"


def test_static_lock_chunk_algorithm_features_present():
    # 切块算法特征：后 1/3 窗口从尾向头反扫 + 中文句读集 + 英文句读「后跟空格」约束。
    # 逐字节锁算法形态太脆，锁三个不可缺特征（窗口起点、句读集、空格约束）
    js = _read_epub_js()
    assert "Math.floor(BOOK_TTS_MAX * 2 / 3)" in js, "后 1/3 窗口起点变了——chunk_long_text 需同步"
    assert "'。！？；…'" in js, "中文句读集变了——chunk_long_text 需同步"
    assert "after === '' || after === ' '" in js, "英文句读后置约束变了——chunk_long_text 需同步"


# ---------- 行为锁：样例 EPUB 提取序列 ----------

def _write_epub(path, one_body, two_body="", one_title="Chapter One"):
    container = """<container xmlns='urn:oasis:names:tc:opendocument:xmlns:container'><rootfiles><rootfile full-path='OPS/content.opf'/></rootfiles></container>"""
    opf = """<package xmlns='http://www.idpf.org/2007/opf'><manifest>
      <item id='one' href='one.xhtml' media-type='application/xhtml+xml'/>
      <item id='two' href='two.xhtml' media-type='application/xhtml+xml'/>
    </manifest><spine><itemref idref='one'/><itemref idref='two'/></spine></package>"""
    one = ("<html xmlns='http://www.w3.org/1999/xhtml'><head><title>%s</title></head><body>%s</body></html>"
           % (one_title, one_body))
    two = "<html xmlns='http://www.w3.org/1999/xhtml'><body>%s</body></html>" % two_body
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("META-INF/container.xml", container)
        archive.writestr("OPS/content.opf", opf)
        archive.writestr("OPS/one.xhtml", one)
        archive.writestr("OPS/two.xhtml", two)


def test_div_with_block_children_is_skipped_but_children_are_collected(tmp_path):
    # 前端口径：DIV 容器跳过、子 p 收——与翻译口径（只收最外层，容器不产段但这里外层是 div 不收）不同
    path = tmp_path / "book.epub"
    _write_epub(path, "<div><p>First.</p><p>Second.</p></div>", one_title="C1")

    assert extract_epub_paragraphs(path) == [("C1", "First."), ("C1", "Second.")]


def test_nested_list_items_are_collected_twice_like_query_selector_all(tmp_path):
    # 嵌套双收：li 与其内部 p 各产一段（querySelectorAll 语义）；服务层按 text_hash 去重
    path = tmp_path / "book.epub"
    _write_epub(path, "<ul><li><p>Same text.</p></li></ul>", one_title="C1")

    assert extract_epub_paragraphs(path) == [("C1", "Same text."), ("C1", "Same text.")]


def test_headings_are_speech_paragraphs_in_reader_scope(tmp_path):
    # 前端选择器含 h1..h6（标题也是朗读段），翻译口径则不含——本口径必须收 h1
    path = tmp_path / "book.epub"
    _write_epub(path, "<h1>Part One</h1><p>Body text.</p>", one_title="C1")

    # h1 同时是章名来源与朗读段（章名口径 h1 优先）
    assert extract_epub_paragraphs(path) == [("Part One", "Part One"), ("Part One", "Body text.")]


def test_long_paragraph_chunks_on_sentence_mark_in_last_third(tmp_path):
    # 连播切块口径：后 1/3 窗口从尾向头找句读；不采用翻译口径的「≤2000+1 窗口最大句界」
    body = "<p>" + ("a" * 1500) + "。" + ("b" * 1200) + "</p>"
    path = tmp_path / "book.epub"
    _write_epub(path, body, one_title="C1")

    chunks = [t for _, t in extract_epub_paragraphs(path)]
    assert len(chunks) == 2
    # 1500 个 a + 句号 = 1501；句号在 2000 窗口的后 1/3（>1333）——第一块在此断句
    assert chunks[0].endswith("。")
    assert len(chunks[0]) == 1501
    assert chunks[1] == "b" * 1200


def test_long_paragraph_hard_cut_without_sentence_marks(tmp_path):
    body = "<p>" + ("x" * 4500) + "</p>"
    path = tmp_path / "book.epub"
    _write_epub(path, body, one_title="C1")

    chunks = [t for _, t in extract_epub_paragraphs(path)]
    assert [len(c) for c in chunks] == [2000, 2000, 500]


def test_chapter_title_prefers_h1_and_falls_back_to_title(tmp_path):
    path = tmp_path / "book.epub"
    _write_epub(path, "<h1>Part One</h1><p>One.</p>",
                two_body="<h2>Sub</h2><p>Two.</p>", one_title="Doc Title")

    paragraphs = extract_epub_paragraphs(path)
    # 章名口径同翻译 parser：h1 文本优先；h2 不作章名、但也是朗读段；第二文件无 h1/title → 空章名
    assert paragraphs == [
        ("Part One", "Part One"),
        ("Part One", "One."),
        ("", "Sub"),
        ("", "Two."),
    ]


def test_text_is_whitespace_normalized_like_text_content(tmp_path):
    path = tmp_path / "book.epub"
    _write_epub(path, "<p>  Multi\nword \t spacing  here. </p>", one_title="C1")

    assert extract_epub_paragraphs(path) == [("C1", "Multi word spacing here.")]
