# 引导导览（Onboarding）· L3

> R109（2026-08）建立三段式 spotlight 导览；R216（2026-10-23）收敛为**账号级只自动邀请一次**。
> 相关：L1 [readme.md](../../readme/readme.md)、L2 [reading/interface.md](../../reading/interface.md)（UI 设置代理）、
> 本次实现 [lld.md](../../../project/iterations/1.0/r216-onboarding-prefs/lld.md)、moon-well R208（`user_ui_settings` 存储主责）。

## 1. 能力与入口

| 入口 | 位置 | 行为 |
| --- | --- | --- |
| 自动邀请 | 仅主站段（书墙/详情等 layout 页面） | 账号从未看过时出现一次；只有「开始引导」与「×」 |
| 设置下拉「使用引导」 | 所有带 layout 的页面（含 `/buddy`） | 按当前页面段手动重看 |
| 阅读器「?」 | 阅读页左下角 | 手动重看阅读器段 |
| 断点续览 | 跨页面 / 新标签 | 24 小时内从上次步骤继续（`localStorage`） |

导览分三段，共享同一套文案与引擎：

- `main`：浏览、搜索、书墙、详情、下载、书架、设置。
- `reader`：目录、翻页、阅读设置、翻译、书签、全屏、AI 伴读。
- `buddy`：`/buddy` 花名册渲染完成后触发，指向雪鸮领取按钮。

## 2. 状态机（R216）

```text
匿名 ─────────────────────────────► 不请求 UI 设置，不自动弹
登录 + main + seen=false + 无旧已读 ─► 唯一邀请卡
    ├─ 开始引导 ─► 导览（可 handoff 到阅读器段）
    └─ × / Esc / 完成 / 跳过 ─► POST onboarding/close（seen=true）
登录 + reader/buddy + seen=false ──► 不自动弹；保留手动入口
登录 + seen=true ──────────────────► 不自动弹；手动入口始终可用
```

「关闭」与「完成」是同一个账号级事实，不再有「以后再说 / 不再提示」第三态。ESC 与右上「×」等价。

## 3. 实现方式

**挂载**（`cps/templates/onboarding_mount.html`）

- 由 `layout.html` 与各阅读器页 include；输出 `window.MagicbookOnboarding`：
  `seen`（旧 `view_settings.onboarding`，**只作回填依据**）、`anonymous`、`guideBookId`。
- 同时输出隐藏 CSRF 域，保证关闭请求在任何页面都有 token。

**前端**（`cps/static/js/onboarding.js`）

| 函数 | 职责 |
| --- | --- |
| `fetchUiSettings()` | `GET <appPath>/ajax/ui-settings`，缓存 promise；成功取 `result.onboardingSeen` |
| `legacySeen()` | 旧 `view_settings.onboarding` 里任一段为 true |
| `closeOnboarding()` | 本机置已读 + 清进度 + `POST /ajax/ui-settings/onboarding/close`（幂等） |
| `isSeen()` | **只认** `accountSeen === true`；localStorage 不参与判断 |
| `runSegment(segment)` | 先恢复断点；仅 `main` 段在未读时显示邀请；其余段只保留手动入口 |

**代理**（`cps/routes/preferences.py`）

- `GET /ajax/ui-settings` → moon-well `GET /user/ui-settings`，超时 8s。
- `POST /ajax/ui-settings/onboarding/close` → moon-well 同名端点，超时 8s。
- 全部 `@user_login_required`，携带当前用户 JWT；上游 401/503/业务错误原样透传，不包装成「没有数据」。

**存储**

- 权威状态：moon-well `user_ui_settings.onboarding_seen`（per-user 单行，跨设备一致）。
- 浏览器只保留两类非权威数据：旧 `cfg.seen` 种子（只读回填）与 `calibre.onboarding.progress`（断点，24 小时 TTL）。
- `localStorage` 的旧 `calibre.onboarding.seen` 已不再读写——它按浏览器共享，同一浏览器换账号会串。

## 4. 边界条件

| 场景 | 行为 |
| --- | --- |
| `GET /ajax/ui-settings` 失败（401/503/非信封） | **fail closed**：不自动邀请，`console.warn` 留痕；手动入口仍可用 |
| 旧用户 `view_settings.onboarding` 任一段为 true、账号状态为 false | 静默调用 close 回填，不重弹 |
| 关闭请求失败 | 本机按已读处理；服务端仍 false，其他设备可能再弹一次；只 warn，不伪装成功 |
| 同一浏览器切换账号 | 新账号以服务端状态为准，不会被上一账号的浏览器状态压住 |
| 匿名访客 | 不发 UI 设置请求、不弹邀请；`view_settings` 指向共享匿名行，不能作为状态 |
| 邀请卡阶段按 ESC | 与「×」同义：写账号已读并关闭，不再按「稍后」处理 |
| 锚点缺失（角色门控、空书库、单格式书） | 该步自动跳过，不卡死；跨段 handoff 由进度驱动 |
| 语言 | 唯一英文 msgid 经 `mbT` 按当前 locale 渲染；中文译文在 `i18n_seed.html` + zh PO |

## 5. 测试

`tests/test_onboarding_tour.py`（R216 增补）：

- 邀请卡只有一个 `onb-invite-start`，源码无 `Never show again` / `Later`。
- 账号级通道已注册：`GET /ajax/ui-settings`、`POST .../onboarding/close`。
- `isSeen()` 只认 `accountSeen === true`，源码无 `localSeen`。
- 匿名分支不请求账号设置、不弹邀请。
- ESC 在邀请阶段可关闭；失败时 fail closed 且旧状态可回填。

## 6. 已知不做

- 不做引导沉底数据迁移：旧 `view_settings.onboarding` 只在读取时回填。
- 不在阅读器/伙伴页自动弹邀请（R216 前「三处各弹一次」的根因）。
- 不改三段导览的步骤定义；新增步骤仍按「锚点存在才生效」的约定。
