# requests.md — 对话需求记录

> 仅记录每一次对话用户的需求，除此之外不做任何事情。
> 2026-10-08 起引入归档：已确认完成且过时的条目按编号区间原样搬移至 `requests-archive/`；未完成与有经验教训价值的条目保留于此。编号永不回改、归档不释放编号，新任务按全史最大编号 +1 递增（当前最大 R153）。

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
145. moon-well 全 token 化（同源 moon-well R145，后端同步改造）：废除 X-User-* 内网互信，_moonwell_proxy 一律持凭证调用——用户会话透传 moonwell_access_token（无 token 干净 401 提示重登），系统身份后台任务改用 magicbook-system 的 mk- API key（fnOS .env MOONWELL_SYSTEM_TOKEN）；tts-warm 脚本同步改凭证。

146. MagicLens 接管检测：不要写死隐藏，改成运行时探测——发现扩展确实接管了这条能力才让位，否则保留内置实现（分能力：本帧划词中继 / 顶层生词高亮各一个标记）。跨仓同源：magiclens R37 负责写标记（v0.8.6）。

147. 为四个项目添加 worktree 使用说明（同源 moon-well R146）：接到开发任务时开一个 worktree 完成开发，完成后 merge 回 develop 再删除 worktree；或改为固定 worktree 池占用模式（每任务找未使用的 worktree，先 merge develop，完成后合回不删）。比较两种方式优劣并落地选定模式的规范。

## 2026-10-10

148. 下载 Magic Tree House（神奇树屋）系列的书（版权系列，非公版）：确定书源后下载 EPUB 并导入 magicbook 书库（去重、打分级标签、挂书架）。

149. 把 book 149 的 azw3 转成 epub 后是个合集（Magic Tree House Library 1-28），要求拆成 28 本独立 EPUB。先只读探测分册边界，再按确认口径（规范化书名 + 删每册尾部试读页/广告/丛书书目 + 丢合集前置页）批量生成到容器 /tmp 验收；写入 metadata.db 入库需单独确认。（与 R148 同系列，书源路径不同：R148 走下载，本条走已有合集拆分）
151. 四股时间预算实装统计（跨仓同源：moon-well R150 后端台账 / magicbook R151 前端）：①学习页「Today's Plan 四股行」改 actual/budget（例：阅读输入 10/5）；②阅读器新增活跃心跳，每满 5 分钟批量上报阅读时长；③web.py 增加对应 moon-well 代理路由。（随 moon-well R150 方案执行，P1 范围）

152. 「说与写」独立页面（P2，随 moon-well R150 四股台账）：写 tab（任务生成→写作→AI 批改→修订对比）+ 说 tab（AI 口语对话：场景/教练风格/会话报告；复述 4-3-2 训练）。后端 26 接口已在（B1/B2），本任务纯 magicbook 前端 + web.py 代理 + 导航入口。worktree 驻留不关（用户指令：完成后由用户确认关闭）。

153. P3 输出训练扩展：①Speaking & Writing 页新增 计时重读（RRR）与 听写 两个 tab（共用听力素材/段落接口；RRR 朗读计时入账 wpm 趋势，听写词级 diff + 一键入生词本）；②每日学习页新增四股周视图面板（strands/summary 7 天堆叠条）；③口语 coach 回复 TTS 自动朗读（复用 /ajax/reading-tts）；随 moon-well R152 查词补报端点。worktree 驻留不关（用户指令）。

154. 导航层级修正：①「每日学习」「说与写」从 Settings 下拉提为顶部一级导航（与高级搜索平级，首页直达）；②每日学习页计划面板加「说与写 →」跳转入口。（用户反馈：学习入口藏设置里太奇怪）

155. 微调 worktree 规范（家族根 + 四仓 AGENTS.md 同源修订）：不要 merge 后立即删除 worktree，改为 merge 后保留 worktree 等用户验收，验收通过后再删除。（跨四仓同源任务：moon-well R153 / magiclens R41 / app-manager R39。编号说明：本条与并行会话的 P3 输出训练曾同占 153，其已先行推送；按「只追加、不回改」原则双方记录并存，本条按纪律续编 155）
156. 词汇量测试增加「细筛」入口（同源 moon-well R155）：测试结果页与卡片提供「细筛测试」按钮，对初步测试置信区间按词频细分（250/500/1000 秩宽自适应）重测一轮；结果页展示前后对比与细档掌握度图；i18n 词条同步。（编号说明：本任务原占 154 且已随 worktree 分支入库，但占号条目在工作区被并行提交操作清除；154/155 已被并行会话的导航修正/worktree 规范占用，按「不改既存、续编空号」纪律落为 156，既有 commit 中的 R154 文案不改）


## 2026-10-11

157. 为书籍增加一个整本阅读功能：按照顺序一段一段持续朗读，随时可以暂停。（R155 评估结论落地：moon-well 零改动，播放队列全部在阅读器前端。范围=epub 阅读器连播队列/跨章自动推进/暂停继续停止/当前段高亮跟随/下一块预取/长段切块连读/手动翻章跟随。编号说明：R155 评估轮占号 155 已被并行提交操作清除，155/156 已被并行会话的 worktree 规范/词汇细筛占用，按「不改既存、续编空号」纪律落为 157）

155. 语音输入模块（随 moon-well R155 转写端点）：口语陪练与复述训练加麦克风——WebAudio 采集端编码 16k 单声道 wav（规避 MediaRecorder webm 兼容性），POST /ajax/learning/asr/transcribe 转写后回填输入框供确认发送；新增 _moonwell_multipart 转发器。

156. 麦克风按钮可用性修正（用户反馈：只有一个空白按钮不会用）：按钮加文字标签与状态自更新（语音输入→录音中 0:12·再点停止→转写中…，红色录音态），口语面板加一行用法提示；图标字体缺失时也不再是空按钮。

158. 麦克风转写卡死修复（用户实测：停止后永远停在「转写中…」且无提示）：根因 = els 注册表漏注册 'sw-s-audio-status'，停止分支对 undefined 赋值抛同步 TypeError（fetch 之前，服务端零日志）；修复 = 注册补齐 + 停止分支 try/catch 防御（任何异常必复原按钮并提示）+ 元素引用完整性静态测试（双锁：引用必已注册、注册必在模板）。

159. 语音输入静音检测（承接 R158 后用户复测仍 50517 的排查结论）：实测引擎侧 SiliconFlow 200+空文本（两次）——录音里没有可识别语音；修复 = ①上传前 PCM 峰值检测（<0.005 即 -46dB 视为设备静音，直接提示「麦克风没有采集到声音…」不上传），峰值写 console 便于远程诊断；②AudioContext 挂起兜底 resume；配合 moon-well R161（空转写 50518 与引擎故障分离）。
