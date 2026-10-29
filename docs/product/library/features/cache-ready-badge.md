# 整本能力缓存齐备标识（L3 实现说明）

> 建立：2026-10-29（R241）。读者是**要改这个标识的人**——这里只讲实现与边界；
> 读者视角的能力描述见 L1 [`product/readme/library.md`](../../readme/library.md)；
> 这一次的取舍与被否方案见 LLD
> [`project/iterations/1.0/r241-cache-ready-badge/lld.md`](../../../project/iterations/1.0/r241-cache-ready-badge/lld.md)。

## 1. 它是什么

书籍详情页（含书卡点开的详情弹层）上的一组小标：

| 标识 | 出现条件 | 悬浮说明 |
| --- | --- | --- |
| `低成本学习` | 三项缓存全部备齐 | 三层缓存都已备齐，学习这本书更省积分 |
| `整本翻译已缓存` | 该链路批次跑满 | 已备齐（n/m 段），命中缓存不额外计费 |
| `整本朗读已缓存` | 该链路批次跑满 | 音频已备齐（n/m 段），命中缓存按 1 积分/段计 |
| `全文详解已缓存` | 该链路批次跑满 | 已备齐（n/m 词），查词命中缓存不再生成 |

整本任务面板的三个页签在对应缓存备齐时也会挂「已缓存」小标（同一份快照）。

## 2. 判定数据源

**本仓三条整本链路的执行台账**，不实时探测 moon-well 缓存：

| 链路 | 表 | 终态 | 跑满判据 |
| --- | --- | --- | --- |
| 整本翻译 | `reading_translation_job` | `COMPLETED` | `completed_count >= total_count` |
| 整本朗读 | `reading_tts_job` | `COMPLETED` | `done_count >= total_count` |
| 全文单词详解 | `reading_word_detail_job` | `COMPLETED` | `covered_words >= target_words` |

四条同时成立的约束：`status == COMPLETED`、`total > 0`、
`book_fingerprint` 与当前文件一致、`book_format` 与展示格式一致。
更新的不满足行不会一票否决更早的满批——按 `created_at` 倒序找到第一条满足即命中。

实现：`cps/reading_insight/readiness.py::book_readiness(book_id, book_format)`，
返回 `{"translate": {"ready", "done", "total"}, "tts": {...}, "wordDetail": {...}, "all": bool}`。
调用点是 `cps/web.py::show_book`，注入 `entry.cache_readiness`。

## 3. 边界

- **不是实时探测**：缓存事后被上游清掉时标识会滞后。真正开跑仍以缓存实况为准
  （moon-well 段落缓存读失败按 miss 降级，下次会自愈）。
- **依赖台账终态收敛**：翻译与详解的 `COMPLETED` 只在整本任务面板/批量进度页轮询时
  由缓存懒回收推进（R78 起不做常驻轮询）；点完就关页面、之后不再打开的批次会一直
  不亮，直到下次有人打开该书面板。朗读链路由 worker 自己置 `COMPLETED`，不受影响。
- **只认本仓发起过的整本批次**：三项缓存完全由逐段翻译 / MagicLens 逐词查询积累的书不会亮；
  管理员对这类书跑一次整本任务即可（全部命中缓存，秒级完成）。
- **失败静默降级**：台账表缺失、库忙、文件不可读都只让标识缺席，绝不拦详情页。
  归档书的详情与内容速览可正常读取，因此已有完成批次且正文指纹一致时也能亮标；
  三个整本任务本身仍默认排除归档书（R247 只放宽内容速览取书，不改整本任务边界）。
- **详解计数口径**：台账分母 `target_words` 是「本次补缺词数」，标识悬停改用
  `distinct_words`（全书去重词数）表述，别把它读成「全书只有这么多词」。
- **不替代代价面板**：`/ajax/whole-book-estimate` 仍按需实时估算「现在还要花多少」；
  标识回答「以前是否已经备齐过」。两者口径不同且互补。
- **可见性**：已登录且有 `role_viewer()` 的读者都能看到（含普通读者）；
  三个整本入口仍只给管理员（R214 拍板①），两者门禁互不牵连。
- **性能**：详情页复用速览 payload 里已算好的正文指纹（`entry.insight["fingerprint"]`），
  不重复取书/stat；三条查询把「书 + 指纹 + 格式 + COMPLETED」全部下推到 SQL 并限 50 行。
- **新增链路时**：给 `readiness.KINDS` 与 `_counts()` 加分支，并同步详情页/面板模板与
  本文件的表格——漏一处只会静默少亮一个标识，不会报错。
