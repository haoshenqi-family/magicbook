# R289 · 滚动复习正文升级为单词详情分页轮播

状态：**开发完成待验收**（2026-11-08；worktree `../magicbook-r289-review-detail-pages`，分支 `feat/r289-review-detail-pages`，merge 后驻留待验收）
占号：2026-11-08（magicbook `requests.md` #289，claim 提交 `7b748bc0`）
跨仓：对端 moon-well R248（`POST /vocabulary/detail/cached-batch` 只读缓存批量端点）

---

## 1. 需求来源（用户原话与拍板）

> 「滚动复习的功能，改为显示单词详情。但是每次只显示一部分，每次显示不超过3行」

两问拍板（2026-11-08）：

1. **数据来源**：只用**已缓存详解**（零计费零等待）；没缓存的词保持 R285 简卡。
   不现场生成（15~30s + 计费，等于推翻 R285 红线）、也不自动预热（隐性计费，未授权）。
2. **翻页节奏**：同词连翻多页（每 8s 一页、翻完换词），但**每词只展示「基本意思 +
   一个随机模块」**——用户原话「详情的所有模块不必要都展示，随机展示两个模块，
   基本意思+一个随机模块，比如词源，或者搭配等。避免每个词太长」。

## 2. 方案总览

```
队列拉到（R285 既有，20 词洗牌）
  └→ POST /ajax/vocabulary/detail-cached-batch {"words":[...]}   ← 本轮新增薄代理
       └→ moon-well R248 POST /vocabulary/detail/cached-batch     ← 只读缓存批量端点
            ├→ batchDetails()  单次 terms 批查（lemma 字段，R171 口径）
            └→ findCached()    未命中词逐词多路兜底（word/lemma/forms/词干）
  ← result: {归一词: WordDetailVO}（未命中词不出现）
前端 reviewDetailPages(detail)：
  基本意思（前 2 义项，每义项一页）+ 随机模块（≤2 页）→ 每词 ≤4 页
轮播：tick 先在词内翻页，翻完换词；页内容 CSS 硬钳 3 行
无缓存/接口失败 → 回退 R285 简卡（meaning+contextSentence+contextBook）
```

## 3. 本仓改动清单

| 文件 | 改动 |
| --- | --- |
| `cps/routes/vocab.py` | 新增 `POST /ajax/vocabulary/detail-cached-batch`（`@user_login_required`）：词表归一（trim/弯撇号/小写/去重/`_READING_WORD_RE` 白名单）→ 透传 moon-well R248；空/全非法词表本地短路返回 `{"success":true,"result":{}}` 不打上游；上限 50 与上游 `CACHE_BATCH_CAP` 同口径 |
| `cps/static/js/ai_chat.js` | R285 块内新增 `REVIEW_DETAILS_URL` + `review.pages`/`review.page` 状态 + 页装配（`reviewDetailPages`/`reviewAppendModulePages`/`reviewAppendEtymologyPages`）+ `reviewLoadDetails()`；`reviewTick` 改为「先翻页后换词」；`reviewRender` 双态（详情页/简卡）；`reviewAdvance`/`reviewMarkKnown` 页码归零 |
| `cps/templates/ai_chat_panel.html` | body 内加 `<div class="ai-review-detail" id="ai-review-detail">`（空时 `:empty` 隐藏） |
| `cps/static/css/ai_chat.css` | `.ai-review-detail`：`-webkit-line-clamp: 3` + `white-space: pre-line`（页内 `\n` 分行） |
| `cps/templates/i18n_seed.html` + `messages.po` + `.mo` | 新增 4 词条：Collocations/Word forms/Slang/Fun facts（Etymology/Synonyms/Antonyms 复用存量）；`pybabel compile -f` 重编译 |
| `tests/test_r285_rolling_review.py` | 禁区名单改为 `/vocabulary/detail/`（逐词路径形）+ `/ajax/reading-word-detail`；新增 `test_r289_detail_pages_only_show_a_slice_per_tick`（翻页优先于换词/页数上限/3 行钳制/失败回退）；`NEW_STRINGS` +4 |
| `tests/test_r289_detail_cached_batch_proxy.py` | 新文件 8 例：登录门槛/归一转发/非法词丢弃/上限 50/空表短路/503 透传 |

## 4. 关键设计决策

- **为什么逐词详解代理不可用**：`/ajax/reading-word-detail`（R123）缓存 miss 即现场生成
  （单次 21.6s 实测、按发起者计费）。滚动复习是无人操作的被动轮播，批量 20 词里每个
  miss 都是一次隐藏下单——所以新增语义钉死的 `detail-cached-batch`，与计费链路无公共
  前缀混淆，R285 守卫测试同步把两条计费路径钉进禁区。
- **为什么每词 ≤4 页**：8s/tick × 4 = 单词最多停 32s；六板块全上会到 60s+，轮播变成
  阅读任务（用户拍板「避免每个词太长」）。
- **3 行怎么保证**：页宽 280px ≈ 21 中文字/行 × 3 行 ≈ 63 字；词源按句切页（~60 字/页）
  之外的所有页结构都是「单义项/单搭配/单词组」，天然不超；CSS `line-clamp: 3` 是
  任何情况下的硬兜底。
- **详情失败为什么静默回退**：详情是增强层，卡片核心功能（轮播+认识）不依赖它；
  失败装进「全员简卡」是**设计好的降级形态**而非吞错（与「把故障伪装成数据不存在」
  的家族禁令不冲突——简卡本身就是完整有效的展示态），可观测性由代理端日志承担
  （`vocabulary detail cached batch` label）。
- **markError 语义微调**：R285 每 tick 清「认识」失败原因；R289 改为**换词才清**——
  错误属于词，翻它的下一页时仍应可见（M3「换词清因」口径不变）。

## 5. 上游契约（moon-well R248，权威 LLD 在对端仓）

`POST /vocabulary/detail/cached-batch` `{"words": [...]}` → `Result<Map<String, WordDetailVO>>`，
键 = 归一请求词（trim+lower），未命中词不出现；只读缓存，**绝不触发生成**；
单次上限 50。`isVariant` 键由双注解钉死（Jackson/fastjson2 两条序列化路径，契约测试钉）。

## 6. 测试与守卫

- 定向：`test_r285_rolling_review.py`(13) + `test_r289_detail_cached_batch_proxy.py`(8)
  + `test_i18n_seed_contract.py` + `test_vocab_test_proxy.py` 共 **52 passed**；
  相关面回归（R280 伴读/R244 动画/R227 语音/公共解包/learning 代理/CSP/词详解批量）
  共 **155 passed**。
- `node --check` 通过；`pybabel compile -f` 通过。
- 集成套件：moonwell `cases/moonwell/vocabulary.py` 新增 T1 语义用例
  （`mw-post-vocabulary-detail-cached-batch`，只读+信封+result 形制）；
  magicbook `mb_session_vocab_buddy.py` T1 写端点组新增空体 400 形制探针
  （`mb-post--ajax-vocabulary-detail-cached-batch`）；矩阵在 dev 部署后重生成
  （`gen_moonwell_matrix.py` / `scan_magicbook_routes.py`），`guard.py` 三向对账全绿。

## 7. 边界与不做

- 不做「详情模块手动切换」（随机定死在队列加载时，重洗靠换页/刷新）。
- 不做 TTS 朗读详情（R285「不出声」口径不变）。
- 不做 `isVariant` 角标与变体说明展示（分页正文不消费，字段仍在上游响应里）。
- 不预热缺失详解（隐性计费未授权；后续若要做应走 R188 全文详解预热的用户侧形态，另立需求）。
