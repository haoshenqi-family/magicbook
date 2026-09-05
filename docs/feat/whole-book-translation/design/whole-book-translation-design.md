# 一键翻译整本书设计方案

**特性代号**：`whole-book-translation`  
**日期**：2026-09-05  
**状态**：设计已确认，尚未开发

## 1. 背景与目标

当前阅读器支持单段翻译和手动整页翻译：magicbook 负责阅读器交互，moon-well 负责翻译调用和 `reading_paragraph_cache` ES 持久缓存。本功能增加一个“一键翻译整本书”入口，把书籍内容按阅读顺序拆成独立任务，交给 moon-well 任务队列/外部执行器处理；任务完成后将译文写入既有段落 ES 缓存，使阅读器后续只读缓存。

本期目标：

1. 用户可从一本 EPUB 书发起整书翻译。
2. 每个可翻译段落对应一个可追踪任务，任务可重试、断点续作。
3. 已有缓存的段落不重复发布任务。
4. 任务完成后，译文写入 moon-well 的 `reading_paragraph_cache`，与在线段落翻译使用同一 doc id 规则。
5. 用户可以查看批次进度，失败段落可以单独重试。

明确不做：

- 不修改 EPUB 原文件，不生成新的译文 EPUB。
- 不在 magicbook 内直接调用 LLM Provider。
- 不把整本书一次性拼成一个超长请求。
- 本期先支持 EPUB/Kepub；PDF、TXT、漫画不纳入整书段落抽取。

## 2. 推荐架构

```text
用户点击“一键翻译整本书”
        │
        ▼
magicbook
  读取书籍 EPUB（按 OPF spine 顺序）
  提取/规范化段落
  创建 translation_job + translation_job_item
  查询已有缓存，未命中段落逐条发布任务
        │  POST /llm/task/publish（taskType=TEXT）
        ▼
moon-well
  system_llm_task_record：PENDING → ACCEPTED → COMPLETED/FAILED
        │
        │ 外部执行器 accept / complete
        ▼
magicbook 回调接收完成结果
  校验 task/job/item 关联
  写入 moon-well reading_paragraph_cache
  更新 item 与 job 统计
        │
        ▼
阅读器按段落读取缓存，直接显示译文
```

推荐采用“完成回调”而不是 magicbook 定时轮询每个任务：一整本书可能包含数千段，轮询会放大请求量，也依赖用户在线。发布任务时携带 `jobId`、`itemId`、`bookId`、`chapter`、`paragraphIndex` 等关联信息；执行方完成任务后由任务平台调用 magicbook 的内部完成回调。

## 3. 数据模型

### 3.1 `translation_job`

使用 magicbook 当前 SQLite/SQLAlchemy 数据库，记录一次用户操作批次。

| 字段 | 说明 |
|---|---|
| `id` | UUID 字符串，批次 ID |
| `user_id` | 发起用户 |
| `book_id` | Calibre 书籍 ID |
| `book_format` | EPUB 或 KEPUB |
| `book_fingerprint` | 书籍文件 hash/更新时间，用于防止旧版本结果写入新书 |
| `status` | `PENDING` / `RUNNING` / `COMPLETED` / `PARTIAL_FAILED` / `FAILED` / `CANCELED` |
| `total_count` | 总段落数 |
| `cached_count` | 发起时已命中缓存数 |
| `published_count` | 成功发布的任务数 |
| `completed_count` | 成功完成数 |
| `failed_count` | 失败数 |
| `created_at` / `updated_at` | 时间 |

同一用户、同一本书、同一 `book_fingerprint` 存在未完成批次时，默认返回已有批次，避免重复发布；用户明确“重新翻译”时才创建新批次。

### 3.2 `translation_job_item`

每个实际段落一条明细，任务与缓存之间通过原文 hash 关联。

| 字段 | 说明 |
|---|---|
| `id` | UUID 字符串 |
| `job_id` | 批次 ID |
| `paragraph_index` | 全书稳定顺序，从 0 开始 |
| `chapter` | 章节标题 |
| `text` | trim 后的原文，最长 2000 字符 |
| `text_hash` | 与 moon-well `SHA-256(trim(text))` 一致 |
| `task_id` | moon-well 任务 ID |
| `status` | `CACHED` / `PUBLISHED` / `ACCEPTED` / `COMPLETED` / `FAILED` / `SKIPPED` |
| `translation` | 回调收到的译文，可选本地冗余 |
| `error_message` | 最后一次失败信息 |
| `attempt_count` | 发布/重试次数 |
| `created_at` / `updated_at` | 时间 |

在同一本书中重复出现的相同段落只发布一次任务，多个 `translation_job_item` 共享同一个 `text_hash`；完成后批量将这些明细标记为 `COMPLETED`。跨书复用由 moon-well ES 的既有段落 hash 缓存负责。

## 4. 段落抽取规则

1. 通过 Calibre DB 校验当前用户有权访问书籍，并取得 EPUB 文件路径。
2. 读取 `META-INF/container.xml` 找到 OPF。
3. 按 OPF `spine` 顺序读取 XHTML/HTML；不按 ZIP 文件名顺序处理。
4. 提取块级文本节点：`p`、`li`、`blockquote`、`h1`-`h6`、`pre`；跳过 `script`、`style`、导航目录和隐藏节点。
5. 将连续空白归一化，去掉空段落；保留章节标题作为 `chapter` 元数据，不单独发布标题任务。
6. 超过 2000 字符的段落按句号、问号、感叹号、分号等边界切分；没有自然边界时按不超过 2000 字符硬切。每个切片独立任务，避免超过现有 moon-well 入参限制。
7. 记录 `paragraph_index`、`chapter`、`text_hash`，保证结果可以稳定回写而不依赖前端 DOM。

## 5. 缓存与任务流程

### 5.1 发起批次

`POST /ajax/reading-translate-book` 请求只携带 `book_id`、`book_format` 和可选 `force`。

magicbook 服务端完成：

1. 创建或复用批次。
2. 抽取并持久化段落明细。
3. 对每个 `text_hash` 查询 moon-well 段落缓存；命中非空 `translation` 的明细标记为 `CACHED`。
4. 对未命中且未发布的唯一段落调用 moon-well `/llm/task/publish`：

```json
{
  "taskType": "TEXT",
  "caller": "magicbook-whole-book-translation",
  "input": "英文段落",
  "parameters": {
    "jobId": "...",
    "itemId": "...",
    "bookId": 123,
    "bookFingerprint": "...",
    "paragraphIndex": 42,
    "textHash": "...",
    "bookName": "...",
    "chapter": "..."
  }
}
```

5. 发布成功后保存 `task_id`，发布失败只影响该 item，不回滚已经成功发布的任务。

### 5.2 领取与完成

外部执行器使用 moon-well 的 `/llm/task/accept` 和 `/llm/task/complete`。执行器输入为 `input`，输出必须是单段中文译文；TTS 不参与本批次。

moon-well 完成任务后调用 magicbook 内部回调，例如：

`POST /internal/reading-translation/task-completed`

回调体至少包括：`taskId`、`jobId`、`itemId`、`textHash`、`bookFingerprint`、`success`、`output`、`errorMessage`。magicbook 校验内部签名/服务凭证、任务归属和书籍 fingerprint 后：

1. `success=false`：item 标记失败，保留错误信息，可重试。
2. `success=true`：调用 moon-well 段落缓存写入接口，使用原文、译文、书名、章节和 `textHash`。
3. 缓存写入成功后 item 标记 `COMPLETED`；同 hash 的其他 item 一并完成。
4. 原子更新 job 统计；全部完成则 `COMPLETED`，有失败则 `PARTIAL_FAILED`。

缓存写入必须幂等：相同 `text_hash` 重复回调只保留同一译文，不得新增重复 ES 文档。`bookFingerprint` 不参与 ES doc id，但必须参与批次关联校验，防止旧书任务污染新文件的批次状态。

## 6. 接口设计

### magicbook 用户接口

| 接口 | 说明 |
|---|---|
| `POST /ajax/reading-translate-book` | 创建/复用整书翻译批次 |
| `POST /ajax/reading-translate-book/status` | 查询批次进度和失败数 |
| `POST /ajax/reading-translate-book/retry` | 重试指定失败 item 或全部失败 item |
| `POST /ajax/reading-translate-book/cancel` | 取消尚未发布/尚未完成的任务 |

### magicbook 内部接口

| 接口 | 说明 |
|---|---|
| `POST /internal/reading-translation/task-completed` | 接收 moon-well/执行器完成回调，需服务间认证 |

### moon-well 需要补充的服务接口

当前 LLM 任务接口已经支持发布、领取、完成，但还没有跨服务完成通知和由 magicbook 调用的缓存写入契约。建议补充：

- 任务发布参数持久化 callback 元数据；
- 完成后可靠投递 webhook，失败重试并记录投递状态；
- `POST /reading/paragraph-cache/save-translation`：按原文写入 `reading_paragraph_cache`，内部服务认证，幂等更新。

如果不希望 moon-well 增加 webhook，也可以由 magicbook 使用服务账号定时查询任务详情，但不推荐作为默认方案。

## 7. 前端交互

在书籍详情页或阅读器工具栏增加“一键翻译整本书”按钮：

- 首次点击显示段落总数、已缓存数和预计待翻译数，用户确认后开始。
- 提交后立即返回批次 ID，不阻塞 HTTP 请求等待整本书完成。
- 显示进度：`已完成 / 总段落`、失败数、当前状态。
- 允许用户继续阅读；已完成段落在翻页时从 ES 缓存显示。
- 失败段落提供“重试失败段落”；批次完成后显示完成提示。
- 取消只阻止尚未发布的任务；已经被领取的任务不能强制中断，完成回调仍按批次校验处理。

## 8. 一致性、并发与安全

- 创建批次使用 `(user_id, book_id, book_fingerprint, active_status)` 约束或事务内锁，防止双击产生两个批次。
- 发布采用逐条提交并记录 task id；服务重启后根据 `PUBLISHED` 且无完成状态的 item 继续发布/查询。
- 回调使用 HMAC 或服务间 Bearer token，并校验 `taskId -> itemId -> jobId` 链路，禁止仅凭前端传入的 item id 写缓存。
- 回调必须幂等，重复回调返回成功，不重复增加 job 计数。
- 原文和译文属于用户阅读数据，日志仅记录 hash、任务 ID 和长度，不记录全文。
- 对单次批次设置上限和速率限制，建议首期最多 20,000 个段落；超限提示用户分批处理。

## 9. 异常与恢复

| 场景 | 处理 |
|---|---|
| EPUB 无法解析 | 批次失败，返回明确错误，不创建任务 |
| 段落超过限制 | 按规则切片；无法切片时硬切 |
| moon-well 发布失败 | item 失败并可重试，已发布任务不回滚 |
| 执行器失败 | moon-well 任务 FAILED，回调更新 item 失败 |
| 回调重复 | 幂等返回，不重复写缓存/计数 |
| 回调暂时不可达 | moon-well webhook 重试；magicbook 后台补偿任务兜底 |
| ES 写入失败 | item 保持待回写/失败状态，重试写缓存，不丢失任务输出 |
| 书籍文件被替换 | fingerprint 不匹配，拒绝回写旧批次 |

## 10. 测试计划

### magicbook

- EPUB OPF/spine 顺序解析、HTML 块级节点提取、隐藏节点过滤。
- 空白归一化、重复段去重、超过 2000 字符切片。
- 已有缓存跳过发布，发布失败局部记录，批次重复创建幂等。
- 完成回调签名、任务链路校验、重复回调、fingerprint 不匹配。
- 完成/失败/取消/重试状态统计。
- 用户无权访问书籍、非 EPUB 格式、段落数超限。

### moon-well

- 任务参数保留 job/item/hash 元数据。
- webhook 成功、失败重试、重复投递幂等。
- 缓存写入与现有在线段落翻译共用 doc id，不覆盖音频和批注字段。

## 11. 已确认的设计决策

| 决策项 | 结论 |
|---|---|
| 完成通知与缓存回写 | 接受 moon-well 增加完成 webhook，并提供内部段落缓存写入契约 |
| 首期文件格式 | 只支持 EPUB/Kepub，不支持 TXT |
| 超长段落 | 按句子边界切片；没有自然边界时按 2000 字符硬切 |
| 入口位置 | 书籍详情页和阅读器工具栏都提供“一键翻译整本书” |
| 版本策略 | 同一用户、同一本书、同一 `book_fingerprint` 只允许一个活动批次；固定英译中、单一版本 |

以上决策作为后续开发基线。本次仍仅完成设计确认，未修改功能代码。
