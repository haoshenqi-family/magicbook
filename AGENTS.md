# 🤖 AGENT INSTRUCTIONS

> 🟢 **加载确认**：读取本文件后，请首行回复：`✅ AGENTS.md 已激活 | 语言：中文 | 模式：严格遵循工作流`

---

## 🔄 核心工作流 (Core Workflow)
接到用户任务时，**必须严格按以下顺序执行**，禁止跳过或合并步骤：

1. **任务分类**：判断当前任务属于下方 `## 📋 任务分类与执行策略` 中的哪一类。
2. **状态同步**：向用户回复 `🔍 正在执行 [任务类型] 类任务`。
3. **前置阅读**：除非任务明确与项目无关，否则**必须优先阅读** `docs/product/readme/readme.md`（L1 模块索引，R129 起）与 `docs/product/REQUIREMENTS.md`；产品需求全册与模块功能以它们为入口。
4. **执行对应流程**：严格按分类指南逐步操作，并在关键节点输出确认信息。

> 💡 提示：在实际执行中，请将路径中的 `<ITER>`（迭代）、`<工作项>`、`<FEATURE>` 和 `<USER_STORY>` 替换为当前任务的实际名称/编号。文档物理布局（product 静态 / project 动态）见下方「项目文档规范」与家族仓 `../ops/docs-architecture.md`。

---

## 🔀 Git Worktree 使用规范（2026-10-10 R147 增补；2026-10-23 ops R158 修订命名并增补同编号互斥；家族统一口径见 ../AGENTS.md「Git Worktree 开发纪律」）

> **模式：一任务一临时 worktree，合并后保留待验收，验收通过后删除**。先例：R144 发布态全量复跑正是用干净 HEAD worktree 才把 25 个失败定性为本地运行态污染而非代码回归；本仓并行会话多，主检出不宜直接切分支开发。

- **何时必须用**：编码类任务（含 bug 修复）开工时创建专属 worktree 开发，**不得在可能被并行会话共用的主检出上直接改分支**；纯问答、排查、文档微改可在主检出直接进行。
- **一次会话一个 worktree（2026-10-12 moon-well R164 同源增补；家族统一口径第 7 条）**：同一会话内的连续工作（含多阶段/多子任务）必须**复用同一个 worktree**——阶段收尾 merge 回开发分支后不删树，续作前 `git fetch` 并 merge `origin/<开发分支>` 拉齐基线继续推进；**禁止每阶段/每子任务各开新树**（反面样本：moon-well R162 重构五阶段 + NAS 下线累积 6 处驻留）。跨会话续作优先复用台账登记的该任务 worktree；仅并行会话允许并存多树。
- **创建**（位置必须在仓库目录外的兄弟目录，命名 **`magicbook-r<编号>-<slug>`**，目录名与分支名的编号一致——2026-10-23 ops R158 修订，原 `<任务slug>` 不带编号、同一任务可被起成两个名字，无法作互斥判据；先 `git fetch origin`，从 `origin/develop` 最新点切出）：
  ```bash
  git worktree add ../magicbook-r<编号>-<slug> -b <type>/r<编号>-<slug> origin/develop
  ```
- **同编号互斥（2026-10-23 ops R158；家族统一口径第 9 条）**：一个 request 编号同时只允许存在一个 worktree——目录名带编号后由文件系统天然强制，同编号目录已存在时 `git worktree add` 直接失败，此时**禁止换 slug 绕开**：是验收期驻留 → 按「一次会话一个 worktree」条在原 worktree 续作；是另一并行会话在途 → 协调而非并行开工；是登记外残留 → 向用户报告，不擅删。互斥粒度钉在编号（功能）级，不升到模块级（同模块多需求并行是常态，跨功能的同文件冲突由「从 origin 切出」的基线纪律兜底）。
- **收尾闸门（merge 后不立即删除，等验收）**：
  ```bash
  git merge <type>/r<编号>-<slug>        # 在主检出 develop 上执行
  ```
  merge 完成后 worktree **原样保留**，等用户验收；验收通过后执行删除：
  ```bash
  git worktree remove ../magicbook-r<编号>-<slug>
  git branch -d <type>/r<编号>-<slug>    # 只用 -d：未合并会被 git 拒绝，此时停下排查
  ```
  **禁止 `branch -D`**（会吞掉未合并提交，属破坏性操作，必须先经用户确认）；worktree 内有未提交残留导致 remove 被拒时，先向用户出示 diff 再处置，不得静默丢弃。
- **验收期驻留（正常状态）**：merge 后未验收的 worktree 属正常驻留，须在当轮 response.md 登记分支名与合并 commit，验收通过后立即删除；用户明确否决的改动，处置方式（revert merge / 保留分支）由用户定夺。本仓验收优势：worktree 干净检出 + 主检出 `.venv` 复用（`../magicbook-r<编号>-<slug>` 目录下 `../magicbook/.venv/bin/python -m pytest`）＋拷贝当轮运行期文件即可真机整站验收（R144 已验证该姿势）。
- **长任务例外**：跨多会话、未到 merge 点的任务同样驻留 worktree，须登记分支名、日期与原因；任务关闭时按闸门收尾。
- **收尾失败留台账**：任务中止、冲突未解等无法完成闸门时，必须在 response.md 记录 worktree 位置、分支名与原因，禁止静默滞留。
- **本仓适配**：
  - 主检出 `.venv` 可直接复用（2026-10-10 R146 实测：在 worktree 目录执行 `../magicbook/.venv/bin/python -m pytest tests/...`，flask 导入与 pytest 收集正常），无需每个 worktree 重建虚拟环境；`.venv` 本身不入 worktree（gitignore）。
  - worktree 内**没有** `library/`、`app.db` 等被 gitignore 的运行态——这正是「干净复跑」的原理（R144 先例），但整站手工验收仍需主检出或完整环境。
  - 发布流程不变：仍按上方「Git 分支管理」节，仅发布时 merge `develop` → `master`。

---

## 📋 任务分类与执行策略

### 📦 1. 需求理解 & 系统设计
- **目标路径**：`docs/project/iterations/<ITER>/<工作项>/hls/md/*.md`（原始需求与标准化 md）；本次实现设计落同目录 `lld.md`（LLD）
- **执行要求**：
	- HLS 文档极度精炼，**逐句解析**，严禁跳过任何背景、目标或限制条件。
	- 遇到不确定的概念/术语，**立即查阅资料或向用户提问**，禁止主观猜测或假装理解。
	- 充分理解需求后，输出系统设计草案供用户确认。

### 💻 2. 编码实现
- **必读文档**： `docs/kb/instructions/coding/*.md`
- **目标路径**：LLD `docs/project/iterations/<ITER>/<工作项>/lld.md`
- **执行要求**：
	- **单线程开发**：每次仅处理 1 个 User Story，完成并验证后再进入下一个。
	- **注释规范**：先写注释阐明 `Why`（业务意图/约束条件），再写 `How`（实现逻辑）。
	- **交付标准（两级单测闸门，2026-10-08 R131 修订）**：代码完成后必须确保项目可正常启动；单元测试按阶段分两级执行：
		- **开发态（默认）**——日常编码 / bug 修复只跑**部分单测**：本次新增或改动的用例必须全绿，再补跑受影响模块的相关测试文件即可，**不要求全量**。命令形如 `.venv/bin/python -m pytest tests/test_reading_vocabulary.py`。
		- **正式发布态**——仅当**用户显式提出「正式发布 / 上线」**（或按下方「Git 分支管理」把 `develop` 合并 `master` 发布）时执行一次**全量单测** `.venv/bin/python -m pytest tests/`，以 0 失败为交付判据，并把用例总数写入 `response.md`；退出码须读 pytest 末行汇总，不要用管道末端返回值判定。
		- ⚠️ push `develop` 即触发 fnOS 构建自动上线（见 `../ops/runbook.md` §1；2026-10-21 R190 起 **GitHub Actions 链**对「纯文档 push」跳过构建与部署——本仓 GHA 已停用，属预案，fnOS 链未加同一判据），因此全量闸门以用户显式指令为准；开发期跳过全量的跨模块回归风险由该闸门兜底。
	- **Code Review**：完成后主动切换模型/Agent 视角进行交叉审查，确认无误后再提交。

### 🔍 3. 验收 (AC 对齐)
- **目标路径**：`docs/project/iterations/<ITER>/<工作项>/ac/<USER_STORY>-ac.md`（若存在）
- **执行要求**：
    - 所有验证点必须全部验证，不可以跳过。条件不足则请求用户提供更多信息。
    - 逐条核对 AC，**重点关注后端实现逻辑**，严禁遗漏任何一条。
    - 复杂场景拆分步骤执行，分步骤验证。
    - 编写测试用例：必须覆盖 Happy Path + 边界条件 + 异常场景。
    - 验收完成后，输出详细的验证报告，包含每条 AC 的验证结果和截图/日志等佐证材料。最后 回复 `✅ 所有 AC 已覆盖验证`

### 🧪 4. bug修复
- **执行要求**：
  - 阐述bug产生的原因、修复方案和验证方法，确保修复后不影响其他功能。
  - 修复完成后更新单元测试并验证通过
  - 更新AC并验证通过

### 🛠 5. 细节修改 & 知识沉淀
- **执行要求**：按需查阅对应迭代工作项目录（`docs/project/iterations/<ITER>/<工作项>/`）、产品侧文档（L1/L2/L3）与 `docs/kb/`。修改完成后，同步更新相关 KB 或决策记录。

### 🌐 6. 项目无关任务
- **适用范围**：简单问答、百科查询、Skill 创建、工具配置等。
- **执行策略**：直接高效响应，无需加载项目文档或触发工作流。

---

## 📁 项目文档规范 (Docs Structure · v2 静态 product / 动态 project 二分)

> 权威约定见家族仓 [`../ops/docs-architecture.md`](../ops/docs-architecture.md)（v2 二分体系与迁移映射）。本节只定本仓落位；与家族册冲突时，先改家族册、再同步本节。

文档按 **静态（product：产品现在长什么样）/ 动态（project：这次、最近改了什么）** 二分。**L1–L3 仅指产品侧静态文档**；原 L2/L3 里的 HLD/**LLD 已拆出去**——「功能 / 接口是什么」留在产品侧，「**这一次怎么实现**」= LLD，归 project 迭代。新建文档一律按下表落位：

| 级别 | 位置 | 读者 | 内容 | 维护时机 |
|------|------|------|------|----------|
| **L1 用户文档** | `docs/product/readme/` | 使用者 | 系统 README + 每模块一份：**只讲功能**，不涉及代码与实现（✅ 索引 + 7 模块） | 新模块上线 / 用户可见能力变化 |
| **L2 接口说明** | `docs/product/<module>/interface.md` | 调用者 / 集成者 | **功能定义 + 功能说明 + 调用方法**（代理端点映射；✅ 首批 reading/vocabulary，其余模块随演进补齐、未建时以 L3 为准） | 新增子功能 / 接口契约变化 |
| **L3 实现说明** | `docs/product/<module>/features/<FEATURE>.md` | 修改者 | **实现方式 + 边界条件**（仅改本功能时需要读；尚未新建，历史实现说明在 `docs/project/_legacy/feat/`） | 每次功能开发 |

| 路径 | 用途与操作规则 |
|------|------|
| `docs/` | 所有项目文档根目录 |
| `docs/product/` | ▶ **静态 · 产品**文档根：描述产品现在长什么样 |
| `docs/product/readme/` | L1：索引 `readme.md` + `<module>.md`（每模块一份） |
| `docs/product/<module>/interface.md` | L2 接口说明 |
| `docs/product/<module>/features/<FEATURE>.md` | L3 实现说明（从新功能开始建） |
| `docs/product/REQUIREMENTS.md` | 产品需求全册（产品级静态文档，非模块级） |
| `docs/product/reading-vocabulary.md` | 跨 reading / vocabulary 的静态实现说明（L3 性质） |
| `docs/project/` | ▶ **动态 · 项目 / 迭代**文档根：记录这次、最近改了什么 |
| `docs/project/requests/` | 需求台账：`requests.md` / `response.md` + `requests-archive/` / `response-archive/` |
| `docs/project/tasks/` | 任务看板（原 `docs/tasks/` 并入）。完成后标记 `Done`（**严禁删除**）；指派任务须明确到 Agent 并复核反馈 |
| `docs/project/iterations/<ITER>/plan.md` | 本次迭代计划（对应 PingCode 迭代 / 版本） |
| `docs/project/iterations/<ITER>/<工作项>/lld.md` | **LLD：这次怎么实现**（头部必须有 `状态` 行：设计 / 开发中 / 已上线） |
| `docs/project/iterations/<ITER>/<工作项>/hls/raw/` | 原始 HLS（**只读**，禁止修改） |
| `docs/project/iterations/<ITER>/<工作项>/hls/md/` | 标准化 Markdown 版 HLS；缺失时用 `docx2md` 转换后放入并向用户确认 |
| `docs/project/iterations/<ITER>/<工作项>/{ac/,test-case/,raw/,sql/}` | 本次交付的过程产物（验收标准 / 测试用例 / 原始资料 / 数据库脚本） |
| `docs/project/_legacy/feat/` | **冻结归档**：老 `docs/feat/`（18 个）整体搬入，**不回溯迭代归属、不逐功能拆分** |
| `docs/kb/` | ▶ **共享知识**：项目信息、实体、编码规范、工作流等（跨产品长期存在） |
| `docs/kb/entity/` | 实体说明文档 |
| `docs/kb/instructions/coding/` | 编码规范文档 |
| `docs/kb/instructions/workflows/` | 工作流指导文档 |
| `docs/kb/sql/` | SQL 相关文档 |
| `docs/superpowers/` | 保留原位（历史设计草稿） |
| `docs/temp/` `docs/temp/scripts/` | 临时文件 / 脚本，**不跟踪 Git** |

**三级联动纪律（v2 重述：2026-10-07 R128 原始，2026-10-16 R188 改口径）**：功能交付前四问——① 用户可见能力变了吗 → 写 L1（`docs/product/readme/<module>.md`）；② 对外行为 / 接口变了吗 → 写 L2 `interface.md`；③ 实现方式 / 边界条件变了吗 → 写 L3 `features/<FEATURE>.md`；④ **这次怎么实现** → LLD 落 `docs/project/iterations/<ITER>/<工作项>/lld.md`，**LLD 头部必须有 `状态` 行**（设计 / 开发中 / 已上线），里程碑时回填，禁止长期滞留失实状态（先例：R127 一次修出 4 份「尚未开发」实已上线的文档）。
**数值同源**：端口、时效、模型名等口径以生产实况（fnOS compose、`.env`）与 moon-well 现行契约为准，禁止沿用裸机时代或旧架构快照。
**历史文档只标注不重写**：被取代的设计加「已被取代」横幅指向新文档（先例：ai-reading-companion 实现计划）；「临时调整」若转为常态，改写为正式决策并注明日期；`docs/project/_legacy/feat/` 内的历史文档一律**只读不改**。
**一致性纪律**：模块/功能清单以 `cps/` 实际代码与阅读器路由为准；文档状态行 ↔ git 历史 ↔ 实际部署三者对齐，发现漂移随手修正。

---

## 🔀 Git 分支管理

> **默认开发分支：`develop`**。`master` 仅用于发布。

- **日常开发**：一律在 `develop` 分支进行（编码、测试、提交、推送）。
- **发布流程**：仅当需要发布新版本时，才将 `develop` 合并到 `master` 并推送。
- **禁止**在 `master` 上直接开发或临时提交；非发布场景不得向 `master` 推送。
- 切换分支前先 `git status` 确认工作区干净，避免运行数据丢失（见下方「不纳入 Git」）。

### 🚫 不纳入 Git 的内容

以下属于运行数据 / 敏感信息，**禁止**提交（`.gitignore` 已覆盖，新增同类文件必须保持忽略）：

| 类别 | 示例 | 原因 |
|------|------|------|
| Calibre 书库 | `library/*/`、`library/metadata.db` | 书库索引与书籍为运行数据；git 跟踪会在切分支时被删除，导致图书丢失 |
| 应用数据库 | `app.db`、`*.db`、`gdrive.db` | 本地运行数据、凭据 |
| 密钥凭据 | `.env`、`.key`、`gdrive_credentials`、`client_secrets.json`、`gmail.json` | 敏感信息 |
| 日志 | `*.log` | 运行日志 |
| 临时文件 | `docs/temp/` | 不跟踪 |

> ⚠️ `library/metadata.db` 曾因被 master 跟踪而在切分支时丢失（BOOK-20260829），已从 git 移除跟踪。新增书库相关文件时必须保持忽略状态。

---



## 1. 内网设备（192.168.31.0/24）

> **拓扑与设备事实的唯一权威源：ops 仓库 `servers` 分册 与 app-manager `docs/kb/truth/server.md`**（2026-10-08 R117/R129/R29/R35 指针化：本表原先在四份 AGENTS.md 中各存一份副本，与 ops、truth 共六处维护，现收敛为两处权威源；冲突以权威源为准）。
> 常用速查：飞牛 NAS（fnOS）`192.168.31.9` · Ubuntu 开发机 `192.168.31.11`（外网代理 naive `:12811`）· 公网统一入口 Server 2 `116.62.200.90`（Traefik :443）。


---


## 📝 对话记录 (docs/project/requests/ · requests.md / response.md)

- **位置（2026-10-16 R188）**：需求台账已从仓库根迁入 `docs/project/requests/`（`requests.md` / `response.md` + `requests-archive/` / `response-archive/`）；本节下文凡称 `requests.md` / `response.md` / 归档目录，均指该目录下对应文件。
- **`requests.md`**：仅记录每一次对话用户的需求，除此之外不做任何事情。**接到任务后立即追加编号占位（占号即 push，2026-10-23 ops R158）**：按 `origin` 最新台账取当前最大编号 +1 写入需求原文，随即**只含该文件 commit 并 push 到 develop，push 成功才算占到号**；被拒即有人先占，`rebase` 后重算编号再 push；本地 develop 领先远端（有待点头的未 push 提交）时用临时 claim worktree 占号，序列见 `../ops/dev-workflow.md` §1 步骤 4。（原「写入即锁定」口径废止：并行会话各自工作区的写入互不可见直到 push，moon-well 152/154 两次撞号即此。）
- **`response.md`**：任务**完成后**再写入回应（编号对应 requests.md 开始时占用的条目），包括：
  - 对每个 request 的回应；
  - 对 requests.md 与 response.md 两个文件的总结。
- **编号纪律**：编号只追加、不回改、不重排；并行会话若仍出现重复编号，不修改既有记录，续编下一个空号，并在 response.md 冲突记录中说明。
- **冲突记录**：若 request 之间存在冲突，必须在 response.md 中记录。
- **归档**：`response.md` 只保留最近 10 个 request 的回应。**任何写入使条目数超过 10，立即把最早超出窗口的回应原样搬移**到 `response-archive/response-R<起>-R<止>.md`（如 `response-R11-R20.md`；孤立单条可命名 `response-R16.md`），并在 `response.md` 顶部归档索引登记；只搬移原文，不总结、不改写。（2026-10-08 修订：原「逢 10 的整数倍触发」在 R110/R120 等触发点多次被跳过致窗口失控，改为写入即检查。）**requests 归档（2026-10-08 新增，R134）**：`requests.md` 中已确认完成且过时的条目按编号区间原样搬移到 `requests-archive/requests-R<起>-R<止>.md`（孤立单条 `requests-R<N>.md`），只搬移原文、不总结、不改写、不改编号；未完成的与有经验教训价值的条目保留；`requests.md` 顶部维护归档索引。归档不释放编号——新任务仍取全史最大编号 +1。（原「requests.md 永不归档」条款同日废止。）
- **查历史**：需要更早的回应细节时，按 request 编号到 `response-archive/` 对应文件检索，不要把全量历史读进上下文。
- **原则**：尽量简单。

---

## 🌐 语言与术语规范
- **默认语言**：中文
- **术语保留**：技术栈/工具名保持原文，**禁止翻译**（如 `Maven`, `Spring Boot`, `MyBatis-Plus`, `XXL-JOB`, `Druid`, `CyberArk` 等）

---

## 📖 扩展阅读
项目全局背景、架构约定、环境配置等详细信息均存放于 `docs/kb/` 目录下，按需查阅。
