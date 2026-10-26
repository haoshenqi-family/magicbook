# AI 回复站内链接

> 读者：修改 `cps/static/js/ai_chat.js` 消息渲染或伴读链接行为的人。
> 状态：现行（2026-10-26 R233，开发完成待验收）。
> 需求基线：[`../requirements.md`](../requirements.md) R233；本次实现：[`../../../project/iterations/1.0/r233-ai-links/lld.md`](../../../project/iterations/1.0/r233-ai-links/lld.md)。

## 实现方式

- `renderMarkdown()` 先把整段回复做 HTML 转义，再按受控顺序处理围栏代码块、行内代码、
  Markdown 链接、裸路径与粗体；不会把模型原文直接拼入 DOM。
- 只接受两类目标：以单个 `/` 开头的站内相对路径，以及以当前
  `window.location.origin` 开头的绝对 URL。`URL` 规范化后必须仍是同一 origin。
- 链接统一输出 `target="_blank" rel="noopener noreferrer"`；`href` 只保留
  `pathname + search + hash`，再做一次属性转义。
- 裸路径支持中文上下文与括号；紧邻的句号、逗号、冒号、问号及中英文括号不计入 `href`。
- 整段行内代码恰好是站内路径时（AI 指南常用 `` `/credits` `` 写法）渲染为可点击的代码链接；
  围栏代码块保持代码样式，不生成链接。

## 允许与拒绝范围

| 输入 | 行为 |
| --- | --- |
| `[积分页](/credits)` | 可点击，新窗口 |
| `/me`、`/book/252`、`/credits?tab=ledger#top` | 可点击，查询参数与 fragment 保留 |
| `https://magicbook.haoshenqi.top/me` | 可点击；渲染时归一化为站内 `/me` |
| `https://evil.example/me` | 纯文本 |
| `//evil.example/me` | 纯文本 |
| `javascript:alert(1)`、含用户名密码的 URL | 纯文本 |
| 围栏代码块中的路径 | 纯文本代码，不链接 |
| 含 `<img onerror=...>` 等 HTML | 一律转义为文字 |

## 边界条件

- 判断基准是**当前页面 origin**，不是硬编码生产域名；所以预发/本地环境也只链本站。
- 外部 URL 即便长得像本站（例如当前域名作为 userinfo）也不会通过 origin 校验。
- 链接只改变可导航性，不调用任何后端接口，也不扩大 AI 工具或用户权限。
- 流式回答每个 `delta` 仍会整体重渲染；链接属性由同一函数确定性生成，不会因分片到达而改变。

## 测试锚点

- `tests/test_ai_message_links_r233.py`：用 Node 执行生产 `renderMarkdown()`，覆盖 Markdown 链接、
  裸路径、同源绝对 URL、查询/fragment、中英文标点、围栏/行内代码、外部 URL、协议相对 URL、
  `javascript:`、凭据 URL 与 HTML 注入。
- `tests/test_reader_r215_ui.py` / `tests/test_buddy_site_assistant.py` / `tests/test_buddy_voice.py`：
  既有面板结构与语音链路的回归守卫。
