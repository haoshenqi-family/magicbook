# AI 伴读图标改「伙伴」+ 伙伴系统前端（magicbook R206）· LLD

**状态**：已入库并 push（develop `6b91bf31`，全量 686 passed）；待 MinIO 资产上传后端到端验收

> **坑（本轮真实踩过，已 push 出一次站内错）**：`i18n_seed.html` 的花名册词条写在 `{% set mb_i18n = { … } %}` **表达式内部**，那里加 `# ---- 分节 ----` 行注释会抛 `TemplateSyntaxError: unexpected char '#'`——Jinja 的词法注释只认 `{# #}`，且只能位于标签体外。本文件被 `layout.html` include，一处模板错＝所有 extends layout 的页面一起 500。判据必须是「页面渲染出来」（`tests/test_buddy_page.py` 已常驻覆盖 `/buddy`），`node --check` / `py_compile` 看不见这一类错。

## 1. 承接

跨仓同源：moon-well R201（伙伴数据面）。用户原话：「AI 伴读悬浮按钮图标改成伙伴图片……不要叫 pet 叫伙伴。默认一个机器人 AI 助手。引导页到伙伴模块，可以领取雪鸮。主要功能就只是 AI 伴读的图标替换。」

一期范围：FAB 换图（主功能）+ 独立 `/buddy` 页（花名册/领取/装备）+ 薄代理 + 引导领取雪鸮 + FAB 动效。积分/成就兑换 = 二期。

## 2. 薄代理（`cps/routes/buddy.py`）

复用 `credit.py` 的 `_moonwell_proxy` 范式，注册进 `routes/__init__.py`：

| 本站路由 | 方法 | 上游 moon-well |
|----------|------|----------------|
| `/buddy` | GET | 渲染 `buddy.html` |
| `/ajax/buddy/catalog` | GET | POST `/buddy/catalog` |
| `/ajax/buddy/mine` | GET | POST `/buddy/mine` |
| `/ajax/buddy/claim` | POST | POST `/buddy/claim` `{code}` |
| `/ajax/buddy/equip` | POST | POST `/buddy/equip` `{code}` |

鉴权 `@user_login_required`；用户身份由 `_moonwell_proxy` 透传 moon-well token。

## 3. `/buddy` 页

`buddy.html`（extends layout）+ `buddy.css` + `buddy.js`。JS 拉 catalog 渲染卡片网格：全身图 + 名 + 稀有度色签（COMMON/RARE/EPIC/LEGENDARY）+ 动作（使用中/装备/领取/未开放）。领取/装备 POST 带 CSRF，用返回的最新 catalog 就地重渲染。解包/CSRF 复用全站 `window.MBApi`。

## 4. FAB 换图（主功能）

- `ai_chat_panel.html`：`#ai-companion-fab` 由纯文字「AI」改为「文字兜底 + `<img>`」双形态。
- `ai_chat.js` `loadBuddyFab()`：拉 catalog 取 equipped 伙伴的 `imageUrl`，`new Image()` 预载成功才加 `has-buddy` 切图；**图片未上传/未装备/代理不可达一律保留「AI」文字**，绝不裂图。
- `ai_chat.css`：`has-buddy` 时 img 铺满圆钮；动效 4 态——idle 呼吸、hover 放大（沿用）、thinking 起伏（`streamChat` 发起到 `finishMessage` 收尾，即 send 禁用→恢复窗口）、sleep 打盹（45s 无交互）；`prefers-reduced-motion` 关闭动效。

## 5. 引导领取雪鸮

`onboarding.js` 新增 `buddy` 段（`STEPS_BUDDY`）：`detectSegment` 命中 `#buddy-roster` 即返回 buddy。因花名册异步渲染，`init` 对 buddy 段直接 return，改由 `buddy.js` 渲染完成后调 `window.MagicbookOnboarding.onRosterReady()` 触发邀请/续览，锚点 `#buddy-claim-hedwig` 指向雪鸮领取按钮。主引导 `settings_menu` 文案补上 Buddies。

## 6. 导航

`layout.html` 设置下拉新增 `#top_buddy → web.buddy_page`（与 achievements/credits 同区）。

## 7. 已知待办

- MinIO 资产上传（`buddy/` 前缀 18 个 PNG）在部署期执行，凭证走 env（脚本见 moon-well `deploy/upload_buddy_assets.py`）。
- 端到端验收需 moon-well R201 先上线。

## 8. i18n

新增英文 msgid（伙伴页 + 引导 + 改写的 settings 文案）已补 `i18n_seed.html` 的 JS 词条映射，并追加到 `zh_Hans_CN` po + `pybabel compile`；运行时目录实测 `Buddies→伙伴` 等生效。
