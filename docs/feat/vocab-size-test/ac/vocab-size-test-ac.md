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
- AC-B2 answer：顺序推进（请求体必带 `seq`）；重发同一题号回放不重复计数；对**已 finished** 会话的重复提交=幂等回放库存报告（不是错误）；对他人/已作废/已超时会话返回 50302；`seq` 跳到前面返回 **50304**（前端据此重新对齐题号继续答，不丢会话）；`answer∉{0,1}` 拒绝。
  - ⚠️ 差异留痕（2026-10-05，US3 定稿）：原条把「对 finished 会话作答」归入 50302，实现按幂等回放处理（结果页刷新/网络重试要能拿回同一份报告）；50304 是从 50302 里新拆的码。业务错误统一 **HTTP 500 + `Result.code`** 出口，参数域错误才是 HTTP 400 + `code=400`——前端判读看 `code` 不看状态码。
- AC-B3 状态机路径：机器人三型用户（高/低/中词汇）分别命中 FINISH(CONVERGED)/FINISH(CEILINGED_LOW)/R6 补测形态；任一会话题量 ≤70。
- AC-B4 finish：报告字段齐全（estimatedSize/ciLow/ciHigh/capped/**bandResults**/addedToNotebook）；重复 finish 幂等回放；提前交卷时**累计答题 <6 题（一个完整探测组）返回 50303**。
  - ⚠️ 差异留痕（2026-10-05，US3 定稿）：原条写「0 题 finish 返回 50303」。后端门槛不是 0 题而是不足 `PROBE_SIZE=6` 题——不足一组时当前 band 通过率无可估样本，给出的区间宽到没有信息量（理由见 moon-well 主 LLD §6 与 us3 设计 §8）。
- AC-B5 落本：`addUnknown=true` 时不认识词出现在 `vocabulary_notebook`，hard_level 按「教学档位优先、缺档回落 band 映射」（`VocabTestParams.BAND_HARD_LEVEL`）；`false` 时零写入。
  - ⚠️ 差异留痕（2026-10-05，US3 交付后按源码校正，原条两处失实）：
    1. 映射方向按 `HardLevel` **枚举码序单调排**：band1–2→初中(1)、band3→高中(2)、band4→CET4(3)、band5→CET6(4)、**band6→托福(6)、band7→雅思(8)**、band8→GRE(9)。早期 D5 文案的「6→雅思、7→托福」是反的——生词判定按「词的档位 > 用户阈值」做数值比较，照文案映射会让 band7 的词比 band6 更容易被判「已掌握」，档位与频段单调性相反。
    2. 原条「已存在词不覆盖 familiarity」**与实现不符**：落本口径与 `VocabularyService.unknown` 一致（存在即把 `familiarity` 置 `UNKNOWN`、刷新 `last_study_time`）。也就是说测试里点「不认识」会把此前标过熟练的词打回生词本。防重复打回靠**每会话至多落本一次**（`notebook_added_at` 令牌，重复 finish 只回放报告不再写本）；这条语义需用户复核确认（见文末「待复核」）。
- AC-B6 history：仅本用户 finished 会话、≤10 条、时间倒序；超 30 分钟 active 会话在下一次 history/start 时转 abandoned。
- AC-B7 单测全绿（`mvn test`，corretto-21）；`ReadingVocabularyServiceTest`/`WordLevelCacheServiceTest` 既有用例无回归。

## C. magicbook 前端（US4）

> **本机验证边界（2026-10-05 定）**：US4 在本机只能验「代理层单测 + 无头 Chrome 视觉截图」。
> moon-well 的数据源由 Nacos 生产 `moon-well.yaml` 下发（本地起服务即连生产库 `magichouse`），
> 因此 **AC-C2/C3/C4/C5/C6 的运行时行为与 `tests/modules/15-vocab-test.sh` 都要等后端部署后执行**，
> 验收报告须逐条标注「本机未验证」，不得记为通过。AC-C8（zh 缺串）可由种子契约测试在本机守住。

- AC-C1 `/reading/settings` 渲染测试卡片；moon-well 不可达时档位区走 `load_error`、测试卡片静默降级为无历史态，页面不报错。
- AC-C2 完整答题流：Start → 浮层逐题（单词+英文例句，**屏上无任何中文释义**）→ 结果视图（估算大字、区间或 25,000+、8 行频段条形图、落本提示）→ Done 回卡片显示 Last result。
- AC-C3 键盘 ←/J、→/K、Esc 生效；IME composition 期间按键不触发（用中文输入法实测确认候选词回车/空格/方向键无串扰，对齐 R114 守卫口径）。
- AC-C4 断网重试：拔线提交 answer → 错误行出现 → 恢复后重试成功且不重复计题。
- AC-C5 Exit 直接回卡片；重进页面 Start 正常（旧会话已 abandoned，不阻塞）。
- AC-C6 `#vt-add-unknown` 勾选态 localStorage 记忆生效；取消勾选后 finish 零落本（配合 AC-B5）。
- AC-C7 视觉：两套主题下卡片/浮层/图表渲染正常，浮层继承宿主主题（无自造实色描边，遵守 UI 纪律）；截图存 `docs/temp` 并附验收报告。
- AC-C8 zh 翻译补全后切换语言无缺串。

### C-结果（US4 本机验收，2026-10-05）

| 条目 | 结论 | 佐证 |
| --- | --- | --- |
| AC-C1 | ✅ 本机通过 | `tests/test_vocab_test_proxy.py::test_page_renders_card_with_single_upstream_call`（首屏只拉 settings，卡片渲染）、`::test_card_survives_settings_load_failure`（settings 失败时走 `load_error`，`id="vt-root"` 仍在）、截图 `docs/temp/vt_us4_shots/vt_us4_fixture__idle.png` |
| AC-C2 完整答题流 | ⛔ **本机未验证** | 需后端在线（边界见上）。代码路径已按 US3 契约逐字段核对，夹具用同形状假响应拍到 asking/result 两态 |
| AC-C3 键盘 + IME | ⛔ **本机未验证**（IME 需真人中文输入法） | 键位与 `isComposing`/`keyCode 229` 判定已实现（`vocab-test.js`），夹具拍到键盘不参与的点击路径 |
| AC-C4 断网重试 | ⛔ **本机未验证**（真拔线） | 错误分支用 fetch 桩拍到：`vt_us4_fixture__error.png` / `..._blur__error.png`（词头保留、红色重试行、进度不清零） |
| AC-C5 Exit / 重进 | ⛔ **本机未验证** | Exit 走 `modal('hide')` + 状态机复位 `idle`，需真实会话才能验「旧会话 abandoned 不阻塞」 |
| AC-C6 勾选态记忆 + 零落本 | ⛔ **本机未验证**（落本在后端） | 勾选态 localStorage 读写在前端，但「取消勾选后零落本」要连库验，属 US5 |
| AC-C7 视觉（两套主题） | ✅ 本机通过（含两处缺陷修复） | 10 张截图（默认主题 + caliBlur × idle/asking/result/history/error）。**修 1**：`.vt-el[hidden]` 兜底——`block header` 排在 `bootstrap.min.css` 之后，自造 `display` 规则盖掉 normalize 的 `[hidden]`，导致隐藏态一加载就显示。**修 2**：浮层从自造 `.vt-scrim`+`.panel` 改为 bootstrap 原生 modal——caliBlur 的深色规则按组件类名下发，自造 panel 拿到「浅底白字」全不可读；并补 `#vt-overlay > .modal-dialog{margin-top:70px}`（`caliBlur.css:5491` 把上外边距改成 0，弹层被 60px 固定导航栏压住）。详见 us4 设计 §2.2 落地修订 |
| AC-C8 zh 无缺串 | ✅ 本机通过 | `pybabel compile` 无告警；脚本核对本特性 20 条新 msgid 空译文 0 条；`tests/test_i18n_seed_contract.py` 的 `JS_FILES` 已含 `vocab-test.js`（JS 取词必须走 seed，漏一条即红） |
| 回归 | ✅ | `pytest tests/ -q` → **325 passed**（含既有 reading-settings / i18n 种子 / 词汇本用例）；夹具生成器改名 `tests/vt_us4_dump_fixture.py`（不带 `test_` 前缀，不进自动收集，显式点名才跑） |

⚠️ 顺带记录一条**不属本特性**的既有主题缺陷（不修，留待单独议题）：caliBlur 下 `/reading/settings` 的两张 `.panel` 卡片是「浅色面板 + 深色主题控件」，`btn-primary`（既有的 Save、新增的 Start test）与 `text-muted` 历史行对比度不足。同页既有 Save 按钮同症状，属页面/主题级问题；本特性不自造配色打补丁，浮层因复用 modal 已随主题正确反色。

**独立交叉审查（2026-10-05）**：评审对本特性前端挑出 2 高 4 中，全部已修并逐条记入 us4 设计 §2.4——① 在途响应未作废：关闭浮层后迟到的 answer/finish 回包会把隐藏态重新点活（Start 按钮永久失效 / 键盘在不可见浮层里提交），加会话代数 `epoch` 判定丢弃；② 登录过期是 302→200+HTML，代理层看成成功，改按 `response.url` 命中 `/login` 即走跳登录；③ 后端中文 `message` 直接上屏（违反单语文案纪律），删掉 `messageOf`，文案一律 `window.mbT`；④ **50304** 复用码的第二种文案「该题正在提交，请重试」不含题号，原先无脑取数字会写坏 `seq`，改为解析不到题号就转成可重试；⑤ finish 遇 50302 无限重试，补回卡片态分支；⑥ `vtCsrfReloaded` 永不自复位，刷新一次后 CSRF 兜底失效。修完 `pytest tests/` 仍 **325 绿**，asking/result/error 三态 × 两主题共 6 张浮层截图重拍复核。评审另提两条经源码核对**不改**：`answer` 后端确为 `Integer@Min0@Max1`（前端 1/0 正确）、`StartResult` 三字段形状与 US3 一致。

## D. 端到端与回归（US5）

- AC-D1 生产发布顺序演练（主 LLD §10，**逐条执行清单见 moon-well `docs/feat/vocab-size-test/release/release-checklist.md`**）：DDL+数据 → moon-well → magicbook 前端；每步后旧功能可用（老前端对新后端无感，新前端对旧后端静默降级）。
- AC-D2 真实用户完整测试一次（browser-use + 用户登录，按项目数据访问纪律），结果数值与人工预期「量级相符」共识判定。
- AC-D3 阅读页划词/生词判定、难度档位保存回归无恙（重点：词表新增 2 万 `level_id=10` 哨兵行后判档行为不变——原文写「level-NULL」，与定稿的枚举哨兵方案不符，已校正）。
- AC-D4 ES `app-log-moon-well` 无本功能新增 ERROR（发版后观察 ≥1 天）。
- AC-D5 文档同步：moon-well 三级文档（L1 `docs/readme/vocabulary.md` 增补功能段 / L2 `docs/vocabulary/hld/hld.md` 增补测试接口契约 / L3 已就位）+ 本 AC 打钩归档。

## E. 完成定义

全部 A–D 打钩 + 佐证（截图、us1-report、ES 查询输出）齐备 → response.md（R116/R95）写入回应 → 按「提交≠推送」纪律单独确认 push（涉及发版触发自动上线）。

## F. 产品语义复核结论（US4 对账时暴露的两条，2026-10-05 全部定稿）

1. ~~**测试判「不认识」会把复习过的词打回生词本**~~ **✅ 已复核确认：维持现状（2026-10-05 用户拍板）**
   （AC-B5 校正项 2）：落本沿用 `VocabularyService.unknown` 的 upsert 口径，`familiarity` 一律置 `UNKNOWN`。
   已用「每会话至多落本一次」限制重复打回，但首次打回是设计内的。定夺理由：测试是**自评校准**场景，
   判「不认识」即视为生词，与阅读页点「不认识」同一口径，不改后端、不产生第二套生词语义。
2. **`addedToNotebook = 0` 与 `null` 在结果页都静默**（US4 §2.2，2026-10-05 已确认）：后端保留两种语义（0=执行了落本但本会话无生词，null=本次没执行），仅 UI 不区分。
