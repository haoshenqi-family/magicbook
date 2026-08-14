# 对话回应记录

> 含每个需求的回应、冲突说明及两个文件的总结。

## 2026-08-14

### 对 requests 的回应

- **R1（增加 agents.md 说明，规范 requests.md / response.md）**：已完成。
  - 在 `AGENTS.md` 中新增「对话记录 (requests.md / response.md)」章节，并在项目文档规范表中补充两个文件的行。
  - 创建 `requests.md`（仅记录需求）与 `response.md`（记录回应与总结）。
  - 原则：尽量简单；请求冲突会在 response.md 中记录。

### 总结

- **requests.md**：需求列表，每次对话新增一条记录。
- **response.md**：每次完成后更新，含对每个需求的回应、冲突说明及两文件总结。

### 冲突记录

- 无。

---

## 2026-08-14（第二次对话）

### 对 requests 的回应

- **R2（打通 magicbook ↔ moon-well 用户体系：SSO + 身份映射）**：已完成设计 + 编码。
  - **需求澄清**：确认目标应用为 magicbook ↔ moon-well；目标形态为「用户身份映射 + 单点登录 SSO」。
  - **风险 1 验证 ✅**：经 Authentik Admin API `preview_user` 实测，同一用户 `hsq` 在 `magicbook`(pk=6) 与 `moonwell`(pk=10) 两 provider 下 `sub` 完全一致（`e3ee9b42...a3e85`），且与 magicbook 既有 `oidc_subject` 一致；两 provider `sub_mode` 均为 `hashed_user_id`。设计基石成立。
  - **新发现 ⚠️**：moon-well 本地账号 `hsq`（oidc_subject 为空）首次走 Authentik 登录会新建重复账号；已在设计 §6.4 补充账号合并策略并实现。
  - **设计文档**：`docs/feat/sso-user-unification/design/sso-user-unification-design.md`（含实现状态 §12）。
  - **编码实现（最小侵入）**：
    - magicbook：`User.user_key` 字段 + 迁移/回填（OIDC 用户=sub，本地=UUID）；OIDC/后台/LDAP/注册建号设置 user_key；`/ajax/reading-vocabulary` 注入 user_key。全量测试 **122 passed**。
    - moon-well：`ReadingVocabularyService` 按 userKey 解析内部 `userId` 落 ES；`OidcAuthController` 账号合并（email 匹配补绑）；`UserRepository` 新增查询。全量测试 **50 passed**（含修复 3 处既有测试编译错误）。
  - **迁移脚本**：magicbook `docs/temp/scripts/export_user_key_map.py`；moon-well `docs/temp/scripts/migrate_reading_vocabulary_userkey.py`。
  - **文档同步**：两侧 `reading-vocabulary.md` 的 `userKey` 语义已更新。
  - **待上线动作**（尚未上线）：部署后自动回填 → 按 §7.3 执行 ES 迁移 → 真实登录核对两端 `oidc_subject`。

### 总结

- **requests.md**：追加 R2（打通用户体系 + 前置验证 + 最小侵入编码 + 迁移脚本/文档）。
- **response.md**：记录 R2 的验证结论、设计要点、实现清单与待上线动作。
- **冲突记录**：无；本次任务涉及两个仓库（magicbook、moon-well），均在各自仓库内改动。
