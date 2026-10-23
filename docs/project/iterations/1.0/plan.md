# 迭代计划 1.0（magicbook 项目）

> 对应 PingCode：项目 `magicbook`（scrum）· 迭代 `1.0`（2026-10-15 → 2026-10-30）· 版本 `1.0`。
> 本文件 2026-10-18 建立（设计阶段补落），是迭代工作项清单与状态权威源；PingCode 工作项与 Ship 需求互链见各行。

## 目标

1. learning 域三条前端接线（R167/R168/R170，后端均先期交付）完成真机验收闭环。
2. LLM 队列监控面板（R130）设计定稿并进入开发。
3. 书库整理收尾（R149 神奇树屋合集拆分的标签/书架/归档）。

## 工作项清单

| 工作项 | 类型 | Ship 需求 | 设计文档 | 状态（更新 2026-10-23） |
| --- | --- | --- | --- | --- |
| MAGICBOOK-1 R167 复习队列干扰项重做（前端） | 用户故事 | [MAGICBOOK-143 关联 R167（idea 3XFi78B4）](https://haoshenqi.pingcode.com/ship/ideas/3XFi78B4) | 无独立设计（实现随 moon-well R171 契约；记录见 `response-archive/response-R165-R173.md`） | 已上线待验收（a8b86438，已推 origin/develop，7 场景无头验证过） |
| MAGICBOOK-2 R168 写作工坊续写（前端） | 用户故事 | [idea AV3N5doZ](https://haoshenqi.pingcode.com/ship/ideas/AV3N5doZ) | L3：`_legacy/feat/learning-hub/design/us2-writing-resume-lld.md` | 已上线待验收（2a16f172 + 测试 208cfc39，2026-10-14 上线，505 全量绿） |
| MAGICBOOK-3 R170 伴读 TTS 播放接线 | 用户故事 | [idea GWzvblAX](https://haoshenqi.pingcode.com/ship/ideas/GWzvblAX) | L3：`_legacy/feat/ai-agent/design/magicbook-side-design.md` §R170 | 已上线待验收（67537f54，merge 19ade770，守卫测试钉住非计费端点） |
| MAGICBOOK-4 R130 LLM 队列监控面板 | 用户故事 | [idea i7iJ3gwo](https://haoshenqi.pingcode.com/ship/ideas/i7iJ3gwo) | [r130-llm-queue-monitor/](./r130-llm-queue-monitor/)（本迭代新增 HLD/LLD/AC 草案） | **已验收完成**（2026-10-19 用户验收通过；`37392cdd` 实现 + `db1590d4`/`e53125c7` 两轮 UI 改版 Tab 化，merge 至 `2fe16c8a` 已上线；worktree 已删） |
| MAGICBOOK-5 R149 神奇树屋合集拆分 28 本 | 任务 | [idea mPh6cT4k](https://haoshenqi.pingcode.com/ship/ideas/mPh6cT4k) | [r149-mth-collection-split/](./r149-mth-collection-split/)（收尾清单） | 拆分+导入已完成（2026-10-10，28 册在库）；剩标签/书架/合集处置/归档 |
| MAGICBOOK-6 R186 B6 判据③整本批次真机回归验收 | 任务 | （idea In progress） | — | 等用户真机验收，不在本轮设计范围 |
| MAGICBOOK-10 R211 [缺陷] OIDC 自助注册默认授予管理员权限 | 缺陷 | [MAGICBOOK-218（idea）](https://haoshenqi.pingcode.com/ship/ideas/) | [r211-oidc-admin-role/lld.md](./r211-oidc-admin-role/lld.md) | **已开发待验收**（2026-10-23，worktree `../magicbook-r211-oidc-admin-role`，分支 `fix/r211-oidc-admin-role`；P0 单独先上线） |
| MB-11 R212 [体验] 入口层：登录页价值主张、新账号语言跟随浏览器、语言入口前置 | 用户故事 | — | 无 | 打开（2026-10-23 PingCode） |
| MB-12 R213 [体验] 首页信息架构：继续阅读/今日计划/分级推荐 + 侧边栏分组 + 移动端底部导航 | 用户故事 | MAGICBOOK-220（Planned） | `r213-home-ia/`（设计文档当前在 worktree `../magicbook-r213-home-ia` 分支 `feat/r213-home-ia`，未合回） | 打开；子任务 MB-16 / MB-17（进行中）/ MB-18 |
| MB-13 R214 [体验] 书籍详情：简介/目录/难度/试读 + 整本任务代价面板 + 元数据修正 | 用户故事 | MAGICBOOK-221 | [r214-book-detail/](./r214-book-detail/)（HLD/LLD/AC **定稿** 2026-10-23） | **开发中**（2026-10-23 起，worktree `../magicbook-r214-book-detail`，分支 `feat/r214-book-detail`；子项 A 先行） |
| MB-14 R215 [体验] 阅读器与 AI 伴读面板：控件可见性、面板可停靠、状态反馈、翻译重排 | 用户故事 | — | 无 | 打开（2026-10-23 PingCode） |
| MB-15 R216 [体验] 引导收敛 + /me 偏好页 + 难度入口前置 + 成就占位 + 伙伴 IP 风险登记 | 用户故事 | — | 无 | 打开（2026-10-23 PingCode） |

## 版本

- PJM 版本 `1.0`（Open）；迭代收尾时随发布流转 Published。

## 备注

- moon-well 侧不单独建迭代：作为后端跟随本项目，跨仓同源以 R 编号互链（R171/R172/R175/R118 均已交付上线）。
- R167 缺独立 L3（交付时未建）；是否补记由第二轮讨论定，不阻塞验收。
- 工作项编号两套写法同物：本表早旧行写的 `MAGICBOOK-N` 即 PingCode `MB-N`（2026-10-23 起新行统一用 MB-N）。
- 需求基线 `docs/product/library/requirements.md` 主仓份已含 R213+R214 两条；`feat/r213-home-ia` worktree 里另有一份只含 R213 的副本，合并时按 union 对齐（勿整文件取一边）。
