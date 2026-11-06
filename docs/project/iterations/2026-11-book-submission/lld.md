# R279 书籍投稿（暂存 + 审核 + 入库）· LLD

> 状态：**开发完成，待验收**（2026-11-04）
> 来源：本会话评估「开放用户上传」影响后，operator 明确要求「给普通用户一个新的上传图书接口，仅上传到 MinIO，管理者审核后可以解析入库」，并「确认，开工」。

## 1. 问题与约束

- calibre 书库全局共享、`books` 无 owner；`/upload` 的 `ROLE_UPLOAD` 可直写书库并覆盖任意书目文件（`cps/editbooks.py:104-107,1421+`）。
- 因此新链路必须**物理隔离**：用户写入只进 MinIO 暂存区，书库写入只发生在管理员审核通过后的后台线程。
- 不修改上游 `/upload` 行为（NFR-1 最小侵入、R78/R92 `metadata.db` 边界）。

## 2. 组件

| 文件 | 职责 |
| --- | --- |
| `cps/library_submission/models.py` | `book_submission` 表（`ub.Base`）与状态常量 |
| `cps/library_submission/storage.py` | MinIO 单例客户端、暂存前缀、配额常量、对象键生成 |
| `cps/library_submission/ingest.py` | 无请求上下文的解析与入库（`extract_meta` / `ingest_book_from_meta`） |
| `cps/library_submission/service.py` | 提交、列表、审核状态机、后台入库线程、预览流 |
| `cps/routes/library_submission.py` | 6 个 HTTP 端点（用户 2 + 管理 4） |
| `cps/templates/me.html` + `cps/static/js/me_submission.js` | 用户投稿面板 |
| `cps/templates/admin_submissions.html` + `cps/static/js/admin_submissions.js` | 审核页 |
| `cps/ui_ia.py` | 管理导航新增 `admin-submissions`；`/admin/submissions` 归管理域 |

## 3. 数据模型

```
book_submission(
  id PK, user_id idx, object_key UNIQUE, original_filename, size,
  sha256 idx, status idx, reviewer_id, reviewed_at, note,
  book_id idx, error_message, created_at, updated_at)
```

状态迁移：

```
PENDING --approve--> APPROVED --worker ok--> INGESTED
PENDING --reject---> REJECTED
APPROVED --worker fail--> FAILED --approve(retry)--> APPROVED
```

所有迁移仅在当前状态匹配时生效，重复点击幂等 no-op。

## 4. 提交校验

1. 扩展名必须在 `config_upload_formats` 白名单内且非音视频（`ingest.allowed_submission_extensions`）。
2. `declaration` 必须为真。
3. 流式算 sha256 与大小（不先落盘）；> `SUBMISSION_MAX_MB` 拒（413）。
4. `file_helper.validate_mime_type` 做 libmagic 校验（与 `/upload` 同一面）。
5. 同一用户同一 sha256 且未 FAILED → 复用原记录，不再写对象。
6. 单用户 `PENDING + APPROVED` 计数 ≥ `SUBMISSION_MAX_PENDING` 拒（429）。
7. 写入 `book-submissions/<uid>/<uuid>.<ext>`，插 PENDING 行。

## 5. 入库细节

`ingest_book_from_meta`：
- 作者/标签/系列/出版社/语言：直接 add-or-get（不做 `/upload` 的改名联动——新书目没有旧路径要搬）。
- 简介：`Markup(...).unescape()` 后 `clean_string`（与 `/upload` 同口径）。
- 目录：`get_valid_filename(作者)/get_valid_filename(标题)`；若目录已存在加 ` (book_id)` 后缀避免同名互覆盖；文件名 `get_valid_filename("标题 - 作者", 90) + .ext`。
- 封面：`cover.jpg`。
- `set_metadata_dirty` 后 commit。

后台线程（`_ingest_worker`）：
- **`app.test_request_context('/')`**（不是纯 app context）：uploader→epub 链路里的 `gettext` 会走 `flask_babel.get_locale()` → `request.accept_languages`（`cps/cw_babel.py:22`），纯 app context 会抛 `Working outside of request context`。
- 入库前必须 `calibre_db.create_functions(config)`：calibre 的 INSERT 触发器依赖 `title_sort`/`uuid4` 等 UDF，线程作用域的新连接要重新注册。
- 作者/标签/系列/出版社/语言一律 `session.add(...)` 后 flush，**不要用 `session.merge`**：merge 返回托管副本，原对象再 append 会撞 `authors.name` UNIQUE。
- MinIO 流 → `书库/.submissions-tmp/sub-<id>.<ext>` → 解析 → 入库。
- 成功：`INGESTED` + `book_id`，删对象；失败：`FAILED` + `error_message`，保留对象供重试。
- 线程不读取请求上下文（`_flask_app()` 捕获 app 实例传入）。

## 6. 安全

- 暂存前缀不进匿名只读 Statement；`storage.py` 无 `presigned`。
- 对象键服务端生成，拒绝用户输入拼路径。
- 预览 `attachment; filename*=UTF-8''...`（RFC 5987），`Cache-Control: no-store`。
- 审核端点全部 `@admin_required`；提交端点登录即可，显式不查 `role_upload`。

## 7. 测试

`tests/test_r279_book_submission.py`（17 例）：普通用户可提交且不查上传位、声明必填、扩展名/音视频拒绝、匿名拒绝、重复 sha 复用、普通用户不能列/审、管理页权限、通过→INGESTED+清对象、驳回→REJECTED+清对象、驳回后不可再审、前缀不进公开源、无预签名、对象键无用户输入、导航项/路径域归属。
契约演进：`tests/test_account_admin_ia_r251.py` 管理页数 14→15。

## 8. 后续（不在本次）

- 站内信通知通过/驳回。
- MinIO 对象定期清理与孤儿扫描（DB 无记录 / 超期未审）。
- 入库后「仅投稿者可见」需要 owner 模型，属独立改造。
- 入库异步化进一步并入「全局上传解析移出事件循环」的架构改造。
