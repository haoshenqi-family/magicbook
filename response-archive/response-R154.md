# response 归档：R154（2026-10-11）

> 从 response.md 原样搬移（2026-10-12 R165 写入触发窗口检查：与并行会话 R161 合并后窗口达 11 条）。只搬移原文，未总结、未改写、未改编号。

## 2026-10-11（R154：导航层级修正——学习入口一级平铺 + 学习页直达说与写）

### R154（用户反馈：学习入口藏 Settings 里层级不对）

- **交付**（worktree `../magicbook-learning-nav`，分支 `feat/r154-learning-nav`，基于 origin/develop 37edb78；worktree 驻留待用户确认）：
  - **layout.html**：「每日学习」「说与写」从 Settings 下拉撤出，提为左侧一级导航（与高级搜索平级，登录后可见，移动端只留图标）；收纳注释同步更新（R154 例外，防后人按旧口径收回去）。
  - **learning.html**：Today's Plan 面板标题右侧加「Speaking & Writing →」直达跳转（练完复习接输出，零新增词条，"Speaking & Writing" 复用既有 po 词条）。
- **测试**：`test_nav_settings_dropdown.py` 增 1 例（两项全页各出现一次且不在下拉块内，防回流）；`test_learning_proxy.py` 页面渲染断言扩为含跳转链接；合计 46 passed。
- **总结**：requests.md 占号 R154；本条为回应；冲突记录：无。归档：窗口未超。

