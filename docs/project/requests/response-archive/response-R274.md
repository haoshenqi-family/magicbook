# response 归档：R274（2026-11-03）

> 从 response.md 原样搬移（2026-11-06 R284 写入使窗口超 10 条，按「写入即检查」搬最早条目）。只搬移原文，未总结、未改写、未改编号。

## R274 · 登录页表单 UI 修正：输入框被压塌 + 重发态不可辨（2026-11-03）

**对 R274 的回应**：截图里验证码框的 placeholder 只露出下半截、还压在边框上。

- **根因不是「样式没写」，是「写得太满」**：`input` 自带高度（约 1.4rem），`.field` 又加了
  `box-sizing: border-box` 与上下 `22rpx` padding，三者相减后内容区≈0，文字被挤出框外。
  改为显式 `height: 92rpx` + 竖向 padding 归零 + `line-height` 兜底。
- **`.field` 上提 `app.wxss`**：登录页与账号页各写过一份，两份都带同一个 bug。留两份等于
  留两次再犯的机会；账号页的 `.field[disabled]` 一并上提。
- **顺带三处**：placeholder 走 `placeholder-class`（不再继承 30rpx）；验证码框 40rpx 居中 + 字距
  12rpx（六位数一眼核对）；「重新发送」倒计时期间灰掉——逻辑层本来就有 `countdown > 0` 拦截，
  但视觉上和可点长得一样，用户会反复点。
- **不动的**：生词本搜索框 `.search` 与复习拼写框 `.field-inline` 没有 `box-sizing: border-box`，
  高度是叠加而非相减，没压塌；没实测的东西不改。也没加 focus 描边——`input` 的 `:focus` 不可靠，
  用 `bindfocus` 改 `setData` 有打断输入的风险。
- **验证**：`tests/test_r274_login_ui.py` 4 例静态锁（显式 height、竖向 padding 为 0、`.field`
  只允许全局定义一次、验证码框与重发两态在位）。**未真机**：本机无开发者工具，需你在真机确认
  文字是否垂直居中（`line-height` 在原生 input 上随基础库版本略有差异）与长邮箱是否被裁。
