# requests.md — 对话需求记录

> 仅记录每一次对话用户的需求，除此之外不做任何事情。
> 2026-10-08 起引入归档：已确认完成且过时的条目按编号区间原样搬移至 `requests-archive/`；未完成与有经验教训价值的条目保留于此。编号永不回改、归档不释放编号，新任务按全史最大编号 +1 递增（当前最大 R138）。

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
