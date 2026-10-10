# requests.md — 对话需求记录

> 仅记录每一次对话用户的需求，除此之外不做任何事情。
> 2026-10-08 起引入归档：已确认完成且过时的条目按编号区间原样搬移至 `requests-archive/`；未完成与有经验教训价值的条目保留于此。编号永不回改、归档不释放编号，新任务按全史最大编号 +1 递增（当前最大 R141）。

## 归档索引

- R01–R129（141 条）→ `requests-archive/requests-R01-R129.md`
- R131–R132（2 条）→ `requests-archive/requests-R131-R132.md`

## 2026-10-08

130. LLM 队列监控面板（管理员可见）：队列总览、失败原因分类查询、任务查询与详情、一键生成恢复预案并重发失败任务。跨项目：对端 moon-well R118，扩展本仓 R126 的 /llm-tasks 面板。先写设计。

> 归档整理注（2026-10-08）：截至整理时无任何 response 回应；与 moon-well R118 同源（LLM 队列监控面板，先写设计），未闭环保留。

133. 排查单词详情 bug：划词查「creation」，详情面板标题显示「created」。magicbook 侧定位代理与前端展示链路（前端标题取 d.lemma，需要查 ES 缓存文档实际 lemma）。

> 归档整理注（2026-10-08）：排查完成（magicbook 侧代理与前端无缺陷），修复在 moon-well 侧且未实施（见 moon-well R123 注记）。

134. 整理 requests.md：已确认完成且过时的条目按编号区间原样归档到 `requests-archive/`（只搬移原文，不改写、不改编号）；未完成的与有经验教训价值的条目保留在 requests.md；编号永不回改、归档不释放编号，新任务继续按全史最大编号 +1 递增。同步修订 AGENTS.md 对话记录条款（原「requests.md 永不归档」废止为「按区间归档」）。（跨四仓同源任务：moon-well R125 / magicbook R134 / app-manager R37 / magiclens R33）

135. 面板显示「待处理任务: 0 · 可重放失败: 8308 · 服务端上限: 4 / 5000」，问管理页面如何做「重放失败」：操作步骤、重放语义（哪些失败可重放、是否重复计费）、单批上限与 8308 条的批次规划、注意事项。

136. 对照家族调研文档 docs/english-graded-reading-path-2026-10-08.md 的六阶书单检查 magicbook 书库：已有书目跳过，缺失的免费公版书从 Project Gutenberg 下载 EPUB 并导入 Calibre 书库（容器自带 calibredb）；最后整理出仍需购买的书单。

137. 做 learning 学习页前端：magicbook 新增学习页（SRS 复习队列卡片——CHOOSE 辨析/RECALL 回忆/SPELL 拼写三种题型 + 答题评分 + 今日计划概览 + 复习统计），配套 moon-well 队列接口补 meaning 释义字段（题干渲染前置依赖）；导航入口接入。（跨仓同源：moon-well R127 补 meaning 字段 / magicbook R137 学习页）

138. 阅读器朗读请求补 bookName/chapter：`/ajax/reading-tts` 目前只发 text，导致 moon-well R128 的缓存分级把书籍段落判成「临时语音」（7 天清理），与 L1「书籍段落永久缓存、重听零等待」不符。

139. 复习队列出现四个空白选项按钮，修复。根因：show() 用 hidden 属性藏元素，被作者样式表覆盖失效（.ln-choices/.ln-spell 的 display:flex、.btn 的 inline-block 都会压过 UA 的 [hidden] 规则）——R137 SELF 降级后每张卡都走「隐藏选项」分支，容器藏不掉且不填词，四个空按钮常驻。

140. 上传 /Users/haoshenqi/Downloads/books 的 7 本书（Roald Dahl 5 本+夏洛的网+动物农场）到 magicbook 书库，按分级建书架（阶1–阶6），把对应分级的书加入书架。

140. 每日学习页统计/计划/复习卡全部消失，复习队列只剩提示语（用户截图）。根因：R139 的 show() 只设内联 display，「显示」时未移除模板挂着的 hidden 属性——无作者 display 规则的元素（.panel 统计/计划、#ln-card、#ln-empty）仍被 UA [hidden] 规则隐藏。修正为属性+内联双管齐下。

## 2026-10-09

141. 划词翻译功能从 magicbook 隐藏，暂时仅通过 magiclens 实现，避免冲突。

142. https://magicbook.haoyuhang.top/read/145/epub 。整本提交 TTS 生成，加入 TTS 任务队列，然后后台慢慢处理（预生成整本书的朗读音频，后续阅读时重听零等待）。

143. 修正 R141 的隐藏边界：只隐藏 magiclens 已经做了的部分（不重复、不打架），段落翻译 magiclens 尚未实现（README 里「段落整页翻译」仍是规划 P1），阅读器段落「译」按钮要恢复。
144. 每日学习页改版（同源 moon-well R143，后端已配套）：「今日到期 1949」压垮用户——①统计头改「今日复习 x/20」进度式（数据来自 moon-well stats 新字段 todayReviewed/todayTarget；dueNow 留接口不展示）；②队列打空且仍有逾期积压时显示「今日复习完成 + 继续复习」按钮，可一直复习下去（替换现在失实的「Nothing due right now」文案）。
