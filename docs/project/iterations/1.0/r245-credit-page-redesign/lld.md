# R245 积分页分区重构与充值活动 400 修复 · LLD

> 状态：**开发完成待验收**（2026-10-29）
> 范围：magicbook 前端；配套 moon-well R229 字段级时间兼容。
> 上游：R205 充值倍率活动、R209 magicbook 充值页。
> PingCode：需求 MB-235（`Nal8mNRY`）、缺陷 MB-21（`xn-uxsjb`）。

## 1. 问题与目标

用户报告两件事：

1. 管理员在积分页点击「发布」充值活动，返回 HTTP 400「请求体格式错误」。
2. 积分页功能堆叠过多；后续验收又指出消耗明细几乎看不清。

目标是把页面按具体任务拆分，修复发布链路，并让明细在条纹表中保持清晰；不改积分业务规则。

## 2. 400 根因

`<input type="datetime-local">` 的 `.val()` 形如：

```text
2026-10-29T00:00:00
```

旧版 `credits.js` 原样放入 JSON。moon-well 全局 Jackson 配置只接受：

```text
yyyy-MM-dd HH:mm:ss
```

因此 `CreditPromotionCreateReqDTO.startTime/endTime` 在进入 Controller 前反序列化失败，被全局异常处理转换为 HTTP 400「请求体格式错误」。

## 3. 修复方案

### 3.1 前端规范化

`promotionWireTime(value)`：

- 接受 `YYYY-MM-DDTHH:mm` 或 `YYYY-MM-DDTHH:mm:ss`；
- 只替换日期与时间之间的 `T`，缺秒补 `00`；
- 不调用 `new Date()`，不改变管理员看到的东八区墙上时间。

提交改用页面共享 `ajax()`，由 `unwrapStrict()` 统一解析 `Result`：

- 成功：行内绿色「活动已发布。」，刷新活动列表和充值档位；
- 失败：行内红色显示上游 `message`，保留表单值；
- 不使用 `window.alert()`，避免页面跳栈后用户看不到细节。

### 3.2 后端字段级兜底

moon-well R229 新增 `FlexibleLocalDateTimeDeserializer`：

- `ISO_LOCAL_DATE_TIME`；
- `yyyy-MM-dd HH:mm:ss`；
- `yyyy-MM-dd HH:mm`。

只在 `CreditPromotionCreateReqDTO` 两个字段上使用 `@JsonDeserialize`，不改全局 Jackson 时间格式，避免其他 API 入参/出参契约被连带改变。

## 4. 页面信息架构

### 4.1 一级任务页签

| 页签 | 用户任务 | 说明 |
| --- | --- | --- |
| 充值 | 给账户充值 | 余额 Hero 与充值档位 |
| 积分卡 | 兑换或购买可转赠卡密 | 兑换、购卡赠送、已购卡密 |
| 明细 | 查积分从哪里来、到哪里去 | 汇总、筛选和流水 |
| 管理 | 管理员运营 | 仅管理员渲染 |

余额 Hero 保留三个快捷按钮，点击后调用 `showCreditTab()`；不复制面板内容，不新增页面路由。

### 4.2 管理子页签

`积分调整 / 充值活动 / 批量发卡` 三个任务共用一个管理父页签，但不再纵向同时展开。权限仍由服务端模板门禁和代理 403 两层控制；页签只是信息组织，不是权限边界。

### 4.3 分享卡密

`consumeSharedCardKey()` 在填入兑换框后自动切换到积分卡页签，避免用户看到「已填入」却仍停留在充值页。

## 5. 明细可读性

旧样式：

- 消耗徽标 `#fcf8e3` 浅黄底 + `#8a6d3b` 棕字；
- 金额用内联 `#8a6d3b`；
- Bootstrap `table-striped` 的浅灰底进一步削弱对比。

新样式：

- 获取：`#d4ead9` 底、`#185c31` 字、`#79a98a` 边框；
- 消耗：`#f3cf7a` 底、`#5c3500` 字、`#b47b0c` 边框；
- 金额使用 `.credit-amount` 加粗；获取 `#216a3a`，消耗 `#8a3b12`；
- 去掉 `renderConsumeRows()` 的 `.css('color', ...)`，由语义类维护视觉。

## 6. 改动文件

| 文件 | 改动 |
| --- | --- |
| `cps/templates/credits.html` | 四个一级页签、管理三子页签、卡密任务分区、Hero 快捷入口、明细高对比样式 |
| `cps/static/js/credits.js` | `showCreditTab()`、分享自动切页、`promotionWireTime()`、共享 `ajax()` 与行内反馈、金额语义类 |
| `cps/translations/zh_Hans_CN/LC_MESSAGES/messages.po` | R245 新增模板词条 |
| `cps/translations/zh_Hans_CN/LC_MESSAGES/messages.mo` | 由合并后的 PO 重新编译，不手改二进制 |
| `tests/test_credit_page_r245.py` | 页签结构、非管理员门禁、时间提交、行内反馈与颜色类守卫 |

## 7. 测试

- `tests/test_credit_page_r245.py`：4 passed。
- `tests/test_credit_card.py + tests/test_credit_consume.py`：24 passed。
- 合并最新基线后复跑 R245、积分卡、积分明细、i18n 契约。
- `node --check cps/static/js/credits.js`。
- `git diff --check`。

## 8. 边界与不变量

- 不改充值档位、倍率计算、订单快照、卡密状态机、管理员调整和邮件通知。
- 不新增后端接口；活动仍通过既有代理转发。
- 不改变管理员白名单和页面权限。
- 活动发布后仍不可修改或撤销，二次确认保留。
- 明细颜色只辅助方向识别，文字徽标仍是主要语义。
- 不修改 Calibre/Library 导航与 R251 的 UI 信息架构规则。
