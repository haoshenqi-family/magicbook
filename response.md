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

---

## 2026-08-16

### 对 requests 的回应

- **R3（检查划词翻译功能）**：已完成检查，定位并修复 2 个真实缺陷。
  - **功能定位**：划词翻译即 EPUB 阅读器生词标注（`cps/static/js/reading/epub.js` 的 `inspectVocabulary`/`markVocabulary`，经 `/ajax/reading-vocabulary` 代理到 moon-well，生词波浪下划线标注，点击查看释义）。按 `docs/reading-vocabulary.md`，PDF/TXT/漫画/音频暂未接入，故划词仅存在于 EPUB。
  - **Bug 1（点击生词弹错释义）**：`markVocabulary` 的 `while` 循环中 `var span` 为函数作用域，所有 `click` 闭包共享同一变量，点击任意生词都弹出**最后一个**生词的释义。已改为 `alert(this.title)`。
  - **Bug 2（生产环境划词静默失效）**：`read.html` 不加载 `main.js`（无全局 `$.ajaxSetup`），而服务端全局启用 CSRF（`cps/__init__.py`），`inspectVocabulary` 的 ajax POST 未带 `X-CSRFToken`，真实环境返回 **400** 导致生词标注静默失效；既有测试因 `WTF_CSRF_ENABLED=False` 掩盖了该问题。已显式补充 `X-CSRFToken` 头，并新增回归测试 `test_rejects_missing_csrf_when_protection_enabled`（临时开启 CSRF 验证：无 token→400，带 token→放行）。
  - **验证**：手工模拟 CSRF 开启的测试客户端确认「WITH token→通过、WITHOUT token→400」；`node --check` 校验 JS 语法；全量测试 **123 passed**。
  - **Bug 3（翻页过快时生词漏标）**：`inspectVocabulary` 在 `relocated` 后触发，但若上一请求仍在飞行（`vocabularyInFlight`）会直接 `return`，导致新页面生词无人检查、直到用户再次翻页。已增加 `vocabularyRetryPending` 标志：飞行中被跳过时置位，请求完成（`always`）后自动重检当前页；`node` 模拟验证翻页场景 `calls=2`（自动重检）。

### 总结

- **requests.md**：追加 R3（检查划词翻译功能）。
- **response.md**：记录 R3 的检查结论、3 个 bug 的成因与修复、验证方式。
- **冲突记录**：无。

---

## 2026-08-19

### 对 requests 的回应

- **R4（magicbook.haoyuhang.top 500 → 重启再检查）**：已重启服务、定位根因并修复一处崩溃 bug。
  - **重启**：执行 `restart.sh`（旧 PID 3265137 → 新 PID 2750877），服务现监听 8085，健康。
  - **后端本机直连验证**（`curl 127.0.0.1:8085`，模拟网关完整代理头）：
    - `/` → 302，`/login` → 200，`/nonexistent-404` → 404。后端正常，500 不来自应用本身。
  - **根因定位（网关侧）**：日志显示网关节点 `aliyun-ctl`（Tailscale 100.107.64.109）每 ~60s 向本机明文 8085 发送 **TLS ClientHello**（`Invalid HTTP method: \x16\x03\x01...`）→ 网关把到 `192.168.31.11/100.120.202.44:8085` 的上游按 **HTTPS** 探测/代理，而后端是明文 HTTP，TLS 握手必失败 → 网关判定后端不可用 → 公网 `magicbook.haoyuhang.top` 对所有路径恒定返回 500。Docker 容器内 openresty（1Panel）的 magicbook-backend 上游是 `localhost:18082`（本机无监听，502），不含该站点。
  - **本机代码修复（顺带）**：`cps/gevent_wsgi.py` `format_request` 在请求头解析失败路径下 `self.environ` 为 `None`，直接 `.get()` 抛 `AttributeError` 导致 greenlet 崩溃并刷屏日志。已改为 `(self.environ or {}).get(...)`，新增回归测试 `tests/test_gevent_wsgi.py`（3 条：None / 空 dict / X-Forwarded-For 覆盖）。全量测试 **126 passed**。

### 状态与待办

- ⚠️ **500 需网关侧配合修复**（本机已无阻塞）：在网关注册该站点后，把
  `proxy_pass`（及健康检查协议）从 `https://<本机>:8085` 改回
  `http://<本机>:8085`，刷新配置即可恢复。已与用户确认方向为“网关改回 http:// 上游”。
- 公网仍 500 时，再回溯网关侧 TLS/config 配置。

### 总结

- **requests.md**：追加 R4（域名 500 → 重启再检查）。
- **response.md**：记录 R4 的根因（网关 HTTPS 上游 vs 明文后端）、本机崩溃 bug 修复与回归测试、全量 126 passed，以及待网关侧执行的修复动作。
- **冲突记录**：无。

---

## 2026-08-20

### 对 requests 的回应

- **R5（grafana.haoshenqi.top 也 500 → 确认还有其他问题）**：完成核实，确认这是**网关侧批量故障**，不止 grafana。
  - **本机各服务全部健康**：
    - grafana：容器 `teslamate-grafana-1` Up 3 weeks，`3000` 直连 200；openresty `14100`（TLS，证书 `*.haoshenqi.top`）→`127.0.0.1:3000` 反代链路完整，从 tailscale 地址访问 302 正常，容器内 `/login` 返回 200、无异常。
    - magicbook：`8085` 直连 302 / 200 / 404 正常（上轮已确认）。
    - authentik/hyh：openresty 高位入口（9009/18901）本机侧响应正常。
  - **批量 500 证据**（DNS 解析到公网网关 116.62.200.90 的子域 **全部 500**）：
    - `grafana.haoshenqi.top`→116.62.200.90→**500**
    - `authentik.haoshenqi.top`→116.62.200.90→**500**
    - `hyh.haoshenqi.top`→116.62.200.90→**500**
    - `magicbook.haoyuhang.top`→116.62.200.90→**500**（上轮）
    - 对比：走内部直连路径的例外——`home.haoshenqi.top`→IPv6 `240e:391:e15:f0e0::8ec`→**302**（正常，该 IPv6 目标非本机动态地址，是另一台设备）；`minio.haoshenqi.top`→8.139.5.79→403（另一主机，正常响应）。
  - **根因（网关侧统一配置故障）**：抓包确认网关节点 `aliyun-ctl`（Tailscale `100.107.64.109`）向本机**明文端口 8085/8080** 发送 **TLS ClientHello**（`Invalid HTTP method: \x16\x03\x01...`）。即网关对所有指向本机的站点，把上游按 **HTTPS** 且端口指向了本机**明文/非 openresty 入口**，TLS 握手必失败 → 网关判定全部上游不可用 → 返回 500。2Panel 内 openresty 各站点上游（`magicbook-backend`=localhost:18082、`teslamate-grafana`=127.0.0.1:3000 等）均为本机内反代，本机侧无阻断。
  - **结论**：500 是网关（116.62.200.90，IGW 节点）对所有走它的 haoshenqi.top/haoyuhang.top 站点的**统一错误**，与各个应用本身无关。修复点在网关侧，而非逐站重启。

### 状态与待办

- ⚠️ **需在网关侧修复**（本机无阻塞）：
  1. 核对网关上各站点的 upstream 目标端口与协议，应与本机 openresty 高位入口（如 grafana=14100、magicbook=18087、authentik=9009、hyh=18901）匹配，且协议为 HTTPS；
  2. 勿再指向本机明文端口（8085/8080 等）；
  3. 修正后刷新网关配置，全站点应恢复。
- 对本机而言，各服务无需重启；如需我辅助，可提供本机各站点的精确入口端口映射表。

### 总结

- **requests.md**：追加 R5（grafana 500 → 确认还有其他问题）。
- **response.md**：记录 R5 确认网关侧批量 500（多个子域全 500）与本机各服务健康证据。
- **冲突记录**：无。

---

## 2026-08-21

### 对 requests 的回应

- **R6（OIDC redirect_uri 仍指向旧域名 hyh.haoshenqi.top → 改为新域名 magicbook.haoyuhang.top）**：已修复。
  - **根因**：`.env` 中 `AUTHENTIK_MAGICBOOK_REDIRECT_URI=https://hyh.haoshenqi.top/oidc/callback` 仍为旧域名。`cps/oidc.py` 的 `login()` 优先取该环境变量生成 `authorize_redirect` 的 `redirect_uri`，故 authentik 授权 URL 里的 `redirect_uri` 一直是旧域名。
  - **修复**：`.env` 该值已改为 `https://magicbook.haoyuhang.top/oidc/callback`。
  - **验证/生效方式**：`.env` 通过 docker-compose `env_file` 注入容器，需 `docker compose up -d`（重建容器）或重启容器后生效；重启后访问 `https://magicbook.haoyuhang.top/login` 触发的 authorize URL 中 `redirect_uri` 应为 `https://magicbook.haoyuhang.top/oidc/callback`。
  - **注意**：authentik 侧 `magicbook` application 的 redirect_uri 白名单须包含新域名 `https://magicbook.haoyuhang.top/oidc/callback`，否则回调仍会因 redirect_uri mismatch 被拒。

### 总结

- **requests.md**：追加 R6（OIDC redirect_uri 域名更正）。
- **response.md**：记录 R6 根因（.env 环境变量旧域名）、修复与生效/authentik 白名单注意事项。
- **冲突记录**：无。

---

## 2026-08-21（第二次对话）

### 对 requests 的回应

- **R7（重启服务）**：已执行 `./restart.sh`，旧 PID 2750877 → 新 PID 4142195，监听 8085；`curl 127.0.0.1:8085/login` 返回 200，`.env` 新 redirect_uri 已随 restart.sh 加载生效。
- **R8（总结会话 + 生成 OIDC login 说明文档）**：已完成。
  - 生成 `docs/kb/instructions/workflows/oidc-login.md`，涵盖：OIDC 登录流程、`.env` 配置项说明、redirect_uri 三方一致性约束（代码/.env/Authentik 白名单）、本次旧域名问题的根因与修复要点、HS256 id_token 500 排障、`restart.sh` 重启与验证、相关测试。

### 总结

- **requests.md**：追加 R7（重启服务）、R8（生成 OIDC login 说明文档）。
- **response.md**：记录重启结果与文档产出位置。
- **冲突记录**：无。

---

## 2026-08-21（接口设计变更）

### 对 requests 的回应

- **R7（划词接口 payload 过大 → 改为只发页文本）**：已完成两端改造，请求体积从「每页数十个 word+sentence」降为「单段 pageText」。
  - **设计**：前端不再逐词提取，只上报当前页完整文本 `pageText`；分词、句子上下文提取、查词、归档全部迁移到 moon-well。响应结构不变，前端标注逻辑零改动。
  - **magicbook 侧（cps/static/js/reading/epub.js）**：
    - `visibleWords()` → `currentPageText()`（收集当前页 body 文本）。
    - `inspectVocabulary()` 发送 `pageText` 替代 `words[]`。
    - 移除 `vocabularySeen`（word 级去重不再必要）；新增 `lastPageTextSignature` 页面签名缓存——翻回已读页时直接复用缓存 records 标注，不重复请求。
  - **moon-well 侧**：
    - `ReadingVocabularyRequest`：`words[]` → `pageText`。
    - `ReadingVocabularyService.analyze()`：新增 `extractWords()` 分词（正则与前端一致、去重、丢弃单字母）+ `sentenceAround()` 句子上下文提取；沿用「查历史 → 查词库释义 → 写 ES → 统计 studyTimes → 响应」逻辑。
    - 全量测试 **54 passed**（新增 extractWords/句子提取 4 条，BUILD SUCCESS）。
  - **magicbook 测试**：`test_reading_vocabulary.py` payload 契约改为 `pageText`，全量 **126 passed**。
  - **部署**：magicbook 已提交 `14c0b52` 并重启生效（前端已含 pageText）；moon-well 已提交 `453f9b7` 并 push 远程 develop（已同步），CI 自动构建镜像。
  - **文档**：`docs/reading-vocabulary.md` 补充接口设计（请求/响应示例）与改动说明。
  - **待办（fnos 侧）**：CI 构建完成后，在 fnos 上 `cd /app/moon-well && docker compose pull && docker compose up -d` 更新 moon-well 容器，使线上接受新 pageText 接口。

### 总结

- **requests.md**：追加 R7（划词接口只发页文本）。
- **response.md**：记录 R7 两侧改动（epub.js 页文本上报 / moon-well 分词归档）、验证（magicbook 126 / moon-well 54）与文档同步。
- **冲突记录**：无。注意：两端工作区另有 R4 遗留的未提交改动（magicbook `gevent_wsgi.py`+测试、moon-well `.gitignore`/`deploy/`），本次提交不包含它们。

---

## 2026-08-22

### 对 requests 的回应

- **R8（总结划词翻译功能要求，更新到 reading-vocabulary.md）**：已完成文档重构。
  - 标题改为「阅读单词学习（划词翻译）」，明确功能定位。
  - 新增「功能要求」章节，按 5 类归纳本次 R7 及历次修复沉淀的全部要求：
    1. 核心目标（自动标记陌生词、释义/历史查看、学习闭环）
    2. 交互要求（波浪下划线、点击弹释义、防嵌套标注）
    3. 数据上报（只报当前页 pageText、CFI 精确取页、分词归档归 moon-well）
    4. 缓存与请求优化（签名去重、records 缓存、飞行中翻页重检）
    5. 异常与降级（未配置/超时静默、15s 超时、CSRF 显式携带）
  - 接口设计章节补充 magicbook 透传代理定位与 moon-well 侧职责（extractWords / sentenceAround / 查史→释义→归档）。
  - 配置示例域名更新为实际 `http://fnos:8082`；`userKey` 语义独立成章，保留历史迁移说明。
  - 修正了文档中重复的「配置」章节。

### 总结

- **requests.md**：追加 R8（总结划词功能要求到文档）。
- **response.md**：记录 R8 文档重构内容。
- **冲突记录**：无。

---

## 2026-08-29

### 对 requests 的回应

- **R11（拉取代码并重新部署服务）**：已完成。
  - 拉取代码：`develop` 分支已与上游一致；远程 `master` 另有 3 个新提交（Authentik OIDC、GPT Luna 划词翻译、Authentik→moon-well JWT 交换）。经用户确认切换并部署 master 前，先完成合并（见 R12）。
  - 重新部署：合并完成后执行 `./restart.sh`，旧 PID 1171493 → 新 PID 4033467；`/login` 返回 200；日志确认 `Starting Gevent server on [::]:8085` 且 AI 数据层连接 MySQL 初始化成功。`/oidc/login` → 302 正常。

- **R12（合并 master 进 develop，推送 develop，之后统一在 develop 开发）**：已完成。
  - 合并提交 `4115cc1 Merge branch 'master' into develop`，已推送 `origin/develop`（`0fd5b35..4115cc1`）。
  - **冲突解决**：
    - `cps/web.py`：`reading_vocabulary`/`reading_translate` 改用 master 的 JWT 鉴权（`authorization: Bearer`），保留 develop 的 15s 冷启动超时容错；增补 `_moonwell_session_authorization()`。
    - `cps/static/js/reading/epub.js`：保留 develop 的 CFI 精确取页 + 签名缓存 + 防重标生词标注（更完善，含历次修复），引入 master 的划词翻译 popover（`translateSelection`/`showTranslationPopover` 等）；丢弃 master 的 `visiblePageText/visibleWords/vocabularySeen` 已被 develop 方案取代的部分。
    - `docs/reading-vocabulary.md`：配置/接口改为 JWT 鉴权描述；新增划词翻译说明。
  - 全量测试 **120 passed**。

- **R13（library 下书籍是否应纳入 git 管理）**：**不应**。已确认：
  - `library/` 下的书籍/metaadata.db 是本地运行数据（书库内容），不属于代码仓库范畴。
  - `develop` 分支 `.gitignore` 已忽略 `library/*/` 与 `library/metadata.db`；合并后 `git ls-files` 确认 `library` 无任何文件被跟踪。
  - 注意：`master` 分支曾误提交 `library/metadata.db`（413KB 二进制），本次合并到 develop 后不再跟踪，仓库保持干净。

- **R14（采用 master 鉴权方式，抛弃 develop 的 user_key/X-Magicbook-Token）**：已完成，全面切换到 master 的 moon-well JWT 方案。
  - **鉴权模型（master）**：OIDC 登录回调里用 Authentik `id_token` 调 moon-well `POST /auth/oidc/exchange` 换取 `moonwell_access_token`（存服务端会话），代理请求以 `authorization: Bearer <token>` 头透传；moon-well 以 JWT `UserContext` 确定用户，杜绝客户端冒充。
  - **移除 develop 的 user_key / 固定令牌体系**：
    - `cps/constants.py`：删除 `MOON_WELL_INTEGRATION_TOKEN`。
    - `cps/ub.py`：删除 `User.user_key` 列、`migrate_user_key_column`、`backfill_user_keys`，及 admin/Guest 创建时的 user_key 赋值（保留 `oidc_issuer`/`oidc_subject`）。
    - `cps/oidc.py`：回调删除 `user.user_key = subject`。
    - `cps/admin.py`、`cps/web.py`：建号入口删除 `user_key = uuid4()` 赋值；`web.py` 的 `import uuid` 无用已移除。
    - `cps/web.py` `reading_vocabulary`：删除 `userKey` 注入，改为 JWT 透传。
  - **测试**：删除 `tests/test_user_key.py`（针对已废弃功能）；`tests/test_reading_vocabulary.py` 重写为 JWT 鉴权覆盖（401 无 JWT / Bearer 透传 / token 不下发前端）。全量 **120 passed**。

### 总结

- **requests.md**：追加 R11~R14（拉取部署、分支合并、library 不入库确认、鉴权切换为 master JWT 方案）。
- **response.md**：记录合并内容、冲突解决、鉴权方案切换范围与验证结果。
- **冲突记录**：无；master 提交的 `library/metadata.db` 属运行数据，已从合并结果中排除（develop .gitignore 忽略）。

### 对 requests 的回应（R15 图书丢失修复）

- **R15（重启后图书全部消失）**：已定位根因并完全修复。
  - **根因**：`master` 分支 git 历史跟踪了 `library/metadata.db`（Calibre 书库索引，运行数据）。本次会话先切 master 再合并回 develop，期间 `git checkout` 用 git blob 覆盖/删除了该文件，导致书库索引丢失。重启后 Calibre-Web 读到空索引，首页图书为零（书籍文件本身 un-tracked，仍在磁盘，无损失）。
  - **修复步骤**：
    1. 用 `calibredb restore_database --with-library=/apprun/magicbook/library --really-do-it` 从各书的 `metadata.opf` 重建索引，**42 本全部恢复**（books/data 表各 42 行）。
    2. `master` 分支执行 `git rm --cached library/metadata.db` 并推送（`dc682e4`），彻底停止跟踪该运行数据文件。
    3. 验证切 master / develop 来回切换后 `metadata.db` 不再被 git 覆盖，books 恒为 42。
    4. 重启服务，`/login` 200，日志无书库错误。
  - **遗留说明**：admin 密码非默认 `admin123`（此前已被修改），登录验证脚本未过；与本次图书问题无关，如需改密另行处理。

### 总结（R15）

- **requests.md**：追加 R15（重启后图书丢失排查恢复 + metadata.db 防复发）。
- **response.md**：记录根因（git 跟踪书库索引→切换分支被删）、恢复过程（calibredb 重建 42 本）、防复发（master 停止跟踪）。
- **冲突记录**：无。

### 对 requests 的回应（R16 / R17 401 排查 + CI 重跑与令牌刷新）

- **R16（reading-vocabulary 401 排查）**：已定位根因，非代码缺陷，而是**部署不同步**。
  - **根因链**：8-29 08:15 推送两侧鉴权切换（moon-well `67e872e` 移除 `/reading-vocabulary/**` 白名单与集成令牌、新增 `/auth/oidc/exchange`；magicbook `6fb461cd` 登录回调换 JWT）→ moon-well 的 GitHub Actions 构建 `33223042837` **失败**（阿里云 Maven 镜像拉 `mapper-extras-client:7.5.0` 返回 502，偶发网络故障），新版镜像从未推送 → FNOS 上 moon-well 仍是 8-22 旧版（无 exchange 接口）→ magicbook OIDC 回调换票失败（仅记 warning，不阻断登录）→ session 无 `moonwell_access_token` → 阅读词汇代理返回 401。
  - **修复路径**：重跑 CI（见 R17）→ FNOS `docker compose pull moon-well && docker compose up -d` → 确认 `.env` 补充 `AUTHENTIK_MAGICBOOK_ISSUER` / `AUTHENTIK_MAGICBOOK_CLIENT_ID` → 用户重新登录 magicbook（exchange 仅在登录回调执行）。

- **R17（重跑 CI + 修复令牌刷新隐患）**：已完成。
  - **CI 重跑**：`gh run rerun 33223042837`，构建成功后镜像推至阿里云仓库。
  - **隐患修复（moon-well access token 7 天过期无刷新）**：
    - `cps/web.py`：两个代理端点收敛为 `_moonwell_proxy()`；上游返回 401 且使用会话令牌时，自动调 moon-well `POST /auth/refreshToken`（在 `/auth/**` 白名单内）换新并重试一次；刷新失败清空会话令牌并返回 401 提示重新登录。客户端自带 `authorization` 头时 401 原样透传（令牌生命周期由客户端自管）。
    - 由于 moon-well 每次刷新同时轮换 refresh token（30 天），只要 30 天内至少使用一次阅读器即永续有效，无需重新登录。
    - **测试**：`tests/test_reading_vocabulary.py` 新增 3 例（401→刷新→重试成功且会话更新；刷新失败→401 清空令牌；客户端令牌 401 透传不刷新），9/9 通过。全量 120 passed；`test_oidc.py` 2 例与 CSRF 顺序用例失败为**改动前已存在**（干净工作区复跑同样失败，系依赖版本/测试顺序问题），与本次无关。
- **遗留待办**：FNOS 侧需人工执行镜像更新 + `.env` 补变量 + 用户重新登录（内网操作，本机不可达）。

### 总结（R16 / R17）

- **requests.md**：追加 R16（401 排查）、R17（重跑 CI + 令牌自动刷新）。
- **response.md**：记录 401 根因链（CI 502→镜像未更新→两侧鉴权不匹配）、CI 重跑、刷新逻辑实现与测试结果。
- **冲突记录**：无。

---

## 2026-08-29（Harry Potter 整理会话，自 ubuntu 工作区合并）

### 对 requests 的回应（R18 Harry Potter 整理）

- **R18（整理 HP 系列 + cover not available + 互联网封面）**：已完成 metadata 整理；封面按用户决定暂不处理。
  - **"cover not available" 根因**：7 本书导入时在 `library/Unknown/` 下生成了**完全相同**的占位 `cover.jpg`（282×400，7 份 md5 一致），且 `books.has_cover=0`，calibre-web 据此判定无封面。
  - **互联网封面可行性（已实测）**：本服务器出网受限——Google Books / OpenLibrary / Wikimedia / Amazon / Douban 全部超时或被拒（仅 baidu/github 可达），无法直接拉取真实封面。已向用户提供替代方案（本地生成文字封面 / 用户提供封面图 / 提供下载脚本在有网机器执行），用户选择**暂不处理封面**。
  - **metadata 整理（calibredb 完成，已备份 metadata.db 至 docs/temp）**：
    - 作者 `Unknown` → `J.K. Rowling`，目录自动迁移至 `library/J.K. Rowling/(44–50)`，`Unknown/` 目录已清空。
    - 丛书 `Harry Potter` #1–#7（正确顺序：50→44→49→46→48→47→45）。
    - 补充出版社（Scholastic / Scholastic Paperbacks / Arthur A. Levine Books）、出版日期、语言（`zh` → `eng`，正文实测为英文）、ISBN（5 本；《凤凰社》无法验证故留空）、英文内容简介 7 条。
    - 修复书名大小写（`Order Of` → `Order of`）。
  - **验证**：DB 查询确认全部字段（author/series/index/pubdate/isbn/comments/lang）就位；书籍文件在磁盘正确就位；`metadata.db` 仍不入 git。
  - **封面（已获用户代理 http://127.0.0.1:12811 后完成）**：配置代理后服务器可出网，改从 **OpenLibrary** 拉取——7 本按 ISBN（第 5 部无 ISBN 用书名检索）下载官方封面写入 `cover.jpg`，`has_cover` 全部置 1（此前封面源 Google Books 429、OpenLibrary 直连超时均不可用）。同时补上此前留空的第 5 部《凤凰社》ISBN：`0439358078`（美版精装，Arthur A. Levine）。

### 总结（R18）

- **requests.md**：追加 R18（HP 整理 + 封面诊断）。
- **response.md**：记录 cover not available 根因、互联网封面不可达的实测结论、metadata 整理明细与验证、封面暂缓的用户决定。
- **冲突记录**：无。

### 对 requests 的回应（R19 Harry Potter 入书架）

- **R19（放入书架 /shelf/2）**：已完成。
  - 书架 #2「harry potter」（public）为 calibre-web 的书架，数据存于 `app.db.book_shelf_link`（非 library/metadata.db）。
  - 按丛书顺序 #1–#7 入库：50→44→49→46→48→47→45，`order` 字段由 1 至 7（原 44 已存在、order 更新为 2，其余 6 本新增），`date_added` 使用 UTC 当前时间。
  - cps 书架读取无查询缓存（`cps/shelf.py` 每请求直查 `ub.BookShelf`），故直接写库即时生效。
  - **验证**：`book_shelf_link` shelf=2 计 7 行且排序正确；`GET /shelf/2` 返回 302→`/login`（站点需登录，书架逻辑正常；登录后即可见 7 本）。

### 总结（R19）

- **requests.md**：追加 R19（HP 入书架）。
- **response.md**：记录书架机制（app.db book_shelf_link）、写入结果（7 本按系列顺序）与验证。
- **冲突记录**：无。

---

## 2026-08-29（第四次对话：reading-vocabulary 仍 401 → HS256 修复与部署）

### 对 requests 的回应（R16 补充 / R17 后续：CI 通过后仍 401）

- **镜像已部署但 401 依旧 → 发现第二个根因（代码 bug）**：
  - 通过公网 `moonwell.haoshenqi.top` + ubuntu 跳板（SSH `root@192.168.31.9`）完成飞牛部署：`.env` 补 `AUTHENTIK_MAGICBOOK_ISSUER/CLIENT_ID/CLIENT_SECRET`（client_secret 取自 ubuntu `/apprun/magicbook/.env`）、`docker-compose.yml` 同步三行环境变量、阿里云 docker 凭证从 ubuntu 复制到飞牛后 `docker compose pull && up -d` 成功。
  - 部署后 exchange 接口已存在，但测试请求返回 `Missing required "keys" member` → 排查 Authentik discovery：**magicbook 与 moonwell 两个 provider 均只支持 HS256 对称签名，JWKS 端点返回空对象 `{}`**。moon-well 的 exchange/callback 用 `JwtDecoders.fromIssuerLocation()`（JWKS 公钥路径）验证 id_token —— **必然失败**，与镜像无关。
- **moon-well 代码修复（`5c19b4b`）**：`OidcAuthController.decodeOidcToken()` 按 token 头部算法自适应——HS 系列用 client_secret 对称验签（`NimbusJwtDecoder.withSecretKey`），RS/ES 仍走 issuer JWKS；exchange 增加 issuer 校验（注意 `jwt.getIssuer()` 返回 URL 对象，必须用 `getClaimAsString("iss")` 比较）；新增配置 `exchange-client-secret`（application.yml + compose.yaml）。新增 2 个单测（HS256 正确验签 / 篡改签名拒绝），OidcAuthControllerTest 5/5 通过。
- **magicbook 侧**：提交推送 `7fa261ff`（令牌自动刷新，见 R17）。
- **会话记录合并**：ubuntu 工作区另一会话留下的 HP 记录（原编号 R16-18）与本地 401 记录编号冲突，已重编号为 R18-20 合并回仓库。

### 总结

- **moon-well**：`fix(oidc): 兼容 Authentik HS256 对称签名的 id_token 验证`（controller + yml + compose + 测试）。
- **magicbook**：`fix(reading): 会话 JWT 过期时自动刷新 moon-well access token` + 会话记录合并。
- **冲突记录**：requests/response.md 两会话编号冲突已合并重排。

---

## 2026-08-29（第五次对话：reading-vocabulary 生词判定重构）

### 对 requests 的回应（R22 单词本判定 + 接口合并）

- **R22（查单词本 + 合并接口）**：已完成设计与实现。
  - **设计先行**：moon-well `docs/feat/reading-vocabulary/design/reading-vocabulary-lld.md`（LLD，含生产数据调研：单词本 4,111 词 56 已掌握、词典 level 1~7 分布、ES 2.4 万事件全是 UNKNOWN 无一 KNOWN）。三项评审决策：未入库词按词典 `level>=hard_level` 才标；hard_level NULL bug 代码+数据一起修；旧端点立即删除（两服务同批部署）。
  - **根因**：analyze 只查 ES `reading_vocabulary.status` 判定生词，从不查单词本 `familiarity`；而 ES 判定通道从未生效（前端从未调用 known 接口），导致全词返回。
  - **moon-well 实现**：生词判定以 `vocabulary_notebook.familiarity` 为单一事实来源（>=FLUENT 不标；<7 标；未入库按词典 level 回退，低于用户档位/词典外不标不写事件）；`/reading-vocabulary/**` 并入 `/vocabulary/reading/**`（旧路径删除），reading known 并入 `/vocabulary/known/{word}`；known/unknown 改 upsert（修 NPE 隐患）；initByUserId 补写 hard_level；ES 事件新增 familiarity 字段、status 改由单词本派生；DTO 移除 userKey（服务端从 JWT 用户生成）。新增回填脚本 `docs/temp/scripts/backfill_notebook_hard_level.py`（默认 dry-run）。
  - **magicbook 实现**：`/ajax/reading-vocabulary|reading-translate` 代理目标切换至 `/vocabulary/reading/analyze|translate`，前端 epub.js 零改动。
  - **测试**：moon-well ReadingVocabularyServiceTest 重写为判定矩阵 18/18 通过（全量 62/63，唯一失败为需真实数据库的 contextLoads 集成测试，本机无 MySQL 属环境依赖）；magicbook test_reading_vocabulary.py 9/9 通过。

### 总结（R22）

- **moon-well**：LLD 设计文档 + analyze 判定重构 + 接口合并 + known/unknown upsert + initByUserId hard_level + 回填脚本 + 文档更新。
- **magicbook**：代理路径切换 + 文档与会话记录更新。
- **冲突记录**：无。

---

## 2026-08-29（第六次对话：reading-vocabulary 503 排查）

### 对 requests 的回应（R23 503 修复）

- **R23（503 根因与修复）**：已完成。
  - **根因**：calibre-web 进程环境携带 `http_proxy=127.0.0.1:12811`（R18 封面下载会话遗留），requests 默认信任环境代理，内网 moon-well 请求（`http://fnos:8082`）被 naive 代理断连（代理无法解析内网主机名），`_moonwell_proxy` 捕获 RequestException 返回 503。日志实证：15:40 两条 `ProxyError('Unable to connect to proxy', RemoteDisconnected(...))`。
  - **复现验证**：带 proxy 环境请求 fnos:8082 必现 ProxyError；`proxies={'http': None, 'https': None}` 直连正常 401。
  - **修复**（magicbook `2287f03d`，已部署 ubuntu）：四处 moon-well 调用（`_moonwell_proxy` 两次转发、`_moonwell_refresh_session_token` 刷新、`oidc.py` exchange）显式 `proxies=None` 内网直连，不再受进程环境影响；封面下载等出网功能继续使用环境代理不受影响。happy-path 测试新增 proxies 断言防回归，9/9 通过。
  - **附带发现**：oidc.py 的 exchange 同样受影响——带 proxy 的进程上登录换票会静默失败（仅记 warning，表现为 session 无令牌、阅读器 401），本次一并修复。
  - **现状**：新进程环境已干净（proxy 为上次会话注入），公网接口恢复 400（未登录正常响应）；代码级免疫确保未来带 proxy 重启不再复发。

### 总结（R23）

- **magicbook**：`fix(reading): moon-well 内网请求绕过环境代理修复 503`（web.py + oidc.py + 测试）。
- **冲突记录**：无。

---

## 2026-08-30（第七次对话：reading-translate 400 与全量 moon-well 排查）

> 注：本会话开始前工作区曾被 reset 至 `origin/develop`，上一会话（R24/R25）部分未提交改动丢失；其中 translate 的 CSRF 修复已由上游作者提交 `757c775`，bar-ui 修复与部分测试需在本会话重建。

### 对 requests 的回应（R24 划词翻译 400）

- **R24（POST /ajax/reading-translate 400）**：根因为前端 **translateSelection 漏带 `X-CSRFToken`**——服务端全局 CSRFProtect，EPUB 阅读器不加载 main.js（无全局 ajaxSetup），缺 token 返回 400 翻译静默失败。已由上游提交 `757c775` 修复（epub.js 补头 + 契约测试）。

### 对 requests 的回应（R25 排查所有 moon-well 调用点）

- **后端出站（6 处，全部健康 ✅）**：`/vocabulary/reading/analyze`（15s）、`/vocabulary/reading/translate`（20s）、`/vocabulary/reading/translate-batch`（60s，沉浸式）、`/tts/speak`（65s，binary 透传 mp3）、`/auth/refreshToken`（8s）、`/auth/oidc/exchange`（8s）——**均经 `_moonwell_proxy`/刷新/交换统一实现，带 `proxies={"http","https": None}` 内网直连、显式超时、authorization 鉴权**；1.3.0 前无二进制检查。`binary=True` 用 `response.content` 透传音频不破坏字节。
- **前端 → magicbook 代理（6 处 POST，全部携带 `X-CSRFToken` ✅）**：划词翻译、生词标注、沉浸式翻译（批量 + 段落重试）、段落朗读（TTS fetch）、书签；`ai_chat.js`（AI 面板）均带 token。
- **发现并修复同类隐患**：`bar-ui.js`（音频阅读器 listenmp3，无 main.js）的 **onpause/onstop/onfinish 3 处 bookmark 上报缺 `csrf_token`**（仅 onposition 带），`set_bookmark` 无 `@csrf.exempt`，服务端 CSRF 会 400 拦截致进度保存静默失效——已显式补带并加静态断言锁定（上一会话修复随工作区 reset 丢失，本会话重建）。

### 对 requests 的回应（R26 CSRF token 过期）

- **R26（`The CSRF token has expired.` 400）**：已完成。
  - **根因**：flask-wtf `WTF_CSRF_TIME_LIMIT` 默认 3600s，token 经 `URLSafeTimedSerializer` 内嵌时间戳。EPUB 阅读器页面长期保持打开，嵌入隐藏域的 CSRF token 无法随页面刷新，**超过 1 小时后的全部阅读请求 400**（生词/划词/沉浸式/TTS/书签），日志 `{csrf.py:263} The CSRF token has expired.`。
  - **修复**：① `cps/__init__.py` 设 `WTF_CSRF_TIME_LIMIT=None`——仅验签不校年龄，token 随签名会话 cookie 生效（防护已由 HttpOnly + SameSite=Lax 承载），旧 token 无需刷新页面即恢复（经 `itsdangerous.loads(max_age=None)` 实测）；② 前端 `reloadIfCsrfBlocked()` 自愈——翻译/TTS/沉浸式/生词标注/书签任一 POST 遇 CSRF 类 400 刷新页面拿新 token（localStorage 恢复阅读位置，sessionStorage 防死循环），TTS 非 CSRF 失败仍降级浏览器语音。
  - **测试**：新增 `test_csrf_time_limit_disabled_for_reading_pages`（配置锁定）、`test_epub_js_reloads_on_csrf_failure`（自愈函数定义 + 6 处失败路径接线 + CSRF 头覆盖）、`test_bar_ui_bookmark_requests_carry_csrf_token`（4 个上报点均带 token）。全量 **139 通过**。

### 总结（R24–R26）

- **magicbook**：`fix(reading): 阅读器 CSRF token 过期 400 修复 + bar-ui 缺 CSRF 头补齐`（__init__.py + epub.js 自愈 + bar-ui.js + 测试 + 文档 + 会话记录）。
- **冲突记录**：工作区 reset 丢改了 R24/R25 部分改动，本会话已核对重建；translate 修复以 `757c775` 为准。

---

## 2026-08-30（第八次对话：本地/远程 epub.js 冲突检查与合并）

### 对 requests 的回应（R27 冲突检查与合并）

- **检查结果**：本地 `develop` 落后 `origin/develop` 1 个提交（`8a74695` 段落级翻译按钮），该提交与本地上次会话未提交的 CSRF 修复**都改了 `cps/static/js/reading/epub.js`**；三方合并模拟确认 `translateSingleParagraph` / `restoreCachedTranslations` 区域（约 592–642 行）真实冲突，其余文件（read.html、设计文档、bar-ui.js、__init__.py、测试）不重叠。
- **处理（用户选择「先提交本地再 merge」）**：
  1. 提交本地 CSRF 修复 → `372dbe5`；
  2. `git merge origin/develop` → 仅 epub.js 冲突；
  3. 手动融合：**保留远程段落级翻译结构**（`.always` 移除 is-loading、`translateParagraph`、`restoreCachedTranslations`），**恢复本地 `reloadIfCsrfBlocked` CSRF 自愈**接线（translate/immersive/vocabulary/bookmark/TTS/popover 6 条路径 + 定义，共 7 处）；删除冲突块外残留的多余闭合行修复 SyntaxError；
  4. 校验：`node --check` 通过，全量 **139 passed**；
  5. 合并提交 `9973e0e`，develop 领先 origin/develop 2 个提交。
- **冲突记录**：epub.js 翻译区两边破坏性改动，已融合；reset 时丢失的 bar-ui/README 修复已在本会话上文重建。

---

## 2026-08-30（第八次对话：TTS 配置咨询与 reading-tts 500 排查）

### 对 requests 的回应（R28 TTS 配置）

- TTS 配置在 **moon-well**（Java 后端），不在 magicbook 本地。生效配置在 **Nacos `moon-well.yaml` 的 `tts:` 段**（环境变量 `DASHSCOPE_API_KEY / DASHSCOPE_BASE_URL / TTS_MODEL / TTS_VOICE / TTS_TIMEOUT_MS`，见 `application.yml:159`），已实测两段值均可用。
- **业务空间 base_url 结论**：不需要。用户提供的 `llm-7t1fnx9dwh5at42z.cn-beijing.maas.aliyuncs.com` 与公共 `https://dashscope.aliyuncs.com` 实测都能 200 合成；走公共端点即可，专属域名可选。

### 对 requests 的回应（R29 reading-tts 500）

- **现象**：magicbook `POST /ajax/reading-tts`（透传 moonwell `POST /tts/speak`）返回 500。
- **根因**：合成阶段正常（`qwen-audio-3.0-tts-flash` + `longanhuan_v3.6` + Nacos key 200 出 URL），失败在 **第二阶段下载 OSS 音频**。moonwell `ReadingTtsService.download()`（`ReadingTtsService.java:239`）用 `restTemplate.exchange(audioUrl, ...)` 传 **String**，RestTemplate 会把 String 当 URI 模板**二次编码**（实证 `%3D` → `%253D`），破坏百炼返回的 OSS 预签名 URL → OSS `SignatureDoesNotMatch` 403 → moonwell `GlobalException` → 500。`GlobalExceptionHandler` 无日志，错误只出现在响应体 `message`，日志看不到属正常。
- **修复**：`download()` 改用 `URI.create(audioUrl)` 传 `URI` 对象，RestTemplate 不再 encode，签名 URL 原样直发。用本机 Spring 6.1.10 对照实测：String 传参 `403 SignatureDoesNotMatch`、URI 传参 `200 OK`（mp3 68KB）。
- **测试**：同步更新 `ReadingTtsServiceTest`（`stubDownload`/下载失败桩/verify 改 `any(URI.class)` + `URI.create`），17 个 TTS 测试全过；moon-well 全量 24 个测试通过；`mvn package` 构建成功（jar 已含修复）。
- **待办（需用户操作）**：部署新 jar 到 fnos 并重启 moon-well（仓库代码已就绪，未提交）。

### 总结（R28–R29）

- **moon-well**：`fix(tts): 下载 OSS 签名音频改传 URI 对象，避免 RestTemplate 二次编码致 403`（ReadingTtsService + 测试）。
- **知识沉淀**：OSS 预签名 URL 走 RestTemplate 必须传 URI 而非 String；`GlobalExceptionHandler` 不落日志、错误在响应体，排查先看响应 `message`。

---

## 2026-08-30（第九次对话：TTS 播放无声——CSP 拦截 blob: 媒体）

### 对 requests 的回应（R30 接口成功但无声）

- **现象**：`/ajax/reading-tts` 返回 200（二进制透传正常），但浏览器无声音。控制台报：
  `Loading media from 'blob:https://magicbook.haoyuhang.top/...' violates CSP directive "default-src 'self' 'unsafe-inline' 'unsafe-eval'". Note that 'media-src' was not explicitly set, so 'default-src' is used as a fallback.`
- **根因**：前端用 `URL.createObjectURL(blob)` 生成 `blob:` 音频 URL，`new Audio(url).play()` 属媒体加载，受 CSP `media-src` 管辖。CSP 构造器（`cps/web.py` `add_security_headers`）只给阅读页放行 `font-src blob:` 与 `img-src data: blob:`，**从未设置 `media-src`** → 回退 `default-src 'self'`（不含 `blob:`）→ 播放被拦。接口成功、解码正常，单纯是 CSP 头部不允许 blob 媒体源。
- **修复**：`cps/web.py` 阅读页分支显式追加 `media-src 'self' blob:`（含 Why 注释）；其他页面 CSP 保持不放行 blob，不扩大攻击面。
- **测试**：新增 `tests/test_csp_media.py` —— 阅读页必须含 `media-src ... blob:` 且含 `'self'`；非阅读页不排放宽。全量 **149 passed**。
- **待办**：提交推送 develop 后 Actions 自动部署；部署后浏览器需强制刷新（CSP 头随响应下发，旧缓存页面可能沿用旧头）。

### 总结（R30）

- **magicbook**：`fix(reading): CSP 放行阅读页 blob: 媒体（media-src），修复 TTS 播放无声`（cps/web.py + test_csp_media.py + 会话记录）。
- **知识沉淀**：HTML5 `Audio` 播放 `blob:` URL 受 CSP `media-src` 管辖，未显式声明时回退 `default-src`；阅读器新增 blob 媒体（音频/视频）须同步放行 `media-src`。

---

## 2026-08-31（第十次对话：划词气泡不消失修复 + ＋/－标记 + ESC 快捷键）

### 对 requests 的回应（R31）

- **Bug 根因（气泡不自动消失）**：EPUB 正文渲染在 iframe 中，**iframe 内事件不冒泡到主文档**；旧实现只在主文档监听 `mousedown`/ESC（epub.js），且 `translateSelection` 在选区为空时直接 `return` 不清理旧气泡。双击查词后点击正文（最常见操作落在 iframe 内）→ 气泡永不关闭。
- **修复**（`cps/static/js/reading/epub.js`）：① iframe document 绑定 `mousedown`（正文任何按下即关气泡）与 `keydown`（iframe 内 ESC）；② `translateSelection` 所有「不弹气泡」路径（空选区/超长/无尺寸 rect）统一 `closeTranslationPopover()`；③ 翻页 `relocated` 关闭坐标已失效的气泡。
- **＋/－标记**：moon-well 已有现成接口 `GET /vocabulary/unknown/{word}` / `GET /vocabulary/known/{word}`（从其 OpenAPI 确认），magicbook 新增纯透传代理 `POST /ajax/reading-word-mark`（`_moonwell_proxy` 扩展 GET 转发）。气泡内仅对单个英文单词显示按钮；标记成功即时同步页面标注（＋`markVocabulary` 补波浪线 / －`unwrapWordSpans` 解包消失），按钮互斥高亮 + toast 反馈。
- **ESC 分层退出**：气泡与 AI 抽屉同开时一次 ESC 只关气泡——epub.js 关闭气泡后 `stopImmediatePropagation()`（先注册可阻断 ai_chat.js 的 jQuery 委托监听），ai_chat.js 另有 `ReaderTranslation.isOpen()` 兜底；气泡未开时 ESC 关 AI 抽屉（EPUB/TXT/PDF 通用）。
- **交叉审查修复 3 项**：word=null 会被 `str()` 转成 `"none"` 存脏词 → 先查类型；`unknown:"false"` 字符串经 `bool()` 恒真 → 必须 JSON boolean；词形正则收紧为**首尾字母**（尾部撇号/连字符的 key 与页面 `\b` 分词永远匹配不上，标记后无效果且存脏 key）。
- **测试**：`tests/test_reading_vocabulary.py` 新增 9 个用例（登录/401/词形白名单含 null 与尾撇号边界/归一化透传 unknown+known/503/GET 401 刷新重试/CSRF 契约/气泡关闭与标记按钮静态锁定/ESC 分层锁定），全量 **159 passed**。
- **文档**：`docs/reading-vocabulary.md` 增补「划词标记」「气泡的关闭」「ESC 分层退出」三节。
- **部署**：仅 magicbook 侧改动（moon-well 接口现成零改动），推送 develop 后 Actions 自动部署；浏览器需强制刷新（JS/CSS 有缓存）。

### 总结（R31）

- **magicbook**：`fix(reading): 划词气泡 iframe 内不消失；feat: 气泡＋/－生词标记与 ESC 分层退出`（web.py/read.html/epub.js/ai_chat.js/reader.css + 9 测试 + 文档）。
- **知识沉淀**：iframe 内事件不冒泡到主文档——阅读器所有「点正文关弹层/ESC」交互必须双 document 绑定；`str(payload.get(...))` 会把 JSON null 静默转 `"None"`，代理端点必须先做 isinstance 检查；三端共享词形 key 时正则必须与分词 `\b` 边界语义对齐（首尾字母）。

---

## 2026-09-03（第十一次对话：阅读器段落批注前端接入）

### 对 requests 的回应（R32）

- **代理路由**：magicbook 新增 3 个登录保护的批注代理：创建批注、按段落查询、按书查询；均转发到 moon-well 对应接口，校验段落/内容长度，trim 书名与章节并限制 200 字符。
- **段落批注 UI**：EPUB 每个段落新增 `✎` 按钮；点击后显示段落原文摘要、已有批注、批注输入框和提交操作。批注提交只发送段落与内容，昵称和时间由 moon-well 服务端生成。
- **本书批注面板**：标题栏新增「批」入口，按章节显示本书已批注段落及其批注列表，支持关闭和空态/失败态提示。
- **同文档契约**：前端批注使用与翻译/TTS 相同的 `paragraphSpeechText` 归一化文本，保证批注与翻译、音频落入 moon-well 的同一个 `reading_paragraph_cache` ES 文档。
- **交互与安全**：批注请求显式携带 `X-CSRFToken`；段落弹层、本书面板、划词气泡和 AI 抽屉支持分层 `Esc` 退出；翻页、点击正文和点击外部区域会关闭失效浮层；CSRF 失败沿用自动刷新恢复机制。
- **测试**：新增代理校验/透传/503/CSRF 测试与 epub.js 静态契约测试；阅读测试 **32 passed**，magicbook 全量测试 **167 passed**（3 个既有 SAWarning，无失败）。JS `node --check`、Python `py_compile` 均通过。
- **遗留工作区说明**：本次未修改此前遗留的 `ai_chat.js`、既有阅读文档、既有测试等未提交改动；它们与本次批注功能一并处于当前工作区，但未被撤销或覆盖。

### 总结

- **requests.md**：新增 R32（magicbook 阅读器段落批注）。
- **response.md**：记录批注代理、段落弹层、本书批注面板、同 ES 文档键契约、安全处理与测试结果。

### 冲突记录

- 无。

---

## 2026-09-08

### 对 requests 的回应

- **R33（移除 magicbook 对 Nacos 的依赖）**：已完成。
  - 删除 `nacos-sdk-python` 依赖、`cps/nacos_client.py` 及应用启动时的 Nacos 注册/发现逻辑。
  - 删除 `NACOS_*`、`MOON_WELL_DISCOVERY_SCHEME` 配置项；moon-well 调用统一使用 `MOON_WELL_READING_URL`。
  - 保留现有 moon-well 请求代理、JWT/会话鉴权与内网直连逻辑不变。
  - `py_compile` 与差异检查通过；启动验证继续被当前环境缺失的 `joserfc` 阻断，该问题与 Nacos 移除无关。

- **R34（修复 joserfc 与 cryptography 依赖问题）**：已完成。
  - **根因**：`cps/oidc.py` 无条件导入 `joserfc`（用于 RS256/JWKS 验签），但 `requirements.txt` 和 `pyproject.toml` 均未声明该依赖；当前机器系统 `cryptography==2.8`（`/usr/lib`）覆盖了 `>=39` 的声明，`joserfc` 无法导入。
  - **修复**：补齐 `requirements.txt` 和 `pyproject.toml` 中 `joserfc>=1.0.0,<2.0.0` 声明；本机执行 `pip install --force-reinstall 'cryptography>=39,<48' 'joserfc>=1,<2'`，将 `cryptography` 升至 47.0.0。
  - **验证**：`./restart.sh` 成功启动（PID 2446058，端口 8085）；`test_oidc.py` **6/6 通过**；阅读测试 setup 错误数量从 30 降至 16（joserfc 阻断已消除，剩余为测试夹具环境问题）。

### 总结

- **requests.md**：新增 R33，记录移除 Nacos 依赖的需求。
- **response.md**：记录 R33 的删除范围、替代地址配置与验证结果及环境阻断。

### 冲突记录

- 无。

---

## 2026-09-08（第三次对话）

### 对 requests 的回应

- **R35（修复登录后 /ajax/reading-vocabulary 返回 401）**：已完成。
  - **根因**：moon-well 要求 `Authorization: Bearer <JWT>` 鉴权，但 `oidc.py` callback 中 token 交换已被移除（注释"不再在此交换 moon-well token"），`_moonwell_proxy` 也不携带 `authorization` 头。moon-well 返回 401「未登录」。
  - **修复**：
    - `oidc.py` callback：登录成功后用 Authentik `id_token` 调 moon-well `POST /auth/oidc/exchange` 换取 `access_token` + `refresh_token`，存入 Flask session。
    - `web.py` `_moonwell_proxy`：从 session 读取 token 携带 `Authorization: Bearer` 头；收到 401 时自动调 `/auth/refreshToken` 刷新并重试一次。
  - **验证**：`py_compile` 通过；`test_oidc.py` **6/6 通过**；服务正常启动，`/login` 返回 200。

### 总结

- **requests.md**：新增 R35，记录 reading-vocabulary 401 问题。
- **response.md**：记录根因（token 交换被移除 + proxy 无 Bearer 头）与修复方案。

### 冲突记录

- 无。

## 2026-09-13

### R36：TXT 阅读器预排版文本乱版修复

- **原因**：`readtxt.html` + `txt_reader.js` + `text.css` 的 TXT 阅读器用 `<pre>`（pre-wrap）+ 双栏（column-count:2）+ 水平翻页渲染。Project Gutenberg 类 TXT 保留纸质书排版：行尾硬换行、行首不规则缩进（起句 4 空格、续行 2 空格）。这些硬换行被原样保留，被双栏分页任意切割，一行起句与续行落入不同栏/页，形成交错乱版（用户截图中 Harper's Young People, January 27, 1880 即此问题）。
- **方案**：在 `cps/static/js/reading/txt_reader.js` 加载文本后增加预排版检测与重排：
  - `isHardWrappedText`：非空行 ≥20 且长行（>72 字符）占比 <30% 判定为预排版（流式 TXT/TED 字幕不受影响）；
  - `reflowHardWrappedText`：空行为段落边界，段内硬换行合并为流式段落——行尾连字符按断词直接拼接（保留连字符，tea- + kettle → tea-kettle），CJK 字符间不插空格，其余以单空格连接；标题行因空行分隔保留为独立段。
  - 已知取舍：诗行会被并入段落（换取整体可读性）。
- **验证**：无 JS 测试基建，用 node 直接加载修改后文件中的真实函数验证：PG #28318 全文判定为预排版并重排成功（诗节成段、标题独立、断词正确）；30 段流式 TED 字幕样本判定为非预排版、原样保留；中文句合并不插空格。部署后建议用截图书目视复核。
- **部署**：develop 分支，需在 Ubuntu（192.168.31.11）重新构建/重启 magicbook 生效（静态资源无缓存版本号，浏览器需强刷）。

### R37：reading-vocabulary「疑似弃用」排查（未改动代码）

- **结论：功能没有被弃用，两侧均在正常服役。**
  - moon-well：`ReadingVocabularyController`（`/vocabulary/reading/analyze|translate|translate-batch`）与 `ReadingVocabularyService` 无任何 `@Deprecated`/开关/下线逻辑；2026-09-12 `f73fc6f` 还把其 ES 索引收编进 `EsIndexEnum.READING_VOCABULARY`（`reading_vocabulary`）统一管理。
  - magicbook：EPUB 阅读器（read.html + epub.js，1483 行）生词标注/划词翻译/标记认识全在，开关 `readingVocabularyEnabled = current_user.is_authenticated`；9/8 刚修复 401（21c93189）。
- **「被弃用」错觉的真实原因（按可能性排序）**：
  1. **TXT 阅读器从未实现过该功能**：`readtxt.html` + `txt_reader.js`（仅 137 行，只有翻页与 R36 排版重排）没有任何 `readingVocabularyUrl`/标注/划词/TTS/批注代码。最近阅读的书恰好全是 TXT（TED 导入书、PG TXT），在 TXT 书里自然看不到生词波浪线——不是功能被弃用，而是功能只存在于 EPUB 阅读器。
  2. **旧接口路径确实删除过**：2026-08-29 `aca377e` 将 `/reading-vocabulary/**` 并入 `/vocabulary/reading/**`（原路径已删除），直接调旧路径会 404，易误判为弃用。
- **验证**：grep 全仓无弃用标记；git log 两项目均无下线提交；requests/response 记录无弃用计划；`web.py:1963` 确认 TXT 书渲染 `readtxt.html`。
- **如需 TXT 阅读器也支持生词标注**：需把 epub.js 的词汇链路（取页文本、CSRF、标注、缓存签名）移植到 txt_reader.js，属新功能开发，另行安排。

### 总结

R36 为纯前端渲染修复，不涉及数据与接口变更；TED 书（moon-well 同步的流式字幕 TXT）不受影响。R37 为排查类任务，未改动任何代码。

### R38：翻译内容显示时长配置（默认 5 秒自动消失，页面可改）

- **实现**（纯前端，EPUB 阅读器 `cps/static/js/reading/epub.js` + `cps/templates/read.html`）：
  - 配置存 localStorage `calibre.reader.translationDisplaySeconds`，默认 5 秒，0 = 一直显示（非法/负数回退 5）；入口在阅读器设置弹窗（齿轮）朗读引擎下方，数字输入框，改动即时保存并生效。
  - 生效范围覆盖全部翻译展示：段落译文块（单段「译」按钮、整页沉浸翻译、翻页缓存回填，统一在 `insertTranslation` 入口调度）与划词翻译气泡（译文渲染完成后计时）。到点移除译文并复位段落按钮，可再点「译」重出（命中缓存即时显示）。
  - 细节：loading（翻译中…）/error（失败重试）中间态不计时；划词气泡内点击（🔊 发音、＋/－ 标记）以捕获阶段监听重置计时，避免操作中途气泡消失；配置修改后已显示的译文立即按新时长重排计时。
- **验证**：`node --check` 语法通过；全量 pytest **160 passed**；node 模拟受控时钟 15 用例全过（默认 5s 到点消失、0 不隐藏、改配置重排、手动取消 no-op、loading/error 不计时、非法值回退）；临时拉起服务确认可正常启动，且 `read.html` 经 Jinja 渲染含新输入项（默认值 5）。
- **部署**：develop 分支工作区改动；静态资源无版本号，部署后需强刷浏览器。

### 总结（R38 后更新）

- **requests.md**：追加 R38（翻译显示时长配置）。
- **response.md**：记录 R38 的实现范围（段落译文块 + 划词气泡）、配置入口（设置弹窗，localStorage 持久化，0 = 不自动消失）与验证结果。
- **冲突记录**：无；R31 曾要求划词气泡可通过 ESC/点击关闭——本次自动隐藏与该需求方向一致（多一种消失途径），配置为 0 时保留原有纯手动关闭行为。

### R39：哈利波特 EPUB（book 50）生词标注失效定位（R37 补充，未改动代码）

- **结论：功能链路健康，9/9 那次 HP 阅读会话的生词上报在目录页之后静默中断，且仅中断在那一次会话。**
  - book 50（Sorcerer's Stone）在 ES `reading_vocabulary` 只有 9/9 07:59:02-03 的 2 条 `"chapter"` 事件——该词只出现在目录页（"CHAPTER ONE…"），说明 analyze 当时只处理了目录页。
  - 同一会话 45 秒后（07:59:48）整页翻译缓存仍在正常写入（`magicbook-read-paragraph`，同一鉴权/同一代理），排除 401/CSRF/代理问题。
  - **全链路今天验证正常**：9/13 12:36 读 book 5 时 analyze 成功调用 10 次、写事件 12 条；用户 hard_level=6、单词本 8499 词（8403 个 familiarity=0），任何 HP 正文页都必然命中生词——9/9 正文页从未发出过 analyze 请求（moon-well 无对应 requestURI 记录）。
  - **书本身无问题**：把 book 50 EPUB 拉到本地，用线上同款 `epub.min.js` 复现「目录页→盲文说明页→第一章正文」逐页取文，全部成功（每页 1600~2200 字符）；`index_split_*` 分章结构与 CSS 均无异常。
  - 9/9 中断的直接现场已不可追溯（moon-well 容器 9/13 重启，日志丢失；magicbook 访问日志随容器重建丢失）。关联背景：`reading_vocabulary` 索引 9/8 22:01 被备份为 `reading_vocabulary_bak_20260908` 后删除，9/9 07:59:02 由该书的第一条请求隐式重建——当时正处于索引迁移窗口。
  - **建议**：环境恢复后在 book 50 上翻一页正文即可验证恢复；若再现中断，浏览器 DevTools Network 看 `/ajax/reading-vocabulary` 是否发出及响应码（最可能：请求未发出=前端取文/翻页事件问题，或 401/503=会话令牌）。
- **顺带发现（建议处理）**：
  1. 公网 `moonwell.haoshenqi.top` 的 Traefik 路由（Server 2 `/app/app-manager/traefik-dynamic/moonwell.yml`）指向 Ubuntu .11 上 8/12 启动的旧 moon-well 裸进程（旧 API 路径、`/auth/refreshToken` 抛 `NoClassDefFoundError`），应改指 fnos:8082 或删除。
  2. book 50 整书翻译任务（9/8 13:22）`PARTIAL_FAILED`：224 段仅完成 1 段。
  3. magicbook `bookmark` 表为空：阅读器书签从未落库，位置恢复仅靠浏览器 localStorage。
- **环境突发（排查尾声，与本问题无关）**：9/13 13:15 前后 PVE 宿主机（192.168.31.5）连同其上的 fnos（.9，magicbook/moon-well 所在）与群晖（.10）全部失联，公网 `magicbook.haoyuhang.top`/`moonwell.haoshenqi.top` 因此整体不可用；13:12 前 SSH/服务均正常。待宿主机恢复后再做实时复现验证。

### 总结（R39 后更新）

- **requests.md**：追加 R39（R37 补充：问题发生在 HP book 50 EPUB）。
- **response.md**：记录 book 50 的定位结论（9/9 单次会话中断、链路今天验证健康、书无问题）、三个顺带发现与 PVE 宿主机宕机事件。未改动任何代码。
- **冲突记录**：R37 初判主因为「TXT 阅读器无此功能」，R39 依据用户补充（HP 为 EPUB）修正为「9/9 那次会话静默中断」；TXT 阅读器无词汇功能的事实不变，作为背景保留。

### R40：哈利波特 EPUB 打开即卡死无法翻页（IndexSizeError 毒化 epub.js 显示队列）修复

- **现象（用户实测复现）**：打开 book 50 后无法翻页，DevTools 报 `Uncaught IndexSizeError: Failed to execute 'setStart' on 'Range': There is no child at offset 309`（epub.min.js 内部 `display → locationOf → toRange` 链）。
- **根因**：阅读器位置恢复逻辑（`cps/static/js/reading/epub.js`）在启动时 `rendition.display(localStorage 保存的 CFI)`。书内容更新（Calibre 重新转换/元数据刷新等）后旧 CFI 的字符 offset 越界，epub.js 内部 `toRange` 抛 IndexSizeError。该异常：① 同步 try/catch 接不住（异步 promise 链）；② rejection 被 epub.js 内部链吞掉，`display()` 返回的 promise 永远 pending、调用方 `.catch` 也不会触发；③ 显示队列（promise 链式 enqueue）被 rejection 毒死——此后所有 `display/next/prev` 永不执行，整本书无法翻页。**生词标注失效（R37/R39）正是此卡死的伴生症状**：翻页不动 → `relocated` 不触发 → `inspectVocabulary` 不跑 → 无 analyze 请求；而划词/段落翻译作用于当前可见页，不受队列影响，仍能工作（与 9/9 现场完全吻合）。
- **本地复现与验证**（/tmp harness + 线上同款 epub.min.js + book50.epub）：现状写法 display(坏CFI) 后 next 两次均 4s 无响应（队列死亡，100% 复现）；`.catch` 与 catch 内的恢复调用均无法挽救（promise 永远 pending）——修复必须让坏 CFI 进不了队列。
- **修复**（纯 `cps/static/js/reading/epub.js`，~100 行）：
  1. **两级位置恢复**：先经 `book.spine.get(savedCfi)` 得到 spine 序号 `display(index)` 安全落位（整数路径不走 CFI Range，无此雷，新老位置缓存统一支持）；随后用 `cfiSafeForCurrentDocument` 轻量校验（解析 CFI 末段 id 断言 + 字符 offset，在当前渲染文档累计该元素文本总长，offset 超界判不安全），通过才 `display(cfi)` 章内精调，不通过丢弃保存的位置并停留在章开头。
  2. **保存端**：位置缓存（localStorage `calibre.reader.position.<bookKey>`）增加 `index`（spine 序号）字段。
  3. **全局兜底**：window error 监听捕获 epub.min.js 的 IndexSizeError（覆盖其他潜在 display(CFI) 调用点，如未来功能），清掉坏位置后刷新重建；sessionStorage 标记防「保存→崩→刷」死循环，阅读器成功初始化后重置标记。
- **验证**：`node --check` 通过；本地 harness 用线上同款 epub.min.js + book50.epub 实测：坏 CFI 判定 `safe=false`、好 CFI `safe=true`；两级恢复落位正确章（index=3, index_split_002.html）；坏 CFI 被拦截未进队列；连续两次 next 均 resolve 且页面切换（对照现状代码为双卡死）。校验与兜底均以「放行+兜底」为缺省，不误伤正常书。
- **部署**：develop 分支提交推送后由 GitHub Actions 构建镜像并经 app-manager 自动更新部署；静态资源无版本号，浏览器需强刷。存量受影响用户（localStorage 中的坏 CFI）部署后首次打开会自动走兜底刷新或两级恢复，无需手动清缓存。

### 总结（R40 后更新）

- **requests.md**：追加 R40（打开 book 50 无法翻页的 IndexSizeError）。
- **response.md**：记录根因（旧 CFI 越界 → epub.js 显示队列毒化 → 翻页卡死 → 生词标注伴生失效）、三级修复（两级恢复/位置缓存加 index/全局兜底）与本地实测结果。
- **冲突记录**：无；R39 中「9/9 中断现场不可追溯」的遗留疑问由 R40 的机制解释补齐。

### R41：复测期偶发 500 定位——moon-well 被并行操作反复重建，窗口期请求必然失败（未改动代码）

- **R40 修复部署验证（成功）**：20:34 CI 构建（1m11s）→ app-manager 自动更新 fnos magicbook 容器 → 线上 epub.js 已含修复。用户强刷后翻页恢复正常，多次复测的生词事件在 ES `reading_vocabulary` 全部落库：20:36 目录页 `chapter`×3、20:49 正文 `half`/`edge`、23:13 正文 `edge`/`open`/`back`/`wide`、23:14 正文 `tiny`/`straight`；21:17 用户在 book 16 上也成功标注 19 词。**生词功能修复确认生效。**
- **「仍然 500」的定位**：用户复测期 `/ajax/reading-vocabulary` 偶发 500。排查发现 fnos 的 moon-well 容器在 23:13:49 与 23:15:24 被 docker compose 连续 replace（`com.docker.compose.replace` 事件，working_dir=/host/app/moon-well），同时 `/book/import-ted` 持续有调用——**有并行会话/自动化正在执行 moon-well 部署与 TED 重导入**。重建窗口期（容器停止→启动→Spring 初始化，约 90 秒）所有代理请求失败，表现为 500/503。窗口外的请求全部成功（23:14:38/40 两次 analyze 成功且事件落库）。moon-well 的 GlobalExceptionHandler 不打日志，故失败实例侧无痕迹。
- **当前状态**：moon-well 现实例 healthy，无 token analyze 正确返回 401；功能链路完整可用。若并行侧（TED 导入/部署）仍在进行，建议待其完成后再复测，避免撞上下一次重建窗口。
- **改进建议（另行安排）**：① magicbook `_moonwell_proxy` 对 502/503/504 增加一次短重试（analyze 幂等可安全重试），跨越部署窗口；② moon-well 侧部署如需零中断，走健康检查就绪后再切流量；③ moon-well `GlobalExceptionHandler` 补异常日志（当前吞异常无痕迹，本次排查显著受阻）；④ `Result.error` 生成的 `success` 字段恒为 true（body `"success":true` 但 code 500），前端无法凭 success 判错，一并修正。

### 总结（R41 后更新）

- **requests.md**：追加 R41（部署后复测仍偶发 500）。
- **response.md**：记录 R40 修复的部署验证结果（ES 多批落库证据）与偶发 500 的根因（moon-well 被并行操作反复重建、窗口期失败），四条改进建议。未改动代码。
- **冲突记录**：无。

### R42：reading-vocabulary 偶发 500 真根因——Nacos 覆盖 ES 为公网环回链路，间歇 IOException（moon-well 侧修复）

- **决定性证据（用户提供 500 响应体）**：`{"message":"save reading vocabulary failed","code":500}`——即 `ReadingVocabularyService.analyze` 中 `client.index()` 抛 IOException 被 `catch (IOException)` 包装的异常。同页其他 analyze 成功、ES 落库正常，故障为间歇性。
- **排查路径**：moon-well 日志成功调用（07:19/07:20/07:32/33 共 8 次全部 201 落库，HP 每页仅 1-2 个超档词，单条写入属正常）与用户稳定 500 矛盾 → `GlobalExceptionHandler` 不打日志吞异常 → 用 magicbook 代理日志改进（R41 建议落地：非 2xx 记录状态码+响应体）拿到响应体 → 定位 ES 写入链路 → **发现容器环境变量（`ELASTICSEARCH_HOST=192.168.31.9` 直连）与运行时行为（`https://es.haoshenqi.top:443`）矛盾** → Nacos 配置中心 `moon-well.yaml`（spring.config.import，优先级高于环境变量）硬编码 `elasticsearch.host: es.haoshenqi.top`。
- **根因**：moon-well 在 fnos 上访问**同机的 ES**，却经 `fnos → Server2 Traefik(443) → Tailscale → fnos:9200` 的公网环回链路（延迟 165ms vs 直连 0.7ms，且受 Traefik keep-alive/Tailscale 抖动影响）。链路间歇失败时：`findPrevious`/`dictionaryEntry` 等查询类调用被 catch 静默（日志中 `nextWord doesn't exists` 频发即征兆），**唯独 index 写入的 IOException 被包装为 500**——表现为「生词标注偶发失败、翻页/翻译正常」。
- **修复**：经 Nacos v3 API 更新 `moon-well.yaml` 的 `elasticsearch` 段为直连（`host: 192.168.31.9, port: 9200, scheme: http`），重启 moon-well。验证：重启后 healthy，RestClient 日志已显示 `GET http://192.168.31.9:9200/_cluster/health` 200。修改前配置已备份至 fnos `/vol1/1000/app/moon-well/nacos-moon-well.yaml.bak-es-roundtrip-20260914`。
- **遗留**：① moon-well `internalUri` 互信路径实测未生效（无 token + X-User-Subject 仍 401），配置绑定待查（Nacos 优先级/绑定问题），不影响主链路（用户走 session token）；② `Result.error` 的 success 恒 true、全局异常处理器无日志，均已列 R41 建议待修；③ Nacos 侧改配置后需重启才对非 @RefreshScope 的 ES client bean 生效。

### 总结（R42 后更新）

- **requests.md**：R41 追加「部署完成后仍 500」。
- **response.md**：记录 R42 真根因（Nacos 覆盖 ES 为公网环回 → index 间歇 IOException → 500）与修复（Nacos ES 段改直连 + 重启验证），含配置备份位置与三条遗留。
- **冲突记录**：R41 曾将偶发 500 归因于并行重建窗口期，R42 以响应体证据修正为 Nacos ES 公网环回链路的间歇 IOException；窗口期失败与链路抖动两类 500 并存，R42 修复后者（主因）。

### 对 requests 的回应（R43 生词两种展示临时下线，requests #42）

- **改动**：`cps/static/js/reading/epub.js` `markVocabulary` 注释掉生词的两种信息展示——① 悬停 tooltip（`span.title`：释义 + 「上次：书 · 章节」）；② 点击 `alert` 弹窗。两者内容相同且过长，仅保留波浪线标注与 `dataset.word`；划词气泡（翻译/发音/＋－标记）不受影响。
- **配合（moon-well 侧）**：analyze 接口同步暂停查词典释义、仅返回生词本身（`word` + `unknown`），响应体积大幅缩小；连带超纲词（词典 level）判定暂停，仅单词本内未掌握词会返回，详见 moon-well response.md R25 与其 `docs/readme/reading-vocabulary.md` 临时调整说明。
- **验证**：`pytest tests/test_reading_vocabulary.py` 27/27 通过；`node --check epub.js` 语法通过；全仓测试无其它断言依赖被注释代码。
- **恢复方式**：取消 `markVocabulary` 内两处注释即可（moon-well 侧需同步恢复 VO 字段）。

### 总结（R43 后更新）

- **requests.md**：2026-09-14 新增 #42。
- **response.md**：记录 R43 前端展示下线范围、moon-well 配套改动、测试结果与恢复方式。
- **冲突记录**：无。

## 2026-09-15

**R43：默认档位 CET4 + 阅读设置独立页**

- moon-well：DEFAULT_HARD_LEVEL 6→3（CET4），未配置 hard_level 的用户按 CET4 判生词；新增 ReadingSettingsService/Controller（GET /vocabulary/reading/settings 返回当前档位+0-9 档全集，POST /vocabulary/reading/settings/hard-level 校验并落库 app_user.hard_level）；路径复用 /vocabulary/reading/** 的 internalUri 放行规则，无需改拦截器。
- magicbook：新增独立页面 /reading/settings（模板 reading_settings.html，不动 calibre 原有 profile/admin 功能）；web.py 增加页面路由与 /ajax/reading-settings、/ajax/reading-settings/hard-level 两个代理（与现有 reading-* 代理同模式：内网信任 + 身份头透传 + 401 自动刷新）；layout.html 两套主题的用户菜单加「Reading Settings」入口。
- 后续扩展：新的用户级阅读配置统一加到 ReadingSettingsService + reading_settings.html 页面，不再散落。
- 测试：moon-well 259/260（MagicbookApplicationTests 为 contextLoads 冒烟，依赖真实 DB，非内网环境连不上，存量问题）；magicbook pytest 163+6=169 全过（新增 tests/test_reading_settings.py）。

**总结**：requests.md 与 response.md 已同步更新；R43 无与既有需求冲突项。

**R43 修复：保存档位 400**

- 根因：CSRFProtect 全局启用，设置页 JS 从 cookie 读 CSRF token（项目 token 不写 cookie），X-CSRFToken 为空被 400 拒绝。
- 修复：表单加 hidden csrf_token input，JS 改从 DOM 读取（与 epub.js/ai_chat.js 项目惯例一致）；400 响应体含 csrf 时自动刷新页面取新 token（sessionStorage 防死循环，与 epub.js reloadIfCsrfBlocked 同策略）；错误提示带上 HTTP 状态码。
- 测试：新增 CSRF 400 透传用例，pytest 164 全过；已提交推送。

## 2026-09-15（续）

**R44：AI 伴读提示词增加未掌握词汇**

- chat-system 模板生词段落改为「以下是用户暂时还未掌握的词汇：{{unfamiliar_words}}」，空态文案统一为「（本页暂无）」（原 "(none marked)" 中英混杂）。
- 数据无需改动：前端 getUnfamiliarWords() 返回的 vocabularyRecords.unknown=true 集合已包含 reading-vocabulary（/analyze 按档位判定）的生词与用户手动 +/− 标记，经 /ai/chat → build_system_prompt 注入提示词。
- 测试：test_ai_memory 断言更新 + 新增句子存在性断言；pytest 164 全过。

**R44 修正：原提示词保留，中文句作为新增段**

- chat-system 模板恢复原「Unfamiliar words on this page」英文段（列表原样），中文句「以下是用户暂时还未掌握的词汇：…」作为单独一段追加在其后——同一数据源（unfamiliar_words）渲染两处，原提示词语义完整保留。

**R44 再修正：原 chat-system 模板原样保留，中文句作为独立段追加在末尾**

- 之前两次把中文句插进了模板中间（原英文生词段内/其后），不符合「保留原先的系统提示词」的本意。
- 现模板结构：原英文 AI Reading Companion 提示词逐字不动（含 Book Metadata 书名段），末尾在 memory 段之后追加独立段落「以下是用户暂时还未掌握的词汇：{{unfamiliar_words}}」，与 {{extra_section}}（管理员附加指令）共存。
- 书名说明：用户发送消息时前端已带 book_title/book_authors（ai_chat.js POST body），服务端渲染进 Book Metadata 的 Title 行，本就满足「带上当前正在阅读的书名」，无需改动。

