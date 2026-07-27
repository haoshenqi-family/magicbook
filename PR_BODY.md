## feat(ai): AI 伴读功能

calibre-web fork，在原阅读器页面上增加 AI 伴读面板。AI 支持多 provider 多模型，默认 DeepSeek。配套 AI 记忆系统、Authentik OAuth 登录。

### 新增功能

- **AI 伴读面板**：在 EPUB / PDF / TXT 阅读器内浮动侧栏，可与 AI 对话关于书籍的内容。聊天上下文包括：书名/作者/标签/简介 metadata、当前页文本、用户问题。
- **SSE 流式响应**：AI 回答实时流式传输到前端，Markdown 渲染。
- **AI 记忆系统**：
  - 对话历史持久化（按 user+book 分组）。
  - 跨书长期记忆：每 N 轮对话自动调用 LLM 提取一条用户偏好/兴趣/知识水平，注入到后续所有对话的 system prompt。
  - 用户可查看、清除自己的记忆。
- **Authentik OAuth 登录**：作为新增 OAuth provider，配置存于 `AiProvider` 表，复用 calibre-web 现有的 token 存储与用户绑定逻辑。
- **多 provider / 多模型抽象**：`BaseProvider` + 注册表机制，DeepSeek 已实现；新 provider 只需继承基类并注册即可。
- **管理员配置页面**：`/ai/admin` 启用 AI、配置 provider API key（Fernet 加密）、选择默认模型、调整记忆提取频率、注入额外 system prompt。

### 架构约束

- 所有 AI 代码集中在 `cps/ai/` 子包（provider、记忆、路由、auth、模型、加密、注册表），新增约 1500 行 Python。
- 上游 calibre-web 仅修改 6 个文件（最小侵入）：`cps/main.py`（注册蓝图+Authentik）、`cps/jinjia.py`（新增 `from_json` 过滤器）、`cps/templates/layout.html`（AI 管理入口）、3 个阅读器模板（注入聊天面板 include）。
- 新表自动创建（继承 `ub.Base` + `metadata.create_all`），无 schema 迁移。
- API 密钥 Fernet 加密存储，复用 calibre-web 现有的 `get_encryption_key`。
- 路由复用 calibre-web 的 `user_login_required` 装饰器。

### 包含的提交

- `09e7c47` SQLAlchemy 模型
- `cfcbe46` Fernet 加密工具
- `c86d9f9` Provider 基类 + DeepSeek 实现（SSE 流式）
- `1024dd9` Provider 注册表 + 默认配置种子
- `fb4dfe2` 记忆系统（system prompt 构建 + 跨书记忆提取）
- `dd6cd0d` 路由、模板、Authentik 集成、阅读器面板挂载

### 测试

新增 5 个测试文件，58 个测试用例全部通过：

- `test_ai_models.py` — 模型默认值、关系、唯一约束
- `test_ai_crypto.py` — Fernet 加解密、空值、错误密钥处理
- `test_ai_memory.py` — system prompt 构建、HTML 剥离、记忆提取间隔、跨用户隔离
- `test_provider_deepseek.py` — provider 类、SSE 流式、非流式、错误处理
- `test_registry.py` — 注册表、默认配置种子
- `test_ai_routes.py` — 各 API 端点、鉴权、消息持久化
- `test_authentik.py` — Authentik 蓝图注册
- `test_integration.py` — 端到端：配置 → 对话 → 历史 → 记忆提取 → 记忆复用

```
58 passed in 18.17s
```

### Snapshot

Tag: `0.1.0-2026-07-27-0802`

### 已知限制

- 当前仅 DeepSeek 一个 provider 实现（`DeepSeekProvider`），但注册表已支持多 provider，按需添加新 provider 类即可。
- 前端聊天面板未做国际化（使用 `{{_('...')}}` 标记，依赖 calibre-web babel 自动抽取）。
- 记忆提取调用 LLM（非流式），默认每 10 轮对话一次，频率可在 admin 页调整。

### 测试运行

```bash
python -m pytest tests/ -v
```
