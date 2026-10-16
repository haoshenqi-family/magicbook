# magicbook 文档修正项明细（DF1–DF8）

> 状态：任务清单（2026-10-15 建档，全部待启动；均为纯文档活，主检出可直接做，无需 worktree）
> 来源：家族根 [`architecture-review-2026-10-14.md`](../../../../../docs/architecture-review-2026-10-14.md) §5（文档冲突标记）中本仓相关条目；编号沿用原文（N=数值冲突、S=状态滞留、K=口径冲突）便于回溯。
> ⚠️ 执行纪律：本清单只登记任务，本轮未执行任何修正。S1/S2 是「product-review(10-07) §5.2 自称已修但一周后依旧失实」的直接证据（报告 §5 ✅复核坐实）——回填前必须核实 git 历史与部署实况，修完登记验收，不得再产生无闭环的「修正声明」。
> 批次状态（2026-10-15，R185）：**DF1–DF5 已完成**（状态行按 git 里程碑回填 `04c591a3`/`817f4381`/`457067c5`；端口 8085→8083；旧域加取代注记；L1 feat 计数 12→实测 18 且五个悬空 feat 全部有入口，悬空复查为空集）。**DF7–DF8 待启动**（`docs/kb/project-describe/` 空壳待用户定夺、仓库卫生清理涉删文件需先出清单）。
> 批次状态（2026-10-16，R187）：**DF7 部分完成（删目录，AGENTS.md 指向待并行会话释放后改）、DF8 已完成**（`test/` + `None` 删除；「docs/temp 入库」与「运行库入库」两条描述实测失实）。

> 批次状态（2026-10-16，R186）：**DF6 已完成**——L1 分级表的 L2 覆盖改为**逐模块实测表**（7 个模块：reading/vocabulary ✅ 已建，library/learning/companion/credit/admin ⬜ 待升 L2 并逐一给出契约现行落位），并把「待升 L2」标注铺到 6 份承载契约的 L3（此前只有 admin-monitor 一份有，AGENTS.md 声称的标记纪律名实不符）；顺带补了 reading L2 §1 缺的两条现役端点行（`/ajax/reading-tts-cached`、`/ajax/reading-tts-book*`），它们此前只存在于 L3。

---

## DF1 ·（S1）whole-book-translation 状态行回填

- **问题**：`docs/feat/whole-book-translation/design/...md` 头部状态停在「设计已确认，尚未开发」（2026-09-05），实际 L1 `library.md` 与 hld 端点表、cps 代码均已上线多轮。
- **任务**：核实上线里程碑（git 历史日期与 commit），回填状态行为「已上线（日期，commit）」。
- **验收**：状态行 ↔ L1/hld 描述 ↔ 代码实况三者一致。

## DF2 ·（S2）sso-user-unification 状态行回填

- **问题**：`docs/feat/sso-user-unification/design/...md` 头部状态停在「设计草案（待评审）」（2026-08-14），实际 Authentik 统一登录为现役能力。
- **任务**：同 DF1——核实后回填。
- **验收**：同 DF1。

## DF3 ·（N2 本仓侧）oidc-login.md 端口口径修正

- **问题**：`oidc-login.md` 仍写「默认端口 8085」，生产实况为 8083（家族根 Agents.md 端口表「8083/8085」另与 ops「8085 为 UBT 项目已停待清理」冲突——该行修正责任在家族根，见跨仓文档；本仓只修自己的 8085 旧值）。
- **任务**：`oidc-login.md` 端口口径改为 8083（数值同源：以 fnOS compose 生产实况为准）。
- **验收**：全仓文档检索无 magicbook 自身端口的 8085 旧值残留。

## DF4 ·（K1）REQUIREMENTS.md 旧域名加取代注记

- **问题**：`docs/REQUIREMENTS.md:7` 在线站点旧域 `hyh.haoshenqi.top` 未加取代注记（现域 `magicbook.haoyuhang.top`）。
- **任务**：按「历史文档只标注不重写」纪律加取代注记（现域指向），正文保留。
- **验收**：旧域出现处均有取代注记。

## DF5 · 悬空 feat 补索引 + L1 计数失实修正

- **问题**（报告 §5「C-索引完整性」）：
  - 5 个 feat（`ai-reading-companion`、`learning-hub`、`sso-user-unification`、`ted-audio-companion`、`whole-book-tts`）在 L1/L2 零路径引用；
  - **L1 索引自称 12 个 feat，实际 16 个（计数失实）**（`docs/readme/readme.md` 分级表「12 个 feat」）。
- **任务**：L1 readme 索引修正 feat 计数并为 5 个悬空 feat 补引用（或在所属 L2 落引用行）；反向索引纪律：每个 L3 目录必须在 L1 索引或所属 L2 中至少出现一次。
- **验收**：`docs/feat/*` 目录集合与 L1/L2 引用集合差集为空；计数与实际一致。

## DF6 · L2 覆盖补齐（2/7 → 明确口径）

- **问题**：L2 hld 仅 reading / vocabulary 两份（2/7 模块），其余模块契约散在 L3 design。
- **任务**：按「其余模块契约先落 L3 design 并标注『待升 L2』」的现行口径，在 L1 分级表注明各模块 L2 状态；新模块 L2 随功能演进补齐（不必一次性补全，但口径要明示）。
- **验收**：L1 分级表的 L2 覆盖描述与实际一致，无「已建 7 份」类失实。

## DF7 · `docs/kb/project-describe/` 空壳待决策

> 状态：**部分完成**（2026-10-16，R187）。按用户选定范围执行「只删空壳目录」——目录及其唯一内容
> `.gitkeep` 已从仓库移除（commit 见本轮）。**未做的那一半是刻意的**：`AGENTS.md` 第 12 行（前置阅读）
> 与第 121 行（目录表）仍写着「`docs/kb/project-describe/` 仍为空壳、填实或删除属待决策项」，
> 而该文件正被并行会话持有未提交改动（2 行文档规范回填），把别人的在途改动一起提交不符合并发纪律，
> 故本轮不动。**遗留（一句话可做完）**：待 `AGENTS.md` 空闲时，把第 12 行的括号说明与第 121 行整行删掉
> ——目录已不存在，这两处是指向不存在路径的悬空引用。

- **问题**：该目录仅 `.gitkeep`，AGENTS 前置阅读指向空目录并自注「待决策」（报告 §5「C-文档体系结构性缺陷」第 5 条）。
- **任务**：**需用户定夺**——填实（以 L1 模块表为源建 project-intro）或删除（同步修订 AGENTS.md 前置阅读指向为 `docs/readme/readme.md`）。两个方向均涉约定变更，不擅自执行。
- **验收**：决策落地且 AGENTS.md 前置阅读指向有效。

## DF8 · 仓库卫生清理

> 状态：**已完成**（2026-10-16，R187，用户逐条确认删除清单后执行）。本轮实测把清单里的三条各自核了一遍：
> ① 「`docs/temp/` 整套 epub/mp3 运行产物入库」**失实**——`git log --all -- docs/temp` 全史无一次提交，
> 该目录只存在于工作树且已被 `.gitignore` 忽略（本轮补规则后在 53 行；683MB 全是本地探针夹具与产物，不进仓库）；
> ② `test/`（3 个跟踪文件，Calibre-Web 原版 QUnit runner 残留，204K）已删除——pytest 的 `testpaths` 只认
> `tests/`、全仓零引用，另补 `.gitignore` 的 `/test/` 防再次误入；
> ③ 根目录空文件 `None`（0 字节，`83e0ec09` 2026-10-15 误入）已删除；「运行库入库」这条同样失实——
> `git ls-files` 无任何 `.db/.sqlite/.log/.sql` 运行产物（`docs/feat/*/sql/*.sql` 是设计文档的正本 DDL）。

- **问题**（报告 §3.2 🟡 / §5 结构性缺陷第 4 条）：
  - `docs/temp/` 整套 epub/mp3 运行产物入库；
  - `test/`（原版残留）与 `tests/` 并存；
  - 根目录 `None` 空文件、运行库入库。
- **任务**：逐项清点后处置（`.gitignore` 补规则 / 移出跟踪 / 删除空文件）。⚠️ 涉及删除文件，执行前向用户出示完整清单确认。
- **验收**：`git ls-files` 无上述产物；`test/` vs `tests/` 的去留有明确决策记录。

> **`test/` vs `tests/` 的决策记录**：留 `tests/`、删 `test/`。`test/` 是上游 Calibre-Web 的 QUnit
> runner 残骸（一个测试汇总 HTML + runner.css/js，全仓无任何引用它的地方），本仓 pytest 的
> `testpaths = ["tests"]` 只认 `tests/`；删除后在 `.gitignore` 补 `/test/`（52 行），防止同步上游时
> 再被带回来。这条就是上面「验收」里要求的那份去留决策记录。
