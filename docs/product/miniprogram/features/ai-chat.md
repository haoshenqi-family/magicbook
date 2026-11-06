# AI 伴读通用对话 · 实现说明（L3）

> 读者：要改这个功能的人。只写「实现方式 + 边界条件」。
> 契约见 [L2 接口说明](../interface.md)，本次怎么实现见
> [R280 LLD](../../../project/iterations/2026-11-wx-ai-chat/r280-miniprogram-ai-chat/lld.md)。

## 1. 页面与状态

- `pages/chat/chat.*`：`scroll-view` 消息列表 + 底部输入栏的三段 flex 布局；
  欢迎语与三个快捷问题在 `messages` 为空时展示，点快捷问题等价于填入并立即发送。
- 消息用自增 `seq` 作 `wx:key` 的 `id`，`scrollTo` 指向 `msg-<id>` 实现跟随出字滚动。
- `patchMessage` 用 `messages[index].field` 的路径式 `setData` 只更新一个气泡的一个字段，
  避免每个 `delta` 都把整段消息数组重新传一遍（流式场景每秒可达数十次）。
- `sending` 期间禁止再次发送与「新会话」；`onUnload` 调 `task.abort()` 掐断流，
  防止后台继续给已卸载页面 `setData`。

## 2. SSE 通道（`utils/api.js` 的 `chatStream`）

小程序没有 `fetch` / `EventSource`，`wx.request` 是唯一能读流的入口：

- `enableChunked: true` + `RequestTask.onChunkReceived`，`responseType: 'arraybuffer'`；
  低版本基础库没有 `onChunkReceived` 时回落 `success` 里的完整响应体（`receivedChunks` 判定）。
- **UTF-8 跨块解码**：`decodeUtf8(bytes, carry)` 逐码点解，凑不齐的字节留进 `carry` 给下一块。
  一个汉字 3 字节、emoji 4 字节，完全可能被 TCP 分块切开；直接 `String.fromCharCode` 会出乱码。
  坏字节用 U+FFFD 兜住，不让一个片段毁掉整段回答。
- **分帧**：`buffer.replace(/\r\n/g, '\n')` 归一后按 `\n\n` 切帧；`parseSseBlock` 读
  `event:` 与 `data:` 行，JSON 解析失败时回落裸文本 `delta`（兼容旧流）。
  结尾用 `drain(true)` 冲刷没有以双换行收尾的最后一帧。
- **401 只在连接阶段重试一次**：`refreshToken()` 成功后整条请求重发。流一旦开始就不能重放，
  否则已发出的 `delta` 会重复出字、重复计费。
- 错误文案保留 `wx.request` 的原始 `errMsg`（白名单 / 超时 / SSL 三类分开，见 `describeNetworkError`，
  R281 起白名单分支带运行时 AppID）；`console.error` 同步留痕以便体验版 vConsole 排查。
- `chatStream` 返回 `{ abort() }` 而不是裸 `RequestTask`，页面只依赖这一个能力；
  401 重试导致 `task` 被替换时 `abort()` 仍指向当前那一条。

## 3. 契约与隐私边界

- 请求体固定带 `scene: 'general'` 与 `skipMemoryExtract: true`，**不带任何书籍 / 网页上下文字段**。
  服务端（moon-well R243）据此加载 `agent-chat-system-general` 并剔除三个书页工具。
- `skipMemoryExtract: true` 只关「对话结束后的自动长期记忆抽取」；模型按用户明确要求调用
  `save_memory` 仍可写记忆，学情计数也不受该开关影响。
- `final.conversationId` 写入 `mb.chat.conversationId`；「新会话」只清本地 id 与界面消息，
  不删服务端历史——删历史需要有服务端接口与二次确认，不能靠清缓存伪装。
- 工具轨迹不渲染，`audio` 事件不自动播放：小程序前后台切换频繁，自动出声会打扰用户。

## 4. 与生词本下掉有关的迁移

- `pages/notebook/*` 已删除，`app.json` 的页面清单与 tabBar 第二项换成 `pages/chat/chat`。
  R283 起该 tab 的 `text` 由「伴读」改为「AI」——只改标签，页面路径、标题与功能名不动。
- 原挂在生词本页的「微信临时账号」提示条迁到「我」页（`pages/stats/stats.wxml`），
  `.shadow-tip` / `.shadow-link` 样式从 `notebook.wxss` 迁到 `app.wxss`——页面删了，
  提示不能跟着一起消失。
- 登录页 / 账号页 / 词汇量测试页的文案统一改为「网页端生词本」「学习记录」，
  避免小程序里出现已经不存在的入口。
- `tests/test_r272_account.py` 与 `tests/test_r275_home_profile.py` 的静态锁按新落位更新；
  新增 `tests/test_r280_ai_chat.py` 同时用 Node 实测跨块 UTF-8 解码与 SSE 分帧。

## 5. 已知边界 / 待真机验收

- **未真机验证 `enableChunked` / `onChunkReceived`**：体验版 `1.0.1` 已于 2026-11-05
  重传（R283 改 tab 文案；本机装有微信开发者工具，CLI 服务端口 13564），
  但当前证据仍只有静态锁、
  `node --check` 与 Node 侧的解码/分帧实测。真机需实测首字到达、中文不乱码、
  切后台再回来的流是否续得上。
- **合法域名按 AppID 存**：新号要在小程序后台重新加 `https://moon-well.haoshenqi.top`，
  并且 `request 合法域名` 与 `socket` 无关；开发者工具勾「不校验合法域名」只影响开发版。
- **180s 上限**：`chatTimeout` 是给长回答留的窗口，超时后 `wx.request` 走 `fail`，
  页面按网络错误提示，不自动重发。
- **通用对话不展示用量**：`final.usage` 目前只落服务端，界面不显示 token 数（与网页端 R232 口径一致）。
