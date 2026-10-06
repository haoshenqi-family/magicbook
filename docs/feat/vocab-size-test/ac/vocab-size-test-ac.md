# Vocab-Size-Test 验收标准 (AC)

> 编号 R116（magicbook）/ R95（moon-well）；US1 词形返工续于 R121 / R99。验收执行规则遵循 AGENTS.md 第 3 类任务：逐条验证、不跳过、不足则补信息；本文件在 US5 阶段逐条打钩并附佐证（截图/日志/SQL 输出）。
> 后端细节 AC 见 moon-well `docs/feat/vocab-size-test/design/us1|us2|us3-*.md` 各「测试/验证」节，本文为**端到端总验收**。

## A. 数据与词表（US1）

- AC-A1 `magicbook_word_level` 终态行数 ∈ [27k, 29k]；`freq_rank` 非空恰 25,000；`level_id` 非空行数 ≥ 原 18,345 中命中数（对账表见 us1-report）。
  - ⚠️ 差异留痕（2026-10-05 复核；同日 A+B+ 词形返工后已按终态重算）：行数区间 **[27k, 29k] 失实，实态 31,668**，
    判据改为「= 25,000 秩词 + 未入秩应试长尾」。
    推导：25,000 秩词中 11,677 命中既有应试行（UPDATE）、13,323 新增哨兵行（INSERT），加 6,668 条未入秩长尾 = 31,668。
    原估按交集 ~9.9k（占应试行 54%）算，清洗定稿改成「Tatoeba 证词 AND 词典收录」后交集升到 11,591（63%），
    哨兵占比反降 → 总行数上抬（见 us1 设计 §6、us1-report §1）；返工换掉秩集 353 词后交集再升到 11,677（63.7%，
    三个百分比分母统一为既有应试行 18,345），总行数落定 31,668。**这不是导入过量**：本次独立复算
    `11,677 + 13,323 = 25,000` 精确闭合，无重复插入、无漏秩。
- AC-A2 `freq_rank` 非空词例句覆盖率 ≥ 99%；抽样 30 条例句人工核对通顺且含目标词 ≥ 28/30。
- AC-A3 锚点校准表已产出（每 level 中位/P25/P75），主 LLD D3 锚点文案已按数据复核并显式记录「维持/修订」决策。
- AC-A4 导入脚本二次重跑结果幂等（行数与逐列值不变，人工修正的例句不被覆盖）。

### A-结果（US1 彩排库复核；2026-10-05 A+B+ 返工重跑后的终态，替换同日早先版本）

> 复核方式：直连本地彩排容器 `vt-us1-mysql`(127.0.0.1:3399, 库 `magichouse`，预灌 2026-09-15 生产备份
> 18,345 行) **重新执行对账 SQL**，而不是照抄 us1-report 的快照数字。本轮下表数字是词形返工（下条）
> 全量重跑 attest→merge→sentences 之后的实测，与 us1-report §10 逐项吻合；返工前那版（31,754 / 23,985）已作废。

| 条目 | 结论 | 佐证（2026-10-05 实测） |
| --- | --- | --- |
| AC-A1 | ✅ 通过（区间判据已按实态修订，见上「差异留痕」） | `total=31668`、`ranked=25000`、`sentinel(level_id=10)=13323`、`exam_rows(level_id 0-9)=18345`（原行零删改）、`exam∩rank=11677`、`未入秩长尾=6668`、`MIN/MAX/DISTINCT(freq_rank)=1/25000/25000`（无空洞无重复）、`source_book='FrequencyWords_top25k'` 恰 13,323 行 |
| AC-A2 | ✅ **通过（生产终态实测 2026-10-06 17:28：`24,981/25,000 = 99.92%` ≥ 99%；后半判据换了口径——见本行末**） | **终局（同一条只读通道直算，17:28）**：`--apply` 已在生产执行完毕——762 句写入 → `24,986/25,000 = 99.94%`；3 条错义句（`AD`/`AIDS`/`I`）置 NULL 后以独立 manifest 重出 1 批（taskId 117382）3/3 合格写库，覆盖净不变；再采纳分层判读的「5 条不入库」（`ora`/`mou`/`nom`/`nss`/`def`）置 NULL ⇒ **终态 `24,981/25,000 = 99.924%`**，`no_sent` 恰 19 = 校验层拒 14 + 主动剔 5，`orphan_sent_on_nonranked` 仍 **0**，秩 1..25,000 无空洞。**过程留痕（17:02 那次只读复测）**：LLM 补漏**生成侧已跑完**——1,003 缺口先由 Tatoeba 免费重绑收回 **227** 词（生产只读复测：有例句 `24,224/25,000 = 96.90%`，非秩行带例句仍 0，秩 1..25,000 无空洞），剩 776 词走 `/llm/task` A 路（fnOS 常驻执行器 + zhipu/glm-5.3-flash，**不走 `NEW_API_KEY`、本机零凭据**）**39 批全部 COMPLETED → 762 句合格 / 14 拒**。`--apply` 已在生产同形态副本端到端演练：写 762 → **`24,986/25,000 = 99.94%` 过 ≥99% 闸**、幂等重跑 delta 0。执行与取证全文在 moon-well `design/us1-llm-gapfill-via-llm-task.md` §12/§13，命令与两道人工闸在 moon-well `release/release-checklist.md` §3.3 (d)。**原行文字**：秩词例句 `23,997/25,000 = 95.99%`（门槛 ≥99%）；缺口精确 1,003 词（4.01%，低于 5% 复核闸口）= `raw/llm-gap-words.txt`，需 `NEW_API_KEY` 跑 `us1_sentences_llm.py --apply`（先出抽检件、人工 ≥5% 通过再写库）。30 条例句抽检已脚本化：`moon-well .../sql/us1_audit_sample.py`（只读、分层取样、重跑同一份样本）产出底账 `raw/us1-audit-30.md`，机械层已代跑完（返工后 **30/30**；返工前 29/30，红的那条正是误绑的 `refuge`），人工只剩「通顺/义项」一栏。**跨版本可比性**：取样盐键没变，但秩集换了 353 词，样本随之重排，返工前那 30 条的人工结论不可累积到本版。**跨库可比性已证（2026-10-06）**：生产 23,997 条 `(freq_rank, example_sentence)` 按秩拼接的 MD5 与彩排库**完全相同**（`6aaccd21091f35f30f7539c5f1ca5cae`）⇒ 抽检所对的那批例句就是生产在用的那批，人工结论可直接累积。**抽检口径本轮已升级**：≥5% 均匀抽 40 条对「短词/专名/元语言」这类分层风险是**结构性盲区**（那 40 条检不出），改为分层红旗件判读 `raw/llm-sentence-audit-suspects.md`（并集 105/762 = 13.8%，全读；建议剔 5 条后写 757 条仍 `24,981/25,000 = 99.92%` 达标）。**后半判据归档口径**：原句「抽样 30 条人工核对通顺且含目标词 ≥ 28/30」已被**分层判读取代**（覆盖面 13.8% > 5%，且正对均匀抽样的结构性盲区）——机械层 30 条 30/30、`+es` 差集恒 0，人工那一栏落在 105 条红旗件上并经用户 17:2x「1 批准」点头收口（moon-well §12.6）；**没有单独再签一份 30 条的人工表**，归档按「替代口径」记，勿写成原判据逐条签字。 |
| AC-A3 | ✅ 通过 | us1-report **§11**（生产口径；§10 为彩排口径）八档锚点表 + 显式决策「偏移未超半档宽，band 区间与锚点文案**不修订**」；考研档样本 130（返工前 119），仍维持原锚点。⚠️ **锚点的 level 标签必须按生产读**：生产是 1/2/3/4/5/**6(托福 2,215,中位 15,171)**/**8(雅思 483,14,932)**/**9(GRE 1,805,17,162)**，彩排库把同一批词标成 7/6/8——`(n, median)` 元组集两边相同、仅标签位移，所以用彩排标签描述「level 1→8」在的生产语境下是失实的 |
| AC-A4 | ✅ 通过 | us1-report §3 记 3 轮全量重跑终态一致；本次复核补一条硬约束证据：`freq_rank IS NULL AND example_sentence IS NOT NULL` 行数 **= 0**（跌出秩集的脏例句已统一清空），且两个例句脚本的写库语句都带 `AND example_sentence IS NULL` → 人工修正不被覆盖。**返工新增前置纪律**：改词形规则后必须**先整列清空 `example_sentence` 再重跑** `us1_sentences.py`，否则 `IS NULL` 守卫会把旧误绑例句原样留在库里——「幂等」不等于「规则变更后自愈」（本轮整列清空后重跑，例句数才从返工前的 23,985 变成终态 23,997） |

**生产侧 A 段实测（2026-10-06 01:13–01:21，`magichouse@192.168.31.9:3306`，用户授权 ssh 取凭据）**：
上表那批数字原为**彩排库**实测，现已在**生产库**逐条复现，A 段可打「生产已落地」——
`total=31668 / ranked=25000 / sentinel=13323 / exam_rows=18345（原行零删改）/ exam∩rank=11677 /
未入秩长尾=6668 / MIN-MAX-DISTINCT=1/25000/25000 / 秩空洞=0 / 非秩残留例句=0 / idx_freq_rank=1`，
准入不变式 `sentinel=13323 short=0 no_evidence=0`，例句覆盖 `23997/25000=95.99%`（最长 101 字符）。
**出题分桶也已按生产直算**（`BAND_UPPER` + 「只装有例句的秩词」那条构建期过滤）：
`band1..8 = 991 / 979 / 971 / 1949 / 2922 / 3907 / 5793 / 6485`，与彩排库**逐档相同**
→ 「AC-A2 那 4% 缺口不阻塞出题」这条判据从按彩排推算升级为按生产直算，最小桶 971 ≫ 单档最多消耗 10 题。
**17:02 只读复测（同一通道，容器内展开口令）**：`total=31668 / ranked=25000 / DISTINCT(rank)=25000 /
非秩行带例句=0` **四项不变**，`有例句 23997 → 24224（95.99% → 96.90%）`——增量全部来自 227 词 Tatoeba 重绑；
上表逐档桶量是 23,997 时代快照，**17:12 直算现况** `band1..8 = 1000 / 999 / 1000 / 1995 / 2976 / 3942 / 5817 / 6495`
（合计 24,224；227 重绑把 band 1 补满到 1,000，最小桶变成 band 2 的 999），后续 `--apply` 只会让桶继续变大，
所以「最小桶 ≫ 单档最多消耗 10 题」
这条不阻塞出题的结论始终成立（逐 band 残余缺口实测：band 8 从 505 词 7.21% 降到 7 词 0.10%，见 moon-well §13.5）。
**终态直算（2026-10-06 17:26–17:28，补漏写库 + 5 条不入库之后，同一只读通道）**：
`band1..8 = 1000 / 1000 / 1000 / 2000 / 2998 / 3999 / 5995 / 6989`，合计 **24,981**（与覆盖率对账一致），
**最小桶 1,000**（band 1–3 已装满，band 5 起才有余量）——17:12 那组 999 的短板已被补满，
「单档最多消耗 10 题」的裕度从 99 倍升到 100 倍，逐档覆盖率 band 1–4 已 **100.00%**、最低 band 8 也 99.84%。
剩余 19 个无句词的档位分布（直算）：band 5 两个（`sakes`/`wah`）、band 6 一个（`chet`）、
band 7 五个（`christening`/`cliché`/`proclamation`/`pedigree`/`def`）、band 8 十一个
（`berk`/`nom`/`positioning`/`ora`/`mortem`/`mou`/`nss`/`veneration`/`annals`/`muss`/`contrition`）
⇒ **缺口全部压在长尾档**（band 5–8），band 1–4 满桶，对出题与估算无影响。
执行细节、备份（`~/vt-backup/magicbook_word_level-prod-20261006.sql.gz` 727,463 B，已回灌验证）与
「先预演再动手」的做法见 moon-well 发布清单 **§3.3**。三条必须记住的生产实况：

1. **`freq_rank` / `example_sentence` 两列不是本次建的**——`7c37816` 镜像启动时 Hibernate
   `ddl-auto: update` 已自动建好（列注释空、`example_sentence` 是 `varchar(255)` 而非 `us1_ddl.sql` 的 512）；
   merge 这次只补了缺失的 `idx_freq_rank`。**不加宽**（101 < 255，为省一次不可逆 ALTER），
   所以「先建列再灌数据」的顺序在生产上已被镜像启动提前完成，属既有事实、非本次动作。
2. **生产 `level_id ↔ level_name` 标注与彩排库位移**（雅思 711 行：生产 8 / 彩排 6；托福 4,491：生产 6 / 彩排 7；
   GRE 5,449：生产 9 / 彩排 8；生产无 level 7、彩排无 level 9），而**词集完全相同**——
   这就是 AC-A1「偏移只来自应试豁免集」的预期实测为**零**的原因（豁免集取全表 word，与 level 标注无关）。
   代价是 **AC-A3 的八档锚点表必须按生产标签读**（`(level, n, median)`：1/1971/1564、2/1846/5243、
   3/1629/7243、4/1598/11570、5/130/10896、6/2215/15171、8/483/14932、9/1805/17162；元组集与彩排一致，仅标签不同），
   **彩排库不得用于教学档位相关推理**。
3. **数据要等缓存重载才生效**：`WordLevelCacheService` 只有 `@PostConstruct` + 每日 04:00（**生产本地时间
   +08:00**）`@Scheduled`，无手工重载入口 → D 段端到端验收前要么等 **2026-10-07 04:00 +08:00**
   （= `2026-10-06T20:00Z`）、要么重启生产容器（需单独授权），否则 `testReady=false`，
   `/vocabulary/test/start` 只会返回 50301 降级。
   ✅ **本项已关闭（2026-10-06 02:41Z 实测）**：没有等到 04:00——并行会话 `02:38Z` 推 moon-well `develop`
   触发自动重建，容器启动重载缓存，ES 出现两条正文时刻 `10:39:15` / `10:41:40`（+08:00）的
   **`18345 level words, 25000 ranked words, 8 bands`** → 数据已进入读路径、`testReady=true`、50301 那堵墙消失。
   同刻复查 `app-log-moon-well` 近 45 分钟 ERROR 命中 0（AC-D4 观察窗从 `02:41Z` 起算，满 1 天 = 2026-10-07 02:41Z）。
   **已取证（2026-10-06 01:33–01:53，只读）**：库侧数字与 §11 逐项吻合，而 ES 里最近三次加载
   （`04:00:00` / `09:13:44` / `09:14:40`，均 +08:00）全是 `18345 level words, 0 ranked words, 0 bands`，
   时刻**全部早于导入落库 09:16–09:17** → 陈旧缓存属预期，**不是导入失败**；
   判据与取证口径见 moon-well 发布清单 **§3.4**（含「本文无后缀时刻一律 UTC」的时区纪律）。
   ⚠️ D 段核对生效时**不要按 ES `@timestamp` 排序取最新日志**：02:00Z 实测容器重建后 filebeat 会把旧日志
   按「读取时刻」重放（同一行索引两次，`@timestamp` 相差 16 小时），应按判据串
   `18345 level words, 25000 ranked words, 8 bands` 查命中、并用正文里的 `+08:00` 时刻定时序（现成命令在 §3.4 取证 4）。
   **两个数都要对**：生效后全表 31,668 行、其中 13,323 行是 `level_id=10` 哨兵，level 视图若从 18,345 跳到 3 万+
   就说明判档视图没排除哨兵（闸口没上线）→ 立刻停止验收并回报。导入前备份件实测全表恰 18,345 行，
   所以现在日志里的 `18345 level words` **还不能**当作排除逻辑已生效的证据（§3.4 取证 4 已收回该误判）。
   → **02:41Z 起这条限制解除**：加载行里 `25000 ranked words` 非零，证明该次加载晚于 01:16Z 的导入，
   而此时全表是 31,668 含 13,323 哨兵，`31,668 − 13,323 = 18,345` 与 level 视图精确对上 →
   **两个数一起看**才成立，单看 `18345` 任何一次陈旧加载都能冒充（这正是取证 4 收回误判的原因）。

- ✅ **抽检暴露的管线缺陷：已定夺并返工完毕（2026-10-05，选项 A + B+，彩排库全量重跑）**
  原缺陷：`us1_sentences.inflections()` 的 `word+"es"` 无条件下发，把**另一个词的复数**认成本词变形——
  秩词例句里只靠它命中的 119 条中 **61 条是误绑**（`refuge`←refugees、`sit`←sites、`cloth`←clothes），
  占 25,000 秩词 **0.24%**；按真实出题分桶（后端常量 `VocabTestParams.BAND_UPPER/PROBE_SIZE`）估，
  典型卷（8 档 × 探测 6 题 = 48 题）**≥1 条坏题的概率 11%**、期望 0.12 题/卷，最重的 band5 单题坏率 0.45%。
  61 条里 49 条是 `level_id=10` 哨兵行，含 `j`/`y`/`se`/`ft` 等非通用英语词。因 `us1_attest.py` 曾用**同一个函数**
  做证词准入，准入侧同样被污染（假词占配额、挤掉真词），故秩集必须重出一版。
  定夺与落地（三条规则，脚本注释各有 Why；数字口径见 us1-report §10、发布清单 §3.0）：
  - **A 例句侧**：`+es` 限定 `s/x/z/ch/sh/o` 词尾，其余变形（±s/±ed/±ing、去 e、双写、y→ies、-fe→-ves）保留——
    实测这些变形对例句是必要的，误绑归零。
  - **B+ 准入侧**：`us1_attest.py` 不再复用 `inflections()`，证词只认「原形在语料句中（非句首）小写出现」；
    准入与例句彻底解耦。`sl`←sled、`cl`←cling、`sid`←siding、`nee`←need、`hav`←having 这类伪证词形全部失效。
  - **B+ 词长下限**：`us1_merge.MIN_ATTESTED_LEN = 3`，只约束纯频率行，应试表(level 0-9)走豁免
    （`I`/`OK`/`TV` 照旧保留）。
  - 代价与效果：证词集 31,710→31,183，秩集换掉 **353 出 / 353 进**，总行数 31,754→**31,668**，
    例句覆盖 95.94%→**95.99%**。96 个零证据词出局时混入几个冷门真词（trawler/impala/mimosa），
    由更有语料证据的真词补位——净收益为正但不是零成本。诚实残留：`com`/`du`/`ge`/`pi`/`merci`
    这类确以小写原形出现过的外来语/缩写噪声，双源 AND + 长度下限都挡不住，再收要引第三方证据（本轮不动）。
  - 判据教训（保留，供后续复检复用）：抽检第一版机械层整层复用了 `inflections()`，于是 30/30 全绿、
    `refuge` 恰好漏检——**拿入库函数的输出去验入库函数的输出是空转**。改为「词形集减去 `+es` 的差集」后，
    该判据在新规则下**按构造恒为 0**，作用退化为防回归；真正的准入证据换成两条可机器复检的不变式
    （`sql/us1_audit_sample.py --tsv eng_sentences.tsv`）：**哨兵行词长 <3 = 0 条**、
    **哨兵行原形在语料句中从未出现 = 0 条**（返工前分别为 172 与 96）。

**A 段独立交叉审查（2026-10-05 返工后，评审视角只读复跑）**：评审用独立 SQL 复算 + 离线重放 `clean_freq`
确认上表数字可复现（含「缺口清单 1,003 词与库里 NULL 例句秩词逐词对称差为空」、审计件与提交版**逐字节一致**），
并核出 `ES_ENDINGS` 无漏（`potato/hero/bus/church/does` 均覆盖，`city` 走 `-y` 分支）、
`MIN_ATTESTED_LEN` 分支位置不破坏「补满 25,000」逻辑。挑出 1 高 4 中，已全部修：
① A-段差异留痕把两个**分母不同**的交集百分比并排（63% 用 18,345 作分母、46.7% 用 25,000），
比值看起来「升高却变小」，现统一按既有应试行 18,345 计；
② `admission_health()` 原先只排句首、不要求小写，比准入宽一寸——当前数据下严格口径同为 0，
但作为防回归闸它会虚假报绿，已按 `us1_attest.py` 口径逐字对齐；
③ `us1_attest.py` 残留未用的 `import sys`（去掉 `inflections` 复用后的死代码）；
④ `inflections()` 注释里「被 `us1_attest.py` 复用」已成历史，且 `clothes` 恰是**现在故意不再覆盖**的例子，易误读，已重写；
⑤ 设计文档（us1 设计 §2/§3、主 LLD、us2 设计）仍以返工前数字陈述「终态」，已各加返工后终口径与指向 us1-report §10 的注。
修完复跑：`py_compile` 全绿、`us1_attest.py` 输出与返工时逐字节一致、审计件仍 30/30 且 `short=0 no_evidence=0`。

## B. 算法与 API（US2/US3，对 moon-well 直连验证）
- AC-B1 start：正常返回首题（band3 词）+ sessionId；二次 start 抢占，旧会话转 abandoned；缓存降级时返回 50301。
  - 🆕 **18:15 「缓存降级返回 50301」已从「仅单测」升级为「真 HTTP 实测」**（本机一次性彩排实例，
    **不碰生产、不碰 Nacos**：`SPRING_CONFIG_IMPORT=` 空值让 config-data 列表为空，数据源由 `DATASOURCE_URL` 给出；
    代码取 `origin/develop` 的隔离 worktree `/tmp/mw-vt`，scratch MySQL `vt-norank-mysql:3398`、
    `vt-redis:6381`，脚本 `moon-well/docs/temp/norank_boot.sh` + `norank_probe.sh`）。
    - 造的数据形态是 **US1 中间态**（词表有教学档位、`freq_rank` 全 NULL），启动加载行实测
      `word level cache loaded (startup): 2 level words, 0 ranked words, 0 bands`——插了 **3** 行
      （`the` l1 / `ubiquitous` l3 / `water` **l10 哨兵**），level 视图只算到 **2**
      ⇒ 闸口① 在**活 JVM 的加载路径**上第二次成立（此前只有 SQL 行数与日志判据两种静态证据）。
    - `POST /vocabulary/test/start`（真 `Authorization: Bearer` 一次性账号）实测：
      **HTTP `500`** + `{"success":false,"code":50301,"message":"词汇量测试暂不可用：分级词表未就绪","result":null}`；
      对照组同实例同 token 的 `GET /vocabulary/test/history` = **HTTP `200` + `result: []`**
      ⇒ 降级只挡开考这一条路径，历史读取无恙、无异常抛出。
    - ⚠️ **顺带更正一处既有记载的口径**（`tests/modules/15-vocab-test.sh` 顶部注释写
      「本服务成功与业务错误都返回 HTTP 200，所以判 `.code` 不判 `$HTTP_STATUS`」）：
      **50301 这一条实际回 HTTP 500**。判 `.code` 的做法仍然正确（LLD §6 就是「HTTP 500 + `Result.code`」），
      但那句注释的「都返回 200」以偏概全——按本轮实测把 50301 归到 500 一侧，别再照抄注释。
    - **本条没有一并关掉的四条 HTTP 级空白，现在只剩三条**：B3 机器人三型终止形态、
      B5 `addUnknown=false` 零写入、F1 大小写不敏感打回（B1 的 50301 已在此关掉）。
      D.1 底账表里那条「需要点头/等待」清单不受影响。
- AC-B2 answer：顺序推进（请求体必带 `seq`）；重发同一题号回放不重复计数；对**已 finished** 会话的重复提交=幂等回放库存报告（不是错误）；对他人/已作废/已超时会话返回 50302；`seq` 跳到前面返回 **50304**（前端据此重新对齐题号继续答，不丢会话）；`answer∉{0,1}` 拒绝。
  - ⚠️ 差异留痕（2026-10-05，US3 定稿）：原条把「对 finished 会话作答」归入 50302，实现按幂等回放处理（结果页刷新/网络重试要能拿回同一份报告）；50304 是从 50302 里新拆的码。业务错误统一 **HTTP 500 + `Result.code`** 出口，参数域错误才是 HTTP 400 + `code=400`——前端判读看 `code` 不看状态码。
- AC-B3 状态机路径：机器人三型用户（高/低/中词汇）分别命中 FINISH(CONVERGED)/FINISH(CEILINGED_LOW)/R6 补测形态；任一会话题量 ≤70。
  - ⚠️ 差异留痕（2026-10-05 复核）：实现按**状态机路径穷举**断言（`allAnswerPathsTerminateInsideCap…` 证明所有应答路径题量 <70 且每个非防御性终止原因都可达），**没有**「画像→形态」的一一映射用例；两者等价性靠「路径全覆盖 ⊇ 三型各自走的那条路」成立，故本条判据按实态理解为路径级。题量上限是 `< MAX_QUESTIONS(70)` 而非 `≤70`（触顶即强制止损属防御分支，实测不可达）。
- AC-B4 finish：报告字段齐全（estimatedSize/ciLow/ciHigh/capped/**bandResults**/addedToNotebook）；重复 finish 幂等回放；提前交卷时**累计答题 <6 题（一个完整探测组）返回 50303**。
  - ⚠️ 差异留痕（2026-10-05，US3 定稿）：原条写「0 题 finish 返回 50303」。后端门槛不是 0 题而是不足 `PROBE_SIZE=6` 题——不足一组时当前 band 通过率无可估样本，给出的区间宽到没有信息量（理由见 moon-well 主 LLD §6 与 us3 设计 §8）。
- AC-B5 落本：`addUnknown=true` 时不认识词出现在 `vocabulary_notebook`，hard_level 按「教学档位优先、缺档回落 band 映射」（`VocabTestParams.BAND_HARD_LEVEL`）；`false` 时零写入。
  - 🆕 **18:17 「`false` 时零写入」已从「仅单测」升级为真 HTTP 实测，并配了差分对照**（同一台本机彩排实例，
    实例与造数口径见上面 AC-B1 那条；词表造了 band3 十词 + band4 十词 ⇒ 加载行
    `22 level words, 21 ranked words, 2 bands`，**哨兵行 `water`(l10) 依旧不进 level 视图**）：
    - **关**：一次性账号会话 1，逐题 `answer=0` 共 8 题，`finish {"sessionId":1,"addUnknownToNotebook":false}`
      ⇒ `code 200` / `addUnknown:false` / **`addedToNotebook:null`**（语义=本次没执行，不是 0），
      同刻直查 `vocabulary_notebook WHERE user_id=<该账号>` = **0 行**。
    - **开（差分对照，缺了它上面那条就是空转）**：同账号会话 2，6 题全 `answer=0`，
      `finish … addUnknownToNotebook:true` ⇒ `addedToNotebook:6`，生词本恰 **6 行**
      （`ubiquitous,w2,w5,w6,w9,w10`）⇒ 同一套探针**会**写，所以 0 行是真零写入。
    - **顺带钉两处契约实况**（比本文此前散文口径更精确）：
      ① `finish` 的**请求**字段名是 **`addUnknownToNotebook`**，响应里才叫 `addUnknown`
      （`VocabTestFinishRequest:24-25 @NotNull` + `vocab-test.js:379` 逐字对上）；
      少传该字段实测回 **HTTP 200 + `{"code":400,"message":"参数错误：addUnknownToNotebook 不能为空"}`**
      ——它不走 503xx 那族，是 DTO 校验层，前端漏传会被 `code!==200` 分支吃掉。
      ② **R9 就近降级在真 HTTP 上跑出来了**：造数只有 band 3/4 两桶，被测者全答「不认识」把目标档压到 band 2，
      服务端仍从 band 3 桶取词 ⇒ 该账号的 `vocabulary_test_item` 里 **`band <> word_band` 有 2 条**，
      `bandResults` 里 `band 2: questions 2 / contribution 0`。
      ⇒ 本文 AC-D2 那条「生产真实会话 `band <> word_band` = **0**」的**空白现在有了真 HTTP 证据（本机造数，非生产）**，
      但它**不替代**生产样本（生产那一半仍待 10-07 04:00+08 之后的只读复查，见 D.1 与 task 记录），
      也**不覆盖**「band→**档位** fallback」（落本时给纯频率词派生 `hard_level`，另一分支，证据不可互用）。
    - 附带一条与 US4/R103 有关的新实测：`finish` 响应体里 **`recommendedHardLevel:1` / `recommendedHardLevelName:"初中"`**
      在真 HTTP 上返回（估算 1,000 → band 1 → 初中），即 R103 的后端侧字段路径实测成立；
      magicbook 侧显示与一键应用（R125）仍是代码级 ✅、真机 ⏳。
  - ⇒ **B 段那四条「HTTP 级未覆盖」现在只剩两条**：B3 机器人三型终止形态、AC-F1 大小写不敏感打回路径
    （B1 的 50301 与 B5 的 `false` 零写入已在本轮关掉）。
  - ⚠️ 差异留痕（2026-10-05，US3 交付后按源码校正，原条两处失实）：
    1. 映射方向按 `HardLevel` **枚举码序单调排**：band1–2→初中(1)、band3→高中(2)、band4→CET4(3)、band5→CET6(4)、**band6→托福(6)、band7→雅思(8)**、band8→GRE(9)。早期 D5 文案的「6→雅思、7→托福」是反的——生词判定按「词的档位 > 用户阈值」做数值比较，照文案映射会让 band7 的词比 band6 更容易被判「已掌握」，档位与频段单调性相反。
    2. 原条「已存在词不覆盖 familiarity」**与实现不符**：落本口径与 `VocabularyService.unknown` 一致（存在即把 `familiarity` 置 `UNKNOWN`、刷新 `last_study_time`）。也就是说测试里点「不认识」会把此前标过熟练的词打回生词本。防重复打回靠**每会话至多落本一次**（`notebook_added_at` 令牌，重复 finish 只回放报告不再写本）；这条语义需用户复核确认（见文末「待复核」）。
- AC-B6 history：仅本用户 finished 会话、≤10 条、时间倒序；超 30 分钟 active 会话在下一次 history/start 时转 abandoned。
- AC-B7 单测全绿（`mvn test`，corretto-21）；`ReadingVocabularyServiceTest`/`WordLevelCacheServiceTest` 既有用例无回归。

### B-结果（US2/US3 本机证据底账，2026-10-05 复核）

> 复核方式：把每条 B 项落到**具体测试方法**上（逐个打开方法体确认断言的就是 AC 写的那个码值/行为），
> 并按项目纪律用 corretto-21.0.9 + `-Djava.version=21` 重跑 `mvn clean test`。
> ⚠️ **证据级别统一说明**：B 段全部是「单测 + 真库彩排」级，**没有一条是 HTTP 端到端**——
> 四端点的真实调用要等后端部署后跑 `tests/modules/15-vocab-test.sh`（该脚本从未执行过）。

| 条目 | 结论 | 证据（测试方法名） |
| --- | --- | --- |
| AC-B1 start | ✅ 单测级 / ⛔ HTTP 级待部署 | 首题+sessionId：`VocabularyTestControllerTest#startUsesContextUserIdAndWrapsServicePayload`、`VocabularyTestHttpContractTest#startMapsPathAndWrapsFirstQuestionInResultEnvelope`；二次 start 抢占→旧会话 abandoned：`VocabularyTestServiceTest#startAbandonsPreviousActiveSessionAndReturnsFirstQuestion`；缓存降级 50301：`#startIsRefusedWhenWordTableNotReady`（`testReady()=false`）+ `#startFailsWhenSamplingPoolIsEmpty`（桶池为空，同一码值两条路径） |
| AC-B2 answer | ✅ 单测级全覆盖 | 顺序推进与重发回放不重复计数 `#retriedAnswerReplaysSameNextQuestionWithoutDoubleRecording`；**对 finished 会话重复提交=幂等回放** `#answerOnFinishedSessionReplaysStoredReport`；他人/超时/作废 50302 `#answerOnSomeoneElsesSessionIsRejected`、`#answerAfterTimeoutIsRejectedAndLeftForLazyMarking`、`#finishOnAbandonedSessionIsRejected`；跳题 50304 `#answerWithFutureSeqIsRejected`（断言码值 + 文案含「第 1 题」+ **item 表零写入**）；`answer∉{0,1}` `#answerWithIllegalValueIsRejected` + `VocabularyTestControllerTest#answerRequestRequiresSessionSeqAndBinaryAnswer` + `VocabularyTestHttpContractTest#invalidAnswerValueIsRejectedByValidationBeforeTheServiceRuns` |
| AC-B3 状态机路径 | ✅（但断言维度与原文不同，见备注） | 路径穷举 `VocabTestPlannerTest#allAnswerPathsTerminateInsideCapAndCoverEveryNonDefensiveReason`（所有应答路径最大题量 **< `MAX_QUESTIONS`=70**，且每个非防御性 `FinishReason` 都可达）；CEILINGED_LOW `#threeConsecutiveAllUnknownProbesStopLow`；R6 邻档补测→CONVERGED `#boundaryMiddleRateProbesAdjacentBandsThenConverges`；band8 封顶 `#band8LowProbeTopsOut`；机器人精度与预算 `VocabTestRobotSimulationTest` 三用例（中位误差 <1.5 档宽、低词汇不会被报成高词汇、随机人群不爆题量）；真库彩排 28/22 题收敛（主 LLD §9）。**备注**：AC 原文按「三型用户画像分别命中三种终止形态」表述，实现是按**状态机路径**穷举的，画像→形态没有专门映射用例；判据等价性成立（路径全覆盖 ⊇ 三型可达），表述已按实态校正 |
| AC-B4 finish | ✅ 单测级 | 字段齐全 `VocabularyTestHttpContractTest#reportDistinguishesNotebookWriteCountFromAbsent` + `VocabularyTestControllerTest#finishCarriesNotebookSwitchAndReportCount`；重复 finish 幂等回放同 B2；**不足 6 题 50303** `VocabularyTestServiceTest#finishBeforeEnoughAnswersIsRejected`（并断言会话仍为 ACTIVE，不作废）；≥6 题提前交卷走部分应答估算 `#earlySubmitEstimatesFromPartialAnswersWithNullReason` |
| AC-B5 落本 | ✅ 单测级 | 档位「教学优先、缺档回落 band 映射」`#notebookHardLevelPrefersTeachingLevelThenBandMapping`；大小写不敏感 upsert（撞唯一索引那条缺陷）`#notebookMatchingIsCaseInsensitiveSoExistingRowIsUpdatedNotReinserted`；开关时序 `#notebookSwitchOffDelaysTheWriteAndTurningItOnLaterStillLandsOnce`、D5 缺陷回归 `#naturallyTerminatedSessionStillLandsUnknownWordsOnTheResultPageSubmit`、提前交卷落本 `#unknownWordsFromAnEarlySubmitFinishLandInTheNotebook`。「打回生词本」语义已按 §F1 定稿**维持现状** |
| AC-B6 history | ✅ 单测级 | `#historyListsFinishedSessionsAndLazyAbandonsStaleActives`；超时口径按**最近作答时间**而非开考时间 `#historyKeepsLongRunningSessionThatAnsweredRecently`；≤N 与默认值 `#historyHonoursLimitAndDefaults`；HTTP 层 `?limit=` 绑定 `VocabularyTestHttpContractTest#historyBindsTheLimitQueryParamAndPassesNullWhenAbsent` |
| AC-B7 全量单测 | ✅ **2026-10-05 重跑** | `JAVA_HOME=corretto-21.0.9`、`mvn clean test -Djava.version=21` → **657 tests / 0 failures / 0 errors / 0 skipped**（73 个测试类）；`ReadingVocabularyServiceTest`、`WordLevelCacheServiceTest` 既有用例无回归 |

- **AC-B HTTP 级首跑（2026-10-05 13:17，`tests/modules/15-vocab-test.sh` → ✅ 33/33）**。
  这份脚本此前**从未在任何环境执行过**，本次首跑即抓出两条工装缺陷（见下），修完才跑通。
  - 环境：`7c37816`（即已上线那一笔代码）的隔离 git worktree，`corretto-21.0.9` + `-Djava.version=21`
    `spring-boot:run`；`SPRING_CONFIG_IMPORT=` 置空断开 Nacos，数据源指彩排容器 `vt-us1-mysql`，
    Redis 用本机一次性容器 `vt-redis:6381`，ES/MinIO/NewAPI/Proxy 全填 dummy —— **全程不碰生产**，
    这也顺带证伪了本文件 §C 前言里「本地起服务即连生产库」那句（已就地更正）。
    `ddl-auto=update` 补出彩排库里没有的 `app_user` 等表；跑前跑后词表都是
    **31,668 行 / 秩 25,000 / 例句 23,997**（与 §A 终态逐项吻合，未被 Hibernate 改动）。
  - 断言覆盖（真 HTTP + 真库，非 mock）：首题 band3/seq1 带英文例句、二次 start 抢占、
    旧会话作答 50302、seq 3 重发回放到「当时的下一题」且进度不变、答满 6 题计数一次、
    跳题 50304、`answer=2` 被 DTO 拦下 400、finish 报告四件套 + `bandResults`、
    `addedToNotebook` 首次 `1`/重放 `null`、history 只列 finished 且不带 per-call 落本数。
  - 落库对账（彩排库实测）：`vocabulary_test_session` id=5 → `status=1 question_count=6 known_count=5
    estimated_size=2833 ci_low=2333 ci_high=3333 capped=0 notebook_added_at=21:17:57.394`，
    `band_result` = band1/band2 未探测按 `rate=1.0` 各贡献 1000、band3 `5/6=0.833`→833，
    **1000+1000+833=2833 与 estimated_size 精确闭合**；被抢占的 id=4 `status=2`。
    `vocabulary_test_item`（session 5）六题 band 全 3、第 6 题 `answer=0`；
    `vocabulary_notebook` 落 `word=extremely, familiarity=1(UNKNOWN), hard_level=2` —— AC-F1
    「打回生词本」的口径在真库上拿到了 HTTP 级佐证。
  - **首跑抓出的两条缺陷（已修，属测试工装不是业务代码）**：
    ① `tests/lib/api.sh` 发的是 `token: Bearer …`，而 `AuthHandlerInterceptor` 取的是
      `request.getHeader(Common.TOKEN)`、`Common.TOKEN = "authorization"`；同一枚 JWT 实测
      `Authorization` 头 200、`token` 头 `code=102 未登录`。这一条让**全部 15 个模块**的身份接口
      都不可能通过，是这套脚本「从未跑过」的直接原因。`api_upload` 里同样的头一并改了。
    ② `assert_status "200" "$HTTP_STATUS"` 紧跟 `local response=$(api_request …)` 时**必然失真**：
      子 shell 里设的全局传不回来，取到的要么是空、要么是上一条直接调用 `api_request` 的残值
      （残值更危险——它显示 ✓ 却什么都没验）。本模块的 4 处改成断言响应体 `.code`，
      与本项目「业务错误判读看 `Result.code` 不看 HTTP 状态」的口径一致。
    ③ 附带：`15-vocab-test.sh` 原来只 `api_login`，而 `accounts.sh` 每次进程重算时间戳用户名、
      全库只有 `01-auth.sh` 注册，单跑本模块时账号不存在 → 模块改成自带 `ensure_account`
      （注册后登录，账号已存在则忽略）。
  - **HTTP 级仍未覆盖**（别当已通过）：AC-B3 机器人三型终止形态（只有单测）、AC-B1 的 50301
    降级分支（本地彩排库有秩数据，构造不出「词表未就绪」）、AC-B5 开关 `false` 时零写入
    （脚本固定传 `true`）、AC-F1「把既有熟练词打回」的大小写不敏感更新路径（仅单测）。
  - ✅ **同一脚本打生产：33/33 全绿（2026-10-06 03:22Z，用户点头「跑并当场一并清理」）**。
    目标 `https://moon-well.haoshenqi.top`，走 `/auth/register` 的一次性账号（不落内网信任头）。
    这不是彩排那一遍的重复：缓存已按发布清单 §3.4 取证 5 实际生效，所以 50302/50304/400 三条分支与
    「落本条数恰为 1」都是**在生产数据上**第一次被真 HTTP 验到，且不存在 §4.1 警告的假绿形态
    （`test_start` 6 条全绿、`history` 的 `.nonEmpty` 也是真绿）。
    - **写库footprint 与台账逐格对上**：`(app_user, session, item, notebook) = (1, 2, 6, 1)`；
      两条会话 `status=2`（被第二次 start 抢占，`question_count=0`）与 `status=1`（6 题 5 认识）；
      六条 item 全在 `band=3`、答案 `1,1,1,1,1,0`、唯一未知词 `cave`。
    - **量级 sanity（给 AC-D2 当前置参照）**：这个「band3 连认识 5/6 题」的画像在生产库上估出
      `estimated_size=2833`、CI `[2333, 3333]`、`capped=0`、`finish_reason=NULL`
      （只有 6 题就 finish，走的正是提前交卷路径，与 §6 约定一致）——落在 band3 上界 3,000 附近，符合预期。
    - **清理已执行并验证残留 0**：按 `user_id` 逐表删（`item 6 → session 2 → notebook 1 → app_user 1`），
      删后 `vocabulary_test_session` / `vocabulary_test_item` **全表计数归零** → 反证本特性是这两张表的唯一写入者。
      `vocabulary_notebook` 与阅读页共用，只删该 uid 那一行。
    - ⚠️ 上面「HTTP 级仍未覆盖」四条**一条都没因这次生产运行而减少**；其中 AC-B1 的 50301 分支现在
      **永久无法在 HTTP 级构造**（生产缓存已就绪，再造出「词表未就绪」只能删生产数据）→ 该条判定按
      「单测级即为终态验收」归档，不要再排期。

## C. magicbook 前端（US4）

> **本机验证边界（2026-10-05 定，同日 13:20 修订）**：US4 在本机只能验「代理层单测 + 无头 Chrome 视觉截图」。
> ~~moon-well 的数据源由 Nacos 生产 `moon-well.yaml` 下发（本地起服务即连生产库 `magichouse`）~~
> **这句已被证伪**：`SPRING_CONFIG_IMPORT=` 置空即可绕开 Nacos，数据源由 `DATASOURCE_URL` 显式给出
> （已在 `7c37816` 上实测跑通，见 §B「AC-B HTTP 级首跑」）。因此 AC-C2～C6 的运行时行为
> **本机就能验**——magicbook 本地起 + 代理基址指向本机 moon-well 实例 + 彩排库；
> 生产部署只用于 AC-D 段。`tests/modules/15-vocab-test.sh` 也已在本机跑通，不再依赖部署。
> 未跑成的条目仍须逐条标注「未验证」并写清卡在哪一步，不得记为通过。AC-C8（zh 缺串）可由种子契约测试在本机守住。

- AC-C1 `/reading/settings` 渲染测试卡片；moon-well 不可达时档位区走 `load_error`、测试卡片静默降级为无历史态，页面不报错。
- AC-C2 完整答题流：Start → 浮层逐题（单词+英文例句，**屏上无任何中文释义**）→ 结果视图（估算大字、区间或 25,000+、8 行频段条形图、落本提示）→ Done 回卡片显示 Last result。
- AC-C3 键盘 ←/J、→/K、Esc 生效；IME composition 期间按键不触发（用中文输入法实测确认候选词回车/空格/方向键无串扰，对齐 R114 守卫口径）。
- AC-C4 断网重试：拔线提交 answer → 错误行出现 → 恢复后重试成功且不重复计题。
- AC-C5 Exit 直接回卡片；重进页面 Start 正常（旧会话已 abandoned，不阻塞）。
- AC-C6 `#vt-add-unknown` 勾选态 localStorage 记忆生效；取消勾选后 finish 零落本（配合 AC-B5）。
- AC-C7 视觉：两套主题下卡片/浮层/图表渲染正常，浮层继承宿主主题（无自造实色描边，遵守 UI 纪律）；截图存 `docs/temp` 并附验收报告。
- AC-C8 zh 翻译补全后切换语言无缺串。

### C-上线事实（2026-10-06 03:39，只读复核）

US4（`5aea1a28`）已随 `develop` push 上到生产 **magicbook.haoyuhang.top**（8083）。时间线与判据：

- `03:35:14Z` push（`5f7e24b2..35300f7d`，22 笔）→ `03:35:17Z` 仓库 webhook 投递返回 **202** → 约 2 分钟后线上出现新产物。
- **⚠️ 更正我此前的记载**：magicbook 的构建链**不是 GitHub Actions**。实测 `Build and Push to Aliyun`
  状态为 `disabled_manually`，且本次 push **没有产生任何 GHA run**（`gh run list` 最新一条仍停在 2026-09-23）；
  真正生效的是 fnOS webhook-builder（`push → webhook.haoshenqi.top → fnOS :9877 → build-magicbook.sh → ACR →
  controller project-update`，权威口径 `ops/apps/app-magicbook.md`）。此前 `deploy/DEPLOY.md` 与本文件按 workflow
  文本推断「push 即 GHA 构建」属**以静态文本代替实测**，已在 `deploy/DEPLOY.md` §CI/CD 更正留痕。
- 只读探针（全部零写入，未进入任何业务 handler）：
  | 探针 | 返回 | 读法 |
  | --- | --- | --- |
  | `GET /static/js/vocab-test.js` | `200`，19,252 B | 新静态资源在镜像里 → 本次构建已上线 |
  | `GET /ajax/vocab-test/start` | `405` | 路由已注册、仅收 POST（Werkzeug 路由层拦下，未进视图） |
  | `GET /ajax/vocab-test/finish` | `405` | 同上 |
  | `GET /ajax/vocab-test/history` | `302` | GET 路由已注册、`login_required` 跳登录 |
  | `GET /ajax/vocab-test/item` | `404` | **是我猜错了路由名**，第四条实为 `/ajax/vocab-test/answer`（`cps/web.py:591`）；此 404 不是缺陷 |
- 后端侧同批复核（moon-well 因两把链并存被重启两次，`11:35:29`/`11:35:47 +08:00`）：两次启动日志的缓存行
  **都是** `word level cache loaded (startup): 18345 level words, 25000 ranked words, 8 bands`，双向判据保持成立；
  窗口内 `app-log-magicbook` ERROR **0** 条。
- ⇒ AC-C2～C6 的前置条件（生产在线）**已具备**，但仍未逐条打钩：它们需要真人 OIDC 登录 + 浏览器操作（见 D 段）。

### C-结果（US4 本机验收，2026-10-05）

| 条目 | 结论 | 佐证 |
| --- | --- | --- |
| AC-C1 | ✅ 本机通过 | `tests/test_vocab_test_proxy.py::test_page_renders_card_with_single_upstream_call`（首屏只拉 settings，卡片渲染）、`::test_card_survives_settings_load_failure`（settings 失败时走 `load_error`，`id="vt-root"` 仍在）、截图 `docs/temp/vt_us4_shots/vt_us4_fixture__idle.png` |
| AC-C2 完整答题流 | ⛔ **本机未验证**（UI 侧仍需真人过眼） | 代码路径已按 US3 契约逐字段核对，夹具用同形状假响应拍到 asking/result 两态。**17:2x 更新**：后端半边已由生产真实会话 id=3 背书（22 题全程落库、`CONVERGED`、估算与 `band_result` 自洽、落本去重成立，见 §D「AC-D2」）；未升级的部分是纯 UI 判据——「屏上无任何中文释义」「结果视图四件套」「Done 回卡片显示 Last result」必须用眼睛确认，DB 证不了 |
| AC-C3 键盘 + IME | ⛔ **本机未验证**（IME 需真人中文输入法） | 键位与 `isComposing`/`keyCode 229` 判定已实现（`vocab-test.js`），夹具拍到键盘不参与的点击路径 |
| AC-C4 断网重试 | ⛔ **本机未验证**（真拔线） | 错误分支用 fetch 桩拍到：`vt_us4_fixture__error.png` / `..._blur__error.png`（词头保留、红色重试行、进度不清零） |
| AC-C5 Exit / 重进 | ⛔ **本机未验证** | Exit 走 `modal('hide')` + 状态机复位 `idle`，需真实会话才能验「旧会话 abandoned 不阻塞」 |
| AC-C6 勾选态记忆 + 零落本 | ⛔ **本机未验证**（落本在后端） | 勾选态 localStorage 读写在前端，但「取消勾选后零落本」要连库验，属 US5 |
| AC-C7 视觉（两套主题） | ✅ 本机通过（含两处缺陷修复） | 10 张截图（默认主题 + caliBlur × idle/asking/result/history/error）。**修 1**：`.vt-el[hidden]` 兜底——`block header` 排在 `bootstrap.min.css` 之后，自造 `display` 规则盖掉 normalize 的 `[hidden]`，导致隐藏态一加载就显示。**修 2**：浮层从自造 `.vt-scrim`+`.panel` 改为 bootstrap 原生 modal——caliBlur 的深色规则按组件类名下发，自造 panel 拿到「浅底白字」全不可读；并补 `#vt-overlay > .modal-dialog{margin-top:70px}`（`caliBlur.css:5491` 把上外边距改成 0，弹层被 60px 固定导航栏压住）。详见 us4 设计 §2.2 落地修订 |
| AC-C8 zh 无缺串 | ✅ 本机通过 | **判据下沉到编译产物**：用 `gettext.GNUTranslations` 直接加载 `messages.mo`，对本特性涉及的两个取词面全量扫描得 35 条 msgid（`reading_settings.html` 整份模板，含同页既有档位卡片文案 + `vocab-test.js` 的 `mbT()`），逐条向 `.mo` 取词，**原样回吐 0 条、空译文 0 条**，`charset=utf-8`，且 `.mo` mtime 晚于 `.po`（防「po 改了没编译」这类只在运行时暴露的缺串）。另有 `tests/test_i18n_seed_contract.py`（`JS_FILES` 已含 `vocab-test.js`，JS 取词漏进种子即红）与 `pybabel compile` 无告警兜底。备注：模板内按钮文案（`I know it`/`Not sure`/`History`）由 Jinja 服务端渲染，**不进 i18n 种子属正确行为**。全库口径扩展复核：1,106 条已译单数词条逐条比对 `.po`↔`.mo`，**漂移 0 条**；`.mo` 取词等于 msgid 的 4 条（`Goodreads API Key`、`Google Books API Key`、`Kobo Token:`、`Arial`）经核对是译文与原文同形的刻意直通，非缺串——重跑此校验时勿误判成漏编译 |
| 回归 | ✅ | `pytest tests/ -q` → **326 passed**（含既有 reading-settings / i18n 种子 / 词汇本用例）；夹具生成器改名 `tests/vt_us4_dump_fixture.py`（不带 `test_` 前缀，不进自动收集，显式点名才跑）。第 326 条是 AC-C8 复核时补的 i18n 契约 5（见上） |

⚠️ 顺带记录一条**不属本特性**的既有主题缺陷（不修，留待单独议题）：caliBlur 下 `/reading/settings` 的两张 `.panel` 卡片是「浅色面板 + 深色主题控件」，`btn-primary`（既有的 Save、新增的 Start test）与 `text-muted` 历史行对比度不足。同页既有 Save 按钮同症状，属页面/主题级问题；本特性不自造配色打补丁，浮层因复用 modal 已随主题正确反色。

**独立交叉审查（2026-10-05）**：评审对本特性前端挑出 2 高 4 中，全部已修并逐条记入 us4 设计 §2.4——① 在途响应未作废：关闭浮层后迟到的 answer/finish 回包会把隐藏态重新点活（Start 按钮永久失效 / 键盘在不可见浮层里提交），加会话代数 `epoch` 判定丢弃；② 登录过期是 302→200+HTML，代理层看成成功，改按 `response.url` 命中 `/login` 即走跳登录；③ 后端中文 `message` 直接上屏（违反单语文案纪律），删掉 `messageOf`，文案一律 `window.mbT`；④ **50304** 复用码的第二种文案「该题正在提交，请重试」不含题号，原先无脑取数字会写坏 `seq`，改为解析不到题号就转成可重试；⑤ finish 遇 50302 无限重试，补回卡片态分支；⑥ `vtCsrfReloaded` 永不自复位，刷新一次后 CSRF 兜底失效。修完 `pytest tests/` 仍全绿（当时 325，AC-C8 复核补 i18n 契约 5 后 326），asking/result/error 三态 × 两主题共 6 张浮层截图重拍复核。评审另提两条经源码核对**不改**：`answer` 后端确为 `Integer@Min0@Max1`（前端 1/0 正确）、`StartResult` 三字段形状与 US3 一致。

## D. 端到端与回归（US5）

- AC-D1 生产发布顺序演练（主 LLD §10，**逐条执行清单见 moon-well `docs/feat/vocab-size-test/release/release-checklist.md`**）：DDL+数据 → moon-well → magicbook 前端；每步后旧功能可用（老前端对新后端无感，新前端对旧后端静默降级）。
  - **实况（2026-10-06 03:39 复核）**：实际顺序 = **moon-well 闸口代码（`7c37816`，01:14Z 上线）→ 生产 DDL+数据导入（01:16–01:17Z）→ 缓存生效（02:41Z 双向判据成立）→ magicbook US4（03:37Z）**，与「闸口代码必须先于数据上线」的定稿一致。
    「老前端对新后端无感」这一半**已被被动验证**：01:14Z→03:35Z 约 2 小时里生产跑的是新后端 + 旧前端，
    实测 ES 该窗口（按 `@timestamp`，即 filebeat **入库时间**，非日志正文时刻）内
    `app-log-magicbook` 与 `app-log-moon-well` 的 `ERROR` 命中数**均为 0**。
    「新前端对旧后端静默降级」**当时未演练**（生产上后端始终比前端新，构造不出该组合），按本机单测口径归档；
    **该结论已被下面 09:55Z 的本地夹具演练取代，上面两句留作过程留痕**。
  - ✅ **该组合已于 2026-10-06 09:55Z 在本地构造并跑通**（本机夹具，不碰生产、不写库）。
    做法可复用：JS 取**线上实装件**（`git show origin/develop:cps/static/js/vocab-test.js`，486 行、不含本地未推的 R125 +104 行），
    夹具用 `docs/temp/vt_us4_fixture.html` 的 DOM（与线上件匹配，`vt-reco` 引用数 0），
    在 `window.fetch` 边界注入四种后端实况，点一次 Start 后把判据写进 `#vt-probe`，
    `chrome --headless=new --dump-dom --virtual-time-budget=8000` 取回文本。
    生成器 `docs/temp/scripts/vt_legacy_fixture.py`（docs 纪律：夹具与产物留在 `docs/temp/`，不提交）。
    | state | 注入的后端实况 | 未捕获异常 | 卡片文案 | 浮层 | 历史入口 | 档位下拉框 |
    | --- | --- | --- | --- | --- | --- | --- |
    | `ok`（**对照组**） | `success:true` + 首题 | `[]` | 空 | **打开**、出词 `ubiquitous` | 隐藏 | 在位 `value=3/10 options` |
    | `legacy404` | Spring 默认 404 错误体（旧 moon-well 无该路由，代理原样透传） | `[]` | 「Start failed, please try again.」 | 未打开 | 隐藏 | 在位 |
    | `unreach503` | 代理自造 503 `{"success":false,…}`（后端不可达） | `[]` | 同上 | 未打开 | 隐藏 | 在位 |
    | `notready` | HTTP 500 + `code:50301`（词表未就绪） | `[]` | 「Test unavailable right now, please try again later.」 | 未打开 | 隐藏 | 在位 |
    - **判读**：`legacy404` 与 `unreach503` 即「新前端 × 旧后端」的两个真实形态（`cps/web.py:1194` 三元组
      原样透传上游状态码、`:1144`/`:1198` 自造 503），两者都**不进入浮层、Start 按钮保持可重试、旧功能（档位设置）
      在同页仍可用、零未捕获异常** ⇒ AC-D1 的「静默降级」这半边从「未演练」升级为「本机夹具端到端验证」。
    - ⚠️ **三条边界写清楚，别夸大**：① 夹具是在 JS 的 `fetch` 边界注入响应，证明的是**前端消费侧**，
      代理层透传由 `tests/test_vocab_test_proxy.py`（`:199-215` 业务码透传、`:273-281` 网络失败 503）背书；
      ② **没有减少 B 段「HTTP 级仍未覆盖」那四条中的任何一条**——`notready` 那行是前端读 50301 的分支，
      不是后端真造出 50301（那条仍只有单测 `#startIsRefusedWhenWordTableNotReady`）；
      ③ 对照组 `ok` 是必须的：没有它，「四格全静默」也可能只是夹具本身坏了。
- AC-D2 真实用户完整测试一次（browser-use + 用户登录，按项目数据访问纪律），结果数值与人工预期「量级相符」共识判定。
  - **生产已存在一条完整真实会话（2026-10-06 17:2x 只读直查，本特性后端全链路首次在线上跑通并留下自洽数据）**：
    `vocabulary_test_session` **id=3 / user_id=1**，`15:54:22 → 15:56:23`（本地，+08:00），
    22 题 / 认识 17 / `estimated_size=4033` / CI `[3033, 5033]` / `capped=0` / `finish_reason=CONVERGED` /
    `add_unknown=1` / `notebook_added_at` 非空。id 1、2 是 §C 段彩排后按 `user_id` 逐表清理掉的测试数据
    （`AUTO_INCREMENT=4` 与此吻合），**这条是新数据**。
    - **估算自洽**：`band_result` 四行 `1000 + 1000 + 700 + 1333 = 4033`——band 1 未出题按满档计入、
      band 2 六题全知、band 3 十题七知（0.7）、band 4 六题四知，与 `VocabTestEstimator` 的加权口径逐项对上。
    - **档位映射在真实数据上零错位**：22 个题面词的 `freq_rank` 全部落在其出题 band 的区间内
      （band 2 = 1,016–1,924、band 3 = 2,240–2,920、band 4 = 3,447–4,827），且
      `band <> word_band`（R9 就近降级）的条目 **0**——`BAND_UPPER` 与桶构建过滤在生产上成立。
    - **落本（US3）线上成立**：5 个「不认识」词 `cab`/`conference`/`gather`/`trauma`/`mansion`
      在 `vocabulary_notebook` 各占一行、`last_study_time` 全为 `15:56:23`；其中 `trauma`/`mansion`
      的 `first_study_time` 同为该刻（新词），另三个只有 `last_study_time` 被推进（此前已在生词本 ⇒ **去重生效**）。
      该用户生词本总量 4,113 行，而这五个词各**只有一行**（未重复插入）；至于是净增 2 还是净增 5，
      仅凭 `first_study_time`/`last_study_time` 两列断不了（三行的 `first_study_time` 本就是 NULL），不记为结论。⇒ 「每会话至多落一次 + 去重」由数据而非单测背书。
    - ⚠️ **归属未证 / 人工判据仍缺**：从库里看不出这条会话是本人还是另一会话经 browser 驱动的，
      所以 AC-D2 的「量级相符」**要用户自己点头**才算打钩；本条只钉住「后端全链路已在生产跑通」这半边。
    - 🆕 **读库顺带抓到一条显示保真缺陷（新特性外，非阻塞）**：词桶存的是**小写折叠键**
      （`WordLevelCacheService:101` `.add(key)`，key = `word.toLowerCase(ROOT)`），
      而生产 25,000 秩词里有 **233 个首字母大写词全部在桶内**（`ranked_capitalized_in_buckets=233`），
      会以小写上屏。**证据就是这条会话的第 12 题**：库里词形 `Katherine`（rank 4,786），
      `vocabulary_test_item.word` 落的是 `katherine`。两类可能的危害已实测排除——秩集内
      `LOWER(word)` **零碰撞**（`bucket_keys_dup=0` / `rankmap_keys_collide=0`）⇒ 不重复出题、不串秩；
      剩下的是语义保真：band 1 的 `I`(2)/`OK`(206)/`Jesus`(635)/`TV`(748)/`Christmas`(766)/`America`(888)/
      `English`(942)/`French`(965) 会以 `i`/`ok`/`jesus`/`tv`… 出题（失真面 233/25,000 ≈ 0.93%）。
      反向收益：它让 moon-well §12.5 对 `AD`/`AIDS`「仍是小写常见义」的 🟡 判读**变成自洽**——
      题面既然显示 `ad`/`aids`，配「广告／帮助」义例句正是该词形的真实高频义。
      修法（桶内并存原形词：出题与落本用原形、查秩仍走小写键）属代码笔，**等点头**；不修就按「已知瑕疵」归档。

- AC-D3 阅读页划词/生词判定、难度档位保存回归无恙（重点：词表新增 13,323 条 `level_id=10` 哨兵行后判档行为不变——原文写「level-NULL」，与定稿的枚举哨兵方案不符，已校正；行数 2026-10-05 由返工前 13,409 校正为终态 13,323）。
  - ✅ **通过（代码路径 + 生产数据双向闭环，2026-10-06 09:4xZ 全程只读取证、未写库、未发任务）**。
    三道闸口逐条对上生产实况：
    ① `WordLevelCacheService:86-88` 判档视图排除 `level_id IS NULL` **与** `FREQ_ONLY(10)`，
    而 `wordLevelsOf()`（`:146-148`）只读这一份视图 ⇒ 阅读页生词判定**结构性看不到**哨兵行；
    ② `ReadingVocabularyService:348-350` 整页取档为纯内存查找（不打 DB），`:227-230`
    `inScope = wordLevel != null && wordLevel > hardLevel` ⇒ 无档位 = 默认认识 = 不写阅读事件，
    与「表外词」同一路径，哨兵行因此与表外词**不可区分**（这正是设计意图）；
    ③ 档位保存：`ReadingSettingsService:48-51` + `HardLevel:50 isSelectable` 拒绝 10，
    且 18:0x 逐点复核 ⇒ 全仓 **`app_user.setHardLevel()` 在生产代码里只有一个调用点**
    （`ReadingSettingsService:53`，前一行 `:49` 就是守卫；其余 12 处 `setHardLevel` 全在 `src/test/`，
    另有 `VocabularyTestService:422 notebook.setHardLevel` 属**生词本反范式列**、不是用户阈值，
    其值域由 `VocabTestParams:63 BAND_HARD_LEVEL` 给出、`VocabTestParamsTest:66/:101` 断言其全部 `isSelectable`）
    ⇒ 这条「唯一写点 + 前置守卫」是**结构性**的，不依赖数据巧合；
    生产 `app_user.hard_level` 实际取值 `{2, 5, 6, NULL}`（3 行为 NULL → 走默认 CET4），
    **无 10、无越界** ⇒ 哨兵值不可能被存成用户阈值。
  - **数据侧不变式**：`COUNT(*) WHERE level_id IS NOT NULL AND level_id <> 10` = **18,345**，
    与线上缓存判据行 `18345 level words, 25000 ranked words, 8 bands` **逐字对上**；
    全表 31,668 = 教学 18,345 + 哨兵 13,323 + **NULL-level 0**（⇒ 排除完全靠哨兵值本身，
    不存在「靠 NULL 兜底」的侥幸）；`level_id NOT BETWEEN 0 AND 10` 命中 **0** 行。
  - **为什么这条闸口是承重的**（新取证，此前文档只有结论没有实例）：哨兵行里秩最小的十一个词是
    `was`(23)/`got`(59)/`did`(64)/`going`(73)/`were`(83)/`had`(86)/`been`(88)/`gonna`(90)/`didn`(98)/`has`(102)/`said`(119)
    ——全是 be/do/have 的屈折形式与口语缩约（生产查询取秩 1..10 时命中的是 `you`/`I`/`the`/`to`/`a`/`it`/`and`/`that`/`of`/`is`，
    **十个都有教学档位 `level_id=1`「初中」**，所以必须往下看才能取到哨兵词——这一层区别我在取证时先搞错、按「top10 即哨兵」写过一版，已按实测校正）。若闸口①缺失，`10 > 任意阈值` 会让 CET4 用户**每一页**
    都被这些基础词标成生词并写进事件流；实测它们 `level_id=10` 且不入判档视图 ⇒ 默认认识、不写事件。
  - **顺带把 19 个无例句秩词按档位侧拆开**（与 moon-well §12.6「14 拒 + 5 主动排除」逐词对账一致）：
    教学侧 5 = `nss`(level 6)、`cliché`/`proclamation`/`pedigree`/`contrition`(level 9)；
    哨兵侧 14 = `sakes/wah/chet/christening/def/berk/nom/positioning/ora/mortem/mou/veneration/annals/muss`。
    ⇒ 这 19 词在**缓存构建期**就被挡在词桶外（`WordLevelCacheService:99`），
    所以 `VocabularyTestService:292` 的跳过分支**在稳态下取不到**。
  - ⚠️ **自我更正（18:0x 复核，原记载过强）**：上一条我原本写的是「`:292` 在现网数据结构下
    **不可能**被触发（保留作防回归）」——这句和代码自己的注释冲突（`:292` 行尾写的是
    `// 仅日更窗口内可能出现`），复核后按实测改写：**「构建期过滤」保证的是「加载那一刻桶里没有无句词」，
    不是「桶里的词在 DB 里永远有句」**——`sentenceOf(word)` 是**现读 DB**（`:291`），
    所以任何一次「把 `example_sentence` 改成空」的写库，都会在下一次缓存加载之前造出一个命中窗口。
    而今天恰好就发生了这样一次写库（§12.6：`ora`/`mou`/`def`/`nom`/`nss` 五行置 NULL）。
    - **排序取证结论：这一窗口的开合时刻「无法由现存证据判定」，因此不能记为未触发**：
      ES `app-log-moon-well` 里 `word level cache loaded` 近 14 小时共 13 条（含 filebeat 重放的重复行，
      按本文件 A 段既有的日志时序纪律——同一行会被 filebeat 重放索引两次，时序只看正文里的 `+08:00` 时刻），**最后一条 = `2026-10-06T17:25:51.441+08:00 (startup)`**；
      5 行 NULL 的写库时刻只夹在两个本地锚点之间——`docs/temp/vocab-sentence-audit-3w.jsonl`
      mtime `17:20:06`（3 词重出句已回读）与「终态只读直算 24,981」的 `17:28`——
      **17:25:51 正落在这个区间里**；`magicbook_word_level` 表**没有** `update_time` 列（实测 SHOW COLUMNS 十列，
      最后列为 `freq_rank`），DB 侧不留写时刻 ⇒ 既不能证明 NULL 早于加载（则桶干净），也不能证明晚于加载
      （则桶里仍留着这 5 个词形、`sentenceOf` 回 NULL、分支正命中）。
    - **命中了会怎样（按 `:283-295` 逐行读，不是推测）**：`continue` 只跳过**该 source band**、
      继续走 R9 就近降级序（`sourceOrder`：目标档 → +1 → −1 → +2 → −2…），
      **不消耗该 band 的索引**（`consumed` 只读不写，item 表也无新行）⇒ 不重复出题、不死循环、不抛错；
      代价是该 band 在这一会话里被永久绕开（每次都取同一个陈旧槽位、每次都跳），
      估算器会收到 `band <> word_band` 的降级样本——**这恰好是上面 AC-D2 真实会话取证里
      「`band <> word_band`（R9 就近降级）条目 0」那条缺的证据**（注意：与本条末尾另一处
      「band→档位 fallback 无生产实证」不是同一分支，后者是落本时给生词派生 `hard_level`，
      两者不可混用同一份证据）：若此刻桶真还留着这 5 个词，任何一次打到 band 7/8 的会话
      都会自然留下 R9 降级记录（无需为它写库彩排）。
      5 词落在的档位（现读 DB，秩→档按 `VocabTestParams:19 BAND_UPPER` =
      1000/2000/3000/5000/8000/12000/18000/25000）：`def`(17,071)→**band 7**，
      `ora`(20,383)/`nom`(19,021)/`mou`(21,875)/`nss`(22,256)→**band 8**——全在最高两档的长尾，
      只有被测者答到最高档才可能撞上，所以**影响面小、且可自愈**。
    - **自愈时刻是实测的，不是约定**：ES 里今天有正文 `2026-10-06T04:00:00.070+08:00` 的
      `word level cache loaded (daily-4am): …` 一条 ⇒ `@Scheduled(cron = "0 0 4 * * ?")`
      （`WordLevelCacheService:66-69`）**在生产确实触发**（此前只有代码证据），
      故最迟 **2026-10-07 04:00 +08:00** 桶与 DB 必然一致、分支重新变为不可达。
    - ⇒ 归档口径改为：「`:292` 分支**不是死代码**，它是为『日更窗口内 DB 例句变空』准备的活守卫；
      今日 17:2x 的 NULL 写库使其当前可达性**不可判定**，最迟 10-07 04:00(+08) 加载后归零」。
      本条更正**不改变 AC-D3 的 ✅ 判定**（三闸口与回归判据与这 5 行长尾无涉），只修一句失实记载。
  - 🆕 **量化后判为「无需动作」的一条新数据事实**：词桶集合 24,981 个可出题词形中
    **22 个（0.088%）不在 `words_alpha` 白名单**，逐条为缩写（`DNA`/`DVD`/`UK`）、现代复合词
    （`website`/`caregiver`/`cyberspace`/`supermodel`/`stuntman`/`upfront`/`walkman`）、
    专名（`Henderson`/`forbes`/`macdonald`/`lesley`/`allende`/`weldon`/`bryn`/`brea`/`Inuit`/`erectus`/`hur`）
    与俚语 `knackered`。**零缩约残片**——我一度据 `didn`(秩 98) 怀疑 FrequencyWords 把 `didn't`
    切成了残片，实测 `didn` **本身就在 `words_alpha` 里** ⇒ 该担忧作废，按失实记载留下不写进结论。
    其中专名那一类与上面 AC-D2 的小写折叠是同一批词，**互为独立佐证**。
  - **测试侧**：`mvn -o clean test -Djava.version=21`（corretto-21.0.9）
    **677 tests / 0 failures / 0 errors / BUILD SUCCESS**（09:39Z 本机）。
    ⚠️ 归因留痕：本轮先跑的 `mvn -o -q test` 退出码 1，起因是 `AgentConversationControllerTest.class`
    由并行会话用 **Java 25** 编译（class file 69.0，JDK 21 上限 65），而 `target/surefire-reports/*.xml`
    里还挂着上一遍 16:46 的「677/0/0」**陈旧报告** ⇒ **陈旧报告与管道退出码都不是判据**，只认 clean 全量。
  - **第四个消费方（划词/单词详解路径）单独取证**——它不读词表、读生词本自带的档位：
    `VocabularyNotebookRepository:38` `unknownWords()` 的条件是
    `vn.familiarity < 7 AND vn.hardLevel >= :hardLevel`，键在 `vocabulary_notebook.hard_level` 这一份
    **反范式列**上 ⇒ 词表新增 13,323 条哨兵行**结构上影响不到它**（不同表）。生产实测（09:46Z）：
    `hard_level` 值域为 `{1,2,3,4,5,6,7,8}`（`6` 占 8,427 行是历史批量初始化），
    **无 0/9/10、无 NULL、`NOT BETWEEN 0 AND 9` 命中 0 行** ⇒ 本特性从未把哨兵值写进阈值列。
  - **`vocabulary_notebook.hard_level` 的写入分支已被真实会话逐词对上**（session id=3 的 5 个落本词，09:46Z）：
    `trauma` 词表档位 8（雅思）→ 落本存 8、`mansion` 词表档位 4（CET6）→ 落本存 4，
    即 `VocabularyTestService:408,422` 的 **teachingLevels 分支实证**；
    `cab`/`conference`/`gather` 落本存 6，而词表档位分别是 2/1/2 —— 差值**不是缺陷**：
    这三行是**既有行**（`addUnknownWordsToNotebook` 只在 `notebook == null` 时派生档位，:417-424），
    upsert 只改 `familiarity`/`last_study_time`、保留用户早先的 6，与 AC-F1「打回既有熟练词」同一语义。
    ⚠️ 反过来也就说明：**band→档位 fallback 分支（纯频率词无教学档位时按 `BAND_HARD_LEVEL={1,1,2,3,4,6,8,9}` 回落）
    在生产尚未被真实会话走到**（这 5 个词全有教学档位），该分支目前只有单测覆盖，别当成已端到端验证。
  - ⚠️ **两条生词判定路径的比较符本来就不一致**（既有事实，本特性未引入，但 D3 归档必须写明，
    以免被读成「同一口径」）：阅读页用 **严格大于**（`ReadingVocabularyService:230`
    `wordLevel > hardLevel`，词表档位），划词/详解用 **大于等于**（`VocabularyNotebookRepository:38`
    `vn.hardLevel >= hardLevel`，生词本自带档位）。同档位的词在阅读页判「认识」、在详解页判「不认识」。
    本特性对两处都**零改动**，故回归无恙；但它意味着「测试落本后该词立刻出现在划词生词列表」
    的可见性取决于落本存进去的那个档位（见上一条两个分支）。
  - **本条未做的部分（别当已通过）**：没有真人登录翻页**目视**核对生词标注样式与档位下拉框，
    那属 AC-C 段同类、需用户本人 OIDC 会话；本条判据是「行为不变」，由代码路径 + 数据不变式 +
    生产档位域三者证明，而非由人眼证明。ES 侧「无相关新增 ERROR」由 AC-D4 的计数背书（含 `ocabulary` 0 条）。
- AC-D4 ES `app-log-moon-well` 无本功能新增 ERROR（发版后观察 ≥1 天）。
  - **观察窗重算（2026-10-06 03:40）**：本特性 push 后生产 moon-well 被**重启两次**
    （`11:35:29` / `11:35:47 +08:00` 两条 `Starting MagicbookApplication`，终态实例 `11:36:01` 启动完成），
    判据缓存行两次都是 `18345 level words, 25000 ranked words, 8 bands`。所以观察窗以**最后一次重启**为准：
    **到 2026-10-07 03:36Z 才算满 1 天**（此前记的 02:41Z 起算作废）。
  - 窗口内唯一 ERROR：`11:35:40 +08:00 ReadingParagraphCacheService: 阅读缓存 bucket 初始化失败:
    java.lang.InterruptedException`——属**与本特性无关**的模块，且落在「两把发版链对同一次 push 各部署一次」
    的竞态里（第一次启动被第二次重启打断）；第二次启动后未复现。⇒ 记为**发版链并存的副作用**，
    不计入本特性的新增 ERROR，但值得单独议题：moon-well 同时挂着 GHA 与 fnOS webhook-builder，
    **一次 push 会让线上 bounce 两次**（magicbook 只有后者，GHA 已 `disabled_manually`）。
  - **观察窗再顺延（2026-10-06 17:2x 实测）**：今日 `app-log-moon-well` 里 `Started MagicbookApplication`
    共三次成功启动——`07:11:26Z` / `07:14:26Z`（双构建链对同一次 push 各部署一次）/ **`09:25:55Z`**
    （§12.6 记的那次 push，夹带 R103 feat）。按「以最后一次重启为准」的既有口径，
    **满 1 天的时刻变成 2026-10-07 09:26Z**（原记 03:36Z 作废）。
    窗口内计数（`02:41Z` 起，`size=0` 只取 hits.total，日志正文不入对话）：
    `app-log-moon-well` 的 `ERROR` 命中 **9 条**，其中含子串 `ocabulary` 的 **0 条**；
    按异常名提取只出现 `InterruptedException`（启动被第二次部署打断，属上面那条归因）与 `GlobalException`。
    ⇒ 「无本功能新增 ERROR」目前**持续为真**，但收口时刻已到 10-07 09:26Z，别提前打钩。
  - 📌 顺带被动验证到 AC-D1 的另一半：moon-well **R103**（`VocabTestViews.Report` 末尾新增
    `recommendedHardLevel` / `recommendedHardLevelName`，不落列、按落库估算值即时派生）已随 push 上线，
    而 magicbook **R125**（结果页显示建议难度 + 一键应用）仍在本地未 push ⇒ 生产当前正是「老前端 + 新后端」组合；
    实测 `app-log-magicbook` 的 `ERROR` 命中数在「US4 上线 03:37Z 起」与「最后一次 moon-well 重启 09:25:55Z 起」
    两个窗口内**都是 0**（additive 字段被旧前端忽略）——这是 D1「老前端对新后端无感」的第二次实测，
    而且这次连契约形状都变了（不只是新增列）。
- AC-D5 文档同步：✅ **三级文档已就位（2026-10-06 02:10，纯 docs）**。L1 `moon-well/docs/readme/vocabulary.md`——「能做什么」增补词汇量测试条目（自适应二元自评、估算+区间、交卷时可勾选收生词本、中途退出/30 分钟无作答作废、历史可回看），「谁在用」补上阅读设置页入口。L2 `moon-well/docs/vocabulary/hld/hld.md`——新增 `### 5. 词汇量测试（/vocabulary/test/*）`：出题池与 8 档/70 题口径、四端点与 DTO、`seq` 幂等三分支（重发回放/串序 50304/并发撞唯一索引 50304）、提前交卷累计 ≥6 题否则 50303、报告形状含 `addedToNotebook` **null ≠ 0**、30 分钟超时与「作废只由 `start`/`history` 两条必然提交路径落库」、错误码 HTTP 500+`Result.code` 与 401 的分界，以及 ⚠️ 调用方约束「缓存只在启动与每日 04:00（生产本地 +08:00）重载、无手工入口 → 词表数据刚导入完 `start` 必回 50301」；L3 索引补挂本特性主 LLD。L3 = `docs/feat/vocab-size-test/design/vocab-size-test-lld.md`（§5/§6 早已就位）。逐条契约均按 `VocabularyTestService`/`VocabTestParams`/`VocabTestError` 源码复核，未凭记忆。**剩「本 AC 打钩归档」一项，待 D 段跑完再做。**

## D.1 收口底账（2026-10-06 18:10，照抄各条自身判定，不新增结论）

**已经关掉（本文件内已打 ✅ 且有佐证）**：A 段 A1–A4（A2 生产终态 24,981/25,000 = 99.92%）、
B 段 B1/B2/B4/B5/B6/B7 的本机与彩排证据部分、C1/C7/C8、**D1（两半：生产被动实测 + 本地夹具端到端）**、
**D3（三闸口 + 唯一写点结构证明）**、D5 的三级文档同步本体。

**剩下四类，每一类都不是我这侧能单独推进的**：

| 类别 | 具体条目 | 谁能动 |
| --- | --- | --- |
| 需要真人 OIDC 登录 + 浏览器 | AC-C2 完整答题流、C3 键盘/IME、C4 断网重试、C5 Exit 重进、C6 勾选态零落本、**AC-D2「量级相符」那句要用户自己点头**（库里那条 id=3 会话归属未证） | 仅用户本人（本机拿不到 `moonwell_access_token`，且无身份探针会造影子账号） |
| 需要等时间 | AC-D4 观察窗收口 **2026-10-07 09:26Z**；`:292` 陈旧桶窗口在 **2026-10-07 04:00(+08)** 日更后必然关闭（顺带可能被动取得 R9 降级样本） | 到点只读复查即可 |
| 需要单独点头的写生产/上线动作 | push 底账**不在本文写死数字**（写死即自指失效：本文每提交一笔，计数就少一）——执行前实测：`git rev-list --count @{u}..HEAD` + `git log --oneline @{u}..HEAD` 逐笔判类（docs / 运行代码）。18:10 那一刻的实况：magicbook 未 push 的里有并行会话 `7bb1853a` **R125 运行代码**，其余为本 AC 的 docs 笔；moon-well 两笔**全是 docs**。⚠️ 推 magicbook 会连带把 R125 上线（两仓库都走 fnOS webhook-builder，push = 重建部署） | 用户点头后逐仓库确认 |
| 已知瑕疵 / 分支空白（可选代码笔） | #29 题面小写折叠（233 个专名以小写上屏）、#29 撇号放宽（可回收 11 词）、#30 **band→档位 fallback** 无生产实证（注意与 `:292`/R9 就近降级是两个分支，证据不可互用）、#28 moon-well 双构建链一次 push bounce 两次（非本特性） | 用户定夺要不要做 |

B 段那四条「HTTP 级未覆盖」**已被 18:1x 两轮本机彩排实例减到两条**（B1 的 50301、B5 的 `addUnknownToNotebook=false`
零写入 + 差分对照，见上面 B 段各自的新条目），**剩两条**：B3 机器人三型终止形态、F1 大小写不敏感打回路径。
本地夹具演练（D1）不冲抵它们——夹具测的是前端消费侧，50301 那格是前端读码值。

## E. 完成定义

全部 A–D 打钩 + 佐证（截图、us1-report、ES 查询输出）齐备 → response.md（R116/R95）写入回应 → 按「提交≠推送」纪律单独确认 push（涉及发版触发自动上线）。

## F. 产品语义复核结论（US4 对账时暴露的两条，2026-10-05 全部定稿）

1. ~~**测试判「不认识」会把复习过的词打回生词本**~~ **✅ 已复核确认：维持现状（2026-10-05 用户拍板）**
   （AC-B5 校正项 2）：落本沿用 `VocabularyService.unknown` 的 upsert 口径，`familiarity` 一律置 `UNKNOWN`。
   已用「每会话至多落本一次」限制重复打回，但首次打回是设计内的。定夺理由：测试是**自评校准**场景，
   判「不认识」即视为生词，与阅读页点「不认识」同一口径，不改后端、不产生第二套生词语义。
2. **`addedToNotebook = 0` 与 `null` 在结果页都静默**（US4 §2.2，2026-10-05 已确认）：后端保留两种语义（0=执行了落本但本会话无生词，null=本次没执行），仅 UI 不区分。

## G. R125 增量：结果页难度推荐（2026-10-06，moon-well R103 联动）

需求：词汇量测试完成后，按测试结果推荐用户修改阅读难度等级（moon-well R103 报告新增 `recommendedHardLevel/Name`，本仓库负责展示与一键应用）。

| # | AC | 验证 | 结果 |
| --- | --- | --- | --- |
| G1 | 推荐口径由后端派生（bandOf(est)→hardLevelOfBand，capped→GRE(9)，≤0 钳初中），本仓库不重复实现 | moon-well `VocabTestParamsTest` +3 条（锚点映射/全值域单调/钳位顶格）、`VocabularyTestServiceTest` +1 条与两处断言、`VocabularyTestHttpContractTest` +2 字段 jsonPath；moon-well 全量 677 绿 | ✅ |
| G2 | 结果页展示「建议难度等级: {name}」；旧后端无该字段时静默不显示（前端先行部署的降级态） | `vocab-test.js` `renderLevelRecommendation`（`typeof recommended !== 'number'` 早退）；视觉验收待部署后真机 | ✅（代码级）/ ⏳（真机） |
| G3 | 与当前档位一致 → 显示「当前难度等级与该测试结果一致。」且不递按钮 | `renderLevelRecommendation` 的 `currentHardLevel() === recommended` 分支 | ✅（代码级） |
| G4 | 一键应用调**既有** `/ajax/reading-settings/hard-level` 端点（`data-level-url`，复用 `post()` 的 CSRF/401/CSRF 自愈口径），无新代理路由 | `tests/test_vocab_test_proxy.py::test_result_view_renders_level_recommendation_surface` 断言 `data-level-url`；代理层零改动 | ✅ |
| G5 | 应用成功后同步档位卡片：下拉选中值、清各 option 的 `(default)` 后缀、「Current level」行、隐藏「default (not saved)」标签；行文案变「难度等级已更新: {name}」 | `markCurrentLevel`（交叉审查 P2 采纳：后缀清理）；`rs-current-level`/`rs-default-label` 锚点入模板断言 | ✅（代码级） |
| G6 | 应用失败（网络/业务码）行变红「应用失败，请重试。」且按钮可重试；重试成功后颜色复位 | apply handler 的 `code !== 200` 与 `.catch` 分支 | ✅（代码级） |
| G7 | i18n：4 个 mbT 词条进种子且 zh po/.mo 非空；模板按钮 msgid 用 `Apply suggested level` 避开上游误译的 `Apply`（「查询」） | `test_i18n_seed_contract.py` 全绿；po 补丁 `docs/temp/scripts/vt_r125_i18n_patch_po.py`（width=76）+ `pybabel compile` | ✅ |
| G8 | 全量回归 | magicbook pytest 336 绿（含 REPORT fixture 新字段透传） | ✅ |

- **交叉审查留痕（2026-10-06，独立 Agent 评审）**：P1（apply 请求纳入 epoch 作废纪律，迟到响应先复位在途锁、stale 但业务成功仍 markCurrentLevel）与 P2（`(default)` 后缀残留）已修；P3#6（设置卡 load_error 态应用成功后卡片仍显示错误横幅，功能不受影响）**接受不改**——设置加载失败时用户本就会被引导先重试加载，浮层内已有成功确认。moon-well 侧评审结论「无保留意见」，其 P3 注释失实两条（null 防护不可达、band<1 防御分支）已一并修正。
- **端到端待部署后核**：真机完成一次测试 → 推荐行出现 → 应用 → 阅读设置立即生效（G2/G5 的真机证据）。
- 文档同步：us4 §4 报告形状补两字段；本节即 AC 增量。
