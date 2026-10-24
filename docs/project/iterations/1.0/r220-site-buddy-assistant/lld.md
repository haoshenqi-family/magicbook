# LLD — R220 Buddy 全站助手

> 状态：开发中（2026-10-24，worktree `../magicbook-buddy`，分支 `feat/r206-buddy`）

## 1. 范围

- Buddy 悬浮按钮与聊天抽屉从三个阅读模板扩展到所有登录后的 `layout.html` 页面；阅读器保留原有专用注入，避免模板结构差异。
- 非阅读页进入 moon-well 既有 web 场景：`bookId=null`，使用 `agent-chat-system-web` 提示词；阅读页仍传书籍上下文，提示词不变。
- 每次发送时采集当前页面可见文本，剔除脚本、样式、导航、页头页脚、iframe 和 Buddy 面板自身，服务端仍按 8000 字符截断。

## 2. 实现

- `cps/templates/layout.html`：页面脚本后引入 `ai_chat_panel.html`，仅对已认证且非匿名用户渲染。
- `cps/static/js/ai_page_extract.js`：新增 `site` 场景识别与 DOM 上下文提取，输出页面标题、主标题和正文文本。
- `cps/static/js/ai_chat.js`：`bookId` 为空时请求全站会话列表，按 `bookId` 是否存在过滤为当前场景会话；发送不再依赖 `bookId`；站点会话标题用当前页面标题；记忆面板在非阅读页不请求 book profile。
- `cps/render_template.py`：统一注入 `ai_context_title`，避免模板未显式传 `title` 时上下文标题缺失。
- `cps/web.py`：MinIO `img-src` 放行条件改为 HTML 响应；JSON/XML/图片/OPDS 等非 HTML 响应维持窄面 CSP。
- i18n：新增 `Ask about this page...`（中文：就本页内容提问…），已编译 zh_Hans_CN catalog。

## 3. 边界

- 登录页、注册页与匿名访问不显示 Buddy，避免无 moon-well token 的入口反复 401。
- 会话归属由 moon-well 新建会话时落为 `bookId=0`；前端列表以 `bookId` 为空/0 视为站点会话。
- 网页场景沿用 moon-well 现有隐私语义：系统提示词要求用户未明确要求时不主动写入长期记忆；本仓不额外强制 `skipMemoryExtract`。
- 本轮不改 moon-well 代码与接口契约。

## 4. 验证

- `node --check cps/static/js/ai_page_extract.js cps/static/js/ai_chat.js`
- `pytest tests/test_csp_media.py tests/test_buddy_page.py tests/test_buddy_site_assistant.py`
- 待真机：首页/每日学习/积分页看到 Buddy，图片正常，提问能引用当前页内容；阅读页书籍上下文与会话不受影响。
