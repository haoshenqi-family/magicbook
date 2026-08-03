# AI Reading Companion — 多会话 + AI 数据独立存储 设计

## 1. 背景与需求

现状：AI 伴读的会话模型是「每本书一个会话」（`AiConversation` 按 `(user_id, book_id)` 唯一），用户无法为同一本书开多个独立对话；AI 相关数据（`ai_*` 表）与 Calibre-Web 用户/配置数据同存在 SQLite `app.db` 中。

需求：
1. **新建会话**：同一本书可创建多个会话，阅读页通过「+ 新建会话」按钮和会话下拉列表切换。
2. **对话入库**：每次对话（用户消息 + AI 回复）都必须持久化到数据库（现状已满足，改造后继续保持）。
3. **数据库连接配置化**：AI 数据连接信息放在 `.env`（`DATASOURCE_*` / `AI_DATABASE_URL`），`.env` **不提交** Git。

用户已确认：
- 仅 AI 会话数据迁移到 MySQL（`ai_*` 表），Calibre 书库与用户体系仍用 SQLite。
- MySQL 实例 `192.168.31.9:3306` 可访问，但需**另建独立数据库**（建议 `ai_companion`）。
- 交互形态：**新建按钮 + 会话下拉列表**。

> 注意：当前开发环境无法直连内网 MySQL（3306 拒绝连接），因此数据源采用「配置了 `AI_DATABASE_URL` 用 MySQL，未配置回退独立 SQLite 文件」策略，保证项目可启动、测试可在无 MySQL 环境运行。

## 2. 现状分析

| 文件 | 现状 | 改造点 |
|------|------|--------|
| `cps/ai/models.py` | 继承 `cps.ub.Base`，与 ub 共用 SQLite | 改为独立 `AiBase`；String 补长度（MySQL 要求）；去掉对 `user` 表的外键 |
| `cps/ai/routes.py` | `_session()` 返回 `ub.session`；按 `(user, book)` 唯一会话 | 数据源换 ai_session；新增多会话 API |
| `cps/ai/memory.py` | 用 `ub.session` 操作 `AiUserMemory` | 换 ai_session |
| `cps/ai/__init__.py` | `seed_default_config` 用 `ub.session` | 换 ai_session |
| `cps/ai/authentik.py` | 查 `AiProvider` 用 `ub.session`（`ub.OAuthProvider` 仍属 ub） | 查 AI 表换 ai_session |
| `cps/ub.py` | `init_db` 里 import AI 模型注册到 `ub.Base` | 删除该段（AI 表不再属于 ub.Base） |
| `cps/__init__.py` | `create_app` 仅初始化 ub | 加 `load_dotenv()` + `init_ai_db()` |
| `cps/main.py` | 注册 blueprint + `seed_default_config` | 基本不动（依赖 create_app 已 init AI DB） |
| 前端 | `ai_chat_panel.html` + `ai_chat.js` 单会话 | 加会话下拉 + 新建按钮 + 切换 |

## 3. 方案设计

### 3.1 数据层独立（新增 `cps/ai/database.py`）

- `AiBase = declarative_base()`：所有 `ai_*` 模型继承它，与 `ub.Base` 完全解耦。
- `init_ai_db()`：
  - 读取环境变量 `AI_DATABASE_URL`（支持 `mysql+pymysql://...` 或 `sqlite:///...`）。
  - 未配置 → 回退 SQLite：`<app_DB目录>/ai_companion.db`（持久化，不依赖 ub 会话）。
  - 创建 engine（`pool_pre_ping=True`），`AiBase.metadata.create_all(engine)` 自动建表。
- `get_session()`：返回 scoped_session（懒加载，启动失败时给出清晰错误）。
- 每次请求结束后 `remove()`（通过 `teardown_appcontext` 或显式调用）。

### 3.2 模型变更（`cps/ai/models.py`）

- `AiConfig`：`default_provider` String(50)、`default_model` String(100)。
- `AiProvider`：`provider_name` String(100, unique)、`display_name` String(100)、`api_base` String(500)、`api_key_encrypted` String(1000)、`models_json` Text。
- `AiConversation`：`user_id` Integer（**去外键**，AI 库无 `user` 表）、`book_id` Integer、`book_format` String(20)、`title` String(500)、时间戳；`messages` relationship + cascade 保留（`conversation_id` FK 指向同库 `ai_conversation.id`）。
- `AiMessage`：`conversation_id` FK、`role` String(20)、`content` Text、`page_context` Text。
- `AiUserMemory`：`user_id` Integer（去外键）、`content` Text、`source_book_id` Integer。
- 所有 String 列补长度以兼容 MySQL。

### 3.3 后端 API 变更（`cps/ai/routes.py`）

新增多会话能力，兼容前端新交互：

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/ai/conversations/<book_id>` | 当前用户在该书下的会话列表（含 `id/title/created_at/updated_at/message_count`，按更新时间倒序） |
| POST | `/ai/conversations/<book_id>` | 新建空会话，返回 `{conversation_id, title}` |
| POST | `/ai/chat` | 请求体增加可选 `conversation_id`；未传或会话不存在 → 自动新建；首条消息写入后若标题为空则用消息前 30 字自动命名 |
| GET | `/ai/history/<conversation_id>` | 按**会话 id**返回该会话消息（原按 book_id 的语义废弃） |
| DELETE | `/ai/history/<conversation_id>` | 按会话 id 删除（含级联消息） |

`/ai/memory`、`/ai/memory/clear`、`/ai/admin` 不变（仅数据源切换）。

### 3.4 前端变更

- `ai_chat_panel.html`：抽屉 header 增加会话 `<select>`（标题下拉）+「＋ 新建会话」按钮。
- `ai_chat.js`：
  - 打开抽屉 → `GET /ai/conversations/<book_id>` 渲染下拉，默认选中最近会话并加载其历史。
  - 「＋ 新建会话」→ `POST /ai/conversations/<book_id>` → 清空消息区并切换。
  - 切换下拉 → `GET /ai/history/<conversation_id>` 加载。
  - 发送消息携带 `conversation_id`。
- `ai_chat.css`：下拉/按钮样式。

### 3.5 配置与安全（`.env`，不提交）

- 新增依赖：`pymysql`（MySQL 驱动）、`python-dotenv`（加载 `.env`）。
- `load_dotenv()` 在 `cps/ai/database.py::init_ai_db()` 内部调用（**不侵入** `create_app`）。
- 新建 `.env`（已 gitignore）：配置 `AI_DATABASE_URL=mysql+pymysql://HSQ:<password>@192.168.31.9:3306/ai_companion?charset=utf8mb4`。
- `.env.example`：仅放占位模板（**不含真实密码**）。
- `.gitignore`：新增 `.env`、`docs/temp/`（前次已加）。
- 建库脚本：`docs/feat/ai-reading-companion/sql/create_ai_database.sql`（`CREATE DATABASE IF NOT EXISTS ai_companion`）。

### 3.6 最小侵入设计（不碰系统 SQLite / 不侵入 create_app）

- **独立数据存储**：AI 数据**绝不**写入系统 `app.db`（`cps/ub.py` 已移除把 AI 表注册到 `ub.Base` 的代码）。未配置 `AI_DATABASE_URL` 时回退到**独立的 `ai_companion.db`**（位于 app.db 同目录）；配置 MySQL 时走 MySQL。
- **零侵入 `create_app`**：`cps/__init__.py` 完全未改动。AI 数据层由 `database.py::get_session()` **懒初始化**（首次使用自动 `init_ai_db()`），并在 `cps/main.py`（AI 集成点）显式调用 `init_ai_db()` 与注册 `teardown_appcontext(remove_session)`。
- **时区**：所有 AI 时间统一使用**中国大陆时区（Asia/Shanghai，UTC+8）**，见 `cps/ai/timezone.py`。返回 naive 北京时间（避免 MySQL DATETIME 无时区 + PyMySQL aware→UTC 转换导致 SQLite/MySQL 存储不一致）。

### 3.7 测试适配

- `tests/conftest.py`：**模块级**设置 `CALIBRE_DBPATH` 与 `AI_DATABASE_URL` 到临时目录（必须在任何 `import cps` 之前，因为 `cps.constants.CONFIG_DIR` 在导入时固化）；`create_app` 后显式调用 `init_ai_db()`；清理逻辑改用 `ai_session`；新增 `ai_session` fixture；测试环境强制标准登录（`config_login_type=LOGIN_STANDARD`、`services.ldap=None`，暂不考虑 LDAP）。
- 各测试改用 `cps.ai.database.get_session()` 操作 AI 表。
- 新增多会话用例：新建会话、列表、切换历史、按会话删除、chat 带/不带 conversation_id、并发多会话互不串扰、book_title 非空时标题仍由首条提问命名、会话列表按活跃时间排序、旧数据迁移。

## 4. 评审修复项（交叉 Code Review 后）

| 项 | 问题 | 修复 |
|----|------|------|
| 会话标题 | 前端恒传 `book_title`，自动命名失效（所有会话标题=书名） | 新建会话始终用默认标题，首条提问统一覆盖命名（`routes.py` `_get_or_create_conversation` + `chat`） |
| 活跃排序 | `updated_at` 仅靠 `onupdate`，追加消息不刷新，列表按创建序 | 保存用户/助手消息时显式 `conv.updated_at = now()`（北京时间） |
| 旧数据迁移 | 原 `app.db` 中 `ai_*` 表数据会孤儿化，升级即丢 | `database.py::_migrate_legacy_sqlite()`：新库无会话时，将旧 `ai_*` 行一次性拷入（SQLAlchemy 1.x/2.0 兼容，失败仅告警不阻塞启动） |
| 并发隔离 | gevent/tornado 单线程下默认线程级 `scoped_session` 被并发请求共享 | `scoped_session(..., scopefunc=greenlet.getcurrent)`（无 gevent 时回退线程作用域） |
| N+1 | 会话列表逐条 `messages.count()` | 一次性 `GROUP BY conversation_id` 批量计数 |
| 事务 | 用户消息先行提交，断连/503 留下悬空用户消息 | 保留用户消息立即可见语义（可接受），异常路径不产生半提交 |
| 测试根因 | 模块级 `import cps.ai` 早于 fixture 设置 env，`CONFIG_DIR` 指向真实 app.db 导致 LDAP/pbkdf2 | conftest 模块级设置环境变量 |

## 5. 移动端适配

- `cps/static/css/ai_chat.css` 新增 `@media (max-width: 600px)`：
  - FAB 缩小（48px）并贴近边缘，避免遮挡 epub.js 翻页热区。
  - 抽屉全屏 `100vw × 100vh`，形成聚焦的聊天视图。
  - 输入框/发送按钮加大触控目标（16px 字号），消息气泡加宽。

## 6. 风险与注意

- MySQL 连接不可达时，配置了 `AI_DATABASE_URL` 会**启动失败**（不静默回退），避免数据写错地方；未配置则用 SQLite 回退，保证本地/CI 可跑。
- **旧数据迁移**：首次升级时自动把原 `app.db` 中的 `ai_*` 数据拷入新存储；新存储已有数据则跳过。若要彻底清理旧表，可手动 `DROP TABLE`（可选）。
- **LDAP 暂不考虑**：测试环境强制标准登录；生产如需 LDAP 登录请另行配置（本次不涉及）。
- **MySQL 字符集**：必须按 `docs/feat/ai-reading-companion/sql/create_ai_database.sql` 以 `utf8mb4` 建库，否则 emoji/多字节会报 `Incorrect string value`。
- **时区**：AI 表时间统一为**中国大陆时区（Asia/Shanghai，UTC+8）**，存 naive 北京时间墙钟时间（见 `cps/ai/timezone.py`）。不采用 aware datetime，以免 MySQL（DATETIME 无时区 + PyMySQL aware→UTC 转换）与 SQLite 存储不一致。
- 移除 `user` 外键后，AI 表与用户表仅应用层关联（`user_id` 整数），删除用户时需注意孤儿数据（当前无删除用户场景，可接受）。
- **`.env` 限制**：`load_dotenv()` 在 `cps.constants` 导入后执行，因此 `.env` 仅用于 `AI_DATABASE_URL`（`CALIBRE_DBPATH` 等需通过环境变量/容器注入）。
