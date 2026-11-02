"""R233: AI 回复中的站内链接与 XSS 边界。

Why 用 Node 跑真实 renderMarkdown：只按源码文本断言 ``target="_blank"`` 无法证明
URL 归一化、代码块排除、标点剥离与转义顺序真的成立。这里直接截取生产函数片段，
在最小 window 环境中执行，再把渲染结果交给 Python 断言。
"""

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
CHAT_JS = ROOT / "cps" / "static" / "js" / "ai_chat.js"
ORIGIN = "https://magicbook.haoshenqi.top"


def _render_cases():
    source = CHAT_JS.read_text(encoding="utf-8")
    start = source.index("  function escapeHtml(")
    end = source.index("  /** 工具芯片", start)
    functions = source[start:end]
    cases = {
        "markdown": "[积分页](/credits)",
        "bare_paths": "入口：/credits、/me、/book/252。",
        "wrapped_paths": "（/credits）和（/me）。",
        "absolute": "打开 https://magicbook.haoshenqi.top/me 即可。",
        "query_fragment": "查看 /credits?tab=ledger#top",
        "punctuation": "去 /credits). 或 /me。",
        "external": "参考 https://evil.example/credits",
        "javascript": "[不要点](javascript:alert(1))",
        "protocol_relative": "[不要点](//evil.example/me)",
        "credentials": "https://magicbook.haoshenqi.top@evil.example/me",
        "html_target": "[<img src=x onerror=alert(1)>](/me)",
        "html_bare": '<img src=x onerror="alert(1)"> /me',
        "fenced_code": "```\n/credits\n[积分](/me)\n```",
        "inline_code": "路径是 `/credits`",
        "bold_link": "**[积分页](/credits)**",
    }
    script = """
const fs = require("fs");
const source = fs.readFileSync(process.argv[1], "utf8");
const start = source.indexOf("  function escapeHtml(");
const end = source.indexOf("  /** 工具芯片", start);
global.window = { location: { origin: process.argv[2] } };
eval(source.slice(start, end));
const cases = JSON.parse(process.argv[3]);
const out = {};
for (const [name, input] of Object.entries(cases)) out[name] = renderMarkdown(input);
process.stdout.write(JSON.stringify(out));
"""
    result = subprocess.run(
        ["node", "-e", script, str(CHAT_JS), ORIGIN, json.dumps(cases)],
        capture_output=True,
        check=True,
        text=True,
        timeout=20,
    )
    return json.loads(result.stdout)


@pytest.fixture(scope="module")
def rendered():
    if shutil.which("node") is None:
        pytest.skip("node is required to execute the production renderMarkdown")
    return _render_cases()


def _anchors(html):
    return re.findall(r'<a\b[^>]*href="([^"]+)"[^>]*>(.*?)</a>', html, re.S)


def _assert_safe_new_window(html):
    for anchor in re.findall(r"<a\b[^>]*>", html):
        assert 'target="_blank"' in anchor
        assert 'rel="noopener noreferrer"' in anchor


def test_markdown_site_link_opens_new_window(rendered):
    html = rendered["markdown"]
    assert _anchors(html) == [("/credits", "积分页")]
    _assert_safe_new_window(html)


def test_bare_paths_are_links_but_punctuation_stays_outside(rendered):
    html = rendered["bare_paths"]
    assert [href for href, _ in _anchors(html)] == ["/credits", "/me", "/book/252"]
    assert "、</a>" not in html and "</a>。" in html
    _assert_safe_new_window(html)


def test_same_origin_absolute_url_and_query_fragment(rendered):
    absolute = rendered["absolute"]
    assert _anchors(absolute) == [("/me", "/me")]
    _assert_safe_new_window(absolute)

    query = rendered["query_fragment"]
    assert _anchors(query) == [("/credits?tab=ledger#top", "/credits?tab=ledger#top")]


def test_trailing_prose_punctuation_is_not_part_of_href(rendered):
    html = rendered["punctuation"]
    assert [href for href, _ in _anchors(html)] == ["/credits", "/me"]
    assert "</a>)." in html and "</a>。" in html


def test_chinese_brackets_stay_outside_href(rendered):
    html = rendered["wrapped_paths"]
    assert [href for href, _ in _anchors(html)] == ["/credits", "/me"]
    assert "（<a " in html and "</a>）" in html


@pytest.mark.parametrize(
    "case",
    ["external", "javascript", "protocol_relative", "credentials"],
)
def test_non_site_urls_never_become_links(rendered, case):
    html = rendered[case]
    assert "<a " not in html
    assert "href=" not in html


def test_html_payload_is_escaped_before_link_rendering(rendered):
    for case in ("html_target", "html_bare"):
        html = rendered[case]
        assert "<img" not in html
        assert "onerror=\"alert" not in html
    _assert_safe_new_window(rendered["html_target"])


def test_code_blocks_do_not_link_but_path_only_inline_code_does(rendered):
    fenced = rendered["fenced_code"]
    assert "<pre><code>" in fenced
    assert "<a " not in fenced
    assert "/credits" in fenced and "[积分](/me)" in fenced

    inline = rendered["inline_code"]
    assert _anchors(inline) == [("/credits", "<code>/credits</code>")]
    _assert_safe_new_window(inline)


def test_bold_wrapping_a_site_link_keeps_one_strong_element(rendered):
    html = rendered["bold_link"]
    assert html.count("<strong>") == 1
    assert _anchors(html) == [("/credits", "积分页")]


def test_site_link_styles_are_scoped_to_chat_messages():
    css = (ROOT / "cps" / "static" / "css" / "ai_chat.css").read_text(encoding="utf-8")
    assert ".ai-chat-msg.assistant .ai-chat-site-link" in css
    assert "text-decoration: underline" in css
