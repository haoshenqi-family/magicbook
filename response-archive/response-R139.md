# response 归档：R139（2026-10-09）

> 从 response.md 原样搬移（2026-10-11 R153 写入触发轮转）。只搬移原文，未总结、未改写、未改编号。

## 2026-10-09（R139 复习队列空白按钮修复）

### R139：复习队列四个空白选项按钮——hidden 属性被样式表覆盖（当天修复上线）

- **根因**：learning.js 的 show() 用 `el.hidden` 藏元素，但 CSS 作者样式优先级高于 UA 的 `[hidden]{display:none}`——`.ln-choices/.ln-spell` 的 `display:flex`（R132/R137 引入）使这两个容器永远隐藏不掉；R132 时代每张 CHOOSE 卡都填词掩盖了潜伏缺陷，R137 SELF 降级（19/20 卡片走「隐藏选项」分支）后暴露为四个空白按钮常驻（SPELL 空输入框同样常驻）。
- **修复**（`b03675f2`，15:34 部署 healthy）：show() 改内联 `style.display`（作者样式之上优先级最高，置空回落样式表原值），一处修复覆盖全部受控元素。28 用例绿；线上 JS 验收通过。
- **教训**：Bootstrap 页面里「hidden 属性」对任何带 display 规则的元素不可靠，显隐统一走内联 style 或 `[hidden]` 提升特异性的样式；vocab-test.js 若有同款 show() 实现值得排查（本轮未查，留待下次触碰）。
- **总结**：requests.md 占号 R139；本条为回应；冲突记录：无。

