# response 归档：R157（2026-10-11）

> 从 response.md 原样搬移（2026-10-13 R166 分支 merge origin/develop 后窗口达 11 节：
> 并行会话的「R164 续二」收尾节与本轮 R166 节并存）。只搬移原文，未总结、未改写、未改编号。

## 2026-10-11（R157：整本连播（听书）——顺序逐段朗读整本书，随时暂停）

### R157（R155/R156 评估结论落地：moon-well 零改动，播放队列全部在阅读器前端）

- **需求**：为书籍增加一个整本阅读功能：按照顺序一段一段持续朗读，随时可以暂停。（编号说明：R155 评估轮占号 155 及其回应条目曾被并行提交操作清除；155/156 已被并行会话的 worktree 规范/词汇细筛占用，按「不改既存、续编空号」纪律落为 157。评估结论在 moon-well response.md R156 有留档。）
- **交付**（worktree `../magicbook-whole-book-read`，分支 `feat/r157-whole-book-read`，基于 origin/develop 41918028）：
  - **moon-well 与 web.py 零改动**（评估已证：/tts/speak 同步音频 + SHA-256(原文) 永久缓存 + 顺序串行天然合规）；
  - `epub.js` 新增独立播放队列状态机 `bookPlayer`（与单段朗读 `activeTts` 互斥让位）：collectParagraphElements 收集本章段落 → 归一化 + 2000 字符切块（句读优先断句，长段不再静默截断）→ 逐块 `POST /ajax/reading-tts` → Audio(blob) 播放 → ended 接下一块；本章耗尽 `rendition.next()` 等 `rendered` 重建队列，spine 尽头自动停并提示「已到全书末尾」；
  - 暂停/继续：`audio.pause()/play()` 段内保留进度；合成期间暂停 = 就位 blob 不开播，点击即续；
  - 预取：当前块 onplay 后预取下一块，全程 ≤1 个在途合成（NAS 本地 TTS CPU 瓶颈、MiMo 100 RPM）；
  - 视图跟随：当前段不在可见页才 `display(段落实时 CFI)` 跳页（实时 CFI 无旧 CFI 越界毒化显示队列风险）；
  - 章界：空文字章节（纯图片封面页）自动跳过（≤10 章上限）；20s 未渲染按翻章失败收尾；
  - 手动导航跟随：rendered 非 internalNav → 重建队列——同章重渲染（字号/主题/分栏）按 lastStartedText 续听原块、换章从新页顶部起播；章内翻页不打断播放；
  - UI：标题栏 `#tts-book`（▶/❚❚ 切换）+ `#tts-book-stop`（■，连播中显示）；当前段 `.reading-tts-speaking` 高亮；8 条新文案走 mbT 五步链；
  - 文档：L1 reading.md 朗读条目扩写+整本连播、L3 深入阅读加链；L2 reading hld 新增 §1.1（无新契约）；L3 `docs/feat/whole-book-listening/design/whole-book-listening-design.md` 新建（状态行已上线）。
- **测试**：i18n seed 契约 5 例绿（JS 字面量 ⊆ seed = po = mo，8 条新词条四层一致）；test_reading_tts + test_csp_media + test_nav_settings_dropdown 20 例绿（代理层零改动回归）；node --check 过；epub.js 全模块通读交叉审查一轮（据此修出：空文字章自动跳过、emptySkips 初始化与重置、FireWaiters 唤醒链抽取）。
- **归档**：本条使窗口达 11，最早一节 R143 原样搬至 `response-archive/response-R143.md` 并登记索引，窗口 R144–R157。
- **总结**：requests.md 占号 R157（在 worktree 内落盘，随本分支 merge 入 develop，避开主检出并行覆写区）；本条为回应；冲突记录：R155 评估轮的占号/回应曾被并行提交清除（已在编号说明留痕），本轮在干净基线重落为 157；worktree 交付后驻留等用户真机验收（AC 见 L3 design §4），验收通过后按两段式闸门收尾。
- **验收与收尾（同日回填）**：用户确认验收通过（2026-10-11「此任务完成的非常好，可以收尾」）——按两段式闸门收尾：worktree `../magicbook-whole-book-read` 已 `git worktree remove`、分支 `feat/r157-whole-book-read` 已 `branch -d` 删除（内容已随 e6a51c48 并入 develop 并部署上线，线上冒烟见前文）。
