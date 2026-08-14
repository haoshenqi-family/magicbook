# SSO 与用户身份映射：magicbook ↔ moon-well 用户体系打通

> 功能特性：`sso-user-unification`
> 状态：设计草案（待评审）
> 日期：2026-08-14

## 1. 背景与目标

### 1.1 背景

magicbook（Calibre-Web fork，Python/Flask）与 moon-well（Spring Boot 能力中台）是两个独立部署、独立维护用户体系的应用。当前两者唯一的联动是「阅读单词学习」：magicbook EPUB 阅读器将当前页英文单词上下文代理给 moon-well 保存，接口为 `POST /reading-vocabulary/analyze`。

该集成目前以 **magicbook 本地自增 `user.id`** 作为 moon-well 的 `userKey` 落 ES。此方案存在根本性缺陷：

1. **不稳定**：`user.id` 是 SQLite 自增主键，重建/迁移 app.db 后编号会漂移；多 magicbook 实例间 id 相互冲突。
2. **不可映射**：`userKey` 与 moon-well 的 `app_user` 无任何关联，moon-well 无法把阅读词汇历史归属到自己的内部用户。
3. **与统一身份无关**：两个应用都已接入 Authentik OIDC，但 Authentik 的稳定身份（`sub`）未被利用，两端各存各的绑定，互不感知。

### 1.2 目标

1. **单点登录（SSO）**：用户经由 Authentik 登录一次，两端识别为同一人，免重复认证。
2. **用户身份映射（identity mapping）**：magicbook 用户 ↔ moon-well 用户建立可靠映射，替代当前脆弱的 `user.id` 即 `userKey` 的方案。

### 1.3 非目标（本版不涉及）

- 不合并两边的数据库/用户表（保留各自用户体系，仅打通身份）。
- 不实现双向自动登录的完整 SSO（一端登录即自动登录另一端）——见 §7「未来增强」。
- 不改变现有本地账号密码登录；不要求所有用户必须走 Authentik。

---

## 2. 现状分析

### 2.1 magicbook（本仓库）

- 用户表 `user`（SQLite `app.db`），关键字段：
  - `id`：自增主键。
  - `name`：登录名，唯一。
  - `email`：唯一。
  - `oidc_issuer` / `oidc_subject`：Authentik OIDC 绑定（`oidc_subject` 唯一）。OIDC 首次登录自动创建本地账号并绑定。
  - 无任何「跨应用稳定标识」字段。
- OIDC 登录入口：`cps/oidc.py`，`/oidc/login` → `/oidc/callback`。
  - Issuer：`https://authentik.haoshenqi.top/application/o/magicbook/`。
  - 绑定/匹配逻辑：`WHERE oidc_issuer=:issuer AND oidc_subject=:sub`；不存在则新建用户。
- 阅读词汇代理：`cps/web.py` 的 `/ajax/reading-vocabulary`：
  - 校验本地 Flask 登录会话 → 取 `current_user.id`。
  - `payload["userKey"] = str(current_user.id)`。
  - 携带 `X-Magicbook-Token`（服务端令牌）转发到 moon-well。

### 2.2 moon-well（/apprun/moon-well）

- 用户表 `app_user`（MySQL `magichouse`），关键字段：
  - `user_id`：自增主键。
  - `username`：唯一。
  - `oidc_issuer` / `oidc_subject`：Authentik OIDC 绑定（`oidc_subject` 唯一），逻辑与 magicbook 一致。
  - 其余：`password`、`email`、`nickname`、`tenant_id` 等。
- OIDC 登录入口：`OidcAuthController`，`/auth/oidc/login` → `/auth/oidc/callback`，成功后返回 moon-well 自有 JWT（`accessToken`/`refreshToken`）。
- 阅读词汇接口：`ReadingVocabularyController` / `ReadingVocabularyService`：
  - 校验 `X-Magicbook-Token`。
  - `userKey` 仅作为 ES `reading_vocabulary` 索引的检索键（`userKey.keyword`），不解析为内部用户。
  - 每条记录字段：`userKey / word / sentence / bookId / bookName / chapter / page / cfi / studyTime / translation / status / studyTimes`。

### 2.3 Authentik 现状

- 两个独立 OAuth2/OIDC Provider：`magicbook`、`moonwell`，各自有自己的 issuer URL。
- **关键前提**：Authentik 同一用户在两个 provider 下返回的 `sub` 一致（默认 `sub` 取用户 UUID，不随 provider 变化）。这是整套映射设计成立的基石，**实施前必须在 Authentik 上实测确认**（见 §10 风险）。

---

## 3. 设计原则

1. **单一身份源**：Authentik 为统一 IdP，Authentik 用户 `sub` 为跨应用 canonical identity。
2. **最小侵入 / 保留本地账号**：不合并数据库；两端通过 `oidc_subject` 建立映射。
3. **服务端令牌鉴权不变**：magicbook ↔ moon-well 之间继续用 `X-Magicbook-Token`，令牌不下发浏览器。
4. **稳定优先**：`userKey` 一经确定不可变；历史数据可迁移。
5. **本地用户兜底**：未走 Authentik 的本地用户（如 admin、历史账号）也能获得稳定的跨应用 key。

---

## 4. 总体方案

```
Authentik (sub = <UUID>)
      │  OIDC                 │  OIDC
      ▼                       ▼
magicbook.user            moon-well.app_user
  oidc_subject=sub          oidc_subject=sub
  user_key=sub(UUID)        （内部 user_id 映射）
      │
      │  /ajax/reading-vocabulary
      │  userKey = user.user_key   ← 替代 user.id
      │  + X-Magicbook-Token
      ▼
moon-well /reading-vocabulary/analyze
  userKey(sub) ──映射──▶ app_user(oidc_subject=userKey)
  记录同时写入 userId（moon-well 内部 user_id）
```

- **跨应用统一标识 = `user_key`**：
  - OIDC 用户：`user_key = Authentik sub`（即 `oidc_subject`）。
  - 本地用户：`user_key = UUID4`（创建时生成，不可变）。
- **映射关系**：magicbook.user ↔ Authentik user ↔ moon-well.app_user，三者经 `sub` 对齐。

---

## 5. magicbook 侧改动（本仓库）

### 5.1 数据模型

`cps/ub.py` 的 `User` 新增字段：

```python
# 跨应用稳定用户标识：OIDC 用户取 Authentik sub；本地用户为 UUID4。
# 生成后不可变，作为 moon-well 等外部系统的 userKey。
user_key = Column(String(64), nullable=True, unique=True)
```

对应迁移（`ub.py` 既有 schema 升级处，参照 `oidc_issuer/oidc_subject` 的 ALTER 逻辑）：

```sql
ALTER TABLE user ADD COLUMN user_key VARCHAR(64);
-- 唯一索引（Python 侧建，见下）
```

**回填逻辑**（启动时执行一次，幂等）：

```text
对每个 user_key IS NULL 的用户：
  user_key = oidc_subject  （若已有 Authentik 绑定）
  否则     = uuid4()        （本地用户）
```

### 5.2 用户创建入口统一生成 user_key

涉及入口（均需在创建时设置 `user_key`）：

| 入口 | 文件 | 规则 |
|---|---|---|
| OIDC 首次登录 | `cps/oidc.py` callback | `user_key = subject` |
| 后台新增用户 | `cps/admin.py`（约 1278/1607 行）| `user_key = uuid4()` |
| 其他本地创建路径 | `cps/web.py`（约 1327 行）| `user_key = uuid4()` |

> 说明：OIDC 用户后续即使补充 `oidc_subject`，`user_key` 已存在则不改写，保证不可变。

### 5.3 代理接口注入逻辑

`cps/web.py` `/ajax/reading-vocabulary`：

```python
payload["userKey"] = current_user.user_key or str(current_user.id)
```

- `user_key` 正常非空；`or str(current_user.id)` 仅为回填前的旧实例兜底。

### 5.4 旧 id → user_key 映射导出

新增一次性脚本（放 `docs/temp/scripts/`，不跟踪 Git）或管理端点，导出：

```text
映射文件格式（JSON/CSV）：{ old_user_id: user_key }
```

供 moon-well 侧重写 ES 旧数据（见 §7）。

---

## 6. moon-well 侧改动（/apprun/moon-well）

### 6.1 身份解析

`ReadingVocabularyService.analyze` 中，在 `require(userKey)` 之后按 `userKey` 解析内部用户：

```text
app_user = SELECT * FROM app_user WHERE oidc_subject = userKey AND oidc_subject IS NOT NULL
```

- 命中：ES 记录额外写入 `userId = app_user.user_id`（moon-well 内部 id）。
- 未命中（本地用户/未走 Authentik）：不写入 `userId`，保持 `userKey` 原样——与现状行为一致，仅失去「映射到内部用户」能力。

### 6.2 数据结构

`reading_vocabulary` ES 索引新增可选字段 `userId`（long，moon-well `app_user.user_id`）。

> 兼容性：ES 动态 mapping 可自动识别；生产建议提前为该字段建 mapping。

### 6.3 接口契约不变

`POST /reading-vocabulary/analyze`、`POST /reading-vocabulary/known/{word}` 的请求/响应结构不变；`userKey` 含义从「magicbook 数字 id」升级为「magicbook user_key（Authentik sub / UUID）」。

### 6.4 OIDC 账号合并（打通用户体系的必要配套）

> **问题（2026-08-14 实测发现）**：moon-well `app_user` 现有本地账号 `hsq`（user_id=1，`oidc_subject=NULL`），与 Authentik 用户 `hsq` 为同一真人（email 均为 `haoshenqitop@163.com`）。其首次经 `/auth/oidc/callback` 登录时，`OidcAuthController.upsertUser` 按 `oidc_subject` 匹配不到，会**新建第二个 username 相同的用户**（数据库 `username` 无唯一约束、不报错，但同一真人产生两条记录，数据归属分裂）。

**改动**：`upsertUser` 增加账号合并策略，按优先级匹配：

```text
1. 按 oidc_issuer + oidc_subject 匹配  → 命中即绑定/复用（现有逻辑）
2. 未命中时按 email（或 username）匹配现有本地账号
   → 命中：复用该账号，补写 oidc_issuer/oidc_subject 完成绑定
3. 均未命中 → 新建（现有逻辑）
```

> 注意：合并以「email 精确匹配」为默认，避免误绑；username 匹配为可选项。此策略同样适用于 magicbook（`cps/oidc.py` 当前明确「不静默合并」，若需打通本地历史账号，可参照提供管理员手动绑定或同策略合并）。

---

## 7. 数据迁移

### 7.1 ES 旧记录重写（`reading_vocabulary`）

1. magicbook 侧按 §5.4 导出 `{old_id: user_key}` 映射。
2. moon-well 侧执行一次性重写脚本：
   - 遍历 ES `reading_vocabulary` 中 `userKey` 为纯数字的旧记录。
   - 按 `old_id` 查映射 → 新 `userKey`（若新 key 命中 `app_user.oidc_subject`，同时补写 `userId`）。
   - `_update_by_query` 或逐条 index 覆盖，不新增事件记录（保持统计语义）。

> 注意事项：若某 app.db 已重建且旧 id 已不可回溯，该部分用户历史无法迁移，仅影响「陌生词状态回退」（可能再次标记为陌生），可接受。

### 7.2 app.db 回填

见 §5.1，magicbook 启动迁移自动完成，幂等。

### 7.3 上线顺序（避免数据割裂）

1. 先改 magicbook：新增 `user_key` + 回填 + 代理注入新规则（此阶段 moon-well 仍按旧逻辑存，`userKey` 变为 UUID/sub 属新命名空间）。
2. 再改 moon-well：身份解析 + 写 `userId`。
3. 执行 ES 重写脚本：把旧数字 id 记录迁移到新 `userKey`。
4. 观察 `studyTimes`/`unknown` 是否连续。

> 风险提示：若上线间隔内新老 `userKey` 并存，ES 中同一用户的记录会短暂分裂，重写脚本后合流。建议 1+2 一起上线、随即执行 3。

---

## 8. SSO 体验设计

### 8.1 本期（Authentik 会话级 SSO）

- 两应用统一走 Authentik 登录。
- 用户登录过一次 Authentik 后，在两应用点击登录均免输凭证（Authentik 域 cookie）。
- 因 `sub` 一致，两端登录后映射为同一人。

### 8.2 未来增强（不纳入本版）

- **自动登录联动**：一端登录成功后，服务端令牌交换在另一端静默建立会话。
- **统一登录入口/门户**：合并 `sso-frontend` 之类的现有前端，提供应用导航。

---

## 9. 测试与验证

### 9.1 magicbook 侧（pytest）

- 迁移回填：构造含 OIDC/本地用户的旧库 → 启动 → 断言 `user_key` 填充且幂等。
- OIDC 登录：新用户 `user_key == subject`；已有用户 `user_key` 不被改写。
- `/ajax/reading-vocabulary`：注入的 `userKey` 为新 `user_key` 而非 `user.id`。
- 回归：`tests/test_reading_vocabulary.py` 既有断言随注入规则更新。

### 9.2 moon-well 侧（单元/接口）

- `analyze`：`userKey` 命中 `oidc_subject` 时 ES 记录含 `userId`；未命中时无 `userId`。
- 兼容：旧纯数字 `userKey` 仍可查询（迁移前不报错）。

### 9.3 端到端

- Authentik 上同一用户分别登录两端 → 比对两端 `oidc_subject` 一致。
  > 已通过 provider `preview_user` 接口预先验证一致（见 §10 风险 1）；上线后仍建议以真实登录再核对一次。
- 阅读器翻页上报单词 → moon-well ES 记录 `userKey` 为 Authentik sub 且 `userId` 正确。
- 迁移脚本前后 `studyTimes` 连续。

---

## 10. 风险与待确认

| # | 风险/事项 | 影响 | 应对 |
|---|---|---|---|
| 1 | ~~**Authentik `sub` 是否跨 provider 一致**~~ **✅ 已实测验证（2026-08-14）** | 整套映射基石 | 经 Authentik Admin API `GET /api/v3/providers/oauth2/{id}/preview_user/?for_user=<pk>` 对比：magicbook(pk=6) 与 moonwell(pk=10) 对同一用户 `hsq`(pk=7) 生成的 `sub` 完全一致，均为 `e3ee9b42f5deb3b7c4bf2f3b877e5e91413bb3d42e3301646f13d2e6d51a3e85`（两 provider `sub_mode` 均为 `hashed_user_id`，实际输出用户 UUID）；且与 magicbook 现存 `oidc_subject` 绑定值一致 |
| 2 | 旧 app.db 已重建，历史 id 不可回溯 | 部分阅读词汇历史无法迁移 | 接受「陌生词状态回退」；文档明示 |
| 3 | 两个仓库上线窗口 | 新老 `userKey` 并存造成短期数据分裂 | 按 §7.3 顺序、缩短窗口 |
| 4 | `user_key` 唯一约束与存量重复 | 回填冲突 | 回填前先为已有 `oidc_subject` 用户设 `user_key=sub`（天然唯一），UUID 生成时重试去重 |
| 5 | **moon-well OIDC 登录账号重复**（已实测确认现象） | 同一真人产生两个 `app_user` 记录，数据归属分裂 | §6.4 账号合并策略：按 email 复用本地账号并补绑 `oidc_issuer/oidc_subject` |

---

## 11. 涉及文件清单

### magicbook（本仓库）

- `cps/ub.py`：`User.user_key` 字段 + schema 迁移/回填。
- `cps/oidc.py`：OIDC 创建用户时设置 `user_key`。
- `cps/admin.py`、`cps/web.py`：本地建号入口设置 `user_key`。
- `cps/web.py`：`/ajax/reading-vocabulary` 注入新 `userKey`。
- `tests/`：新增/更新上述行为测试。
- `docs/temp/scripts/`：旧 id→user_key 映射导出脚本（不跟踪 Git）。

### moon-well（/apprun/moon-well）

- `ReadingVocabularyService.java`：按 `userKey` 解析 `app_user`（`oidc_subject`），写入 `userId`。
- 迁移脚本：重写 ES `reading_vocabulary` 旧记录。
- 相关测试。

### 文档

- 本设计文档；`docs/reading-vocabulary.md`（magicbook 侧）与 moon-well 侧 `docs/readme/reading-vocabulary.md` 同步更新 `userKey` 语义说明。

---

## 12. 实现状态（2026-08-14）

### ✅ 已完成（编码）

**magicbook（本仓库）**
- `cps/ub.py`：`User.user_key` 字段、`migrate_user_key_column` 迁移、`backfill_user_keys` 幂等回填、`create_admin_user/create_anonymous_user` 生成 `user_key`。
- `cps/oidc.py`：OIDC 创建用户 `user_key = subject`。
- `cps/admin.py`（后台建号 / LDAP 建号）、`cps/web.py`（注册）设置 `user_key = uuid4()`。
- `cps/web.py` `/ajax/reading-vocabulary`：注入 `user_key`（兜底 `user.id`）。
- 测试：新增 `tests/test_user_key.py`（回填/幂等/初始用户/OIDC callback），更新 `tests/test_reading_vocabulary.py`。
- 全量测试：**122 passed**。
- 迁移脚本：`docs/temp/scripts/export_user_key_map.py`（导出 `{old_id: user_key}`，不跟踪 Git）。

**moon-well（/apprun/moon-well）**
- `ReadingVocabularyService.java`：按 `userKey` 解析 `app_user.oidc_subject`，命中写入 `userId`（ES `reading_vocabulary` 新增可选字段）。
- `OidcAuthController.java`：`upsertUser` 账号合并（按 email 复用本地账号并补绑 OIDC）。
- `UserRepository.java`：新增 `findByOidcSubject` / `findFirstByEmail`。
- 测试：`ReadingVocabularyServiceTest`（+2）、新增 `OidcAuthControllerTest`（3）；**全量 50 tests passed**。
- 修复既有测试编译错误 3 处（`new User(...)` 旧 13 参构造器 → 15 参，行为不变）。
- 迁移脚本：`docs/temp/scripts/migrate_reading_vocabulary_userkey.py`（重写 ES 旧记录，dry-run 支持）。

### ⚠️ 待上线动作（风险 2/3 已确认忽略，尚未上线）

1. 部署后 magicbook 启动自动完成 `user_key` 迁移回填。
2. 上线切换后按 §7.3 顺序执行 ES 迁移（导出映射 → 重写 ES → 校验 `studyTimes` 连续）。
3. 上线后以真实 Authentik 登录两端各一次，核对两端 `oidc_subject` 一致（风险 1 已通过 `preview_user` 预验证）。
