# 书籍投稿（book-submission）· L3 实现说明（R279）

> 状态：**开发完成，待验收**（2026-11-04）
> 代码：`cps/library_submission/`、`cps/routes/library_submission.py`、`cps/templates/admin_submissions.html`、`cps/templates/me.html`（投稿面板）、`cps/static/js/admin_submissions.js`、`cps/static/js/me_submission.js`

## 为什么单独做一条链路

书库（calibre `metadata.db`）是全站共享的，`books` 表**没有归属字段**；上游 `/upload` 只要用户带 `ROLE_UPLOAD` 位就能直写书库，`upload_book_formats` 甚至不校验书目归属（可覆盖任意书目的格式文件）。因此「让普通用户上传」不能复用该链路，本功能把写权限收回管理员：

```
普通用户 → POST /ajax/library/submit → MinIO 私有暂存区 + book_submission(PENDING)
管理员 → /admin/submissions 预览/通过 → 后台线程解析 → 写 calibre 书库 → INGESTED
                                    → 驳回 → 删对象 → REJECTED
```

**投稿全程不碰书库**，只有管理员的「通过」动作会调用入库函数。

## 数据与存储

- 表 `book_submission`（app.db / `ub.Base`，懒建）：`user_id`、`object_key`、`original_filename`、`size`、`sha256`、`status`、`reviewer_id`、`reviewed_at`、`note`、`book_id`、`error_message`、`created_at`、`updated_at`。
- 状态机：`PENDING → APPROVED → INGESTED`；`PENDING → REJECTED`；`APPROVED → FAILED`（可重试回 `APPROVED`）。
- MinIO：bucket 沿用 `magicbook`，前缀 `book-submissions/<user_id>/<uuid>.<ext>`。**绝不可加进匿名只读 Statement**（现只放开 `buddy/`、`ted-audio/`）；预览走同源代理，不生成预签名直链。

## 入口与权限

| 端点 | 权限 | 说明 |
| --- | --- | --- |
| `POST /ajax/library/submit` | 登录即可（**不查 `role_upload`**） | multipart `file` + `declaration=1`；扩展名白名单（音视频除外）、MIME 校验、sha256 去重、单用户待审上限、5/hour 限流 |
| `GET /ajax/library/submissions/mine` | 登录即可 | 我的投稿状态 |
| `GET /admin/submissions` | `@admin_required` | 审核页 |
| `GET /ajax/admin/submissions` | `@admin_required` | 列表 |
| `GET /ajax/admin/submissions/<id>/preview` | `@admin_required` | 同源代理下载暂存对象 |
| `POST /ajax/admin/submissions/<id>/review` | `@admin_required` | `{"approve": bool, "note": str}` |

## 入库

`cps/library_submission/ingest.py` 内的 `ingest_book_from_meta` 是**不依赖请求上下文**的精简入库实现（现有 `create_book_on_upload` 依赖 `flash()`/`current_user`，线程里调会崩）。流程：建 Books/作者/系列/标签/出版社/语言/简介/格式行 → 生成 `书库/<author>/<title>/` 并搬入文件 → 封面 copy 为 `cover.jpg` → `set_metadata_dirty` + commit。失败全量记录到 `book_submission.error_message` 并置 `FAILED`，可重审。

后台线程用 `app.app_context()` + `db.CalibreDB(app)`（scoped_session 线程隔离，R249 教训），不共享请求线程的会话。

## 配额与安全

- `SUBMISSION_MAX_MB`（默认 100）、`SUBMISSION_MAX_PENDING`（默认 10，按条数）。
- 上传 5/hour 限流（`flask_limiter`，按远端地址）。
- 对象键由服务端 uuid 生成，不含用户输入；原始文件名只用于展示与还原扩展名。
- 提交页必须勾选「我有权分享此文件」——通过即发布，版权责任由投稿人先自认。

## 边界与未做

- 入库后书仍进共享书库、无 owner 字段；「只对投稿者可见」不在本功能内。
- 未做站内信通知（通过/驳回只改状态，用户回 `/me` 可查）。
- 未做对象生命周期定时清理（仅驳回/入库时删除；孤儿扫描待后续）。
