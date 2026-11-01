# LLD — R261 Jinshu 借鉴三件套（阅读器行内 gloss / Book Fit 话术 / 复习小件）

> 状态：已开发待验收（2026-11-01）
> 对应需求：PingCode [MB-238](https://haoshenqi.pingcode.com/ship/products/MAGICBOOK/)；moon-well 侧编号 R236（gloss 数据源 / repeatedUnknownCount / learning_plan_settings 两列），两仓 LLD 互链
> 背景：竞品 Jinshu（built4.fun 分级 EPUB 阅读器）调研结论三项落地、两项不做（纠错上报=AI 伴读覆盖、墨水屏=无场景，决策记入 requirements 基线）。

## 1. A：阅读器行内小字释义（Word Wise 式，可选功能默认关）

数据链：moon-well R236 analyze 响应新增 `gloss`（词典文档缓存批量首义项）→ magicbook 纯透传 → 前端渲染。

- **开关**：`read.html` 设置弹窗新增 checkbox「Show short gloss above vocabulary words」，localStorage `calibre.reader.vocabGloss`（默认关；与 showPagesCount/沉浸式翻译同款本机偏好范式，不走服务端）。切换时调 `window.ReaderVocabGloss.remark()`。
- **挂属性**：`epub.js` `markVocabulary()` 在包 `span.reading-vocabulary-unknown` 时，`vocabGlossEnabled() && record.gloss` 双守卫通过才挂 `span.dataset.gloss`；词典无文档（record.gloss 缺失）自然降级为仅波浪线。翻回已读页经 `vocabularyRecords` 缓存重标，行为一致。
- **渲染**：`reader-core.js` READER_TOOLS_STYLE（每次 `rendered` 注入 iframe——reader.css 够不到 iframe 文档）新增两条规则：`[data-gloss]{position:relative}` + `::after{content:attr(data-gloss); position:absolute; bottom:calc(100%+1px); font-size:10px; ...}`。**Why 绝对定位不占文档流**：占流会把分栏分页整体重排、翻页时全文抖动；浮在词头不推挤正文。
- **切换重标**：`epub.js` 暴露 `window.ReaderVocabGloss = { enabled, remark }` 桥（生词台账 `vocabularyRecords` 留在 IIFE 内）；`remark` 遍历当前 iframe 已有 span，按开关增删 `data-gloss`，**不发新请求**（数据已在缓存）。
- **边界**：①逐页标注的既有重排特性被 gloss 放大（行高增量），可选功能默认关即取舍答案；②多义词取词典首义项不做语境消歧（与 SRS 题干同源同风险）；③MagicLens 接管高亮（`lensOwnsHighlight`）时整条内置标注链照旧让位，gloss 随之停用；④魔改主题若强制 text-transform/italic，样式已显式归一。

## 2. B：选书页 Book Fit 话术（数据接 moon-well R236 `repeatedUnknownCount`）

- `learning-match.js`：每本书卡新增「~N repeated above-level words to learn」行（zh：`~N 个重复出现的超纲词`），`item.repeatedUnknownCount != null` 才渲染——存量画像未重算时整行隐藏，不显示误导性 0。
- 生词样例展示条件从仅 `HARD` 放宽到 `FIT || HARD`（正合适区的书同样值得预览要面对的词）。
- 三档徽章（Easy read / Just right / Challenging）与密度行保留，口径不动。

## 3. C：复习小件（学习模块，可选默认关）

设置存储：moon-well R236 `learning_plan_settings.review_source_chip` / `hub_due_badge`（null 不落库、出厂关）。

- **管理抽屉**：`learning.html` 抽屉新增「复习小件」组两 checkbox（与 R208 轮播勾选语义分开）；`learning-hub.js` 打开抽屉时按 plan/today 带回的 settings 回填（null 按镜像），保存显式携带两布尔（全量替换接口，老前端不带字段不受影响——后端 null 不落库），并写 localStorage 镜像。
- **复习卡来源书 chip**：`learning_review.html` 卡顶新增 `#ln-source-chip`；`learning-review.js` `renderSourceChip()` 读镜像键 `ln-review-source-chip-v1` 判开关，`item.contextBook` 有值才显示「最近遇见于《书名》」；**只亮书名**——章节/原句继续走 post-reveal 原门控（原句含目标词=泄题），书名的轻微提示性由用户显式开启承担。无遇见记录（测试/手动入池词）contextBook=null 不显示。
- **学习入口待复习角标**：`layout.html` 顶栏 `#top_learning` 与移动底栏学习项各加 `span.ln-due-badge`；内联脚本镜像键 `ln-hub-due-badge-v1` **判关零请求**，开启才 fetch `/ajax/learning/srs/stats` 取 `dueNow`（sessionStorage 5 分钟缓存），`99+` 封顶；暴露 `window.MBDueBadge.refresh()` 供学习抽屉保存后即时重渲（顺带清缓存）。跨设备镜像滞后为装饰性提示可接受（R208 同款权衡）。
- **样式**：`magicbook.css` 追加 `.ln-due-badge` 与底栏绝对定位（`.mb-bottom-item` 补 `position:relative`）。

## 4. i18n 与测试

- 五步链全走：JS mbT 2 条（`Recently met in` / `repeated above-level words to learn`）+ 模板 `_()` 4 条，`generate_i18n_seed.py` 重跑（种子+2、清单 26 文件）、pybabel extract/update、zh po 补 6 条 msgstr、**只编 zh** mo（R223 教训）。
- 新增 `tests/test_r261_jinshu_borrow.py` 8 条静态锁：开关默认无勾选、gloss 双守卫、attr 渲染不占流、重复词数行 null 容错、chip 只亮书名（不得拼 contextChapter/contextSentence）、badge 镜像判关+缓存+refresh 钩子、抽屉两开关存在、hub 保存携带两开关并落镜像。
- 开发态闸门：`test_r261_jinshu_borrow(8) + i18n_seed_contract + learning_banner_manage + learning_hub_cards + learning_pages_static + learning_proxy + reader_module_surface + reader_r215_ui + reading_vocabulary + reader_lens_handoff + learning_story` 全绿（160+62+8）；改动 JS 全部 `node --check` 通过。未跑全量（push develop 上线时按用户指令另跑）。
