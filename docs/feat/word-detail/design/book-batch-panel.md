# 全文单词详解（R176）· magicbook 侧台账与页面

> L3 详细设计 | 状态：**已实现**（`tests/test_word_detail_batch_r176.py` 36 例本地绿，未推送）
> 需求原文：`requests.md` R176 | 对端：moon-well `docs/feat/word-detail/design/book-batch-warm-by-words.md`（R188，开工时登记为 R185、与架构评审流撞号后改锁）
> 同族：[整本翻译 admin-panel](../../llm-task-run/design/admin-panel.md)（R126）、`reading_translation` / `reading_tts` 两条批处理链路

## 1. 目标

详情页第三个「整本」按钮：**给这本书把查不到的词补成单词详解**。与整本翻译、整本朗读共用形制
（job/item 台账 + 请求线程定格 token + 查询时懒回收 + 页面轮询），**两处刻意不同**：入队前多一次
只读预览（见 §2），轮询是 30s 而不是 4s（见 §4）。

与 top 25k 那种「按词频铺词典」的区别就是本功能的立身理由：今天实测一本真文本里缺失的词只有
**几十个**（687 去重词、缺失 64、其中 40 个还是缩略形），而按词频铺到秩 19,000 时缓存才涨到 6,575 篇
——**花钱的方向和阅读行为完全脱钩**。所以这里明确不做整库批处理，只按书。

## 2. 两步式，不接受一键下单

| 步骤 | 端点 | 副作用 |
| --- | --- | --- |
| ① 预览 | `POST /ajax/word-detail-preview` | **只读**：抽正文→分词→调 moon-well `cached-check`→回 `{去重词, 已缓存, 待生成, 非词形, 粗算 tokens, 缺失样例}` |
| ② 入队 | `POST /ajax/word-detail-start` | 建 job/item 台账，后台分批 200 词调 moon-well `warm-publish-by-words` |

预览路由**只拿 check 闭包、结构上就拿不到 publish 能力**（单测据此断言 `warm-publish-by-words`
一次都没被打）——「不产生副作用」做成约束而不是靠约定。

Why：管理员必须在看到「这本书要生成 N 个详解 ≈ M 万 tokens」之后再点第二次。数字来自
moon-well 的只读端点，前端不做任何覆盖率判断；粗算 tokens 用 `待生成 × 4,000`（4,000 来自 R109
生产实测均值），UI 上必须标成「粗算」而不是「预计花费」。

## 3. 台账（新表，形制照抄 reading_translation）

`reading_word_detail_job`：`id, user_id, book_id, book_format, book_name, book_fingerprint, status(PENDING/RUNNING/PARTIAL_FAILED/CANCELED/COMPLETED), distinct_words, cached_words, target_words, published_words, covered_words, skipped_not_word_like, failed_batches, created_at, updated_at`
`reading_word_detail_job_item`：`id, job_id, batch_seq, words_json, word_count, status(PENDING/PUBLISHED/DONE/FAILED/SKIPPED), published_count, skipped_cached, skipped_in_flight, skipped_invalid, skipped_not_word_like, covered_count, error_message, created_at, updated_at`（唯一约束 `job_id + batch_seq`）

**item 粒度 = 一批 200 词，不是每词一行**：一本书上万行的台账只会让进度页变成滚动条坟场，
而 moon-well 侧本来就是按批返回计数；词本身已在 `words_json` 里，需要逐词时用 `cached-check` 现查。

`covered_count` 的两个来源：①发布回执里的 `skippedCached`（受理即知的覆盖，进度条不必从 0 起步）；
②之后的每轮覆盖率探针。`_item_target = word_count − skipped_invalid − skipped_not_word_like`：
被词形过滤挡掉的词**永远不会**生成详解，留在分母里覆盖率就永远到不了 100%，页面会一直报假故障。

去重与幂等：`book_fingerprint`（沿用 `text_hash` 那套指纹思路）+ 「同书有活动 job 且 `updated_at` 在 30 分钟内」直接复用
（`translate_all_english_books` 的 30 分钟拦截同形），**复用判定放在抽词与探针之前**——重复点击不该白付一趟
索引级扫描。真正的重复防护在服务端：已缓存跳过、在途跳过。

## 4. 进度口径（这是本设计最容易写错的地方）

**进度 = 词覆盖率**，不是任务完成率：`coveredWords / targetWords`，每次刷新走 `cached-check` 重算，
且**一轮只发一次聚合探针**（把所有未覆盖批次的词并成一个去重列表、按 2000 一批切），只探非终态批次。

Why 不能用任务状态：详解的执行方是队列消费者（外部 worker 或 R110 面板），magicbook 既不是发起者也不是
唯一消费者；把「COMPLETED」当完成还会踩上午那个坑——**872 条 COMPLETED 里有约 202 条产出不合契约、
缓存里根本没有**，只有覆盖率是唯一的真话。

Why 绝不能用 `GET /vocabulary/detail/{word}` 探进度：那会把「查进度」变成「下单」（miss 即现场生成并计费）。

**轮询 30s（不是整本翻译的 4s），且只在页面可见时**：`cached-check` 在服务端是一趟索引级扫描
（`search_after` 每页 1000 翻页），整本翻译能 4s 是因为它的进度源是本地 SQLite 行计数。
`POLL_MS` 由单测钉住，改回 4s 即红。

**发布阶段也在后台线程**（设计初稿说「发布是同步短请求」，实测口径修正）：moon-well 每批都要做一次索引扫描
+ 数百次单事务插入，几十批串起来必然被公网网关 60s 掐断——整本翻译 R78 就是被同一件事教过
（生产 3,160 段只发出 109 段）。代价是 start 的 HTTP 响应先于批次失败发生，所以**上游闸门文案改由
`progress.lastError`  surface**（台账里最新一条 FAILED 批次的 error_message），页面把它显示在 note 区。
不做起动恢复线程：本链路自愈是「同书再点一次」——30 分钟僵尸判定会关掉旧批次，服务端按已缓存/在途跳过，
重入零成本。

## 5. 代码落点（全部复用，零新造）

| 复用 | 位置 |
| --- | --- |
| 抽正文段落 | `cps/reading_translation/parser.py:93 extract_epub_paragraphs` |
| moon-well 转发 | `cps/web.py:1209 _moonwell_proxy`（含 401 刷新重试、`_MOONWELL_NO_PROXY` 绕代理） |
| admin JSON 门禁 | `cps/web.py` `_llm_task_admin_gate` 形制（`abort(403)` 给 HTML，必须返 JSON 403） |
| 请求线程定格身份 | `cps/web.py:1198-1233` 的 publish/lookup 闭包范式 |
| 台账骨架/僵尸自愈/SQLite 锁重试 | `cps/reading_translation/service.py:109/133/193/33` |
| 页面形制 | `cps/templates/translate_all.html`（自带 `post()` + CSRF + 进度表） |
| 按钮位 | `cps/templates/detail.html:82-85`（整本翻译/朗读旁）+ JS `:392-432` |
| 测试范式 | `tests/test_llm_task_run_r126.py`（monkeypatch 代理断言 path/payload/timeout、非 admin 403、po 词条、模板相邻重复行守卫） |

分词正则必须与 moon-well `ReadingVocabularyService.extractWords` 的 `\b[A-Za-z][A-Za-z'’-]*\b` 同口径，
缩略形与连字符词**在 magicbook 侧照抽、由 moon-well 内核统一过滤并计数**——过滤规则只能有一处，
否则两边各自「聪明」，同一本书在两入口下会得出不同的待生成集合。

## 6. 不做

- 整库批处理（「全库所有英文书补详解」）：与 top 25k 同一种错误，只是换了个维度。
- 自建 worker 合成/执行：执行归队列消费者，与整本朗读（自带 worker）刻意不同。
- 详解内容分页展示：阅读器划词点「详解」已有，页面只报数与进度。
- 第二套进度轮询、`static/js/*.js` 新文件、bootstrap-table：沿用 R126 的内联脚本形制。

## 7. 测试与验收（`tests/test_word_detail_batch_r176.py`，36 例本地绿）

1. ✅ preview 只读：断言打到上游的路径集合恰为 `{cached-check}`，`warm-publish-by-words` 一次都没被调
2. ✅ preview 计数来自上游 + 按 2000 分批（2500 词 → `[2000, 500]`）+ 非法 `book_id` 不先花上游调用
3. ✅ start 分批：450 词 → `[200, 200, 50]`，payload 逐字段透传（`words`/`bookName`/`skipCached`），
   分批总数与词数对齐、`batch_seq` 连续
4. ✅ 非管理员四个 ajax 端点 JSON 403（且门禁在任何上游调用之前）；页面路由 403；`book_id=abc` → 400
5. ✅ 上游闸门文案经 `progress.lastError` 原样到达浏览器（发布在后台线程，不能断在 start 响应码上）
6. ✅ 同书活动 job 30 分钟内复用（且不额外发探针）；`updated_at` 拨回 31 分钟即判僵尸、新建批次
7. ✅ 进度口径：数字来自 `cached-check` 覆盖率；**入队后才被判非词形的词不算覆盖**（防提前 100%）；
   批次满覆盖后不再被探（探针是一趟索引扫描）
8. ✅ 取消：`no_publish` 桩给静态现场 → job `CANCELED`、未发布批次落 `SKIPPED`；他人批次不可读（403）
9. ✅ 模板：锚点齐全、`wd-start` 初始 disabled、`POLL_MS = 30000` 钉死、msgid↔po 一致、
   JS 无裸 `_()`、**相邻重复行守卫**（R113 事故）、**无 `.innerHTML =` 赋值**（书名来自书库）
10. ✅ zh 真实渲染（含 `.mo` 已编译）：页面文案 9 项全中，且 `Start Backfill`/`To generate` 不得残留
11. ⏳ `pytest tests/` 全量：本次只跑开发态闸门（123 例：本文件 + R126/R77/R75/TTS/i18n 种子/
    重复行/导航/CSP/让位），全量留到用户显式提出正式发布时（AGENTS 两级单测闸门）
12. ⏳ 真机验收：需要一本真实英文书 + moon-well R188 已上线（本地无法验书库，见 `magicbook 本地验证边界`）

## 8. 上线顺序

1. **moon-well 先发**（R188 两端点 + 词形过滤，已提交两枚本地待推），否则 preview 的 `cached-check` 404；
2. magicbook 侧无新增环境变量（复用 `MOON_WELL_READING_URL`），需确认 magicbook 管理员映射到的
   moon-well userId 在 `ai.llm.task-manual-run.admin-user-ids` 白名单内（warm-publish-by-words 沿用它）；
3. 两仓同轮上线，避免面板半瘫。

## 9. 并发写避让

开工前 `git status --porcelain cps/ tests/` 必须为空；本轮 magicbook 代码面干净（仅 `requests.md`/`response.md`
被文档会话改动）。moon-well 侧避让 `moon-well-vocab-design`、`moon-well-word-detail-derivative-prompt` 两个驻留 worktree。
