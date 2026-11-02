## 2026-10-29（R245：积分页按任务分区、充值活动发布 400 与明细可读性修复）

### R245（用户：「积分充值活动，点击发布报错，400 请求体格式错误。积分页功能太多，堆砌太杂乱了。按照具体的小功能且分优化一下。」；后续补：「积分消耗明细项颜色和背景色几乎一样，根本看不出来」）

- **任务定位**：缺陷修复 + 修改意见，承接 R205 充值倍率活动 / R209 充值页；前端主责 magicbook R245，后端同源 moon-well R229。不是新功能域。PingCode：需求 MB-235（`Nal8mNRY`）、缺陷 MB-21（`xn-uxsjb`）。
- **400 根因**：浏览器 `datetime-local` 提交 `2026-10-29T00:00:00`，moon-well 全局 Jackson 只接受 `yyyy-MM-dd HH:mm:ss`，DTO 反序列化在 Controller 前失败并映射为「请求体格式错误」。前端现由 `promotionWireTime()` 只替换 `T`、缺秒补 `00`，不 `new Date()`，不改变东八区墙上时间；moon-well R229 同时在两个 DTO 字段上兼容 ISO/空格/分钟级格式，部署顺序不再触发 400。
- **发布反馈**：活动提交改用共享 `ajax()` + `unwrapStrict()`，成功/失败写入 `#credit-promo-feedback`；失败显示上游 `message` 并保留表单值，不再用 `alert`；成功后刷新活动列表与充值档位。
- **页面分区**：余额 Hero + `充值 / 积分卡 / 明细 / 管理` 四个任务页签；管理只在管理员侧渲染，内部再分 `积分调整 / 充值活动 / 批量发卡`；积分卡页拆为兑换、购卡赠送、已购卡密。余额快捷按钮只切页签，分享卡密进入页面时自动切到积分卡。
- **明细可读性**：去掉金额内联颜色，新增 `.credit-amount.income/consume`；获取徽标改深绿字 + 浅绿底 + 边框，消耗徽标改深褐字 + `#f3cf7a` 琥珀底 + 深琥珀边框，金额均加粗。普通行与 Bootstrap 条纹行都不再出现浅棕字贴在浅黄/浅灰底上的低对比问题。
- **测试**：`tests/test_credit_page_r245.py` 新增 4 条结构/提交/颜色守卫；合并最新基线后定向 `test_credit_page_r245 + test_credit_card + test_credit_consume + test_i18n_seed_contract` 合计 **33 passed / 0 failed**；`node --check cps/static/js/credits.js` 与 `git diff --check` 通过。
- **文档四问**：能力 → L1 `docs/product/readme/credit.md`；契约/页面消费 → L2 `docs/product/credit/interface.md`；实现边界 → 新建 L3 `docs/product/credit/features/page-layout.md`；本次实现 → `docs/project/iterations/1.0/r245-credit-page-redesign/lld.md` 与 `ac/acceptance.md`；需求基线、产品需求总册和迭代 plan 已回填。
- **i18n**：R245 新增模板词条已合并进 `zh_Hans_CN/messages.po`；最新基线带来 `.mo` 二进制冲突，按正确姿势从合并后的 PO 重新 `pybabel compile`，没有用 ours/theirs 二选一。
- **上线状态**：用户令 `merge and push` 后，任务分支快进推送 `origin/develop`（`e4708c27..5e5979f9`）。fnOS `build END OK`，app-manager `deploy SUCCESS`，容器 `running/healthy` 且镜像标签 `house.build-sha=5e5979f9...`；匿名 `/credits` 按预期 302 到登录页。
- **状态与驻留**：**已上线待验收**。worktree `../magicbook-r245-credit-page-redesign`（分支 `fix/r245-credit-page-redesign`）驻留；实现 `39135634`、明细可读性 `0cc8a0dc`、文档 `244634b4`、最新基线合并 `83765414`、发布提交 `5e5979f9`。验收通过后再清理 worktree 与分支。
- **窗口与总结**：写入前 10 节，新增后 11 节；按“写入即检查”把最旧 R241 整节原样搬至 `response-archive/response-R241.md` 并登记索引，窗口恢复 10。requests.md 条目 245 已从占位回填；冲突记录：无撞号，R251 基线合并仅 `.mo` 产物冲突。

