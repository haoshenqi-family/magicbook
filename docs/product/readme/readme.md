# magicbook 使用手册（L1）

magicbook 是一个电子书库与英语阅读学习站点：以 Calibre 书库为基础，提供网页阅读器与围绕阅读的 AI 能力（整页/整本翻译、词汇量测试、每日学习、AI 伴读），账号经 Authentik 统一登录，与 moon-well 同一账号体系。装了姊妹扩展 [MagicLens 词镜](https://github.com/haoshenqi-family/magiclens) 时，划词查词、单词详解与生词高亮自动交给扩展（两者共用同一账号与生词本数据）；没装则阅读器自带同样的能力，不装扩展也能查词。

> 本目录是 **L1 用户文档**：只讲「这个系统能做什么」，不涉及实现。设计文档入口见文末分级表。
> （2026-10-08 R129 建立 L1/L2 骨架；2026-10-16 R188 迁入 v2 二分体系——product 静态 / project 动态，家族权威约定见家族仓 [`ops/docs-architecture.md`](../../../../ops/docs-architecture.md)。）

## 模块一览

| 模块 | 能做什么 | 用户手册 |
| --- | --- | --- |
| library | 书库：书架浏览/搜索、上传下载、元数据管理、OPDS/Kobo 同步、整本翻译、Halo 文章接入 | [library](library.md) |
| reading | 阅读器：EPUB/PDF/TXT 阅读、段落/整页/整本翻译、朗读、AI 批注、新概念课级音频、5 个内置主题跨设备同步（划词查词由 MagicLens 扩展承担） | [reading](reading.md) |
| vocabulary | 词汇学习：生词自动判定、认识/生词标记、生词本、词汇量测试与难度推荐（标记与高亮的入口在 MagicLens） | [vocabulary](vocabulary.md) |
| learning | 每日学习中枢：功能 banner 循环卡片进八个功能页——复习队列（辨析/回忆/拼写三梯度、四档评分）、听写、AI 口语陪练、复述训练 4-3-2、计时重读、写作工坊、单词编故事、选书难度匹配；另有今日计划/复习摘要/本周四股 | [learning](learning.md) |
| companion | AI 伴读：围绕当前书对话提问、工具调用、跨书记忆；伙伴系统（AI 阅读按钮的外观） | [companion](companion.md) |
| credit | 积分与订阅：积分余额/流水/充值（支付宝扫码）、可转赠积分卡、订阅状态、成就徽章 | [credit](credit.md) |
| admin | 管理：LLM 任务手动执行面板、用户与站点管理、OIDC 登录 | [admin](admin.md) |

## 快速开始（使用者视角）

1. 浏览器打开站点，通过 Authentik 完成统一登录（首次使用自动建立同名账号，moon-well 侧同步建号）。
2. 书架选书进入阅读器；鼠标移到段落上点「译」看该段译文，工具栏「译」翻整页、「整本译」翻全书。划词查词、单词详解与生词高亮：装了 MagicLens 扩展就由它接管，没装就用阅读器自带的同一套（自动切换，不会两个气泡并存）。
3. 词汇能力（词汇量测试、难度档位）可从首页书墙上方入口两步到达，也可在个人页 `/me` 调整；AI 伴读在阅读页右侧抽屉。
4. 个人页 `/me` 是偏好页：语言、阅读难度、阅读主题、伙伴。5 个内置阅读主题跟随账号跨设备生效，自定义颜色只留在本机。「导出我的学习数据」也在这里：把词汇与练习记录打包成加密 ZIP（内含可导入 Anki 的单词卡与回顾报告），文件保留 7 天。
5. 首次登录后，主站会自动邀请一次 2 分钟引导；关闭或完成后不再自动出现（同一账号跨设备一致）。需要重看时用设置下拉「使用引导」；阅读器里也可点右下角「使用引导」。匿名访问不弹引导。
6. 积分在个人页：AI 功能按 token 消耗积分，余额不足会提示，可支付宝扫码充值；也可以购买文本卡密送人，或兑换别人转赠的有效卡密。

## 文档分级（本仓库的文档体系 · v2）

文档按 **静态（product）/ 动态（project）** 二分：`product/` 描述「产品现在长什么样」，`project/` 记录「这次 / 最近改了什么」。

| 级别 | 位置 | 读者 | 内容 |
| --- | --- | --- | --- |
| **L1 用户文档** | `docs/product/readme/` | 使用者 | 系统与各模块功能介绍，不涉及实现 |
| **L2 接口说明** | `docs/product/<module>/interface.md` | 调用者 / 集成者 | 功能定义 + 功能说明 + 调用方法（代理端点映射）；**7 个模块已建 3 份**，逐模块状态见下表 |
| **L3 实现说明** | `docs/product/<module>/features/<FEATURE>.md` | 修改者 | 实现方式 + 边界条件（仅改本功能时需要读） |

- **HLD / LLD 已从 L2 / L3 拆出**：L2 / L3 只承载「功能 / 接口是什么」（静态）；「这一次怎么实现」= **LLD**，随迭代沉在 `docs/project/iterations/<ITER>/<工作项>/lld.md`（动态）。
- **历史设计冻结归档**：老 `docs/feat/`（18 个）整体冻结在 `docs/project/_legacy/feat/`，不回溯迭代归属、不逐功能拆分；原「18 个 feat 反向索引」纪律改由该归档目录自身承接，新工作从 `product/<module>/features/` 与 `project/iterations/` 起。
- **需求台账在 `docs/project/requests/`**（`requests.md` / `response.md` + 归档）。
- 后端契约的**唯一权威**是 moon-well 仓库的对应 L2（moon-well `docs/product/<module>/interface.md`）。
- 家族级权威约定（物理归位、迁移映射）见 [`ops/docs-architecture.md`](../../../../ops/docs-architecture.md)。

### L2 覆盖现状（逐模块实测，2026-10-16 R186，路径按 R188 v2 更新）

| 模块 | L2 | 接口契约现在在哪 |
| --- | --- | --- |
| reading | ✅ 已建 | [reading/interface.md](../reading/interface.md) |
| vocabulary | ✅ 已建 | [vocabulary/interface.md](../vocabulary/interface.md) |
| library | ⬜ 待升 L2 | L3（历史归档）：[whole-book-translation](../../project/_legacy/feat/whole-book-translation/design/whole-book-translation-design.md)（端点已在 reading L2 §1 挂号）、[halo-book-connector](../../project/_legacy/feat/halo-book-connector/design/lld.md) |
| learning | ⬜ 待升 L2 | L3（历史归档）：[learning-hub](../../project/_legacy/feat/learning-hub/design/us1-hub-banner-lld.md) |
| companion | ⬜ 待升 L2 | L3（历史归档）：[ai-agent](../../project/_legacy/feat/ai-agent/design/magicbook-side-design.md)、[ai-reading-companion](../../project/_legacy/feat/ai-reading-companion/design/ai-reading-companion-implementation-plan.md) |
| credit | ✅ 已建 | [credit/interface.md](../credit/interface.md) |
| admin | ⬜ 待升 L2 | L3（历史归档）：[llm-task-run/admin-monitor](../../project/_legacy/feat/llm-task-run/design/admin-monitor.md) |

口径（与 AGENTS.md 文档规范节同源）：**未建 L2 的模块，其接口契约以标着「待升 L2」的那份实现说明为准**，新模块的 L2 随功能演进补齐、不要求一次性铺满；上表逐模块核对过，两边不符时以本表为准并回填标注。

## 开发者入口（非用户能力）

- 架构评审任务拆分（2026-10）：重构项 B1–B8 与文档修正 DF1–DF8 的任务清单与波次，见 [arch-review-2026-10/design/overview.md](../../project/_legacy/feat/arch-review-2026-10/design/overview.md)（历史归档）。
