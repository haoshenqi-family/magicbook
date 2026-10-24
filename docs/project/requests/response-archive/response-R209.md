# 归档 — R209 积分内测活动 + 充值倍率机制

> 2026-10-24 R213-C 与 R217 合流（develop）后窗口达 11 节触发轮转搬移，原样搬移不改写。

## 2026-10-23（R209：积分内测活动 + 充值倍率机制——充值页代理与前端）

### R209（承接 moon-well R205；用户：「增加一个内测活动，当前积分获取率*10……仅管理员可以发布活动」）

- **本仓职责**：moon-well 负责倍率解析、下单快照、注册赠送；magicbook 只做「代理 + 展示 + 管理员发布入口」，不参与任何积分计算（数字一律由服务端给，前端不拼接）。
- **代理路由（`cps/routes/credit.py`）**：新增 `/ajax/credit/admin-promotion-create`、`/ajax/credit/admin-promotion-list`，均 `@user_login_required` + `current_user.role_admin()`，形态与既有 `/ajax/credit/admin-adjust` 一致；非管理员直接 403（前端入口本来也不渲染，这是第二道闸；moon-well 还有白名单第三道）。
- **档位卡片（`cps/static/js/credits.js` + `cps/templates/credits.html`）**：`multiplier > 1` 时加「内测 ×N」红标、`baseTitle` 划线（文案「原到账 …」）、倒计时（`promotionEndTimeEpochMs - Date.now()` 换算「剩 N 天/小时/分」，60 秒刷新）。**为什么不用时间字符串**：`new Date('2026-12-31 23:59:59')` 按浏览器本地时区解析，UTC 环境的用户会差 8 小时看到「活动已结束」。
- **管理员面板**：同一 `role_admin()` 面板内新增发布表单（`datetime-local` 起止 + 倍率 1–100，默认起=今天零时、止=2026-12-31 23:59:59）与活动列表（起/止/倍率/状态）。提交前 `confirm` 明示「发布后不可修改或撤销」——活动不可变是用户拍板的口径，配错只能由 DBA 改库，所以必须让人在动手前看清。
- **时区约定**：`datetime-local` 的值**原样提交**，不做客户端换算；moon-well 用显式 `Asia/Shanghai` 的 Clock 解释。这样「管理员填的 10-24 00:00」在任何办公地时区下都指北京时间的 10-24 00:00。
- **验证**：`python -c "ast.parse"`（路由语法）、`node --check cps/static/js/credits.js`、模板元素 id 与 JS 选择器逐一对照（`credit-promo-form/start/end/multiplier/rows` 全命中）。真机验收清单：活动期角标与倒计时、无活动时角标消失且标题回 1,000、普通用户直接 POST 代理路由返回 403、发布重叠活动弹出后端文案且不落库。
- **窗口**：本条写入使回应节数达 11，按「写入即检查」把最早一节（原文件标 `## 2026-10-19（R130 …）`、正文实为 R190 回应）原样搬至 `response-archive/response-R130.md` 并登记索引，窗口回 10；只搬移不改写，节标题的错误沿用原文并在归档头注记。冲突记录：无撞号（moon-well R205 / 本仓 R209 各自唯一）。
- **驻留**：worktree `../magicbook-credit-promotion`（分支 `feat/r209-credit-promotion`）待验收，验收通过后 `worktree remove` + `branch -d`；未 push。
- **验收期微调（2026-10-24，用户两条意见，原 worktree 续作）**：① 档位划线文案去掉「原到账」前缀——「原到账 50万 积分」改为「50万 积分」，划线 + 灰色已表达原价语义，`baseTitle` 服务端文案原样展示；② 管理员调整目标用户从手填 ID 改为**下拉选择**——userId 与本站账号不同源（moon-well `app_user`），手填极易打错人。配套：新增代理 `/ajax/credit/admin-users`（`role_admin()` 门禁同 admin-adjust，moon-well 白名单三道闸），新占位符「Select user...」补中文翻译并重编译 `.mo`；JS 下拉标签 `#id 昵称 (email)`，加载失败 alert 可见、禁止静默退化回手填。测试：`test_credit_consume.py` 10 例 + `test_i18n_seed_contract.py` 5 例全绿（新增转发/403/下拉结构与文案断言）。moon-well 侧同轮加 `POST /credit/admin/users`（见其 R205 LLD §10）。
