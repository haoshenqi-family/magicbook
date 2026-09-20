# 订阅充值页面 — 详细设计（LLD）

## 1. 背景与目标

- moon-well 已具备 SaaS 计费后端（套餐/订单/支付宝当面付/订阅开通，见 moon-well `docs/feat/saas/design/saas-alipay-lld.md`），但无任何前端入口。
- 本设计在 magicbook Web UI 新增「订阅充值」页面：浏览套餐 → 支付宝扫码付款 → 自动开通订阅。**moon-well 侧零改动**。

## 2. 架构与鉴权链路

```
浏览器(magicbook.haoyuhang.top)
  → magicbook 后端 /ajax/subscription-*（@user_login_required + CSRF）
    → _moonwell_proxy 转发（携带 session 中的 moon-well JWT + X-User-* 身份头）
      → moonwell.haoshenqi.top /api/saas/**（JWT 鉴权）
```

- moon-well JWT 来源：OIDC 登录时经 `POST /auth/oidc/exchange` 用 Authentik id_token 换取（`cps/oidc.py`），存 flask session；代理层 401 自动刷新（`_moonwell_refresh_session_token`）。
- **不走前端直连**：CSP `default-src 'self'` 禁止跨域 fetch，且 token 不落浏览器；与现有 ~20 个 `/ajax/*` moon-well 代理路由同一模式。
- 本地密码登录（OIDC 未启用）用户 session 无 moon-well token → 接口 401，页面按错误信息提示；与成就/阅读设置等既有 moon-well 功能行为一致。

## 3. 接口契约（magicbook 代理 ↔ moon-well）

| magicbook 路由 | moon-well 上游 | 方法/入参 | 返回（Result.result） |
| --- | --- | --- | --- |
| `GET /subscription` | —（页面） | — | subscription.html |
| `GET /ajax/subscription/plans` | `GET /api/saas/plan/list` | — | 套餐数组（id/name/description/price/durationDays/features） |
| `GET /ajax/subscription/current` | `GET /api/saas/subscription/current` | — | 当前订阅（planId/startDate/endDate/status） |
| `POST /ajax/subscription/order` | `POST /api/saas/order/create` | `{planId}` | 订单体（orderNo/amount/status=0/expireTime，30min 有效） |
| `POST /ajax/subscription/pay` | `POST /api/saas/payment/alipay/precreate` | `{orderNo}` | `{orderNo, qrCode}`（二维码内容串） |
| `POST /ajax/subscription/order-status` | `POST /api/saas/payment/alipay/query` | `{orderNo}` | 订单体（status：0 待支付/1 已支付/2 已取消）；moon-well 侧对待支付订单主动查支付宝补偿落账 |

所有响应为 moon-well `Result` 包装 `{success, message, code, result}`；代理超时：外呼支付宝的 pay/order-status 15s，其余 10s。

## 4. 前端设计

- 页面：`cps/templates/subscription.html`（extends layout.html；**必须用 `{% block js %}`**，layout 无 `scripts` block——achievements.html 存在用错 block 的存量 bug，勿模仿）。
- 逻辑：`cps/static/js/subscription.js`
  - 套餐卡片渲染（过滤 price≤0 的免费套餐，不走支付宝）；features 为 JSON 字符串，解析为特性列表（失败静默）。
  - 购买：建单 → 预下单拿 qrCode → qrcodejs（vendored，MIT，`cps/static/js/libs/qrcode.min.js`）canvas 渲染二维码 → 倒计时（按订单 expireTime，缺失时按 30 分钟兜底）→ 3s 轮询 order-status。
  - 终态：status=1 → 停轮询、提示开通成功、刷新当前订阅；status=2 或倒计时归零 → 停轮询、提供「重新生成订单」（同一套餐重新建单）。
  - 容错：连续 5 次轮询失败自动停止并提示；所有失败展示 moon-well 返回的 message。
- 导航入口：layout.html 两处主题（caliBlur 下拉 + 默认 navbar）各加 `top_subscription`（glyphicon-credit-card），仅登录可见（`not current_user.is_anonymous`）。
- CSRF：模板 hidden input `#subscription-csrf`，JS 取值放 `X-CSRFToken` 头（POST 必带）。
- i18n：文案走 `{{_('...')}}` / 英文 fallback，翻译文件补全不在本次范围。

## 5. 安全考量

- 支付动作全部经登录态代理，orderNo 不可预测（毫秒时间戳+随机 4 位）；moon-well 侧 precreate/query 有订单归属校验（他人 orderNo 无法拉起收银台/查询）。
- 二维码内容为支付宝标准 qrCode 串，仅用于拉起支付宝付款，泄露风险=他人代付。
- 不暴露 moon-well JWT 到浏览器；CSP 无需放宽。

## 6. 已知边界

- moon-well 用户无 tenantId 时建单会报错（存量行为，上游约束）。
- 免费套餐（FREE）开通不在本页面支持（后续可加"直接开通"按钮走 mock 渠道或上游扩展）。
- 订单过期后二维码不可复活，只能重新建单（上游 30 分钟订单约束）。

## 7. 验证

- 静态：`python3 -m compileall cps/web.py`；6 个路由 AST 检查；Jinja 解析（subscription.html / layout.html）。
- E2E（需部署环境，见 ac/ac.md）：登录 → 页面选套餐 → 扫码支付 → 状态自动变已开通。

---

## v2：积分充值改造（R61，2026-09-20）

- **变更**：订阅套餐暂时隐藏，页面语义改为「Credits 积分充值」：余额面板 + 三档充值（¥99→2000 分 / ¥10→100 分 / ¥0.01→1 分测试档）+ 原收银台/轮询组件复用。
- **路由**：页面 `/credits`（`credits_page`），旧 `/subscription` 重定向；导航两处主题入口改名 Credits（id top_credits）。subscription 的 5 个 `/ajax/subscription-*` 代理**保留不动**，恢复订阅仅需前端改回。
- **新增代理**：`POST /ajax/credit/account`（余额）、`GET /ajax/credit/packages`、`POST /ajax/credit/recharge-order|pay|status` → moon-well `/credit/*`（上游设计见 moon-well `docs/feat/credit-recharge/design/lld.md`）。
- **测试档可见性**：moon-well 无角色概念，模板注入 `data-is-admin`（`current_user.role_admin()`），JS 过滤 `adminOnly` 档位——纯 UI 约束（0.01 元=1 积分无套利）。
- **文件**：`templates/credits.html`（新）+ `static/js/credits.js`（新）；subscription.html/js 删除。
- **发放语义**：moon-well 在支付落账（通知或查单补偿）同事务内调用 `CreditService.grant` 即刻发放，前端 status=1 后刷新余额面板。
