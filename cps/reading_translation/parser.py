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
            title_nodes = root.xpath("//*[local-name()='title']/text()")
            if not title_nodes:
                title_nodes = root.xpath("//*[local-name()='h1']/text()")
            chapter = normalize_text(" ".join(title_nodes[:1]))
            seen_nodes = set()
            for node in root.iter():
                tag = etree.QName(node).localname.lower() if isinstance(node.tag, str) else ""
                if tag not in BLOCK_TAGS or id(node) in seen_nodes:
                    continue
                if any((ancestor.tag if isinstance(ancestor.tag, str) else "").split("}")[-1].lower() in BLOCK_TAGS
                       for ancestor in node.iterancestors()):
                    continue
                if any((ancestor.tag if isinstance(ancestor.tag, str) else "").split("}")[-1].lower() in SKIP_TAGS
                       for ancestor in node.iterancestors()):
                    continue
                seen_nodes.add(id(node))
                text = normalize_text(" ".join(node.itertext()))
                for chunk in split_long_text(text):
                    paragraphs.append((chapter, chunk))
    return paragraphs
