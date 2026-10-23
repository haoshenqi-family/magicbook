# LLD — R214 书籍详情（A 基础信息 / B 内容速览 / C 代价面板）

> 状态：**定稿（2026-10-23）**；子项 A **已上线**（c4a98e54→develop，push 040b627b 触发部署）＋**A 验收缺陷 R218 已修**（§12，88ba3626/8643f8fe）；子项 B **已合入 develop**（f10fd755 缓存/解析/端点 + 3a52c102 模板三区块，2026-10-23，测试全绿）；子项 C 待开发（费率回传端点 moon-well R207 **已实现**，见 §11）；拍板⑦：AI 简介无「重新生成」按钮
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

### 4.3 `POST /ajax/whole-book-estimate`（admin）

请求：`{book_id, book_format, kind: "translate"|"tts"|"wordDetail"}`

```json
{"success": true, "result": {
  "kind": "translate",
  "units": {"chapters": 12, "paragraphs": 3160, "chars": 210000, "englishWords": 29455},
  "mutatesOriginal": false,
  "coverage": {"known": true, "cached": 2841, "total": 3160},
  "duration": {"basis": "history", "samples": 7, "seconds": 8640},
  "credits": {"known": true, "estimated": 1180, "upperBound": 1310, "rate": {"per1kToken": 10, "charsPerCredit": 1000}}
}}
```

`coverage` 分支：朗读固定 `{"known": false, "reason": "tts-cache-not-batchable"}`；
`credits.known=false / reason="rate-unavailable"` 当 moon-well 费率端点不可用（前端显示字符/token 量，不显示猜测数字）。

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

- `units(job)`：翻译取 `published_count`（本次真正发了多少段），朗读取 `done_count`。
- 量级过滤：只用「单位数 ≥ 30」的批次，避免 3 段的小批次把中位数带偏。
- 常量兜底（并在 UI 注明「按常量估算」）：翻译 `10.0 s/段`（依据 `reading_translation/service.py:22` 注释「moon-well 顺序执行器 ~1 段/10s」），朗读 `3.0 s/段`（0.8s 间隔 + 合成延迟；该常数**必须标注为估算**，R142 实测最长段 78.6s 说明方差极大）。
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
| AI 简介上游失败 | 区块内红字显示上游 message，不冒充「暂无简介」 |
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
