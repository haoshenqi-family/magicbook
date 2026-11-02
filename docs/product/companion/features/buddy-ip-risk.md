# 伙伴 IP 风险登记（L3）

> R216（2026-10-23，MAGICBOOK-223 / MB-15）按用户拍板建立：**内测保留现有哈利波特 Q 版角色，本条不改代码、不改角色数据**；正式对外发布前须换为原创形象。
> 本文是风险登记与替换点清单，不构成法律意见。相关：L1 [companion.md](../../readme/companion.md)、本次实现 [lld.md](../../../project/iterations/1.0/r216-onboarding-prefs/lld.md)。

## 1. 当前事实

伙伴定义种子在 moon-well，共 9 只（启动时按 `code` 幂等 upsert）：

| code | 展示名 | 稀有度 | 获取方式 | 是否 HP 派生 | 资产对象 |
| --- | --- | --- | --- | --- | --- |
| `robot` | 机器人 | —（默认） | DEFAULT | 否（本站原创） | `buddy/robot-{full,head}.png` |
| `neville` | 纳威 | COMMON | ACHIEVEMENT | 是 | `buddy/neville-{full,head}.png` |
| `ron` | 罗恩 | COMMON | ACHIEVEMENT | 是 | `buddy/ron-{full,head}.png` |
| `hedwig` | 雪鸮 | RARE | CLAIM（新用户可领） | 是 | `buddy/hedwig-{full,head}.png` |
| `hermione` | 赫敏 | RARE | ACHIEVEMENT | 是 | `buddy/hermione-{full,head}.png` |
| `dobby` | 多比 | EPIC | ACHIEVEMENT | 是 | `buddy/dobby-{full,head}.png` |
| `snape` | 斯内普 | EPIC | ACHIEVEMENT | 是 | `buddy/snape-{full,head}.png` |
| `harry` | 哈利 | LEGENDARY | ACHIEVEMENT | 是 | `buddy/harry-{full,head}.png` |
| `dumbledore` | 邓布利多 | LEGENDARY | ACHIEVEMENT | 是 | `buddy/dumbledore-{full,head}.png` |

- 种子唯一事实源：moon-well `src/main/java/top/haoshenqi/magicbook/buddy/service/BuddyDefinitionService.java`。
- 资产不入 git，存 MinIO `magicbook` 桶 `buddy/` 前缀；上传脚本 `moon-well/deploy/upload_buddy_assets.py`。
- 除 `robot` 与 `hedwig`（新用户领取）外，其余 7 只在花名册中显示为「成就解锁」，本期不可领取。

## 2. 风险

| 项 | 说明 |
| --- | --- |
| 权利来源 | 8 个角色的名称、形象与设定来自 Harry Potter 系列，权利归 J.K. Rowling、Warner Bros. 等权利人；仓库内没有授权记录 |
| 使用场景 | 伙伴头像会出现在阅读器悬浮按钮、`/buddy` 花名册、`/me` 伙伴卡与引导文案中，属于对外可见的产品界面 |
| 当前边界 | 站内内测、非公开注册、无商业售卖时可作为临时素材；**一旦公开注册、对外宣传、上架应用商店或商业化，风险不可接受** |
| 主要风险 | 著作权（角色形象/美术）、商标（名称/标识）、角色形象的商品化权；即使免费使用也不等于获得授权 |
| 触发条件 | 公开邀请链接、公开发布截图/视频、应用商店上架、任何收费或赞助 |

**结论：这是一条已接受的临时风险，不是已解决的风险。** 在替换完成前，不应把伙伴角色作为对外卖点。

## 3. 未来替换点（按依赖顺序）

### 3.1 角色数据与展示名

- moon-well `BuddyDefinitionService.seedDefs()`：`code` / `name` / `rarity` / `unlockType` / `sortOrder`。
- `buddy_def` 表由启动 upsert 刷新展示属性；**不会删除旧 code**，替换后需单独清理旧行。
- `user_buddy` 以 `buddy_code` 记录用户拥有关系；换 code 必须迁移，否则用户丢失伙伴。

### 3.2 美术资产

- MinIO 对象名与 code 对齐：`buddy/<code>-full.png`、`buddy/<code>-head.png`。
- 上传走 `moon-well/deploy/upload_buddy_assets.py`；替换后确认 18 个对象（9 只 × 2）全部到位，缺一张会导致裂图或 FAB 文字兜底。
- 头像用于 FAB 与 `/me`，全身图用于 `/buddy` 花名册；两张图都要换，不能只换一张。

### 3.3 前端硬编码

| 位置 | 现状 | 替换动作 |
| --- | --- | --- |
| `cps/static/js/onboarding.js` | `#buddy-claim-hedwig` 选择器；步骤标题「Claim your snowy owl」；正文点名 Hedwig | code 变化时同步改选择器；文案改为原创角色名 |
| `cps/templates/i18n_seed.html` | `Claim your snowy owl`、`Hedwig is free…`、`Claim your first companion — a snowy owl…` | 删旧 msgid、加新文案 |
| `cps/translations/zh_Hans_CN/.../messages.po` | 上述三条的中文 | 同步增删并重编译 `.mo` |
| `cps/static/js/buddy.js` / `me.js` | 展示服务端 `name` / `imageUrl`，无角色名硬编码 | 数据换掉即可，无需改代码 |
| 测试 | `tests/test_onboarding_tour.py` 可能断言雪鸮文案；`tests/test_buddy_page.py` 断言花名册结构 | 按新角色更新断言，保留结构守卫 |

### 3.4 引导与入口

- `STEPS_BUDDY` 的锚点由花名册按钮 id `buddy-claim-<code>` 决定；换 code 必须同步 `sel`。
- 新用户领取入口若仍保留「免费领一只」，应换成原创角色，且避免使用「雪鸮」等指向性描述。

## 4. 替换策略（二选一）

| 方案 | 做法 | 优点 | 代价 |
| --- | --- | --- | --- |
| A. 保留 code，只换展示 | 改 `name`、换 MinIO 图、改文案 | 不动 `user_buddy`，改动最小 | code/URL 仍含 `harry` 等痕迹，不能彻底去 IP |
| B. 新 code + 数据迁移 | 新建原创 code，迁移 `user_buddy.buddy_code`，删除旧 `buddy_def` 与旧对象 | 界面、网络请求、对象名都不再出现原角色 | 需要一次性 DB 迁移与资产重传 |

**建议**：正式对外发布前用 **B**；A 只适合极短的过渡窗口，且不能用于任何对外物料。

## 5. 对外发布前检查清单

- [ ] 原创角色设定与美术来源可追溯（自制/委托合同/授权书），记录权利归属。
- [ ] `BuddyDefinitionService` 与新资产替换完成，`buddy_def` / `user_buddy` 迁移并验证。
- [ ] 全仓搜索 `harry|hedwig|hermione|dumbledore|snape|dobby|neville|ron`（代码、i18n、测试、文档）无残留可见引用。
- [ ] MinIO `buddy/` 下无旧角色对象；CDN/浏览器缓存已失效。
- [ ] 对外截图、宣传文案、应用商店素材不含旧角色。
- [ ] 本文件更新为「已替换」，记录替换日期与 commit。

## 6. 责任与时限

- **责任人**：产品所有者（用户）。
- **时限**：不晚于首次公开注册/对外发布；当前内测阶段保持登记状态。
- **触发复审**：公开注册、对外宣传、商业化、或收到权利人通知时立即复审。
- **本条不做什么**：R216 不修改任何角色数据、图片或 `BuddyDefinitionService`；只改伙伴页文案，说明「伙伴 = AI 阅读入口的脸」。
