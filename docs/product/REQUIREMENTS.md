# magicbook AI 伴读 二次开发需求文档

> 本文档记录该项目的产品需求。每当有**新增需求**或**更正/澄清需求**时，都必须更新本文档，并在文末「变更记录」中追加一条说明。
>
> - 项目性质：calibre-web 的 fork，进行二次开发。
> - 项目目标：在 calibre-web 基础上增加「AI 帮助阅读」能力。
> - 在线站点（参考）：`https://hyh.haoshenqi.top/ai/admin`（~~报错~~ 已修复，见 §8 变更记录 2026-07-31。**该旧域已被取代**：magicbook 现用 `https://magicbook.haoyuhang.top`）

---

## 1. 项目背景

本项目是 [calibre-web](https://github.com/janeczku/calibre-web) 的一个 fork。希望在尽量不破坏原项目结构的前提下，为读者提供 AI 辅助阅读能力：在阅读书籍时可以与 AI 对话，AI 能记住读者的偏好，并支持通过 Authentik 登录。

## 2. 总体目标

1. 在原阅读页面中集成「AI 伴读」功能，读者可与 AI 围绕当前书籍内容进行对话。
2. 提供 AI 记忆系统，使 AI 跨书籍、跨会话地记住读者的偏好与上下文。
3. 接入 Authentik 作为登录方式。
4. AI 能力支持多 provider、多模型，可扩展；初期只需支持 DeepSeek（模型名见 §5）。
5. **最小侵入**：尽量新写代码，而不是修改 calibre-web 的既有代码。

## 3. 功能需求

### FR-1　AI 伴读页面

- 在原阅读页面上增加一个「AI 伴读」入口/页面，用户可在其中与 AI 就当前书籍内容进行对话。
- 每次提问时，需将以下信息一并发送给 AI：
  - 当前正在阅读书籍的 **metadata**（如书名、作者、标签、简介等）。
  - **当前页**的文本内容。
  - 用户的**问题**。
- 对话需围绕书籍内容展开（AI 应基于 metadata 与当前页作答）。
- 应覆盖 calibre-web 的主要阅读器（EPUB / PDF / TXT 等）。

### FR-2　AI 记忆系统

- AI 具备记忆能力，可记录用户的长期偏好/洞察。
- 记忆应可在跨书籍、跨会话的场景下被复用，注入到后续对话的上下文中。
- 需要提供记忆的管理能力（至少包括查看与清除）。

### FR-3　接入 Authentik 登录

- 将 Authentik 作为新的登录方式接入 calibre-web。
- 与 calibre-web 既有的用户体系打通（复用既有用户绑定/注册流程，而非另起一套）。

### FR-4　多 Provider / 多模型支持

- AI 能力需设计为支持**多 provider、多模型**，便于后续扩展。
- 初期只需支持 **DeepSeek**（具体模型见 §5）。
- Provider/模型的配置应可在管理后台维护（如 API Base、API Key、可用模型列表、启用/禁用等）。

## 4. 非功能需求

### NFR-1　最小侵入

- **尽量少地修改 calibre-web 既有代码**，尽量以**新写代码**的方式实现功能。
- 新增的 AI 相关代码应集中放在独立子包（如 `cps/ai/`）中，与原项目解耦。
- 对原项目的改动应限定在必要的「接入点」（如蓝图注册、阅读器模板引入伴读面板、后台导航入口等），并尽量控制在极少量行数。

### NFR-2　可配置与安全

- API Key 等敏感信息需加密存储，不以明文落库。
- AI 功能默认关闭，需管理员在后台显式启用。

## 5. 技术约束

- AI Provider：初期只支持 **DeepSeek**。
- 模型：用户指定为 **deepseek V4 flash**。
  > ⚠️ 待澄清：DeepSeek 目前公开的模型为 `deepseek-chat`（V3）与 `deepseek-reasoner`（R1），当前代码默认使用 `deepseek-chat`。「V4 flash」是否为最新模型名或别名，需用户确认后统一口径。

## 6. 当前实现状态（供参考）

> 本节描述仓库中已存在的实现情况，便于对照需求与现状。后续如实现发生变化，应同步更新本节。

- AI 代码集中位于 `cps/ai/` 子包（`routes.py` / `models.py` / `registry.py` / `deepseek.py` / `memory.py` / `authentik.py` / `crypto.py`）。
- 蓝图已在 `cps/main.py` 中注册，`/ai/admin` 路由存在。
- 伴读面板模板 `cps/templates/ai_chat_panel.html`，静态资源 `cps/static/js/ai_chat.js`、`ai_page_extract.js`、`cps/static/css/ai_chat.css`。
- 已注入到阅读器模板（`read.html` / `readpdf.html` / `readtxt.html`）。
- 后台配置页 `cps/templates/ai_admin.html`，支持 Provider/模型配置与 Authentik client_secret。
- AI 表自动创建：`cps/ai/__init__.py` 在导入时调用 `ensure_ai_tables()`（显式 `Base.metadata.create_all` AI 相关表）与 `seed_default_config()`（写入默认 `AiConfig` + deepseek `AiProvider`）。这是因为 calibre-web 的 `ub.init_db()` 在 `create_app()` 内执行 `create_all` 时，`cps.ai.models` 尚未导入注册到 `Base.metadata`，AI 表不会被自动创建。
- 已知问题：~~`https://hyh.haoshenqi.top/ai/admin` 报错~~ **已修复**（见 2026-07-31 变更记录；该旧域现已被 `magicbook.haoyuhang.top` 取代）。

## 7. 待办与待澄清

- [x] 排查 `/ai/admin` 在线报错原因。（根因：AI 表未创建 + 默认 config 未 seed；已于 `cps/ai/__init__.py` 修复）
- [ ] 确认「deepseek V4 flash」的准确模型标识，并统一配置默认模型。
- [ ] 明确记忆系统的提取频率/触发策略是否需要可配置（当前默认每 N 条消息提取一次）。

## 8. 变更记录

| 日期 | 变更内容 | 说明 |
| --- | --- | --- |
| 2026-07-31 | 初始版本 | 依据用户原始需求整理：AI 伴读页面、AI 记忆系统、Authentik 登录、多 provider/多模型（初期 DeepSeek）、最小侵入原则；并记录 `/ai/admin` 报错待排查、deepseek V4 flash 模型名待澄清。 |
| 2026-07-31 | 修复 `/ai/admin` 500 报错 | 根因：`cps.ai.models` 在 `create_app()` 的 `Base.metadata.create_all` 之后才被导入，导致 `ai_config`/`ai_provider` 等表从未创建，首次访问 `/ai/admin` 查询即抛 `OperationalError: no such table`。修复：在 `cps/ai/__init__.py` 导入时新增 `ensure_ai_tables()` 显式建表，并调用 `seed_default_config()` 写入默认配置。验证：模拟线上全新 DB 启动，`/ai/admin` 返回 200 且含 DeepSeek；测试套件 58 passed。 |
| 2026-10-25 | R225 注册跳转 / 阅读权限 / 封面占位 | 注册邀请改回 Authentik 2025.10.2 接受的顶层 `?itoken=...&next=...`；新账号固定具备在线阅读位但不自动获得下载/管理员；存量账号用 `scripts/reader_role_audit.py` 点名补阅读位；无封面统一使用品牌深墨绿占位图。 |
| 2026-10-25 | R226 阅读器验收缺陷 | 伙伴头像恢复透明无白底；阅读器导览入口由无文案「?」改为右下角「使用引导」；整页翻译改为请求期顶栏加载态、全部返回后一次渲染，避免逐段插入触发的连续重排。AI 面板 420px 覆盖式抽屉维持 R215 既有拍板。 |
| 2026-10-25 | R227 Buddy 语音能力 | 伴读面板复用口语陪练的录音+ASR 链路：全站可语音提问（转写填输入框、编辑后发送，录音不留存）；每条助手回复可手动朗读（Web Audio 播放、长回复分段、不带书籍上下文以免污染段落缓存）。CSP 未放宽。 |
| 2026-10-25 | moon-well R214 / magicbook R228 伴读 Agent Skills | 消费侧记录：伴读 Agent 可按需加载随服务发布的 MagicBook 全功能指南，用于页面导航、学习流程与能力边界说明；Skill 只读、不扩权。magicbook R214 仍为书籍详情，消费侧占 R228。 |
| 2026-10-26 | R232 伴读面板不显示 token 用量 | 聊天界面不再渲染每轮「tokens 输入/输出」，正文保持干净；用量照常记录并按 token 扣积分，唯一可见入口是【设置】【积分】的消耗明细（「原因」列含 token 数）。记录侧（moon-well 流水 `total_tokens`）零改动。 |
| 2026-10-29 | R241 整本能力缓存齐备标识 | 书籍详情页新增缓存齐备标识：整本翻译/整本朗读/全文单词详解三项缓存都备齐过时，逐项亮「已缓存」小标（含 n/m 计数与计费口径），三项齐备再加「低成本学习」总标；判定取本仓三条整本链路台账（COMPLETED + 跑满 + 正文指纹一致），不实时探测上游缓存；标识面向普通读者，三个整本入口仍仅管理员。 |
| 2026-10-29 | R252 书籍详情展示整本费用 | 书籍详情页新增整本翻译与整本朗读成本摘要：翻译展示 token 估算与全文生成积分，朗读展示字符量、全文生成积分与缓存收听积分；已缓存项按「缓存值（全文原价）」并列展示。TTS 明确不按 token 计费；成本取 moon-well 费率与 R213 缓存收听口径，不实时探测整本缓存。 |
| 2026-10-29 | R253 缓存翻译计费修订 | 翻译缓存复用由 R252 的 0 积分改为 1 积分/缓存段；详情页显示「缓存翻译 = translate.total × 1」，与全文生成原价并列。朗读缓存收听仍为 1 积分/段，两条链路段数分别取各自 readiness 台账。 |
| 2026-10-29 | R251 UI 信息架构与导航分组 | 顶栏收敛为首页/书库/学习/账号/管理五域，每页最多一个 active；侧栏按 Calibre 浏览/书架/分级/媒体/系统分层并显示数量，分级按数字排序且未知项安全兜底；移动底栏保留四个高频入口。规则集中到产品层 `cps/ui_ia.py`，不改 Calibre 路由、模型与 vendored CSS，不新增 `Shelf.kind`。长期原则沉淀到 `docs/kb/instructions/coding/ui-information-architecture.md`。 |
| 2026-10-29 | R245 积分页按功能分区与明细可读性 | 积分页改为余额 Hero + 充值/积分卡/明细/管理四个任务页签，管理内再分积分调整/充值活动/批量发卡；卡密页拆为兑换、购卡赠送、已购卡密。活动发布时间提交前规范为 `yyyy-MM-dd HH:mm:ss`，与 moon-well R229 字段级 ISO 兼容形成双保险；发布结果改行内反馈。明细获取/消耗徽标与金额改高对比样式，去掉浅色内联样式。 |
