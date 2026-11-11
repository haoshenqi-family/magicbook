## R282 · 报错必须说出「实际请求的完整 URL」（2026-11-05）

**对 R282 的回应**：白名单三处都对（后台、「项目配置 → 域名信息」、工具本地缓存里
`RequestDomain` 含 `https://moon-well.haoshenqi.top`，appid 为正式号、`isTrusted: true`），
服务端也实测可达、无跳转、带小程序 UA 返回业务 JSON，可请求仍报 `url not in domain list`。

- **这一轮没能定位根因，但拿掉了「靠猜」的那部分。** 之前所有排查都建立在我们自己的提示上，
  而那条提示只打印 `CONFIG.baseUrl`——**它永远显示那个「本该正确」的域名**。于是无论真实原因
  是什么（路径拼接错、baseUrl 带隐藏字符、请求发往别处），用户看到的都是「添加
  moon-well.haoshenqi.top」，看起来完全正确，人就被引去反复确认后台。这是提示的设计缺陷，
  不是运气差。
- **改法**：`rawRequest` 先把 `const url` 算出来，`wx.request`、日志、错误文案共用同一个值；
  白名单文案变成三段——「为这个 AppID 添加 `<被拦域名>`｜实际请求 `<完整 URL>`｜微信原文
  `<errMsg>`」。被拦域名从**真实 URL** 里取（`hostOf()`），不再从 `CONFIG.baseUrl` 取，
  这样两者不一致才会暴露出来。SSE 的 `chatStream` 同步带上 `chatUrl`。
- **`hostOf()` 保留端口**：白名单不接受端口，若 URL 真带了端口，提示里必须原样显示，
  否则又会变成一个「看起来对」的域名。
- **本次已排除**：开发者工具项目记录与缓存（单条记录、appid 正确、域名齐全）、
  `project.config.json` 的 `appid`、`baseUrl` 的字符构成（纯 ASCII 31 字符）、所有请求路径
  均以 `/` 开头、服务端 301/302（四个路径全部直连）、网关对小程序 UA 的拦截。
- **验证**：`tests/test_r282_requrl.py` 6 例（URL 只算一次并复用、日志打 URL 不打 path、
  文案含真实 URL 与 errMsg 原文、两处调用点都传 url、`hostOf` 行为）+ R277/R281 既有锁，
  合计 **13 passed**；`hostOf` 经 Node 实测含 null/空串/带端口。
- **状态**：**已上线**（`d83cf2ae` 合入 develop 并推送）。用户于 2026-11-05 11:22 确认开发调试恢复。
  **根因未确证**——白名单三处与运行时 AppID 全部正确、服务端无跳转，恢复也可能来自工具侧配置刷新；
  这条改动本身只负责「下次报错能自证」，不解决故障。

**台账总结**：`requests.md` 第 282 条本处回填；`response.md` 写入前 9 节（上一轮已归档 R272 之外的
旧条目），本次回到 10 节，最旧一节 R272（小程序账号体系）原样搬入
`response-archive/response-R272.md` 并登记索引。
