# R274 · 登录/账号页表单 UI 修正

## 1. 起因

真机截图里，验证码输入框的 placeholder「6 位验证码」只露出下半截、还压在边框线上，
输入框视觉高度明显小于预期。

## 2. 根因

`input` 在小程序里有自带高度（约 `1.4rem`），而 `.field` 同时写了：

```css
box-sizing: border-box;
padding: 22rpx 24rpx;
```

于是内容区 = 自带高度 − 上下内边距 ≈ 0，文字被挤到框外，只剩被裁剪的下半截。
`box-sizing` 本身没错，错在**用 padding 去撑 input 的高度**。

## 3. 改法

```css
.field {
  height: 92rpx;         /* 高度显式给，不再靠 padding */
  padding: 0 24rpx;      /* 竖向 padding 必须为 0 */
  box-sizing: border-box;
  line-height: 92rpx;    /* 兜底：line-height 不生效时 input 自身也居中 */
}
```

同时把 `.field` **上提到 `app.wxss`**：登录页与账号页各写过一份，两份都带同一个 bug；
留两份就等于给自己留两次再犯的机会。账号页的 `.field[disabled]` 一并上提。

## 4. 顺带的三处调整

| 项 | 之前 | 现在 |
|---|---|---|
| placeholder | 继承 `.field` 的 30rpx | 走 `placeholder-class="field-ph"`，28rpx 浅灰 |
| 验证码框 | 与邮箱框同款左对齐 | `.field-code`：40rpx、居中、`letter-spacing: 12rpx`，六位数一眼能核对 |
| 「重新发送」 | 恒为主色，看不出倒计时中不可点 | `resend-wait`（灰）/ `resend-ready`（主色）两态；逻辑层本来就有 `countdown > 0` 拦截，这次把视觉补上 |

## 5. 没动的地方（以及为什么）

- 生词本搜索框 `.search`、复习页拼写框 `.field-inline`：都只写 padding、**没有** `box-sizing: border-box`，
  高度由「自带高度 + padding」叠加，不会被压塌。没实测的东西不动。
- 未加输入框 focus 描边：小程序 `input` 的 `:focus` 不可靠，用 `bindfocus` 改 `setData` 有
  重渲染打断输入的风险，收益不抵风险。

## 6. 验证

- `tests/test_r274_login_ui.py` 4 例静态锁：`.field` 必须有显式 height、竖向 padding 必须为 0、
  `.field` 只允许在 `app.wxss` 定义一次、验证码框与重发两态必须在位。
- 全部 `.js` 过 `node --check`、全部 `.json` 过 `JSON.parse`。
- **本机没有微信开发者工具：未编译、未真机**。真机需确认两件事：输入框文字是否垂直居中（`line-height`
  在原生 input 上的支持度随基础库版本略有差异），以及长邮箱在框内是否被裁。

## 7. 影响面

只改样式与两处模板属性，不动任何请求与状态机；`pages/account`、`pages/login` 两个页面的行为不变。
