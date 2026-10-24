> 归档：R183（B4 epub.js 分域，含批次 1–7 七节）原样搬移自 `response.md`。
> 2026-10-23 R211 写入触发轮转搬移，只搬移原文、不总结、不改写。

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

## 2026-10-21（R194：写作批改改为 SSE 进度流——magicbook 代理与前端）

