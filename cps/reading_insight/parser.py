# cps/reading_insight/parser.py — R214 B：EPUB 内容速览解析（一次解析、多处消费）。
#
# Why 独立成第三份解析器而不复用 reading_translation/parser.py / reading_tts/extractor.py
# （HLD §3.1）：那两份绑着各自 job 的批次/计费生命周期，R214 明确「不改 job 内核」；
# 三份解析逻辑并存的重复度已记技术债，收口另立需求，不塞进 R214。
#
# 产出契约（LLD §3 / §4.1）：
#   chapters            [{title, level, href, paragraphCount, firstParagraph}]
#   paragraphCount/charCount/englishWordCount
#   declaredLanguages   [lang3, ...]（按 OPF 声明，不猜正文）
#   excerpt             [{chapter, text}] — 自首章起 ≤EXCERPT_MAX_CHARS 字；
#                       全书解析量超 MAX_PARSE_BYTES 的「大书」只出 chapters + 统计、
#                       不出摘录（摘录只为「先看文风」，不值得为超大书付内存代价）。
import html
import posixpath
import re
import zipfile

from lxml import etree

from .. import isoLanguages
from ..epub_helper import PURL_NAMESPACE, default_ns, get_content_opf
from ..reading_word_detail.service import WORD_RE

EXCERPT_MAX_CHARS = 1200
MAX_PARSE_BYTES = 8 * 1024 * 1024
FIRST_PARAGRAPH_MAX_CHARS = 200

BLOCK_TAGS = {"p", "li", "blockquote", "pre"}
SKIP_TAGS = {"script", "style", "nav", "svg", "noscript"}

NS = dict(default_ns, dc=PURL_NAMESPACE)
# 宽松解析与 reading_translation/parser 同款姿势：坏章节不拖垮整本（recover），
# 禁实体解析与网络访问（XXE 面与 epub_helper._safe_parser 对齐）。
_LOOSE_PARSER = etree.XMLParser(recover=True, resolve_entities=False, no_network=True)

# 未定义命名实体（&nbsp; 等）在 XML 宽松解析下以字面量进入文本，统一按实体语法展开
# （reading_translation/parser.py:23 同口径，独立实现以保持本模块零 job 依赖）。
_NAMED_ENTITY_RE = re.compile(r"&([A-Za-z][A-Za-z0-9]*);")


def _normalize_text(value):
    value = _NAMED_ENTITY_RE.sub(lambda m: html.unescape(m.group(0)), value or "")
    return re.sub(r"\s+", " ", value).strip()


def _local_tag(node):
    return node.tag.split("}")[-1].lower() if isinstance(node.tag, str) else ""


def _resolve(base_dir, href):
    """把 nav/ncx/manifest 里的相对 href 归一到 zip 内绝对路径（去掉 #fragment）。"""
    href = (href or "").split("#", 1)[0]
    return posixpath.normpath(posixpath.join(base_dir, href))


def _iter_blocks(root):
    """产出外层块级节点（p/li/blockquote/pre），跳过 SKIP 子树。

    Why 只取最外层块：li>p 同为块级，两层都数会把一段话计成两段（reading_translation
    的 _block_ancestor_kind 是同一判据的另一种实现）。块内不再下钻即天然去重。
    Why 子节点逆序入栈：栈是 LIFO，逆序压入才能以 pop() 得到文档序——摘录段序与
    firstParagraph 都依赖「第一段真的是第一段」。
    """
    stack = [root]
    while stack:
        node = stack.pop()
        tag = _local_tag(node)
        if tag in SKIP_TAGS:
            continue
        if tag in BLOCK_TAGS:
            yield node
            continue
        for child in reversed(list(node)):
            stack.append(child)


def _h1_or_title(root):
    for name in ("h1", "h2", "h3"):
        for node in root.iter():
            if _local_tag(node) == name:
                text = _normalize_text("".join(node.itertext()))
                if text:
                    return text
    for node in root.iter():
        if _local_tag(node) == "title":
            text = _normalize_text("".join(node.itertext()))
            if text:
                return text
    return ""


def _declared_languages(opf_tree):
    """OPF 全部 dc:language → lang3 去重保序（与 cps/epub.py 子项 A 的口径一致）。"""
    codes = []
    for raw in opf_tree.xpath("/pkg:package/pkg:metadata/dc:language/text()", namespaces=NS):
        code = isoLanguages.get_lang3(_normalize_text(raw).split("-", 1)[0].lower())
        if code and code not in codes:
            codes.append(code)
    return codes


def _manifest(opf_tree, opf_dir):
    items = {}
    for item in opf_tree.xpath("/pkg:package/pkg:manifest/pkg:item", namespaces=NS):
        item_id = item.get("id") or ""
        items[item_id] = {
            "href": _resolve(opf_dir, item.get("href") or ""),
            "media_type": (item.get("media-type") or "").lower(),
            "properties": (item.get("properties") or "").lower(),
        }
    return items


def _spine_hrefs(opf_tree, manifest):
    hrefs = []
    for ref in opf_tree.xpath("/pkg:package/pkg:spine/pkg:itemref", namespaces=NS):
        item = manifest.get(ref.get("idref") or "")
        if item and item["href"]:
            hrefs.append(item["href"])
    return hrefs


def _read(zf, path):
    try:
        return zf.read(path)
    except KeyError:
        return b""


def _parse_nav(zf, nav_path):
    """EPUB3 nav（properties 含 nav）：嵌套 <ol>/<li> → level，返回 {href: (title, level)}。"""
    root = etree.fromstring(_read(zf, nav_path), parser=_LOOSE_PARSER)
    nav_dir = posixpath.dirname(nav_path)
    toc_nav = None
    for node in root.iter():
        if _local_tag(node) != "nav":
            continue
        nav_type = " ".join(node.attrib.get(k, "") for k in node.attrib if k.endswith("type"))
        if "toc" in nav_type.lower():
            toc_nav = node
            break
        if toc_nav is None:
            toc_nav = node
    if toc_nav is None:
        return {}

    result = {}

    def walk(parent, level):
        for child in parent:
            if _local_tag(child) == "ol":
                walk(child, level + 1)
            elif _local_tag(child) == "li":
                title, href = "", ""
                for sub in child:
                    tag = _local_tag(sub)
                    if tag in ("a", "span") and not title:
                        title = _normalize_text("".join(sub.itertext()))
                        href = sub.get("href") or ""
                    elif tag == "ol":
                        walk(sub, level + 1)
                if title and href:
                    result[_resolve(nav_dir, href)] = (title, level)

    walk(toc_nav, 0)
    return result


def _parse_ncx(zf, ncx_path):
    """EPUB2 toc.ncx：navPoint 递归深度 → level，返回 {href: (title, level)}。"""
    root = etree.fromstring(_read(zf, ncx_path), parser=_LOOSE_PARSER)
    ncx_dir = posixpath.dirname(ncx_path)
    result = {}

    def walk(parent, level):
        for point in parent:
            if _local_tag(point) != "navpoint":
                continue
            title, href = "", ""
            for sub in point:
                tag = _local_tag(sub)
                if tag == "navlabel":
                    title = _normalize_text("".join(sub.itertext()))
                elif tag == "content":
                    href = sub.get("src") or ""
            if title and href:
                result[_resolve(ncx_dir, href)] = (title, level)
            walk(point, level + 1)

    # navPoint 挂在 navMap 下，直接从根迭代找不到；深度 1 起算（LLD §3）。
    nav_map = None
    for node in root.iter():
        if _local_tag(node) == "navmap":
            nav_map = node
            break
    walk(nav_map if nav_map is not None else root, 1)
    return result


def _toc_titles(zf, opf_tree, manifest):
    """nav 优先（EPUB3 语义权威），ncx 兜底；都没有 → {}（调用方退化按文件计章）。"""
    for item in manifest.values():
        if "nav" in item["properties"].split():
            titles = _parse_nav(zf, item["href"])
            if titles:
                return titles
    for item in manifest.values():
        if item["media_type"] == "application/x-dtbncx+xml":
            titles = _parse_ncx(zf, item["href"])
            if titles:
                return titles
    return {}


def _group_excerpt(pairs):
    """(title, text) 段落流 → [{chapter, text}]，总正文字符 ≤EXCERPT_MAX_CHARS。

    预算只计正文字符，拼接换行不计（LLD §3：摘录是「先看文风」的量，不是精确截断器）。
    """
    entries = []
    used = 0
    for title, text in pairs:
        room = EXCERPT_MAX_CHARS - used
        if room <= 0:
            break
        piece = text[:room]
        used += len(piece)
        if entries and entries[-1]["chapter"] == title:
            entries[-1]["text"] = entries[-1]["text"] + "\n\n" + piece
        else:
            entries.append({"chapter": title, "text": piece})
    return entries


def parse(path):
    opf_tree, opf_name = get_content_opf(path, default_ns)
    opf_dir = posixpath.dirname(opf_name)

    with zipfile.ZipFile(path) as zf:
        manifest = _manifest(opf_tree, opf_dir)
        spine_hrefs = _spine_hrefs(opf_tree, manifest)
        toc_titles = _toc_titles(zf, opf_tree, manifest)

        chapters = []
        paragraph_count = char_count = en_words = 0
        total_bytes = 0
        excerpt_pool = []

        for index, href in enumerate(spine_hrefs, 1):
            raw = _read(zf, href)
            total_bytes += len(raw)
            title, level = toc_titles.get(href, ("", 1))
            paragraphs_here = 0
            first_paragraph = ""

            if raw:
                try:
                    root = etree.fromstring(raw, parser=_LOOSE_PARSER)
                except etree.XMLSyntaxError:
                    # 单个坏章节只跳过统计、不拖垮整本；目录里仍保留该章（LLD §8
                    # 的「前端各区块独立降级」在解析层先兜一半）。
                    root = None
                if root is not None:
                    if not title:
                        title = _h1_or_title(root)
                    for node in _iter_blocks(root):
                        text = _normalize_text("".join(node.itertext()))
                        if not text:
                            continue
                        paragraphs_here += 1
                        paragraph_count += 1
                        char_count += len(text)
                        en_words += len(WORD_RE.findall(text))
                        if not first_paragraph:
                            first_paragraph = (
                                text if len(text) <= FIRST_PARAGRAPH_MAX_CHARS
                                else text[:FIRST_PARAGRAPH_MAX_CHARS] + "…")
                        excerpt_pool.append((title or ("章节 %d" % index), text))

            title = title or ("章节 %d" % index)
            chapters.append({
                "title": title,
                "level": level,
                "href": href,
                "paragraphCount": paragraphs_here,
                "firstParagraph": first_paragraph,
            })

    return {
        "chapters": chapters,
        "paragraphCount": paragraph_count,
        "charCount": char_count,
        "englishWordCount": en_words,
        "declaredLanguages": _declared_languages(opf_tree),
        # 大书（全书解析量超限）只出 chapters + 统计：摘录池整体丢弃，不做「截半段」
        # 的伪试读（LLD §3）。
        "excerpt": [] if total_bytes > MAX_PARSE_BYTES else _group_excerpt(excerpt_pool),
    }
