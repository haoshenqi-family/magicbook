"""R280 小程序 AI 伴读（通用对话）+ 生词本下掉的静态锁。

钉住四件事：
1. tabBar 与页面清单换成 AI 对话页（R280 tab 文案「伴读」，R283 改为「AI」），
   pages/notebook 整目录消失；
2. 对话请求必须带 scene='general' 且不带任何书籍/网页上下文字段
   （否则后端会回落到网页助手 prompt，用户看到「正在浏览网页」）；
3. SSE 流式通道的关键件（enableChunked / onChunkReceived / UTF-8 分块解码 /
   对话单独超时）不能缺，且能用 Node 实测中文与 emoji 跨片段不乱码；
4. 首页、工程描述里不再宣传生词本功能。
"""

import json
import os
import subprocess

ROOT = "miniprogram"


def _read(relative):
    with open(os.path.join(ROOT, relative), encoding="utf-8") as handle:
        return handle.read()


def test_tabbar_swapped_to_chat_and_notebook_page_removed():
    app = json.loads(_read("app.json"))
    pages = app["pages"]
    assert "pages/chat/chat" in pages
    assert all("notebook" not in page for page in pages)
    assert not os.path.exists(os.path.join(ROOT, "pages", "notebook")), "生词本页目录必须删除"

    tabs = app["tabBar"]["list"]
    # R283 修改意见：tabBar 文案「伴读」→「AI」，其余三项不动
    assert [item["text"] for item in tabs] == ["复习", "AI", "词汇量", "我"]
    assert tabs[1]["pagePath"] == "pages/chat/chat"


def test_chat_requests_general_scene_without_book_context():
    chat = _read("pages/chat/chat.js")
    assert "scene: 'general'" in chat, "必须显式声明通用对话场景"
    assert "skipMemoryExtract: true" in chat, "通用闲聊默认不写长期记忆"
    assert "/ai/agent/chat" in _read("utils/api.js")
    for forbidden in ("bookId", "bookTitle", "pageText", "unfamiliarWords", "authors", "chapter"):
        assert forbidden not in chat, "通用对话不得携带书籍/网页上下文字段 " + forbidden


def test_sse_transport_is_complete():
    api = _read("utils/api.js")
    assert "enableChunked: true" in api
    assert "onChunkReceived" in api
    assert "Accept: 'text/event-stream'" in api
    assert "function decodeUtf8" in api and "carry" in api
    assert "parseSseBlock" in api
    assert "CONFIG.chatTimeout" in api
    # 连接期 401 单次刷新，且失败仍透传 errMsg（R277 的教训不能丢）。
    # R282 把 describeNetworkError 扩成 (err, url)，让报错带出真实请求地址；
    # 这里锁 chatStream 的 fail 分支仍调用它、并传入 SSE 自己的 chatUrl。
    assert "function describeNetworkError" in api
    assert "describeNetworkError(err, chatUrl)" in api
    assert "retried" in api
    config = _read("config.js")
    assert "chatTimeout: 180000" in config, "对话不能沿用 15s 普通请求超时"


def test_general_prompt_key_is_documented():
    readme = _read("README.md")
    assert "agent-chat-system-general" in readme
    assert "scene=general" in readme or "scene: 'general'" in readme
    assert "moon-well R243" in readme, "前后端部署顺序必须写明"


def test_notebook_is_not_advertised_as_a_miniprogram_feature():
    assert "生词本" not in _read("app.json")
    assert "生词本" not in _read("project.config.json")
    assert "生词本" not in _read("pages/login/login.wxml")
    # 词汇量测试仍会写回网页端生词本，这里只允许出现「网页端生词本」这种去向说明
    assert "生词本" not in _read("pages/test/test.wxml").replace("网页端生词本", "")


def test_utf8_chunk_decode_and_sse_frame_via_node():
    script = r"""
const api = require(process.cwd() + '/miniprogram/utils/api.js');
const source = '通用对话：中😀文';
const bytes = Buffer.from(source, 'utf8');
const cut = 5; // 故意切在某个汉字中间
const first = api.decodeUtf8(new Uint8Array(bytes.slice(0, cut)), []);
const second = api.decodeUtf8(new Uint8Array(bytes.slice(cut)), first.carry);
const joined = first.text + second.text;
if (joined !== source) { console.error('UTF8_MISMATCH', JSON.stringify(joined)); process.exit(1); }
if (second.carry.length !== 0) { console.error('TRAILING_BYTES'); process.exit(2); }
const ev = api.parseSseBlock('event: delta\ndata: {"text":"你好"}');
if (!ev || ev.name !== 'delta' || ev.data.text !== '你好') {
  console.error('SSE_PARSE_FAILED', JSON.stringify(ev)); process.exit(3);
}
const ev2 = api.parseSseBlock('event: final\ndata: {"conversationId":42}');
if (!ev2 || ev2.data.conversationId !== 42) { console.error('FINAL_PARSE_FAILED'); process.exit(4); }
console.log('SSE_OK');
"""
    result = subprocess.run(
        ["node", "-e", script],
        cwd=os.getcwd(), capture_output=True, text=True, check=False)
    assert result.returncode == 0, "Node 解码/分帧自检失败: " + result.stdout + result.stderr
    assert "SSE_OK" in result.stdout
