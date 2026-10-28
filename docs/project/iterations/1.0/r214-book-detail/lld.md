# LLD — R214 书籍详情（A 基础信息 / B 内容速览 / C 代价面板）

> 状态：**定稿（2026-10-23）**；子项 A **已上线**（c4a98e54→develop，push 040b627b 触发部署）＋**A 验收缺陷 R218 已修**（§12，88ba3626/8643f8fe）；子项 B **已合入 develop**（f10fd755 缓存/解析/端点 + 3a52c102 模板三区块，2026-10-23，测试全绿）；**B 验收缺陷 R222 已上线**（§14，上游故障改 502 + Magpie 白名单，push `a2056ec5`）；**子项 C 开发完成**（2026-10-24：`estimate()` + `/ajax/whole-book-estimate` + 面板 partial/JS，实现修正见 §4.3 表内；待真机验收）；**入口可达性缺陷 R236 已修**（2026-10-28，§15：弹层内恢复「整本任务」入口，链接跳完整详情页）；**R237 已修并部署**（2026-10-28，§16：后端 proxy 三元组被 tts 二元组解包 + 前端进度条被浮动列撑成整屏透明层，`8c388234`；§17：部署重启打断 worker 后进度条提供「继续」入口，待验收）；拍板⑦：AI 简介无「重新生成」按钮
> **2026-10-23 子项 A 验收缺陷修复**：`/book/<id>` 对「在任意书架里的书」整页 500（难度阶把 shelf id 当 Shelf 对象取 `.name`）——见 §12，分支 `fix/r214-detail-500`
> 对应 HLD：[`hld.md`](./hld.md) · 验收：[`ac/acceptance.md`](./ac/acceptance.md)
> 迭代 1.0 · PJM MB-13 · Ship MAGICBOOK-221

## 1. 文件清单

| 动作 | 路径 | 说明 |
| --- | --- | --- |
| 新增 | `cps/reading_insight/__init__.py` | 空壳导出 |
| 新增 | `cps/reading_insight/models.py` | `BookInsight` 表 |
| 新增 | `cps/reading_insight/parser.py` | OPF spine / nav / ncx 解析、章节与摘录、词数语言统计 |
| 新增 | `cps/reading_insight/difficulty.py` | 难度阶解析（四级兜底，与 R213 共用） |
| 新增 | `cps/reading_insight/service.py` | `get_or_build()`、`generate_summary()`、`estimate()` |
| 新增 | `cps/routes/book_detail.py` | 4 个 ajax 端点（挂 `web` 蓝图，与 `routes/reading.py` 同形） |
| 新增 | `cps/templates/partials/whole_book_panel.html` | 代价面板模态 + 进度条骨架 |
| 新增 | `cps/static/js/whole-book-panel.js` | 面板交互（替换 `detail.html` 内联 jQuery） |
| 改 | `cps/templates/detail.html` | 元数据区块、简介/目录/试读区块、按钮区、内联脚本迁出 |
| 改 | `cps/web.py`（`show_book`，:2441） | 注入 `insight`、`difficulty`、`pubdate_is_import_date`、活跃批次快照 |
| 改 | `cps/epub.py`（:84-94, :114） | `dc:language` 读全（多语言列表） |
| 新增 | `scripts/backfill_languages.py` | 存量语言补正（dry-run 默认） |
| 新增 | `tests/test_book_detail_r214.py` | 单测 + 守卫 + 反向变异 |
| 新增 | `tests/test_whole_book_estimate.py` | 估算分支单测（覆盖率/耗时/积分/降级） |
| 新增 | `tests/test_epub_languages.py` | 多语言导入回归 |
| 改 | `cps/static/css/…`（对应 detail 样式文件） | 「已在书架」芯片、双语徽标、AI 简介标注 |

## 2. 表结构

```python
class BookInsight(ub.Base):
    __tablename__ = "book_insight"
    id            = Column(Integer, primary_key=True)
    book_id       = Column(Integer, nullable=False, index=True)
    book_format   = Column(String(20), nullable=False)
    fingerprint   = Column(String(64), nullable=False)
    payload_json  = Column(Text, nullable=False)     # 见 HLD §3.1
    schema_version= Column(Integer, nullable=False, default=1)
    built_at      = Column(DateTime(timezone=True), default=now_utc, nullable=False)
    last_error    = Column(Text)
    __table_args__ = (UniqueConstraint("book_id", "book_format", name="uq_book_insight"),)
```

- 建表沿用 `ub.Base.metadata.create_all(bind, tables=[BookInsight.__table__])`（`reading_job/service_base.py:73` 同款），首次访问懒建。
- 唯一键 `(book_id, book_format)`；`fingerprint` 变化即重建覆盖，不追加历史。
- `payload_json` 里 `aiSummary` 单独可写（生成简介只 UPDATE 该键，不动整条 payload）。

## 3. 解析实现（`reading_insight/parser.py`）

```python
def parse(path) -> dict:
    opf_tree, opf_name = get_content_opf(path, default_ns)   # cps/epub_helper.py:60
    spine_files = [...]                                       # manifest + spine 顺序
    chapters = []                                             # 先 nav/ncx，取不到退化按文件
    paragraphs, chars, en_words = 0, 0, 0
    excerpt = []
    for href in spine_files:
        root = lxml_parse(zip.read(href), recover=True)       # 与 translation/parser 同款宽松解析
        title = nav_title.get(href) or _h1_or_title(root)
        n = 0
        for node in block_nodes(root):                        # p/li/blockquote/pre，跳过 nav/script/style/svg/noscript
            text = normalize(node)
            if not text: continue
            n += 1; paragraphs += 1; chars += len(text)
            en_words += len(WORD_RE.findall(text))
            if len("".join(excerpt)) < EXCERPT_MAX_CHARS: excerpt.append((title, text))
        chapters.append({"title": title or fallback, "href": href, "paragraphCount": n})
    languages = decl_languages(opf_tree)                     # 全部 dc:language → lang3
    return {...}
```

- 常量：`EXCERPT_MAX_CHARS = 1200`、`MAX_PARSE_BYTES = 8 * 1024 * 1024`（超限只出 chapters + 统计，不出摘录）、`WORD_RE = re.compile(r"\b[A-Za-z][A-Za-z'’-]*\b")`（与 moon-well 取词口径逐字一致，见 `reading_word_detail/service.py:31`）。
- 目录层级：nav.xhtml 的嵌套 `<ol>` → `level`；ncx 的 `navPoint` 深度同理；退化路径 `level=1`。
- **不复用** `reading_translation/parser.py` / `reading_tts/extractor.py`（HLD §3.1 已述），三个 job 的解析器保持不动。

## 4. 端点契约（`cps/routes/book_detail.py`）

全部挂 `web` 蓝图、`@user_login_required`；写操作带 `X-CSRFToken`。

### 4.1 `GET /ajax/book-insight?book_id=&book_format=`

```json
{"success": true, "result": {
  "bookId": 337, "bookFormat": "epub", "fingerprint": "…",
  "chapters": [{"title": "Chapter 1", "level": 1, "paragraphCount": 24}],
  "paragraphCount": 3160, "charCount": 210000, "englishWordCount": 29455,
  "declaredLanguages": ["eng", "chi"],
  "excerpt": [{"chapter": "Chapter 1", "text": "…"}],
  "aiSummary": {"text": "…", "model": "…", "generatedAt": 1792741949} , "builtAt": 1792741949}}
```

失败：`{"success": false, "message": "…"}` + 400/500；`last_error` 同时落库。前端各区块独立降级（目录失败不影响简介）。

### 4.2 `POST /ajax/book-summary`（admin + `_llm_task_admin_gate`）

- 入：`{book_id, book_format}`；入参组装 metadata + chapters + excerpt（≤1200 字）。
- 出：`{success, result:{text, model, generatedAt}}`；落 `book_insight.ai_summary`。
- 上游：`POST {moonwell}/book/ai/ability/book-intro`（跨仓 R207），timeout 60s。
- 失败：**透传上游 message**，前端区块内显示红字；不写 `ai_summary`，不静默变「暂无简介」。
  状态码按故障所属层区分：本地入参/书籍文件问题 `400`；moon-well/Magpie 未完成生成 `502`（R222）。

### 4.3 `POST /ajax/whole-book-estimate`（admin）

请求：`{book_id, book_format, kind: "translate"|"tts"|"wordDetail"}`

```json
{"success": true, "result": {
  "kind": "translate",
  "units": {"chapters": 12, "paragraphs": 3160, "chars": 210000, "englishWords": 29455,
            "billable": 2987},
  "mutatesOriginal": false,
  "coverage": {"known": true, "cached": 2841, "total": 2987},
  "duration": {"known": true, "basis": "history", "samples": 7, "seconds": 8640},
  "credits": {"known": true, "estimated": 1180, "upperBound": 1310, "rate": {"per1kToken": 10}},
  "activeJobs": {"translate": {"jobId": "…", "status": "RUNNING", "total": 2987, "done": 1200},
                 "tts": null, "wordDetail": null}
}}
```

`coverage` 分支：朗读固定 `{"known": false, "reason": "tts-cache-not-batchable"}`；
`credits.known=false / reason="rate-unavailable"` 当 moon-well 费率端点不可用（前端显示字符/token 量，不显示猜测数字）。
TTS 关闭计费时给专属 `reason="tts-not-billed"`，不与「费率不可得」混为一谈。

**实现修正（2026-10-24，C 轮落地时）**

| 项 | 设计 | 落地 | 原因 |
| --- | --- | --- | --- |
| `units.billable` | 无 | 新增 | 翻译/朗读台账的 item 都按 `text_hash` 唯一（`TranslationJobItem` 的 unique 字典、`ReadingTtsJobItem` 的 `uq(job_id,text_hash)`）。拿全书段落数当工作量会把重复段算两遍，耗时与积分一起虚高；`paragraphs` 保留书目真实段数，`billable` 才是本次真实单位 |
| `activeJobs` | 无（§7.5 只说「show_book 注入快照」） | 估算响应与 `show_book` 共用 `active_jobs()` | 页面初始进度态需要一个服务端承载字段；让估算与首屏用同一函数，两条路径的 `total/done` 口径不会分叉 |
| `duration.known` | 隐含有值 | 显式 known/reason | 详解没有经过实测的常量（LLD §5.2 只给了翻译 10s/段、朗读 3s/段），无样本时宁可不给数字，也不编一个 |
| `credits.rate` | 同时回传 `per1kToken` 与 `charsPerCredit` | 只回传本条链路用到的那一个 | 翻译不按字符计费、朗读不按 token 计费，一起给会让前端误配 |
| 详解覆盖率 | 「走 preview」 | 直接分批调 cached-check | `preview()` 内部会重抽一遍正文（估算已抽过），而它的 `notWordLike` 只在预览页有解释位；面板只要 cached/total |

`coverage.known=false` 时 `credits.reason="full-text-upper-bound"`：积分按全书去重后的
字符算，前端据此把这一行标成上界而不是「预计」。

### 4.4 复用既有端点

| 用途 | 端点 |
| --- | --- |
| 翻译起批 / 进度 / 重试 / 取消 | `/ajax/reading-translate-book{,/status,/retry,/cancel}` |
| 朗读起批 / 进度 / 重试 / 取消 | `/ajax/reading-tts-book{,/status,/retry,/cancel}` |
| 详解预览 / 起批 / 进度 / 取消 | `/ajax/word-detail-{preview,start,progress,cancel}` |

**一个都不改形制**；面板只是它们的调用方。

## 5. 估算算法（`service.estimate()`）

### 5.1 覆盖率

| kind | 算法 |
| --- | --- |
| translate | `_whole_book_closures().lookup(paragraph_texts)`（只读，不 publish），`cached = len(hit)` |
| wordDetail | 走 `word_detail_batch_service.preview()`，取 `targetWords / distinctWords` |
| tts | 不算（拍板③），`coverage.known = false` |

### 5.2 耗时（历史实测中位数，不足回落常量）

```python
def _rate_per_unit(model, status_done):  # 翻译 / 朗读各一张台账
    rows = (ub.session.query(model).filter(model.status == status_done)
            .order_by(model.created_at.desc()).limit(20).all())
    samples = [((r.updated_at - r.created_at).total_seconds() / units(r))
               for r in rows if units(r) >= MIN_UNITS]
    return statistics.median(samples) if len(samples) >= 3 else None
```

- `units(job)`：翻译取 `published_count`（本次真正发了多少段），朗读取 `done_count`，详解取 `published_words`。
- 量级过滤：只用「单位数 ≥ 30」的批次，避免 3 段的小批次把中位数带偏。
- 常量兜底（并在 UI 注明「按常量估算」）：翻译 `10.0 s/段`（依据 `reading_translation/service.py:22` 注释「moon-well 顺序执行器 ~1 段/10s」），朗读 `3.0 s/段`（0.8s 间隔 + 合成延迟；该常数**必须标注为估算**，R142 实测最长段 78.6s 说明方差极大）。
- **详解没有常量兜底**：没有任何一条实测能支撑「秒/词」，样本不足时 `duration.known=false`，面板写「暂无实测样本」——编一个数字比不给数字更糟。
- 返回 `samples` 数量，UI 显示「基于最近 N 个批次」。

### 5.3 积分（粗算）

```
translate : tokens ≈ chars / 4          ; credits = ceil(tokens / 1000) * per1kToken
tts       : credits = chars // charsPerCredit
wordDetail: tokens = targetWords * 4000  ; credits = ceil(tokens / 1000) * per1kToken
```

- 费率全部来自 `/ajax/credit/billing`（moon-well R207），5 分钟进程内缓存；取不到即 `credits.known=false`。
- `upperBound`：翻译/详解取 `estimated * 1.1`（取整），朗读即 `estimated`（已是全 miss 上限）。
- UI 措辞固定为「约 N 积分（粗算，非账单）」，与 `reading_word_detail/service.py:37-39` 的既有口径一致。

## 6. 模板改动（`cps/templates/detail.html`）

| 位置 | 现状 | 改法 |
| --- | --- | --- |
| `:80`–`:117` | 一个 `role_admin()` 包住 阅读 + 三个整本入口 | 拆两个条件块：阅读入口改 `role_viewer()`；整本入口保持 `role_admin()`。**第一笔提交只做这一处** |
| `:82`–`:93` | 三个整本按钮并列 | 合并为一个「整本任务」按钮，`data-book-id/format` 挂面板入口 |
| `:183`–`:189` | 语言行 | 声明 ≥2 语言时追加 `<span class="label label-info">双语</span>`；语言集合直接来自 `entry.languages`（不猜） |
| `:228`–`:232` | 出版日期 | `entry.pubdate_is_import_date` 为真 → `导入于 {{ entry.timestamp|formatdate }}` + tooltip；否则原样 |
| `:305`–`:310` | 简介 | 三级回退：comments → `insight.aiSummary`（带「由 AI 生成 · model · date」标注；**无「重新生成」按钮**，拍板⑦）→ 「暂无简介」+ 指向目录/试读 |
| 新增区块 | — | 目录（前 8 章 + 展开全部，章节展开显示该章首段）+ 首章试读（≤1200 字，淡出遮罩 + 继续阅读） |
| `:341`–`:358` | 移除书架按钮组 | 改 chip：`span.label.label-default` + ✕；与「加入书架」按钮分视觉层级 |
| `:364`–`:373` | 编辑元数据 / 取消 | 收进「管理员工具」分隔区（`role_edit()` 不变） |
| `:395`–`:436` | 内联 jQuery（两个 confirm + alert） | 整体迁到 `whole-book-panel.js`；旧 `#whole-book-translate` / `#whole-book-tts` id 由面板按钮替代 |

## 7. 前端交互（`whole-book-panel.js`）

1. 点「整本任务」→ 打开模态，默认 Tab = 翻译；Tab 切换时按需拉 `/ajax/whole-book-estimate`（结果按 `kind` 缓存到内存，切换不重复请求）。
2. 卡片渲染顺序：量 → 不修改原文件 → 覆盖率 → 耗时 → 积分 → 主按钮。任一字段 `known=false` 时显示灰色说明句，**不显示 0 或占位数字**。
3. 主按钮「开始整本翻译」→ 二次确认（复用现有文案 + 追加「预计 X 小时 · 约 N 积分」）→ 调既有 start 端点 → 关闭模态，页面顶部出现进度条。
4. 进度条：`setInterval` 轮询既有 status 端点（翻译 4s / 朗读 5s / 详解 30s），显示 `done/total`、百分比、上次更新时间；`COMPLETED` 后停轮询并提示（不自动刷新页面）。
5. 页面初次加载若有活跃批次（`show_book` 注入快照），直接进入进度态，不显示「开始」。
6. `t()` 文案走 i18n 种子（`i18n_seed.html` 同款），不硬编码中文到 JS 之外的地方——注意 `tests/test_i18n_seed_contract.py` 会校验新增文案。

## 8. 降级与失败可见（家族纪律：禁止静默降级）

| 失败点 | 行为 |
| --- | --- |
| insight 解析失败 | 对应区块显示「解析失败：<原因>」，其余区块正常；`last_error` 落库便于排查 |
| 费率端点不可用 | 积分行显示「费率暂不可得」，仍显示字符/token 量；按钮可点 |
| 翻译 cache lookup 失败 | 覆盖率显示「缓存命中暂不可得」，**不显示 0** |
| AI 简介上游失败 | 区块内红字显示上游 message；HTTP 502（非 400），不冒充「暂无简介」 |
| 活跃批次查询失败 | 按钮回到「开始」并在控制台留 warn（页面可用） |
| 详情弹窗 AJAX 非 2xx | 弹窗内显示「加载失败」（`layout.html` 预置节点 + `main.js` `.fail()`），**不停在占位符 `...`**；见 §12 |

## 9. 存量语言补正（`scripts/backfill_languages.py`）

```
python3 scripts/backfill_languages.py                 # dry-run：只出清单
python3 scripts/backfill_languages.py --apply --ids 337,336
```

- 逐本读 EPUB 全部 `dc:language` → `lang3` 列表，与 `books_languages_link` 现状 diff。
- 输出三列：`book_id | 现状 | OPF 声明`；只列**有差异**的。
- `--apply` 走 Calibre 语义的写库（`books_languages_link` upsert），**不动 EPUB**；执行前自动备份 `metadata.db` 到 `metadata.db.bak-<ts>`。
- 默认只读，符合家族「扫描＝只出报告」纪律；书虫 137 册是否真有 `chi` 声明，由 dry-run 结果决定是否执行（HLD §7 待定项 2）。

## 10. 测试

| 类型 | 用例 |
| --- | --- |
| 单测 | `parse()`：单语言 EPUB / 双语 EPUB / 无 nav 退化 / 大书跳过摘录；`difficulty` 四级兜底；`estimate` 三 kind 的 coverage/duration/credits 分支（含 `rate-unavailable`、`tts-cache-not-batchable`） |
| 契约守卫 | `estimate` 响应必须含 `units/mutatesOriginal/coverage/duration/credits` 六个键；`coverage.known=false` 时必须带 `reason` |
| 模板守卫 | 断言 `detail.html` 里「在线阅读」**不在** `role_admin()` 条件块内（反向变异：把它移回去 → 测试报红） |
| 模板守卫 | 断言 AI 简介渲染包含「由 AI 生成」文案（防标注被删） |
| 导入回归 | `get_epub_info()` 对含 2 个 `dc:language` 的 EPUB 返回 `["eng","chi"]`（反向变异：改回 `tmp[0]` → 报红） |
| 集成 | 真 socket 起 app，`/book/337` 普通用户可见「在线阅读」、不可见「整本任务」；admin 两者都可见 |
| 回归 | 既有 66 个测试文件全绿（尤其 `test_no_duplicate_js_lines.py` 与 `test_i18n_seed_contract.py`） |

## 11. 未决（不阻塞开工）

1. 存量语言补正的执行范围（dry-run 出来后请你确认）。
2. ~~moon-well R207 占号~~ **已落地（2026-10-23）**：`POST /book/ai/ability/book-intro`（按正文入参，不吃 bookId）+ `GET /credit/billing`（费率回传）已实现并合入 moon-well develop（`f89c9ff`+`2433c65`）。**设计修正**：book-intro 不进 `perCall` 白名单——能力调用走 `callForTask` 任务路径按 token 计量，`perCall` 只覆盖交互路径，原「perCall 加 book-intro:1」会造出假费率，已回正（详见 moon-well requests R207）。两侧 L2 契约文档互链待 C 收尾时补。

> 已拍板关闭：AI 简介不提供「重新生成」按钮（2026-10-23 拍板⑦）；简介长度 120–200 字、模型取 moon-well `book-intro` 默认。

## 12. 子项 A 验收缺陷：`/book/<id>` 整页 500（2026-10-23，`fix/r214-detail-500`）

**现象**：书架页点封面 → 「书籍详情」弹窗正文只剩字面量 `...`，读不了书。

**根因**（`fdd95225` 引入）：A6 的二级兜底要「书架名」，调用点写成
`shelf_names=[s.name for s in book_in_shelves]`；而 `book_in_shelves` 攒的是
`ub.BookShelf.shelf` —— `Column(Integer, ForeignKey('shelf.id'))`，整数列不是 Shelf 关系对象。
`AttributeError: 'int' object has no attribute 'name'` → `show_book` 抛 500。

**为什么只有部分书炸**：不在任何书架的书 `book_in_shelves` 为空，推导式不执行 → 页面照常。
现象因此长成「有的书打得开、书架里的整架打不开」，容易被误读成个别文件损坏。
线上 ES 实证 21:07 起 9 次 `Exception on /book/{id}`，栈顶即 `web.py:2576`。

**为什么单测没拦住**：§10 表里那条「集成：真 socket 起 app 打 `/book/337`」**子项 A 没落地**，
`test_book_detail_r214.py` 全是模板正则守卫 + `resolve_difficulty` 纯函数单测——
纯函数签名写明「参数为名称列表、不碰数据库」，调用点却传了 id 列表，两侧各自正确、
接线错误无人守。ops 准则⑦的同一形态：契约有形制、消费侧无守卫。

**修法**：名称由 `_shelf_names_for_book(shelf_ids)` 单查一次（`in_` 一条 SQL，不按书架数
lazy load 出 N+1）。`book_in_shelves` 保持 id 列表不动——`detail.html` 用
`shelf.id in books_shelfs` 判「已加入书架」，形制改了会连带坏掉。

**补的守卫**（`tests/test_book_detail_r214.py`）：
- 真 ORM 造「阶N」书架 + 书-架关联，钉住 id→名→解析器整条接线，含空集分支；
- **调用点源码守卫**：断言 `show_book` 体内是 `_shelf_names_for_book(book_in_shelves)`，
  且全文件不再出现 `[s.name for s in book_in_shelves]`——转换器与解析器的单测都拦不住
  「参数形制在调用点错位」，只能钉调用点（反向变异换回去即报红，已实测）；
- 弹窗失败可见性守卫 ×2（见下）。

**顺带修掉的第二半（静默降级）**：`#bookDetailsModal` 的 `$.get` 原先只挂 `.done()`，
服务端一报错弹窗就停在模板占位符 `...`——接口故障被伪装成「这本书没详情」。现补 `.fail()`
显示「加载失败」（复用 po 已有词条，不新引 msgid、不动 i18n 生成链）。同时补
`preFilters.remove(useCache)`：原代码只在成功路径摘，一次失败就把 preFilter 永久挂在
jQuery 上污染后续所有 AJAX。

## 13. 子项 C 验收缺陷：面板打开后「跳错地方」+ 估算 500（2026-10-24）

用户首轮验收报「整本任务点击后跳转路径不对」，Console 给出两条硬事实：
`/ajax/whole-book-estimate` **500**；页面里出现 `#bookDetailsModal` 套整页的错乱。

**缺陷一：入口按钮落在「书卡弹层」的 XHR 片段里。**
列表页点书卡走的是 XHR：`show_book` 用 `is_xhr|yesno("fragment.html", "layout.html")`
把 `detail.html` 渲染成**片段**，片段没有 `block js` ⇒ 面板骨架（modal + `whole_book_panel.html`）
与 `whole-book-panel.js` 都不下发，但按钮在 `block body` 里照旧渲染。点下去 `data-target`
选不到 `#whole-book-panel`，Bootstrap 的 data-api 静默空转，与页面上既有的
`#bookDetailsModal` 抢同一次点击，最终形态就是「整页被套进另一个弹层」。
**修法**：① 按钮加 `not is_xhr` 门禁——整本任务只在完整详情页出现；② 按钮不再用
`data-toggle`/`data-target`，改由 JS 显式绑定（`preventDefault` + `stopPropagation`），
把这一次点击从 data-api 的模糊地带里拿出来。守卫：`test_entry_button_does_not_use_bootstrap_data_api`、
`test_entry_button_hidden_in_xhr_fragment`、`test_panel_open_is_bound_explicitly`。

**缺陷二：`/ajax/whole-book-estimate` 500。**
估算链路里有两处「辅助数据」的裸查询（`_history_rate` 的台账采样、`active_jobs` 的活跃批次），
任何一处抛错（表缺失/库忙/ORM 异常）都会把整个面板打成 500，而 `.fail` 拿到的是 HTML，
界面上只剩「估算失败：500 Internal Server Error」——**既不知道原因，也不知道该不该重试**。
**修法**：① 两处查询各自 try/except，降级为「没有实测样本 / 没有活跃批次」并落 warning
（辅助数据不该决定主结论）；② 路由补兜底 `except Exception`：落 `traceback.format_exc()`
到服务端日志，把 `异常类型: 消息` 回给前端——面板上直接显示原因。
守卫：`test_history_rate_swallows_query_errors`、`test_active_jobs_swallows_query_errors`、
`test_estimate_route_reports_instead_of_bare_500`。

**缺陷三（顺带，形制级）：`data-t-start-wordDetail` 取不到值。**
HTML 解析器把属性名统一小写（`data-t-start-worddetail`），而 JS 侧 `t('start-' + kind)`
用的是 camelCase ⇒ 详解 tab 的主按钮文案是空字符串。**修法**：模板属性名写全小写，
JS 侧 `String(kind).toLowerCase()`。守卫：`test_start_label_keys_are_lowercase`。

## 14. 子项 B 验收缺陷：生成简介返回 400（2026-10-24，R222，`fix/r222-book-summary-400`）

**现象**：管理员点「生成简介」，浏览器 Console 报
`POST https://magicbook.haoshenqi.top/ajax/book-summary 400 (Bad Request)`。

**根因分两层**：

1. **应用层误报**：`service._unwrap_result()` 把 moon-well 的任意失败统一抛成 `ValueError`，
   `/ajax/book-summary` 又与入参错误共用同一 `except`，因此上游 HTTP 500 被改写成 HTTP 400。
2. **运行层真实故障**：moon-well 调 Magpie 的来源是 Docker bridge 地址 `172.28.0.1`，但
   Magpie `settings.json` 的 `allowIPs` 只有 `192.0.0.0/8`。Magpie 返回 403，moon-well
   包装为 500（`Magpie call failed: HTTP 403`），magicbook 再误报为 400。

**修法**：

- 新增 `UpstreamServiceError` 携带上游状态码；`/ajax/book-summary` 对上游故障返回 **502**，
  本地入参/文件问题仍返回 400，message 原样透传。
- Magpie `allowIPs` 增加 `172.28.0.0/16`（只覆盖该 bridge，不放开任意来源），
  修改前备份 `settings.json`，重启后 `magpie healthcheck` 为 0。

**证据**：

- 修改前日志：ES `app-log-moon-well` 在 18:33–18:36 连续记录
  `Magpie call failed: HTTP 403`，对应 `/book/ai/ability/book-intro` 返回 500；
  Magpie 同步记录 `refused POST /v1/chat/completions from 172.28.0.1: not on the allow list`。
- 修改后从 `moon-well-green` 容器带 gateway key 请求 `GET /v1/models`：HTTP 200；
  Magpie 不再以 allow-list 拒绝该来源，重启后的日志只有缺失 key 的预期 401（探针未带 key
  那次）与 Qoder 登录态过期的既有噪音，无新的 403。
- 回归：`tests/test_book_detail_r222.py`（502 / 成功 / 3xx 非成功 / 400 四分支）+
  `tests/test_book_insight.py` + `tests/test_book_detail_r214.py` 共 49 passed。
- 上线：`a2056ec5` 推送 `origin/develop` 后，fnOS 链于 19:07 构建并部署成功；
  运行镜像 label `house.build-sha=a2056ec5`，容器 `healthy`；首页稳定返回登录跳转 302。
  Magpie 文件为 `65532:65532`（settings 700、备份 600），healthcheck rc=0；
  moon-well/magicbook 近 20 分钟无新的 allow-list 拒绝或 book-intro 403。
  最终「生成简介」200 与简介落库仍需管理员登录页面验收。

## 15. 入口可达性缺陷：弹层里整本任务入口不可达（2026-10-28，R236，`fix/r236-wholebook-modal-entry`）

**现象**：管理员在书库列表找不到「整本任务」入口。§13 的修法把开面板按钮加
`not is_xhr` 门禁收进完整详情页后，完整详情页在 UI 里**没有任何普通左键可达的路径**——
书卡（封面/书名）链接全部被 `data-toggle="modal"` 截去 `#bookDetailsModal`，弹层即
XHR 片段；只有 Cmd+点击/中键/手输 `/book/<id>` 才能到达。入口事实上对所有人隐藏。

**根因**：§13 修复选了「把按钮从弹层里拿掉」而非「让面板在弹层里可用」，且弹层内
没有任何通往完整详情页的链接——可达性缺口是那次修复引入的回退（`42ddfb19`）。

**修法（用户拍板：只做弹层恢复入口，不改其他）**：`detail.html` 新增
`{% if current_user.role_admin() and is_xhr %}` 分支，渲染同款样式的普通链接
`<a class="btn btn-default" id="whole-book-panel-link"
href="{{ url_for('web.show_book', book_id=entry.id) }}">整本任务</a>`。
同 URL 不带 `X-Requested-With` 头即渲染完整详情页，面板在完整页内照常打开；
不挂 `data-toggle`/`data-target`（§13 data-api 抢点击教训）。开面板按钮行
（`whole-book-panel-open`）原样不动，`not is_xhr` 语义不变。

**守卫**：`test_xhr_modal_entry_is_full_page_link`（链接指向 show_book、无
data-api、role_admin + is_xhr 双门禁）；既有四条守卫（admin 门禁/data-api 禁用/
XHR 隐藏/旧三按钮不复活）全部原样通过。回归：detail 相关 4 个测试文件 108 passed。

## 16. 验收缺陷：整本朗读批次全灭——proxy 三元组被二元组解包（2026-10-28，R237，`fix/r237-tts-proxy-unpack`）

**现象**：R236 入口恢复后真机验收，点「开始整本朗读」后批次受理成功（job 3007 段），但
done 恒为 0、failed 全量增长；moon-well 侧每段收到**两次** `/tts/speak`（第一次真合成
2~10s、约 1s 后同文本再命中缓存 6ms）。伴随日志 `voice select failed (too many values
to unpack (expected 2))`。用户报告的「开始整本朗读后白屏」面板 JS 无白屏路径（成功/400/
504 三变体真浏览器 harness 验证页面完好、零 JS 错误），最可能是批次空转双倍合成 +
每段两次 sqlite 写把 fnOS CPU/DB 打满、后续页面加载长时间白屏等待所致。

**根因**：`MoonWellClient.proxy` 恒返回三元组 `(body, status, headers)`（成功分支与
`_error_tuple` 失败分支都是），而 `cps/reading_tts/service.py` 两处按二元组解包：
①`_select_voice` 的 `body, status = self._proxy(...)`——ValueError 被 try 吞成 WARN
「选角失败回退默认音色」；②`_synth_worker` 的 `body, status = proxy(...)`——每次调用
抛 ValueError，被重试环 `for attempt in (1, 2)` 捕获、睡 1s 重发（第二次命中 moon-well
缓存）后仍抛 → 每段 FAILED。**单测漏网根因**：`tests/test_reading_tts_service.py` 的
桩 proxy 也只回二元组——桩没有镜像真实契约，service 的二元解包在单测里永远通过。

**修法**：两处改为 `body, status, _headers = ...`；三个测试桩全部改为三元组返回
（桩即契约镜像）；新增守卫 `test_moonwell_proxy_contract_is_three_tuple`（钉住
proxy 成功分支 `return (body, response.status_code,` 与 `_error_tuple` 三元组形态，
反向变异报红）。反向变异实测：改回二元组解包 → 3 failed。

**止血与善后**：发现时 book 50（HP1，3007 段）批次已烧 208 段全 FAILED，已直接置
`CANCELLED` 停止空转（done=0/failed=208 留档）；两次合成的音频均已落入 moon-well
段落缓存，重启批次将全部缓存命中、不重复计费。测试：tts 全家 5 文件 50 passed。

**验收追加：白屏的真因是进度条覆盖整页（2026-10-28）**。前文「批次资源耗尽拖成白屏」
的假设已被生产页 CSSOM/盒模型实测推翻；后端 proxy 解包缺陷仍真实存在且必须保留修复。
真机 DOM 显示 `whole_book_panel.html` 的 `block js` 实际落在详情页
`.container-fluid` 内，该容器的 Bootstrap 浮动列高 775px 且未清除；
`.wb-progress` 外层的 border box 从容器顶部起算，内层却被浮动推到 y=846，导致外层
`getBoundingClientRect()` 为 `813px` 高、页面中心 `elementFromPoint()` 命中进度条，
正文并未丢失，只是被透明层覆盖。临时设 `clear:both` 可让外层回到 38px，但会把吸顶
进度条固定到文档底部；最终修法是在 `whole-book-panel.js` 初始化时把 `#whole-book-progress`
`insertAfter(body > .navbar)`，回正常文档流并保留原 sticky 吸顶语义。实测重挂后外层
38px、内层 37px，页面中心重新命中 `.book-meta`。守卫：
`test_progress_bar_is_moved_out_of_float_layout`。回归：detail 39 passed；整本估算 +
tts 5 文件 62 passed；i18n / 重复 JS 行 6 passed。

## 17. 验收缺陷：部署重启后批次失联——进度条「继续」入口（2026-10-28，R237，`fix/r237-tts-proxy-unpack`）

**现象**：R237 修复部署后，`book 50` 的整本朗读批次停在 `RUNNING 1239/3007`，
`PENDING 1768`、`FAILED 0`；最后推进 14:15:32，14:15:53 与 14:33:00 两次容器重启
均发生在批次运行期间。页面仍轮询状态，但「开始」在活跃批次下被禁用，用户没有恢复入口。

**根因**：整本朗读 worker 是 magicbook 进程内 daemon 线程。部署重启会杀掉线程，
SQLite 台账仍保留 `RUNNING`；`get_progress()` 只读台账，无法从 DB 判断线程是否还活着。
服务已有 `_needs_worker()` 自愈判据（未取消 + 无活线程 + 仍有 PENDING），但此前只有
`start/retry` 请求会触发它，页面状态轮询不会。

**实现**：

- `WholeBookTtsService.progress()` 增发 `canResume`：仅当状态属于 `RUNNING/PARTIAL_FAILED`
  且 `_needs_worker(job)` 为真时返回 `true`。该字段是对「当前进程是否真的还有 worker」
  的服务端判定，不是单纯根据 `updated_at` 猜测停滞。
- `whole_book_panel.html` 在进度条增加隐藏的「继续」按钮与错误行，
  `data-url-tts-retry` 指向既有 `/ajax/reading-tts-book/retry`。
- `whole-book-panel.js` 在状态轮询返回 `canResume=true` 时显示按钮；点击后调用 retry，
  成功后用返回快照恢复轮询，失败原因留在进度条内。恢复使用原批次台账，不新建 job，
  不重置进度，已完成段与 moon-well 音频缓存继续复用。

**边界**：活线程仍在时不显示「继续」；`CANCELLED` 不复活；`COMPLETED` 不显示；
`retry` 的后端原子 spawn 仍负责防止并发双开。

**守卫**：`test_progress_can_resume_only_when_pending_and_no_live_worker` 钉住
canResume 的服务端语义；`test_stalled_tts_batch_has_a_frontend_resume_entry` 钉住
模板按钮、retry URL、JS 接线；路由测试补 `/retry` 转发。
