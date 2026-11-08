# 迭代计划：2026-11 滚动复习（magicbook）

> 对应 PingCode：产品 `MAGICBOOK` / 迭代 `1.0`（载体待建，按「台账 + plan.md」降级规则承载）。
> R285 阶段不新建后端能力；R289 增量为正文升级，对端 moon-well R248 提供只读缓存批量端点。

## 目标

在不产生任何积分消耗的前提下，为已登录用户提供一个全站可见的被动复习入口：Buddy 悬浮球头顶定时轮播 SRS 到期词——R285 轮播基础信息，R289 升级为单词详情分页（每词「基本意思 + 1 个随机模块」、每页 ≤3 行，只用已缓存详解）。

## 工作项清单

| 工作项 | 类型 | Ship 需求 | 设计文档 | 状态（2026-11-08） |
| --- | --- | --- | --- | --- |
| R285 Buddy 头顶滚动复习气泡 | 用户故事 | 待建（挂 MAGICBOOK 产品） | [HLD](./r285-rolling-review/hld.md) · [LLD](./r285-rolling-review/lld.md) · [AC](./r285-rolling-review/ac/acceptance.md) | **开发完成待验收**（worktree `../magicbook-r285-rolling-review`，分支 `feat/r285-rolling-review`） |
| R289 滚动复习正文升级为单词详情分页轮播 | 用户故事（R285 增量） | 待建（挂 MAGICBOOK 产品） | [LLD](./r289-detail-pages/lld.md) | **开发完成待验收**（worktree `../magicbook-r289-review-detail-pages`，分支 `feat/r289-review-detail-pages`；对端 moon-well R248） |

## 依赖与边界

- R285 上游零改动：`GET /learning/srs/queue`、`GET /vocabulary/known/{word}` 均为既有端点；本仓 `cps/routes/*` 零改动。
- R289 新增一个**只读**薄代理 `POST /ajax/vocabulary/detail-cached-batch`（`routes/vocab.py`），对端 moon-well R248 `POST /vocabulary/detail/cached-batch`；详解缓存未命中的词不上游生成，前端回退 R285 简卡。
- 与 R243「不新增轮询 daemon」基线：本功能是产品明确批准的**页面内定时轮播**（8s，`pagehide` 清理），不是后端轮询或后台任务；队列与详情各只读一次。
- 与 R227「回复朗读不自动播放、按次计费」口径：本功能完全不出声、不调 TTS，不冲突。
- R289 不预热缺失详解（隐性计费未授权）；若未来要做，走 R188 全文详解预热的用户侧形态并另立需求。
