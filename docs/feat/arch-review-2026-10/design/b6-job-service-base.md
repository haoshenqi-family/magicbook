# B6 · JobServiceBase 模板方法（整本批次三胞胎去重）· L3 交付记录

**状态**：已合入本地 develop（R186，2026-10-16），**待用户真机批次回归**（判据③）；未推送。
**需求**：magicbook requests R186 ｜ **任务清单**：`refactor-items.md` §B6 ｜ **对端**：无（纯本仓重构）

## 1. 现状（改前实测）

| 文件 | 行数 | 说明 |
| --- | --- | --- |
| `cps/reading_translation/service.py` | 547（代码 371） | 整本翻译（R75/R77/R78） |
| `cps/reading_tts/service.py` | 435（代码 305） | 整本朗读预生成（R166/R169） |
| `cps/reading_word_detail/service.py` | 396（代码 256） | 全文单词详解（R176） |

评审报告登记的是「翻译 ↔ 朗读」双胞胎，实测**实际是三胞胎**：R166 的设计文档自己写明
「镜像 `WholeBookTranslationService` 骨架」，R176 又照抄一次。逐字比对结果：

- `_book_file` / `_fingerprint`：三份**完全相同**；`_ensure_tables` 三份只差两张表名；
- 「按 (用户, 书, 正文指纹) 取最新未终态批次」的复用查询：三份同形；
- 30 分钟僵尸判定 + 关闭：三份同语义，`ZOMBIE_MINUTES=30` 两处常量 + 四处内联表达式；
- `ACTIVE_STATUSES` 两份完全相同（朗读刻意少一个 PENDING）；
- 「按 id + 属主取批次并抛各自文案」：翻译三处、详解两处，同一 shape。

风险不是推测：R169 的整本朗读批次事故就是「双胞胎侧改一处漏一处」的形态。

## 2. 抽取边界（收了什么，没收什么）

新增 `cps/reading_job/service_base.py`（191 行，其中代码 87 / 说明 104）：

| 骨架成员 | 来源 | 三个调用方 |
| --- | --- | --- |
| `_ensure_tables`（按 `job_model`/`item_model` 建表） | 三份合一 | 全部 |
| `_book_file` / `_fingerprint` | 三份合一 | 全部 |
| `_find_active_job` | 三份合一 | 全部 |
| `_is_stale`（阈值 `ZOMBIE_MINUTES` 单一事实源） | 翻译内联 ×2 + 详解内联 ×1 + 朗读 `_is_stalled` | 全部 |
| `_close_as_zombie` | 三份合一 | 全部 |
| `_own_job` + `missing_job_error` | 翻译 ×3 处 + 详解 `_own_job` | 翻译、详解（朗读不筛属主，见 §4） |
| `_pending_count` / `_needs_worker` / `_revive_running` / `_spawn_worker` / `_worker_guarded` | R169 自愈机制（原在朗读） | 朗读 |
| `ACTIVE_STATUSES` | 两份相同合一 | 翻译、详解（朗读用 models 里的那份） |

**刻意没做**（做了就是行为变更，不属于去重重构）：

1. **进度口径**：三家返回字典各异（`totalCount/cachedCount/…` vs `total/done/failed/voice/style` vs
   `targetWords/coveredWords/coverage`），强行统一会改前端契约。
2. **item 状态机**：翻译 PENDING/PUBLISHED/ACCEPTED/COMPLETED/FAILED/SKIPPED，朗读 PENDING/DONE/FAILED，
   详解 PENDING/PUBLISHED/DONE/SKIPPED。骨架只在 `_pending_count` 上用「PENDING」这一共同起点。
3. **给翻译/详解也套花名册**：这两家的发布线程靠「幂等复用通道 + 新鲜度拦截」防重复，且重复发布
   被 moon-well 侧缓存/在途跳过兜底；套上花名册会把「连点两次」的现有语义从「再起一条」改成
   「静默跳过」。判据①要求行为不变，因此只在朗读侧使用这套骨架，骨架本身保持三家可复用。
4. **朗读的按属主过滤**：见 §4 的待决事实。

## 3. 验收

- **判据①（既有测试全绿，含 R169 批次自愈用例）**：全量 `pytest tests/` **601 passed**
  （基线 590 + 本批新增 11 例守卫），`test_reading_tts_service.py` 的
  `test_spawn_worker_is_atomic_and_never_double_spawns`、
  `test_retry_spawns_when_no_live_worker_and_pending`、
  `test_retry_does_not_double_spawn_while_worker_is_live`、
  `test_start_still_spawns_worker_when_preselect_crashes` 全部原样通过。
- **判据②（重复骨架归一）**：三个 service 的代码行由 371/305/256 降到 337/244/222，
  归一出的 87 行骨架只有一份实现。新增 `tests/test_job_service_base.py`（11 例）钉住：
  骨架方法不得在子类里长回第二份、同一原语三家只有一份实现、类属性必须显式填、
  僵尸阈值单一事实源、三家「查无批次」文案逐字不变、`_needs_worker` 的三条边界。
  **反向变异已验**：给 `WholeBookTtsService` 重新塞一个 `_fingerprint` 后守卫 2 例转红，
  恢复后逐字节一致。
- **判据③（整本翻译与整本朗读各跑一轮真机批次回归）**：**未验**——本机无 calibre 书库
  （`/`、`/book/<id>`、`/read/...` 一律 500），需要用户在线上各点一轮「整本译」与「整本朗读」。

测试桩的跟着代码走的改动（不是放水）：`calibre_db` / `config` / `threading.Thread` 三处
monkeypatch 的**打桩位置**随 `_book_file` 与线程创建移到骨架模块，断言一字未动。

## 4. 本轮实测到的待决事实（未在本批处置）

1. **整本朗读的批次 loader 不按属主过滤**：`cps/reading_tts/service.py` 的
   `get_progress`/`retry`/`cancel` 用 `query(ReadingTtsJob).get(job_id)`，而翻译与详解都是
   `filter_by(id=…, user_id=int(current_user.id))`。批次 id 是 uuid4 hex（不可枚举），
   路由又全部 `@admin_required`，所以现在打不到别人数据；但这条与另两家的口径不一致，
   补齐属于鉴权变更，另立需求做。
2. **两处日志措辞归一**：僵尸关闭行统一为 `<前缀> stale job <id> (book=… updated_at=…) closed as zombie`，
   由此丢掉两句尾巴——翻译的「; creating fresh batch」、朗读的「(no pending left)」；
   朗读的线程崩溃行由 `synth worker crashed` 变为 `worker crashed`。测试没有按这些字样断言，
   ES 侧按消息正文检索时需注意（`app-log-magicbook`）。
3. 骨架内部日志的 logger 名归到调用方模块（`job_log = log` 逐类注入），避免评审 M6 发现的
   「logger 名塌到基类」问题在 Python 侧重演。
