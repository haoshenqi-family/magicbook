# Vocab-Size-Test 验收标准 (AC)

> 编号 R116（magicbook）/ R95（moon-well）。验收执行规则遵循 AGENTS.md 第 3 类任务：逐条验证、不跳过、不足则补信息；本文件在 US5 阶段逐条打钩并附佐证（截图/日志/SQL 输出）。
> 后端细节 AC 见 moon-well `docs/feat/vocab-size-test/design/us1|us2|us3-*.md` 各「测试/验证」节，本文为**端到端总验收**。

## A. 数据与词表（US1）

- AC-A1 `magicbook_word_level` 终态行数 ∈ [27k, 29k]；`freq_rank` 非空恰 25,000；`level_id` 非空行数 ≥ 原 18,345 中命中数（对账表见 us1-report）。
- AC-A2 `freq_rank` 非空词例句覆盖率 ≥ 99%；抽样 30 条例句人工核对通顺且含目标词 ≥ 28/30。
- AC-A3 锚点校准表已产出（每 level 中位/P25/P75），主 LLD D3 锚点文案已按数据复核并显式记录「维持/修订」决策。
- AC-A4 导入脚本二次重跑结果幂等（行数与逐列值不变，人工修正的例句不被覆盖）。

## B. 算法与 API（US2/US3，对 moon-well 直连验证）

- AC-B1 start：正常返回首题（band3 词）+ sessionId；二次 start 抢占，旧会话转 abandoned；缓存降级时返回 50301。
- AC-B2 answer：顺序推进；重发同一答案回放不重复计数；对 finished/他人会话作答返回 50302；`answer∉{0,1}` 拒绝。
- AC-B3 状态机路径：机器人三型用户（高/低/中词汇）分别命中 FINISH(CONVERGED)/FINISH(CEILINGED_LOW)/R6 补测形态；任一会话题量 ≤70。
- AC-B4 finish：报告字段齐全（estimatedSize/ciLow/ciHigh/capped/bandResult/addedToNotebook）；重复 finish 幂等回放；0 题 finish 返回 50303。
- AC-B5 落本：`addUnknown=true` 时不认识词出现在 `vocabulary_notebook`，hard_level 等于 deriveHardLevel 映射值（抽 3 词手工推演核对）；`false` 时零写入；已存在词不覆盖 familiarity。
- AC-B6 history：仅本用户 finished 会话、≤10 条、时间倒序；超 30 分钟 active 会话在下一次 history/start 时转 abandoned。
- AC-B7 单测全绿（`mvn test`，corretto-21）；`ReadingVocabularyServiceTest`/`WordLevelCacheServiceTest` 既有用例无回归。

## C. magicbook 前端（US4）

- AC-C1 `/reading/settings` 渲染测试卡片；moon-well 不可达时档位区走 `load_error`、测试卡片静默降级为无历史态，页面不报错。
- AC-C2 完整答题流：Start → 浮层逐题（单词+英文例句，**屏上无任何中文释义**）→ 结果视图（估算大字、区间或 25,000+、8 行频段条形图、落本提示）→ Done 回卡片显示 Last result。
- AC-C3 键盘 ←/J、→/K、Esc 生效；IME composition 期间按键不触发（用中文输入法实测确认候选词回车/空格/方向键无串扰，对齐 R114 守卫口径）。
- AC-C4 断网重试：拔线提交 answer → 错误行出现 → 恢复后重试成功且不重复计题。
- AC-C5 Exit 直接回卡片；重进页面 Start 正常（旧会话已 abandoned，不阻塞）。
- AC-C6 `#vt-add-unknown` 勾选态 localStorage 记忆生效；取消勾选后 finish 零落本（配合 AC-B5）。
- AC-C7 视觉：两套主题下卡片/浮层/图表渲染正常，浮层继承宿主主题（无自造实色描边，遵守 UI 纪律）；截图存 `docs/temp` 并附验收报告。
- AC-C8 zh 翻译补全后切换语言无缺串。

## D. 端到端与回归（US5）

- AC-D1 生产发布顺序演练（主 LLD §10）：DDL+数据 → moon-well → magicbook 前端；每步后旧功能可用（老前端对新后端无感，新前端对旧后端静默降级）。
- AC-D2 真实用户完整测试一次（browser-use + 用户登录，按项目数据访问纪律），结果数值与人工预期「量级相符」共识判定。
- AC-D3 阅读页划词/生词判定、难度档位保存回归无恙（重点：词表新增 2 万 level-NULL 行后判档行为不变）。
- AC-D4 ES `app-log-moon-well` 无本功能新增 ERROR（发版后观察 ≥1 天）。
- AC-D5 文档同步：moon-well 三级文档（L1 `docs/readme/vocabulary.md` 增补功能段 / L2 `docs/vocabulary/hld/hld.md` 增补测试接口契约 / L3 已就位）+ 本 AC 打钩归档。

## E. 完成定义

全部 A–D 打钩 + 佐证（截图、us1-report、ES 查询输出）齐备 → response.md（R116/R95）写入回应 → 按「提交≠推送」纪律单独确认 push（涉及发版触发自动上线）。
