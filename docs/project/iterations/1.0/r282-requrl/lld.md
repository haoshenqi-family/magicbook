# R282 · 请求失败诊断补全（打印实际请求的完整 URL）

## 1. 背景

排查「白名单已配但仍报 `url not in domain list`」时，出现一个无法闭合的矛盾：

| 证据来源 | 结论 |
|---|---|
| 小程序后台「开发管理 → 开发设置 → 服务器域名」 | request 合法域名含 `https://moon-well.haoshenqi.top` |
| 开发者工具「详情 → 项目配置 → 域名信息」 | 同上（该面板拉的是服务端生效配置） |
| 开发者工具本地缓存 `WeappLocalData/localstorage_*.json` | `attr.network.RequestDomain` 含该域名；`appid=wx7b31b435be6beae3`；`isTrusted=true`；无旧 AppID 记录 |
| 服务端实测 | 四个路径均无 301/302；带小程序 UA 的 `POST /auth/wx/login` 返回 `{"code":50402}` |
| 代码 | 所有 `path` 以 `/` 开头；`CONFIG.baseUrl` 为纯 ASCII 31 字符 |

四者皆正常，报错却持续存在。说明**我们给出的诊断信息本身不足以定位**。

## 2. 问题：提示只打印「本该正确」的域名

原实现：

```js
url: CONFIG.baseUrl + options.path,
fail: (err) => {
  console.error('[api] 请求失败', options.path, 'appid=' + runtimeAppId(), err.errMsg);
  reject({ code: -1, message: describeNetworkError(err) });   // 内部只用 CONFIG.baseUrl
}
```

`describeNetworkError` 里写的是 `CONFIG.baseUrl.replace('https://','')`。也就是说，
**无论真实请求发往哪里**，提示永远显示 `moon-well.haoshenqi.top`。

一旦出现下列任一情况，提示都会「看起来完全正确」：

- `options.path` 少写开头 `/` → 主机名被拼成 `moon-well.haoshenqi.topauth`
- `baseUrl` 含零宽字符/不间断空格 → 显示相同、比对不等
- 某个调用点传了完整 URL 或空 path
- 请求实际走了别的域名（后续新增接口时最易发生）

这解释了为什么排查会反复回到「再去后台确认一遍」。

## 3. 改法

1. `rawRequest` 内先算 `const url = CONFIG.baseUrl + options.path;`，
   `wx.request`、`console.error`、`describeNetworkError` 三处共用同一个值——**只算一次**，
   避免「日志里一个、发出去另一个」。
2. 新增 `hostOf(url)`：去协议、去路径、去查询串，**保留端口**。
   端口保留是有意的：白名单不接受端口，若 URL 真带端口，提示必须原样暴露，
   否则又会变成一个看起来对的域名。
3. 白名单文案改为三段式：

   ```
   请求域名未配置白名单（当前 AppID wx…）：请在小程序后台「开发管理 → 开发设置 → 服务器域名」
   为这个 AppID 添加 <host>｜实际请求 <完整 URL>｜微信原文 <errMsg>
   ```

   被拦域名取自**真实 URL**（`hostOf(url)`），取不到才回退 `CONFIG.baseUrl`。
4. `chatStream` 的 SSE 请求同样抽出 `chatUrl`，日志与文案一并带上。

## 4. 兼容性

- 不改请求行为、不改重试逻辑、不改登录流程，只改失败时的可见信息。
- 保留 R277（errMsg 不丢、白名单单独识别、兜底带原文）与 R281（文案带运行时 AppID）
  的全部约定；两套锁未改动，仍通过。
- 开发版重新编译即可生效，**不需要重新上传体验版**。

## 5. 验证

- `tests/test_r282_requrl.py` 6 例：URL 只算一次并复用、日志打 URL 而非 path、
  文案含「实际请求」「微信原文」、两处调用点都传 url、`hostOf` 行为、文案体内含 URL。
- 与 R277（4 例）、R281（3 例）合计 **13 passed**。
- `hostOf` 经 Node 实测：`https://moon-well.haoshenqi.top/auth/wx/login` → `moon-well.haoshenqi.top`；
  `https://a.b:8443/x?y=1` → `a.b:8443`；`''` / `null` → `''`。
- **未真机**：本机无微信开发者工具，需在开发版重编译后观察新文案。

## 6. 遗留

根因尚未定位。下一次报错时，屏幕上会直接给出「实际请求的完整 URL」与「微信原文」：

- 若 URL 与预期一致 → 问题在微信侧对该域名的运行时校验（备案回查、白名单快照），
  需要平台侧或时间解决；
- 若 URL 不一致 → 立刻能看出是哪一段拼错，属于代码问题，可直接修。

这条改动不解决故障，但把「猜」这一步从流程里去掉了。
