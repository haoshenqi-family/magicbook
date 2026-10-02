# Halo → magicbook 书籍连接器 LLD（方案 A：magicbook 内部导入 API）

> **特性代号**：halo-book-connector ｜ **日期**：2026-09-30 ｜ **状态**：已定稿（R107 评审通过，Q1-Q4 已拍板）
> **需求来源**：requests.md R106/R107 ｜ **关联设计**：`docs/feat/whole-book-translation/design/whole-book-translation-design.md`
> **代码事实依据**：`cps/editbooks.py`（格式上传/落盘）、`cps/reading_translation/service.py`（整本翻译）、`cps/usermanagement.py`（信任头）、`cps/main.py`（blueprint 注册）

---

## 1. 背景与目标

《Magicbook User Guide》（书 #89）等自著指南类图书，内容需要持续修订。当前改书流程是手工的：下载 EPUB → 解包改 xhtml → 重打包 → 网页上传 → 重新触发整本翻译，链条长、易错、无法交给非技术家庭成员。

**本期目标**：
1. 书的**原文以 Halo（note.haoshenqi.top）Markdown 文章为唯一事实源**，作者点「发布」即完成出书；
2. 新建轻量连接器服务：接收 Halo 发布事件 → 拉取 Markdown → 构建 EPUB → 调用 magicbook 内部 API 入库；
3. magicbook 新增**内部导入 API**（共享密钥鉴权）：替换指定书的 EPUB 格式文件（可选换封面），并可选触发整本翻译；
4. 全链路幂等：同一内容重复发布不产生副作用；失败可重放。

**明确不做（负面清单）**：
- 不做多书并发管理后台（V1 用静态映射配置，一篇 Halo 文章 ↔ 一本 magicbook 书）；
- 不改 calibre 的 `metadata.db` 表结构，不引入新库；
- 不做 Halo 插件（Halo 2.x 原生 webhook 够用，避免 Java 插件工程）；
- 不做读者进度/书签的 CFI 迁移（结构大改导致偏移属已知代价，接受）；
- 不做反向同步（magicbook → Halo）。

---

## 2. 总体架构

```
┌─ fnOS (192.168.31.9) ──────────────────────────────────────────────┐
│                                                                     │
│  Halo 容器                halo-book-connector (新, Python)          │
│  note.haoshenqi.top       监听 :9878                                │
│  post.published ──webhook──→ ① HMAC 验签                            │
│        │                    ② REST API + PAT 拉 Markdown ←──┐       │
│        │                    ③ Markdown → EPUB 构建（模板）───┼──┐    │
│        └────────────────────────────────────────────────────┘  │    │
│                                    │ ④ POST /api/internal/      ▼    │
│                                    │    book-import (共享密钥)  EPUB  │
│                                    ▼                                │
│                     magicbook 容器 :8083                            │
│                     ⑤ 覆盖 <path>/<name>.epub (+cover)              │
│                     ⑥ last_modified / set_metadata_dirty            │
│                     ⑦ (可选) WholeBookTranslationService.start      │
│                              └──→ moon-well LLM 翻译（既有链路）      │
│                     ⑧ Bark 通知（连接器侧发）                        │
└─────────────────────────────────────────────────────────────────────┘
```

流量全部内网闭环：Halo → 连接器 → magicbook 均走 192.168.31.9 内部网络，连接器**不暴露公网路由**。

---

## 3. 组件设计

### 3.1 Halo 侧（零代码，纯配置）

| 项 | 约定 |
| --- | --- |
| 书 = 一篇文章 | 每本书对应 Halo 一篇**固定 slug** 的文章（如 `book89-magicbook-user-guide`），正文 Markdown，H1 分章 |
| 文章元数据 | 使用 Halo 自定义注解（annotation）`magicbook.family/book-id=89`、`magicbook.family/trigger-translation=true`，连接器按注解路由，避免服务端配置里硬编码 |
| 发布事件 | Halo 2.26.1 原生 webhook 订阅 `post.published`，回调 `http://192.168.31.9:9878/hooks/halo`，带 Halo 的签名头 |
| 内容拉取 | 连接器收到事件后**不信任回调 body 的正文**，一律用 Halo REST API（PAT token）按 name 重新 GET 最新发布版本，防事件乱序（旧事件重放覆盖新书） |

### 3.2 halo-book-connector（新服务，Python 3.12）

单容器小服务（Flask 或 FastAPI），职责与内部模块：

```
connector/
├── server.py          # webhook 接收、验签、任务入队（同步处理即可，V1 无并发）
├── halo_client.py     # Halo API：get post（markdown content 字段）、PAT 认证
├── builder.py         # Markdown → EPUB 构建（核心）
├── mapping.py         # slug/注解 → book_id 路由表（YAML 配置）
├── magicbook_client.py# 调内部导入 API，重试 + 超时
└── notify.py          # Bark（复用家族 BARK_KEY 惯例）
```

**EPUB 构建（builder.py）**：
- 复用 book #89 现成模板结构（`docs/temp/book89/english/`：`title.xhtml / preface.xhtml / chN.xhtml / appendix.xhtml / colophon.xhtml + nav.xhtml + toc.ncx + content.opf + style.css`），模板文件收进连接器仓库 `templates/magicbook/`；
- 解析：`markdown` 库（`extensions=["toc","fenced_code","tables"]`）把正文按 H1 切分为章节 → 逐章渲染 xhtml；H2 进 TOC；
- 图片：Markdown 内引用 Halo 附件 URL，构建时下载到 `OEBPS/images/` 并重写 src；
- 封面：若映射配置指定 `cover_from=halo_cover_annotation`，下载文章封面图作为 EPUB 内嵌封面 + 单独传给导入 API 换书库封面；
- 打包：zip，`mimetype` 首置不压缩（沿用 R63/R80 已验证的打包方式）；
- 产物落盘 `out/<book_id>/<sha8>.epub`（sha 前 8 位命名，天然幂等可追溯），保留最近 20 份。

**幂等与防抖**：
- 以「拉取到的 Markdown 内容 sha256」为版本键；与上次成功发布的版本相同 → 直接跳过（Halo 重复 webhook、手动重放均无副作用）；
- 同一 slug 处理中收到新事件 → 排队合并，只处理最新；
- 状态持久化：`state.json`（卷挂载），记录 slug → {last_sha, last_book_id, last_job_id, last_time}。

### 3.3 magicbook 内部导入 API（本项目唯一动 core 的部分）

新模块 `cps/book_import/`（blueprint 注册按 `main.py` 惯例追加，参考 ai 模块最小侵入方式）：

```
POST /api/internal/book-import        (multipart/form-data)
```

**鉴权（新建机制，家族首个入站服务间认证）**：
- 请求头 `X-Connector-Key: <secret>`；
- 服务端校验：`hmac.compare_digest` 常量时间比对环境变量 `BOOK_IMPORT_KEY`；
- **`BOOK_IMPORT_KEY` 未配置 → 路由整体不注册（fail-closed，默认关闭）**；
- `@csrf.exempt`（CSRFProtect 全局启用，见 `__init__.py:136`）；不挂 Flask-Limiter（无全局默认限流，密钥即门槛，另见 §6）。

**请求字段**：

| 字段 | 必填 | 说明 |
| --- | --- | --- |
| `book_id` | 是 | 目标书（V1 只支持更新已有书，不支持新建） |
| `file` | 是 | EPUB 文件 |
| `cover` | 否 | JPEG/PNG，同时替换书库封面 |
| `trigger_translation` | 否 | `true` 时导入成功后触发整本翻译 |
| `source_ref` | 否 | 溯源串（如 `halo:book89-magicbook-user-guide@sha256:ab…`），写入日志与 book comments 尾部标记行 |

**处理流程**（复用既有代码路径，不重造轮子）：
1. 校验 book 存在、格式白名单（`config_upload_formats`）、MIME 与扩展名（同 `upload_book_formats` 的校验逻辑，直接调用其等价函数）；
2. 覆盖写 `<config.get_book_path()>/<book.path>/<Data.name>.epub`——**同名格式替换不动 `Data` 行**（`editbooks.py:1476-1487` 实证：已存在则无需写库）；
3. `book.last_modified = utcnow` + `calibre_db.set_metadata_dirty(book.id)` + `session.commit()`（SQLite 写锁冲突走 `_commit_with_retry` 既有范式）；
4. 若带 `cover`：`helper.save_cover` + `replace_cover_thumbnail_cache(book.id)`（与网页上传封面同路径）；
5. 若 `trigger_translation`：以 admin 用户（配置项指定 user_id，默认 1）构造登录上下文，复用 `_whole_book_closures()` 的请求线程快照 → `whole_book_translation_service.start(book_id, "EPUB", force=False, publish, lookup)`；fingerprint=`sha256(path:size:mtime)` 保证同内容幂等；
6. 返回 JSON：`{"bookId":89,"format":"EPUB","size":25941,"fingerprint":"…","translationJobId":"…"|null}`。

**响应码约定**：200 成功｜401 密钥错｜404 路由未启用/book 不存在｜413 超限｜415 格式不合法｜409 并发导入锁｜502 翻译触发失败（**文件已替换成功**，响应体标注 `translationError`，连接器据此降级告警而非回滚）。

**并发锁**：模块内 per-book_id 线程锁，同一书并发导入直接 409（webhook 重放场景由连接器防抖兜底，此为二道防线）。

---

## 4. 数据模型

**零新表**。两侧状态：
- 连接器：`state.json`（版本键/任务记录）+ `out/` 产物，卷持久化；
- magicbook：复用 `books` / `data` / `TranslationJob` 既有表；溯源 `source_ref` 只进日志与 comments 标记行（`<p class="source-ref">…</p>` 由连接器写入 EPUB colophon 页，服务端不解析）。

---

## 5. 时序（正常路径）

```
作者点「发布」→ Halo 存稿 → webhook POST :9878/hooks/halo (签名)
  → 连接器验签 → PAT GET post → sha256(markdown) 与 state 比对
    ├─ 相同 → 200 返回，结束（no-op）
    └─ 不同 → 构建 EPUB → POST /api/internal/book-import (X-Connector-Key)
         → magicbook 覆盖文件/封面 → 提交 DB → start() 翻译批次
         → 200 {jobId} → 连接器更新 state → Bark「📖 book89 已更新，翻译中」
（翻译完成通知沿用整本翻译既有 Bark，不重复造）
```

失败路径见 §7。

---

## 6. 安全

| 面 | 措施 |
| --- | --- |
| 入站（Halo→连接器） | Halo webhook 签名校验 + 仅监听内网（不配 Traefik 公网路由） |
| 入站（连接器→magicbook） | 共享密钥 `BOOK_IMPORT_KEY`，常量时间比对，未配置即不注册路由 |
| 密钥管理 | 连接器与 magicbook 各自 `.env`（fnOS `/vol1/1000/app/*/.env`，家族惯例）；密钥仅授予「导入指定书」能力，端点不暴露任何其它 admin 操作 |
| 能力最小化 | 内部 API 只接受 EPUB + 封面替换，不接受任意路径/文件名（文件名由服务端从 `Data.name` 推导，杜绝路径穿越）；上传大小上限 50 MB |
| XSS/内容 | Markdown→xhtml 由连接器完成，输出走既有 EPUB 阅读器沙箱语义；禁用 raw HTML 中的 script/iframe（构建期清洗） |
| 审计 | magicbook 侧导入日志带 `X-Trace-Id`（家族 trace-id 规范，filebeat→ES 可查）；连接器日志落盘 + 容器 stdout |

---

## 7. 异常与恢复

| 故障 | 行为 |
| --- | --- |
| Halo 拉取失败（PAT 过期/网络） | 连接器 5xx 响应 → Halo 按自身策略重试；连续失败 Bark 告警 |
| EPUB 构建失败 | 不发起导入；保留上一版线上书不受影响；错误详情 Bark |
| magicbook 4xx | 不重试（内容问题），Bark 带原因 |
| magicbook 5xx/超时 | 指数退避重试 3 次（同文件同 sha，服务端幂等）；仍失败 Bark |
| 翻译触发失败（502） | 文件已生效，属可独立补救步骤：连接器按 `jobId=null` 走人工/自动补触发（沿用 `trigger_book89.py` 的服务端脚本兜底） |
| 连接器重启 | 处理中任务丢失 → Halo 重放 webhook 或后台「重新发布」即恢复（全链路幂等） |
| 事件乱序（旧版后到） | 一律以拉取时刻的 Halo 最新发布版为准，事件仅作触发器 |

---

## 8. 测试计划

**magicbook 侧（pytest，进 CI）**：
- 鉴权：无 key/错 key/未启用（env 缺失 404）三类；
- 导入：替换成功（文件字节一致、`last_modified` 变化、`Data` 行数不变）、非法扩展名 415、超大 413、book 不存在 404、并发 409；
- 封面替换与缩略图刷新；
- 翻译触发：mock publish/lookup，断言 fingerprint 幂等复用批次；
- 回归：网页端「上传格式/编辑元数据」不受影响。

**连接器侧（pytest）**：
- builder：样例 Markdown → EPUB 结构断言（mimetype 首位、章节切分、TOC、图片下载重写）；
- 防抖：同 sha 二次触发 no-op；
- magicbook_client：重试/退避/4xx 不重试。

**联调（生产）**：Halo 发布 → ES 查 `app-log-magicbook` 导入日志 → 线上 `/book/89` 校验内容与翻译进度；读者端抽验书签偏移程度并记录。

---

## 9. 开放问题（2026-09-30 评审全部拍板，无遗留）

- **Q1 Halo 版本**：✅ 实测 note.haoshenqi.top 为 **Halo 2.26.1**，原生 webhook 可用，无需轮询退化方案；
- **Q2 一章一文的书写模式**：✅ 接受 V1「一篇长文 = 一本书」，按章拆文聚合留待后续（仅扩展连接器映射，接口不变）；
- **Q3 翻译触发默认值**：✅ **默认自动触发**（`trigger_translation` 缺省 true），fingerprint 幂等保证内容无变化时零开销；
- **Q4 新建书能力**：✅ 接受 V1 不做，只支持更新已有书（先覆盖 #89 场景）。

## 10. 已拍板的设计决策

| # | 决策 | 理由 |
| --- | --- | --- |
| D1 | 原文事实源在 Halo，单向同步 | 用户工作流诉求 |
| D2 | 方案 A：magicbook 加内部 API（非 calibredb 旁路、非模拟网页） | 链路最干净、可复用给未来所有书 |
| D3 | 连接器独立小服务，不做 magicbook 内嵌模块、不做 Halo 插件 | 转换/外呼职责与书库核心解耦，故障隔离 |
| D4 | 内部 API 鉴权用共享密钥 + fail-closed | 家族首个入站服务间认证，最小够用；不引入 OAuth 复杂度 |
| D5 | 替换同名格式不动 `Data` 行 | `editbooks.py` 实证行为，最小写面 |
| D6 | Halo 2.26.1 原生 webhook 为触发源 | 评审 Q1：版本满足，无轮询退化 |
| D7 | V1 一篇 Halo 长文 = 一本书 | 评审 Q2：映射最简，聚合留待后续 |
| D8 | `trigger_translation` 缺省 true | 评审 Q3：fingerprint 幂等兜底，无变化零开销 |
| D9 | V1 不支持新建书 | 评审 Q4：先覆盖 #89 更新场景 |
