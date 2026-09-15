import hashlib
import posixpath
import re
import zipfile

from lxml import etree

from ..epub_helper import get_content_opf, default_ns


BLOCK_TAGS = {"p", "li", "blockquote", "pre"}
SKIP_TAGS = {"script", "style", "nav", "svg", "noscript"}
MAX_TEXT_LENGTH = 2000


def normalize_text(value):
    return re.sub(r"\s+", " ", value or "").strip()


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
    """Return paragraphs in OPF spine order as ``(chapter, text)`` tuples."""
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
                root = etree.fromstring(archive.read(resource), parser=etree.XMLParser(resolve_entities=False, no_network=True))
            except (KeyError, etree.XMLSyntaxError):
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
