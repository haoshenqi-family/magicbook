# R233 AI 回复站内链接 · LLD

> 状态：**开发完成待验收**（2026-10-26）
> 工作项：R233（magicbook 单仓交付）· 迭代 1.0 · 目录 `docs/project/iterations/1.0/r233-ai-links/`
> 用户原话：「AI给出的本站链接应该可以直接跳转（在新窗口）。」

## 1. 范围与根因

AI 伴读抽屉的助手消息与历史消息都经 `cps/static/js/ai_chat.js::renderMarkdown()` 渲染。原实现只做
HTML 转义、围栏/行内代码、粗体和换行，既不解 Markdown 链接，也不识别裸站内路径，因此模型给出的
`/credits`、`/me`、`/book/252` 都只能读、不能点。

本轮只修改消息展示层，不改 `/ai/agent/*` 契约、SSE 帧、模型提示词、工具白名单、会话历史结构或 CSP。

## 2. 安全设计

1. **先转义再构造标签**：对整段文本先转义 `& < > " '`，再把受控占位还原为链接/代码/粗体，避免模型
   输出借由 Markdown 注入 HTML。
2. **href 白名单归一化**：只接受单个 `/` 开头的相对路径或当前 `window.location.origin` 开头的绝对
   URL；拒绝控制字符、反斜杠、协议相对 URL、外部 origin、非 HTTP(S) 协议与带 userinfo 的 URL。
3. **二次属性转义**：最终只把规范化后的 `pathname + search + hash` 写入 `href`，并按 HTML 属性上下文
   再转义一次。
4. **新窗口隔离**：所有链接固定 `target="_blank" rel="noopener noreferrer"`。
5. **代码块隔离**：围栏代码先占位，不参与裸路径扫描；行内代码只有“整段就是站内路径”时才变为链接。
6. **标点剥离**：裸路径尾部的中英文句末标点与括号不进入 `href`，避免复制链接时带上正文标点。

## 3. 实现落点

| 文件 | 改动 |
| --- | --- |
| `cps/static/js/ai_chat.js` | `escapeHtml()`、`normalizeSiteHref()`、`siteLink()`；重写 `renderMarkdown()` 的受控占位渲染顺序 |
| `cps/static/css/ai_chat.css` | 助手消息站内链接样式（蓝色下划线 + hover 深色）；用户消息链接保持白字可辨 |
| `tests/test_ai_message_links_r233.py` | Node 执行生产函数做真实渲染断言；覆盖安全与标点边界 |

## 4. 行为口径

| 场景 | 行为 |
| --- | --- |
| Markdown 站内链接 | 生成站内链接，链接文字保留 |
| 裸 `/credits` / `/me` / `/book/252` | 生成站内链接，展示原路径 |
| 当前 origin 绝对 URL | 生成站内链接，`href` 归一化为路径 |
| 查询参数 / fragment | 原样保留 |
| 中文/英文尾随标点或括号 | 留在链接外 |
| 围栏代码块 | 仍显示代码，不链接 |
| 行内代码恰好为站内路径 | 显示代码样式链接 |
| 外部 URL / `//host` / `javascript:` / 凭据 URL | 纯文本 |
| HTML 标签与事件属性 | 转义为文字，不执行 |

## 5. 测试

- 新增 `tests/test_ai_message_links_r233.py`：13 条，其中 Node 用生产 `renderMarkdown()` 跑 15 组输入，
  验证链接、同源归一化、查询/fragment、标点、代码与 XSS。
- 定向回归：`test_ai_message_links_r233.py` + `test_buddy_site_assistant.py` + `test_reader_r215_ui.py`
  + `test_buddy_voice.py`，共 **36 passed / 0 failed**。
- `node --check cps/static/js/ai_chat.js` 通过；`git diff --check` 通过。

## 6. 未做与风险

- 不把普通外部 URL 变成可点击链接：用户只要求本站链接，且外链会扩大钓鱼面。
- 不做 URL 短链、跳转确认页或域名白名单管理；当前 origin 即唯一边界。
- 本机自动化只验证渲染函数与静态资源；生产部署后仍需在 AI 抽屉真机点击确认新标签行为。
