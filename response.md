# 对话回应记录

> 含每个需求的回应、冲突说明及两个文件的总结。
> **归档规则**：本文件仅保留最近 10 个 request 的回应；更早内容原样归档至 `response-archive/`（按 request 区间分文件），需要历史细节时按编号检索归档目录，不要读全量历史。

**归档索引**

- `response-archive/response-R01-R31.md`：R1–R31（2026-08-14 ～ 2026-08-31）
- `response-archive/response-R32-R49.md`：R32–R49（2026-09-03 ～ 2026-09-17）
- `response-archive/response-R50.md`：R50（2026-09-18）
- `response-archive/response-R51-R70.md`：R51–R70（2026-09-18 ～ 2026-09-21）
- `response-archive/response-R70-R80.md`：R70–R80（2026-09-22 ～ 2026-09-28；含 R70/R71 历史重复条与 R74 补写条，见文件头说明）
- `response-archive/response-R81-R101.md`：R81–R101（2026-09-27 ～ 2026-09-30；含 R88/R90/R98 补记与重复编号，原样搬移）
- `response-archive/response-R102-R110.md`：R102–R110（2026-09-30 ～ 2026-10-01；R110 条目含 R107/R109 代提交，R120 触发轮转搬入）

---

## 2026-10-02（R111 阅读器导览视觉重做：降噪微调，保留挖洞）

### R111（「图书内的导览太丑了」——阅读器段 spotlight 视觉）

- **需求**：阅读器内导览观感差。经逐项确认，痛点四项全中：① 蒙层太重（整屏 `rgba(0,0,0,.62)` 盖住正在读的书页）② 挖洞的 2px `#4285f4` 蓝描边土气、像截图标注工具 ③ 360px 纯白圆角卡 + 投影是 Bootstrap 味、与阅读器排版两套语言 ④ 文字太多（中英两段正文 + 四个按钮，一步读一屏字）。方向选定「降噪微调，保留挖洞」：形态不动，只压数值、换语汇。
- **实现**（`onboarding.css` 重写 + `onboarding.js` 几何）：
  - **蒙层分级**：主段 `.38`、阅读器段 `.18`、居中卡 `.45/.30`；深色主题下「黑压黑」无对比，改极淡白纱 `.10/.08`。
  - **环去描边**：`#onb-ring` 不再 `border`，改 `inset 0 0 0 1px` 细内描边 + 内影 + `0 0 10px 4px` 外柔影，边缘色走 `--onb-ring-edge/--onb-ring-glow` 变量。
  - **卡片对齐阅读器语汇**：照 `.reading-translation-popover`（`radius 6px`、`0 4px 18px rgba(0,0,0,.22)`、accent `#4a90d9`），宽度 300px / 阅读器段 258px / 居中卡 320px，字号 13px。**根因之一**：`read.html` 不引 bootstrap，旧 `.btn .btn-primary` 在阅读器里渲染成浏览器原生灰按钮——按钮改为自带 `.onb-btn`。
  - **亮区与环分离**：`drawMask(protect, ring)`；阅读器段 `protectFor()` 取目标所在**整条工具带**（`closest("#titlebar, #sidebar, .read-footer")`）留亮，书页只吃薄纱；主段仍按目标外扩 12px。`visualRect()` 去掉 `.arrow` 的 160/80px 透明内边距热区（只在元素自身无背景/无背景图时内缩，否则按钮会被高亮成「几个字」）。
  - **深浅色卡**：`body.onb-chrome-dark` 只在阅读器段出现，按 `#main` 实际计算底色算亮度（`0.299R+0.587G+0.114B<140`）而非抄主题对照表——5 套主题加可任取颜色的 `customTheme`，查表必漏。作用域类 `onb-seg-main/onb-seg-reader/onb-chrome-dark` 在 `teardown()` 一并清理。
- **验收方式**：本机无 calibre 书库、`/read/...` 起不来，故建 gitignored 静态夹具 `docs/temp/reader_fixture.html`（按 `read.html:186-276` 1:1 复刻 DOM，引真实 CSS/JS，`?tour=1&at=N&dark=1&debug=1` 驱动并把 target/side/ring/bubble 的 rect 打进 `<pre id="dbg">`）+ 无头 Chrome 逐帧截图（`--window-size=1440,987 --virtual-time-budget=25000`，profile 每次唯一且串行）+ browser-use `evaluate_script` 读几何量。实跑（视口 831×741）：`#sidebar`=(0,0,300,741) 为亮区、环=(2,9,26,28) 只勾 18×20 的 `#show-Toc`、气泡 258×116 贴洞右侧。夹具暴露并修掉 3 个静态检查看不见的缺陷：环漏 `position:fixed` 画在 (0,0)、箭头热区圈出大块空白、深色主题无对比。
- **测试**：新增 `tests/test_onboarding_reader_visual.py` 15 项源码级回归锁（蒙层浓度单调、深色白纱、**级联顺序按规则字节位置**、环无硬描边且 fixed/pointer-events、卡片宽度相对关系、配色走变量、`read.html` 无 bootstrap 且按钮自给自足、工具带亮区、`visualRect` 内缩条件、作用域类设置与清理、亮度探测、常驻「?」重算次序、气泡 z-index 高于蒙层、蒙层容器放行点击/四边拦截）。全量 **278 passed**（含并行 R112 的 i18n 契约用例）。
- **交叉 Code Review（独立 agent）**：无 P0；3 条 P1 全部修掉——① `body.onb-chrome-dark #onb-mask.onb-dim` 与 `body.onb-seg-reader #onb-mask.onb-dim` 特异度相同、原先写在前面被静默覆盖（深色主题的居中卡仍是黑压黑，白纱设计永不生效），已调序并加**按规则字节位置**的断言（做过变异测试：换回顺序即红）；② `teardown()` 摘掉 `onb-chrome-dark` 后，常驻「?」因 `showReaderHelp()` 提前返回不再重算配色，导览结束那刻从暗色卡跳回白按钮 → 重算移到提前返回之前；③ R112 交叉产生的死选择器 `#onb-invite .onb-invite-title small` 连同 `.onb-title-en` 删除。另修一处对比度回退：深色主题环的外柔影原为黑色（黑底等于没有），改 `rgba(255,255,255,.16)` 淡白光晕，截图 `/tmp/r_d2_{band,paging}.png` 复核目标明显「亮起来」且浅色主题不受影响。未采纳的两条（换主题时配色要到下一步才跟上、次要按钮 opacity .62 对比度 4.4:1 略低于 AA）记入设计稿 §12.7 遗留。
- **文档**：设计稿新增 §12（痛点表、两段作用域、protect/ring 分离、夹具与实跑数据、与 R112 的边界、未验项）——`docs/feat/onboarding-tour/design/onboarding-tour.md`。
- **未验（诚实边界）**：真实书库下的端到端观感；主段（layout 页）在真实页面的截图——其 R111 差异只有蒙层 `.38` 与 `expand(rect,12)` 两个数值，已由源码断言覆盖，观感待用户线上走一遍确认。
- **对 requests.md/response.md 的总结**：requests.md 占号 R111（该条目已在会话中先行登记）；response.md 本条；按归档规则（R110 已完成却未归档，本次补做）把 R102 之前的 21 条回应**原样**搬移至 `response-archive/response-R81-R101.md`，保留窗口现为 R102–R111。
- **冲突记录**：**与并行 R112（语言模块）会话同文件并发写入**。R111 期间 `onboarding.js / layout.html / read.html / login.html / messages.po(.mo) / tests/test_onboarding_tour.py` 被 R112 会话同时改写，并新增 `cps/templates/i18n_seed.html`；Edit 工具两次提示 "file changed since your last read"。处置：① R111 的视觉逻辑（`setSegmentScope/applyChromePalette/expand/protectFor/visualRect/paintMask/drawMask(protect,ring)`、`.onb-btn`）在合并后的工作区**全部存活**，未被覆盖；② 原计划由 R111 落的「正文只留中文」由 R112 的 `mbT()` 取词方案实现得更彻底（中英双写行整体删除），R111 相应删除了已失效的 `#onb-bubble .onb-title-en` 死规则；③ 为避免争用同一测试文件，R111 的 15 项断言**另起新文件** `tests/test_onboarding_reader_visual.py`，未改写 R112 在写的 `tests/test_onboarding_tour.py`（该文件里「中文为主 + 英文辅助双写」的旧断言由 R112 改为走 gettext 单语，属其职责范围）。两拨改动目前都还在工作区未提交，提交前需两会话产出都稳定。

## 2026-10-02（语言模块修复：按 locale 单语切换 + JS 层 i18n 通道）

### R112（「语言模块还是有问题。很多没有双语设置，很多直接把双语显示出来了，而不是根据选择的语言切换」）

- **需求**：R102 的双语方案落地后仍有两类问题——① 很多控件中英并排硬显示，不随账号语言切换；② 很多 magicbook 自有文案中文用户看到的仍是英文。形态经两项确认：msgid 用**英文** + `zh_Hans_CN` po 出译文（与上游 Calibre-Web 约定一致，`pybabel extract` 的 jinja2 抽取器可扫），三个 User Story 全做。
- **根因拆分（三个独立成因，不是一件事）**：① R102 的「中文 + `<small>English</small>`」双写**刻意绕过 Babel**，locale 再怎么设都是两行字；② magicbook 自有 `_()` msgid 从未进过 `zh_Hans_CN` po，`_()` 只能回退 msgid（英文）；③ `epub.js` / `ai_chat.js` / `onboarding.js` 是静态 JS，**根本没有本地化通道**，阅读器里所有提示恒英文。
- **US1 模板层**：`layout.html` 设置下拉（阅读设置/成就/积分/使用引导/整本翻译）与 `login.html`（`Sign in` / `Log in` / `Sign up`）的双写全部改 `{{ _('...') }}`，入口 id 一个不改（DOM 契约）；magicbook 自有 msgid 补入 po。
- **US2 JS 通道 + 引导**：新增 `cps/templates/i18n_seed.html`——模板里 `{% set mb_i18n = {"Skip": _("Skip"), ...} %}` 渲染成 `window.MB_I18N`，配 `window.mbT(id)` 取词，消费侧统一 `var mbT = window.mbT || function (id) { return id; };` 降级；`onboarding.js` 两段步骤表（13 + 8 步）改英文 msgid 并删掉 `.onb-title-en` 英文副标题行。挂载次序是硬约束：种子必须早于 `epub.js`（顶层作用域取词），`readtxt.html` / `readpdf.html` 也补了 include（它们经 `ai_chat_panel.html` 加载 `ai_chat.js`，漏挂即静默回退）。
- **US3 阅读器文案收编**：`epub.js` 55 处、`ai_chat.js` 21 处中文字面量走 `mbT()`，含整本翻译台账、段落批注、TTS、生词本、会话与记忆面板、学情画像；带变量的句子重构成占位符式 `mbT('Whole-book translation completed: {d}/{t}').replace('{d}', …)`。
- **msgid 复用陷阱（实测）**：`Edit` / `Delete` 在上游 po 已译作「编辑书籍」「删除数据」，记忆面板复用会显示错误文案 → 改用独立 msgid `Edit memory` / `Delete memory`；`'Delete this memory?\n'` 这种把换行写进 msgid 的形态与运行时字符串不逐字符相等（po 查不到即静默英文）→ msgid 去掉换行，`\n` 在 `mbT()` 之外拼接。
- **测试**：新增 `tests/test_i18n_seed_contract.py` 4 条源码级契约（① 种子 key 与 `_()` 实参逐字符相同；② 三个 JS 的 `mbT('字面量')` 都在种子里；③ 每个种子 msgid 在 po 有非空译文；④ `onboarding.js` 步骤表 title/body 都在种子里——动态取词正则抓不到，尾点缺陷正出在这一类），并用变异测试确认四条**各自**能复现对应缺陷；渲染层在 `test_onboarding_tour.py`（种子只注入一次、en 取回 msgid、zh 取回中文并遍历全部 144 词条非空）、`test_nav_settings_dropdown.py`（en 无中文回流 / zh 无双写回流）、`test_login_invite_link.py`。全量 **275 passed**。
- **交叉 Code Review 与事故**：审查无 P0，三条 P1 全部处理——(1) 种子 key 带尾点而 `_()` 实参不带（zh 用户静默拿英文）；(2) 学习画像 3 个前缀 msgid（`Difficulty: ` / `Topics: ` / `Frequent words: `）用了 `mbT()` 却没进种子与 po，属本轮引入的本地化倒退；(3) `i18n_seed.html` 仍是 untracked 文件（提交时必须 `git add`）。P2 里修了有实际后果的一条：`String.replace` 的第二参对 `$&`/`$1` 做特殊展开，而生词文本、伴读角色名、会话名三处占位符填的正是用户可控文本（实测 `'删除会话「{t}」'.replace('{t}', '$& 测试')` 会把占位符吞掉），已改回调形式并 `node --check` 通过；其余 P2（种子内联体积、CSS `content` 里 `Tr` 徽标的脆弱性、`esc()` 不转义属性引号）记入设计稿「未采纳项与遗留」，不在本轮扩大改动面。**处置 (2) 时出过一次事故**：`write_po` 参数名写错抛异常，而目标 `.po` 已被 `open(..., "wb")` 截断为 0 字节。恢复姿势是从 `git show HEAD:` 取 base po + 用已编译的 `.mo`（1083 条译文，恰为收编后的最终态）回灌，再补 3 条新词条；事后逐条比对确认 **base 876 条 msgid 零丢失、零译文倒退、新增 211 条**。教训与脚本一并留在设计稿 §8（改 po 要写临时文件再原子替换，译文字典同时留副本）。
- **文档**：`docs/feat/language-i18n/design/language-i18n.md`（三成因对照表、种子通道四条设计约束、msgid 复用坑、四条契约、改动清单、未采纳项、事故记录）+ `docs/feat/language-i18n/ac/language-i18n-ac.md`（US1 6 项 / US2 6 项 / US3 6 项 + 回归 4 项，逐条对齐测试）。
- **未验（诚实边界）**：本机无 calibre 书库，`/`、`/book/<id>`、`/read/...` 起不来，zh 账号在真实阅读器里的中文渲染未做浏览器实跑（由 `test_i18n_seed_renders_chinese_for_zh_user` 的渲染层断言 + 契约测试覆盖）；`epub.js` 里注释与注释掉的代码仍留中文（不参与渲染，故意不动）。种子内联约 9KB/页，词条再膨胀时改独立 JSON + fetch。
- **对 requests.md/response.md 的总结**：requests.md 占号 R112（会话开始时登记）；response.md 本条；保留窗口 R102–R112（未到 10 整倍数，无归档动作）。
- **冲突记录**：① **本条推翻 R102 的一条决策**——R102 因「admin 账号 locale=en、magicbook 词条未入 po，纯 Babel 对实际用户永远英文」选了双写；本轮把词条补进 po 并让用户改用 zh_Hans_CN locale 后，双写失去存在理由，按 R112 需求删除。R102 条目文字保留不改（记录不回改）。② 与并行 R111 会话同文件并发写入（`onboarding.js` / `layout.html` / `read.html` / `messages.po(.mo)` / `tests/test_onboarding_tour.py`），Edit 工具多次提示 "file changed since your last read"；本条改动（步骤表 msgid 化、种子注入）与 R111 的视觉几何（`drawMask(protect, ring)` / `.onb-btn` / 作用域类）在合并后的工作区互不覆盖，全量 275 passed 含 R111 的 12 项视觉断言。③ 两拨改动均未提交；`cps/templates/i18n_seed.html`、`tests/test_i18n_seed_contract.py` 是新增文件，提交时需显式 `git add`（未擅自提交/推送，线上生效还需 fnOS 构建链）。

## 2026-10-02（R113 线上事故：阅读器常驻「?」点了没反应）

### R113（「阅读部分的引导模式卡死，点击？没有反应，已经强制刷新浏览器」）

- **症状**：线上阅读器页左下角常驻「?」完全点不动，用户已自行强制刷新仍无效，因而无法重放/开启阅读器段导览。
- **根因（一行 `append` 被写了两遍，且两个环节互相掩护）**：`showReaderHelp()` 里
  `$("body").append('<button id="onb-help" …>')` 出现两行逐字符相同的代码。① 监听用
  `$("#onb-help").on("click", …)` 反查节点，而 jQuery 的 ID 选择器走 `document.getElementById`
  **只返回第一个**匹配节点 → 只有 A 号按钮拿到监听；B 号是 DOM 靠后、`position:fixed` 同坐标的节点，
  按文档序画在 A 之上，是真正命中点击的那个 → 点击全落在没有监听的空壳上。② 去重守卫
  `if ($("#onb-help").length) return` 同样只数到 1，既没拦住重复，也让源码看上去只有一处渲染入口。
  「强刷无效」是这状态的指纹：入口是否渲染取决于 `localStorage` 的 `seen`，硬刷新不清 localStorage。
  顺带排除遮挡嫌疑：`#onb-help` z-index 2147483640 高于阅读器自身全部 chrome（`reader.css` 最大 10001），
  只有右下角 AI FAB(…646)/抽屉(…647) 更高，不可能盖住左下角入口——重复节点是唯一成因。
- **归因（谁引入的）**：**本会话 R111 的提交 `71d126cb`**，不是 R112。交叉 review 逐 commit 数
  `^+.*id="onb-help"`：`44cd4721`=1、`7668aec7`=1、`31027d00`（R112，未触碰 `onboarding.js`）=0、
  `71d126cb`=**2**。`onboarding.js` 当时正被两会话同文件并发改写（Edit 多次提示 "file changed since your
  last read"），R111 提交时把合并残留一并带进仓库并推送上线；R111 条目的「冲突记录」只写了并发冲突、
  没发现重复行，属当轮 review 漏检（记录不回改，更正记在本条）。线上容器实测
  `docker exec magicbook grep -c 'id="onb-help"' /app/cps/static/js/onboarding.js` → 2，`develop` 与
  `origin/develop` 齐平，即缺陷版本已构建部署。
- **修复（不做「只删一行」）**：`cps/static/js/onboarding.js:598-611`——入口节点建到局部变量 `help`，
  **监听绑在节点本身**再 `$("body").append(help)`；去重守卫改 `document.getElementById("onb-help")`
  （在 DOM 里真数节点）；`if (!isReaderPage()) return` 与重复守卫拆成两行。差别在于：将来若再产生
  重复节点，最坏是「两个都能点」，而不是「两个都点不动」。`applyChromePalette()` 仍在两个提前返回之前
  （保住 R111 §12.7-2 的暗卡配色锁）。
- **验证（真浏览器实跑，夹具 `docs/temp/reader_fixture.html?seen=1`）**：修复前——`querySelectorAll('#onb-help').length===2`、
  `jQuery('#onb-help').length===1`、两 rect 逐位重合 `(16,691,34×34)`、`elementFromPoint(圆心)` 返回 `nodes[1]`
  （`withHandler:[true,false]`）、向其 dispatch 真实 click 后 `#onb-invite` 仍为 0 → 症状完整复现。
  修复后——`#onb-help` 1 个且带监听、它就是自身圆心处的命中元素、点它出邀请卡 → Start Tour → 8 步走到
  「Happy reading」→ teardown 干净（`body.className` 空、`progress` 清空、`seen` 落盘）→ 再点「?」仍可重放；
  把 `#main` 改深色后邀请卡为 `rgb(35,36,39)`（暗卡配色未破）；console 无报错。
- **测试**：新增 3 条锁。`tests/test_onboarding_tour.py::test_reader_help_entry_appended_exactly_once`
  （函数体内 `$("body").append(` 恰好一次，另带 `applyChromePalette` 存在性作**切片自检**，防正则圈空即静默通过）、
  `::test_reader_help_handler_bound_to_created_node`（守卫必须 `getElementById`、函数体内不得出现 `$("#onb-help")`、
  `help.on("click", …)` 排在 `append(help)` 之前）、**新文件** `tests/test_no_duplicate_js_lines.py`
  （全仓自有 JS 的「相邻同文有效代码行」结构守卫，比较前丢掉空行与纯注释行，短行按 `MIN_LEN=20` 放行，
  上游 `caliBlur.js:143-144` 那对幂等 `.remove()` 走显式白名单并注明理由）。变异实测四种形态全部转红：
  线上原始两行字面 append、「字符串建一次 + append 两遍」、被注释隔开的两遍 append、以及只删重复行不改绑法时
  机制锁仍红。源码级断言统一先经 `_js_code()` 去注释（Why 注释里会复述被禁写法，全文匹配会把已修好判成缺陷）。
  全量 **281 passed**。
- **交叉 Code Review（独立 agent 视角）**：无 P0。**P1 一条被采纳并已改**——原本节/JS 注释/测试 docstring
  三处都把成因归给「R112 合并 / `31027d00`」，reviewer 用逐 commit 计数证伪，实为 `71d126cb`（R111 自己），
  归因错误会误导后续「该约束谁」，故三处文案统一更正。P2 采纳两条：切片自检断言、全仓结构守卫
  （reviewer 实测今天全仓自有 JS 仅 1 处命中且无害，成本可控）。P2 不采纳三条并记入设计稿 §13.5 遗留：
  ① `esc()` 不转义 `"` 却用于属性拼接（R112 已列为遗留，要改应连 `showInvite` 一起改 `.attr()` 构造，
  不在事故修复里做半套）；② `init()` 的提前 `return` 分支不渲染常驻「?」，首访用户在阅读器里点「以后再说」
  后本次会话内既无蒙层也无入口、需刷新才出现——修法要先给 `showInvite` 补去重守卫（`onboarding.js:573`
  目前无守卫，直接同调会造两张叠卡），且它改变「看过才给 ?」的语义，应单独一轮定 AC，不与本次混提交；
  ③ 不引入 eslint/prettier（无前端构建链，格式 churn 会掩盖真实 diff）。确认 R111/R112 契约未破。
- **文档**：`docs/feat/onboarding-tour/design/onboarding-tour.md` 新增 §13（13.1 根因与失效链两环 + 夹具实测数据 +
  逐 commit 归因证据、13.2 修法与「为什么不只删一行」、13.3 三条回归锁与四种变异、13.4 同类风险扫描与实跑、
  13.5 交叉 review 吸收与不采纳）。
- **未验（诚实边界）**：修复仍在工作区，**未提交未推送**（线上那份坏代码要等构建部署后才替换），故线上
  真实阅读器页的「?」点击无法在本轮复验；本轮以 z 序审计 + 夹具真浏览器实跑替代。控制浏览器无该站登录会话，
  因此未做线上只读复现（线上证据是容器内文件计数）。部署侧提醒：`cps/cache_buster.py:52` 按文件内容 md5
  生成 `?q=`，新 JS 上线后用户无需强刷即可拿到——反过来说，本轮之前用户强刷也只会拿到同一份坏代码。
- **对 requests.md/response.md 的总结**：requests.md 占号 R113（会话开始时登记，编号无冲突）；response.md 本条；
  保留窗口 R102–R113（113%10≠0，无归档动作）。

## 2026-10-03（R114 输入法回车误提交优化：全局 IME 守卫）

### R114（「我经常在输入法中输入回车，magicbook 就自动提交了搜索条件，想完全写完再提交」）

- **根因**：全仓自有 JS/模板无任何 composition/isComposing 处理。中文 IME 用回车确认候选词时，
  keydown(Enter) 会连带触发原生 form 隐式提交或元素级 Enter 监听，涉及 5 类入口：
  `layout.html` header 搜索（GET 跳转）、`basic_layout.html` 精简主题搜索、`search_form.html`
  高级搜索（POST）、`book_edit.html` meta-search + typeahead 下拉回车选中、`ai_chat.js` 裸 Enter 发送。
- **方案（用户选定「IME 守卫」而非全面禁回车）**：新增 `cps/static/js/ime_guard.js`——
  document **捕获阶段**监听 keydown：keyCode 229 一律拦截；无修饰键的 Enter 在
  isComposing/composition 标记期间 `preventDefault + stopPropagation`（同时挡住原生提交与
  typeahead 等元素级监听）；compositionstart/end 维护标记，compositionend 后留 100ms 宽限
  （兼容候选先上屏、再补发裸 Enter 的 IME 时序）。非组合输入的 Enter 行为完全不变。
- **接入**：`layout.html`（覆盖主主题全部页面）、`basic_layout.html`（精简主题）、
  `ai_chat_panel.html`（read/readpdf/readtxt 系独立模板，随面板引入）。不改 typeahead.bundle.js 库源码。
- **验证**：`node --check` 语法通过；无头 Chrome 夹具 `docs/temp/ime_guard_fixture.html` 合成事件 5 项断言
  全过（composing 拦截 / 229 兜底拦截 / Ctrl+Enter 放行 / 宽限期内拦截 / 宽限期后放行）——首轮夹具曾暴露
  「229 事件 key 非 Enter 被提前返回漏拦」，据此重写守卫判定顺序。全量 pytest **281 passed**。
- **未验（诚实边界）**：真实 IME 组合输入无法在无头浏览器复现，端到端手感（Windows 微信键盘/搜狗等）
  需上线后用户实测；本轮以合成事件夹具替代。
- **对 requests.md/response.md 的总结**：requests.md 占号 R114；response.md 本条；
  保留窗口 R102–R114（114%10≠0，无归档动作）。

## 2026-10-04（R115 引入《新概念英语》全四册到线上书库）

### R115（「我想引入新概念英语 到magicbook」）

- **来源（用户选定「联网检索下载」）**：GitHub `tangx/New-Concept-English`（非 LFS 直存四册教材 PDF +
  276 课 mp3/lrc 音频）。下载至 `docs/temp/nce/`（9.3/19/14/16MB，%%EOF 完整、字节数与仓库 blob 一致）。
- **入库通道**：先走网页 UI（用户登录 authentik→导航栏隐藏 `#btn-upload` 显形→自动提交），第一册 9.3MB
  成功入库 #92；第二/三册（19MB、13.5MB）POST /upload 均中断（xhr status 0，前端报「File size may be too big」），
  重试一次仍失败——**确定性失败**，阈值在 9.3–13.5MB 之间，magicbook 应用本身无大小配置项，系公网
  Traefik(Server 2)→fnOS Tornado 链路限制。**遗留问题**：>10MB 文件无法经 UI 上传，待修复链路（记入待办）。
- **剩余三册（用户改选「ssh fnOS 原文件入库」）**：scp 内网到 /tmp/nce → `docker cp` 进 magicbook 容器 →
  `calibredb add --library-path /calibre-library` 入库为 #93/#94/#95（web 实时识别，无需重启）；
  `calibredb set_metadata --field` 统一四册元数据：title「新概念英语 N 副书名」、authors L. G. Alexander、
  出版社外语教学与研究出版社、丛书「新概念英语」#1–4、tags 英语学习/教材、languages en。
  临时文件已清理（主机与容器 /tmp）。
- **验证**：`/ajax/listbooks?search=新概念` 四册字段正确（旧 PDF 元数据的 NUL 尾巴已被覆盖）；
  `/download/<id>/pdf` HEAD 四册均 200 且 Content-Length 与原始字节数一致；书库目录
  `/app/magicbook/library/L. G. Alexander/` 落盘 4 个 PDF。
- **未验（诚实边界）**：阅读器内 PDF 翻页体验（扫描件体积大、无书签导航）未逐册实测；未做线上封面/详情页截图。
- **可选后续**：四册均无封面（has_cover 0），可用 ImageGen 生成统一丛书封面（先例 R104 book#89）。
- **对 requests.md/response.md 的总结**：requests.md 占号 R115；response.md 本条；
  保留窗口 R102–R115（115%10≠0，无归档动作）。

---

## R117（2026-10-04）ES 日志级别分析（magicbook 侧）

- **需求**：requests.md R117（与 moon-well R96 同任务）。
- **结论**：app-log-magicbook 全量仅 5363 条/13 天（warn 1695 / info 822 / error 71，无 debug/trace；另 2775 条为多行日志续行如 Python warnings 堆栈，filebeat 不打级别），量级太小，**不建议调整级别**。warn 主要是 db.py:937 "Author not found" 上游噪音与 uploader.py:251 ImageMagick policy 限制，可忽略；error 主要是 helper.py:953 File not found——**book 92–95（《新概念英语》四册）源文件在 /calibre-library 缺失**，属真实数据问题（与 book 2/19/20 待重传同类），建议列入重传清单。
- **冲突记录**：无。

### 总结

- **requests.md**：占号 R117。
- **response.md**：本条。

## 2026-10-04（Chrome 插件可行性评估）

### R118（magicbook 非 calibre-web 阅读能力做成 Chrome 插件——可行性评估，只读不改码）

- **需求**：把 magicbook 非 calibre-web 部分（词汇表、翻译、语音生成等阅读能力）做成 Chrome 插件，自由翻译任意 web 页面的单词/段落，逻辑与 magicbook 一致。
- **架构事实**（调研结论）：
  - magicbook 的阅读能力后端全部是 moon-well 薄代理（`cps/web.py` `_moonwell_proxy`）：生词判定 `/vocabulary/reading/analyze`、划词翻译 `/vocabulary/reading/translate`、批量段落翻译 `/vocabulary/reading/translate-batch`、词标记 `GET /vocabulary/known|unknown/{word}`、TTS `/tts/speak`、阅读设置 `/vocabulary/reading/settings(+/hard-level)`。前端逻辑集中在 `cps/static/js/reading/epub.js`（2063 行，含划词气泡、段落译文注入、生词波浪线标注、TTS 状态机、并发池）。
  - moon-well 认证三通道：JWT Bearer（access 7 天 / refresh 30 天，`/auth/oidc/exchange` 用 Authentik id_token 换取，`/auth/refreshToken` 续期）、`mk-` 静态 API-key（存 user.token，无签发 HTTP 端点）、内网信任头 X-User-*（`INTERNAL_TRUST_ENABLED=true`，仅内网语义，公网入口未定义 moon-well 路由——插件不能依赖信任头）。
  - CORS 全开（`allowedOrigins("*")`）；所有相关端点均为 POST + JSON、`Result{success,result}` 包装；段落缓存 ES 幂等（同段落命中缓存不重复计费）；analyze 的 bookId/bookName/chapter 全部可空（网页场景可直接复用，bookId 缺省为 0）。
- **可行性结论**：**可行，且工程量小**——推荐「插件直连 moon-well + 复用既有 API + 前端逻辑从 epub.js 移植」方案。不需要后端改造（或仅需新增 1 个 API-key 自助签发端点）。核心移植面约 600–800 行 JS；MV3 插件结构天然规避 CORS/CSRF/iframe 三大障碍（epub.js 里的 CSRF 自愈、iframe 坐标换算在插件里全部消失，content script 直插主文档）。
- **主要风险与对策**：① moon-well 无公网 HTTPS 入口（fnOS 8082 仅内网）→ 需在 Traefik 加一条路由（如 `api.haoshenqi.top` → 100.x/192.168.31.9:8082）或仅限内网/Tailscale 环境使用；② JWT 刷新 30 天窗口 → 插件需静默 refreshToken + 过期引导重登；③ TTS 65s 超时对长段/慢网需 loading 态与降级（浏览器 speechSynthesis 兜底，epub.js 已有同款逻辑可移植）；④ MV3 Service Worker 生命周期 → 音频播放/状态机放 content script 或 offscreen document。
- **产出**：评估报告（对话内交付），含架构图、API 映射表、移植清单、分期建议（P0 划词翻译+词标记 → P1 段落翻译+生词标注 → P2 TTS+设置页）。未改任何代码。
- **命名（同日新会话补充）**：复核端点（`ReadingVocabularyController` /vocabulary/reading/{analyze,translate,translate-batch}、`VocabularyController` /known|/unknown/{word}、cps `/tts/speak` 代理）确认 R118 事实仍成立；交付命名建议：首推 **MagicLens（词镜）**——magic- 家族命名 + 透镜隐喻，Chrome 商店无同名翻译插件（仅 MangaLens 漫画 OCR 不冲突）；备选拾词（谐音诗词）、WordWell（呼应 moon-well）；AnyBook、MagicScroll 已有同名占用，不推荐。

### 总结

- **requests.md**：占号 R118。
- **response.md**：本条。
- **冲突记录**：无。

## 2026-10-04（Chrome 插件 AI 伴读聊天移植评估）

### R119（追加 R118：AI 伴读聊天移植到插件的可行性）

- **链路事实**（实读代码确认）：
  - magicbook 侧只是薄皮：`ai_chat.js`（576 行 UI/SSE 消费）+ `ai_page_extract.js`（76 行 epub/pdf/txt 页面文本采集）+ `cps/ai/proxy.py`（180 行透传，SSE 流式转发）。真正智能全在 moon-well：`AgentChatService`（332 行）+ `AgentLoop`（411 行有界循环）+ 7 工具（lookup_word/get_paragraph_translation/list_annotations/add_annotation/save_memory/recall_memory/reflect）+ MySQL 会话/消息/记忆/学情 + SSE 分型事件（delta/tool_call/tool_result/final/error）。
  - 关键宽容性：`AgentChatRequest` 除 message 外全部可空——bookId null=非书场景（落 0）、bookTitle/authors/chapter/pageText/unfamiliarWords 全可选；会话列表 bookId null=全部会话；学情摘要 bookId≤0 直接返回空串；工具结果与记忆注入全部进程内 Service 直调，userId 行级隔离自动生效。**moon-well 对「非 magicbook 前端」零耦合**。
  - system prompt 模板硬编码「英文书伴读助手」「《{{bookTitle}}》的『{{chapter}}』章节」——网页场景语义错位（书名会显示「未知书名」），这是唯一需要 moon-well 侧改动的地方（模板加场景分支或新增 web 场景模板）。
  - SSE 消费端 ai_chat.js 是标准 fetch+ReadableStream 手写 SSE 解析（event:/data: 帧、[DONE]、降级裸文本），零 jQuery 依赖核心，可整体移植；CORS 全开 + SSE 端点 `SseEmitter(0L)` 不设超时，插件 fetch 直连无障碍。
  - 写确认是「非交互式门」：`write-confirm-required=true` 时写工具直接被服务端拒绝并引导模型把内容展示给用户——不是暂停等确认，插件 UI 无需实现确认交互。
- **结论**：**高度可行，比 R118 词汇/翻译部分更顺**——后端零改动即可跑通（网页场景 bookId 传 null，7 个工具里 lookup_word/记忆三件套/reflect 天然可用，get_paragraph_translation 命中段落缓存照样工作，add_annotation/list_annotations 按段落文本定位与书无关）。体验层面的优化（web 场景 system prompt、页面上下文采集策略）是小改。前端移植面 ~1.2k 行（ai_chat.js 去 jQuery 化 + 页面提取器重写为通用 DOM 正文提取 + Shadow DOM 面板）。
- **新增风险**：① SSE 长连接与 MV3 Service Worker 生命周期——fetch 流应在 content script 侧消费（与页面同生命周期），或 offscreen document；不在 background 里挂 300s 流。② 网页正文提取质量参差（spa/懒加载/正文噪声），P0 先做「选中文本+视口段落」双通道。③ token 事件带 usage（计费可见）——插件侧正常展示即可。④ 长对话 memoryExtractOnFinish 会照常运行，网页会话也会被抽取记忆（合理，记忆本就跨书）。⑤ ai.agent.enabled 生产开关需为 true。
- **产出**：评估报告（对话内交付），未改任何代码。

### 总结

- **requests.md**：占号 R119。
- **response.md**：本条。
- **冲突记录**：无。

## 2026-10-04（上传链路 100MB + 新概念课级音频播放）

### R116（①上传限制改 100MB；②封面先不动；③NCE mp3 入 MinIO + 课级音频播放）

- **① 上传链路（已完成，生产验证）**：根因非应用配置——magicbook 无大小上限项，掐断点在 Server 2
  Traefik 静态配置 `transport.respondingTimeouts.readTimeout` 默认 60s，13.5MB 上传在超时窗口内传不完被
  RST（前端 xhr status 0 表现为「File size may be too big」）。修复：`/app/app-manager/docker-compose.yml`
  websecure entryPoint 增 read/write/idleTimeout=15m，重启 Traefik 生效（重启时机经用户确认）。验证：登录 UI
  实传 19.8MB PDF 成功入库（#101），随后经 `/ajax/deletebook` 清理测试书，闭环。
- **② 封面**：用户令「先不动」，未做。
- **③ NCE 课级音频（US1 完成，待部署）**：
  - **素材入库**：GitHub `tangx/New-Concept-English` 276 课美音 mp3+lrc 共 552 文件（~620MiB）按仓库 tree
    blob size 全量校验（首轮 34 个空文件、若干截断，多轮补拉后 fixed=26 failed=0；GitHub 直连劣化时改走
    Ubuntu 192.168.31.11:12811 naive 代理）。逐册生成 `manifest.json`（title 取仓库文件名、duration 取
    ffprobe，四册 72/96/60/48 课）后 `mc mirror` 至 MinIO `magicbook/nce-audio/book{1..4}/`，
    `mc ls --recursive` 核对 556 对象，抽验 mp3 头/时长/lrc 均可读。
  - **实现**（LLD `docs/feat/nce-audio/design/lld.md`，并行会话按 LLD 实装、本会话审查）：新增 `cps/nce/`
    蓝图（series.py 映射 series「新概念英语」+series_index 1–4→册号；store.py MinIO 惰性单例+manifest TTL
    缓存；routes.py 播放页/课表/audio Range 流/lyric 四端点，全 `@user_login_required`+manifest 白名单）；
    `main.py` 仅在 MINIO_* 三键齐备时注册（fail-closed）；`detail.html` NCE 书详情页增「Lesson Audio」入口；
    播放器 `nce_player.html`（原生 audio：播放/上下课/拖动 seek/自动连播/localStorage 记忆位置）。
    `requirements.txt` 增 `minio>=7.2.0,<9.0.0`。
  - **测试**：`tests/test_nce.py` 22 项（映射纯函数、_parse_range、登录 302、非 NCE 404、MinIO 故障 503、
    200/206/416、lyric、课表 JSON），store 全 monkeypatch 不依赖真 MinIO；全量 303 passed。真实 MinIO 直读
    验证：四册 manifest 计数正确、book1/001-002 Range 读 1024B（ID3 头）、lrc 首行正确。
  - **AC 对照**（LLD §9）：1–5 有单测/实测证据；6（公网 Traefik 链路播放）待部署后浏览器实测。
- **部署与生产首验（2026-10-04 晚，经用户确认推送+部署）**：
  - fnOS `.env` 增 `MINIO_ENDPOINT/MINIO_ACCESS_KEY/MINIO_SECRET_KEY`（值从 moon-well `.env` 直拷、未回显；备份 .env.bak-nce-20261004）。
  - 推送 develop 触发 webhook 构建，builder 侧 `git fetch` 三次死于 GitHub TLS 劣化（ai-fix 已登记）；人工修复=构建仓库 `git config http.proxy http://192.168.31.11:12811`（固化），手动重跑 `build-magicbook.sh` → 镜像推送 ACR、deploy SUCCESS、容器自动重建。
  - 生产浏览器实测（公网 HTTPS 链路）：`/nce/93` 播放页 96 课+时长正确；点课即播（时长 78.6s 与 manifest 一致）、`/audio/01` 返回 **206** audio/mpeg、拖动 seek（45s）成功、播到尾部自动连播至第 02 课；`/book/93` 详情页有 Lesson Audio 按钮、`/book/2` 无；匿名 `/nce/93` 302→/login。**AC 1–6 全部通过**（5 以单测+fail-closed 隔离背书，未真停机 MinIO）。
- **未验（诚实边界）**：MinIO 真停机时生产 503（仅单测覆盖）；四册全量 276 课逐课试听（抽检 2 课）。
- **交付状态**：`5f7e24b2` 已推送 develop 并构建上线（`magichouse/magicbook:latest`，容器 healthy）。

### 总结

- **requests.md**：占号 R116（本条），无新号。
- **response.md**：本条；116%10≠0，无归档轮转。
- **冲突记录**：R116 编号与词汇量测试会话（requests.md 双 116 行）并存，按只追加约定共号不同任务；
  nce 实现由并行会话按本会话 LLD 实装，本会话负责下载/入库/审查/测试验证，未重复写码。

## 2026-10-05（epub 整章音频调研——放弃）

### R120（三本《新概念英语85》epub 章节末位整章播放——用户决定放弃）

- **需求**：#102（第三册）/#103（第四册）/#104（第二册）epub 阅读器每章末尾挂整章 mp3。
- **调研结论（阻断性数据事实）**：三本 epub 为外研社 **1985 老版**课文结构，而 nce-audio 美音源自 **1997 修订版**，课序天然不对齐——按编号直接映射第四册仅 4/60 对得上；改按课文标题模糊匹配实测覆盖：二册 93/96（97%）、三册 50/60（83%）、**四册仅 21/60（35%）**。缺口全部是老版特有课文无对应录音，代码无法弥补。
- **决策**：用户选「放弃匹配」，未写实现代码。曾拟方案留档备查：服务端 `/nce/epub/<book_id>/chapters`（读库内 epub 解析 ncx + manifest 标题匹配，返回 {spine href→课号}，进程缓存）+ epub.js rendered 钩子在命中章节末尾注入原生 `<audio controls>`（复用 `/nce/<id>/audio/<num>` 206 流）+ 三本 calibredb 补 series 元数据。若未来取得 85 老版配套音频源（尤其四册 60 课版），方案可直接复用。
- **产出**：三本 epub ncx 标题表与 manifest 匹配率实测脚本（docs/temp，gitignore）。

### 总结

- **requests.md**：占号 R120。
- **response.md**：本条；120%10==0 触发轮转——R102–R110 搬入 `response-archive/response-R102-R110.md`，保留窗口 R111–R120。
- **冲突记录**：无。

## 2026-10-05（划词翻译 6 秒排查）

### R122（/ajax/reading-translate 划词 evidence 耗时 6.13s 归因）

- **现象**：用户读 NCE3 Lesson 1 划词 "evidence"，DevTools Timing：Queueing 0.84ms / Stalled 0.75ms / **Proxy negotiation 0.27ms** / Waiting 6.13s / Download 4.93ms。
- **链路拆解（实测）**：magicbook `/ajax/reading-translate` 是纯代理（`_moonwell_proxy` → `MOON_WELL_READING_URL=http://192.168.31.9:8082` 本机直连）；moon-well `ReadingVocabularyService.translate`：ES 段落缓存查 → 单词走 iciba（3s 超时×2 词形还原）→ miss 才 LLM。
- **moon-well 侧证据（app-log-moon-well，修正 REQ 行时间戳=完成时间）**：
  - 20:31:20.349 到达、**161ms 完成**（source=dictionary：ES 缓存 miss + iciba 命中 + 缓存回写，全部健康）；20:31:53/59、20:33:23 三次重复划词 10/5/13ms（ES 缓存命中）。
  - 反推浏览器发送时刻 ≈ 20:31:14.41 → **~5.94s 丢失在「浏览器发出 → moon-well 入口」之间**，翻译本身无罪。
- **逐一排除（都有证据）**：moon-well 处理慢（同窗口 /llm/task/accept 260-310ms 正常基线，现在也是 ~250ms）；401→refreshToken→重试（HttpLoggingFilter @HIGHEST_PRECEDENCE+10 先于 Spring Security，401 必留痕——早上 08:56 三条 401 可证；20:31 窗口 0 条 401、0 条 /auth 调用）；magicbook 重启（容器 up 自 10-04 15:39）；fnOS 内核/IO 事件（journal 20:29-20:33 干净）；Tailscale 路径劣化/PMTU 黑洞（fnOS↔Server2 有 agent 30s 心跳保温；实测容器内 4KB POST 30ms、宿主机一致）；magicbook 鉴权（本地 session+本机 MySQL，无远程调用）。
- **归因（剩余盲区）**：时间丢在浏览器→Traefik→magicbook→moon-well 入口这段，而这段当前**零观测**（Traefik 无 access log、magicbook 代理层成功请求不打耗时日志、magicbook ES 日志窗口为空）。DevTools 出现 "Proxy negotiation" 行证明浏览器走了本地代理（Clash/Surge 类）——**首选假设：本地代理/家庭网络瞬时抖动**（代理死节点 fallback 超时典型 5-6s，与 6.13s 高度吻合）；次选 Traefik→magicbook（Tailscale）瞬时抖动。事后无法二分定责。
- **建议（未实施，待用户定夺）**：① 本地代理对 `*.haoshenqi.top`/`*.haoyuhang.top` 加 DIRECT 规则再观察；② Traefik 开 access log（一个 flag，拿到每请求后端耗时，补最大盲区）；③ magicbook `_moonwell_proxy` 成功路径记 INFO 耗时（>1s 记 WARN）。
- **交付状态**：纯诊断，未改任何代码。

### 总结

- **requests.md**：占号 R122。
- **response.md**：本条；122%10≠0，无归档轮转。
- **冲突记录**：无。
- **【2026-10-05 补充】R122 根因确认**：用户确认是本地代理问题（与排查结论首选假设一致）。服务端各环节均有证据排除，DevTools "Proxy negotiation" 行是关键指向；建议的 DIRECT 规则仍值得加上以防复发。

## 2026-10-06（R124 阅读器单词详解）

### R124（划词气泡「详」按钮 + 六板块详解面板）

- **回应**：阅读器与 magiclens v0.4.0 同步获得单词详解能力（后端复用已上线的 moon-well R100，magicbook 侧零 LLM/存储改动）：
  - **代理**：`cps/web.py` 增 `POST /ajax/reading-word-detail`（`@user_login_required` + CSRF），校验/归一化与 word_mark 完全同口径（`_READING_WORD_RE`、小写、弯撇号归一、≤64），转发 `GET /vocabulary/detail/{word}`（30s——缓存 miss 时 moon-well 现场生成）。
  - **前端**（epub.js/reader.css/read.html/i18n）：气泡在 🔊/＋/－ 旁挂「详」按钮（仅单个英文单词）；详解面板六板块渲染与 magiclens 同构（lemma 标题、「变体」角标+说明行、不规则金色 chip、空板块隐藏、textContent 组装禁 innerHTML、请求序号防旧响应）。
  - **交互耦合（审查修复）**：P0-1 seq 取号在 closeWordDetailPanel 之前会把自己的响应作废（面板永卡 Loading）→ 先清理后取号；P0-2 主文档 mousedown「点气泡外即收」会把兄弟节点的详解面板连带收走 → 豁免面板内点击；P1-1 气泡 5s 自动隐藏必然杀掉 30s 级生成 → 面板存活期间挂起计时、面板关闭恢复倒计时；P2-1 Esc 捕获层 stopImmediatePropagation（一次 Esc 只关面板这层）。
  - **i18n**：14 个新词条入 i18n_seed.html + zh_Hans_CN po（译文补全）+ pybabel 重编译 .mo，`test_i18n_seed_contract` 五契约全绿。
  - **测试**：新增 5 个 word-detail 测试（登录门禁/非法词 400/归一化转发 GET+30s+禁代理/上游故障 503/阅读器接线契约——含「seq 取号后不得再自增」「非空 innerHTML 禁入」两条防回归断言）；全量 334 通过。
- **总结**：requests.md 占号 R124（撞号更正：本会话初占 123 与并行会话「会话 cookie 持久化」R123 撞号，按纪律不改既有记录、续编 124，重复的 123 条目保留并在 124 中标注）；response.md 本条；冲突记录：编号撞号如上，无需求内容冲突（并行会话改 cps/__init__.py/reverseproxy.py，本任务改 web.py/epub.js 等互不重叠）。未 push——push develop 将触发 fnOS webhook-builder 自动构建部署，待用户确认。

### R124 补记（部署上线）

- **部署链**：push develop（d55a8cd9）→ fnOS webhook-builder 自动构建（11:38:48 推镜像 :latest）→ app-manager deploy SUCCESS → 容器 healthy；`POST /ajax/reading-word-detail` 未登录请求 400（CSRF 门控，对照不存在路由 404 确认路由匹配），登录用户可正常使用。
- **验收提示**：阅读器划词 → 气泡点「详」→ 六板块面板；重点 ran/running 变体还原与二次查询秒回。

### R123 会话 cookie 持久化（修「一天就要重新登录」）

- **根因**（承接 moon-well R101 诊断）：moon-well access/refresh token 存在 magicbook Flask 签名会话 cookie 内，未配 session.permanent → cookie 无 Expires/Max-Age（浏览器会话级），浏览器一关登录态连同 token 全丢。ES 日志佐证：近 30 天 moon-well 服务端 0 次 JWT 过期拦截，而 magicbook 近 16 天中 14 天每天 1–4 次 token exchange（每日重登）。
- **修复**：`PERMANENT_SESSION_LIFETIME` 默认 30 天（`SESSION_PERMANENT_DAYS` 可调）+ `SESSION_REFRESH_EACH_REQUEST=True` 滑动续发 + 全局 before_request 钩子对**非空**会话标记 permanent（空会话不动——permanent setter 写 _permanent 置 modified，会破坏内部 M2M 端点「响应不携带会话 cookie」契约）。与 moon-well JWT access 30 天/refresh 90 天（R101）对齐。
- **顺带修复**：①`ReverseProxied.script_name` 构造期未初始化，session_transaction 等绕过 WSGI 的 save_session 路径会 AttributeError（潜在雷，生产未触发）；②登出 `/logout` 只清 flask-login 身份键不清 moonwell token——持久化后 token 会在 cookie 里滞留 30 天滑动续期，登出改为 `session.clear()`（save_session 对空+modified 会话下发删除头）。
- **审查记录**：独立 agent 交叉审查 1 P1（登出 token 滞留，已随本修复一并修）+ 8 P3（采纳：钩子跳过已标记会话、注释机制描述更正、测试断言相对 config 生效值免受本地 .env 干扰；记录取舍：strong session protection 对 permanent 会话退化为 basic（flask-login 上游刻意设计），个人工具接受；SESSION_COOKIE_SECURE 未加——保留 fnOS 内网 http://192.168.31.9:8083 直连可用性，如确认纯 HTTPS 访问可加）。占号冲突：本会话初占 123 后并行会话「单词详解」也占 123，对方按纪律续编 124（见 requests.md），本任务沿用 123，无文件冲突。
- **测试**：新增 tests/test_session_permanent.py 4 例（config 生效/cookie 带 Expires≈lifetime/钩子注册/登出清空+删除头）；全量 335 通过。已知边界：cw_login remember_token 恢复路径当次请求不标记 permanent，下一请求自愈。
- **部署**：push develop → fnOS webhook-builder 自动构建部署；上线后需重新登录一次（旧 cookie 仍为浏览器会话级），此后浏览器重启不再掉登录。
- **总结**：requests.md 占号 R123（并行撞号已按纪律处置）；response.md 本条 + 收录并行会话 R124 部署补记；冲突记录：编号撞号已注明，无内容冲突。

## 2026-10-06（R125 词汇测试结果页难度推荐 + 一键应用）

### R125（结果页展示推荐难度，一键应用到阅读设置）

- **回应**：词汇量测试完成后，结果页按 moon-well R103 报告新字段 `recommendedHardLevel/Name` 展示推荐并支持一键应用（对应 requests.md R125）：
  - **DOM**：`#vt-result` 内增 `#vt-reco-line`（推荐/确认/失败文案，className 携带 `vt-el` 保 `[hidden]` 兜底）与 `#vt-apply-level` 按钮；按钮 msgid 用 `Apply suggested level`——po 里上游 `"Apply"` 已被误译为「查询」，撞上即回错词。
  - **渲染**（`renderLevelRecommendation`）：旧后端无字段 → 静默不显示（先行部署降级态）；与当前档位一致 → 只显示「当前难度等级与该测试结果一致。」不递按钮；不同 → 「建议难度等级: {name}」+ 按钮。当前档位取 `#hard-level-select`。
  - **应用**：POST `data-level-url`（= 既有 `web.reading_settings_update_hard_level`，**零新代理路由**），复用 `post()` 的 CSRF 头/自愈与 401 判读；成功 `markCurrentLevel` 同步下拉选中值、清各 option `(default)` 后缀、更新 `#rs-current-level` 行、隐藏 `#rs-default-label`，行文案变「难度等级已更新」；失败（网络/业务码）行变红可重试。
  - **交叉审查**（独立 agent）：P1 已修——apply 请求纳入 epoch 作废纪律（发请求捕获 `mine=epoch`；`.then/.catch` 先复位在途锁再判 stale，迟到响应不得写新一轮结果页或吞按钮；stale 但业务成功仍先 `markCurrentLevel` 反映服务端真值）；P2 已修（`(default)` 后缀残留）；P3 采纳 `pendingRecoName` 复位；P3「load_error 态应用成功后设置卡仍显错误横幅」接受不改（浮层内已有确认，功能不受影响）。
  - **i18n**：4 个 mbT 词条入 `i18n_seed.html` + zh_Hans_CN po（补丁脚本 `docs/temp/scripts/vt_r125_i18n_patch_po.py`，width=76 原子口径）+ `pybabel compile` 重编 .mo；`test_i18n_seed_contract` 五契约全绿。
  - **测试**：`test_vocab_test_proxy.py` 增 `test_result_view_renders_level_recommendation_surface`（DOM 面 + `data-level-url` + `rs-current-level` 锚点）并给 `REPORT` fixture 补两字段守透传形状；全量 pytest **336 通过**。
  - **文档**：us4 设计 §4 报告形状补字段 + 新增 §6 R125 增量节；ac 文档新增 G 节 8 条（含端到端待部署后核与交叉审查留痕）。
- **部署**：未 push——push develop 触发 fnOS webhook-builder 自动构建部署，按「提交≠推送」纪律待用户确认；对旧后端已做静默降级，先推前端亦安全。
- **总结**：requests.md 占号 R125（无撞号）；response.md 本条；冲突记录：无。

## 2026-10-07（R125 详解面板粘性）

### R125（面板不因离开/误点关闭 + AI 生成中提示）

- **回应**：详解面板与划词气泡生命周期解耦（epub.js）：
  - 面板仅由 ✕/Esc 关闭；滚动、新选区、翻页、点正文（含 iframe 内）不再误关面板——生成等待期 15~30s 误关一趟就白等。
  - 加载文案改为「AI 正常生成中…（首次查询约 15~30 秒，面板保持打开并自动显示结果）」（i18n seed + zh po/.mo 同步）。
  - 失败态（非鉴权）支持点击重试——后端已缓存结果时重试瞬时命中。
  - 气泡自动隐藏挂起逻辑保留（面板存活期间气泡不消失），面板关闭后气泡恢复倒计时。
  - 契约测试增两条防回归：closeTranslationPopover 不得调用 closeWordDetailPanel；点外关闭监听必须不存在。全量 336 通过。
- **SSE 取舍说明**（用户提议「优先使用 SSE」）：暂缓。详解是单次结构化 JSON 输出，流式到达的半截 JSON 无法优雅增量渲染，逐板块流式需自写增量 JSON 解析器，收益低复杂度高；当前痛点（误关 + 静默等待）已由面板粘性 + 明确提示解决，且 thinking 关闭后生成仅 15~30s。若之后想「逐板块流式呈现」再立项 SSE 版（moon-well 流式接口 + 两端增量解析）。
- **总结**：requests.md 占号 R125；response.md 本条；冲突记录：无。

### R126（LLM 任务手动执行面板，对齐 moon-well R110 US3）

- **交付**：`cps/web.py` 5 视图 + `_llm_task_admin_gate()`；`cps/templates/llm_tasks.html`（provider/model/caller/并发/上限/重放 + 开始·刷新·停止 + 4s 轮询进度）；`layout.html` admin 下拉新增 `top_llm_tasks`；42 条英文 msgid 进 `zh_Hans_CN` po 并**重编译 .mo**（重编译前先验证「当前 po 重编译产物与仓库内 .mo 逐字节一致」，确保 diff 只含新增）；`tests/test_llm_task_run_r126.py` 28 条。全量 `pytest tests/` → **364 passed**。
- **薄代理边界**：请求体原样透传（不做 snake_case 映射层，否则两侧契约漂移无人发现），队列语义/夹取/退避/重放全在 moon-well；**不**把 `/llm/task/run*` 加进内网互信白名单——手跑真实消耗模型配额，必须带管理员本人 token 才能归因与拒绝。
- **交叉审查抓到 3 条必须修**（都已在真浏览器夹具里实测修复）：① `loadOptions()` 每次覆盖并发/上限输入，而 `maxTasksPerRun` 默认 5000 ⇒ 管理员填 100、切一次供应商就变 5000，点开始就是一批 5000 次真实调用（改为 `touched` 脏标记 + 默认 `min(100,上限)`）；② 切 provider 不清模型名 ⇒ A 网关的模型名提交到 B 网关，整批 FAILED 且配额已耗（change 里清空）；③ 无视 options 的 `enabled`/`admin` ⇒ 面板看着可用、点什么都失败（Start 初始禁用，options 成功且白名单命中才解禁；未配置供应商 `<option disabled>`）。
- **建议修一并处理**：JSON 端点从 `abort(403)`（HTML）改为 handler 内 JSON 403（对齐 `/ajax/credit/admin-adjust`），并加「门禁先于转发」断言；回显服务端实际夹取值（填 9 → 提示并发 4）；`renderProgress`/`watch` 异常接入 reject 分支；`currentRun` 在 run 结束时清零 + `optionsSeq` 丢弃过期回包（实测 10s 内 status 恰好 3 次，无叠加轮询）；404 专门提示「moon-well 需发新版」。
- **新增跨仓库契约测试**（2 条）：面板提交的键与 moon-well `LlmTaskRunReqDTO` 字段名互锁、前端读取字段必须存在于三个响应 DTO。首跑就因正则不容嵌套泛型误报 `modelCandidates`，修正后确认两侧字段名对齐。
- **浏览器夹具的一课**：第一版把打桩 `<script>` 插进了面板脚本的 `<script>` **内部**，浏览器当脚本文本处理、面板逻辑一行没跑，而 `providerOptions=[]` 看起来像「没数据」而不是「脚本没执行」——判据是桩里定义的 `window.__calls` 变成 undefined。插在开标签之前才对。夹具与临时用例已删（`docs/temp` 本就 gitignored）。
- **待线上验收**（AC A14–A18）：moon-well 发版 + Nacos 加 `ai.llm.task-manual-run` 块后，用小上限（`maxTasks=20`、并发 2）跑一批，确认进度、停止、与自动模式互斥的文案。白名单口径已用生产数据预核：`app_user` 中 `user_id=1` = `hsq`（余额 1,007,760），`admin-user-ids` 配 `[1]`；OIDC 换票是否把本管理员落到 id=1 仍需线上点一次确认。
- **台账**：`requests.md` 追加 R126（前一条 125 有并行会话重复编号，未回改）；`docs/feat/llm-task-run/design/admin-panel.md` + `ac/admin-panel-ac.md`；本文件。
