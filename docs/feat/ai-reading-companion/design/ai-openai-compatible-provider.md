# AI Provider 架构：OpenAI 兼容 Provider

## 1. 背景与需求

AI 伴读目前仅内置 DeepSeek provider。用户希望增加一个**兼容 OpenAI 接口**的通用 provider，以便接入任意 OpenAI 兼容端点（OpenAI 官方、Azure 兼容端点、本地 Ollama/vLLM、OneAPI/new-api 网关等）。

## 2. 现状分析

| 文件 | 现状 |
|------|------|
| `cps/ai/base.py` | `BaseProvider` 抽象基类 + `ModelInfo`（id/label/context_window/supports_streaming） |
| `cps/ai/deepseek.py` | `DeepSeekProvider`：硬编码的 OpenAI 兼容实现（名称、错误消息写死） |
| `cps/ai/registry.py` | provider 类注册表；`list_providers()` 供 admin 下拉，`get_provider(name, api_base, api_key)` 实例化 |
| `cps/ai/__init__.py` | `seed_default_config()` 为每个 provider 建 DB 行（api_base / 加密 api_key / models_json） |
| `cps/templates/ai_admin.html` | 通用渲染所有 `AiProvider` 行：api_base、api_key、models_json（`id|label` 换行） |

## 3. 设计

### 3.1 新增 `cps/ai/openai_compat.py`

`OpenAICompatProvider(BaseProvider)`：
- `name` → `"openai"`；`requires_key = False`（支持无鉴权本地端点）。
- `chat()` → POST `{api_base}/chat/completions`，OpenAI 格式 payload，Bearer 鉴权；支持流式（SSE 生成器）/非流式；错误消息用「OpenAI-compatible」措辞。
  - 保留字段（model/messages/stream）在 kwargs 合并后强制覆盖，防止调用方篡改。
  - 流式 SSE 中出现 `{"error": ...}` 数据块会抛出 `RuntimeError`（不静默吞掉）。
  - 非流式响应解析异常统一转为 `RuntimeError`（符合 `BaseProvider` 契约）。
- `available_models()` → 有 api_key 时尽力从 `{api_base}/models` 拉取（容错 dict/扁平字符串列表；失败/无 key 返回空，不阻塞）；模型列表的真实来源是 admin 的 `models_json`。
- **无 api_key 也允许**（如本地 Ollama），此时不发送 `Authorization` 头。

### 3.1.1 应用层放行 keyless provider（`cps/ai/base.py` + `cps/ai/routes.py`）

- `BaseProvider` 新增类属性 `requires_key = True`；`OpenAICompatProvider` 覆写为 `False`。
- `get_active_provider()` 仅在 `provider.requires_key` 为 True 且无 key 时才拒绝（`routes.py`），因此 Ollama 等无鉴权端点可正常使用。

### 3.2 注册（`cps/ai/registry.py`）

`register_provider_class("openai", OpenAICompatProvider)` —— admin 下拉自动出现 `openai` 选项。

### 3.3 默认配置（`cps/ai/__init__.py::seed_default_config`）

默认创建 `openai` 行：`display_name="OpenAI Compatible"`、`api_base=""`（留空由用户填）、默认模型 `gpt-4o` / `gpt-4o-mini`。重构 seed 为循环创建 deepseek + openai 两行，避免重复代码。

### 3.4 配置方式（admin 页面 `/ai/admin`）

用户填入：
- `api_base`：如 `https://api.openai.com/v1`、`http://localhost:11434/v1`（Ollama）等
- `api_key`：OpenAI 格式密钥（可留空给本地无鉴权端点）
- `models`：每行 `模型id|显示名`（如 `gpt-4o|GPT-4o`）

## 4. 测试

- `tests/test_provider_openai_compat.py`：name、/models 拉取（成功/无 key/错误）、流式/非流式、HTTP 错误、api_base 尾部斜杠处理、无 key 省略鉴权头。
- `tests/test_registry.py`：`openai` 在 list_providers、可实例化；seed 创建 openai 行且幂等。

## 5. 风险与注意

- **`available_models()` 只是尽力而为**：`/models` 可能需额外鉴权或不实现，返回空不影响功能；admin 的 `models_json` 是模型列表的唯一权威来源。
- **认证**：`Authorization: Bearer <key>` 仅在有 key 时发送，兼容无鉴权的本地端点。
- **URL 拼接**：`api_base.rstrip("/")` 再拼 `/chat/completions`，避免双斜杠。
