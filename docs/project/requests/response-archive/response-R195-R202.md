> 归档：R195–R202（博客导入链与 TED 导入链缺陷盘点 + 修复）原样搬移自 `response.md`。
> 2026-10-23 R216 写入触发轮转搬移，只搬移原文、不总结、不改写。

## 2026-10-21（R195–R202：博客导入链与 TED 导入链缺陷盘点 + 修复）

### R195–R202（用户：检查博客导入和 TED 导入还有哪些不足 → 拆分记录进 PingCode，然后开始修复）

- **盘点口径**：不按代码逐行找 bug，而是按每条链路的**事实源语义**倒推失效面——博客链的事实源是「Halo 当前发布版，webhook 只是触发器」，TED 链的事实源是「moon-well 按 title+author 索引的段落注册表与原声」。凡「源已改、书没跟上」或「源能查到、调用方查不到」的路径都算缺陷，共出 8 条：4 条数据正确性（P0/P1）、1 条体验缺口（P2）、3 条仅记录待排期。
- **PingCode 登记**：8 条拆成 8 个独立条目（非一个总条目），产品 MAGICBOOK、按模块分 suite——library：MAGICBOOK-206（state 竞态）/207（事件白名单）/208（resync）/209（封面顺序）/210（EPUB 体验缺口，Pending）；reading：MAGICBOOK-211（bookId 语义错位，关键）/212（去重不补缓存 + busy_timeout）/213（TED 无封面/进度/倍速，Pending）。206–209、211、212 置 In progress，验收前不流转 Completed。
- **R195 连接器 state 竞态**：`_load_state/_save_state` 整份读-改-写只有 per-slug 锁，`gunicorn --threads 4` 下两本书同时发布互相覆盖 `last_sha` → 下次发布旧 sha 被当新版本 → 重建 EPUB → 整本翻译 fingerprint 变 → 白烧积分。新增模块级 `_state_lock`，读改写收敛为 `_state_entry` / `_state_update`（`remove=(...)` 顺带替掉手写 pop）。
- **R196 事件白名单**：原硬编码只认 `NEW_POST`，修订后重新发布不进书。改 `_allowed_events()`，`CONNECTOR_EVENTS` 可覆盖（缺省 `NEW_POST,UPDATE_POST`），DELETE 类不隐式放宽。
- **R197 新增 `POST /resync`**：webhook 无补投，停机期丢的事件只能去 Halo 手动重发布。沿用 `X-Hook-Token`，body 可带 `{"slugs":[...]}`（缺省全量），逐条 `_process_slug`（sha 未变 no-op ⇒ 幂等），单条失败不中断，末尾汇总 `{total, imported, failed, results}`；未映射 slug 记 `no-mapping`。
- **R198 封面先于 EPUB 落盘**：`_do_import` 原顺序「save_cover → 写 EPUB」，EPUB 校验失败时出现「新封面 + 旧正文」。改为「临时文件 → 校验 → `os.replace` → 换封面」，封面失败降级为 `coverError` 字段（正常路径契约不变）。
- **R200 TED 原声伴听（关键）**：前端传 `calibre.bookId`，moon-well `/book/ted-audio` 用它查**自家 book 表**——两套自增序列只有巧合对齐才命中，错位即 `result=null`、前端静默回落 TTS 机器音（与 R172/R173 事故同症状）。`cps/web.py` 的 `_ted_audio_book_id` → `_ted_book_identity`（返回 title/author/error），两个代理改发 `{"bookName","author"}`；非数字书号 → 400（不再让脏串进上游 `Long.valueOf`）、本地无此书 → 404（不把空书名送去上游当「未缓存」）。跨仓同源 moon-well R197。
- **测试**：`tools/connector/tests` 21 passed（含 5 线程并发放大窗口用例；反向变异实测无锁时 5 个 slug 只剩 1 条，确认用例有效）；`test_book_import.py` 17 passed；`test_ted_audio_proxy.py` 17 passed（含 404 与「源码不得再出现 `"bookId": book_id`」负向锁）；reading 域回归 91 passed。开发态只跑本次改动相关用例，未跑全量。
- **边界（如实）**：① 全部改动未经真机验收——`/resync` 与 `CONNECTOR_EVENTS` 需在 fnOS 连接器容器实跑一次，Halo 2.26.1 的修订事件实际枚举仍待抓一次 webhook 日志核实；② TED 原声链路未在真实 TED 书上验证「按名查命中并返回 audioUrl」，仅由单测与源码锁保证；③ 未修项见 R199/R202（H2 不进 TOC、srcset 漏下载、TED 无封面、未缓存态与无原声不可区分、无进度/倍速）。
- **台账**：magicbook 分支 `fix/r195-import-gaps`、worktree `../magicbook-import-gaps`，合入本地 develop **`2ffce335`**；moon-well 分支 `fix/r197-ted-audio-chain`、worktree `../moon-well-ted-audio-fix`，合入本地 develop **`0ff7c93`**（跨仓 R197/R198，测试 22 passed）。**两仓 worktree 原样驻留待验收；push 已按用户指令执行（见本节「上线」条）**；验收通过后再删 worktree 并流转 PingCode 状态。
- **文档**：magicbook `docs/product/reading/interface.md` 新增 §1.2 两个代理契约（入参口径、错误码、禁 `bookFormat` 判据）；moon-well `docs/product/book/interface.md` §4 与调用方契约补 `bookId | bookName+author` 二选一；两仓各建 `docs/project/iterations/2026-10-import-audit/{blog-import,ted-audio}/lld.md`（含状态行）。
- **上线（用户指令「push 然后我来验证」）**：全量闸门先在合并后基线重跑——`pytest -q` **647 passed / 0 failed**，连接器 `tools/connector/tests` **21 passed**。跨仓顺序按兼容性排：**先推 moon-well**（新入参 `bookName+author` 需后端先就位，否则 magicbook 新代理打旧后端会 400），等约 2 分钟构建部署窗口后**再推 magicbook**。moon-well push `961f98c..8a64094`、magicbook push `68cb9a06..8a09af81`。推送后实测 `moon-well.haoshenqi.top/actuator/health` **200**、`magicbook.haoyuhang.top/login` **200**（`/` 仍 302 跳登录，符合预期）。
- **证据边界**：本次只有外部可达性证据，**未核对 fnOS 构建日志的 START/END 行**（沙箱内无 fnOS 访问通道）；「线上是否真跑上新代码」由用户在浏览器侧验证，判据见下条。
- **验证路径**：① 打开一本 TED 书点「整本播放」——应播真人原声且随段落高亮，不再回落机器音（若仍是机器音，先看 `/ajax/ted-audio` 返回体里 `result` 是否 null）；② 手动补账 `curl -X POST http://<connector>:9878/resync -H "X-Hook-Token: $TOKEN"`，返回 `unchanged` 说明 sha 对账正常；③ 发布一篇已发文章的修订版，确认触发重导（`UPDATE_POST` 是否真被 Halo 2.26.1 发出，需看连接器日志的 eventType）。
- **总结**：requests.md 占号 R195–R202（8 条）；moon-well 同源 R197/R198。R199/R202 是「已登记未修」的体验缺口，不在本轮范围。
