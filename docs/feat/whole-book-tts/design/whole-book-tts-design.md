# 整本朗读（TTS 预生成）设计

状态：设计定稿 v3（2026-10-12 两轮拍板齐全：D1–D4 + 整本选角 + MiMo 默认 + 听=消费 + 积分体系×10；可进开发）
需求：2026-10-12「llm 已经重构，整本翻译功能有了，需要一个类似的整本使用 TTS 生成朗读的功能」（magicbook R163 / moon-well R165）；同日二轮拍板：听=消费（命中也扣）、积分体系×10（注册 1 万 / 充值×10 / 1k token 折 10 积分）、家人送积分用既有 admin adjust（magicbook R164 / moon-well R166）。

## 0. 检查结论：功能不存在；且 /tts/speak 现状零计费

对四条既有链路逐一核实（代码级，非记忆）：

| 既有能力 | 现状 | 与本需求的差距 |
| --- | --- | --- |
| moon-well `/tts/speak` | 段落级**同步**合成；缓存键 = SHA-256(trim(段落原文))，bookName/chapter 非空即永久缓存（ES 引用 + MinIO `reading-tts/`）；**ReadingTtsService 直调 TtsProviderChain，不经 AiGateway.speak——缓存命中与 miss 合成都不扣积分**（DefaultAiGateway.speak 的字符计费能力已建好但无消费方） | 无批次、无进度、无后台批量、无计费 |
| magicbook R157 整本连播（epub.js `bookPlayer`） | 前端播放队列，逐段在线请求 `/ajax/reading-tts`，**边播边合成** | 首听每段等几秒~几十秒（长段最长 78.6s）；预生成靠手工 |
| magicbook R142 整本预热 | fnOS 宿主机 `tts_warm.py` 手工脚本（不入 Git），book 145《Matilda》1393 段全量跑通并验证缓存键口径 | **运营态方案，零代码**；无产品入口、无进度 UI |
| moon-well llm_task TTS 任务型 | R162 P4 收口后 = **外部 worker 领用契约**（进程内执行器对非 TEXT 显式快速失败），无 worker 部署 | 队列路径不通（维持 P4 遗留④原判，本设计不消费） |

**结论**：整本 TTS 预生成（一键发起 → 后台批量合成 → 进度可查 → 完成后零等待听书）**不存在，需新建**。R142 脚本验证的链路（逐段调 `/tts/speak` 写永久缓存）正是本设计要产品化的对象。

**默认模型确认（拍板项）**：`tts.fallback-chain` 默认 **`mimo,local,dashscope`——小米 MiMo v2.5 TTS 已是第一顺位（音质最优注释），零改动即满足「默认用小米 TTS」**。MiMo 100 RPM 上限 vs daemon 串行 0.8s 段间隔 ≈ 75 RPM，留 25 RPM 余量给阅读器即时朗读，合规。⚠ 部署检查项：Nacos 若覆盖过链序列表须写**完整列表**（列表键按下标合并的坑，application.yml 注释明示）；上线时以 Nacos 实际快照为准回读确认。MiMo 环 30s 超时失败自然回落 local（180s）——链路既有语义，长段兜底成立。

## 1. 目标与非目标

**目标**：书详情页一键为整本书预生成朗读音频；**发起前先按书的元信息 AI 选角（音色 + role 风格提示词），整本统一**；后台逐段合成进 moon-well 永久缓存；进度/失败/重试可见；幂等（发起者重跑不重复扣）；**计费分层落地（调用者听=消费每次请求扣、发起者按字符、命中语义分侧）**；**积分体系×10（注册/充值/token 换算）**；完成后 R157 连播与单段朗读全程毫秒级命中。

**非目标**：
- PDF、TXT（与整本翻译、连播口径一致，仅 EPUB/KEPUB）；
- 不做「全部英文书批量」（串行算力下无意义）；
- 不做 find-audio 批量探测端点（拍板 D4，注意点见 §6）；
- 不改 R157 连播与前端朗读逻辑（自动受益）；不动 llm_task TTS 任务型（P4 遗留④维持）；
- 划词翻译（单词级）、批注、口语、写作等其他 AI 能力的计费**不在本期**（purpose 配置体系天然支持后续按需开，见 §4.2）；
- 段落翻译/单词详情的**命中扣费**不随 TTS 对齐（见 §4.2 注；用户「听=消费」语境为收听侧）。

## 2. 决策记录（2026-10-12 两轮拍板）

| # | 决策 | 拍板结果 |
| --- | --- | --- |
| D1 | 执行架构 | **方案 A**：magicbook 批次 + daemon 逐段直调 `/tts/speak`，写永久缓存 |
| D2 | 计费 | **分层**：发起者（整本预生成）1000 字符=1 积分；调用者朗读 **1 段=1 积分**；段落翻译、单词详情改按次（1 段 / 1 次 = 1 积分） |
| D2'（二轮） | 收听计费语义 | **听=消费：调用者每次请求一段即扣 1 积分，缓存命中也扣**（计费点前移到入口）；发起者批量侧维持「命中免费」（幂等重跑不重复扣） |
| D2''（二轮） | 积分体系×10 | 注册送 **1 万**（原 1000）；充值套餐积分**×10、价格不变**（R56 先例第二次）；文本链 **1k token 折 10 积分**（原折 1）；内容按次单价（1 段/次=1 积分）与发起者字符单价（1000 字符=1 积分）**不变** |
| D3 | 范围 | 仅书详情页单本入口（admin） |
| D4 | moon-well 探测端点 | **不做 find-audio**：靠缓存键（SHA-256(段落原文)）天然幂等——miss 才合成，命中直接返回 |
| 新增 1 | 整本选角 | 预生成前先把**书的元信息**告诉 AI，由 AI 选合适音色 + role（风格）提示词，整本统一使用 |
| 新增 2 | 默认模型 | 确认默认 TTS = 小米 MiMo（**现状已满足，零改动**，见 §0） |
| 新增 3 | 送积分 | 家人积分走**既有 `POST /credit/admin/adjust`**（零开发）；外部用户走既有充值链路 |

## 3. 总体设计

### 3.1 magicbook 侧（主体改动）

**新模块 `cps/reading_tts/`**，镜像 `reading_translation/` 结构：

```
cps/reading_tts/
├── __init__.py
├── models.py       # ReadingTtsJob / ReadingTtsJobItem
├── extractor.py    # 朗读口径段落提取器（§3.3，不复用翻译 parser）
└── service.py      # WholeBookTtsService（start/progress/retry/cancel + daemon 合成线程）
```

**数据模型**（镜像 TranslationJob/Item；无探测端点后计数简化——不区分 cached/synthesized，只关心段状态）：

`reading_tts_job`：id / user_id / book_id / book_format / book_name / **book_author / book_summary（选角输入，§5）** / book_fingerprint / status（RUNNING / COMPLETED / PARTIAL_FAILED / CANCELLED）/ total_count / done_count / failed_count / **voice / style（选角结果留档，供批次页展示与排查）** / created_at / updated_at。

`reading_tts_job_item`：id / job_id / paragraph_index / chapter / text / text_hash（SHA-256，unique(job_id, text_hash)）/ status（PENDING / DONE / FAILED）/ error_message / attempt_count / created_at / updated_at。**无 task_id 列**（`/tts/speak` 同步无任务号）、**无产物列**（音频在 moon-well 缓存，本仓不落任何音频）。

**服务流程**（复刻翻译 start 骨架）：

1. `start(book_id, book_format, force)`：书文件校验（EPUB/KEPUB）→ 指纹（path:size:mtime）→ 幂等复用（同 user+book+fingerprint 活动批次静默复用）→ 僵尸自愈（updated_at 停滞 >30min 置 PARTIAL_FAILED 关闭）→ 朗读口径提取（§3.3）→ 按 text_hash 去重建 job+items → **调 moon-well 整本选角端点（§5，失败不阻断：回落 moon-well 内部默认选角）** → spawn daemon → 立即返回 progress（HTTP 只承诺受理；整本发布在请求线程必被网关超时杀死——翻译 HP2 3160 段实测教训）。
2. **daemon 合成线程**：串行逐段（仅 PENDING）POST moon-well `/tts/speak`，payload `{text, bookName, chapter, source: "book-tts-batch"}`（source 标记 = 发起者计费通道，§4）；客户端超时 ≥200s（服务端 local 环 180s + 余量；R142 实测最长段 78.6s）；段间 0.8s 限速（≈75 RPM < MiMo 100 RPM；**命中段也 sleep**——daemon 不识别命中，简单且安全）；失败原地重试 1 次，再败置 FAILED 留 error_message；线程内自建 DB session（scoped_session 不能跨线程）；**批次表即断点台账**（R142 done.jsonl 的产品化），容器重启丢线程由 retry/start 幂等兜底。
3. `progress(job_id)`：计数聚合（total/done/failed + 按 done 速率的 ETA 滑动平均）。**无缓存懒回收**（find-audio 不做；「省了多少」从积分流水看，见 §6）。
4. `retry(job_id)`：FAILED 段重跑；幂等（发起者命中免费）。
5. `cancel(job_id)`：置 CANCELLED；daemon 每段开跑前查批次状态，见 CANCELLED 即退出。

**路由**（镜像翻译四件套，全部 `admin_required`）：

- `POST /ajax/reading-tts-book` `{book_id, book_format, force}`
- `POST /ajax/reading-tts-book/status` `{job_id}`
- `POST /ajax/reading-tts-book/retry` `{job_id}`
- `POST /ajax/reading-tts-book/cancel` `{job_id}`

身份传递：与翻译 publish 闭包同理——daemon 线程无 Flask 上下文，令牌在请求线程定格为快照传入（R51/R145 教训）。daemon 请求带发起者（admin）身份头（R142 同款：magicbook 代理透传 OIDC 令牌），moon-well 侧 UserContext = 发起者 → 计费挂发起者。

**UI**：`detail.html`「整本翻译」按钮旁加「整本朗读」按钮（admin）；确认弹窗展示 `{总段数, 总字符, 预估积分上限}`（§4 口径，上限 = 全 miss 假设；文案注明「已缓存段落自动跳过、不重复计费，实际以积分流水为准」）+ 选角结果预览（voice + style，选角失败则显示默认）；进度轮询复用翻译进度样式 + ETA。

**阅读器零改动**：R157 连播按段落文本请求 `/ajax/reading-tts`，预热后全量命中（收听按段计费见 §4.1，由 moon-well 侧自动生效）。

### 3.2 moon-well 侧改动清单

| # | 改动 | 说明 |
| --- | --- | --- |
| 1 | `/tts/speak` 增加可选 `source` 字段 + 计费接入 | `source=book-tts-batch` → 发起者侧：**miss 合成时** floor(chars/1000) 扣（落点走 `aiGateway.speak`——字符计费现成，仅把 ReadingTtsService 的 providerChain 调用按 source 分流），**命中 0**；无 source（阅读器）→ 调用者侧：**每次请求扣 1 积分（命中也扣，§4.1）** |
| 2 | 新端点 `POST /tts/book-voice/select` | 整本预选角（§5）：入参书元信息，upsert `tts_book_voice` |
| 3 | `PromptDefinitions.TTS_BOOK_VOICE` 扩展变量 + Nacos 模板同步 | 加 bookAuthor / bookSummary / language 变量（§5）；Nacos 更新走程序化重建+结构断言（R162 P2 事故教训） |
| 4 | `CreditBillingProperties` 扩展 per-call 配置 | purpose 级按次计费白名单（§4.2），Nacos 热调 |
| 5 | 文本链计费切换（网关单点） | purpose 命中 per-call 白名单时交互路径按次扣；`TOKENS_PER_CREDIT` 参数化（1 千 token 折 10 积分，Nacos 可调，§4.3） |
| 6 | 积分体系×10 | `credit.new-user-grant` 1000→**10000**；`CreditRechargePackage` 档位积分×10 价格不变（R56 先例第二次，§4.3） |
| 7 | OpenApiConfig 分组 | 新端点并入「阅读朗读 TTS」组 |

`/tts/speak` 的回落链（MiMo → local → dashscope）、缓存写回、Media-Type 判定全部原样；`POST /credit/admin/adjust`（送积分）**现状已有，零开发**。

### 3.3 段落提取口径（核心风险点）

**Why 不能复用整本翻译的 `reading_translation/parser.py`**——两套口径系统差异，预生成用错口径 = 缓存键与前端请求键对不上 = **白合成**（烧积分 + 算力）：

| 维度 | 前端朗读口径（epub.js，缓存键的消费者） | 翻译提取器（parser.py） |
| --- | --- | --- |
| 元素集 | `PARAGRAPH_SELECTOR = 'p, li, blockquote, h1..h6, div'`；DIV 含块级子元素跳过；嵌套按 querySelectorAll 语义**双收** | `BLOCK_TAGS = {p, li, blockquote, pre}`；有块级祖先的节点**跳过**（只收最外层） |
| 文本 | `textContent` → `\s+`→`' '` → trim | `itertext()` 拼接 + 命名实体展开 + 同款空白归一 |
| 超长段 | 连播**切块** ≤2000（后 1/3 窗口从尾向头找 `。！？；…` / `.!?`+空格，找不到硬切） | `split_long_text` 句界正则切块（窗口与断点算法不同） |

提取器必须以**朗读口径 + 连播切块口径**为准（按单段截断口径预热，>2000 的段在听书模式仍要现合成）。方案：把 R142 脚本（已对 book 145 实测「同一文本两次调用 4.7s 合成 → 0.028s 命中」验证缓存键一致）的提取逻辑移植固化进 `extractor.py`，并建**口径契约测试双锁**：

1. 静态锁：测试读 `epub.js` 源码断言 `PARAGRAPH_SELECTOR` / `BOOK_TTS_MAX` / `BLOCK_CHILD_SELECTOR` 常量值与 extractor 对应常量一致（漂移即红）；
2. 快照锁：book 145（1393 段，R142 全量验证过）段落序列快照入库，extractor 输出逐段比对。

## 4. 计费设计（D2 + 二轮拍板落地）

**统一原则**：
- **调用者（交互，即时使用）= 内容消费：按次计费，TTS 收听「听=消费」命中也扣**；
- **发起者（批量/任务，垫付成本）= 算力计量：按字符 / token，命中免费（幂等重跑不重复扣）**；
- **平台调用（internalUri 白名单 / 无用户上下文）：不计费**（现状语义保留）。

### 4.1 TTS 朗读

| 场景 | 计费 | 实现 |
| --- | --- | --- |
| 发起者：整本预生成 daemon（`source=book-tts-batch`，发起者身份） | **miss 合成时** floor(chars / 1000) 积分（Matilda 221,296 字符 ≈ 221 积分）；**命中 0**（重跑/retry 幂等） | ReadingTtsService 按 source 分流到 `aiGateway.speak`（字符计费现成，userId=UserContext=发起者）；台账 modality=tts |
| 调用者：阅读器单段朗读 / 连播逐段（无 source，用户身份） | **每次请求 1 段 = 1 积分，命中也扣**（听=消费；计费点在缓存查询之前；重复听同一段每次都扣） | ReadingTtsService（或 controller）入口按次扣 `consumeAmount(userId, 1)` + usageLedger 记账；欠费（precheckSufficient 拒绝）直接报错不出音频 |
| 平台调用（无用户上下文） | 不计费 | UserContext 为空现状路径 |

### 4.2 段落翻译、单词详情改按次（网关单点）

现状：两者经 AiGateway 文本链按 token 计量扣费（原 1 千 token 折 1 积分，`consumeForLlmTask`）。改为 **purpose 级 per-call 白名单**（`CreditBillingProperties` 扩展，形如 `credit.billing.per-call.{purpose}=1`，Nacos 热调）：

- 白名单 purpose：`reading-translate`（段落翻译，miss 段每段 1 积分）、`vocabulary-word-detail`（单词详情，每次调用 1 积分）；
- 仅交互路径（`call/callSync`，userId=UserContext=调用者）切换按次；任务路径（`callForTask/callWithUsage`，如整本翻译批次执行）**维持按 token 计量（折 10 积分/千 token）**——发起者口径；
- **注（不对称声明）**：TTS 收听「命中也扣」，而翻译/详情**命中缓存段不调网关、维持免费**——「听=消费」语境是收听侧；翻译命中扣费需把计费点移到查询端点 find-translations（改动面大），用户未要求，维持现状；如需对齐后续一行迁移。
- 其他 purpose（划词、批注、口语、写作等）不配置即维持按 token 计量，后续按需一行配置开。

### 4.3 积分体系×10（二轮拍板）

| 项 | 原值 | 新值 | 落点 |
| --- | --- | --- | --- |
| 注册赠送 | 1000（`credit.new-user-grant`） | **10000** | @Value 默认值 + Nacos |
| 充值套餐（`CreditRechargePackage` 代码常量，价格不变） | 99 元=20000 / 10 元=1000 / 测试 0.01 元=10 | **99 元=200000 / 10 元=10000 / 测试 0.01 元=100** | 枚举常量 ×10（R56 先例第二次）；⚠ 标题/描述字段含积分数文案同步改 |
| 文本 token 换算 | 1 千 token 折 1 积分（`TOKENS_PER_CREDIT=1000` 内建常量） | **1 千 token 折 10 积分** | 参数化进 `CreditBillingProperties`（Nacos 可调），默认 10 |
| 内容按次（TTS 段 / 翻译段 / 详情次） | — | **1 积分（不变）** | per-call 白名单 |
| 发起者 TTS 字符 | — | **1000 字符=1 积分（不变）** | `credit.billing.tts.chars-per-credit` |

**计价结构（算术验证）**：充值×10 后 10 元 = 10000 积分 → 1 积分 ≈ 0.001 元；听一本《Matilda》（1393 段）= 1393 积分 ≈ **1.4 元**（用户口径「听一本书只要 1 块钱」✓）。家人积分由 admin 经既有 `/credit/admin/adjust` 赠送（零开发）；外部用户走既有支付宝充值链路（`credit-recharge`，仅需档位×10）。

### 4.4 数值同源联动（R56 先例警示，强制项）

R56 曾做同型×10 并漏改 L1 被点名。本轮×10 交付必须同步：L1 用户文档（积分/充值相关页）、L2 credit hld 换算表、`CreditRechargePackage` 标题/描述文案、magicbook 充值页展示（若有写死积分数）。**文档与代码同轮交付，禁止只改代码。**

## 5. 整本选角设计（拍板新增 1）

**现状底座**：`BookVoiceService.resolve(bookName, chapter, sampleText)` 已实现按书选角——LLM（callSync，thinking 关闭）从 `MimoVoices.CATALOG` 选 voice + style（role 风格指令 ≤200 字符），落 `tts_book_voice` 表（bookName 唯一），同书并发合流只选一次，失败回落静态默认（Chloe + 平静叙述）。**局限（代码注释明示）**：输入只有书名 + 当前段文本（≤1500 字符）——「moon-well 拿不到书的简介/语种/体裁（book 表没有这些列）」，而**这些信息恰好在 magicbook 的 metadata.db**。

**设计**（补齐 gap，不另起炉灶）：

1. **magicbook start 时**：从 Calibre 元数据取 书名 / 作者 / comments（简介，清洗 HTML 后截断）/ 语言 / 样本文本（extractor 前 2~3 段拼接 ≤1500 字符），调 moon-well 新端点 `POST /tts/book-voice/select`：
   ```json
   {"bookName": "...", "author": "...", "summary": "...", "language": "eng",
    "sampleText": "前几段正文…", "force": false}
   ```
   force=false 且 `tts_book_voice` 已有该书 → 直接返回现有选角（复用）；force=true → 重选覆盖（upsert）。
2. **moon-well 侧**：`BookVoiceService` 增加带元信息的选角入口——`PromptDefinitions.TTS_BOOK_VOICE` 模板增加 `bookAuthor` / `bookSummary` / `language` 变量（缺失时渲染为空串，兼容阅读器旧路径），选角结果 upsert 落库（唯一约束冲突取先写者，沿用 persist 语义）。选角 LLM 调用走 gateway.callSync，计费随调用身份（发起者令牌 → 挂发起者；走平台则不计费）。
3. **daemon 逐段合成**时 `ReadingTtsService` → `BookVoiceService.resolve(bookName, ...)` 直接命中库中选角，**全书同一 voice + style**；并发合流闸门兜底（预生成与用户即时朗读同书并发安全，既有测试覆盖）。
4. **阅读器即时朗读路径不动**：未预生成的新书首段朗读仍按旧输入（书名+首段）懒选角——两路径共享 `tts_book_voice`，先到先得。
5. 选角失败不阻断批次：job 表 voice/style 留空，daemon 用 moon-well 内部默认选角继续合成（选角是增强而非依赖，既有原则）。

## 6. find-audio 移除的注意点（拍板 D4 连带）

| 注意点 | 处置 |
| --- | --- |
| start 无法精确报「已缓存 N 段 / 实际待合成」 | 弹窗改报**预估上限**（全 miss 口径字符折算）+ 文案「已缓存段落自动跳过、不重复计费，实际以积分流水为准」；book 145 场景显示上限 221 积分，实际 daemon 全命中 0 消耗 |
| 命中段也走完整 `/tts/speak` 响应（音频字节全量回传） | 内网可接受（R142 实测命中 0.028s/段）；一本书几百 MB 串行慢传，不占合成锁 |
| 批次表不区分 cached/synthesized | 计数简化为 done/failed；「实际省了多少」由发起者积分流水（实际扣减 vs 上限）反映，不在批次内重复记账 |
| 懒回收能力失去（翻译有 lookup 单向回收） | 无影响：daemon 重跑/retry 走缓存幂等天然「回收」；status 无需外部刷新 |
| 调用者收听扣费与 daemon 批量扣费并行 | 收听扣费挂调用者、批量扣费挂发起者且命中免费——同一本书两条计费线互不干扰（§4.1 表格） |

## 7. 关键时序

```
start    admin → magicbook 建批次 → 选角（/tts/book-voice/select：书元信息 → AI 定
         voice+style，落 tts_book_voice）→ 返回 {total, chars, estCredits 上限, voice}
daemon   逐 PENDING 段 → POST /tts/speak {text, bookName, chapter, source=book-tts-batch}
         → moon-well: 查 ES 缓存 → 命中=毫秒级返回、发起者 0 扣（幂等）
                              → miss → floor(chars/1000) 扣发起者 → TtsProviderChain
                                合成（MiMo→local→dashscope）→ 传 MinIO → 写 ES → 回字节
         → magicbook 置 DONE；0.8s 间隔下一段
播放     用户连播/单段 → /ajax/reading-tts → 入口先扣调用者 1 积分（听=消费，命中也扣）
         → moon-well 缓存命中 → 毫秒级返回；欠费拒绝
即时朗读 未预生成书 → 同上（入口扣 1）→ miss 合成（不走发起者通道）
中断恢复 容器重启丢线程 → retry / start 幂等复用（僵尸自愈关旧批 → 新批全量重跑，
         命中段发起者 0 扣，仅未完成段真合成）
```

## 8. 异常与边界

| 场景 | 处置 |
| --- | --- |
| 长文本段（>1000 字符） | MiMo 30s 超时 → 回落 local（180s）；daemon 客户端 ≥200s |
| 选角 LLM 失败 / 输出怪音色 | 回落静态默认（Chloe + 平静叙述），不阻断批次（既有语义） |
| 调用者积分不足 | 朗读请求直接拒绝（不出音频，提示充值/联系管理员）；家人由 admin adjust 送分 |
| 发起者积分中途耗尽 | 后续段 FAILED（error_message 可辨）；充值后 retry 补跑（命中段 0 重复扣） |
| moon-well 重启 / 网络抖动 | 段请求失败重试 1 次 → FAILED；批次不丢（SQLite），retry 恢复 |
| 回落链全不可用 | 段 FAILED 透传错误信息；链路恢复后 retry |
| 同书重复发起 | 同指纹活动批次静默复用；force=true 强制新批（命中段发起者仍 0 扣） |
| 重复段落 | unique(job_id, text_hash) 去重（连播命中同一缓存） |
| EPUB 解析失败 | 宽松解析（R101 XMLParser recover 经验）；0 段直接 400，不建空批次 |
| 预热与用户即时朗读同书并发 | BookVoiceService 合流闸门（既有，含测试） |

## 9. 已确认决策与边界声明

- ~~假设 1~~（已拍板）：**「听=消费」——调用者每次请求一段扣 1 积分，命中也扣**；发起者批量侧命中免费（幂等）。
- **不对称声明**：翻译/详情命中维持免费（§4.2 注），与 TTS 收听不同——语境差异（收听=消费 vs 查询展示），如需对齐另行拍板。
- 边界声明：划词翻译（单词级）、批注、口语、写作、听力等能力计费**本期不动**；purpose 白名单机制支持后续一行配置扩展。

## 10. 测试与验收

**magicbook 单测**：批次服务（幂等复用 / 僵尸自愈 / 提取去重 / retry / cancel / 选角失败不阻断）；extractor 口径契约测试双锁（§3.3）；路由权限（admin 门禁）+ 请求校验；预估上限计算。

**moon-well 单测**：`/tts/speak` source 分流计费（批量=miss 按字符挂发起者+命中 0 / 阅读器=每次请求扣 1 含命中 / 平台调用不计费 / 欠费拒绝）；`book-voice/select`（元信息入参 / force 重选 / upsert 冲突取先写者 / 失败回落）；purpose per-call 白名单（白名单内按次、任务路径按 token 折 10、白名单外不变）；`TOKENS_PER_CREDIT` 参数化换算；注册赠送 10000 / 充值档位×10。

**AC（真机）**：① book 145（R142 已预热）→ start 后 daemon 全量命中：**发起者 0 积分消耗**（流水核对）、分钟级完成、完成后连播零等待；② admin 连播听 book 145 全本：**调用者侧逐段扣 1（命中也扣）**，全本 ≈1393 积分（流水核对）；③ 未预热书 → start（选角返回 voice/style）→ daemon 合成按字符扣 → 完成后连播零等待（含 >2000 长段按连播切块口径命中）；④ 未预生成书即时朗读：每次请求扣 1（miss 与命中同价，流水 purpose 可查）；⑤ 段落翻译 miss 段 1 积分 / 单词详情 1 次 1 积分；⑥ 整本翻译批次计费：按 token 计量、1 千 token 折 **10** 积分（×10 回归）；⑦ 注册新用户送 **10000**；充值 10 元档到账 **10000**（档位×10 回归，前端文案同步）；⑧ admin adjust 加积分（家人场景）→ 余额增加、流水类型正确；⑨ 中途 cancel 即停；⑩ 人为制造 FAILED → retry 补跑成功且已完成段发起者 0 重复扣费。

**上线后**：R142 脚本退役（fnOS `tts-warm/` 留档不删）；三级文档联动（§4.4 强制项 + magicbook L1 `docs/readme/reading.md`、moon-well L2 tts/reading/credit hld 补计费契约与新端点）。

## 11. 开发拆分建议（进 worktree 后）

1. moon-well P1：`book-voice/select` 端点 + prompt 变量扩展（独立可测）；
2. moon-well P2：计费分层与积分×10（source 分流 + per-call 白名单 + TOKENS_PER_CREDIT 参数化 + 注册/充值档位 + 文案联动）；
3. magicbook P3：extractor + 批次服务 + daemon + 路由 + UI；
4. 两仓联调 + AC。
