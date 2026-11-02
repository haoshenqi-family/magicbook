"""R232 守卫：伴读面板不显示 token 用量，用量只在【设置】【积分】看。

为什么是源码断言：这轮的失效模式是「多了点东西」而不是「坏了」——没有任何异常、
没有报错、测试也不会红，只有用户看到聊天里每轮多一行灰字。反向也一样：以后有人
为了调试把 usage 渲染加回来，也同样是静默的。两头都只能靠字面量锁住。

记录侧不在本仓：moon-well 的 CreditServiceImpl.consumeForLlmTask 把 total_tokens
落库并写流水（remark「AI任务消耗 N token、每千 token 折 10 积分」），前端删掉渲染
不影响记账，也不影响积分页明细。
"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHAT_JS = os.path.join(ROOT, "cps", "static", "js", "ai_chat.js")
CHAT_CSS = os.path.join(ROOT, "cps", "static", "css", "ai_chat.css")
CREDITS_HTML = os.path.join(ROOT, "cps", "templates", "credits.html")
JS_DIR = os.path.join(ROOT, "cps", "static", "js")


def _read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def test_chat_js_does_not_render_token_usage():
    """面板里不得再出现 usage 的渲染节点或字段读取。"""
    src = _read(CHAT_JS)
    assert "ai-chat-usage" not in src, "伴读面板不得再渲染 token 用量（R232）"
    assert "promptTokens" not in src, "final 事件里的 usage 只许可用于调试，不得进 DOM"
    assert "completionTokens" not in src


def test_no_other_panel_script_renders_token_usage():
    """全站前端脚本都不许渲染 token 用量——面板自 R220 起全站挂载，漏一个页面就又冒出来。"""
    offenders = []
    for name in sorted(os.listdir(JS_DIR)):
        if not name.endswith(".js"):
            continue
        path = os.path.join(JS_DIR, name)
        if os.path.isdir(path):
            continue
        text = _read(path)
        if "promptTokens" in text or "completionTokens" in text or "ai-chat-usage" in text:
            offenders.append(name)
    assert not offenders, "这些脚本仍在读 usage 字段：%r" % offenders


def test_final_event_still_binds_conversation_id():
    """删用量不许顺手把 final 分支删掉：首条消息的会话 id 就靠它回传。"""
    src = _read(CHAT_JS)
    assert 'case "final"' in src
    start = src.index('case "final"')
    body = src[start:src.index("break;", start)]
    assert "conversationIdFromFinal" in body, "final 分支必须保留会话 id 回传（服务端建会话的唯一来源）"
    assert "obj.usage" not in body, "final 分支不得再消费 usage 做展示"


def test_chat_css_has_no_usage_style():
    """样式一并删掉，避免「节点没了但样式还在」的半截状态诱导后人加回去。"""
    css = _read(CHAT_CSS)
    assert ".ai-chat-usage" not in css


def test_credit_page_keeps_usage_ledger():
    """用量唯一的可见入口是【设置】【积分】的消耗明细：时间/类型/原因/功能/积分。

    「原因」列就是 moon-well 流水的 remark，含 token 数；这个表被删或改名，
    用户就再也看不到用量的来源解释了。
    """
    html = _read(CREDITS_HTML)
    assert 'id="credit-consume-rows"' in html
    assert "_('Reason')" in html, "消耗明细必须保留「原因」列（token 用量在这里）"
    assert "_('Feature')" in html
    assert "_('Credits')" in html
