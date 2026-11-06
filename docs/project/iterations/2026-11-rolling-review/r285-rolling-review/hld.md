# HLD · R285 Buddy 头顶滚动复习气泡

> 状态：设计定稿（2026-11-06，用户两轮拍板后开发）
> 需求基线：`docs/product/companion/requirements.md` §6；LLD：[`lld.md`](./lld.md)；AC：[`ac/acceptance.md`](./ac/acceptance.md)

## 1. 问题与目标

用户希望在阅读之外也能被动地反复见到该复习的词：Buddy 悬浮球头顶定时出现一张词卡，自动往下滚，看到认识的可以划掉。上一轮核查确认：

- 用户原话里的「最近划词的单词详情」在库里没有可查询形态（`vocabulary_study_history` 只写不读、无倒序接口、无索引，划词/详解/扩展路径都不写入），**本轮不做查词记录**。
- 真正能回答「该复习哪些词」的是 `learning_review_schedule` + 既有 `GET /learning/srs/queue`。
- 用户说的「点击认识算复习」在代码里不成立：`GET /vocabulary/known/{word}` 只把调度行毕业，不写 `learning_answer_log`、不涨 x/20。已向用户说明，用户确认「复用已有 known/{word} 不用改」，语义收敛为「这条从轮播里移除」。

## 2. 拍板口径

| # | 结论 |
| --- | --- |
| 1 | **A**：取 SRS 到期队列（20 个，前端随机），不做查词记录、不新建表 |
| 2 | 点「认识」复用 `POST /ajax/reading-word-mark {unknown:false}` → `/vocabulary/known/{word}`，后端零改动 |
| 3 | 一段话 = `word + meaning + contextSentence`（队列 VO 现成字段），不取六板块详情 |
| 4 | 开关放气泡上、状态记本机 localStorage；节奏 8s，页面不可见/不活跃/伙伴隐藏时停，全站 |
| 5 | 不出声、不计费 |
| 6 | 只做被动展示，不改 SRS 排程、不计复习进度 |

## 3. 方案选型

| 备选 | 结论 | 理由 |
| --- | --- | --- |
| 新建「查词记录」表 + recent 端点 | **否决（本轮）** | 与 `vocabulary_study_history` 语义重复；且用户第 4 条已把词源改为到期队列 |
| 调 `/vocabulary/detail/{word}` 拿六板块 | **否决** | 缓存 miss 触发 LLM 生成（15~30s、计费），与「不出声、不计费」冲突；队列已带首义项与原句 |
| 组合 `known/{word}` + `/learning/srs/answer` | **否决** | 前者 `@Async AFTER_COMMIT` 与后者状态写会竞态，且越过「只做被动展示」 |
| 卡片挂进 `#ai-companion-fab-wrap` | **否决** | wrap 的 hover 快捷气泡会遮住卡片、卡片会抢走拖拽命中区 |
| 卡片挂 `#ai-companion-root`，fixed 跟随 FAB；只消费两个既有端点 | **采用** | 零后端改动、零计费、与既有 FAB 交互解耦 |

## 4. 组件与数据流

```
[登录页面] layout/read 模板
   └─ #ai-companion-root
        ├─ #ai-companion-fab-wrap（既有：FAB / 快捷气泡 / 角标 / 拖拽）
        ├─ #ai-companion-restore（既有）
        └─ #ai-companion-review（新增，fixed，位置按 FAB rect 算）
              │
              ├─ 初始化  ── GET /ajax/learning/srs/queue ──→ moon-well dueQueue
              │              （只读一次，Result.result → 洗牌 → 20 条）
              ├─ 8s tick ── 暂停条件判定 → 换下一条 → 纯文字重绘
              └─ 点「认识」── POST /ajax/reading-word-mark {unknown:false}
                             ──→ moon-well GET /vocabulary/known/{word}
                             ──→ 成功只改本地数组；失败保留词卡 + 显示上游 message
```

## 5. 风险与对策

| 风险 | 对策 |
| --- | --- |
| 自动播放/计费与 R227 口径冲突 | 本功能完全不调 TTS，无任何音频路径 |
| 与 R243「不新增定时器」基线冲突 | 产品明确批准的页面内轮播；`pagehide` 清理，队列只读一次，不新增后台任务或轮询 |
| 与 hover 快捷气泡 / 拖拽抢命中区 | 卡片移出 wrap，fixed 定位；快捷气泡展开时 CSS 让位 |
| 上游内容注入 | 所有服务端字段 `textContent`，不拼 HTML |
| 接口故障被当成「没有单词」 | `resp.ok` + `unwrapStrict` + 独立错误面板 + Retry，失败可见 |
| i18n 静默英文回退 | 新文案走 `t()`，seed / zh po / 编译 mo 三方齐全，测试钉住 |

## 6. 不做什么

语音播放、六板块详解、查词历史、生词高亮、跨设备开关同步、SRS 评分与排程修改、任何新端点/新表/新后台任务。
