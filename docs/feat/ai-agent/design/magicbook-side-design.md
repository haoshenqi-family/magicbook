# 伴读 Agent 化：magicbook 侧改造设计（前端 + 薄代理 + 数据迁出）

**特性代号**：`ai-agent`
**日期**：2026-09-29
**状态**：设计已完成，待排期开发（本期仅设计，不开发）
**对应后端设计**：moon-well `docs/feat/ai-agent/design/ai-agent-backend-design.md`（R66–R70 对话链）
**决策来源**：magicbook requests R90–R95 / moon-well requests R66–R70

## 1. 背景与定位

伴读 agent 完全后端化到 moon-well（D1），magicbook 的角色收敛为三件事：

1. **阅读上下文采集**（前端注入，D4）：当前页文本/章节/生词由阅读器采集，随聊天请求上行；
2. **伴读 drawer UI**：多会话、工具芯片展示（tool_call/tool_result 事件可视化）；
3. **薄代理**：`/ai/*` 端点透传 moon-well，含 SSE 流式转发。

`cps/ai/` 包（约 1750 行）随之退役，本设计给出退役清单与数据迁移方案。

## 2. 前端注入上下文（D4 落地）

`window.AICompanion` 桥接协议**保持不变**（ai_page_extract.js / reader 桥接的 `getChapter()`、`getUnfamiliarWords()`、`getPageContextAsync()` 全部复用），仅请求体扩展：

```js
// ai_chat.js 发送体（现状字段保留 + 语义调整）
POST /ai/agent/chat   （经 magicbook 薄代理）
{
  conversationId,                  // 可选，null 则新建
  message,
  bookContext: {                   // D4：前端采集，每轮重新上行，不进历史
    bookId, bookTitle, authors[], tags[],
    chapter,                       // 当前章节名
    pageText,                      // 当前页原文（ getPageContextAsync() ）
    unfamiliarWords[]              // 当前页生词（ getUnfamiliarWords() ）
  }
}
```

截断规则由 moon-well 侧执行（moon-well 设计 §5.2）；前端不做额外截断（采集层仅限 PDF 分页提取的既有上限）。

## 3. 数据边界（已拍板，R92/R93 逐表核实）

| 数据 | 存储 | 处置 |
| --- | --- | --- |
| calibre `metadata.db` | magicbook 本地 | **不动**（Calibre 家族互操作契约；R78 评审既定边界） |
| app.db 21 张表 | magicbook 本地 | **零表迁移**（消费者全在本地：web/阅读器/Kobo 协议/翻译台账） |
| `reading_translation_job/item` | app.db | 留 magicbook（运维数据，跟书走，D7） |
| `ai_conversation/ai_message/ai_user_memory` | ai_companion.db（SQLite） | **全量迁** moon-well MySQL（§6） |
| `ai_config/ai_provider` | ai_companion.db | **退役**（provider 收敛 Nacos `ai.llm.configs`，D8） |

**不挂载** magicbook SQLite 给 moon-well（R94 决策）；TED 直写线维持现状不扩大。

## 4. 薄代理设计（`/ai/*` 端点）

### 4.1 端点清单（替换现有 `cps/ai/routes.py` 的代理部分）

| magicbook 端点 | 转发目标（moon-well） | 形态 |
| --- | --- | --- |
| `POST /ai/agent/chat` | `/ai/agent/chat` | **SSE 流式透传**（§4.2） |
| `GET /ai/agent/conversations?bookId=` | `/ai/agent/conversations` | JSON |
| `GET /ai/agent/history?conversationId=` | `/ai/agent/history` | JSON |
| `POST /ai/agent/memory`（查/改本人记忆） | `/ai/agent/memory` | JSON |

实现模式：复用 `_moonwell_proxy` 的身份头 + JWT 管理与自动刷新（cps/web.py），与 credits/reading-translate 代理同构。

### 4.2 SSE 流式转发（本设计的核心技术点）

现有 `_moonwell_proxy` 是 20s 阻塞超时的 JSON 转发，不能直接用于 SSE。新增流式变体：

```python
def _moonwell_proxy_sse(path, payload):
    """SSE 流式转发：requests stream=True 逐 chunk 转发，无整体超时，
    每连接 idle 超时 300s 对齐 moon-well 侧 SseEmitter 预算。"""
    # 响应头：Content-Type: text/event-stream、X-Accel-Buffering: no、
    # Cache-Control: no-cache、禁用代理缓冲（Traefik 层无请求体缓冲问题，
    # 响应缓冲需确认 fnOS 上 magicbook 容器前置无 Nginx 类缓冲层）
```

要点：

1. **Tornado/gevent 兼容**：magicbook 是 gevent WSGIServer（cps/ai/database.py 注释确认），SSE 长连接占 greenlet 而非 OS 线程，并发能力充足；流式转发用 `requests` 的 `stream=True` 逐 chunk yield，不缓冲整段。
2. **token 刷新在连接建立前完成**（SSE 连接中途 401 无法重放——流已开始无法回滚；刷新逻辑前置到代理函数入口）。
3. **断连处理**：客户端断开时及时关闭上游连接（moon-well 侧 SseEmitter onCompletion/onTimeout 回调已有钩子）。
4. **CSRF**：沿用现有 EPUB 阅读器长期打开场景的 CSRF token 嵌入方案（ai/__init__.py:94 注释）。

### 4.3 现有 `cps/ai/` 退役清单

| 模块 | 处置 |
| --- | --- |
| `routes.py` 聊天/会话/历史端点 | 替换为 §4.1 薄代理 |
| `openai_compat.py` / `deepseek.py` / `base.py` / `registry.py` | **删除**（provider 调用归 moon-well LlmGateway） |
| `crypto.py` | **删除**（Nacos 托管，无需 DB 加密层） |
| `database.py` / `models.py` | **删除**（表迁 MySQL；迁移完成后本地 SQLite 文件归档） |
| `memory.py`（相关性注入/抽取 prompt） | 抽取 prompt 迁 moon-well（AgentMemoryService）；正则白名单作为 prompt 引导素材 |
| `prompts.py`（chat-system 模板） | 迁 moon-well Nacos prompt registry（与 reading-companion 模板同库管理） |
| `ai_admin.html` 管理页 | provider 管理部分下线；全局开关读 moon-well 配置（代理透传状态） |
| 前端 `ai_chat.js` / `ai_chat.css` / drawer | **保留并升级**（§5） |

## 5. 前端 drawer 升级（工具芯片交互）

### 5.1 事件渲染

现有 SSE 解析（`data: {delta}` / `[DONE]`）升级为分型事件（协议见 moon-well 设计 §8）：

```text
delta       → 正文追加（打字机，同现状）
tool_call   → 插入「芯片」：🔍 lookup_word "sidebars"…（可点击展开 argsSummary）
tool_result → 芯片收尾：✓ 200ms 词典命中 / ✗ error（可展开 resultSummary）
final       → 收尾：显示 token 用量与积分消耗（轻量角标）
error       → 错误条（同现状错误处理）+ 可重试
```

芯片默认折叠为单行（图标 + 工具名 + 参数摘要 + 状态），点击展开完整 args/result——避免工具轨迹刷屏打断阅读流。

### 5.2 会话列表与降级

- 会话列表/历史读取改走薄代理（moon-well MySQL 数据源）。
- **降级模式**：`final` 事件缺失（旧后端/网关不支持 tools）时按纯文本渲染——协议里 `delta` 同时携带 `data` 兼容字段，前端旧解析逻辑兜底。

## 6. 数据迁移（ai_companion.db → moon-well MySQL）

### 6.1 迁移脚本（一次性，Python，跑在 magicbook 容器或宿主）

```text
输入：ai_companion.db（SQLite，5 张表）
输出：moon-well MySQL ai_conversation / ai_message / ai_user_memory

流程：
1. 读 SQLite 全量（5 表：ai_config、ai_provider、ai_conversation、ai_message、ai_user_memory）
2. ai_conversation / ai_message / ai_user_memory → 逐行 INSERT MySQL（moon-well 表结构）
   - id 映射：SQLite 自增 id 与 MySQL 自增 id 建映射表（migration_id_map），
     或直接保留原 id（MySQL AUTO_INCREMENT 起点拨到 max(id)+1）——推荐后者，简单
   - user_id 对齐：magicbook user.id 与 moon-well user.id 的映射关系需在迁移前核实
     （OIDC 统一认证后两系统用户体系是否同 id；不同则建 user 映射，迁移时换算）
   - 时间戳：SQLite naive UTC → MySQL DATETIME（保持 UTC 语义，与 moon-well now_cn 体系对齐）
3. ai_config / ai_provider 不迁移，记录快照归档（provider 收敛 Nacos）
4. 验证：行数对账 + 抽样内容比对（conversationId 连续性、message 归属）
```

### 6.2 切换与回退

- **切换点**：新前端发 `/ai/agent/chat`（代理到 moon-well）即为切换；旧 `cps/ai` 端点保留只读（历史会话展示）直到迁移验证完成，随后下线。
- **双写窗口**：无（切换是原子的——旧端点停写、新端点开写；期间旧会话在旧库只读、新会话在新库）。
- **回退**：迁移前后端点开关切换（feature flag），出问题切回旧端点（旧库数据未动，天然可回退）。
- **备份**：迁移前 `ai_companion.db` 文件级备份（与 book89 迁移同款操作纪律，R80）。

### 6.3 迁移前必须核实的一项

**user_id 映射**。magicbook app.db 的 user 表与 moon-well MySQL 的 user 表是否同 id 体系。两系统经 OIDC（authentik）统一认证（sso-user-unification 特性），大概率 subject 对齐，但需实测核实——这是迁移脚本的前置条件，开发期第一件事。

## 7. 测试与验收（开发期执行，本期仅设计）

- **薄代理单测**：SSE 流式转发（chunk 完整性、idle 超时、断连清理）、JWT 刷新前置、401 透传。
- **前端**：事件分型渲染（五类事件）、芯片交互、降级模式（无 tool 事件的旧后端兼容）。
- **迁移脚本**：SQLite→MySQL 行数对账、id 映射、user_id 换算、时间戳语义。
- **回归**：阅读器批注弹层「AI 伴读区」（段落级角色批注）零影响；OPDS/Kobo 链路零影响。
- **AC 验收**（覆盖 happy path + 边界 + 异常）：
  1. 提问 → 查词工具触发 → 芯片展示 → 答案流式输出（happy path）；
  2. 工具 error → 模型自愈换工具/向用户说明；
  3. SSE 中途断网 → 前端提示 + 重试不丢会话；
  4. 迁移后旧会话可在新 UI 读到、继续对话；
  5. 降级模式（moon-well agent 开关关）→ 行为等价现状对话框。

## 8. 开发切分（与 moon-well P0–P4 对齐）

| 阶段 | magicbook 侧内容 | 依赖 |
| --- | --- | --- |
| P0 | SSE 薄代理变体 + 端到端打通验证（Traefik/容器链路） | moon-well P0 |
| P1 | drawer 事件分型渲染 + 芯片交互 + bookContext 上行 | moon-well P1 |
| P2 | 记忆面板（查/改本人记忆，走代理） | moon-well P2 |
| P3 | 学情摘要展示（会话列表入口） | moon-well P3 |
| P4 | 数据迁移脚本 + `cps/ai` 退役 + 旧端点下线 | moon-well 表就绪 |

## 9. 开放问题（与 moon-well 侧 §12 联动）

1. user_id 映射核实（§6.3，迁移前置条件）。
2. Traefik SSE 缓冲预演提前到 P0（两文档已对齐该建议）。
3. drawer 芯片视觉稿是否先出设计稿（当前描述为交互语义，视觉实现开发期定）。

## 10. 实施记录（R98，2026-09-29 开发完成，与上文偏差以本节为准）

**薄代理落地**（`cps/ai/proxy.py`，blueprint `aiagent`，main.py 与 `aichat` 同序注册）：
- JSON 端点复用 `cps.web._moonwell_proxy`（身份头 + Bearer + 401 自动刷新），形制适配为
  GET（conversations/history/memory/book-profile，`?bookId=`/`?conversationId=`）→ moon-well
  POST body；写端点（memory/save、memory/delete、conversation/rename、conversation/delete）
  POST body 原样透传。moon-well Result 包装（`{success, result}`）不解包，前端统一处理。
- SSE `/ai/agent/chat`：`requests stream=True` 逐 chunk yield（不缓冲）；连接建立阶段 401
  可安全重试（刷新前置），流开始后不再重试；上游 ≥400 的 JSON 错误原样透传；客户端断开
  finally 关上游连接；响应头 `X-Accel-Buffering: no`，read timeout 300s 对齐 agent 预算。

**会话「新建」语义变化**：不再有本地建会话端点——前端「＋」只清空本地 conversationId，
moon-well 服务端在首问时创建会话，`final` SSE 事件回传 `conversationId`/`messageId`。

**moon-well 侧随附新增**（R98 追补）：`/ai/agent/conversation/rename`、
`/ai/agent/conversation/delete`（承接既有 drawer 的改名/删除交互）。

**cps/ai 退役（本轮）**：写路径（chat/conversations POST/rename/history DELETE/
memory clear/test_provider/admin 管理页）全部 410 停写，SQLite 不再产生新数据；
读路径（conversations/history/memory GET）保留到迁移验证完成。provider/registry/
crypto/memory 等模块文件保留（迁移窗口内 routes.py 不再 import 大部分），随最终
退役一并删除。ai_admin.html 模板成为死文件（无路由渲染），最终退役时删除。

**迁移脚本**（`scripts/migrate_ai_companion_to_moonwell.py`）：
- 全量迁 ai_conversation/ai_message/ai_user_memory；ai_config/ai_provider 快照归档
  JSON（D8 退役）；id 原样保留 + AUTO_INCREMENT 拨到 max(id)+1；
- 列映射：`content`→`memory`、`source_book_id`→`book_id`（NULL→0 跨书通用）、
  `page_context` 无目标列→以 `{"legacy_page_context": ...}` 存入 `tool_trace`（新 UI 不渲染）；
- user_id 映射：`--user-map` JSON 或 `--identity-mapping`（须先实测核实，设计 §6.3）；
  支持 `--dry-run` 只读对账；结束打印逐表行数对账。
- **迁移窗口与回退**（§6.2 落地）：切换点即旧写端点 410（已生效）——生产部署本版本后
  SQLite 立即冻结，迁移脚本是唯一把存量搬走的通道；旧库文件级备份后天然可回退。

**前端**（ai_chat.js/css、ai_chat_panel.html）：SSE 解析升级为 `event:`+`data:` 分型帧
（无 event 行的裸文本按 delta 兼容，降级模式）；工具芯片折叠渲染（写工具 ✍ 标记 +
requireConfirm 高亮）；final 显示 token 用量角标；记忆面板（🧠 按钮：学情摘要 +
记忆查/改/删 + 手动添加）。

**测试**：全量 214 passed（基线 229：删除 26 个旧 chat/admin 行为测试，新增薄代理 8、
迁移脚本 5、退役语义改写 13、过渡 E2E 4）。
