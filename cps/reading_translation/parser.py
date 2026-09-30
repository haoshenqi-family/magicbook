import hashlib
import html
import posixpath
import re
import zipfile

from lxml import etree

from .. import logger
from ..epub_helper import get_content_opf, default_ns


log = logger.create()


BLOCK_TAGS = {"p", "li", "blockquote", "pre"}
SKIP_TAGS = {"script", "style", "nav", "svg", "noscript"}
MAX_TEXT_LENGTH = 2000

# 未定义命名实体（&nbsp; 等）在 XML 宽松解析下以字面量进入文本，统一按
# 实体语法展开；限定 &name; 完整形态避免 HTML5 无分号旧实体误伤普通文本
# （如 "AT&T;" 里的 &T; 不是已知实体，unescape 原样返回）。
_NAMED_ENTITY_RE = re.compile(r"&([A-Za-z][A-Za-z0-9]*);")


def normalize_text(value):
    value = _NAMED_ENTITY_RE.sub(lambda m: html.unescape(m.group(0)), value or "")
    return re.sub(r"\s+", " ", value).strip()


def text_hash(value):
    return hashlib.sha256(normalize_text(value).encode("utf-8")).hexdigest()


def split_long_text(value, max_length=MAX_TEXT_LENGTH):
    value = normalize_text(value)
    if len(value) <= max_length:
        return [value] if value else []
    chunks = []
    remaining = value
    # Prefer sentence boundaries, then use a hard boundary as a safe fallback.
    sentence_pattern = re.compile(r"(?<=[.!?;。！？；])\s+")
    while len(remaining) > max_length:
        candidate = remaining[:max_length + 1]
        boundaries = [m.end() for m in sentence_pattern.finditer(candidate) if m.end() <= max_length]
        cut = max(boundaries) if boundaries else max_length
        chunks.append(remaining[:cut].strip())
        remaining = remaining[cut:].strip()
    if remaining:
        chunks.append(remaining)
    return [chunk for chunk in chunks if chunk]


def _local_tag(node):
    """Element local tag name in lowercase (None for comments/PIs)."""
    return node.tag.split("}")[-1].lower() if isinstance(node.tag, str) else ""


def _block_ancestor_kind(node):
    """Walk parents via getparent() and report first BLOCK/SKIP ancestor tag.

    Why getparent() instead of iterancestors()/id(): lxml element proxies are
    created on demand and garbage collected — id(node) is NOT stable and
    iterancestors() yields ephemeral proxies. Materializing through the
    parent chain keeps real references alive for the duration of the checks.
    """
    parent = node.getparent()
    while parent is not None:
        tag = _local_tag(parent)
        if tag in BLOCK_TAGS:
            return "block"
        if tag in SKIP_TAGS:
            return "skip"
        parent = parent.getparent()
    return None


def _chapter_title(root):
    """Chapter heading: h1 first (real chapter name), <title> as fallback.

    Why: Calibre-converted books carry the book name in every split file's
    <title>, so title-first collapsed all chapters into the book title.
    """
    for xpath in ("//*[local-name()='h1']", "//*[local-name()='title']"):
        nodes = root.xpath(xpath)
        for node in nodes[:1]:
            title = normalize_text(" ".join(node.itertext()))
            if title:
                return title
    return ""


def extract_epub_paragraphs(file_path):
    """Return paragraphs in OPF spine order as ``(chapter, text)`` tuples.

    R101: 正文统一宽松解析（XMLParser recover 模式），单一路径、无严格/宽松
    双轨。真实世界的 EPUB 内容文件是「给人看的 HTML」而非良构 XML——未闭合
    的 <link>/<meta>/<br> 都属常态，严格 XML 会整文件拒收（生产 book 91 实测
    32/32 个 spine 文件全部 XMLSyntaxError，被静默 continue 跳过后整本 0 段，
    报 no translatable paragraphs found）。

    为什么不用 HTMLParser：HTML 树构建规则不允许 <p> 容器内嵌 <table>/<div>，
    解析时会被强制拆开，嵌套文本成为无块级祖先的孤儿而丢失（book 88 实测
    文本受损）；XML recover 模式对良构文件树级零改动（book 88 逐文件验证
    strict==recover），对坏文件自动修补标签错配（book 91 恢复 10 万字符
    完整正文）。未定义实体改为展开后，长文本变短会令分片数变化（book 88
    6667→4512，实体展开后新旧文本流逐字等价，且不再有整段只有 "&nbsp;"
    字面量的垃圾段落）。编码语义与旧严格解析一致：XML 声明优先，缺省
    UTF-8。
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
                # recover 模式下几乎不会走到这里（zip 缺文件、空内容等极端情况），
                # 但必须留痕：0 段报错时这是唯一能区分「无文本」与「解析失败」的证据。
                log.warning("whole-book translation: unparseable spine file %s in %s",
                            resource, file_path)
                continue
            if root is None:
                log.warning("whole-book translation: empty spine file %s in %s",
                            resource, file_path)
                continue
            chapter = _chapter_title(root)
            # Why: 物化成强引用列表再遍历。root.iter() 逐个产生的元素代理是
            # 临时对象，循环内 id(node) 存入 seen_nodes 后代理可能被 GC，后续
            # 元素复用同一地址，导致大量段落被误判「已见」而随机跳过（实测
            # 同一本书三次抽取分别得到 759/78/78 段，生产 3177 个 <p> 只剩
            # 128 段）。列表持有真实引用后地址稳定，嵌套去重才可靠。
            nodes = [node for node in root.iter() if _local_tag(node) in BLOCK_TAGS]
            for node in nodes:
                tag = _local_tag(node)
                if tag not in BLOCK_TAGS:
                    continue
                ancestor_kind = _block_ancestor_kind(node)
                if ancestor_kind is not None:
                    continue
                text = normalize_text(" ".join(node.itertext()))
                if not text:
                    continue
                for chunk in split_long_text(text):
                    paragraphs.append((chapter, chunk))
    return paragraphs
