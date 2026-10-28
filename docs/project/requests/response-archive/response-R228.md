## 2026-10-25（R228：moon-well R214 伴读 Agent Skills 的 magicbook 消费侧说明）

### R228（承接 moon-well R214；用户：「把magic book 所有的功能 总结一下，做成一个skill 给 AI伴读的agent使用。先判断AI伴读的agent 是否支持skill」）

- **任务定位**：跨仓消费说明，magicbook **零代码改动**。后端主责 moon-well R214；本仓 R214 已被“书籍详情”占用，故消费侧顺延占 **R228**，不覆盖既有编号。
- **支持判断**：原 AI 伴读 Agent **不支持 Codex / Claude 原生 Skill**；它是 moon-well 内有界工具循环 + `AgentToolRegistry` 白名单 + Nacos 提示词。直接放 `SKILL.md` 不会生效，因此 moon-well R214 实现的是产品内只读、无脚本、渐进披露的 Skill 机制。
- **消费侧交付**：`companion` L1 说明伴读可按需加载 MagicBook 全功能指南并强调不扩权；`companion/requirements.md` 记录 moon-well R214 / magicbook R228；`iterations/1.0/r214-agent-skill/lld.md` 写明真实页面路径、不可执行动作、失败退化与验收清单；迭代 `plan.md` 增跨仓工作项。
- **用户可见范围**：涉及阅读、翻译、查词、词汇、学习计划、朗读、积分或伙伴的问题，助手可先取指南再给具体页面/操作；指南按需读取、不占每轮上下文；不会因此获得点按钮、改设置、下单、启动整本任务或管用户的新权限。
- **不变量**：不改前端模板、不改 `/ai/agent/*` 代理、不改 SSE/会话/消息结构、不改工具白名单或写确认门配置；moon-well 关闭 Skill 或白名单未放行时，magicbook 无需变化。
- **验收（2026-10-26 生产真机）**：① 每日学习回答覆盖当前八项（写作、口语、复述 4-3-2、计时重读、听写、复习队列、Word Story、选书难度匹配），并给出 `/learning` 及各活动入口；② 改难度 / 买积分 / 启动整本翻译均拒绝代执行，给出 `/reading/settings`、`/credits`、书籍详情页真实路线，轨迹无写工具；③ 价格、倍率和活动结束时间明确以页面为准，未编造数值；④ 普通寒暄未加载 Skill。新词查询与 TTS 首次 miss 3 积分、第二次命中 1 积分也已实测。
- **新注册普通账号补测**：`r214probe-20261026-6457`（moon-well userId 15）的 `/admin` 404、`/admin/user/1` 403、`/shelf/create` 可访问、下载按钮显示未开通；每日学习加载正文与参考，寒暄不加载，查词走 `read_skill` + `lookup_word`，记忆初始为空、明确要求后 `save_memory ✓`，书 252 批注写入并由 `list_annotations` 回读成功。
- **TTS / 积分补测**：新文本首次提示本次 3 积分、二次缓存命中 1 积分；账本 `15:07:27 reading-tts -3`、`15:07:57 reading-tts -1`（此前 181 字符段另有 `13:58:41 -3`、`14:00:41 -1`）。赠送 10000、余额 7972、账本累计 2028；分组 `ai-agent-step` 1840/40 次、`ai-agent-memory` 180/18 次、`reading-tts` 8/4 次，证明 Skill、function call 与 Agent 内部调用均消耗当前登录用户积分。
- **隔离与边界（如实）**：会话与长期记忆按用户隔离成立（userId 15 有 3 个会话、4 条记忆；其他用户 24 个会话、8 条记忆；带唯一标记的 2 条记忆只属于 userId 15）；批注按既有设计为段落级共享，`ReadingAnnotationService.listByParagraph()` 不按 `userId` 过滤，不能写成私有隔离。生产写确认门为 `false`，写工具真实成功；`requireConfirm()` 只影响前端醒目样式，不是执行确认。
- **验收结果**：TTS 计费文案 GUI 补测通过；会话/长期记忆用户隔离通过；批注段落共享作为既有设计边界单独列明；当前用户积分对账通过。生产写工具真实成功，不能写成“被确认门拦截”。未发现 Skill 新增权限、系统身份调用或隐藏接口路径。
- **能力与计费边界**：生产白名单共 10 项，只有 `add_annotation` / `save_memory` 两个写工具；所有业务工具使用当前登录用户的真实能力、`UserContext` 与积分链路，不注入系统身份，也不提供脚本、任意文件或未注册接口。
- **上线与台账**：moon-well 代码提交 `05ed7fd` 已推送 `origin/develop` 并部署，生产健康 `UP`；验收文档 `f0bafad` 为 docs-only。正式发布态全量 **1559 tests / 0 failures / 0 errors / 0 skipped**。本仓 R228 为 docs-only，无代码 worktree；moon-well 原 worktree `../moon-well-r214-agent-skill` 与分支 `feat/r214-agent-skill` 已不存在，旧驻留记录不破坏性重建。
- **窗口**：写入前 10 节；按“写入即检查”把最早 R213-C 整节原样搬至 `response-archive/response-R213-C.md` 并登记索引，窗口保持 10。
