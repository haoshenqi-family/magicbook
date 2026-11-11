## R279 · 普通用户投稿书籍：暂存 MinIO，管理员审核后入库（2026-11-04）

**对 R279 的回应**：需求是「给普通用户一个新的上传图书接口，仅上传到 MinIO，管理者审核后可以解析入库」，operator 已确认开工。

- **没有复用 `/upload`**：那条链路的权限位 `ROLE_UPLOAD` 会直写共享书库，`upload_book_formats` 甚至能覆盖任意书目的格式文件。新链路把写权限收回管理员：用户提交只进 MinIO 私有暂存区并落一条 PENDING 台账，**入库只发生在管理员点「通过」之后**。
- **暂存前缀 `book-submissions/<user_id>/<uuid>.<ext>`**：不进匿名只读 Statement（现在只放开 `buddy/`、`ted-audio/`）。预览走同源代理、不生成预签名直链，仓库侧有守卫测试锁死。
- **审核页** `/admin/submissions`（管理 → 内容与 AI → 书籍投稿）：列表、预览、通过、驳回；通过后后台线程 `app.app_context()` + 线程作用域会话解析入库，状态写 `INGESTED` 并回填 `book_id`；驳回删对象留备注。失败置 `FAILED` 可重审。
- **用户侧**：`/me` 新增「建议一本书」面板，提交前必须勾选「我有权分享此文件」；文件先入私有暂存区，审核通过前不出现在书库。支持 epub/pdf/txt/mobi/azw3/fb2/docx 等，单文件上限 100MB。
- **未做**：站内信通知、对象定期清理/孤儿扫描、「只对投稿者可见」的 owner 模型——均记入 LLD §8，需另立需求。
- **验证**：`tests/test_r279_book_submission.py` 20 例（提交/声明/白名单/音视频拒绝/匿名/去重/权限/通过入库/驳回/状态机/安全守卫/导航归属 + 3 条 E2E 回归守卫）全绿；**真实上传测试**用一本真实 EPUB 走完「提交→暂存→审核→入库」：`book_id=1`、暂存对象已删、`calibredb list` 可见「E2E 投稿测试书 / 测试作者 / EPUB」；这次 E2E 抓出并修掉三个单测桩覆盖不到的缺陷（后台线程需 `test_request_context`、入库前需 `create_functions`、add-or-get 不能用 `merge`）。生产 MinIO 凭据本机不可得，E2E 用本地 S3 兼容端点走真实 minio SDK，生产真机验证待合并部署后补。`test_account_admin_ia_r251` 契约演进 14→15 管理页；i18n 种子契约与相关导航/账号回归全绿。**全量 1315 passed / 21 failed（21 项在 origin/develop 基线同样失败，属本机无 calibre 书库的环境性失败，非本次回归）**。画面证据见 `docs/project/iterations/2026-11-book-submission/evidence/`。

**台账总结**：`requests.md` 第 279 条本处回填；`response.md` 写入前窗口与 R280/R281 并行增长，merge develop 后按 10 节窗口把最旧一节 R271（微信小程序）原样搬入 `response-archive/response-R271.md` 并登记索引（R270 由 develop 侧 R280 写入轮转、R269 由 R279/R281 先后轮转，见归档索引）。
