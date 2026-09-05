import zipfile

from cps.reading_translation.parser import extract_epub_paragraphs, split_long_text, text_hash


def _write_epub(path):
    container = """<container xmlns='urn:oasis:names:tc:opendocument:xmlns:container'><rootfiles><rootfile full-path='OPS/content.opf'/></rootfiles></container>"""
    opf = """<package xmlns='http://www.idpf.org/2007/opf'><manifest>
      <item id='one' href='one.xhtml' media-type='application/xhtml+xml'/>
      <item id='two' href='two.xhtml' media-type='application/xhtml+xml'/>
    </manifest><spine><itemref idref='one'/><itemref idref='two'/></spine></package>"""
    one = "<html xmlns='http://www.w3.org/1999/xhtml'><head><title>Chapter One</title></head><body><div><p> First   paragraph. </p><p>Second.</p></div></body></html>"
    two = "<html xmlns='http://www.w3.org/1999/xhtml'><body><h1>Chapter Two</h1><p>Third.</p><script>ignore me</script></body></html>"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("META-INF/container.xml", container)
        archive.writestr("OPS/content.opf", opf)
        archive.writestr("OPS/one.xhtml", one)
        archive.writestr("OPS/two.xhtml", two)


def test_extracts_in_spine_order_and_skips_nested_or_script_nodes(tmp_path):
    path = tmp_path / "book.epub"
    _write_epub(path)

    assert extract_epub_paragraphs(path) == [
        ("Chapter One", "First paragraph."),
        ("Chapter One", "Second."),
        ("Chapter Two", "Third."),
    ]


def test_long_paragraph_prefers_sentence_boundaries_and_hash_is_trimmed():
    text = "A sentence. " * 300
    chunks = split_long_text(text)

    assert len(chunks) > 1
    assert all(0 < len(chunk) <= 2000 for chunk in chunks)
    assert text_hash("  hello  ") == text_hash("hello")
