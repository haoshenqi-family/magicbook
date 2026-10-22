# 对话回应记录

> 含每个需求的回应、冲突说明及两个文件的总结。
> **归档规则**：本文件仅保留最近 10 个 request 的回应；更早内容原样归档至 `response-archive/`（按 request 区间分文件），需要历史细节时按编号检索归档目录，不要读全量历史。

**归档索引**

- `response-archive/response-R01-R31.md`：R1–R31（2026-08-14 ～ 2026-08-31）
- `response-archive/response-R159.md`：R159 语音输入静音检测（2026-10-14 R169 轮转，窗口转入 R160 起）
- `response-archive/response-R160-R164.md`：R160 麦克风设备选择器 + 同节嵌套的 R164 worktree 纪律修订（2026-10-14 R170 写入触发轮转搬移，父级日期标题随节一并搬移）
- `response-archive/response-R161-R162.md`：R161 公网入口超时排查（Tailscale 直连黑洞）+ R162 两本《傲慢与偏见》版本对比（2026-10-14 R173 写入触发轮转搬移，窗口转入 R165 起）
- `response-archive/response-R32-R49.md`：R32–R49（2026-09-03 ～ 2026-09-17）
- `response-archive/response-R50.md`：R50（2026-09-18）
- `response-archive/response-R51-R70.md`：R51–R70（2026-09-18 ～ 2026-09-21）
- `response-archive/response-R70-R80.md`：R70–R80（2026-09-22 ～ 2026-09-28；含 R70/R71 历史重复条与 R74 补写条，见文件头说明）
- `response-archive/response-R81-R101.md`：R81–R101（2026-09-27 ～ 2026-09-30；含 R88/R90/R98 补记与重复编号，原样搬移）
- `response-archive/response-R102-R110.md`：R102–R110（2026-09-30 ～ 2026-10-01；R110 条目含 R107/R109 代提交，R120 触发轮转搬入）
- `response-archive/response-R111-R119.md`：R111–R119（2026-10-02 ～ 2026-10-05；2026-10-08 R129 补账搬移）
- `response-archive/response-R120-R125.md`：R120–R125（2026-10-06 ～ 2026-10-07；R135 写入触发搬移，含 R134 登记的窗口欠账补账）
- `response-archive/response-R126-R131.md`：R126、R127、R128、R129、R131（2026-10-07 ～ 2026-10-08；2026-10-09 R141 写入触发轮转搬移，清掉 R134 登记的窗口欠账）
- `response-archive/response-R132-R133.md`：R132、R133（2026-10-08；2026-10-10 R143 写入触发轮转搬移）
- `response-archive/response-R134.md`：R134（2026-10-08；2026-10-10 R144 写入触发轮转搬移，其父级日期标题随节一并搬移）
- `response-archive/response-R143.md`：R143（2026-10-10；2026-10-11 R157 写入触发轮转搬移）
- `response-archive/response-R144-R153.md`：R144、R145、R147（含嵌套 R146）、R151、R152、R153（2026-10-10 ～ 2026-10-11；2026-10-12 R161 写入触发轮转搬移，清并行欠账）
- `response-archive/response-R154.md`：R154（2026-10-11；2026-10-12 R162 写入触发轮转搬移）
- `response-archive/response-R165-R173.md`：R165、R166、R167、R168、R169、R170、R172、R173（2026-10-12 ～ 2026-10-14；2026-10-15 R183 写入触发轮转搬移，窗口转入 R174 起）
- `response-archive/response-R174-R177.md`：R174、R176、R177（2026-10-15；2026-10-16 R185 写入触发轮转搬移，窗口转入 R178 起）
- `response-archive/response-R175.md`：R175（2026-10-15；2026-10-16 R188 写入触发轮转搬移，窗口转入 R178 起）
- `response-archive/response-R178.md`：R178 moon-well 防腐层迁出 web.py（B1，架构评审波 2）（2026-10-15；2026-10-16 R189 写入触发轮转搬移）
- `response-archive/response-R179.md`：R179 架构评审 B2 尝试（撤销回基线，留存重做清单）（2026-10-15；2026-10-19 R130 写入触发轮转搬移）
- `response-archive/response-R180.md`：R180 B2 前置小修两项（2026-10-21 R190 写入触发轮转搬移）
- `response-archive/response-R130.md`：R130 LLM 队列监控面板（承接 moon-well R118 契约、扩展 R126 /llm-tasks），2026-10-21 R191 写入触发轮转
- `response-archive/response-R181.md`：R181 架构评审波 3 · B2 小步重做完成：web.py 蓝图分域拆分（2026-10-21 台账合并时轮转搬移）
- `response-archive/response-R182.md`：R182 架构评审波 4 · B7：i18n 种子与 JS 清单生成化（2026-10-21 台账合并时轮转搬移）

---

> 归档索引：[response-R01-R31.md](response-archive/response-R01-R31.md) · [response-R32-R49.md](response-archive/response-R32-R49.md) · [response-R50.md](response-archive/response-R50.md) · [response-R51-R70.md](response-archive/response-R51-R70.md) · [response-R70-R80.md](response-archive/response-R70-R80.md) · [response-R81-R101.md](response-archive/response-R81-R101.md) · [response-R102-R110.md](response-archive/response-R102-R110.md) · [response-R111-R119.md](response-archive/response-R111-R119.md)（2026-10-08 R129 补账搬移）· [response-R120-R125.md](response-archive/response-R120-R125.md)（2026-10-08 R135 写入触发搬移，含 R134 登记的窗口欠账补账）· [response-R126-R131.md](response-archive/response-R126-R131.md)（2026-10-09 R141 写入触发轮转搬移）· [response-R132-R133.md](response-archive/response-R132-R133.md)（2026-10-10 R143 写入触发轮转搬移） · [response-R134.md](response-archive/response-R134.md)（2026-10-10 R144 写入触发轮转搬移） · [response-R135-R137.md](response-archive/response-R135-R137.md)（2026-10-10 R147 写入触发轮转搬移，含 R145/R146 两次写入的窗口欠账补账） · [response-R138.md](response-archive/response-R138.md)（2026-10-11 R152 写入触发轮转搬移） · [response-R139.md](response-archive/response-R139.md)（2026-10-11 R153 写入触发轮转搬移） · [response-R140.md](response-archive/response-R140.md)（2026-10-11 R153 复核后的补搬——R152 写入时搬走 R138 后窗口仍为 11） · [response-R141-R142.md](response-archive/response-R141-R142.md)（2026-10-11 R155 集成时窗口超限搬移） · [response-R144-R153.md](response-archive/response-R144-R153.md)（2026-10-12 R161 写入触发轮转搬移，清并行欠账 R144–R153） · [response-R154.md](response-archive/response-R154.md)（2026-10-12 R165 写入触发轮转搬移） · [response-R155-R156.md](response-archive/response-R155-R156.md)（2026-10-13 R166 写入触发轮转搬移，含同日同编号「细筛」那条） · [response-R157.md](response-archive/response-R157.md)（2026-10-13 R166 分支 merge origin/develop 后窗口仍达 11，续搬最旧一节） · [response-R156-mic.md](response-archive/response-R156-mic.md) · [response-R158.md](response-archive/response-R158.md)（2026-10-13 R168 写入触发轮转搬移）（2026-10-13 R167 写入触发轮转搬移；与 response-R155-R156.md 里的同编号「细筛」条目不同事） · [response-R160-R164.md](response-archive/response-R160-R164.md)（2026-10-14 R172 写入触发轮转搬移，窗口转入 R161 起） · [response-R161-R162.md](response-archive/response-R161-R162.md)（2026-10-14 R173 写入触发轮转搬移，窗口转入 R165 起） · [response-R165-R173.md](response-archive/response-R165-R173.md)（2026-10-15 R183 写入触发轮转搬移，窗口转入 R174 起） · [response-R174-R177.md](response-archive/response-R174-R177.md)（2026-10-16 R185 写入触发轮转搬移，窗口转入 R178 起） · [response-R175.md](response-archive/response-R175.md)（2026-10-16 R188 写入触发轮转搬移）

### R183（检查四仓 worktree 进度 → 用户改序「先做 moon-well 和 magicbook，app-manager 纯内网使用最后做」→ 本仓续做 B4）

- **进度盘点**：本仓架构评审已落地 B5→r177、B1→r178、B2→r181、B7→r182（均合回本地 develop 未 push），剩余编码项按波次最高优先为 **B4**（epub.js 分域，波 3）。
- **B4 前置摸底**（只读调研产出，后续批次依据）：`epub.js` 3,279 行实有 **7 个 `// =====` 主节 + 9 个 `// ---` 子节**，最大四节为整本连播 491 / TED 原声 422 / 沉浸式翻译 307 / AI 伴读 302 行；跨域共享态底账——`readerToast` 27 处、`readerCsrfToken` 17 处、`reloadIfCsrfBlocked` 16 处、`paragraphSpeechText` 7 处调用，另有 `translationPopover`（B↔D↔E↔P）、`activeTts`/`bookPlayer`/`tedAudioPlayer` 三态互斥（H↔I↔J↔K）；**三处「后定义先调用」靠函数提升兜底**（`updateBookmark` 定义 3235／绑定 49、`markVocabulary` 3113／调用 510、`currentChapterTitle` 3044／调用 1135），拆文件即断链；对外接口面仅 3 处（`window.ReaderTranslation`、`window.AICompanion.getChapter/getUnfamiliarWords`，消费方 `ai_chat.js`），`var reader` 声明在 IIFE 之外被 `read.html` 内联脚本裸用 6 处。
- **批次 1 交付**（commit `a1e58b6f`，merge `72b97ad5` 本地 develop，未 push）：搬「被最多域共用且不能有两份真相」的一层——toast / CSRF 自愈 / 段落口径（`paragraphSpeechText`、`PARAGRAPH_SELECTOR`、`BLOCK_CHILD_SELECTOR`、`collectParagraphElements`、`injectReaderToolsStyle`、词数折算）→ 新文件 `cps/static/js/reading/reader-core.js`（155 行，`window.ReaderCore`，形制同 `js/common/api.js`）。epub.js 保留同名薄委托（评审 §2.0-5 的过渡形态），27/17/16 处调用点与函数名不动；`TRANSLATION_DISPLAY_KEY`/`_DEFAULT` 一并单点化——此前设置面板写字面量、折算逻辑读字面量，两处各写一遍。
- **配套改守卫（本批次的真正价值）**：原先 5 个静态锁按 `epub.js` 单文件路径读全文，拆分后会集体误红或失明。新增 `tests/reader_js_modules.py`：按 `read.html` 真实 `<script src>` 顺序拼接 reader 模块全集，口径锁（`test_reading_tts_extractor.py`）与 CSRF 锁（`test_reading_vocabulary.py`）改读该集合——顺带把**装配顺序**纳入锁定（新文件漏插、或插到 epub.js 之后即取不到目标）。i18n 清单由 r182 的生成脚本自动收录 `reader-core.js`（`tests/i18n_js_files.json` +1 行）。
- **验证**：拆分前先立基线 **585 passed**；批次 1 后 worktree 内 **585 passed**；merge 后在 develop 新基线复跑 **585 passed**（同数、零回归，27s）。epub.js 3,279 → 3,212 行。
- **后续批次（同一 worktree 续作，不再新建树）**：按摸底清单拟 8 个域模块（TTS 簇 I+H+G+K ≈820、TED J 422、沉浸式 L 307、AI 伴读 M+N+O 477、详解面板 D 217、划词 B+C+E 420），每批一验；拆到 TTS 簇前需先设计「装配层反向依赖」接缝（各域要调 `renditionLocation`/`currentPageText`，不能反向 import 装配层私有函数）。
- **worktree 台账**：`../magicbook-arch-b5` 现检出 `refactor/r183-epub-modules`；该目录原分支 `refactor/r178-moonwell-client`（B1/B5/B2/B7 六项交付）仍待验收未删。两树合并驻留，验收通过后按闸门 `worktree remove` + `branch -d`。
- **归档**：本条写入使 `response.md` 达 19 条（并行会话多轮未轮转的欠账），按纪律把最旧 8 节（R165、R166、R167、R168、R169、R170、R172、R173，277 行）原样搬至 `response-archive/response-R165-R173.md`，窗口回 10 条内；只搬移、不总结、不改写。
- **总结**：requests.md 占号 R183（接全史最大 182）；冲突记录：无撞号，主检另有 R174/R175/R176 三条未提交并行条目，本条不重排既有记录。

### R183 续（批次 2：单词详解面板迁出 reader-word-detail.js，浏览器探针实测）

- **交付**（commit `d25ac150`，merge 本地 develop 未 push）：D 节 217 行（面板 DOM、请求序号守卫、六板块渲染、定位、Esc/✕ 关闭）整体搬到 `cps/static/js/reading/reader-word-detail.js`，epub.js 3,212→**3,018** 行。
- **边界设计（本批次的关键决定）**：两侧不能互相 import IIFE 私有函数，故由 epub.js 在载入时 `RD.setHost({normalizedWord, schedulePopoverHide, cancelAutoHide})` 注入三个回调——词形归一（C 节）与气泡自动隐藏定时器（B 节 `popoverHideTimer`）的可变状态仍由 epub.js 独占，模块只在面板生命周期里请求「挂起 / 恢复」，不带第二份真相。`RD` 缺失时 `console.error` 明报而非静默跳过（静默的表现是「详按钮点了没反应」，报障指不到载入顺序）。
- **契约测试的等价改写（只动一条）**：面板存活判定从 `wordDetailPanel` 变量改成 `RD.isOpen()`，`test_word_detail_reader_wiring_contract` 里 `if (wordDetailPanel) return;` 随之改为 `if (RD.isOpen()) return;`；其余断言（`appendWordDetailButton(popover, text)` 调用点、`function renderWordDetail…positionWordDetailPanel`、`var seq = ++wordDetailRequest`、禁止 `wordDetailRequest++`、`closeTranslationPopover` 体内不得出现 `closeWordDetailPanel`）靠 blob 读取**全部原样成立**，未削弱。
- **真机证据（静态测试看不见模块边界）**：无头 Chrome 探针 `docs/temp/wd_probe.html`（`$.ajax` 桩返回六板块 Result 信封，五步快照 initial / after-click-pending / after-render / after-esc-close / after-x-close）实测：`ReaderCore`+`ReaderWordDetail` 按 read.html 顺序均就位；点「详」走**宿主注入的** `normalizedWord`（面板标题先显示 `RUN-NORMALIZED`）；渲染出 Meaning/词源/搭配·用法·习语/变形/同反义/俚语/冷知识共 8 个小节且 lemma 把标题词替换为 `run`、变体行显示；`Esc` 关面板并恢复气泡倒计时（sched 1→2）、`✕` 同样（→4）；**全程零非空 `innerHTML` 写入**（用 `Element.prototype.innerHTML` setter 拦截计数）。
- **验证**：`node --check` 三个 JS 通过；merge 后在 develop 新基线复跑 **585 passed**（与批次 1 同数）。
- **台账**：分支 `refactor/r183-epub-modules` @ worktree `../magicbook-arch-b5`（批次 3 起继续复用，不新建树）；按家族新增的 PingCode 闭环补登 **MAGICBOOK-2 `4X51sVcJ`（In progress，等验收）**。
- **冲突记录（PingCode 侧重复风险）**：并行会话正在做「全史 requests 迁入 MAGICBOOK 需求池」（本仓 R184，其 requests 行仍在工作区未提交），其范围含 R01–**R183**；我这条 R183 已先行建为 MAGICBOOK-2。**批量迁移若按 requests.md 逐条建条目会产出一条重复的 R183**，去重归迁移会话处置（保留带进度正文的 MAGICBOOK-2 或改由迁移条目承载均可）。本轮不代改他人未提交的 requests.md。

### R183 续二（批次 3：批注域整体迁出 reader-annotations.js，八步探针验到宿主接缝）

- **交付**（commit `2b1437c7`，merge 本地 develop 未 push）：段落批注 + AI 伴读批注 + 本书批注面板共 **477 行**迁出，epub.js 2,545 行（累计 3,279→**2,545**，−734）。
- **为什么这一批先做**：摸底的「叶子」判据——本域对外只依赖装配层一处 `currentChapterTitle`（只有它持有 rendition/toc），其余全是 core 原语；反向入口只有五处（G 节两个段落按钮、E 节右键关闭、装配层 mousedown/Esc/relocated）。TTS 簇横切 `bookPlayer`/`tedAudioPlayer`/`translationPopover` 三态，不是叶子，故批次排在它前面先把模块形制与宿主回调范式立稳。
- **形制**：模块内**保留原函数与状态名**（`openAnnotationPopover` / `closeAnnotationPanel` / `annotationRequestSeq`…），正文与 epub.js 时代逐字一致，仅两处 host 依赖改走 `AN.setHost({currentChapterTitle})`，core 原语用同名别名——于是归一化契约、三条 `X-CSRFToken` 断言、iframe mousedown 关闭路径都无需改写。等价改写的四条是**状态归属变了**的那些：`if (annotationPanel)`→`if (AN.isPanelOpen())`、`if (annotationPopover)`→`AN.isPopoverOpen()`、relocated 与右键菜单里的 `closeAnnotationPopover()`→`AN.closePopover()`；工具栏「批」的联动（active 类、点按钮不被 mousedown 抢先关掉）由 `AN.panelContainsNode` / `AN.isToggleClick` 表达，与原 `clickedAnnotationToggle` 语义一致，检查强度（顺序 + `stopImmediatePropagation` 阻断）不降。
- **真机证据**：无头 Chrome 八步探针 `docs/temp/an_probe.html`（`$.ajax` 桩同时支持 done/fail 与 then/catch——第一版只桩 done/fail 时模块的 `companion-roles` 路径直接抛 `$.ajax(...).then is not a function`，顺带证明该路径确实在跑）实测：工具栏点开面板→书内批注渲染 1 张卡片（摘录「I run every morning.」）→ 关面板 `toggle.active` 清除；段落弹层打开并渲染列表 2 个节点；**提交批注的请求体 `{"paragraph":"I run every morning.","content":"本机探针批注","bookName":"Probe Book","chapter":"Chapter 1"}`**——`chapter` 证明走宿主注入回调、`paragraph` 证明走 core 归一化，两处接缝都接对了。
- **验证**：`node --check` 三个 JS；全量 **585 passed**（merge 后在 develop 新基线复跑同数）；i18n 清单生成脚本收录第 18 个文件。
- **台账**：MAGICBOOK-2 描述已更新到批次 3；worktree `../magicbook-arch-b5` 分支 `refactor/r183-epub-modules` 继续驻留复用（批次 4：沉浸式翻译 307 行或划词簇 420 行；TTS 簇 820 行需先定装配层反向依赖接缝）。冲突记录：无；moon-well 侧 `local/*` 六条暂存删除仍未处置，r189 仍无法 merge。

### R183 续三（批次 4：划词簇迁出 reader-selection.js，并补跨模块 API 表面守卫）

- **交付**（commit `cac5ed01`，merge develop 未 push）：B 翻译气泡 + C 划词发音/生词标记 + E 右键菜单共 **419 行**合成 `reader-selection.js`；epub.js 2,545→**2,135**（累计 3,279→2,135，−35%）。
- **为什么是三节合一**：它们是一次划词的三段（探测 MagicLens 接管 → 决定弹不弹气泡 → 气泡上挂 ＋/－、「详」、朗读），`translationPopover`/`popoverHideTimer`/`selectionMenu` 三份状态只在彼此之间流转；拆成三个模块只会把内部耦合升格成 API 表面。对宿主只反向依赖两张「只有装配层才有」的表：生词台账 `markVocabulary`（`vocabularyRecords`）与浏览器朗读 utterance 组装 `buildSpeechUtterance`，均经 `RS.setHost` 注入。批次 2 的 `RD.setHost` 随之改道（词形归一与倒计时挂起现归 selection 持有），本文件里那条过时注释一并更正。
- **装配层十处入口**改走 `RS.*`（`bindFrame` / `closeMenu` / `closePopover` / `isMenuOpen` / `isPopoverOpen` / `menuContainsNode` / `popoverContainsNode` / `lensOwnsHighlight` / `startWholeBookTranslation` / `window.ReaderTranslation.isOpen` 桥接）。
- **静态锁**：五处随状态归属改写调用形态（让位判定、relocated 收气泡、Esc 三段连续等），检查强度不变；`test_reader_lens_handoff.py` 与「popover 自动消失」用例原按单文件读源码，改读 reader 模块全集。
- **新增守卫** `tests/test_reader_module_surface.py`（本批次真正的价值）：跨文件调用是纯运行时的，`node --check` 与文本断言都看不见「方法名拼错」——该用例把「调用面 ⊆ 导出面」做成机械检查 + 锁载入顺序 + 锁「气泡/菜单状态只有模块一份归属」。**反向变异已验**：把 `RS.isPopoverOpen` 改成 `RS.isPopoverOpenXX` 立刻报红，改回即绿。
- **真机证据**：无头 Chrome 探针 `docs/temp/sel_probe.html` 实测让位探测随 `dataset.magiclensSelection`/`magiclensHighlight` 真假切换、`normalizedWord('  Don’t  ') === "don't"`（弯撇号归一，词族判定口径）、**以真实 RS 函数重放 `RD.setHost` 后点「详」仍渲染出 lemma 与板块**（跨模块注入路径可用）、空态下 `close*/schedule*/cancelAutoHide` 不炸。
- **验证**：`node --check` 通过；全量 **588 passed**（新增 3 例表面守卫），merge 后在 develop 新基线复跑同数。
- **未验（如实）**：装配层接线段（mousedown 外部关闭、Esc 逐层、relocated 联动）在真书页面的实际表现仍需整站真机验收——本机无 calibre 书库，epub.js 依赖 `reader`/`EPUBJS` 无法整体加载，本轮只做到「模块级真运行 + 调用面机械校验」；验收判据见 refactor-items B4②③。
- **台账**：MAGICBOOK-2 已更新到批次 4；worktree `../magicbook-arch-b5` 继续复用（批次 5 候选：沉浸式翻译 307 / TED 原声 422；TTS 簇 820 非叶子需先定装配层反向依赖接缝）。冲突记录：无新增；moon-well `local/*` 六条暂存删除仍未处置，r189 仍无法 merge。

### R183 续四（批次 5：沉浸式翻译迁出 reader-immersive.js，拆出两个真缺陷）

- **交付**（commit `f1f01b8b`，merge develop 未 push）：L 域 307 行迁出，epub.js 2,135→**1,845**（累计 3,279→1,845，**−44%**），`js/reading/` 现 9 文件。本域与两种整段播放器互斥、并取章标题做译文缓存键，故经 `setHost` 注入八个回调（I/J 拆出后应收敛成播放仲裁器，已记在模块头）。
- **拆的过程本身就是收益——两个缺陷不拆就发现不了，发现不了就是线上事故**：
  1. `ttsBookBtn.addEventListener('click', bookListenToggle)` 里的 `bookListenToggle` 是 J 节私有函数，照原样搬进模块即 **ReferenceError**——整本播放按钮直接失灵。改走宿主注入，R172/R173 的「分流判据只能运行时探测」仍在。
  2. 原 L 域末尾的载入期副作用（探测 TED 原声 + 刷新两种播放器按钮语义）和 #tts-book 绑定，都发生在模块 IIFE 执行期，那一刻宿主还是默认空函数——表现不是报错，而是**静默空操作**（「点了没反应」「第一次播有点慢」），正是家族根纪律⑦要防的那类病。现收进 `init()`，由 epub.js 注入完回调再显式调用。
- **守卫同步**：`test_reader_module_surface.py` 扩 `RI` 别名并新增「声明 init 的模块必须有调用点」（删掉 `RI.init();` 即报红）；`test_ted_audio_proxy.py` 的 #tts-book 分流锁改读模块全集、断言形态随之改为 `host.bookListenToggle`。`TRANSLATE_ENABLED_KEY` / `TRANSLATION_CACHE_MAX` 两个只被本域使用的常量归模块，F 节头部不再留副本。
- **真机证据**：无头 Chrome 探针 `docs/temp/imm_probe.html`——init **之前**点 #tts-book 计数 0（证明没绑成静默空函数）、setHost+init **之后**计数 1、`bookPlayerUpdateButtons` 与 `tedAudioEnsureLoaded` 各 1 次、`isTedBook=false` 时不刷原声按钮；逐段翻译走通（译文节点 `我每天早晨跑步。`）。注：探针第一版把桩响应写成对象显示「Translation failed」，查后端契约后确认 moon-well 的 `result` 是**数组**（`response.result[0]`），属我桩错、非代码缺陷——这条判据值得记住。
- **验证**：`node --check`；全量 **589 passed**，merge 后在 develop 新基线复跑同数。**未验**：真书页面下 `#immersive-translate` 批量翻译与整本翻译仍需整站验收（本机无书库、依赖 `reader.getContents()`）。
- **台账**：MAGICBOOK-2 已更新到批次 5。冲突记录：无新增；moon-well `local/*` 六条暂存删除仍未处置，r189 仍无法 merge。

### R183 续五（批次 6：TED 原声迁出 reader-ted-audio.js，新守卫当场逮到三处真缺陷）

- **交付**（commit `1ed7c73e`，merge develop 未 push）：J 域 422 行 → 模块 475 行，epub.js 1,845→**1,449**（累计 3,279→1,449，**−56%**；批次 6 的 commit message 写 1,438 系笔误，此处以实测为准）。`js/reading/` 现 10 文件。宿主回调八个：与整本连播/逐段朗读的互斥（`bookPlayerStop`/`bookPlayerToggle`/`bookPlayerActive`/`stopTts`/`ttsButtonsRender`）+ 翻页与章标题口径（`followPageInSection`/`renditionLocation`/`findTocLabel`）。R172/R173「分流判据只能运行时探测」保住了：探测成功才置 `TED_BOOK`，无原声仍回落 `host.bookPlayerToggle()`。
- **这批的主要产出不是搬代码，而是把一类看不见的缺陷变成必然报红**。给 `test_reader_module_surface.py` 加了「模块不得直接引用 epub.js 闭包内符号」的守卫（剥注释与字符串后取本模块可见集，命中即红），它当场逮到三处：
  1. **批次 4 遗留**：`reader-selection.js` 调 `startWholeBookProgressPolling()`（整本翻译启动后的进度轮询）——运行时 ReferenceError；
  2. **批次 4 遗留**：同文件直接读写 `vocabularyRecords`（生词台账归装配层独占，翻回已读页与 `inspectVocabulary` 都读它）——改走宿主 `applyWordRecord` / `getWordRecord`；
  3. 本批：`reader-ted-audio.js` 两处 `bookPlayer && bookPlayer.active` 条件。
 　这三处 `node --check` 不报、文本断言不报、pytest 全绿，用户侧表现是「点了没反应」。反向变异已验：把宿主回调改回直接引用即报红。
- **真机证据**：无头 Chrome 探针 `docs/temp/ted_probe.html`——`ensureLoaded()` 前 `isTedBook()=false`、后 `true`（探测驱动分流），`bindSeek(真实 document)` 与 `stop()` 在无播放态安全；顺带再验一次 R173 契约：**桩必须返回统一 Result 信封（`data.success`）**，给裸 payload 时前端按失败处理。
- **验证**：`node --check`；全量 **590 passed**（新增 1 例守卫），merge 后在 develop 新基线复跑同数。**未验**：真书页面下的原声起播/时间轴高亮/点段切播仍需整站验收（本机无书库、依赖 `reader.book.navigation`）。
- **台账**：MAGICBOOK-2 更新到批次 6；下一批只剩 TTS 簇（≈820 行，非叶子）与装配层收尾——TTS 簇建议连同「播放仲裁器」一起做（届时 immersive/ted-audio 两组共 16 个回调可收敛）。冲突记录：无新增；moon-well `local/*` 六条暂存删除仍未处置，r189 仍无法 merge。

### R183 续六（批次 7：朗读与连播迁出 reader-tts.js，B4 判据①达成）

- **交付**（commit `d2a00fff`，merge develop 未 push）：F/G/H/I 共 724 行迁出，**epub.js 3,279→734 行（−77%）**——「每文件 <1,000 行」达成，epub.js 至此只剩装配层（初始化 / 位置恢复 / 生词台账 / 书签 / 主题字体 + 七张 `setHost` 注入单）。
- **一处设计反转（针对我自己上轮的建议）**：原计划把 TTS 簇连同「播放仲裁器」一起做，实施前否掉了——仲裁器要靠 `call('ted','ensureLoaded')` 这类动态派发，而本会话刚建的守卫靠的是**静态**调用面比对；为了收敛 16 个回调去毁掉一道真逮到过 bug 的守卫不划算。实测该簇对 TED 零调用（播放器互斥在前几批已单向化），根本不需要仲裁器。
- **顺带还掉一笔过渡债**：批次 1 留在 epub.js 的四个薄委托（`readerToast` / `readerCsrfToken` / `reloadIfCsrfBlocked` / `translationDisplay*`）随本批退役，装配层仅存 5 处调用改直连 `RC.*`；薄委托只保留在模块内部（那里的价值是让正文与既有静态锁逐字一致）。
- **守卫自己也漏过一次**：`test_reader_module_surface.py` 的别名清单是手写的，漏了 `RT`/`RTTS` → 对新模块形同不设防。已改为从 `ALIASES` 单一来源生成正则（教训写进注释：手写清单本身会漂移），跨闭包白名单同步补 `RTTS`/`RTed`。反向变异已验：`RTTS.stopTtsXX` 立刻报红。
- **真机证据**：无头 Chrome 探针 `docs/temp/tts_probe.html`——API 齐全；冷路径 `stopTts()` / `bookPlayerStop(false)` / `bookPlayerUpdateButtons()` / `ttsButtonsRender(null)` 全不炸（状态机拆出来最怕冷路径抛异常）；`getTtsEngine()` 无配置回落 `browser`；`injectParagraphTools` 对两段注入 8 个按钮（含 2 个朗读键）。
- **验证**：`node --check`；全量 **590 passed**（merge 后在 develop 新基线复跑同数）。
- **B4 剩余**：判据②「阅读器全功能真机回归」与③「R172/R173 不回退」需线上整站验收；A/P 段（位置恢复 / 生词台账 / 书签）还可再拆 `reader-location` / `reader-vocabulary`，但 <1,000 已满足——是否继续由用户定夺，故台账标「判据①达成」而非「B4 完成」。
- **台账**：MAGICBOOK-2 已更新；worktree `../magicbook-arch-b5` 分支 `refactor/r183-epub-modules` 驻留待验收。冲突记录：无新增；moon-well `local/*` 六条暂存删除仍未处置，r189 仍无法 merge。

## 2026-10-16（R185 架构评审文档修正批：DF1–DF5）

### R185（magicbook DF1–DF5：把「修正声明无闭环」的实证项就地修掉）

- **范围**：家族根评审 §5 的 C-状态滞留 / C-数值冲突 / C-索引完整性中属本仓的五项。**纯文档批，零代码改动**（按 doc-fixes 清单口径「纯文档活主检出可直接做，无需 worktree」）。
- **DF1 / DF2（状态行回填，日期与 commit 全部取自 git，不凭报告改写）**：`whole-book-translation` 的 L3 状态停在「设计已确认，尚未开发」而 L1 与 hld 端点表早已上线多轮 → 已上线（2026-09-05 `04c591a3`；2026-09-17 `817f4381` 补容器重启断点续作）；`sso-user-unification` 停在「设计草案（待评审）」→ 已上线（2026-09-07 `457067c5` Authentik 唯一登录）。这两条正是 product-review(10-07) §5.2 自称已修、一周后依旧失实的原件；正文按「历史文档只标注不重写」保留原貌。
- **DF3（端口口径）**：`oidc-login.md` 三处 8085 → 生产 **8083**（fnOS），并写明 8085 系 UBT 旧部署、已停用待清理——不留「旧值加个注」的二义。家族根端口表那行属 X5/RF2，责任在家族根，未顺手改。
- **DF4（旧域）**：`docs/REQUIREMENTS.md` 两处 `hyh.haoshenqi.top` 加「已被 `magicbook.haoyuhang.top` 取代」注记。
- **DF5（索引完整性）**：L1 分级表 feat 计数由失实的 12 改为实测 **18** 并列出全量目录名；此前五个悬空 feat（ai-reading-companion / learning-hub / sso-user-unification / ted-audio-companion / whole-book-tts）现全部有入口，**遍历复查差集为空**。
- **未做（如实）**：DF6（L2 覆盖口径明示）、DF7（`docs/kb/project-describe/` 空壳填实或删除——需用户定夺）、DF8（仓库卫生：`docs/temp/` epub/mp3 入库、`test/` 与 `tests/` 并存、根目录 `None` 空文件——涉删跟踪文件，须先出清单再动）。
- **验证**：悬空复查脚本（遍历 `docs/feat/*` 与 L1/L2 引用集合）为空集；两处状态行回读；无代码改动故不跑 pytest 闸门。
- **过程失误（记下来）**：本条第一次写入时脚本的索引锚点按表格行去找、实际是列表行，`assert` 及时中止，但同一条命令里 `git add/commit` 是独立行、仍把**归档文件**先提交了（commit `cd9617c7`），造成「归档已生成、response.md 未搬移」的中间态；本提交完成搬移，两条都在本地未 push。教训：多步 shell 链里 assert 只保护它自己那一步，收尾动作要另起一条命令或前置 `&&`。
- **台账**：commit `de80c8f3` + 本条；requests.md 占号 R185，并行会话未提交的 R184（家族迁入 PingCode）随本批原样入库、内容未改；冲突记录：无撞号。窗口：本条写入使 request 数达 11，按「写入即检查」把最旧一节（R174 及其节内的 R176、R177，共 31 行）原样搬至 `response-archive/response-R174-R177.md`，窗口回 10 个 request 内。

### R186（magicbook DF6 + B6：L2 覆盖口径明示 + 整本批次三胞胎抽 JobServiceBase）

- **范围**：用户指令「做 magicbook DF6 + B6」，两项合并一轮交付；代码活按 worktree 纪律在本会话既有 worktree `magicbook-arch-b5` 续作（分支 `refactor/r186-job-service-base`，复用同一 worktree 而非新开）。
- **DF6（口径明示，不是补写七份 hld）**：L1 分级表把「首批：reading、vocabulary，其余暂以 L3 为准」这句含糊话改成**逐模块实测表**（`ls docs/*/hld/hld.md` 实测只有两份，其余五个模块连 `docs/<module>/` 目录都不存在）。配套把「待升 L2」标注从 1 份补到 6 份承载契约的 L3——AGENTS.md 一直声称这条纪律存在，此前只有 `llm-task-run/admin-monitor.md` 一份兑现，属名实不符。顺手修 reading L2 §1 的两条缺失现役端点行（`/ajax/reading-tts-cached`、`/ajax/reading-tts-book*`），它们只存在于 L3，是「L2 覆盖描述与实际一致」这条验收的直接反例。
- **B6（实测是三胞胎，不是评审登记的双胞胎）**：`reading_word_detail/service.py`（R176）是第三条同形制链路。逐字比对后归一的部分只有被证明相同的那些：`_book_file`/`_fingerprint` 三份全同、`_ensure_tables` 三份只差表名、活跃批次复用查询三份同形、30 分钟僵尸判定 = 两处常量 + 四处内联表达式、`ACTIVE_STATUSES` 两份相同。新增 `cps/reading_job/service_base.py`（191 行，其中代码 87 / 说明 104），三个 service 代码行 371/305/256 → 337/244/222（总代码行 932 → 890，减去骨架 87 后单源化 129 行重复）。
- **刻意没做的四条（写清楚，免得被当成「重构没做完」）**：①进度字典与 item 状态机不统一——三家返回字段各异，统一即改前端契约；②花名册只由朗读侧启用——翻译/详解的发布线程靠「幂等复用 + 新鲜度拦截」防重复且后端按缓存/在途跳过兜底，套上花名册会把「连点两次」从「再起一条」改成「静默跳过」，那是行为变更；③朗读 loader 不筛属主（`query(ReadingTtsJob).get(job_id)` vs 另两家 `filter_by(id, user_id)`）如实记为待决事实，鉴权不动；④`_commit_with_retry`/`_thread_db_session` 是单份实现被跨包引用，不是重复，不搬。
- **观测性守则**（moon-well M6 的教训在 Python 侧重演过一次就够）：骨架日志走 `job_log` 逐类注入，logger 名仍是 `cps.reading_*`，不塌到基类；报错文案（`translation job is unavailable` / `word detail job is unavailable` / `job not found`）与线程名 `whole-book-tts-<id8>` 逐字保持，并由守卫测试钉住。**两处措辞归一**：僵尸关闭行丢掉「; creating fresh batch」与「(no pending left)」两句尾巴，朗读崩溃行 `synth worker crashed` → `worker crashed`；无测试按这些字样断言，ES 正文检索需注意。
- **验证**：全量 `pytest tests/` **603 passed**（基线 590 + 新守卫 13 例），merge 后在主检出 develop 重跑同样 603。新增 `tests/test_job_service_base.py` 钉「骨架方法不得在子类里长回第二份 / 同一原语三家只有一份实现 / 类属性必须显式填 / 僵尸阈值单一事实源 / 文案逐字不变 / `_needs_worker` 三条边界」。**反向变异两处已做**：给 `WholeBookTtsService` 重新塞一个 `_fingerprint` ⇒ 守卫 2 例转红；把 `_own_job` 的 `user_id` 过滤删掉 ⇒ 属主边界用例转红；两次都从 `/tmp` 副本恢复并核到逐字节一致。测试桩随代码走：`calibre_db`/`config`/`threading.Thread`/`current_user` 四处 monkeypatch 的**打桩位置**移到骨架模块，断言一字未动。
- **未验（如实）**：B6 判据③「整本翻译与整本朗读各跑一轮真机批次回归」——本机无 calibre 书库跑不了真实书籍页面，需用户在线上各点一轮；B4 的判据②③ 同样仍在等真机验收。
- **交叉评审揪出三处「形状相似但判据被改」**（`140d334d`，merge `17f68bee`，全部落回原语义并各配用例）：① `_needs_worker` 的否决条件我从「`status == CANCELLED`」写成「`status not in active_statuses`」——朗读 `retry` 按 id 直取批次、终态行也会进来，于是「台账已 COMPLETED 却仍留着 PENDING 段」这种矛盾批次，旧实现会补线程拉回正轨，改后变成**点重试静默 no-op**；已落回原判据，取消态提为类属性 `cancelled_status`（朗读 `CANCELLED`、翻译与详解 `CANCELED`，注释写明这个拼写分叉）。② 一键译全库的「在跑就跳过」我写成 `not _is_stale(...)`，而旧的两条比较在 30 分整那条记录上**不是互补的**（旧＝开新批次，取反＝算在跑）；新增 `_is_fresh` 原样保留严格大于式，并用冻结时间的边界用例钉住「两条都 False」。③ `_own_job` 的 `current_user` 随方法搬进骨架后，测试桩仍打在原子类模块上 ⇒ 翻译/详解的 `get_progress/retry/cancel` 一条都没被跑到，**属主过滤这条鉴权边界失去可测性**；补齐双模块打桩，新增「别人的批次取不到 / 不存在的取不到 / 文案逐字」用例。另把 `_pending_count` 的口径写进 docstring：它数的是 `status == "PENDING"`（没人认领的活儿），不是「未完成」——翻译/详解的「未完成」含 PUBLISHED（已发给队列、正在消费），混为一谈会让自愈对着在途批次再起一条线程。这三条正是我先前那句「判据①要求行为不变」没做到的地方，记录在此而不是悄悄修掉。
- **台账与并发**：requests.md 占号 R186 于开工前单独 commit `895435ec`（先占后写，避免被整文件写回抹掉）；merge `2ff595bf` 本地 develop（本条收尾提交后 `git rev-list --count origin/develop..develop` = **33**，**未 push**；worktree `magicbook-arch-b5` 与分支 `refactor/r186-job-service-base` 原样保留待验收）。并发实况：主检出有另一会话未提交的 `cps/AGENTS.md` 改动，本批全程未触碰、未提交（所有 commit 用 `--only` 显式列文件）；另发现仓库里有一条 **2026-10-12 的 `stash@{0}: autostash`**（learning / speaking-writing / i18n_seed / layout / web.py 等一批文件），非本会话产物，未 apply 也未 drop，需要它的人自己处置。冲突记录：无撞号（R184 属并行会话的家族迁入 PingCode 条目，原样保留）。PingCode 新增 **MAGICBOOK-201**（In progress）；R183 的 `MAGICBOOK-2` 与并行迁移生成的 `MAGICBOOK-198` 仍是同需求双条目，处置待用户定夺。response.md 窗口：本条写入后为 9 个 request（R175/R178–R183/R185/R186），未触发轮转。

### R187（第四类文档失实 + DF7 删空壳 + DF8 清产物 + 三仓 push）

- **范围**：用户指令「先把第四类做掉，然后 push；DF7 先删了；DF8 的 /locals 是误提交不该被跟踪」。
- **第四类（文档失回填）**：四仓 `overview.md` 头部那句「全部待启动」按 `git log origin/<dev>..<dev>` 实测重写成进度快照——moon-well `4e4fc3d`（同批给 `.gitignore` 补了 `/local/` 兜底：`cb090d9` 只把 `local/` 移出跟踪，规则里原本只有 `.local/` 与两个子路径，`local/` 本身还能被下次 `git add` 带回来）、magicbook `2dae052e`、app-manager `c9e99f8`（main，纯文档）。**magiclens 的 overview.md 没动**：它正被并行会话持有未提交改动（他们已把 L2 行改成「进行中」），同一文件两处并发是 R113 那类残留的成因。
- **DF7（按用户选定范围：只删目录）**：`docs/kb/project-describe/` 连同唯一的 `.gitkeep` 移出仓库（`49f84e77`）。**刻意留下的那一半**：`AGENTS.md` 第 12 行「`docs/kb/project-describe/` 仍为空壳、填实或删除属待决策项」与第 121 行目录表那行仍是悬空指向，因为该文件有并行会话在途的 2 行改动（12→18 feat、6→7 模块，写得对、只是没提交），我不把他们未提交的内容混进我的 commit。已在 DF7 段落写成「一句话可做完」的遗留项。
- **DF8（用户逐条确认后删）**：`test/` 三个上游 QUnit 残骸 + 根目录 0 字节 `None` 删除，`.gitignore` 补 `/test/`（52 行）防同步上游再带回来，并在 DF8 段落补上「留 `tests/` 删 `test/`」的决策记录（那条正是 DF8 验收要求的）。**两条原描述实测失实**：`docs/temp/` 从未入库（`git log --all -- docs/temp` 空、`.gitignore` 已忽略，683MB 全是本地探针夹具）；「运行库入库」也无依据（`git ls-files` 无任何 `.db/.sqlite/.log`）。没有照着清单去删不存在的东西。
- **push 结果（用户选「三仓全推」，实际推了两仓）**：magicbook `a2cb8ba0..052f875d`（39 提交）已上线——新基线全量 **603 passed** 后推，公网探针确认 `static/js/reading/reader-tts.js` 已是 R183 批次 7 的新内容、首页 302 正常（B4 的七个 reader-* 模块**第一次真正发到线上**）；magiclens `88accf2..77bb3ce`（r46/r47/r48 三提交，无自动化框架，闸门=11 个改动 JS 文件逐个 `node --check` 全过；扩展要生效仍需另发版本）。
- **⛔ moon-well 没推，是全量闸门拦住的**：`mvn clean test -Djava.version=21`（corretto-21.0.9，`.env` 齐备）**Tests run: 1398, Failures: 3, BUILD FAILURE**——① `CreditRechargeServiceTest.packagesContainTestTierMarkedAdminOnly:100` 期望 3 实得 4；② 同类 `testTierHiddenWhenSwitchDisabled:115` 期望 2 实得 3；③ `ReadingSettingsServiceTest.currentSettingsReturnsStoredValue:71` 期望 6 实得 3。追因：**前两条不是这 13 个未推提交造成的**，破坏来自 `37aa393`（2026-10-15 09:43:14，提交信息「docks：update」）新增 `TOPUP_999`（¥999 / 500 万积分）档而没改断言，**该提交已在 origin/develop**——即线上基线从 10-15 起就带着两条红单测。本地 `.env` 最后修改 10-08 且无任何 tier/package 键，排除了「我机器配置漂移」这条解释。moon-well 的 push 需要先把这三条判红处置清楚，而「999 元档是要的还是误加」是产品判断，我不擅自改断言把它洗白。
- **顺手记一条家族级观察**：magicbook 那个 `None` 空文件的来源提交是 `83e0ec09`，与 moon-well 的 `37aa393` **同一秒（2026-10-15 09:43:14）、同一提交信息「docks：update」**。这类跨仓批量提交没跑测试就落了库，magicbook 侧留下垃圾文件、moon-well 侧留下红单测——正是评审报告 §5「修正/提交无验收闭环」那条结构性缺陷的新样本。
- **冲突记录**：`requests.md` 的 187 号本会话已提交（`94e1588a`，内容=本批），而并行会话有一条**分支名** `refactor/r187-docs-v2`（实测该分支 tip 就是 `a2cb8ba0`，**0 个自有提交、无台账行**），家族根 `Agents.md` 已被改写成「magicbook ✅ v2 已迁，R187 试点」——四仓 `git ls-files` 实测 `docs/product/` 与 `docs/project/` 命中数全为 0，即该声明目前没有仓库产物支撑。按「编号只追加不回改」：**台账 187 = 本批**；v2 迁移真正开工时请续编 **188** 并自带 L3，别沿用 187。已改的家族 `Agents.md` 属规则文件，按约定我不回改，更正写进本条。
- **窗口**：本条写入后 request 数为 10（R175/R178–R183/R185/R186/R187），仍在「保留最近 10 个」上限内，未触发轮转。

## 2026-10-16（R188 家族文档架构 v2 试点迁移：magicbook `docs/` 全仓重排）

### R188（`docs/` v1 三级体系 → v2 静态 product / 动态 project 二分；蓝本 `ops/docs-architecture.md` §7）

- **范围**：用户指令「开始 magicbook 试点」。纯文档结构迁移 + 路径口径同步，零逻辑改动（动到的 `cps/reading_job/service_base.py` 仅一行 docstring 里的文档路径）。
- **物理搬迁（`git mv`，内容原样保留、不重写）**：`docs/readme/`（8 份）→ `docs/product/readme/`；`docs/reading/hld/hld.md` → `docs/product/reading/interface.md`、`docs/vocabulary/hld/hld.md` → `docs/product/vocabulary/interface.md`；`docs/feat/`（18 个）→ `docs/project/_legacy/feat/`（**冻结归档**，内部链接一律不回溯）；空目录 `docs/tasks/` → `docs/project/tasks/`；仓库根 `requests.md` / `response.md` / `requests-archive/` / `response-archive/` → `docs/project/requests/`；游离的 `docs/REQUIREMENTS.md` 与 `docs/reading-vocabulary.md` → `docs/product/` 根（产品级 / 跨模块静态文档；已写进 `ops/docs-architecture.md` §2 说明与 §5 映射表，作为试点对蓝本的补充）。`docs/kb/` 与 `docs/superpowers/` 留原位。
- **链接修正（绝对 → 相对）**：模块页 L2 指向 `../<module>/interface.md`、L3 指向 `../../project/_legacy/feat/...`；跨仓指针（moon-well 尚未迁移）统一改成「仓库名 + 仓内相对路径」纯文本形制——相对路径跨 worktree / 主检出会失效，绝对 FS 路径又绑死机器。全量相对链接存在性脚本校验通过（`_legacy/` 与 `requests/` 冻结区除外）。
- **文档改写**：`AGENTS.md` 文档规范节整体改 v2（L1/L2/L3 新定义 + product/project 路径表 + 四问纪律含 LLD 状态行），核心工作流与「对话记录」节路径同步；`docs/product/readme/readme.md` 分级表改 v2 并**并入 develop 侧 R186 的「L2 覆盖现状（逐模块实测）」表**（路径按 v2 更新）；家族根 `Agents.md` 文档规范节 v2 + 四仓落位映射 magicbook 行改 v2（moon-well / magiclens / app-manager 标「v1 待迁」，不越权预改）。**顺手闭合 R187 遗留项**：`docs/kb/project-describe/` 已被 DF7 删除，AGENTS.md 前置阅读与路径表两处指向一并清掉——R187 当初因主检出该文件有并行会话未提交改动而挂起，本轮那份改动已被 v2 重写取代。
- **工具同步（试点副产物）**：`ops/tools/pingcode_migrate.py` 的 `collect_files` 补规则——除 `requests*` 外，`response*` 文件与 `requests-archive` / `response-archive` 目录一律跳过（台账迁进 `docs/project/requests/` 后若不跳，会把 response 台账与全量归档镜像进 Wiki；这是迁移后才暴露的口径漏洞）；`parse_requests` 增加 `ledger_dir()` 自动定位（`docs/project/requests/` 存在即用之，否则回落仓库根），供四仓陆续迁移后复用。
- **基线事故与处置（本轮最大教训）**：开工按纪律「从 `origin/develop` 切」建树，但主检出 `origin/develop` 比本地 `develop` **落后 39 个提交**（R176–R187 未 push），迁移事实上做在陈旧基线上；收尾 `git merge develop` 拉齐后冲突面比预期小（仅 `docs/product/readme/readme.md` 一处内容冲突 + 3 处 rename 目标位置提示），但 **git 静默丢掉了 develop 侧的 R187 回应条目**（`response.md` 尾部 13 行，无冲突报告）——已用 `diff <(git show develop:response.md)` 逐文件比对找出并原样补回，同一比对确认 `requests.md` 与 34 份归档文件均无损。**纪律修订建议**：切 worktree 前先跑 `git rev-list --count origin/develop..develop`，非零时改从本地 `develop` 切或先 push。
- **占号（R187 → R188）**：主检出台账在并行会话推进下已达 R187（架构评审收尾批），且 R187 的回应条目里已明确写下「v2 迁移真正开工时请续编 **188** 并自带 L3，别沿用 187」——本轮据此锁 **R188**，分支名定为 `refactor/r188-docs-v2`。
- **未做 / 待决**：① **Wiki 镜像重刷暂缓**——`pingcode_migrate.py wiki` 按 `(parent, name)` 建页且**工具无删除能力**，目录改名后重刷会在 PingCode DEV 空间留下旧目录页（`readme` / `feat` / `kb` …）与新 `product` / `project` 并存，属对远端知识库的破坏性操作；**用户 2026-10-16 拍板：暂缓重刷**（仓库 `docs/` 仍是权威源，wiki 只是只读镜像；等四仓都迁完或单独安排一轮再统一处理，现在不动就不会留下新旧并存的中间态）；② `docs/product/<module>/features/`（L3）与 `docs/project/iterations/`（迭代 LLD）本轮只落口径，**从新工作开始建**。
- **验证**：目录树与 `git status --short` 复核；相对链接存在性脚本全绿；`AGENTS.md` / 家族根 `Agents.md` / L1 索引三处 v2 口径一致性人工核对；台账窗口轮转（R175 搬 `response-R175.md`）；无行为代码改动故不跑 pytest 闸门。
- **收尾**：merge 本地 `develop`，worktree `../magicbook-docs-v2` 与分支 `refactor/r188-docs-v2` **原样保留待验收**（验收通过后再 `worktree remove` + `branch -d`）。response.md 窗口：本条写入使 request 数达 11（R175…R188），按「写入即检查」把最旧一节（R175，含其 2026-10-15 日期标题）原样搬至 `response-archive/response-R175.md`，窗口回 10 个 request（R178–R183/R185/R186/R187/R188）。
- **主检出在途改动处置**：主检出 `AGENTS.md` 一直挂着本迁移设计阶段未提交的 2 行计数改动（**12 个 feat → 18 个 feat**、**✅ 已建：readme 索引 + 6 模块 → + 7 模块**），R187 当初正因它而挂起 `docs/kb/project-describe/` 的两处指向。本轮 v2 重写已把这两处计数吸收进新表（「✅ 索引 + 7 模块」与「老 `docs/feat/`（18 个）」），故 merge 前按「被取代」丢弃该未提交改动（原值已逐字抄在本条，未留 stash）；主检出工作区在 merge 前已核为空。

### R189（X1 契约治理两端联合彩排：本机起真 moon-well，把「形制 + 解包」验穿）

- **范围**：用户选定路线 B（不等三端上线，先做两两联合）。本机起一台**真的 moon-well develop HEAD**（`4e4fc3d`，含 M4 `ResultResponseBodyAdvice` 与 M5 `UserContext`）：detached worktree `/tmp/mw-x1` + scratch MySQL(3397)/Redis(6382) + `SPRING_CONFIG_IMPORT=` 空值不碰 Nacos + ES/MinIO/NewAPI 全 dummy；magicbook 侧 `docs/temp/run_x1_pair.py` 用 `create_app` + `before_request` 注身份，**不桩 `_moonwell_proxy`**，走真 HTTP + 真 `mk-` API-key。生产零接触。
- **本轮解锁的一条老边界**：`session["moonwell_access_token"]` 只在 OIDC 回调产生、本机拿不到合法令牌 ⇒ 以往判定「依赖 moon-well 运行时的链路本机验不了」。这次直接往 `app_user` 插一行 `token='mk-<hex32>'`，走拦截器的 `mk-` 静态 key 分支查库校验 ⇒ 本机就能以合法身份打真链路。**这条姿势可复用**（已写进 LLD §7 的六步命令）。
- **判据①② 实测结论 = 达成**：五样本（200 Result / 校验失败 500 / 401 / 网关 HTML 404 / 不可达 503）+ 无头 Chrome 跑真 `api.js` 的解包矩阵。成立理由是**可达性**而不是解包会抛——`ai_chat` 走 `$.getJSON`（非 JSON 进 jQuery 的 fail 分支）、`learning`/`credits` 走 `unwrapStrict`（null 必抛），所以「parse 失败返回 null 不抛」那一格今天不可达；失败可见一侧 `credits.js` 全走 `showError`/`text-danger` 行、`learning-common.js:122` 走 `window.alert(err.message)`，姿势正确。
- **我自己的账也要更正**：占号那条把三条写重了，逐条降级并写进 LLD §4.1——① ai_chat 的吞错 catch 只在「2xx 且 `success:false`」才可能触发，属冗余写法，不是线上缺陷；② 「`reading_settings.html` 没引 i18n 种子」是**我读错了模板**：它 `{% extends "layout.html" %}`，种子在 layout 第 263 行，`mbT` 在该页有定义，故降级为「api.js 作为全站公共层硬依赖 `window.mbT`」这条**潜在约束**，本轮只把依赖写进注释、不为不存在的场景加兜底分支；③ `loadConversations` 本来就有带设计理由的 `.fail()`。**教训：库级探针只能证明「这段代码会怎样」，证明不了「线上会怎样」——判定必须再过一遍可达性。**
- **真正挖出来的一条缺陷（属 moon-well，未跨仓擅改）**：`POST hardLevel=99` 时服务端日志抛的是精确文案 `IllegalArgumentException: hardLevel 必须是 0-9 之间的有效档位`，但 `GlobalExceptionHandler` 把非 `GlobalException` 一律降级成 `500 {"success":false,"message":"系统异常，请联系管理员"}` ⇒ 用户在页面上永远只看到「系统异常」，排查要反查 traceId。这正是家族规约⑦「失败可见且可归因」要防的形态；修法属 moon-well 的异常映射（校验类 → 400 + 原文案），需那边立项。
- **落位（v2 首单）**：新建 `docs/project/iterations/2026-10-arch-review/`（本仓 v2 迁移后第一个迭代目录；`<ITER>` 取名是**提案**，改名只动一个目录）+ `x1-contract-pair-rehearsal/lld.md`（五样本原文 + 六步复现命令）；`docs/product/reading/interface.md` 补「统一信封」口径（代理原样透传 body 与状态码、不包装成「无数据」、两种解包语义的差别）。`docs/project/_legacy/feat/` 里的 arch-review 归档件按「只读不改」纪律没动。
- **验证**：全量 `pytest tests/` **603 passed**（无行为变更，唯一代码改动是 api.js 的注释块）；`node --check cps/static/js/common/api.js` 通过。
- **收尾**：merge 本地 `develop` `2984facb`（分支 `fix/r189-x1-unwrap`，worktree `../magicbook-arch-b5` 驻留待验收）；**未 push**——这批只有文档与注释，是否再触发一次 fnOS 构建由用户定。彩排件已清：moon-well JVM 停、`/tmp/mw-x1` worktree 摘除、`vt-x1-mysql`/`vt-x1-redis` **stopped 但保留**（内含那行 `mk-` 身份，重跑只需 `docker start`）、我起的 8099/18111 静态服务已停。Docker Desktop 是本轮为彩排启动的，仍开着。
- **冲突记录与自我更正**：并行会话的 v2 迁移（`6e4cb243` + 两条补记，188 号）在我上一条报告之后合入了 develop——**我那句「v2 声明无仓库产物支撑」已过时**，迁移现在是真的（`docs/product/` + `docs/project/` 有物）；我 R187 留下的 DF7 尾巴（`AGENTS.md` 指向已删除的 `docs/kb/project-describe/`）也由他们的迁移顺带清掉，**DF7 至此闭环**。编号无冲突（187=我、188=他们、189=我）。窗口：本条写入使 request 数达 11，按「写入即检查」把最早一节 R178 原样搬至 `response-archive/response-R178.md` 并登记索引。

## 2026-10-19（R130 LLM 队列监控面板：四区块实现）

### R190（用户：恢复历史写作任务、改完文稿后没有可点的「提交 AI」按钮，按钮显示「两稿已完成」）

- **根因（不是渲染缺陷）**：R168 的设计规则是「每任务初稿 + 修订稿两稿封顶」——moon-well 第三稿返回 `50513`，前端 `refreshSubmitButton` 在 `lastDraftNo >= 2` 时主动 `disabled`。用户恢复的正是已完成两稿的历史任务，所以编辑框能改、按钮不能点。用户拍板**放开两稿上限**（不是改成只读回看）。
- **前端改动**：`learning-writing.js` 删除 `done` 分支与 disable，交过稿后统一「提交修订稿」且始终可点（在途锁仍由 `busy()` 管）；提交后状态行统一为「第 N 稿已批改，可在上面改完再提交」；历史状态改为「已交第 N 稿 · 可继续修订」；一键续写固定指向最近一次写作并带稿状态（不再挑「<2 稿」）。模板按钮改「继续上次的写作」，批改面板提示补「修订次数不限」。
- **i18n**：`scripts/generate_i18n_seed.py` 追加 `Draft {{n}} reviewed · can keep revising`；`messages.po` 新增 3 条译文并 `pybabel compile` 重编 `.mo`。旧「两稿已完成」词条保留为未引用项（运行时不取）。
- **测试**：`pytest tests/test_learning_proxy.py tests/test_learning_pages_static.py tests/test_i18n_seed_contract.py` → **90 passed**；新增静态守卫 `test_writing_workshop_never_caps_draft_submissions`（禁止 `btn.disabled = done` / `lastDraftNo >= 2` / 「两稿已完成」回流）。
- **文档**：L1 `docs/product/readme/learning.md` 改为「修订次数不限」；LLD 落 `docs/project/iterations/2026-10-writing-unlimited/writing-unlimited/lld.md`（状态：开发中）。
- **收尾**：分支 `fix/r190-writing-unlimited`，merge 本地 `develop` **`67e8409e`**；合并并行 R130 后（merge `977636ee`）按用户指令 push `develop`，fnOS 构建 **END OK** + 部署 **SUCCESS**，容器 `Up (healthy)`；线上抽查 `https://magicbook.haoyuhang.top/static/js/learning-writing.js` 已无 `btn.disabled = done`、含 `can keep revising`（新状态机已生效）。worktree `../magicbook-r190-writing-unlimited` 留待验收后删除。跨仓依赖 moon-well R192（`revise` 稿号顺延）已于同一时段部署成功（`8dc8690`，active slot=blue）。
- **发布态全量闸门**：`pytest tests/` → **622 passed / 13 failed**。13 个失败全部在 `test_metadata_outbound.py`（`shutdown(cancel_futures)` 需 Python 3.9+，本机 3.8）与 `test_reading_tts_service.py`（`book file is unavailable` 缺本机书库 fixture），已在干净 `origin/develop` 基线（`d85ba8ba`）复现 **13 failed / 15 passed**，与本轮写作改动无关；本机无仓库要求的 `.venv`，故用系统 Python 3.8 跑，正式判据以 CI/容器环境为准。本轮改动的三个测试文件 **90 passed**。
- **总结**：requests.md 占号 R190；合并 origin/develop 时并行 R130 已轮转 R179，本条写入使窗口达 11，按「写入即检查」再搬最早一节 R180 至 `response-archive/response-R180.md` 并登记索引；冲突记录：与 R130 的 po/response 改动按并集合并，无撞号。
- **复测 503 说明（2026-10-21 15:40）**：用户提交修订稿收到 `learning b1: /learning/writing/revise service unavailable`。根因是回填文档的 push 触发第二次部署，moon-well 旧容器 graceful shutdown 中断了在途 revise（15:40:38），代理按连接异常返回 503。服务稳定后 moon-well 端已用系统身份端到端复验 generate → submit(1) → revise(2) → revise(3) 全部成功；前端无需改动，用户重试即可，历史草稿与批改均未丢失。该次确为部署停机窗口；**15:43 起的复发是另一因**——代理 90s 小于后端 LLM 150s 预算，见 R191。

## 2026-10-21（R191：写作批改 503 复发——代理预算小于后端 LLM 预算）

### R191（用户：近期没有部署，revise 还是 503）

- **证据（moon-well 访问日志）**：`15:43:04` 的 revise 实际返回 **200**、耗时 **104494ms**，而 magicbook 代理 `timeout=90` 先到点 → 统一返回 `learning b1: /learning/writing/revise service unavailable`；`15:49` 另一次 200 / 79814ms；`16:04`、`16:06` 两次在 magpie 150s 预算处超时。前两次是「后端成功、前端假 503」，后两次是「后端 150s 失败、前端 90s 已先 503」。
- **根因**：客户端代理预算（90s）< 后端 LLM 预算（150s，Nacos `moon-well-ai.yaml` 的 `magpie.timeout-ms: 150000`）。与蓝绿部署无关；15:40 那次才是部署停机窗口。
- **改动**：`cps/routes/learning.py` 新增 `_WRITING_LLM_TIMEOUT = 210`（后端 150s + 落库/网络余量），`/ajax/learning/writing/submit` 与 `/revise` 使用；`task/generate` 保持 90s。前端不加自动重试——幂等由 moon-well R193 保证（相同正文复用上一稿批改），自动重试只会放大供应商压力。
- **中间层核对**：Server 2 Traefik 未配置 `readTimeout/writeTimeout`（写超时默认不限）、fnOS Caddy 无响应超时、浏览器 `fetch` 无默认超时，210s 不会被先掐断。
- **测试**：`pytest tests/test_learning_proxy.py` → **52 passed**；新增 `test_writing_review_timeout_covers_backend_llm_budget`，锁住 submit/revise 两个入口的转发超时为 210s。
- **文档**：L1 `docs/product/readme/learning.md` 补「长文批改 1–3 分钟、原样重试不会多一稿」；LLD §5 记录证据、根因与预算口径。
- **收尾**：分支 `fix/r191-writing-timeout`，merge develop **`a070a9fe`**，push 后 fnOS 构建 **END OK**、容器 `Up (healthy)`；`docker exec magicbook grep _WRITING_LLM_TIMEOUT /app/cps/routes/learning.py` 确认线上为 **210**，submit/revise 两处均引用该常量。全量闸门沿用 R190 已复现的本机基线（13 个 Python 3.8/书库 fixture 失败）；本轮定向 `pytest tests/test_learning_proxy.py` **52 passed**。真实 >90s 链路需用户会话 + 长文，未做线上代理计时；预算与中间层超时已在 LLD §5 逐项核对。

- **上线后真实批改复验**：moon-well 同一 task=3 追加一句新正文后调 revise，**71.4s** 返回 `draftNo=4`、`progress=true`；该耗时已超过旧 90s 预算的边缘区间，新 210s 预算可完整承接。代理层未改业务逻辑，幂等复用路径由 moon-well R193 保证。

### R192（部署链纯文档跳过构建/部署）

- **范围**：用户指令「修改一下部署脚本，如果只有文档更新，则不触发部署」；四仓同源 + 「触发但跳过构建/部署」两口径拍板。
- **改动**：`.github/workflows/build-and-push.yml` 新增 `changes` job（compare API 取改动文件 + 文档口径正则），`build` job 加 `needs` / `if` 门禁；纯文档 push 时镜像构建、ACR 推送、`project-update` 部署通知整体跳过，step summary 留痕。
- **文档口径**：`docs/`、`doc/` 下任意文件、`*.md`、`LICENSE`、`.gitignore`、`.gitattributes`。安全侧兜底同上（首次推送 / 手动触发 / API 失败 / ≥300 文件一律走完整构建）。
- **验证**：YAML 解析通过、`bash -n` 通过、桩响应端到端 5 例符合预期（纯文档 true，其余 false）。
- **适用性提醒**：本仓 **GitHub Actions 主链已手动停用、现役是 fnOS webhook-builder 链**（`../ops/runbook.md` §1），因此本次改动属**预案**——恢复 GHA 或切回主链即生效；fnOS 链的同一判据待单独处置（脚本在 fnOS，本轮无 SSH 凭据）。
- **驻留**：worktree `../magicbook-doc-skip-deploy`，分支 `chore/r190-doc-skip-deploy`，合并 commit `a8c2af35`（本地 `develop`，未 push）。
- **补记（2026-10-21 15:55，覆盖面缺口已关闭）**：R153 记的「fnOS 链未加判据，纯文档 push 仍会构建部署」当轮补齐——fnOS `pipeline_lib.sh` 新增 `docs_only_diff` + 基线 marker（`logs/.magicbook.deployed-sha`），`build-magicbook.sh` 在 checkout 后插入 `scope-check`：纯文档时打印 `build SKIPPED (docs-only) (<sha>)` 并 `exit 0`，不构建镜像、不触发 project-update 部署、不发 Bark；`drift-check-build.sh` 已把 SKIPPED 视同 `END OK`。实测 4 例 + 端到端纯文档跳过全符合预期。详见 `../ops/runbook.md` §1 与 ops R154。

### R193（收敛 fnOS 单链 + 部署前按代码指纹判等，2026-10-21）

**背景**：magicbook 的 GHA 早已 `disabled_manually`，现役是 fnOS 链，所以「只留 fnOS」这条对本仓是**补齐代码与事实的一致性**——workflow 文件里还写着 push 触发、还挂着 R190 的 `changes` job，一旦有人 re-enable 就会双链复发。

**改动**

- `.github/workflows/build-and-push.yml`：只留 `workflow_dispatch`，删掉 `changes` job 与 build 门禁。
- 新增 `deploy/fnos/deploy.sh`：这就是 `/app/magicbook/deploy.sh` 的版本化副本——此前它只存在于 fnOS 项目目录，仓库里的 `deploy/deploy.sh` 是另一个 139 行的开发者多功能脚本，两者不是一回事。以后改部署逻辑要改 `deploy/fnos/` 这份并同步过去。
- 判等：`docker compose pull magicbook` 之后比新镜像与在跑容器的 `house.code-digest`，一致则打印「镜像代码指纹未变 -> 跳过重启」并退出——不停容器、不 `up -d`。原来的 `stop` + `start` 有停机窗口，判等直接把这窗口也省掉。

**验证**

- 假 docker 三例：指纹一致→跳过（`up -d` 0 次）；指纹变化→`[2/3]` 部署（1 次）；旧镜像无 label→保守部署（1 次）。
- 真实构建实测（只跑到 push 为止，不触发部署）：镜像 label `code-digest=d73089e559f6bab3`、`build-sha=1b3428d5…`，与 `code_digest HEAD` 算出的值一致。

**状态**：worktree `../magicbook-doc-skip-deploy`（分支 `chore/r191-deploy-skip-unchanged`），未 push。

## 2026-10-21（R194：写作批改改为 SSE 进度流——magicbook 代理与前端）

### R194（用户：批改要 70–150s，前端只有转圈，能否改成 SSE 显示进度）

- **背景与承接**：写作批改是同步 LLM 调用，实测 70–150s。R190 已放开无限修订、R191 已把代理预算提到 210s、moon-well R193 已让同文 revise 幂等，但用户在等待期间仍只看到按钮转圈，任何中间层 idle timeout 或部署切换都会把长连接掐断。本轮把 magicbook 侧批改主路径改为 SSE：状态行显示等待秒数，`result/error` 仍用统一信封，JSON 端点保留回退。
- **编号顺延（如实）**：本需求原占 R192，合入时发现并行部署链请求已占用本仓 R192/R193（纯文档跳过、fnOS 单链），按全史最大 +1 顺延为 **R194**；`requests.md`、L1/L2、LLD 与代码注释均已同步，分支名 `feat/r192-writing-sse` 与首条 commit 信息保留历史编号，不代表现行占号。跨仓同源 moon-well 顺延为 **R196**。
- **代理（`cps/routes/learning.py`）**：新增 `POST /ajax/learning/writing/submit/stream`、`/revise/stream`，复用 `_b1_payload` 白名单校验，`requests.post(stream=True, timeout=(10, 300))` 逐 chunk 透传；建连前 401 自动刷新 token 并重连一次，流开始后不重放；上游非 200 原样透传 body/状态码；响应加 `Cache-Control: no-cache`、`X-Accel-Buffering: no`、`Connection: keep-alive`；客户端断开时关闭上游连接，但不取消 moon-well 批改。
- **前端（`cps/static/js/learning-writing.js`）**：不用 `EventSource`（需要 POST body 与 `X-CSRFToken`），改 `fetch` + `ReadableStream` + `TextDecoder` 解析 `status/ping/result/error`；`ping.elapsedMs` 显示「Reviewing… Ns」；`result` 走既有 `renderReview` 并刷新历史；仅在 SSE 建连失败、HTTP 非 200 或尚未收到任何事件时回退一次 JSON，已收到 `status/ping` 后断网不重试。模板注入两个 stream URL。
- **契约**：`status {phase}` → `ping {elapsedMs}`（后端 5s 一条）→ `result Result<Review>` 或 `error Result`；建连前失败仍是 JSON 400/401/503。完整事件语义以 moon-well L2 为权威，本仓 L2 只维护代理映射与超时口径。
- **测试**：`tests/test_learning_writing_sse.py` 6 条（登录、submit/revise 映射、payload 白名单、响应头、401 刷新重连、上游非 200 透传）；静态守卫锁 `postSse/getReader/streamStarted` 与两个 stream URL、禁止 `new EventSource(`；i18n 种子新增 `Connection error` 并通过 po/mo 契约。定向 `test_learning_proxy.py + 上述三文件` **98 passed**；全量 `pytest -q` **630 passed / 13 failed**，13 个失败均为既有 Python 3.8 / 缺书籍 fixture 基线，无新增失败。
- **上线**：commit `2d2b2804`，merge develop **`4cded68c`**，push 后 fnOS 构建 **END OK**（17:15:45）、部署 **SUCCESS**，容器 `magicbook Up (healthy)`；回填编号与证据的 commit **`bf45c23a`** 再次 END OK（17:23:56），容器仍 healthy。线上 `learning-writing.js` 已含 `streamEndpoint/postSse`，模板已注入两个 stream URL。后端 SSE 直连复验见 moon-well R196：首条 ping 5.01s、87.61s 返回 result。
- **边界（如实）**：代理层 `X-Accel-Buffering` 与 401 重连由契约测试锁定，未用真实登录态在公网代理上做逐 chunk 计时；SSE 不降低 LLM 延迟，也不解决 blue-green 25s/40s drain 中断（已完成的批改会落库，未完成的仍需重试）；模型 token 级流式、异步 job 不在本轮。
- **台账**：分支 `feat/r192-writing-sse`，worktree `../magicbook-r192-writing-sse` 留待验收后按闸门删除；临时 merge worktree `../magicbook-r192-merge` 在文档回填推送后移除。冲突记录：与并行部署链 R192/R193 撞号，已顺延 R194；无内容冲突。
- **验收结论（2026-10-22，未通过/暂停）**：用户复测 task=2 修订稿，浏览器 Network 确认命中 `POST /ajax/learning/writing/revise/stream`、`200 OK`，约 2.5min 后 UI 报错、Response 面板为空。moon-well 同一请求 `09:29:47` 建连 37ms，`09:32:18` magpie `Read timed out` 后发出 SSE `error`；magpie 台账 `ms=150013,status=499`。结论：magicbook 的 SSE 代理与前端解析已生效，失败原因是后端 LLM 150s 预算耗尽，不是代理缓冲、也不是前端仍走旧 JSON。
- **DevTools 说明**：`text/event-stream` 的响应体在 Network → Response 为空是正常显示，应看 EventStream/事件列表；UI 报错对应后端 `error` 事件。
- **停止修复与配置回滚**：moon-well 侧曾临时把 Nacos `ai.providers.magpie.timeout-ms` 调到 240000，按用户“放弃修复”指令已回滚为 150000；本仓无新增代码改动。LLD 状态改为“已上线，真机验收未通过”。
- **总结**：requests.md 占号 R194；本仓 R192/R193 已被部署链占用，故不再重复占号。

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

## 2026-10-21（R203：验收时报 `RT is not defined`——B4 拆分漏带跨模块别名，4 个段落按钮失效）

### R203（用户验收 R200 时贴出：`reader-tts.js:657 Uncaught (in promise) ReferenceError: RT is not defined at bookPlayerStart`）

- **不是本轮改动引入的**：`git log -L` 定位到 `d2a00fff`（2026-10-16，R183 B4 批次 7 把段落朗读与整本连播整块迁出 epub.js）。迁移时 `RT.` / `RI.` / `AN.` 三处跨模块调用连前缀一起搬走，但这三个别名原本是 epub.js 的**函数作用域**变量（`var RT = window.ReaderTedAudio`），新文件里没有重新声明。每个 reader 模块是独立 IIFE，拿不到别人的闭包 → 运行时 `ReferenceError`。
- **影响面比报障更大（4 个按钮，全部「点了没反应」）**：① 段落「朗读」——**所有书**（`speakParagraph` → `RT.isActive()`）；② 整本连播在 TED 无原声回落时（`bookPlayerStart`，用户报障点）；③ 段落「译」按钮（`RI.translateParagraph`）；④ 批注 / AI 批注按钮（`AN.openPopover`）。后两个是加守卫时顺手扫出来的，不在报障范围内。
- **为什么两把静态锁都没响**（已写进新用例 docstring）：① `test_每个跨模块调用都在导出面上` 读的是**拼接后的 blob**——epub.js 段里的 `var RT` 让 reader-tts.js 段的 `RT.` 照样对得上号；② `test_模块不得直接引用_epubjs_闭包内的符号` 只扫**小写开头且长度 ≥5** 的标识符（`RT` 三条都不满足），还被 `_GLOBALS` 白名单兜住。教训：静态锁的**粒度**和**字符类**本身就是漏检来源，「拼接后检查」不能替代「单文件检查」。
- **修法**：`reader-tts.js` 补 `var RI/AN/RT = window.Reader*`；RT 用空实现兜底（让位类调用空转优于连累朗读），RI/AN 不兜底（用户动作空转就是本类事故本身，宁可让 epub.js 的模块缺失检查把话说明白）；顺手删掉重复的 `var TTS_ENGINE_KEY`。
- **守卫**：`tests/test_reader_module_surface.py` 新增 `test_跨模块别名必须在所属文件内声明`——按**单文件**粒度检查，先剥离注释与字符串（避免「注释里提到 `RS.setHost`」误报），别名清单复用 `ALIASES` 自动纳入新模块。**反向变异**（删掉 RT 声明）实测报红，确认这条锁真的会响。
- **测试**：`test_reader_module_surface.py` 6 passed；reader/朗读/TED 定向 **60 passed**；合并后全量 `pytest -q` **648 passed / 0 failed**（较上轮 +1，即新增守卫）。
- **上线**：branch `fix/r203-rt-alias`，merge develop **`a9ebfd58`**，push `11d041b9..a9ebfd58`。**线上实证**：部署窗口后 `curl https://magicbook.haoyuhang.top/static/js/reading/reader-tts.js` → HTTP 200、35,950 字节，文件内含 `var RT = window.ReaderTedAudio`（第 24 行起 `var RI = window.ReaderImmersive`）——这次拿到了「线上真跑新代码」的直接证据，不再是只靠可达性。
- **边界（如实）**：只做了静态与测试层验证 + 线上文件比对，**没有在浏览器里逐一点击 4 个按钮**；TED 书若原声未缓存，现在会正常走 TTS 连播（不会再崩），但仍是机器音——那是 MAGICBOOK-213 的未修项，不是本 bug。
- **台账**：R203（PingCode **MAGICBOOK-214**，进行中，待用户验收）。

## 2026-10-22（R204：写作批改 SSE 真机无进度——根因是 WSGI 容器把流缓冲掉了）

### R204（用户：还是有问题。2.5分钟后 超时，response 一直没有数据）

- **先纠正上一轮的定性**：上一轮把这次失败判成「magpie 150s 预算耗尽，代理已生效」。后半句是错的——代理确实逐 chunk `yield`，但**一帧都没离开进程**。两个缺陷同时存在，各自独立。
- **根因（容器内实测，不是推断）**：本仓用 tornado `HTTPServer(MyWSGIContainer(app))` 起 WSGI（容器内 `import gevent` 直接失败，走的 tornado 分支）。tornado ≥6.3 的 `WSGIContainer.handle_request` 把 WSGI iterable 的全部 chunk 收进 `response` 列表，最后 `b"".join` 一次性 `write_headers(chunk=body)` 并补 `Content-Length`。SSE 于是被整体缓冲：`status`/`ping` 全押到批改结束，前端整个等待期看不到任何事件——就是用户说的「一直没有数据」。
- **复现手法（可复用）**：在生产容器里跑一个与业务无关的最小 WSGI 应用（4 帧、每帧间隔 1s），用 `MyWSGIContainer` + tornado `HTTPServer` 起服务，客户端按行打时间戳。修复前：**响应头 4.00s 才出现、`Content-Length: 108`、四帧全部挤在 4.00s**。这比读代码更硬，因为用的是生产同一个类、同一个容器。
- **第二个隐蔽坑**：tornado 6.3 起 `WSGIContainer` 默认 `dummy_executor`（WSGI 应用跑在事件循环线程）。SSE 的阻塞读一次要等 5s 心跳、极端情况下整段批改，若沿用会让整站请求跟着卡死。所以流式分支必须换独立线程池。
- **修法（只动 `cps/tornado_wsgi.py` 一处）**：覆写 `handle_request`，按响应头 `Content-Type` 分流 —— ① `text/event-stream` 走流式：丢弃 `Content-Length`（上游给了也丢，否则浏览器按定长读完即关）、逐 chunk `write` 并在返回的 Future 上 await（等价 flush）、阻塞读放 16 worker 的专用 `ThreadPoolExecutor`、断连只停推送不取消上游；② 其余响应保持上游整段缓冲语义，响应形态与改动前逐字节一致。
- **测试**：新增 `tests/test_tornado_wsgi_stream.py` 4 条（真实 socket，按「首帧到达时刻」判定）：eager/lazy 两种 `start_response` 形态的流式断言、非 SSE 仍带 `Content-Length`、SSE 在途时普通请求不被阻塞。**反向变异**：把 `tornado_wsgi.py` 换回旧实现，两条流式用例立刻报红（access log `200 GET / 1511.69ms`）。
- **闸门**：定向 `test_tornado_wsgi_stream.py + test_learning_writing_sse.py + test_learning_proxy.py` **62 passed**；全量 **594 passed / 0 failed / 58 errors**，同环境主检出基线 **590 / 0 / 58**——差值正好是新增 4 条，58 个 error 全是沙箱 pytest 临时目录权限问题（`pytest-of-root` 建不了目录），与本次改动无关。
- **仍未解决（如实）**：magpie 环在 150s 处零 token 挂起（`ms=150013,status=499`），批改本身仍会以 `error` 结束。那是 moon-well 的 LLM 预算/路由问题，本仓不越界改；修完流式后，用户至少能逐秒看到进度、并在 150s 时收到明确错误而不是干等。
- **台账**：分支 `fix/r204-sse-stream`，worktree `../magicbook-r204-sse-stream` 留待验收后按闸门删除。

## 2026-10-22（R205：每日学习「单词编故事」——Hub 第八张卡 + 子页面 + SSE 代理）

### R205（承接 moon-well R200；用户：「每日学习新增一个功能，单词编故事，根据我最近需要复习的单词或者我指定的一批单词，让 AI 编一个小故事来帮助我记忆理解。」）

- **页面**：`/learning/story`，双入口（今天到期的词一键 / 粘贴词表），默认 6 词、上限 8；结果面板含标题、正文（目标词加粗）、词表卡（释义 / 原句 / `missing` / `uncached` 标签）、整篇朗读与入账提示；历史点击取详情回看。
- **代理**：`/ajax/learning/story/generate|generate/stream|history|detail`。写作专用 SSE 代理泛化为 `_llm_sse_proxy(path, label, payload_builder)`；`_story_payload` 只放行 `source/count/words/cefrLevel`，manual 的整段粘贴折成单元素 list，词长 ≤2000；detail 的 id 只认数字。
- **前端复用**：`postSse` 下沉 `learning-common.js`，写作页改为 `MB.postSse`；故事页只在建连失败 / 未收到首事件时回退 JSON，收到 `status`/`ping` 后断网不重试（故事可能已落库并入账）。
- **Hub / i18n / 配图**：中枢新增第八张卡（`data-key="story"`、`data-strand="language"`）与 `story.webp`；seed/po/mo 补齐 19 条模板词条与 8 条 JS 词条。`generate_i18n_seed.py` 修两处：mbT 双引号内含撇号漏扫、回填未转义（后者会写坏 Jinja 字典）。
- **测试**：定向 5 文件 **104 passed**（story / pages_static / hub_cards / writing_sse / i18n_seed_contract）；额外 `test_nav_settings_dropdown.py` + `test_no_duplicate_js_lines.py` **8 passed**。覆盖登录、页面元素、due 白名单、manual 折叠、非法 payload、SSE 头/事件/401 刷新、历史与 detail、50524 透传、卡片顺序与文案译文。
- **边界（如实）**：未起浏览器真机走完整链路——朗读出音、词汇股徽章 +2 分钟、历史回看均依赖登录后的真人验收；页面与静态资源已确认上线。
- **上线**：全量 **684 passed**；push `a4b1a53b..c6489147`；部署后 `/static/js/learning-story.js` 200（9,313 B），`/learning/story` 302 → `/login?next=%2Flearning%2Fstory`（登录门槛正常）。
- **台账**：requests.md 占号 R205（跨仓 moon-well R200）；分支 `feature/r205-word-story`，worktree `../magicbook-word-story` 原样驻留待验收；merge 本地 develop **`b44e20ad`**。

## 2026-10-22（R206：AI 伴读图标改「伙伴」+ 伙伴系统前端——薄代理 + /buddy 页 + FAB 换图 + 引导领取）

### R206（承接 moon-well R201；用户：「AI 伴读悬浮按钮图标改成伙伴图片……主要功能就只是图标替换。默认一个机器人。引导页到伙伴模块，可以领取雪鸮」）

- **薄代理**：新增 `cps/routes/buddy.py`（复用 `credit.py` 的 `_moonwell_proxy` 范式，注册进 `routes/__init__.py`）：`/buddy` 页 + `/ajax/buddy/{catalog,mine,claim,equip}` 透传 moon-well `/buddy`，鉴权 `@user_login_required`。
- **`/buddy` 页**：`buddy.html`/`buddy.css`/`buddy.js`——花名册卡片网格（全身图 + 名 + 炉石稀有度色签 + 使用中/装备/领取/未开放），复用 `window.MBApi` 解包与 CSRF，领取/装备后就地重渲染。
- **FAB 换图（主功能）**：`ai-companion-fab` 由文字「AI」改为「文字兜底 + `<img>`」双形态；`loadBuddyFab()` 拉 catalog 取装备伙伴 `imageUrl`，`new Image()` 预载成功才加 `has-buddy` 切图，**未上传/未装备/代理不可达一律保留「AI」文字、绝不裂图**；动效 idle 呼吸 / hover 放大 / thinking 起伏（`streamChat`→`finishMessage`，即 send 禁用→恢复窗口）/ sleep 打盹（45s 无交互），`prefers-reduced-motion` 关闭。
- **引导领取雪鸮**：`onboarding.js` 新增 `buddy` 段（`STEPS_BUDDY`，锚点 `#buddy-claim-hedwig`）；因花名册异步渲染，`init` 对 buddy 段先 return，由 `buddy.js` 渲染完调 `MagicbookOnboarding.onRosterReady()` 触发；主引导 settings 文案补 Buddies。
- **导航**：设置下拉新增 `#top_buddy → web.buddy_page`。
- **i18n**：新增英文 msgid 注册进 `i18n_seed.html`，补 `zh_Hans_CN` po 13 条并 `pybabel compile`；运行时实测 `Buddies→伙伴` 等生效。
- **验证（如实）**：JS/Python 语法校验通过（`node --check` ×3、`py_compile`）；**未起浏览器真机验收**——FAB 换图与 `/buddy` 页依赖 moon-well R201 先上线 + 18 个资产先传 MinIO（脚本 `moon-well deploy/upload_buddy_assets.py`），二者未就绪前 FAB 走文字兜底、页面无数据。
- **台账**：requests.md 占号 R206（跨仓 moon-well R201）；分支 `feat/r206-buddy`，worktree `../magicbook-buddy` 原样驻留待验收；merge 本地 develop **`cf068ddb`**（未 push）。PingCode 写入待用户单独确认。
