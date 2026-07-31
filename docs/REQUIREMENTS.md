# Calibre-Web AI 伴读 二次开发需求文档

> 本文档记录该项目的产品需求。每当有**新增需求**或**更正/澄清需求**时，都必须更新本文档，并在文末「变更记录」中追加一条说明。
>
> - 项目性质：calibre-web 的 fork，进行二次开发。
> - 项目目标：在 calibre-web 基础上增加「AI 帮助阅读」能力。
> - 在线站点（参考）：`https://hyh.haoshenqi.top/ai/admin`（当前报错，待排查）。

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
- 已知问题：~~`https://hyh.haoshenqi.top/ai/admin` 报错~~ **已修复**（见 2026-07-31 变更记录）。

## 7. 待办与待澄清

- [x] 排查 `/ai/admin` 在线报错原因。（根因：AI 表未创建 + 默认 config 未 seed；已于 `cps/ai/__init__.py` 修复）
- [ ] 确认「deepseek V4 flash」的准确模型标识，并统一配置默认模型。
- [ ] 明确记忆系统的提取频率/触发策略是否需要可配置（当前默认每 N 条消息提取一次）。

## 8. 变更记录

| 日期 | 变更内容 | 说明 |
| --- | --- | --- |
| 2026-07-31 | 初始版本 | 依据用户原始需求整理：AI 伴读页面、AI 记忆系统、Authentik 登录、多 provider/多模型（初期 DeepSeek）、最小侵入原则；并记录 `/ai/admin` 报错待排查、deepseek V4 flash 模型名待澄清。 |
| 2026-07-31 | 修复 `/ai/admin` 500 报错 | 根因：`cps.ai.models` 在 `create_app()` 的 `Base.metadata.create_all` 之后才被导入，导致 `ai_config`/`ai_provider` 等表从未创建，首次访问 `/ai/admin` 查询即抛 `OperationalError: no such table`。修复：在 `cps/ai/__init__.py` 导入时新增 `ensure_ai_tables()` 显式建表，并调用 `seed_default_config()` 写入默认配置。验证：模拟线上全新 DB 启动，`/ai/admin` 返回 200 且含 DeepSeek；测试套件 58 passed。 |
