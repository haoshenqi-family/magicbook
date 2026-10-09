# magicbook 使用手册（L1）

magicbook 是一个电子书库与英语阅读学习站点：以 Calibre 书库为基础，提供网页阅读器与围绕阅读的 AI 能力（划词翻译、生词高亮、单词详解、词汇量测试、AI 伴读），账号经 Authentik 统一登录，与 moon-well 同一账号体系。

> 本目录是 **L1 用户文档**：只讲「这个系统能做什么」，不涉及实现。设计文档入口见文末分级表。
> （2026-10-08 R129 建立 L1/L2 骨架，统一方案见家族根 `../../docs/agents-doc-spec-plan-2026-10-07.md`。）

## 模块一览

| 模块 | 能做什么 | 用户手册 |
| --- | --- | --- |
| library | 书库：书架浏览/搜索、上传下载、元数据管理、OPDS/Kobo 同步、整本翻译、Halo 文章接入 | [library](/Users/haoshenqi/codelib/haoshenqi-family/magicbook/docs/readme/library.md) |
| reading | 阅读器：EPUB/PDF/TXT 阅读、划词翻译、生词高亮、单词详解、朗读、AI 批注、新概念课级音频 | [reading](/Users/haoshenqi/codelib/haoshenqi-family/magicbook/docs/readme/reading.md) |
| vocabulary | 词汇学习：生词自动判定、认识/生词标记、生词本、词汇量测试与难度推荐 | [vocabulary](/Users/haoshenqi/codelib/haoshenqi-family/magicbook/docs/readme/vocabulary.md) |
| learning | 每日学习：SRS 间隔重复复习（辨析/回忆/拼写三梯度题型）、四档评分、今日计划、学习统计、选书难度匹配 | [learning](/Users/haoshenqi/codelib/haoshenqi-family/magicbook/docs/readme/learning.md) |
| companion | AI 伴读：围绕当前书对话提问、工具调用、跨书记忆 | [companion](/Users/haoshenqi/codelib/haoshenqi-family/magicbook/docs/readme/companion.md) |
| credit | 积分与订阅：积分余额/流水/充值（支付宝扫码）、订阅状态、成就徽章 | [credit](/Users/haoshenqi/codelib/haoshenqi-family/magicbook/docs/readme/credit.md) |
| admin | 管理：LLM 任务手动执行面板、用户与站点管理、OIDC 登录 | [admin](/Users/haoshenqi/codelib/haoshenqi-family/magicbook/docs/readme/admin.md) |

## 快速开始（使用者视角）

1. 浏览器打开站点，通过 Authentik 完成统一登录（首次使用自动建立同名账号，moon-well 侧同步建号）。
2. 书架选书进入阅读器；划词即翻译，生词自动标波浪线，点击「详」看单词详解。
3. 词汇能力（词汇量测试、难度档位）在「阅读设置」里；AI 伴读在阅读页右侧抽屉。
4. 积分在个人页：AI 功能按 token 消耗积分，余额不足会提示，可支付宝扫码充值。

## 文档分级（本仓库的文档体系）

| 级别 | 位置 | 读者 | 内容 |
| --- | --- | --- | --- |
| **L1 用户文档** | `docs/readme/` | 使用者 | 系统与各模块功能介绍，不涉及实现 |
| **L2 设计概要（HLD）** | `docs/<module>/hld/` | 模块调用者/集成者 | 代理端点映射与接口约定（首批：reading、vocabulary，其余模块契约暂以 L3 为准） |
| **L3 详细设计（LLD）** | `docs/feat/` | 开发/维护者 | 具体设计、验收、测试（12 个 feat） |

模块对应的 L3 详细设计在 `docs/feat/`（如 `whole-book-translation`、`vocab-size-test`、`llm-task-run` 等）；后端契约的**唯一权威**是 moon-well 仓库的 L2（`moon-well/docs/<module>/hld/`）。
