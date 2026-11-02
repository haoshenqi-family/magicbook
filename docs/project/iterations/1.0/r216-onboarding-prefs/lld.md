# R216 引导收敛 + /me 偏好页 + 难度入口前置 + 成就占位 + 伙伴 IP 风险登记 · LLD

> 状态：已定稿，**已上线并验收通过**（2026-10-23 push develop `634a24c6`；跨仓 moon-well R208 先行为 `e03afbe`。第四次合并基线上全量 **808 passed / 0 failed**，现网探针 `ui-prefs.js`/`me.js` 200、`/ajax/ui-settings` 302、`reader-theme` 405）。余下＝带鉴权的真人跨设备验收
> 工作项：PingCode MB-15 / Ship MAGICBOOK-223（R216）· 关联 R109（引导）· R208（账号级偏好范式）· QA 报告 §六/§七
> 跨仓：moon-well R208（账号级 UI 偏好存储与契约主责；原占 R207，2026-10-23 让号）· magicbook R216（本仓）
> 迭代：magicbook 1.0 · 设计文档路径 `docs/project/iterations/1.0/r216-onboarding-prefs/`

## 1. 目标与不做什么

**目标（用户故事六条）**

1. 引导收敛：三处弹窗统一为一套文案/语言；**账号级只自动出现一次**；匿名不弹；只留「开始引导 + 关闭」两个动作。
2. `/me` 变成真正的偏好页：语言、阅读难度、阅读主题、伙伴；去掉 Kindle 与 20+ 个闲置勾选框；保存按钮是真 `<button>`（键盘可达）。
3. 首页前置阅读难度入口（两步内可调）。
4. 成就页灰色占位态修正（不再像坏图）。
5. 伙伴页文案说明「伙伴 = AI 阅读入口的脸」。
6. 伙伴 IP 风险登记（代码不动角色，写 L3/kb，标出未来替换点）。

**非目标**

- 不改 R213 的 `/home` 信息架构（难度入口做成可复用 partial，R213 落地时直接复用）。
- 不做主题云同步的强实时（阅读页异步拉取，允许新设备一次短暂默认色）。
- 不做自定义主题的跨设备同步（`customTheme` 仍只存本机；`/me` 只提供 5 个内置主题）。
- 不改成就定义、解锁逻辑与伙伴角色图片；只改展示与文案。
- 不做引导沉底数据迁移（老用户以 `view_settings.onboarding` 的已读事实回填，不重弹）。

## 2. 现状与问题根因

| 现象 | 根因 | 本单修法 |
| --- | --- | --- |
| 引导出现三次、文案两套 | `main` / `reader` / `buddy` 三段各自独立邀请；`buddy` 段另有一套文案 | 只保留一套邀请文案；**只在主站段自动邀请一次**；阅读器/伙伴页只保留手动入口与断点续览 |
| 跨设备重复弹 | 状态存 `User.view_settings` + localStorage，且三段各记各的 | moon-well 新表 `user_ui_settings.onboarding_seen` 账号级；关闭即写、读取即判 |
| 中文界面英文弹窗 | 匿名页按浏览器 `Accept-Language`，登录页按 `current_user.locale`；两套文案又各自缺词条 | 匿名直接不弹；唯一文案走 `mbT` 并补齐 zh PO；语言仍由 R212 的 locale 策略决定 |
| `/me` 是 Calibre-Web 原版设置页 | `user_edit.html` 与管理员编辑用户共用；`change_profile` 全量覆盖，删字段会把 `random_books`/`locale`/`sidebar_view` 重置 | 新建 `me.html` + `/me/preferences` **只更新语言两项**；`user_edit.html` 继续给管理员用 |
| 保存按钮键盘不可达 | `<div id="user_submit" class="btn">` + jQuery click | 改为真 `<button type="submit" id="user_submit">`；删掉 main.js 的 click 拦截；管理员页同步受益 |
| 难度入口埋没 | 仅在设置下拉 → 阅读设置 | 首页书墙上方加 `difficulty_entry` partial（可复用），两跳可达 |
| 成就灰块 | `.ach-card.locked .ach-badge { background:#b8b8b8 !important }` + 0.62 透明度 | 保留 tier 底色，锁态改成「虚线卡 + 锁标 + 进度」，不再整块灰 |
| 伙伴页说不清是什么 | 文案只写「rides along on the AI reading button」 | 明确「伙伴是 AI 阅读按钮的脸，纯外观，不改变 AI 的英语老师角色」 |

## 3. 数据与契约

### 3.1 moon-well（主责仓 R208）

新表 `user_ui_settings`（`ddl-auto: update` 自动建表，per-user 单行）：

| 列 | 类型 | 语义 |
| --- | --- | --- |
| `id` | BIGINT PK | 自增 |
| `user_id` | INT UNIQUE | moon-well 用户 id |
| `onboarding_seen` | TINYINT(1) | 账号级「引导已结束/已关闭」 |
| `onboarding_seen_at` | DATETIME NULL | 关闭时间（审计） |
| `reader_theme` | VARCHAR(32) NULL | 5 个内置主题 key；NULL=未设置 |
| `updated_at` | DATETIME | 最后更新 |

端点（均要求用户 JWT；统一 `Result{success,result,message}` 显式包装）：

| 方法 | 路径 | 入参 | 出参 |
| --- | --- | --- | --- |
| GET | `/user/ui-settings` | — | `UserUiSettingsVO` |
| POST | `/user/ui-settings/onboarding/close` | — | `UserUiSettingsVO`（幂等） |
| POST | `/user/ui-settings/reader-theme` | `{"theme":"darkTheme"}` | `UserUiSettingsVO` |

`UserUiSettingsVO`：`onboardingSeen`（布尔）、`onboardingSeenAt`（可空）、`readerTheme`（可空）、`updatedAt`。

**校验与失败语义**

- `theme` 只接受 `lightTheme|darkTheme|sepiaTheme|amberTheme|blackTheme`；非法值 `BusinessException`（不静默回落）。
- 未登录由 `AuthHandlerInterceptor` 拦截；用户身份一律 `UserContext`，不接受 body 里的 userId。
- 关闭引导幂等：已 seen 再调用不报错、不覆盖 `onboarding_seen_at`。
- 数据库异常向上抛，由统一异常处理返回 `success:false`，不吞。

### 3.2 magicbook 代理（本仓）

| magicbook 端点 | moon-well 端点 | 方法 | 说明 |
| --- | --- | --- | --- |
| `GET /ajax/ui-settings` | `GET /user/ui-settings` | 透传 | 页面读账号级 UI 偏好；401/503 原样透传 |
| `POST /ajax/ui-settings/onboarding/close` | `POST /user/ui-settings/onboarding/close` | 透传 | 关闭/完成引导 |
| `POST /ajax/ui-settings/reader-theme` | `POST /user/ui-settings/reader-theme` | 透传 | 保存内置主题；代理层先挡非法 theme（400） |

- 全部 `@user_login_required`，带当前用户 JWT；不新增内网身份头。
- 代理层校验 `theme` 白名单是为了让前端拿到可读 400，而不是上游 500。
- 失败不伪装成功：`/ajax/ui-settings` 失败时前端**不自动弹引导**（避免把「读不到状态」当成「没看过」），并 `console.warn` 留痕。

### 3.3 `/me` 偏好保存

- 页面路由 `GET /me` 渲染 `me.html`；阅读难度服务端用既有 `_moonwell_settings_fetch()` 首屏渲染，失败显示可见错误条（沿用阅读设置页形态）。
- 语言表单 `POST /me/preferences`：**只更新 `locale` 与 `default_language`**，不触碰 `random_books` / `sidebar_view` / `kobo_only_shelves_sync` / `kindle_mail`。成功后 `flash` + 重定向 `/me`。
- 难度保存复用 `POST /ajax/reading-settings/hard-level`。
- 主题保存走 `POST /ajax/ui-settings/reader-theme`，成功后同时写本机 `localStorage["calibre.reader.theme"]`。
- 伙伴卡只读：`/ajax/buddy/mine` 取当前装备伙伴，展示头像/名字，链接到 `/buddy` 领取或切换（账户级数据已在伙伴页管理，不在 `/me` 重复写）。

### 3.4 阅读器主题同步

- `ui-prefs.js` 在阅读器 `<head>` 早载：异步 `GET /ajax/ui-settings`；成功后写 `localStorage` 并广播。
- `epub.js` 仍从 `localStorage` 读初始值（离线/新设备首帧可回落默认）。
- 用户点内置主题时 `selectTheme(id)` 追加 `POST /ajax/ui-settings/reader-theme`；`customTheme` 不同步（本机）。
- 同步失败：当前设备主题照常生效，页面角落 toast/status 提示「主题未能同步到账号」，不静默。

## 4. 引导状态机（收敛后）

```
匿名 ──────────────────────────────► 不自动弹、不请求 UI 设置
登录 + 主站段 + 服务端 seen=false
  + 旧 view_settings.onboarding 无 true ──► 显示唯一邀请卡
      ├─ 开始引导 ──► 导览（main → 阅读器 handoff）
      └─ × / Esc / 跳过 / 完成 ──► POST onboarding/close（seen=true）
登录 + 阅读器/伙伴页 + seen=false ──► 不自动弹；阅读器保留「?」手动入口
登录 + seen=true ──► 任何页面都不自动弹；设置下拉「使用引导」仍可手动重看
```

- 旧数据回填：首次 `GET /ajax/ui-settings` 返回 seen=false、但页面种子 `view_settings.onboarding` 任一为 true → 前端静默调用 close，**不重弹**。
- 邀请卡只有两个动作：主按钮「开始引导」与右上「×」；ESC 等价于 ×。
- 「以后再说 / 不再提示」删除：关闭即视为本次引导结束，不再有第三态。

## 5. 页面改动清单

| 文件 | 改动 |
| --- | --- |
| `cps/static/js/onboarding.js` | 单邀请卡；只主站自动邀请；账号级 seen 拉取/关闭；删 later/never；ESC=关闭；保留三段导览与手动入口 |
| `cps/templates/onboarding_mount.html` | 去掉 `seen` 种子的权威语义（保留为 legacy 回填依据）；匿名标记保留 |
| `cps/routes/preferences.py`（新） | `/ajax/ui-settings*` 三条代理 |
| `cps/routes/__init__.py` | 注册 preferences 域 |
| `cps/web.py` | `/me` 改渲染 `me.html`；新增 `/me/preferences` 局部保存；删除仅供旧 `/me` 的 `change_profile`（管理员编辑用户另走 admin 路由） |
| `cps/templates/me.html`（新） | 偏好页：账号只读、语言、难度、主题、伙伴；真 `<button>` |
| `cps/static/js/me.js`（新） | 难度/主题保存、伙伴卡加载、可见状态与错误 |
| `cps/templates/user_edit.html` | `#user_submit` 改真 `<button type="submit">`（管理员页键盘可达） |
| `cps/static/js/main.js` | 删除 `#user_submit` click 拦截；删除用户时按最近 form 的逻辑保留 |
| `cps/templates/difficulty_entry.html`（新） | 首页难度入口 partial（R213 可复用） |
| `cps/static/js/difficulty_entry.js`（新） | 异步取当前档位；失败保留「设置难度」链接，不显示假值 |
| `cps/templates/index.html` | 书墙上方 include 难度入口 |
| `cps/templates/reading_settings.html` | 难度面板加 `id="difficulty"` 供深链 |
| `cps/static/js/reading/epub.js` | 初始主题读取顺序：账号同步值优先于 localStorage（由 `ui-prefs.js` 写入）；`selectTheme` 上报内置主题 |
| `cps/static/js/ui-prefs.js`（新） | 阅读页账号主题拉取与应用 |
| `cps/templates/read.html` | 引入 `ui-prefs.js` |
| `cps/static/css/achievements.css` | 锁态：虚线卡 + 保留 tier 底色 + 锁标，去掉整块灰 |
| `cps/static/js/achievements.js` | 锁态徽章内加锁图标；`title`/标签说明 |
| `cps/templates/buddy.html` | 文案改写：伙伴是 AI 阅读按钮的脸、纯外观、不改变英语老师角色 |
| `cps/static/js/buddy.js` | 锁定态按 `unlockType` 给准确文案（成就解锁，而非 Coming soon） |
| `cps/templates/i18n_seed.html` + zh PO | 新文案词条与中文翻译 |

## 6. 可访问性与交互

- `/me` 所有控件有 `<label for>`；保存用 `<button type="submit">`；Tab 顺序自然。
- 引导邀请卡 `role="dialog"`、关闭按钮 `aria-label`；ESC 关闭；焦点落在主按钮。
- 难度入口是普通链接，键盘可达；状态文本 `aria-live="polite"` 不抢焦点。
- 主题单选项用原生 `radio`，不用纯 div 点击区。

## 7. 失败与降级口径

| 场景 | 行为 |
| --- | --- |
| moon-well UI 设置不可达 | 引导**不自动弹**（宁可漏一次，不重复骚扰）；console.warn；手动入口仍可用 |
| 引导关闭写失败 | 本机先按已看处理（localStorage），下次进入若服务端仍 false **会再弹一次**；console.warn 留痕 |
| 主题账号同步失败 | 本机主题立即生效；显示「未能同步到账号」状态；不回滚 |
| `/me` 阅读难度上游失败 | 页面显示红色错误条 + 重试按钮（复用阅读设置页口径），不隐藏 |
| 伙伴卡加载失败 | 显示错误文案 + 重试；不影响其他偏好保存 |
| 旧后端（无 `/user/ui-settings`） | `GET` 404/非信封 → 视为不可用，不自动弹；不写坏数据 |

## 8. 测试与验收

**自动测试**

- moon-well：`UserUiSettingsServiceTest`（默认值、幂等关闭、主题白名单、用户隔离）；`UserUiSettingsControllerTest`（Result 形制断言、非法主题返回 success:false）。
- magicbook：R216 守卫脚本/测试（可用现有 pytest/JS 静态断言）：
  - 邀请卡只出现一个 `onb-invite-start`，且源码无 `Never show again` / `Later` 自动邀请按钮；
  - 匿名分支不 fetch UI 设置；
  - `/me` 模板不含 `kindle_mail` / `show_` 勾选框 / `kobo`；
  - `user_edit.html` 的 `#user_submit` 是 `<button>`；
  - 成就 CSS 不再有 `#b8b8b8` 锁态。

**人工/无头验收**

1. 同一账号两台设备（或清 localStorage + 新无痕窗口）：仅第一次看到邀请；关闭后另一设备不再自动弹。
2. 匿名访问首页/阅读器：无邀请卡、无 UI 设置请求。
3. `/me` 只用键盘完成「改语言 → 保存」「改难度 → 保存」「改主题 → 保存」。
4. 换设备进阅读器，主题跟随账号；改主题后另一设备刷新生效。
5. 首页两次点击内到达难度设置；当前档位显示正确（如「CET4（默认）」）。
6. 成就页锁态可见 tier 色彩 + 锁标，不再像坏图。
7. 伙伴页文案能回答「伙伴是什么、会不会改变 AI 角色」。

## 9. 文档回填（交付四问 · 2026-10-23 已落地）

- L1：`docs/product/readme/readme.md`（快速开始 + /me/引导行为）、`readme/companion.md`（伙伴定义）、`readme/library.md`（首页难度入口）。
- L2：`docs/product/reading/interface.md` 增补三条 UI 设置代理映射；moon-well 侧 L2 由其 R208 工作项维护。
- L3：`docs/product/learning/features/onboarding.md`（状态机与失败口径）、`docs/product/reading/features/reader-theme-sync.md`（主题同步）、`docs/product/companion/features/buddy-ip-risk.md`（IP 风险登记，含 8 个 HP 派生角色与替换点）。
- 迭代：`docs/project/iterations/1.0/plan.md` MB-15 状态回写；`response.md` 驻留台账。
