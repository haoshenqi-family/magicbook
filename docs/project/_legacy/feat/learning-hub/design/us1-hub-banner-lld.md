# 每日学习中枢化 + 功能 banner（R166）· L3 设计

> **L2 状态**（DF6/R186）：`learning` 模块尚无 `docs/learning/hld/hld.md`（**待升 L2**），本页端点与七个子功能的契约以 L3 为准。

**状态**：已上线（2026-10-13 21:20，develop `771923c4`，fnOS `build END OK`）；
真数据下的四股入账与七个子页面练习流程待用户浏览器验收。

## 1. 背景与目标

「说与写」（R152/R153/R155~R160）与「每日学习」（R132/R137/R144/R147/R150/R151/R153）
此前是**两个平行页面**：`/learning` 内嵌复习队列与选书匹配两个面板，
`/learning/speaking-writing` 用五个 tab 装写作/口语/复述/重读/听写。用户视角的后果是
「今天该练什么」没有单一入口，五个输出训练藏在 tab 里、与复习并列不成体系。

本轮目标：把 `/learning` 变成**唯一中枢**，七个学习功能以 banner 卡片（插画 + 标题 + 详细描述
+ 今日进度）循环露出，练习在各自子页面进行。

**能力边界不变**：七个功能的后端契约（moon-well learning 模块）与 `/ajax/learning/*` 代理
零改动，本轮纯前端信息架构 + 呈现层重构。

## 2. 决策（用户 2026-10-13 拍板）

| 岔路口 | 选定 | 放弃项与代价 |
| --- | --- | --- |
| 子页面化范围 | 全 7 项子页面化，中枢留**复习摘要卡** | 放弃「中枢仍内嵌复习队列」——每天复习多一次点击 |
| banner 形态 | 单卡整幅轮播（图左文右） | 放弃卡片轨道（一屏露 2–3 张）与静态网格 |
| 一级导航 | 撤掉 Speaking & Writing 一级项，旧 URL 302 回中枢 | R154 刚把它提为一级项，本轮按新 IA 收回 |
| 前端脚本 | 拆 7 个功能模块 + common + voice | 放弃「守卫式复用旧大文件」——工期与回归面换取每页只载自己那份 |

## 3. 信息架构

### 3.1 路由（`cps/web.py`）

| 路由 | 端点 | 模板 | 说明 |
| --- | --- | --- | --- |
| `/learning` | `learning_page` | `learning.html` | 中枢：banner + 今日计划 + 复习摘要 + 本周四股 |
| `/learning/review` | `learning_review_page` | `learning_review.html` | 复习队列（三题型状态机） |
| `/learning/match` | `learning_match_page` | `learning_match.html` | 选书难度匹配（选架→估算→推荐 + 轮询） |
| `/learning/writing` | `learning_writing_page` | `learning_writing.html` | 写作工坊 |
| `/learning/speaking` | `learning_speaking_page` | `learning_speaking.html` | AI 口语陪练 |
| `/learning/retell` | `learning_retell_page` | `learning_retell.html` | 复述训练 4-3-2 |
| `/learning/reread` | `learning_reread_page` | `learning_reread.html` | 计时重读 |
| `/learning/dictation` | `learning_dictation_page` | `learning_dictation.html` | 听写 |
| `/learning/speaking-writing` | `speaking_writing_page` | — | 302 → `/learning`（书签/R152 期文档链接不失效） |

元素 id **原样保留**（`ln-*` / `sw-w-*` / `sw-s-*` / `sw-r-*` / `sw-rr-*` / `sw-d-*`），
只把 CSRF 隐藏域统一成 `lh-csrf`（common 单一读取点）。Why 不换前缀：id 是 R158 静态锁的
比对对象，改名等于把七份面板的绑定关系全部重验一遍，收益为零。

### 3.2 前端模块（`cps/static/js/`）

| 文件 | 职责 | 加载页 |
| --- | --- | --- |
| `learning-common.js` | mbT/byId/show/csrf/httpJson/get/post/resultOf/busy/clear/li/esc、`STRANDS` 四股字段口径表、`loadMaterials`/`paragraphLine` | 全部 8 页（**必须最先**） |
| `learning-voice.js` | WebAudio 采集→16k wav→`/ajax/learning/asr/transcribe`、设备下拉、按钮态机；对外只暴露 `MBLearningVoice.attach()` | 口语、复述 |
| `learning-hub.js` | 轮播 + 徽章 + 缺口排序 + 计划行 + 摘要卡 + 周视图 | 中枢 |
| `learning-review.js` / `-match.js` / `-writing.js` / `-speaking.js` / `-retell.js` / `-reread.js` / `-dictation.js` | 各子页面状态机 | 对应子页面 |

删除：`learning.js`（579 行）、`speaking_writing.js`（1097 行）。

**每页注入 `window.learningUrls`，只列本页端点**；模块内一律
`var urls = window.learningUrls || {}` 自行声明。Why 强调「自行声明」：见 §6.1。

### 3.3 样式

子页面共用 `cps/templates/learning_sub_css.html`（`.ln-*` + `.sw-*` 规则合集，由 7 份子页面
`{% include %}`）；中枢 banner 样式随 `learning.html`。纪律不变：布局补丁只管间距与字号，
颜色来自 bootstrap/主题类；唯一硬编码是轮播圆点强调色 `#5b9bd5`，与四股主色同源。

⚠️ 已知上游干扰：`style.css:134` 的 `.container-fluid img{max-height:100%;height:auto}` 与本
文件同特异度，而 `layout.html` 把 `header` 块放在该 link **之前**（18 行 vs 19 行），后来居上
——**卡片图只能靠宽度收**（媒体盒定宽 + img `width:100%`），写 `max-height` 无效（实测计算值
恒为 100%）。

## 4. banner 规格

- 结构：`#lh-banner > .lh-banner-viewport > a.lh-card[data-key][data-strand]`，卡片是
  `<a href=子页面>`——**无 JS 也能点进子页面**，轮播只做显隐与顺序。
- 卡内：`img`（`/static/img/learning/<key>.webp`）+ `.lh-card-title` + `.lh-card-desc`
  （2–3 句，讲清「是什么/怎么玩/计入哪股」）+ `.lh-card-meta`（股别与时长）+
  `.lh-card-badge`（今日进度，缺数隐藏）+ `.lh-card-cta`。
- 节奏：`AUTO_MS=6000`；`mouseenter/focusin` 暂停、`mouseleave/focusout` 恢复；
  `document.visibilityState==='hidden'` 跳过当拍；`prefers-reduced-motion: reduce` 直接不建
  定时器；圆点（`role=tab`，aria-label 取卡片标题）、左右箭头、容器 `tabindex=0` + ←/→ 键、
  触摸横滑阈值 40px。`restart()` 只重排定时器**不动 paused**（悬停中手动翻页不该偷偷恢复自动播）。
- 徽章取数：`data-strand` → `MBLearning.STRANDS[key].{budget,earned}`（/plan）；
  `data-key=review` 特例走 stats（`{{done}}/{{target}} reviewed · {{n}} due`）；
  `data-strand=none`（选书）不出徽章。
- 缺口排序：首份 /plan 到手后按 `budget-earned` 降序重排 DOM（带原索引次键保证稳定），
  只排一次（`ordered` 闩），之后用户手动翻页不再被打断；缺数按 0 处理——宁可不提前，也不把
  没数据的卡顶到第一位。

## 5. 图片资产

`cps/static/img/learning/{writing,speaking,retell,reread,dictation,review,match}.webp`，
7 张合计 52KB（640×436，cwebp q72）。统一风格：扁平插画、dusty blue/warm sand/coral 柔色、
4:3、**画面内不放文字**（避免中英渲染错乱）。生成脚本与压缩参数见
`docs/temp/scripts/`（不跟踪）；ImageGen 产物右下角「Qoder AI 生成」水印位于画面下方空白带，
按 `cwebp -crop 0 0 1024 698` 裁掉底部 70px 去除，未触碰画面内容。

## 6. 顺带修掉的三个既有缺陷

### 6.1 今日计划与四股周视图自 R153 起静默不渲染（本轮排查发现）

`learning.js:167` 引用了从未声明的 `urls.week`（该文件只有 `window.learningUrls`），严格模式下
`loadWeek()` 同步抛 `ReferenceError`；调用链是 `renderPlan → loadWeek`，而 `renderPlan` 挂在
计划请求的 `.then` 里，异常被 `loadAll` 的 `.catch(function(){/* 计划头失败不挡队列 */})` 吞掉
——**页面照常 200、单测照常绿**，今日计划行与周视图两块面板永远隐藏。
引入于 `76691314`（R153）。本轮拆分后每模块显式声明 `urls`，并加静态锁
`test_page_declares_its_url_snapshot`（见 §7）。真机验证：中枢在假上游下渲染出计划行与 7 行周
视图（§8）。

### 6.2 麦克风按钮录完后标签跳英文

`speaking_writing.js` 复位用硬编码 `MIC_IDLE_LABEL = 'Voice input'`，中文用户录一次后按钮文案
从中文变英文。`learning-voice.js` 改为 attach 时读取按钮当前文案作为 idle 标签。

### 6.3 计时重读「推荐段落」入口可能留下死面板

原实现选推荐段落后不重置 `sw-rr-start/stop` 的 hidden：三遍读完（start 已隐藏）再选推荐段落，
面板显示但无「Begin round」按钮。现与手选段落走同一条 `armPanel()` 复位路径。

## 7. 测试

| 文件 | 变更 |
| --- | --- |
| `tests/test_learning_pages_static.py` | **新增**（替 `test_speaking_writing_static.py`，后者删除）。R158 两条锁按「模块 ↔ 它自己的模板」逐页参数化（引用必已注册 / 注册必在模板），新增 `test_page_declares_its_url_snapshot`（§6.1 的回归锁）、`test_page_loads_common_before_its_module`（装配顺序）、`test_no_page_references_the_deleted_scripts`（死脚本引用防回流） |
| `tests/test_learning_hub_cards.py` | **新增**。七张卡的标题/配图/描述长度/股别/顺序、卡片 href 与 `url_for` 一致且可 200 打开、图文件存在且 <200KB、轮播控件齐备、中枢不再留旧面板 DOM、旧 URL 302、`test_banner_copy_is_translated`（判据下沉到编译产物 `.mo`，逐条取词，回吐原 msgid 即红） |
| `tests/test_i18n_seed_contract.py` | `JS_FILES` 换成 10 个新模块（learning.js/speaking_writing.js 出列） |
| `tests/test_nav_settings_dropdown.py` | 一级项断言改为「`top_learning` 恰一次 + `top_speaking_writing` 不回流」 |
| `tests/test_learning_proxy.py` | 中枢/子页面渲染断言按新 IA 重写；旧页断言改 302；麦克风断言拆到口语页与复述页 |

开发态闸门（本轮实跑，非全量）：`test_learning_pages_static` + `test_learning_hub_cards` +
`test_i18n_seed_contract` + `test_no_duplicate_js_lines` + `test_nav_settings_dropdown` +
`test_learning_proxy` + `test_smoke` + `test_integration` + `test_achievements` +
`test_reading_settings` → **全绿**（134 例）。

## 8. 验收记录

本机无 calibre 书库、无合法 moon-well 令牌，故用 `docs/temp/run_learning_hub_check.py`
（不跟踪）起真实 Flask：`?probe=1` 注入几何探针供 `chrome --headless=new --dump-dom` 读取，
`?stub=1` 把 `_moonwell_proxy` 换成固定 Result 信封。内置浏览器在本环境 `innerWidth` 恒为 0，
几何与截图一律走本机无头 Chrome（本仓既有结论）。

- 中枢（假上游数据）：计划行「四股时间预算（每天 40 分钟）：阅读输入 6/20min · 词汇学习
  2/10min · 说与写 0/5min · 流利度训练 5/5min」、今日新词、摘要卡 3/20·14·212·91%、
  「现在有 9 个词到期。」、周视图 7 行 + 图例，全部渲染 ✓（§6.1 修复的直接证据）
- 缺口排序：language(8) > output(5) > fluency(0) > none → 首屏卡片为听写 ✓
- 徽章：`dictation=今日 2/10 分钟`、`review=今日已复习 3/20 · 到期 9`、`match=(hidden)` ✓
- 轮播：6s 自动推进（13s 时停在第 3 张）、圆点高亮跟随、←/→ 与箭头可切换 ✓
- 几何：1440/768/500 三档 `scrollW ≤ innerWidth`（无横向溢出），500px 档媒体盒 220×150、
  卡片纵向堆叠 ✓
- 七个子页面 + 静态资源（common/hub/voice JS、webp 图）HTTP 200 ✓
- 旧 `/learning/speaking-writing`：pytest 断言 302 → `/learning` ✓

**未验（需用户线上真数据验收）**：真实 moon-well 下的四股入账是否如假数据所示折算正确；
七个子页面的实际练习流程（出题/批改/会话/朗读/听写词级 diff）在真账号下的表现；深色主题与
caliBlur 下的 banner 观感；扩展 MagicLens 与本页无交互、不受影响。

## 9. 三级联动

- L1：`docs/readme/learning.md` 按新 IA 重写（中枢 + 七卡 + 各子页面），
  `docs/readme/readme.md` 模块表 learning 行同步。
- L2：本轮无接口契约变化（`/ajax/learning/*` 与上游 moon-well 契约不动），不新建 HLD。
- 后端：moon-well 零改动。
