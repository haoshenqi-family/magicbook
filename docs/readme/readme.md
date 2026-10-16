# magicbook 使用手册（L1）

magicbook 是一个电子书库与英语阅读学习站点：以 Calibre 书库为基础，提供网页阅读器与围绕阅读的 AI 能力（整页/整本翻译、词汇量测试、每日学习、AI 伴读），账号经 Authentik 统一登录，与 moon-well 同一账号体系。装了姊妹扩展 [MagicLens 词镜](https://github.com/haoshenqi-family/magiclens) 时，划词查词、单词详解与生词高亮自动交给扩展（两者共用同一账号与生词本数据）；没装则阅读器自带同样的能力，不装扩展也能查词。

> 本目录是 **L1 用户文档**：只讲「这个系统能做什么」，不涉及实现。设计文档入口见文末分级表。
> （2026-10-08 R129 建立 L1/L2 骨架，统一方案见家族根 `../../docs/agents-doc-spec-plan-2026-10-07.md`。）

## 模块一览

| 模块 | 能做什么 | 用户手册 |
| --- | --- | --- |
| library | 书库：书架浏览/搜索、上传下载、元数据管理、OPDS/Kobo 同步、整本翻译、Halo 文章接入 | [library](/Users/haoshenqi/codelib/haoshenqi-family/magicbook/docs/readme/library.md) |
| reading | 阅读器：EPUB/PDF/TXT 阅读、段落/整页/整本翻译、朗读、AI 批注、新概念课级音频（划词查词由 MagicLens 扩展承担） | [reading](/Users/haoshenqi/codelib/haoshenqi-family/magicbook/docs/readme/reading.md) |
| vocabulary | 词汇学习：生词自动判定、认识/生词标记、生词本、词汇量测试与难度推荐（标记与高亮的入口在 MagicLens） | [vocabulary](/Users/haoshenqi/codelib/haoshenqi-family/magicbook/docs/readme/vocabulary.md) |
| learning | 每日学习中枢：功能 banner 循环卡片进七个子页面——复习队列（辨析/回忆/拼写三梯度、四档评分）、听写、AI 口语陪练、复述训练 4-3-2、计时重读、写作工坊、选书难度匹配；另有今日计划/复习摘要/本周四股 | [learning](/Users/haoshenqi/codelib/haoshenqi-family/magicbook/docs/readme/learning.md) |
| companion | AI 伴读：围绕当前书对话提问、工具调用、跨书记忆 | [companion](/Users/haoshenqi/codelib/haoshenqi-family/magicbook/docs/readme/companion.md) |
| credit | 积分与订阅：积分余额/流水/充值（支付宝扫码）、订阅状态、成就徽章 | [credit](/Users/haoshenqi/codelib/haoshenqi-family/magicbook/docs/readme/credit.md) |
| admin | 管理：LLM 任务手动执行面板、用户与站点管理、OIDC 登录 | [admin](/Users/haoshenqi/codelib/haoshenqi-family/magicbook/docs/readme/admin.md) |

## 快速开始（使用者视角）

1. 浏览器打开站点，通过 Authentik 完成统一登录（首次使用自动建立同名账号，moon-well 侧同步建号）。
2. 书架选书进入阅读器；鼠标移到段落上点「译」看该段译文，工具栏「译」翻整页、「整本译」翻全书。划词查词、单词详解与生词高亮：装了 MagicLens 扩展就由它接管，没装就用阅读器自带的同一套（自动切换，不会两个气泡并存）。
3. 词汇能力（词汇量测试、难度档位）在「阅读设置」里；AI 伴读在阅读页右侧抽屉。
4. 积分在个人页：AI 功能按 token 消耗积分，余额不足会提示，可支付宝扫码充值。

## 文档分级（本仓库的文档体系）

| 级别 | 位置 | 读者 | 内容 |
| --- | --- | --- | --- |
| **L1 用户文档** | `docs/readme/` | 使用者 | 系统与各模块功能介绍，不涉及实现 |
| **L2 设计概要（HLD）** | `docs/<module>/hld/hld.md` | 模块调用者/集成者 | 代理端点映射与接口约定；**7 个模块已建 2 份**，逐模块状态见下表 |
| **L3 详细设计（LLD）** | `docs/feat/` | 开发/维护者 | 具体设计、验收、测试（18 个 feat） |

### L2 覆盖现状（逐模块实测，2026-10-16 R186）

| 模块 | L2 | 接口契约现在在哪 |
| --- | --- | --- |
| reading | ✅ 已建 | [docs/reading/hld/hld.md](../reading/hld/hld.md) |
| vocabulary | ✅ 已建 | [docs/vocabulary/hld/hld.md](../vocabulary/hld/hld.md) |
| library | ⬜ 待升 L2 | L3：[whole-book-translation](../feat/whole-book-translation/design/whole-book-translation-design.md)（端点已在 reading L2 §1 挂号）、[halo-book-connector](../feat/halo-book-connector/design/lld.md) |
| learning | ⬜ 待升 L2 | L3：[learning-hub](../feat/learning-hub/design/us1-hub-banner-lld.md) |
| companion | ⬜ 待升 L2 | L3：[ai-agent](../feat/ai-agent/design/magicbook-side-design.md)、[ai-reading-companion](../feat/ai-reading-companion/design/ai-reading-companion-implementation-plan.md) |
| credit | ⬜ 待升 L2 | L3：[subscription-page](../feat/subscription-page/design/lld.md) |
| admin | ⬜ 待升 L2 | L3：[llm-task-run/admin-monitor](../feat/llm-task-run/design/admin-monitor.md) |

口径（与 AGENTS.md 文档规范节同源）：**未建 L2 的模块，其接口契约以标着「待升 L2」的那份 L3 design 为准**，新模块的 L2 随功能演进补齐、不要求一次性铺满；上表与 L3 里的标注由 R186 逐模块核对过，两边不符时以本表为准并回填标注。

模块对应的 L3 详细设计在 `docs/feat/`，共 18 个（反向索引纪律：每个 L3 目录都要在此可见）：ai-agent、ai-reading-companion、arch-review-2026-10、halo-book-connector、language-i18n、learning-hub、llm-task-run、magicbook-fnos、nce-audio、onboarding-tour、sso-user-unification、subscription-page、ted-audio-companion、vocab-size-test、whole-book-listening、whole-book-translation、whole-book-tts、word-detail；后端契约的**唯一权威**是 moon-well 仓库的 L2（`moon-well/docs/<module>/hld/`）。

## 开发者入口（非用户能力）

- 架构评审任务拆分（2026-10）：重构项 B1–B8 与文档修正 DF1–DF8 的任务清单与波次，见 [docs/feat/arch-review-2026-10/design/overview.md](../feat/arch-review-2026-10/design/overview.md)。
