# response 归档：R135–R137（2026-10-08 ~ 2026-10-09）

> 从 response.md 原样搬移（2026-10-10 R147 写入触发轮转；R145/R146 两次写入均超窗未轮转，本条一并补账）。只搬移原文，未总结、未改写、未改编号。

## 2026-10-08（R135 面板「重放失败」操作指引）

### R135（管理页面如何做「可重放失败 8308」）

- **回应**：纯操作/机制问答，零代码改动。那行概览「待处理任务 0 · 可重放失败 8308 · 服务端上限 4 / 5000」来自 R126 `/llm-tasks` 面板顶部（数据源 moon-well `/llm/task/run/options`）：
  - **语义**：可重放失败 = `status='FAILED' AND started_at IS NULL`（`countReplayableFailed`，全队列口径、不随 caller 下拉变化）——从未真正调用过模型的失败行（R109 类外部 worker 网络失败天然属此类），重放**不重复计费**；并发上限 4、单批上限 5000 来自 `LlmTaskManualRunProperties`。
  - **操作**：面板选 provider + model（切 provider 清空模型名）→ caller 下拉可筛只重放某发布方（留空=全队列）→ 并发 ≤4、本批上限 ≤5000 → **勾选「重放失败」** → 开始执行（二次确认）。认领逻辑 PENDING 优先、排空后才取可重放 FAILED 且不混批（`LlmTaskManualRunService.claimCandidates`）；当前待处理=0，开跑即直接进入失败重放。
  - **批次规划**：单批硬上限 5000 < 8308 ⇒ 至少两批（5000 + ~3308），第一批跑满自动停，看进度表「队列剩余」归零后再开第二批；R109 实测吞吐 110–335 条/小时 ⇒ 8308 条约 25–75 小时，可中途「停止」（已发起的调用跑完、未开始的退回队列），进度以服务端 `accepted_by=runId` group by 为准，刷新/重启页面不失真。
  - **注意事项**：① 手动批次不扣管理员积分但真实消耗模型配额；② 大批重放前先确认网络/网关已恢复（R109 教训：DNS 抖动 9 分半烧穿 7,596 条），建议先小批量探针；③ started_at 非空的失败（超时/内容过滤等真调用过的行）不在这 8308 内、也不能走此路，其恢复要等 R130 监控面板的 republish-failed（新行 + retriedFrom，设计已写未实现）。
- **窗口补账**：本条写入触发「超 10 立即搬移」，R120/R122/R123/R124/R125×2 六条原样搬入 `response-archive/response-R120-R125.md`（含 R134 登记的欠账），窗口恢复为 R126 起最近 10 个 request。
- **总结**：requests.md 占号 R135；response.md 本条 + 归档搬移；冲突记录：无。

## 2026-10-09（R137：学习页三题型题干改造 + 部署网络事故处置）

- **背景**：R132 的 B3 页面已上线但三题型不可作答（CHOOSE 变「选出它自己」、RECALL 先亮词、SPELL 无 UI 死卡）——根因是 moon-well 队列接口无释义字段，词面即答案。本条与 moon-well R127（队列补 meaning）配套。
- **交付**（commit `841bb589` + 补丁 `16c9e5c2`，均已上线并验收）：
  - **题干机制**：有释义时统一「看释义作答」——CHOOSE 释义四选一（藏词面防泄题）/ RECALL 看义回忆（揭示亮词+语境）/ SPELL 看义拼写（输入+回车判定，归一口径与服务端 normalize 一致：trim/小写/弯撇号），判后亮词面与语境卡、错拼标红附正确拼写。
  - **双降级**：CHOOSE 无干扰项 → RECALL（服务端契约）；**无释义（详解缓存未命中，当前 19/20）→ SELF 亮词自评**（Anki 基础模式），任何卡片保底可答；缓存随划词自然增长后自动升级完整题型。
  - **i18n**：seed+po 新增 4 词条重编 zh mo；test_learning_proxy DOM 断言锁定 ln-stem/ln-spell 契约；22+6 用例绿。
  - **L1 补账**：docs/readme/learning.md 新建 + readme.md 模块表加行（R132 漏建）。
- **部署网络事故**（本次发版被堵 40 分钟的根因）：fnOS 默认网关指向 192.168.31.11（Ubuntu），全部外网经 sing-box 透明代理 → naive(12811) → HK 节点 `hk.haoshenqi.top`；naive 裸进程 73 天无 systemd，H2 连接腐烂（ERR_CONNECTION_CLOSED）致 fnOS 全外网中断（ACR/docker login、GitHub、DashScope 全超时）。**处置：原样重启两个 naive 实例恢复**（fnOS→ACR 0/8→3/8，节点仍劣化）；magicbook 构建在 acr-login 三连败两次后由手动重跑第 2 次通过（16c9e5c，15:03 部署 healthy）。
- **遗留建议**（需用户决策，未擅动）：① HK 节点劣化是 fnOS 全仓构建链的单点，建议在 sing-box 路由把国内目标（registry.cn-hangzhou.aliyuncs.com 等）分流 DIRECT，摆脱对代理节点的无谓依赖；② naive 无进程守护，建议补 systemd 单元；③ 释义覆盖率可考虑后续接 LLM 任务队列批量预热 SRS 词。
- **总结**：requests.md 占号 R137；本条为回应；冲突记录：无（moon-well R127 同源配套）。

## 2026-10-09（R136 分级书单核查与 37 本公版书入库）

**回应**：
- **核查**：书库原 84 本。与家族调研文档 `../docs/english-graded-reading-path-2026-10-08.md` 六阶书单对照，已命中：公版 9 本（爱丽丝/汤姆·索亚/绿野仙踪/彼得兔/野性的呼唤/丛林之书/时间机器/绿山墙安妮/小妇人）+ 版权书哈利波特 1–7、小王子 ×2、冰与火之歌 1–5，均跳过。
- **下载**：37 本缺失公版书从 Project Gutenberg 下载 EPUB，逐本 unzip CRC 校验通过（82MB）。
- **导入**：容器自带 calibredb 逐本 `add --tags "英文分级,阶N"`，入库为 book id 105–141（书库现 121 本）；标签、EPUB 格式行（37/37）、权限（999:999 与原库一致）全部验证；容器 healthy。
- **购买书单**：见对话回应——夏洛的网、Roald Dahl 系列、小屁孩日记、神奇树屋、纳尼亚 1、动物农场、老人与海、饥饿游戏、Percy Jackson、Wonder、Flipped、Holes、1984、追风筝的人、Life of Pi、Educated、魔戒、书虫分级读物等（哈利波特/小王子/冰与火已有，无需购买）。
- **踩坑记录**：① PG 对本机公网 IP 限流升级至直连完全拒绝（CODE=000），换 naive 代理（192.168.31.11:12811）解决；② 代理单响应有 10MiB 截断上限（哈克/傲慢与偏见/基督山均精准断在 10485760B），`curl -C -` 续传循环收敛（傲慢与偏见 24MB、哈克 15.6MB）；③ 基督山伯爵 epub3 图片版达 84.5MB，改用 noimages 纯文本版（1.26MB）；④ Great Big Treasury of Beatrix Potter #20049 在 PG 仅剩 rdf/封面、正文全部 404（疑似下架），且彼得兔 #14838 已在库，放弃；⑤ `calibredb` 无 `count` 子命令致脚本尾段 chown/清理未跑（无实害，已手动验证+清理）。
- **总结**：requests.md 占号 R136 并以本条回应；冲突记录：无（R137/R138 为并行会话正常顺延，非撞号）。
