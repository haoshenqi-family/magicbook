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
| MB-11 R212 [体验] 入口层：登录页价值主张、新账号语言跟随浏览器、语言入口前置 | 用户故事 | — | 无 | **代码完成待真机验收**（2026-10-24）：交付项 1/3/4 已补齐并定向回归；交付项 2/5 已上线。R224 worktree `../magicbook-r224-close-out`，未 push |
| MB-12 R213 首页信息架构（汇总项） | 用户故事 | [MAGICBOOK-220](https://haoshenqi.pingcode.com/ship/ideas/) | [r213-home-ia/](./r213-home-ia/)（HLD/LLD/AC） | **A 除侧边栏分组外已上线 / B1–B5 已验收、B6 已开发待复验 / C 已开发待验收**（2026-10-24）。A 的侧边栏四组分组按用户 2026-10-24 拍板「本迭代不改，下个迭代再说」，本迭代以「除分组外已上线」结项（LLD §5 保留设计，不删不实现） |
| MB-13 R214 [体验] 书籍详情：简介/目录/难度/试读 + 整本任务代价面板 + 元数据修正 | 用户故事 | MAGICBOOK-221 | [r214-book-detail/](./r214-book-detail/)（HLD/LLD/AC **定稿** 2026-10-23） | **A 已上线**（push 040b627b）+ **A 验收缺陷 R218 已修**（书架内书籍 `/book/<id>` 500，88ba3626/8643f8fe）；**B 已合入 develop**（简介/目录/试读，f10fd755+3a52c102，2026-10-23）；**C 开发完成**（2026-10-24：estimate + `/ajax/whole-book-estimate` + 面板 partial/JS，全量 804 tests 绿；待真机验收）。R237 部署重启后 worker 失联的恢复入口已补并上线：`canResume` + 进度条「继续」调用 retry（LLD §17，实现 `b48a29ed` / 部署 `a2a1e88f`，待真机验收）。R246 修复进度条任务类型标题为空（LLD §18，`fix/r246-wholebook-progress-label`，待验收）。R247 修复归档书内容速览误报 `book is unavailable`（LLD §19，`fix/r247-archived-insight`，待验收）。R248 修复进度条挂到书架/书卡弹层的问题，改为仅在完整详情页整本任务区域显示（LLD §20，`fix/r248-progress-detail-only`，待验收）。R249 修复整本朗读 worker 与请求线程共享 `ub.session` 导致 `ResourceClosedError`、批次停在进行中的问题（LLD §21，`fix/r249-tts-worker-session`）；生产 book 145 已续跑至 `1348/1348 COMPLETED`，ES/MinIO 均 1348/1348，待用户验收。 |
| MB-14 R215 [体验] 阅读器与 AI 伴读面板：控件可见性、面板可停靠、状态反馈、翻译重排 | 用户故事 | [MAGICBOOK-222](https://haoshenqi.pingcode.com/ship/ideas/b4haUEuv) | [r215-reader-ai-panel/](./r215-reader-ai-panel/)（HLD/LLD/AC **定稿** 2026-10-23） | **已开发待验收**（2026-10-23，worktree `../magicbook-r215-reader-ai-panel`，分支 `feat/r215-reader-ai-panel`；全量 727 tests 绿，已推 develop 触发上线） |
| MB-15 R216 [体验] 引导收敛 + /me 偏好页 + 难度入口前置 + 成就占位 + 伙伴 IP 风险登记 | 用户故事 | [MAGICBOOK-223](https://haoshenqi.pingcode.com/ship/ideas/) | [r216-onboarding-prefs/lld.md](./r216-onboarding-prefs/lld.md) | **已验收完成**（2026-10-23 用户确认真人跨设备验收通过；magicbook develop `634a24c6` + 台账 `5bdf32e4`、moon-well R208 develop `e03afbe` + 台账 `6bcfed6`；全量 808 / 1504 双绿；PJM MB-15 与 Ship MAGICBOOK-223 均流转「已完成」；两仓 worktree 按闸门清理） |
| MB-16 R213-A 导航与外壳：侧边栏分组 / chips 文字 / 卡片徽标 / 搜索合并 / 移动底部导航 | 任务 | 同上 | [r213-home-ia/lld.md](./r213-home-ia/lld.md) §5–§6 | **除侧边栏分组外已上线**（2026-10-23，`05587241`；chips 文字 / 格式徽标 / 搜索合并 / 移动底栏 / 裁切修复 + `3c2c6a6d` 高级搜索「阅读状态」四态化）。**侧边栏四组分组：用户 2026-10-24 拍板「本迭代不改，下个迭代再说」**，本迭代结项不实现；LLD §5 设计保留，`Shelf.kind` 判定留待下迭代开工时拍板（HLD §7.1） |
| MB-17 R213-B 继续阅读：`reading_progress` 表 + 进度回传 + 首页模块 | 任务 | 同上 | [r213-home-ia/lld.md](./r213-home-ia/lld.md) §1–§3 | **B1–B5 已验收**（2026-10-23 用户真机确认「继续阅读可以了」；代码 `0dccef16`/`420a6c48` 已上线）；**B6 进度总开关已补开发，待复验**（2026-10-24）：`config_reading_progress_enabled` + 迁移 + 端点/三种阅读器下线路径，待真机确认关闭后无库写入 |
| MB-18 R213-C 今日计划 + 分级推荐：新 `/home` 路由与首屏组装 | 任务 | 同上 | [r213-home-ia/hld.md](./r213-home-ia/hld.md) §3.4 / §7、[lld.md](./r213-home-ia/lld.md) §4 | **已开发待验收**（2026-10-24，全量 `pytest tests/` 873 passed / 0 failed；worktree `../magicbook-r213-home-ia`，分支 `feat/r213-home-ia`，基线 `origin/develop` `a3515312`）。落地：`/home` 四块首屏 + 落点判据单点 `cps/landing.py` + 开关 `config_home_landing`（含迁移）+ 卡片宏 `partials/_book_card.html`；跨仓改动为零（`createdAt`/`lastDraftNo` 既有即够）。待用户真机验收 G1/C2/C3 |
| MB-19 R221 AI 口语陪练语音优先：教练默认语音、用户录音转写后确认发送 | 用户故事 | 待建 | [r221-speaking-voice/lld.md](./r221-speaking-voice/lld.md) | **验收缺陷已修复，待验收**（2026-10-24，worktree `../magicbook-r221-speaking-voice`，分支 `feat/r221-speaking-voice`）。原语音优先功能已合入 develop；验收发现音频接口正常但 `blob:` 被口语页 CSP 拦截，已仅为 `/learning/speaking` 放行 `media-src 'self' blob:` 并补端点 + 真实路由守卫；发布态全量 `pytest tests/` 903 passed / 0 failed |
| MB-20 R217 注册后自动回 magicbook：邀请注册走 OIDC 上下文，enrollment 完成后静默授权回站并已登录 | 任务 | （关联 MAGICBOOK-11 / MAGICBOOK-219） | [r217-oidc-signup-return/lld.md](./r217-oidc-signup-return/lld.md) | **已开发待验收**（2026-10-23，worktree `../magicbook-r217-oidc-signup-return`，分支 `feat/r217-oidc-signup-return`；新增 16 条守卫测试 + 相关回归 49 条全绿；现网端到端链路实测：flow 结束精确还原 `next` → authorize → Authentik 签发 code → 302 回 `/oidc/callback`） |
| MB-21 R225 注册跳转 / 普通账号阅读权限 / 品牌封面占位 | 缺陷 | 待建（挂 R219 / R211 / R214） | [r225-auth-reader-covers/lld.md](./r225-auth-reader-covers/lld.md) | **已上线待验收**（2026-10-25，开发 `890bc607`；worktree `../magicbook-r225-auth-reader-covers`，分支 `fix/r225-auth-reader-covers`；定向 90 passed，全量 961 passed；生产注册跳转与品牌封面已核验，存量读者需点名授权） |
| MB-14/R223 阅读器验收缺陷 R226 | 缺陷 | 待建（挂 MAGICBOOK-222 / R215 / R223 / R216） | [r226-reader-verify/lld.md](./r226-reader-verify/lld.md) | **开发中待验收**（2026-10-25，worktree `../magicbook-r226-reader-verify`，分支 `fix/r226-reader-verify`）：伙伴白圆底、幽灵「?」、批量翻译连续重排已修；420px AI 覆盖式抽屉维持既有拍板 |
| MB-22 R227 Buddy 语音：全站语音输入转写 + 每条回复手动朗读（复用口语陪练链路） | 用户故事 | 待建 | [r227-buddy-voice/lld.md](./r227-buddy-voice/lld.md) | **已上线、已收尾**（2026-10-25 上线 `cb198e00` + 补丁 `5497538a`，2026-10-26 清理 worktree/分支）：`learning-voice.js` 依赖降级全站复用；朗读走 Web Audio（不动 CSP）、分段 1800 字；计费拒绝带出上游 message；全量 972 passed |
| MB-23 R232 伴读面板不显示 token 用量（用量只在设置·积分看） | 用户故事 | 待建 | [r232-hide-token-usage/lld.md](./r232-hide-token-usage/lld.md) | **开发完成待验收**（2026-10-26，worktree `../magicbook-r232-hide-token-usage`，分支 `feat/r232-hide-token-usage`）：`final` 分支删 usage 渲染、保留会话 id 回传；记录侧（moon-well `total_tokens` 流水）零改动；新增 5 条守卫，定向 22 passed，全量 986 passed；push 闸门留用户 |
| moon-well R214 / magicbook R228 伴读 Agent Skills（消费侧） | 跨仓能力 | 无（后端主责 moon-well R214） | [r214-agent-skill/lld.md](./r214-agent-skill/lld.md) | **已上线，验收证据已补齐，待用户最终确认**（2026-10-26）：伴读可按需加载 MagicBook 全功能指南；magicbook 无代码改动，复用既有 `/ai/agent/*` 代理。新注册普通账号已验证权限、Skill、查词、记忆、批注、TTS 与当前用户积分；批注为段落共享边界。本仓 R214 仍为书籍详情 |
| MB-23 R233 AI 回复中的本站链接可点击并在新窗口打开 | 用户故事 | 待建 | [r233-ai-links/lld.md](./r233-ai-links/lld.md) | **已上线待验收**（2026-10-26，实现 `f68e39b3`，worktree `../magicbook-r233-ai-links`，分支 `feat/r233-ai-links`）：`renderMarkdown()` 支持站内 Markdown/裸路径/同源 URL，统一 `target="_blank" rel="noopener noreferrer"`；外部 URL、危险协议、围栏代码与 HTML 注入保持纯文本；新增 Node 真执行测试 13 条，定向回归 36 passed；生产 `/book/252` 真回复中 `/credits` 与 `[我的页面](/me)` 均点击打开新标签，目标页正常且无法取得源页面 opener |
| R223 修改意见 R234 悬浮球快捷动作：AI 对话恒第一位且不可删除（服务端不变量） | 修改意见 | 无（挂 R223，不建独立 idea） | [r234-buddy-qa-chat-first/lld.md](./r234-buddy-qa-chat-first/lld.md) | **已上线待验收**（2026-10-26，worktree `../magicbook-r234-buddy-qa-chat-first`，分支 `feat/r234-buddy-qa-chat-first`）：`_pin_chat_first()` 写入读回双归一，POST 数量按归一后 4–5 算，前端行为不变；守卫 +3，定向 26+50 passed |
| R238 全文单词详解预览卡死修复 + 后台预计算 | 缺陷 | 待建（挂 R176 全文单词详解） | [r238-word-detail-preview/lld.md](./r238-word-detail-preview/lld.md) | **已上线待验收**（2026-10-28，实现 `5bb6336e`，merge `9577c541`，build `c0f4f598` 于 14:33 部署成功；worktree `../magicbook-r238-word-detail-preview`，分支 `fix/r238-word-detail-preview`）：模板脚本移入 `block js`，修复所有书共有的 `$ is not defined`；预览改持久化快照 + 后台线程 + 页面轮询，READY 10 分钟复用、FAILED 60 秒退避；全量 1014 passed、定向 68 / 扩展 179 passed；生产已验 `book_id=145/50` 与快照复用 |
| R243 / R228 站内信邮件系统：伙伴信封、抽屉 Mail、独立邮件页 | 用户故事 | [MB-234 / tBWd4R5g](https://haoshenqi.pingcode.com/ship/ideas/tBWd4R5g) · [MB-20 / YOLhI0oR](https://haoshenqi.pingcode.com/pjm/workitems/YOLhI0oR) | [r243-mail-inbox/hld.md](./r243-mail-inbox/hld.md) · [lld.md](./r243-mail-inbox/lld.md) · [AC](./r243-mail-inbox/ac/acceptance.md) | **前后端已实现，待验收**（2026-10-29）：worktree `../magicbook-r243-mail-inbox`，分支 `feat/r243-mail-inbox`，合并 R244 `a241f287`；moon-well `81 tests`；magicbook 合并后定向 `137 passed`，另 R233 链接/阅读器结构 `19 passed`；部署顺序 moon-well R228 先、magicbook R243 后，当前未 push |
| R239 全文单词详解预览屈折词覆盖漏算 | 缺陷 | 承接 R238 / moon-well R226 | [r239-word-detail-inflection/lld.md](./r239-word-detail-inflection/lld.md) | **开发中待上游上线**：根因在 moon-well `cachedLookupKeys` 漏投影 `forms.type`；本仓仅更新 L2/L3/需求与验收口径，不改词形算法，待部署后 `force=true` 复核 book 145 |
| R241 整本能力缓存齐备标识 | 用户故事 | 待建 | [r241-cache-ready-badge/lld.md](./r241-cache-ready-badge/lld.md) | **开发完成待验收**（2026-10-29，worktree `../magicbook-r241-cache-ready-badge`，分支 `feat/r241-cache-ready-badge`）：详情页三枚分项小标 + 三项齐备「低成本学习」总标，整本面板页签同步「已缓存」；判定取三条整本链路台账（COMPLETED + 跑满 + 指纹/格式一致），零上游调用；新增 18 条守卫；moon-well 零改动 |
| R242 积分卡：购买、兑换与管理员发卡入口 | 用户故事 | [MB-233 / ahh6wJTz](https://haoshenqi.pingcode.com/ship/ideas/ahh6wJTz) | [2026-10-credit-card/](../2026-10-credit-card/credit-card/lld.md) | **已上线待验收**（2026-10-29）：九条代理 + 积分页兑换/购卡/已购卡密/复制 + 管理员发卡/批次/作废/导出；购卡收银台自动弹窗；卡密操作拆为复制卡密/复制并分享，`/credit-card/share` 使用说明页已发布（提交 `79261d2b`，fragment 携带卡密、不自动兑换，生产验证通过）。worktree `../magicbook-r242-credit-card` 保留待用户验收 |
| R250 管理员运营站内信：自由撰写、单发/群发、发送历史与整批撤回 | 用户故事 | 待建（跨仓 moon-well R230） | [r250-admin-mail/](./r250-admin-mail/)（HLD/LLD/AC） | **开发完成待验收**（2026-10-29）：`/admin/mail` + 五个 `/ajax/admin-mail/*` 代理 + 精确全体人数 + 5000 人上限 + 发送历史与整批撤回；用户侧复用 `/mail` 渲染 `ADMIN_ANNOUNCEMENT`。定向 `103 passed`。worktree `../magicbook-r250-admin-mail`，分支 `feat/r250-admin-mail`，未 push |

## 版本

- PJM 版本 `1.0`（Open）；迭代收尾时随发布流转 Published。

## 备注

- moon-well 侧不单独建迭代：作为后端跟随本项目，跨仓同源以 R 编号互链（R171/R172/R175/R118 均已交付上线）。
- R167 缺独立 L3（交付时未建）；是否补记由第二轮讨论定，不阻塞验收。
- 工作项编号两套写法同物：本表早旧行写的 `MAGICBOOK-N` 即 PingCode `MB-N`（2026-10-23 起新行统一用 MB-N）。
- 需求基线 `docs/product/library/requirements.md`（2026-10-23 建）：主仓份已含 R213+R214 两条；R211/R212/R215/R216 随各自设计阶段补齐，不静默滞留。`feat/r213-home-ia` worktree 里的早期副本只含 R213，合并按 union 对齐（勿整文件取一边）。
