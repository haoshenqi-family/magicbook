"""整本朗读（听书）口径的段落提取器（magicbook R166 设计 §3.3）。

Why 不复用 reading_translation/parser.py：两套口径存在系统差异——翻译口径
（p/li/blockquote/pre、只收无块级祖先的最外层、句界正则切块）产出的文本与前端
朗读口径对不上，而 TTS 永久缓存键 = SHA-256(trim(段落原文))，预生成用错口径 =
缓存永不命中 = 整本白合成（烧积分 + 算力）。翻译场景口径差异只造成部分段
miss → 现场翻译（代价小），TTS 预热场景 miss = 纯浪费（代价大）。

本模块逐条复刻 epub.js 朗读口径（R142 脚本已对 book 145《Matilda》1393 段
全量实测验证缓存键一致：同一文本两次调用 4.7s 合成 → 0.028s 命中）：

- 段落选择 = ``PARAGRAPH_SELECTOR``（p, li, blockquote, h1..h6, div）：
  DIV 含任意块级后代则跳过（文字归子元素）；嵌套匹配按 querySelectorAll
  语义双收（li 内的 p 与外层 li 各产一段，服务层按 text_hash 去重）；
- 文本 = textContent 全后代拼接 → 空白归一 → trim（实体在 XML 宽松解析下
  按字面量进入文本，沿用翻译 parser 的实体展开经验）；
- 超长段按连播切块（bookPlayerChunkTexts）：≤2000，后 1/3 窗口从尾向头找
  句读（。！？；… 或 .!? + 后跟空格/结尾），找不到硬切——必须按连播口径而非
  单段朗读的截断口径，否则 >2000 的段在听书模式仍要现合成。

口径契约测试双锁（tests/test_reading_tts_extractor.py）：JS 常量静态锁 +
样例 EPUB 提取序列快照锁，epub.js 口径漂移即红。
"""

import posixpath
import re
import zipfile

from lxml import etree

from .. import logger
from ..epub_helper import get_content_opf, default_ns
from ..reading_translation.parser import _chapter_title, _local_tag, normalize_text

log = logger.create()

# 与 epub.js PARAGRAPH_SELECTOR 逐字对应（口径契约测试静态锁定）
PARAGRAPH_TAGS = {"p", "li", "blockquote", "h1", "h2", "h3", "h4", "h5", "h6", "div"}
# 与 epub.js BLOCK_CHILD_SELECTOR 对应：DIV 含这些块级后代即跳过（querySelector 语义 = 任意层级后代）
BLOCK_CHILD_TAGS = {"p", "li", "div", "blockquote", "section", "article", "table",
                    "ul", "ol", "h1", "h2", "h3", "h4", "h5", "h6"}
# 与 epub.js BOOK_TTS_MAX 一致：单请求上限，超长按连播切块
BOOK_TTS_MAX = 2000

# bookPlayerChunkTexts 的句读集：中文句读直接断；英文句读要求后跟空格/结尾（防小数点）
_CN_SENTENCE_MARKS = "。！？；…"
_EN_SENTENCE_MARKS = ".!?"
# JS Math.floor(BOOK_TTS_MAX * 2 / 3) —— 后 1/3 窗口起点
_LOOKBACK_BOUND = BOOK_TTS_MAX * 2 // 3

_WS_RE = re.compile(r"\s+")


def chunk_long_text(value):
    """超长段切块，逐语句复刻 epub.js bookPlayerChunkTexts（连播口径）。

    与翻译 parser.split_long_text 的差异（Why 不能复用）：后者用「边界 ≤2000+1
    窗口内取最大句界 + 消费边界后空白」，且边界集合不含「后跟空格」约束——两种
    算法在多数文本上切点相同，但长段无空格或句读密集时结果不同，缓存键随之分叉。
    """
    text = _WS_RE.sub(" ", value or "").strip()
    chunks = []
    pos = 0
    while pos < len(text):
        if len(text) - pos <= BOOK_TTS_MAX:
            chunks.append(text[pos:])
            break
        window = text[pos:pos + BOOK_TTS_MAX]
        cut = -1
        for j in range(len(window) - 1, _LOOKBACK_BOUND - 1, -1):
            ch = window[j]
            if ch in _CN_SENTENCE_MARKS:
                cut = j + 1
                break
            if ch in _EN_SENTENCE_MARKS:
                after = window[j + 1] if j + 1 < len(window) else ""
                if after == "" or after == " ":
                    cut = j + 1
                    break
        if cut < 0:
            cut = BOOK_TTS_MAX
        chunks.append(text[pos:pos + cut])
        pos += cut
    return [c for c in chunks if c]


def _has_block_descendant(node):
    """epub.js el.querySelector(BLOCK_CHILD_SELECTOR)：任意层级后代（不含自身）。"""
    for desc in node.iter():
        if desc is node:
            continue
        if _local_tag(desc) in BLOCK_CHILD_TAGS:
            return True
    return False


def extract_epub_paragraphs(file_path):
    """按 OPF spine 顺序返回 (chapter, chunk) 元组，口径与阅读器朗读/连播完全一致。

    解析沿用整本翻译的宽松策略（R101：真实世界的 EPUB 是「给人看的 HTML」，
    XMLParser recover 单一路径，book 91 实测 32/32 文件严格模式全拒收）。
    """
    tree, opf_name = get_content_opf(file_path, default_ns)
    opf_dir = posixpath.dirname(opf_name)
    manifest = {}
    for item in tree.xpath("/pkg:package/pkg:manifest/pkg:item", namespaces=default_ns):
        manifest[item.get("id")] = item.get("href", "")
    spine_ids = tree.xpath("/pkg:package/pkg:spine/pkg:itemref/@idref", namespaces=default_ns)
    paragraphs = []
    with zipfile.ZipFile(file_path) as archive:
        for spine_id in spine_ids:
            href = manifest.get(spine_id)
            if not href:
                continue
            resource = posixpath.normpath(posixpath.join(opf_dir, href.split("#", 1)[0]))
            try:
                root = etree.fromstring(archive.read(resource), parser=etree.XMLParser(
                    recover=True, resolve_entities=False, no_network=True))
            except (KeyError, ValueError, etree.XMLSyntaxError):
                log.warning("whole-book tts: unparseable spine file %s in %s",
                            resource, file_path)
                continue
            if root is None:
                log.warning("whole-book tts: empty spine file %s in %s", resource, file_path)
                continue
            chapter = _chapter_title(root)
            # Why 物化列表再遍历：lxml 元素代理按需创建且可能被 GC（翻译 parser 同款教训，
            # id 不稳定会让嵌套去重/遍历随机漏元素）
            nodes = [node for node in root.iter() if _local_tag(node) in PARAGRAPH_TAGS]
            for node in nodes:
                tag = _local_tag(node)
                if tag == "div" and _has_block_descendant(node):
                    # DIV 含块级后代 = 容器，文字归子元素（前端同款跳过）
                    continue
                text = normalize_text("".join(node.itertext()))
                if not text:
                    continue
                for chunk in chunk_long_text(text):
                    paragraphs.append((chapter, chunk))
    return paragraphs
