# 订阅充值页面 — 验收标准

## AC-1 页面与入口

- [ ] **AC-1.1**: 登录用户顶部导航可见「Subscription」入口（默认主题与 caliBlur 主题两处），点击进入 `/subscription`
- [ ] **AC-1.2**: 未登录访问 `/subscription` 跳转登录页（@user_login_required）
- [ ] **AC-1.3**: 页面展示当前订阅面板：无订阅显示 "No active subscription"，有订阅显示套餐名 + 到期日

## AC-2 套餐浏览

- [ ] **AC-2.1**: 套餐列表从 `/ajax/subscription/plans` 加载，展示名称/价格/时长/描述/特性
- [ ] **AC-2.2**: 价格为 0 的套餐不显示购买按钮对应的收银台（前端过滤，不进入支付宝流程）
- [ ] **AC-2.3**: moon-well 不可用或未配置时代理返回 503，页面展示失败信息而非白屏

## AC-3 购买与支付

- [ ] **AC-3.1**: 点击 Buy Now 依次调用 order → pay，页面出现收银台（二维码 + 金额 + 套餐名）
- [ ] **AC-3.2**: 二维码可被支付宝 App 识别并拉起付款（金额与套餐一致）
- [ ] **AC-3.3**: 倒计时按订单 expireTime 递减，归零后停止轮询并提示过期，可「重新生成订单」
- [ ] **AC-3.4**: 轮询期间支付成功 → 页面自动显示开通成功，当前订阅面板刷新为新套餐与到期日

## AC-4 异常与安全

- [ ] **AC-4.1**: POST 请求携带 X-CSRFToken 头，缺 CSRF 时 magicbook 拒绝（400）
- [ ] **AC-4.2**: 非 OIDC 登录（session 无 moon-well token）时接口返回 401，页面展示错误信息
- [ ] **AC-4.3**: 连续 5 次状态查询失败自动停止轮询并提示，不无限重试
- [ ] **AC-4.4**: 用他人 orderNo 调 /ajax/subscription/pay 或 order-status 被 moon-well 拒绝（归属校验）

## E2E 手工步骤（部署后执行）

1. Authentik 账号登录 magicbook → 顶部「Subscription」
2. 选一个付费套餐 Buy Now → 支付宝扫码支付
3. 观察页面 3~10s 内自动变为 "Payment received! Subscription is active."
4. 回到页面顶部确认当前订阅面板已更新；moon-well 侧 `GET /api/saas/order/detail` 确认 status=1、pay_type=alipay，`saas_subscription` 出现/续期记录
5. 异常路径：等订单过期（或调小有效期）后确认倒计时归零 → 重新生成订单可用

---

## v2 积分充值 AC（R61）

- [ ] **AC-5.1**: `/credits` 展示余额（AI 扣费说明），`/subscription` 重定向到 `/credits`
- [ ] **AC-5.2**: 普通用户见 ¥99/¥10 两档；管理员另见 ¥0.01 测试档
- [ ] **AC-5.3**: 充值扫码支付成功后页面自动确认且余额立即刷新（+档位积分数）
- [ ] **AC-5.4**: moon-well `credit_transaction` 出现 RECHARGE GRANT 流水，金额/积分与档位一致
- [ ] **AC-5.5**: 重复通知/轮询并发下积分只发放一次；金额不符不发（上游幂等与校验，moon-well AC 覆盖）
- [ ] **AC-5.6**: 订阅套餐不出现在页面；订阅后端代理保留（恢复开关）
