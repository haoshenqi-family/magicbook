# 迭代计划：2026-11 滚动复习（magicbook）

> 对应 PingCode：产品 `MAGICBOOK` / 迭代 `1.0`（载体待建，按「台账 + plan.md」降级规则承载）。
> 本迭代只含一个工作项，不新建后端能力。

## 目标

在不新增后端端点、不新增数据库表、不产生任何积分消耗的前提下，为已登录用户提供一个全站可见的被动复习入口：Buddy 悬浮球头顶定时轮播 SRS 到期词的基础信息。

## 工作项清单

| 工作项 | 类型 | Ship 需求 | 设计文档 | 状态（2026-11-06） |
| --- | --- | --- | --- | --- |
| R285 Buddy 头顶滚动复习气泡 | 用户故事 | 待建（挂 MAGICBOOK 产品） | [HLD](./r285-rolling-review/hld.md) · [LLD](./r285-rolling-review/lld.md) · [AC](./r285-rolling-review/ac/acceptance.md) | **开发完成待验收**（worktree `../magicbook-r285-rolling-review`，分支 `feat/r285-rolling-review`） |

## 依赖与边界

- 上游 moon-well 无需改动：`GET /learning/srs/queue`、`GET /vocabulary/known/{word}` 均为既有端点。
- 本仓 `cps/routes/*` 零改动；只改 `ai_chat_panel.html` / `ai_chat.js` / `ai_chat.css` / i18n 三方 / 文档 / 测试。
- 与 R243「不新增轮询 daemon」基线：本功能是产品明确批准的**页面内定时轮播**（8s，`pagehide` 清理），不是后端轮询或后台任务；队列只读一次。
- 与 R227「回复朗读不自动播放、按次计费」口径：本功能完全不出声、不调 TTS，不冲突。
