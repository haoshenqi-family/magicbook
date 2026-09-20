## 2026-09-18

### R50（整本翻译接口逻辑检查，只读分析，未改代码）

- **接口链路**（`web.py:361` → `cps/reading_translation/service.py`）：POST + `user_login_required` + `admin_required`（非登录 302/401、非管理员 403）；JSON 取 `book_id`（必填）、`book_format`（默认 epub，仅 epub/kepub）、`force`。`start()` 同步段完成校验/指纹/幂等复用/建批次落库，随后拉 daemon 线程后台发布（缓存回收 + 逐段 publish moon-well `/llm/task/publish`），HTTP 立即返回进度。
- **前端两个触发入口**：① 阅读器工具栏「整本译」（`read.html:64` 按钮、`read.html:174-178` 注入 `wholeBookTranslationUrl`，均仅 `role_admin()`；`epub.js:1099` 绑定 → `epub.js:290` 发请求）；② 书籍详情页按钮（`detail.html:82` + 内联 handler `detail.html:381`）。
- **关键静默点**：`epub.js:291` `if (!calibre.wholeBookTranslationUrl || !window.confirm(...)) return;`——URL 变量缺失或 confirm 取消时点击零反应、零报错、零请求。`wholeBookTranslationUrl` 只在管理员渲染的 `read.html` 中注入。
- **缓存隐患**：`read.html:524` 加载 `js/reading/epub.js` 无版本号 cache-busting，前端拆分后浏览器可能新旧 JS/HTML 配对错配。
- 结论：本地 develop 代码链路自洽；「后端完全没收到请求」与浏览器侧从未发出（上述静默点/缓存/非管理员）最吻合，属后续 debug 方向，本次未执行。

### 总结

- **requests.md**：追加 R50。
- **response.md**：记录接口逻辑检查结论。
- **冲突记录**：无。

---
