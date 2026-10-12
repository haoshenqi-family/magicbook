# 整本朗读（TTS 预生成）设计

状态：设计（待用户确认决策点 §7 后进入开发）
需求：2026-10-12「llm 已经重构，整本翻译功能有了，需要一个类似的整本使用 TTS 生成朗读的功能，先检查是否有这个功能，如果没有，先做设计」（magicbook R163 / moon-well R165 同源）

## 0. 检查结论：功能不存在，需新建

对四条既有链路逐一核实（代码级，非记忆）：

| 既有能力 | 现状 | 与本需求的差距 |
| --- | --- | --- |
| moon-well `/tts/speak`（ReadingTtsController → ReadingTtsService） | 段落级**同步**合成；缓存键 = SHA-256(trim(段落原文))，bookName/chapter 非空即永久缓存（ES 引用 + MinIO `reading-tts/`）；R162 P3 起有用户上下文按字符计费 | 无批次、无进度、无后台批量；一次一段 |
| magicbook R157 整本连播（epub.js `bookPlayer`） | 前端播放队列，逐段在线请求 `/ajax/reading-tts`，**边播边合成**；其设计文档明确「零等待可先跑 fnOS tts-warm 脚本」 | 首听每段等几秒~几十秒（长段实测最长 78.6s）；预生成靠手工 |
| magicbook R142 整本预热 | fnOS 宿主机 `tts_warm.py` 手工脚本（不入 Git），逐段调 `/tts/speak` 写永久缓存；book 145《Matilda》1393 段全量跑通 | **运营态方案，零代码**；无产品入口、无进度 UI、断点靠 jsonl 记账 |
| moon-well llm_task TTS 任务型 | R162 P4 收口后 = **外部 worker 领用契约**（进程内执行器对非 TEXT 显式快速失败），无 worker 部署；产物回写协议属 R162 P4 遗留④「待真实消费者出现再补」 | 队列路径不通，走它需先定协议+部署 worker |

**结论**：用户要的「类似整本翻译」的整本 TTS 预生成（一键发起 → 后台批量合成 → 进度可查 → 完成后零等待听书）**不存在**。R142 脚本验证过的链路（逐段调 `/tts/speak` 写永久缓存）正是本设计要产品化的对象。

## 1. 目标与非目标

**目标**：书详情页一键为整本书预生成朗读音频；后台逐段合成进 moon-well 永久缓存；进度/失败/重试可见；幂等（已缓存段跳过且不重复计费）；完成后 R157 连播与单段朗读全程毫秒级命中。

**非目标**：
- PDF（canvas 渲染无段落）、TXT（阅读器结构简单）——与整本翻译、连播口径一致，仅 EPUB/KEPUB；
- 不做「全部英文书批量」（R77 翻译有 translate-all；本地 Qwen3-TTS 全局合成锁下串行执行，一本书 1.5~2.5h，批量无意义）；
- 不改 R157 连播与前端朗读（自动受益：缓存命中即零等待）；
- 不动 R162 P4 遗留④（TTS 任务型回写协议）——本设计不消费它，见 §2 方案 B 触发条件。

## 2. 架构选型（决策点 D1）

| | 方案 A（推荐）：magicbook 批次 + daemon 逐段直调 `/tts/speak` | 方案 B：走 moon-well llm_task TTS 任务型 |
| --- | --- | --- |
| 链路 | 镜像整本翻译的批次壳，执行不走 llm_task 队列：daemon 串行逐段 POST `/tts/speak` | 镜像整本翻译全链：逐段 publish，moon-well 补 TTS worker + 产物回写协议 |
| 依据 | R142 已全量验证（1393 段）；缓存命中天然幂等（命中不合成、不计费、毫秒级）；moon-well 近零改动 | R162 P4 遗留④本就要补 |
| 代价 | magicbook 新模块（翻译批次基建可复刻）；moon-well 仅加一个只读探测端点（§3.2） | 需定义 audioBase64/缓存编排回写协议 + 部署/内置 worker，工程量数倍；而 TTS 预热的执行特征（串行、长尾单段、断点即缓存）用不上队列编排 |
| 判定 | **推荐** | 列为未来：出现「无 magicbook HTTP 直调语境的消费者」或 ASR 批量同型需求时再补协议（维持 P4 遗留④原判） |

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

**数据模型**（镜像 TranslationJob/Item，两处实质差异加粗）：

`reading_tts_job`：id / user_id / book_id / book_format / book_name / book_fingerprint / status（RUNNING / COMPLETED / PARTIAL_FAILED / CANCELLED）/ total_count / cached_count（探测已命中数）/ synthesized_count（**本批次新合成数**，替代翻译的 published_count）/ failed_count / created_at / updated_at。

`reading_tts_job_item`：id / job_id / paragraph_index / chapter / text / text_hash（SHA-256，unique(job_id, text_hash)）/ status（PENDING / DONE / FAILED）/ error_message / attempt_count / created_at / updated_at。**无 task_id 列**（`/tts/speak` 同步无任务号）、**无产物列**（音频在 moon-well 缓存，不在本仓落任何音频）。

**服务流程**（复刻翻译的 start 骨架）：

1. `start(book_id, book_format, force)`：书文件校验（EPUB/KEPUB）→ 指纹（path:size:mtime，翻译同款）→ 幂等复用（同 user+book+fingerprint 的活动批次静默复用）→ 僵尸自愈（updated_at 停滞 >30min 置 PARTIAL_FAILED 关闭）→ **朗读口径提取**（§3.3）→ 按 text_hash 去重建 job+items → `find-audio` 批量探测（§3.2）命中段直接置 DONE（计 cached_count，不消耗）→ spawn daemon 线程 → 立即返回 progress（HTTP 只承诺受理，整本发布在请求线程必被网关超时杀死——翻译 HP2 3160 段实测教训）。
2. **daemon 合成线程**：串行逐段（仅 PENDING 段）POST moon-well `/tts/speak`，payload `{text, bookName: 书名, chapter: 章名}`（书籍上下文非空 = 永久缓存，moon-well 既有分级语义）；HTTP 客户端超时 **≥200s**（服务端 `tts.local.timeout-ms` 生产现值 180s + 余量；R142 实测最长段 78.6s）；段间限速 **0.8s**（R142 补跑参数）；失败原地重试 1 次，再败置 FAILED 留 error_message；线程内自建 DB session（scoped_session 不能跨线程，翻译同款）；**批次表即断点台账**（R142 done.jsonl 的产品化），容器重启丢线程由 §5 恢复路径兜底。
3. `progress(job_id, lookup)`：计数聚合 + 懒回收——经 `find-audio` 单向刷新「外部已完成」段（前次批次残留、用户手动听过、脚本预热过），不触发合成。
4. `retry(job_id)`：FAILED 段重跑；幂等（命中缓存免费）。
5. `cancel(job_id)`：置 CANCELLED；daemon 每段开跑前查批次状态，见 CANCELLED 即退出。

**路由**（镜像翻译四件套，全部 `admin_required`）：

- `POST /ajax/reading-tts-book` `{book_id, book_format, force}`
- `POST /ajax/reading-tts-book/status` `{job_id}`
- `POST /ajax/reading-tts-book/retry` `{job_id}`
- `POST /ajax/reading-tts-book/cancel` `{job_id}`

身份传递：与翻译的 publish 闭包同理——daemon 线程无 Flask 上下文，令牌在请求线程定格为快照传入（R51/R145 教训：线程内解析身份必 RuntimeError 全批 FAILED）。

**UI**：`detail.html`「整本翻译」按钮旁加「整本朗读」按钮（admin 可见）；确认弹窗展示 `{总段落数, 已缓存, 待合成, 预计积分}`（积分 = ceil(待合成字符数/1000)，口径见 §3.4）；进度轮询复用翻译的进度展示样式，追加 ETA（按最近 20 段耗时滑动平均）。

**阅读器零改动**：R157 连播按段落文本请求 `/ajax/reading-tts`，预热后全量命中。

### 3.2 moon-well 侧（唯一改动：一个只读端点）

新增 `POST /reading/paragraph-cache/find-audio`（镜像既有 `find-translations`，挂 ReadingParagraphCacheController）：

- 入参 `{paragraphs: [文本...]}`（与 ReadingParagraphCacheLookupRequest 同构）；
- 出参 `{result: {段落原文: 来源模型标签}}`——只回传**命中标记**（音频与译文共文档，doc id = SHA-256(trim(段落原文))，判 `audioObject` 非空即命中），**不回传音频字节**；
- 用途：start 时统计已缓存段（省得全量 speak 靠命中幂等——慢且每次都传音频字节，一本书数百 MB 内网流量）；status 懒回收。
- 批量上限、OpenApiConfig 分组与 find-translations 同口径（并入阅读朗读 TTS 组）。

`/tts/speak` 完全不动：计费（UserContext 身份）、回落链（LocalQwen → DashScope → MiMo）、缓存写回全部原样。

### 3.3 段落提取口径（核心风险点）

**Why 不能复用整本翻译的 `reading_translation/parser.py`**——两套口径存在系统差异，预生成用错口径 = 缓存键与前端请求键对不上 = **白合成**（烧积分 + 算力，整本数百次无效合成）：

| 维度 | 前端朗读口径（epub.js，缓存键的消费者） | 翻译提取器（parser.py） |
| --- | --- | --- |
| 元素集 | `PARAGRAPH_SELECTOR = 'p, li, blockquote, h1..h6, div'`；DIV 含块级子元素跳过（文字归子元素）；嵌套按 querySelectorAll 语义**双收** | `BLOCK_TAGS = {p, li, blockquote, pre}`；有块级祖先的节点**跳过**（只收最外层） |
| 文本 | `textContent` → `\s+`→`' '` → trim | `itertext()` 拼接 + 命名实体展开 + 同款空白归一 |
| 超长段 | 连播**切块** ≤2000（后 1/3 窗口从尾向头找 `。！？；…` / `.!?`+空格，找不到硬切）；单段朗读是**截断** | `split_long_text` 句界正则切块（窗口与断点算法不同） |

翻译场景口径差异只造成部分段 miss → 现场翻译（代价小）；TTS 预热场景 miss = 纯浪费（代价大）。**提取器必须以朗读口径为准**，且必须按**连播切块口径**（若按单段截断口径，>2000 的段在听书模式仍要现合成）。

方案：把 R142 脚本（fnOS `/app/magicbook/tts-warm/tts_warm.py`，已对 book 145 实测「同一文本两次调用 4.7s 合成 → 0.028s 命中」验证缓存键一致）的提取逻辑移植固化进 `cps/reading_tts/extractor.py`，并建立**口径契约测试**双锁：

1. 静态锁：测试读 `epub.js` 源码断言 `PARAGRAPH_SELECTOR` / `BOOK_TTS_MAX` / `BLOCK_CHILD_SELECTOR` 常量值与 extractor 中的对应常量一致（漂移即红）；
2. 快照锁：对固定样例书（book 145，1393 段，R142 全量验证过）产出段落序列快照入库，extractor 输出与快照逐段比对。

### 3.4 计费与额度（决策点 D2）

现状：R162 P3 起 `/tts/speak` 经 DefaultAiGateway 计费——有 UserContext 用户即按 `floor(chars / credit.billing.tts.chars-per-credit)` 扣积分（默认 1000 字符 = 1 积分，Nacos 可调可关）；无用户上下文 = 平台调用不计费。

方案：daemon 以**发起者（admin）令牌**调用 → 逐段扣积分，与整本翻译挂发起者（consumeForLlmTask）口径一致。start 确认弹窗展示预估（book 145 口径：221,296 字符 ≈ **221 积分**）。积分不足段：`precheckSufficient` 拒绝 → FAILED（error_message 可辨）；中途余额耗尽 → 后续段 FAILED，充值后 retry 补跑（幂等，已完成段免费）。

备选：Nacos 关 `credit.billing.tts.enabled`（全局免 TTS 计费，仍记台账）——不为此功能单独加豁免通道（避免新概念）；不推荐默认走平台身份（绕过计费且丢失台账归属）。

### 3.5 限速与并发保护（全部复用既有件）

- 本地 Qwen3-TTS 全局合成锁 = 服务端串行，daemon 单线程串行 + 0.8s 段间隔即天然合规；
- BookVoiceService 同书并发合流闸门（R142 后加固，含 BookVoiceServiceTest 用例）：预热期间用户在阅读器点同一本书朗读，安全；
- 多批次并发：每批次一线程，moon-well 合成锁全局排队，不做额外限流（个人站）；一期不加同时活动批次上限，进度页可见即可，压观察期数据再定。

## 4. 关键时序

```
start    admin → magicbook 建批次 → find-audio 批量探测 → 命中段置 DONE
         → 返回 {total, cached, toSynthesize, estCredits}（HTTP 即回）
daemon   逐 PENDING 段 → POST /tts/speak {text, bookName, chapter}
         → moon-well: 查 ES 缓存 → miss → 计费 → TtsProviderChain 合成（回落链）
           → 传 MinIO → 写 ES 引用 → 回音频字节 → magicbook 置 DONE
播放     用户连播 → /ajax/reading-tts → moon-well 缓存命中 → 毫秒级返回
中断恢复 容器重启丢线程 → status 懒回收（lookup 刷新）/ start 幂等复用
         （僵尸自愈关旧批 → 新批次 lookup 跳过已缓存段）
```

## 5. 异常与边界

| 场景 | 处理 |
| --- | --- |
| 长文本段（>1000 字符） | 服务端 `tts.local.timeout-ms` = 180s（生产现值），daemon 客户端 ≥200s；R142 实测最长 78.6s |
| moon-well 重启 / 网络抖动 | 段请求失败重试 1 次 → FAILED；批次不丢（SQLite），retry 恢复 |
| 回落链全不可用（DashScope 免费额度已失效为已知现状） | 段 FAILED 透传错误信息；链路恢复后 retry |
| 同书重复发起 | 同指纹活动批次静默复用；force=true 强制新批（新批仍 lookup 跳过已缓存段，不重复计费） |
| 重复段落 | unique(job_id, text_hash) 去重（翻译同款；连播命中同一缓存） |
| EPUB 解析失败（坏文件） | 沿用翻译的宽松解析经验（R101 XMLParser recover）；0 段直接 400 报错，不建空批次 |
| 预热与阅读器同时朗读 | BookVoiceService 合流闸门保护（既有） |

## 6. 测试与验收

**magicbook 单测**：批次服务（幂等复用 / 僵尸自愈 / 提取去重 / lookup 预标 DONE / retry / cancel）；extractor 口径契约测试双锁（§3.3）；路由权限（admin 门禁）+ 请求校验。

**moon-well 单测**：find-audio（命中 / 未命中 / 空列表 / 超长列表拒绝口径同 find-translations）。

**AC（真机）**：① book 145（已由 R142 预热）→ start 秒回 `{cached: 1393, toSynthesize: 0}`，零消耗；② 未预热书 → start → 进度推进 → 完成后连播全程零等待（含 >2000 长段按连播切块口径命中）；③ 中途 cancel 即停；④ 人为制造 FAILED（如临时断 moon-well）→ retry 补跑成功；⑤ 发起者积分流水与 system_ai_usage 台账可查（purpose=tts，chars 计量）。

**上线后**：R142 脚本退役（fnOS `tts-warm/` 目录留档不删）；L1 `docs/readme/reading.md` 补「整本朗读」入口说明，moon-well L2 `docs/reading/hld/`（或 tts hld）补 find-audio 契约（交付时三级联动）。

## 7. 决策点汇总（待拍板）

| # | 决策 | 推荐 | 备选 |
| --- | --- | --- | --- |
| D1 | 执行架构 | A：magicbook 批次 + daemon 直调 `/tts/speak`（R162 P4 遗留④维持不动） | B：补 llm_task TTS worker + 回写协议（工程量数倍，暂无必要） |
| D2 | 计费 | 挂发起者逐段扣积分 + start 弹窗预估展示 | 全局关 TTS 计费（Nacos 一键，影响所有 TTS 调用） |
| D3 | 一期范围 | 仅书详情页单本入口（admin） | 追加全部英文书批量（不建议，串行算力下无意义） |
| D4 | moon-well 改动 | 仅新增 find-audio 探测端点 | 零改动（start 无缓存统计，daemon 全量 speak 靠命中幂等；慢、费带宽，不推荐） |
