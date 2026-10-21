# requests.md — 对话需求记录

> 仅记录每一次对话用户的需求，除此之外不做任何事情。
> 2026-10-08 起引入归档：已确认完成且过时的条目按编号区间原样搬移至 `requests-archive/`；未完成与有经验教训价值的条目保留于此。编号永不回改、归档不释放编号，新任务按全史最大编号 +1 递增（当前最大 R173，2026-10-14 R173 轮更新）。

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

160. 语音输入加麦克风设备选择器（用户场景：合盖外接显示器，iPhone 连续互通麦克风为输入）：口语/复述面板各加设备下拉（enumerateDevices，选中值存 localStorage 跨面板同步），getUserMedia 按选择设备采集；解除浏览器 per-site 设备记忆与系统默认不一致的坑。

（R160 占号已在 worktree 创建时登记——麦克风设备选择器）

161. 排查 https://magicbook.haoyuhang.top/ 打不开的问题（2026-10-12：公网入口 TLS 正常但请求超时，需定位 Traefik→NAS 后端链路）。

## 2026-10-12

162. 对比书库两本《傲慢与偏见》（book 128 与 book 337，/read/128/epub、/read/337/epub）：两本有什么区别？书虫版是简化改写版还是内容与原著一样？

163. 整本朗读（TTS 预生成）功能调研与设计（同源 moon-well R165）：llm 已重构（R162）、整本翻译已有，需要一个类似的「整本用 TTS 生成朗读」功能。先检查是否已有（结论：无——R157 连播是在线边播边合成、R142 预热是 fnOS 手工脚本、moon-well llm_task 的 TTS 任务型无 worker），无则参照整本翻译做设计：书详情页入口、TTS 批次表、后台逐段合成写 moon-well 永久缓存、进度/重试/幂等（已缓存段跳过且不重复计费）。本轮仅设计不编码。（占号说明：追加在工作区，与并行会话 R162 轮未提交内容同文件，本轮仅提交设计文档新文件，本条随下轮提交）

164. 设计二轮拍板（承接 R163，同源 moon-well R166）：①听=消费——调用者朗读每次请求一段扣 1 积分，缓存命中也扣；②积分体系整体×10：注册送 1 万积分（原 1000）、充值套餐积分×10 价格不变（原 99 元=2万/10 元=1千 → 20万/1万，R56 先例第二次）、文本链 1k token 折 10 积分（原折 1）；听一本书约 1393 积分≈1 块钱（充值×10 后 1 积分≈0.001 元）；家人积分用 admin adjust 送（端点已有），外部用户走充值。设计文档同步更新。

165. bug 修复：阅读器「单词详解」面板内容一长就需要滚动，滚动时头部（词目 + ✕）跟着移出可视区，看到最后没法方便地关闭面板。要求滚动时把一部分内容固定住。（同源 magiclens R42，两仓详解面板保持同构）

## 2026-10-13

166. 优化每日学习模块，把「说与写」也包括进去：以 banner 的形式把 写作工坊 / AI 口语陪练 / 复述训练（4-3-2）/ 计时重读 / 听写 / 复习队列 / 选书难度匹配 做成循环的小功能，练习在各子页面进行。为每个小的学习功能生成标题、图片和详细描述，做成卡片。（占号说明：本轮先出草案，四个岔路口经 AskUserQuestion 拍板后开工；条目按「接任务即占号」锁定 R166。主检出工作区曾手工追加过同一条未提交文本，merge 时以本分支版本为准）

167. 复习队列选择题的干扰项重做（承接 moon-well R171，同源后端已交付）：后端把干扰项改成「反义项 + 用户生词 + 同难度词」三源随机抽，并新增 DISCRIMINATE 同义辨析题（正确项是该词的同义词、不等于目标词）。前端须接：①判分改按 `answer` 字段而不是 `word`（否则辨析题选对被判错）；②辨析题题干出词面而非释义；③答后展示 `answerNote` 辨析说明；④作答回传 `questionType`；⑤未知题型兜底不出死卡。另修命名冲突：L1 里现有四选一被叫作「辨析题」，新题型中文须另起名。

## 2026-10-13

168. 写作工坊支持「继续上一次未完成的写作」（承接 moon-well R172 后端契约；占号说明：原计划记 R167，merge 新基线时发现 R167 已被并行会话的复习干扰项前端占用，按「不改既存、续编空号」纪律落为 168）：历史列表只能看不能续写。四项拍板＝历史行可点 + 顶部一键续写 / 走新增任务详情端点取草稿 / tips 后端已加列落库（旧任务补不回）/ 已交初稿的连上次批改一起恢复。

169. 按方案 C 修复整本朗读批次：①_book_meta 取 book.language 抛 AttributeError（本仓 Books 无该标量列，语言在 languages 关系上）；②元数据/选角整段不得阻断批次（事故形态＝job+307 条 item 已 commit、daemon 从未 spawn，台账永久 RUNNING 0/N）；③补自愈——retry 与 reuse 遇「停滞且有 PENDING」要重新 spawn，不能只在有 FAILED 时动线程。（生产现场：Animal Farm book=143 批次 0/307 停摆 21h）

170. 承接 moon-well R175 的前端接线：伴读 agent 新增 `synthesize_tts` 工具与 SSE `audio` 事件后，magicbook 必须接上播放，否则用户只看到工具芯片打勾而不出声（正是家族纪律禁止的静默降级）。新增不计费回读代理 `/ajax/reading-tts-cached` → moon-well `POST /tts/cached-audio`；`ai_chat.js` 接 `audio` 事件播放，取不到/被浏览器拦下都要在对话里可见。关键约束：`/tts/speak` 是「听=消费」（每次含缓存命中都扣 1 积分），工具内已扣过，前端复用就会同一次朗读扣两遍——必须走回读端点。

## 2026-10-14

172. TED/博客类书的「原声伴听 + 全文同步高亮」（承接 moon-well R178 后的 TED 交付链）。用户指出：博客/TED 本质是「**一段连续原声**」，与小说类「**多段 TTS 拼接**」不同——若不区分，TED 走整本朗读会用机器音念文本而非播原声（语义错 + 白烧算力/积分）。方案：阅读器按 `calibre.bookFormat === 'TED'` 分流——TED 播整段原声 `ted-audio/<slug>.aac`（moon-well `POST /book/ted-audio` 取 `audioUrl`），用注册表段落 `tedAudioStart/End` 做当前段高亮（复用 `.reading-tts-speaking` + `bookPlayerFollowPage`）与段落级切播（点段落 seek 到 `startMs`）；无原声的普通书维持 R157 整本 TTS 连播，两模式互斥。magicbook 侧加两个薄代理 `/ajax/ted-audio`、`/ajax/ted-audio-paragraphs` → moon-well `/book/ted-audio`、`/book/paragraph/list`（**moon-well 零改动**）。本轮先出 L3 设计文档待审（`docs/feat/ted-audio-companion/design/ted-audio-companion-lld.md`）。（占号说明：本 worktree 基线为 `origin/develop`（`requests.md` 止于 R169），但主检出 develop 已有 R170、仓内已存在 R171 分支，按「续编下一个空号」锁 **R172**，避免与并行会话撞号）

173. 修复 R172「TED 原声伴听」上线后仍是 AI 合成音（用户实测反馈：线上 `epub.js` 已含 `tedAudioToggle`，但 TED 书播的还是机器音）。根因＝R172 首版分流判据 `calibre.bookFormat === 'TED'` **恒为 false**——magicbook 的 `bookFormat` 是 Calibre **文件格式**（`epub/pdf/txt`，`read.html` 里来自 URL 的 `book_format` 段，同文件 L327 还拿它当 `book_format` 提交给 Calibre），与 moon-well `BookFormatEnum.TED`（内容形态）**同名不同义**，而 TED 书在 Calibre 里同样是 `epub` ⇒ 分流从未生效，一直走 R157 逐段 TTS。修法＝判据改**运行时探测** `/ajax/ted-audio` 的 `result.audioUrl` 是否为空（有整段原声即原声伴听，否则回落 R157 整本 TTS）；`#tts-book` 点击统一走 `bookListenToggle()`（先确保探测完成再定分流）。同步取消「原声未缓存 → 隐藏按钮 + 提示」——探测区分不了「普通小说书」与「TED 但未缓存原声」，该提示会误伤普通书；改为无原声即回落 TTS、也没有 `readingTtsUrl` 才隐藏。配套：静态双锁（正向锁探测置位 + 负向锁禁止再用 `bookFormat`）+ 三条反向变异实测报红；LLD §4.1 与新增 §9 变更记录同步。

## 2026-10-15

174. 家族根架构评审任务拆分建档（跨四仓同源：moon-well R180 / magicbook R174 / magiclens R45 / app-manager R42）：阅读家族根 `docs/architecture-review-2026-10-14.md`，把评审结论拆分为各仓待办并落入各仓文档，**仅写文档不做开发**。magicbook 侧落位 `docs/feat/arch-review-2026-10/design/`（overview 总表 / refactor-items B1–B8 + X2 本仓部分 / doc-fixes DF1–DF8，含 S1/S2 状态滞留、N2 端口旧值、K1 旧域、悬空 feat 与计数失实等登记项），跨仓协同项 X1–X6 与家族根修正任务登记在家族根 `docs/arch-review-2026-10-tasks-crossrepo.md`。

176. 发布固化（同源 moon-well R182）：从 develop 检出 release/2026-10-15 分支并推送远端；给 docker 镜像打固定 release tag（不再只有 latest）方便回滚。用户拍板：仅 registry 补 tag（ssh fnOS 把 ACR 现有 latest 补打成 `release-2026-10-15`，部署引用不动）；范围仅 moon-well + magicbook；release 分支从 origin/develop 最新点切并 push。回滚姿势写入 ops/apps/app-magicbook.md。（编号说明：本地最大 R174（架构评审拆分）；并行提交已在 origin/develop 占用 R175（阅读页 CSP 放行 MinIO 外网源）；按全史最大编号 +1 取 176）

177. 架构评审波 1 开工——B5 / X1 本仓部分：统一 API 公共层。前端三套请求层（learning-common.js / ai_chat.js / vocab-test.js）+ CSRF 获取三份（#lh-csrf / #credit-csrf / input[name=csrf_token]）+ 解包语义漂移（ai_chat 容错 vs credits 严格）收编为 `static/js/common/api.js`（window.MBApi）；解包容错（非信封不误判）+ 失败必须可见；同窗口对接 moon-well M4 包装兑底（magiclens L1 后补即 X1 三端合围）。范围（用户拍板）：本轮只做 moon-well + magicbook。（编号说明：接 R176）

178. 架构评审波 2 继续——B1：抽 `cps/moonwell/` 防腐层包（web.py:1483-1977 的 _moonwell_proxy/refresh/base_url/trace_id/system_token/multipart/settings_fetch 迁出为 MoonWellClient），统一三元组返回形态（消灭失败二元组/成功三元组隐式契约），收编 oidc.py exchange 直连，7 处反向 import web 清零（ai/proxy、__init__ 恢复闭包、book_import），bridge（业务编排 107 行）按计划留守 B2。push 待用户指令。（编号说明：接 R177）

179. 架构评审波 3——B2：web.py 蓝图分域拆分（routes/reading|learning|credit|vocab，94 条定制路由迁移，endpoint 名不变，web.py 回归原版形状）。**本轮尝试未完成，已撤销回基线（549 passed）**——踩到四类坑（详见 response），方案与完整迁移清单已留存供小步重做。另：迁移中发现游离 ''' 死字符串块在 web.py 行删除后会扩大吞呑范围（get_sort_function 及大段原版路由被吞），getcomic 死块的处置需先行确认。（编号说明：接 R178）

180. B2 前置小修两项（用户指令「先做 2 和 3」）：① getcomic 死字符串块清除激活（删除 1828/1874 两个游离 ''' 行，getcomic 路由从死代码变为注册可用，真机验证点：/ajax/getcomic/<id>/<fmt>/<page> 漫画页）；② gdriveutils.py 守卫化（cli_param.gd_path 为 None 时 engine 用内存库兑底、create_all 跳过——消除 sqlite:///None 错误文件与 os.path.exists(None) TypeError，配置就绪时行为逐字不变）。完成后再启动 B2 小步重做。（编号说明：接 R179）

181. 架构评审波 3 继续——B2 小步重做完成：web.py 3304→2299 行，94 条定制路由分四批迁出（每批跑一次全量：reading 28 段→credit 19→vocab 9→learning 38），cps/routes/ 四域文件（reading 470/credit 227/vocab 146/learning 432 行，全部 <1000）；装饰注册沿用原 web blueprint（endpoint 名不变，前后比对 133 无丢失）；getcomic 死字符串块同步清除（路由激活）。push 待用户指令。（编号说明：接 R180）

182. 架构评审波 4——B7：i18n 种子与 JS 清单生成化（scripts/generate_i18n_seed.py：扫描 static/js 的 mbT() 字面量，种子字典自动追加新词条（幂等不删旧）+ tests/i18n_js_files.json 生成物入库替代手维护清单——手维护漏 3 个用 mbT 的 js 文件的实证修复；五步链两处人肉环节消除）。push 待用户指令。（编号说明：接 R181）

## 2026-10-15

175. 修复 TED 音频仍无法播放（承接 moon-well R181：MinIO 外网直链与 Nacos 配置已就绪，用户复测仍失败）。根因＝**阅读页 CSP 的 media-src 白名单拦住了 MinIO 外网源**：控制台报 `Loading media from 'https://home.haoshenqi.top:9001/magicbook/ted-audio/…' violates the following Content Security Policy directive: "media-src 'self' blob: https://dict.youdao.com"`。R172 起 TED 原声由浏览器**直连** moon-well 返回的 MinIO 公共 HTTPS 直链播放（不经 magicbook 代理），而阅读页 CSP 只放行了 `'self'`/`blob:`/有道词库源，跨源 media 被拦而静默无声。修法＝在 `cps/web.py` 的 `add_security_headers` **仅对阅读页**（`request.endpoint == "web.read_book"`）的 `media-src` 追加 `https://home.haoshenqi.top:9001`（沿用有道源同款硬编码先例；非阅读页不动，不扩大攻击面）。配套：`tests/test_csp_media.py` 新增「阅读页放行 MinIO 源」正向守卫 + 反向变异实测报红，保留「非阅读页不 emit media-src」负向锁。附：用户同时贴出的 `Blocked script execution in 'about:srcdoc'…` 系 epub.js 内容沙箱既有告警（默认 `allowScriptedContent: false` → iframe `sandbox="allow-same-origin"`，拦的是书内脚本，非父页 audio），与本次阻塞无关，判定无害不改。（占号说明：主检出 develop 工作区已有并行会话未提交的 R174 文档任务，本 worktree 基线 `origin/develop` 止于 R173，按「续编下一个空号」锁 **R175** 避免撞号）

176. 「全文单词详解」功能（跨项目 moon-well R185）：给定一本书，抽正文词表→比对详解缓存→按批把缺失词入队生成，与整本翻译、整本朗读并列为详情页第三个整本按钮。含 job/item 台账与进度页。

183. 架构评审波 3 继续——B4：`cps/static/js/reading/epub.js`（3,279 行单 IIFE、12+ 功能域混居、全仓最热文件）按文件内注释分域拆模块，epub.js 收缩为装配层（评审报告 §2.2 B4 / §3.2 🟠）。复用台账登记的该任务驻留 worktree `magicbook-arch-b5`（不新建树），基线拉到 develop（含 r176 全文详解、r181 web.py 分域、r182 i18n 生成化）。（编号说明：接本文件全史最大 182；主检出另有并行会话未提交的 R174/R175/R176 条目，本条不与既有记录重排）

184. 家族迁入 PingCode（跨仓同源：magicbook R184 / magiclens R49 / ops R131；用户指令：学习使用 PingCode，把项目搬上去）：①知识管理——本仓 `docs/` 与根 README 全量镜像至 PingCode DEV 空间（目录结构同源；顶级页与空间主页平级，主页是空间系统页、API 不能挂子页；仓库 docs/ 仍是权威源，wiki 只读镜像）；②产品管理——本仓全史 requests 197 条（R01–R183 含归档）建为 MAGICBOOK 产品需求池条目，标题 R 编号开头、描述带原文与来源脚注，状态按已完成/未完成分类（Completed/Pending/In progress/Closed）；③工作流——此后新需求先记本台账占号，再 `../ops/tools/pingcode.py idea-create magicbook "R<编号> 标题" --desc "详情"` 发布，agent 按看板领取建 worktree 开发并流转状态，产品进度以看板为准（手册 `../ops/pingcode.md` §10，家族根 AGENTS.md「需求管理」节同源）。

185. 架构评审文档修正批（magicbook DF1–DF5）：修「修正声明无闭环」的实证项——whole-book-translation 与 sso-user-unification 两份 L3 状态行按 git 里程碑回填（`04c591a3` 2026-09-05 / `817f4381` 2026-09-17；`457067c5` 2026-09-07，不凭评审报告改写）；oidc-login.md 本仓端口旧值 8085 → 生产 8083 并交代 8085 来历；REQUIREMENTS.md 旧域 hyh.haoshenqi.top 加取代注记；L1 索引 feat 计数由失实的 12 改为实测 18 并补齐 5 个悬空 feat 的入口。（编号说明：并行会话 R184 条目随本批一并入库，不重排他人记录）

186. 架构评审 magicbook 续批（DF6 + B6）：①DF6 L2 覆盖口径明示——L1 分级表把「首批」改为逐模块实测状态（reading/vocabulary 已建 hld，admin/companion/credit/learning/library 未建且契约落 L3），并给这四条链路的 L3 设计补「待升 L2」标注，使 AGENTS.md 声称的标记纪律名实相符；②B6 整本批次三胞胎抽公共骨架——`reading_translation`/`reading_tts`/`reading_word_detail` 三个 service 的正文文件解析、指纹、建表、幂等复用查询、僵尸判定与关闭、待跑项计数与 R169 自愈的花名册+原子 spawn 归一到 `cps/reading_job/service_base.py::JobServiceBase`，三个服务只留各自差异（进度口径、item 状态机、worker 循环），行为与报错文案逐字不变。（B6 判据③「整本翻译/整本朗读各跑一轮真机批次回归」需线上验收）

187. 架构评审收尾批（第四类文档失实 + DF7 + DF8 + 三仓上线）：① 四仓 overview 头部那句「全部待启动」按 `git log origin/<dev>..<dev>` 实测回填（moon-well M1–M7 已合、magicbook B1/B2/B4/B5/B6/B7 + DF1–DF6 已合、app-manager A1 未开工但 LLD 与 D1–D3 决策已入库；magiclens 的 overview.md 正被并行会话持有未提交改动，本轮不碰）；② DF7 按用户选定范围执行「只删空壳目录」——删除 `docs/kb/project-describe/`（仅 .gitkeep），AGENTS.md 的两处指向因该文件有并行会话在途改动而挂起，登记为后续项；③ DF8 删除 `test/` 三个 Calibre-Web 原版 QUnit 残留与根目录空文件 `None`（实测 pytest `testpaths` 只认 `tests/`、全仓零引用），并补 `.gitignore` 的 `/test/` 规则防再次误入；DF8 原描述「`docs/temp/` epub/mp3 入库」实测失实（该路径从未入库、`.gitignore:51` 已忽略）；④ 按用户指令 push magicbook / moon-well / magiclens 三仓 develop——上线前每仓在新基线重跑全量闸门。

188. 家族文档架构 v2 试点迁移（用户指令「开始 magicbook 试点」；蓝本 `ops/docs-architecture.md` §7）：本仓 `docs/` 由 v1 三级体系（L1 `docs/readme/` / L2 `docs/<module>/hld/` / L3 `docs/feat/`）改为 **v2 静态 product / 动态 project 二分**——`docs/product/`（L1 `readme/` 8 份、L2 `<module>/interface.md` 首批 reading/vocabulary、L3 `<module>/features/` 待新建、产品级 `REQUIREMENTS.md`、跨模块 `reading-vocabulary.md`）+ `docs/project/`（`requests/` 台账、`tasks/`、`_legacy/feat/` 冻结归档、`iterations/`）。用户拍板口径：**L1–L3 仅指产品侧静态文档**；HLD / LLD 从 L2/L3 拆出、**LLD 归 project 迭代**（`iterations/<ITER>/<工作项>/lld.md`）；`tasks/` 并入 `project/`；`his/` 取消（历史=已结束迭代）；老 `feat/`（18 个）**整体冻结归档、不回溯迭代归属、不逐功能拆分**；`requests.md`/`response.md`（含两个归档目录）由仓库根迁入 `docs/project/requests/`；magiclens / app-manager 本轮不动（单模块产品，允许退化形态）。同步改写本仓 AGENTS.md 文档规范节为 v2，并**顺手闭合 R187 遗留项**——`docs/kb/project-describe/` 已由 DF7 删除，AGENTS.md 前置阅读与路径表两处指向一并清掉；家族根 `Agents.md` 四仓落位映射的 magicbook 行改 v2。路径口径变更同步代码/文档注释 2 处（`cps/reading_job/service_base.py`、`docs/kb/instructions/workflows/oidc-login.md`）；`ops/tools/pingcode_migrate.py` 补台账过滤（`response*` 与归档目录不入 Wiki 镜像）与台账路径自动定位。（占号说明：主检出台账在并行会话推进下已达 R187，本 worktree 基线 `origin/develop` 止于 R175，按「续编下一个空号」锁 **R188**，避免与并行会话撞号）

189. X1 契约治理两端联合彩排（本机真链路，用户选定路线 B）：用 release-checklist §4.0 那套配方在本机起一台**真的 moon-well develop HEAD**（scratch MySQL 3397 + Redis 6382，`SPRING_CONFIG_IMPORT=` 空值不碰 Nacos，含 M4 ResultResponseBodyAdvice 与 M5 UserContext），magicbook 经真 HTTP + 真 `mk-` API-key 打过去、**不桩 `_moonwell_proxy`**，采五类真实响应形制（正常 Result / 上游业务失败 500 / 401 凭证无效 / 非 Result 网关 HTML / 上游不可达 503），再喂给真 `common/api.js` 跑解包矩阵。实测逮到三条：① `unwrapResult` 对「解析失败的 null」原样返回，配合 ai_chat 的 `catch (e) { convs = []; }` 会把网关故障伪装成「没有会话」（正是家族点名的静默降级反模式，且违背 ai_chat 自己注释里的契约）；② `api.js` 对 `window.mbT` 是硬依赖，`reading_settings.html` 只引 api.js 不引 i18n 种子，非信封响应的 strict 解包会抛 `TypeError: window.mbT is not a function` 而不是可读文案；③ 那两个吞错的调用点没有任何 fail 分支，jQuery 侧解析失败时面板永远停在「加载中」。处置：api.js 加 `t()` 兜底与「null 即失败」判定，ai_chat 两处改为呈现错误行（与同文件 loadMemories/loadBookProfile 的既有正确姿势对齐），并加静态形制守卫测试。

## 2026-10-21

190. 修复写作练习「恢复历史任务后改完文稿没有提交 AI 按钮」：现象＝恢复已完成任务后按钮置灰、文案「两稿已完成」。根因非渲染缺陷，而是 R168 设计规则——moon-well 每任务硬性封顶初稿+修订稿两稿（第三稿 50513），前端按 `lastDraftNo>=2` 置灰。用户拍板**放开两稿上限**：同一任务可无限次「修改后再提交批改」，每稿都对比上一稿给进步确认。magicbook 侧改按钮状态机与历史/续写状态文案；moon-well 侧改 `LearningWritingService` 的稿号分配（R192）。跨仓同源：moon-well R192。

191. 写作批改仍报 503（承接 R190 / moon-well R193）：用户复测「近期没有部署，revise 还是 503」。moon-well 日志证据：revise 实际 200、耗时 104494ms，而 magicbook 代理 `timeout=90` 先超时 → 统一返回 `service unavailable`；另两次在 magpie 150s 预算处超时。修复：把 writing submit/revise 代理超时提到 210s（显式常量 + 注释说明后端 150s 预算），并在 moon-well 侧对相同正文的修订稿做幂等复用（跨仓 R193），避免超时重试再生成一稿。跨仓同源：moon-well R193。

192. 写作批改改为 SSE 进度流（承接 R190/R191 / moon-well R194）：批改实测 70–150s，前端全程只转圈；任何中间层或部署超过预算仍可能掐断连接，用户只看到 503。改为：moon-well 新增 `submit/stream`、`revise/stream`，事件 `status/ping/result/error`；magicbook 新增 SSE 代理与 `fetch + ReadableStream` 解析，状态行显示已等待秒数；保留 JSON 端点回退，断线不取消批改，结果继续落库；同 `taskId + 正文 + submit/revise` 的并发请求共享一次批改。非目标：模型 token 级流式、异步 job、blue-green drain。跨仓同源：moon-well R194。

192. 部署链加「纯文档提交不触发部署」判据（跨仓同源：app-manager R51 / moon-well R194 / magiclens R51；用户指令「修改一下部署脚本，如果只有文档更新，则不触发部署」，四仓同源 + 「触发但跳过构建/部署」两口径拍板）：`.github/workflows/build-and-push.yml` 增 `changes` 判定 job——compare API 取本次 push 改动文件，全部是文档（`docs/`、`*.md`、`LICENSE`、`.gitignore`/`.gitattributes`）时 `docs_only=true`，构建与 app-manager 更新通知整体跳过；混合改动 / 手动触发 / 判定失败走完整构建。**注意本仓 GitHub Actions 主链已手动停用、现役为 fnOS webhook-builder 链**，本次改动属预案（恢复 GHA 或切回主链即生效），fnOS 链的同一判据待单独处置。worktree 开发，push 闸门留用户。

193. 部署链收敛 fnOS 单链 + 部署前按代码指纹判等（承 R192；跨仓同源 app-manager R52 / moon-well R195；用户拍板「只留 fnOS 链，部署之前检查 docker 镜像，如果当前镜像并没有真的改变则不触发重新部署」）：①**单链**——GHA workflow 只留 `workflow_dispatch`，`push` 不再触发，删掉 `changes` job（GitHub 侧已 `disabled_manually`）；②**指纹**——构建时打 `house.code-digest`（非文档文件树摘要）+ `house.build-sha` label；③**判等**——新增 `deploy/fnos/deploy.sh`（`/app/magicbook/deploy.sh` 的版本化副本，此前只存在于 fnOS 项目目录、未入库），`pull` 后比新镜像与在跑容器的指纹，一致则打印「镜像代码指纹未变 -> 跳过重启」并退出，不停容器、不 `up -d`。worktree 开发，push 闸门留用户。
