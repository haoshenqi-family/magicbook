# HLD — R214 书籍详情：简介/目录/难度/试读 + 整本任务代价面板 + 元数据修正

> 状态：**定稿（2026-10-23 用户复核通过）**；拍板⑦（2026-10-23）：AI 简介**不提供「重新生成」按钮**，已生成即定稿
> 迭代：1.0 · PJM 工作项 [MB-13](https://haoshenqi.pingcode.com/pjm/workitems/Ablr7c9a)（用户故事）· Ship 需求 MAGICBOOK-221
> 来源：首访体验 QA 报告 §四（`docs/project/qa/2026-10-23/2026-10-23-qa-report.md`，截图 `a2-book-detail.png`）
> 需求基线：[`docs/product/library/requirements.md`](../../../../product/library/requirements.md) §2 R214
> 关联：R211（已上线，暴露了本条 §2-④ 的阅读入口问题）· R213（难度阶解析器共用）· moon-well R207（费率回传，待占号）

## 1. 目标与范围

一条 M+ 量级的详情页改版，拆成三个可独立验收的子项：

| 子项 | 内容 | 量级 | 外部依赖 |
| --- | --- | --- | --- |
| **A 基础信息与元数据修正** | pubdate 不伪造、语言按书目声明、难度分级标签、「已在书架」视觉；**顺带解禁阅读入口** | S | 无（存量语言补正是运维动作） |
| **B 内容速览** | 简介三级回退（comments → AI 生成并标注 → 暂无）、EPUB 目录树、首章试读 | M | 无（复用本仓 AI 通道） |
| **C 整本任务统一入口 + 代价面板** | 三个整本按钮合并为「整本任务」+ 代价卡（量 / 耗时 / 积分 / 是否改原文件 / 缓存命中）+ 二次确认 + 进行中状态 | L | moon-well R207 费率回传 |

依赖顺序 **A → B → C**：A 的第一笔提交要先把「在线阅读」从 admin 门禁里救出来（§3.5），否则 B/C 都做在了一个普通读者根本进不来的页面上。

## 2. 现状诊断（代码事实，2026-10-23 核查）

| # | 事实 | 证据 | 影响 |
| --- | --- | --- | --- |
| ① | 详情页**已有**简介渲染，只是要求 `comments[0].text` 非空 | `cps/templates/detail.html:305` | QA 的「没有简介」是数据缺，不是功能缺 → 要回退方案而不是新写一段模板 |
| ② | 出版日期直接输出 `entry.pubdate` | `detail.html:228`；`cps/epub.py:91-92,104-105`；`cps/db.py:413` | Calibre 在 OPF 无 `dc:date` 时用导入时间填 pubdate → 显示的是「入库日」被当成「出版日」 |
| ③ | **语言只取第一条 `dc:language`** | `cps/epub.py:84-94`（`tmp[0]`）+ `:114` 单值 `.split('-')` | 声明了 `eng + chi` 的双语 EPUB 导入后只剩 `eng` → 正是「双语书单标英语」的机制性原因 |
| ④ | **一个 `role_admin()` 条件包住四个按钮** | `detail.html:80` 开条件，内含整本翻译(:82)、整本朗读(:85)、全文单词详解(:92)、**在线阅读(:95-116)**，`:117` 关闭 | R211 修完后新账号不是管理员 ⇒ 普通读者详情页**没有阅读入口**。这是本条最急的一处 |
| ⑤ | QA 说的「加入书架面板默认展开」 | 截图那个白框是 `#remove-from-shelves`（`detail.html:341-358`）的「移除」芯片，与「加入书架」同款 `btn` | 不是展开逻辑 bug，是「已加入」与「加入」两个控件视觉不可分 |
| ⑥ | 三个整本入口只有 `confirm` + 提交后 `alert` | `detail.html:397-434` | 无量化信息；只有「全文单词详解」是两步式页面（`word_detail_batch.html`，可当范式） |
| ⑦ | 三个整本链路都不写回原文件 | 翻译写 `TranslationJobItem` + moon-well 段落缓存，朗读写 MinIO 音频，详解写详解缓存 | 「会不会覆盖我的文件」可以用事实回答「不会」，不必靠话术安抚 |
| ⑧ | 朗读缓存命中不可批量查 | 只有逐条 `/ajax/reading-tts-cached`（`cps/routes/reading.py:94`） | 代价面板的「缓存命中」对朗读只能是**上限口径**（§3.4） |
| ⑨ | 积分费率不在本仓 | moon-well `CreditBillingProperties`（`creditsPer1kToken=10`、`tts.charsPerCredit=1000`、`perCall` 白名单） | 要显示积分必须跨仓拿费率，见 §4 |

## 3. 方案

### 3.1 `book_insight`：一次解析，三处消费

新建 `cps/reading_insight/`（`builder.py` + `service.py` + `models.py`），每本书每个格式只解析一次，落 app.db：

```
book_insight(
  id, book_id, book_format, fingerprint,     -- 唯一键 (book_id, book_format)
  payload_json,                              -- 见下
  built_at, last_error
)
payload = {
  chapters: [{title, level, paragraphCount}],-- 目录
  paragraphCount, charCount, englishWordCount,
  declaredLanguages: ["eng","chi"],          -- 来自 OPF，全部声明
  excerptParagraphs: [{chapter, text}],      -- 首章前 ≤1200 字
  aiSummary: {text, model, generatedAt} | null,
  schemaVersion
}
```

- **失效**：`fingerprint` 复用 `JobServiceBase._fingerprint`（大小 + mtime 摘要），重新导入自动重建；`schemaVersion` 变更整表按需重建。
- **不碰 job 内核**：目录/摘录由本模块独立解析 `nav.xhtml` / `toc.ncx`，**不**改 `reading_translation/parser.py` 与 `reading_tts/extractor.py`（R214 明说「不改 job 内核」）。代价：正文解析逻辑出现第三份副本 —— 记为技术债，另立一条收口（建议下一迭代，别塞进本条）。
- **成本控制**：只解析 `epub`/`kepub`；`>8MB` 的书跳过摘录只出目录与统计（避免详情页被单本大书拖到秒级）。
- **构建时机**：详情页请求内同步构建（实测目标 <300ms/本）；失败只降级对应区块（`last_error` 落库），不阻断页面。

### 3.2 元数据修正

**pubdate（不伪造）**：`pubdate` 与 `timestamp`（入藏时间，`db.py:412`）相差 ≤ 1 天视为「未标注出版日」，页面改显示 `导入于 YYYY-MM-DD`，并保留 tooltip 说明判定依据；否则照常显示 `出版于`。判定放 `show_book`（`cps/web.py:2441`）注入 `entry.pubdate_is_import_date`，模板只负责呈现——**判定不进模板**，便于单测。

**语言（按书目自身声明）**：
1. 页面**不猜**：只显示书目声明的语言集合（现状即如此）。
2. 导入侧修声明读全：`cps/epub.py:84-94` 把 `language` 改为收集全部 `dc:language`，逐个 `isoLanguages.get_lang3`，去重后传给 `import_book(languages=[...])`（`cps/db.py:432` 已支持列表）。
3. 存量补正：`scripts/backfill_languages.py`（dry-run 默认）——遍历书库 EPUB，读全部 `dc:language`，与 `books_languages_link` 对账，输出「将变更清单」；`--apply` 才写库（走 Calibre 的 `set_metadata` 同款语义）。**书虫 137 册是否真在 OPF 里声明了 `chi`，由 dry-run 清单给答案**——若声明本就只有 `eng`，则本条不负责替它编造，属元数据维护（管理员手改 languages），页面仍不猜。
4. 声明 ≥2 种语言时，语言行加「双语」徽标（纯展示，`detail.html:183-189`）。

**难度分级标签**：与 R213 共用同一个解析器 `cps/reading_insight/difficulty.py`，来源按优先级四级兜底——① 标签 `阶N` ② 书架名 `阶N`（R213 已拍板的唯一来源）③ 系列名映射（`书虫·第N级` → 阶，口径见 R162 讨论记录）④ `未分级`。扩展 ①②③ 是对 R213 拍板项「按书架名解析」的**扩源**而非推翻（R213 条目追加「已被 R214 扩源」注记，不删原结论）。

**「已在书架」视觉**：`#remove-from-shelves` 从 `btn btn-default` 改为标签式 chip（`label label-default` + 移除 ✕），与「加入书架」按钮区分层级；`取消/编辑元数据` 那一排随 §3.5 一起收敛为「管理员工具区」。

### 3.3 内容速览

**简介三级回退**（不伪造，与 pubdate 同一条原则）：

| 优先级 | 来源 | 展示 |
| --- | --- | --- |
| 1 | `entry.comments[0].text`（书目自带） | 原文，无标注 |
| 2 | `book_insight.ai_summary` | 摘要正文 + 明确标注「由 AI 生成 · `<model>` · `<generatedAt>`」 |
| 3 | 都没有 | 「暂无简介」+ 提示可看目录与试读（**不自动生成**） |

AI 生成**不能走本仓**：`cps/ai/routes.py` 的对话/能力接口已整体退役（`/ai/chat`、`/ai/test_provider` 等一律 410，注释写明「provider 管理随 agent 后端化退役，moon-well LlmGateway 承接」）。也不能直接复用 moon-well 现成的 `POST /book/ai/ability/summarize`：它的入参是 **moon-well 自己的 `bookId`**（`AiAbilityDTO`），与 Calibre 书号是两套序列，错位时摘要的是另一本书——这正是 R197/R200 用「bookName + author」替换 bookId 的原因。

因此：moon-well 新增**按正文入参**的一次性摘要端点（走 `BookAiController` 的 ability 形态，与 `summarize` 并列但**不吃 bookId**），入参＝书名/作者/系列/难度/目录/首章摘录，出参 `{text, model}`，输出 120–200 字中文简介。magicbook 侧薄代理后落 `book_insight.ai_summary`。
触发方式：管理员在详情页点「生成简介」（**不自动跑**，避免每次访问都花钱）；已生成的对所有读者可见。**不提供「重新生成」按钮**（拍板⑦：已生成即定稿，改写/重生成属未来需求另立）。生成失败必须在区块内可见错误原文（禁止静默降级成「暂无简介」）。跨仓编号见 §4。

**目录**：`nav.xhtml`（EPUB3）优先，`toc.ncx`（EPUB2）兜底，取不到则退化为「按 spine 文件的章标题」；每章显示段数，默认显示前 8 章 + 「展开全部」。**不做跳章**（阅读器当前无 hash/CFI 入口，硬做等于新开一条定位链路），点击章节＝展开该章在文中的首段摘录（数据已在 insight 里，零额外成本）。

**首章试读**：首章前 ≤1200 字，淡出遮罩 +「继续阅读」打开阅读器。与「在线阅读」的区别是**不离开页面先看一眼文风**。

### 3.4 整本任务：统一入口 + 代价面板

**可见性（拍板①）**：仍 `role_admin()` only。面板与三个入口同门禁；**普通读者只看到「在线阅读」**（§3.5）。

**形态**：详情页一排放「在线阅读」为主按钮、「整本任务」为次按钮；点击开一个模态，三个 Tab（整本翻译 / 整本朗读 / 全文单词详解），每个 Tab 一张同构代价卡。

字段与可算性（拍板②③）：

| 行 | 数据来源 | 文案口径 |
| --- | --- | --- |
| 章数 / 段数 / 字符数 / 英文词数 | `book_insight` 本地解析 | 准数，直接给 |
| 是否修改原文件 | 事实（§2-⑦） | 「不修改原文件，结果存缓存」 |
| 覆盖率（已做/总数） | 翻译：`find-translations` 批量查；朗读：**算不了**（拍板③） | 朗读写「按全 miss 上限估算，已缓存段落自动跳过不重复计费」 |
| 预估耗时 | 同类历史批次中位数（翻译/朗读 job 台账 `created_at/updated_at + done_count`），样本 <3 回落常量（翻译 ≈10s/段，依据 R78 注释；朗读 ≈0.8s 间隔 + 合成延迟） | 「约 X 小时 Y 分 · 基于最近 N 个批次实测」，样本不足时明写「按常量估算」 |
| 预估积分 | 量 × moon-well 回传费率（§4） | 「约 N 积分（粗算，非账单）」 |
| 操作按钮 | — | 「开始」前必须二次确认；确认文案复用现有风险说明并补上上面三行数字 |

**进行中状态**：页面加载时按 `_find_active_job`（`reading_job/service_base.py:100`）查三类活跃批次，有则把「整本任务」按钮改为进度条（done/total + 上次更新时间），轮询间隔：翻译 4s、朗读 5s、详解 30s（沿用各链路既有口径）。

**「粗算」措辞**：直接沿用 R176 已定口径（`reading_word_detail/service.py:37-39` 注释：「UI 上必须标成粗算，它是决策用的量级，不是账单」），三个 Tab 用同一套措辞，不新造第二套。

### 3.5 阅读入口解禁（缺陷，先行）

把 `detail.html:95-116` 的「在线阅读 / 在线阅读-格式下拉」移出 `role_admin()` 条件块，改为 `role_viewer()`；三个整本入口保留原条件。同时把 `编辑元数据 / 取消` 收进「管理员工具」区（`role_edit()` 已有，R211 后普通用户自然看不到，本次只做视觉分组）。

## 4. 依赖与跨仓契约

| 契约 | 现状 | 本条动作 |
| --- | --- | --- |
| `GET /credit/billing`（moon-well） | **不存在**；费率只在 `CreditBillingProperties`（Nacos 热调） | moon-well 新增只读端点回传 `{creditsPer1kToken, tts:{enabled,charsPerCredit}, perCall}`；magicbook 薄代理 `/ajax/credit/billing` 并缓存 5 分钟 |
| `POST /book/ai/ability/book-intro`（moon-well） | **不存在**；现有 `ability/summarize` 吃 moon-well bookId，两套 id 序列不可通用 | 按**正文入参**新增 book-intro 能力，出 `{text, model}`；`credit.billing.perCall` 加 `book-intro:1`（按次计费，与 `reading-translate` / `vocabulary-word-detail` 同形） |
| `GET /reading/paragraph-cache/find-translations` | 已有 | 代价面板复用其返回做「已缓存段数」，不改形制 |
| `/ajax/word-detail-preview` | 已有（R176） | 详解 Tab 直接复用，不重算 |
| `/tts/speak`、`/tts/cached-audio` | 已有 | 不改；朗读 Tab 只用字符数算上限（拍板③：不加批量探针） |

> 上面两条 moon-well 动作同属「magicbook R214 的后端配套」，建议**合并占一个 moon-well 编号**（当前台账到 R206，预计 R207），一个 worktree 交付，标题注明跨仓同源 magicbook R214。

## 5. 风险与回滚

| 风险 | 处置 |
| --- | --- |
| 详情页同步解析大 EPUB 拖慢首屏 | 缓存命中即 0 成本；`>8MB` 跳过摘录；解析异常只降级对应区块并落 `last_error` |
| `book_insight` 表随书库增长膨胀 | 只存摘要级数据（目录 + ≤1200 字摘录），单条约 3–8KB；按 `book_id` 唯一，重导入覆盖不追加 |
| AI 简介被当成书目原文 | 标注必须带「由 AI 生成 · 模型 · 时间」；不写入 Calibre comments（不动书库数据），只存 insight |
| 费率回传端点故障 | 积分行显示「费率暂不可得」并给字符/token 量，**不猜数字**；按钮仍可点（旧 confirm 文案兜底） |
| 耗时中位数样本偏差（老批次机器不同） | 只取最近 20 个同类批次且量级差 ≤2×；不足则回落常量并注明 |
| 门槛仍在 admin，普通读者看不到面板 | 有意为之（拍板①）：本条不改变「整本任务＝管理员工具」的定位 |
| 阅读入口解禁带来的权限回归 | 只放宽到 `role_viewer()`（原本 Calibre-Web 的阅读权限位），下载/编辑仍各自门禁；加一条守卫测试盯住「阅读入口不在 admin 条件内」 |

## 6. 拆单与顺序

```
A 基础信息（含 §3.5 解禁）──→ B 内容速览 ──→ C 代价面板
        ↑                            ↑
   难度解析器（与 R213 共用）      book_insight 落库
```

- 第一笔提交只做 §3.5（阅读入口解禁），因为它决定普通读者能否进入这个页面，且与后续全部改动正交。
- 三个子项同一 worktree、分阶段提交（家族纪律第 7 条：一次会话一个 worktree，`magicbook-r214-book-detail`，分支 `feat/r214-book-detail`）。
- C 的跨仓依赖（moon-well R207）未就绪时，C 的积分行先接「费率暂不可得」分支，不阻塞 merge。

## 7. 拍板记录（2026-10-23 第二轮讨论）

| # | 问题 | 拍板 |
| --- | --- | --- |
| 1 | 整本任务对谁可见 | **仅管理员**；面板与三个入口同门禁，普通读者只保留在线阅读 |
| 2 | 积分费率来源 | **moon-well 新增只读费率回传端点**（跨仓占号），magicbook 不镜像常量 |
| 3 | 朗读的缓存命中 | **暂不做**批量探针；面板给「全 miss 上限」+ 「已缓存段不重复计费」说明 |
| 4 | 简介缺失怎么办 | **AI 生成**，并在页面上标注「由 AI 生成」；不自动生成，管理员触发 |
| 5 | 双语怎么判 | **按书目自身声明**：页面不猜；导入侧把 `dc:language` 读全；存量走补正脚本 |
| 6 | 难度阶数据源 | 共用 R213 的解析器，**扩源**为「标签 `阶N` > 书架名 `阶N` > 系列映射 > 未分级」 |
| 7 | AI 简介要不要「重新生成」按钮 | **不要**（2026-10-23）：已生成即定稿；改写/重生成属未来需求，另立条目 |

**仍待定**（不阻塞 A/B/C 开工）：
1. 存量语言补正清单出来之后，书虫那批是「脚本批量写」还是「只在有 `chi` 声明时写」（dry-run 结果决定，届时请你确认执行）。

## 8. 非目标

- 不做阅读器章节跳转（无 hash/CFI 定位通道，另立需求）。
- 不做按正文探测语言（拍板⑤已否决）。
- 不改三个 job 的内核逻辑、不改 moon-well 的 job 接口。
- 不做书封大图 / 试读分页 / 读者评分与评论。
- 不收敛三份 EPUB 解析器（记技术债，另立一条）。
