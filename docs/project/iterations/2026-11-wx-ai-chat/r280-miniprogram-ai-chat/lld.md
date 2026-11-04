# R280 小程序接入 AI 伴读（通用对话）· LLD

状态：开发中（代码完成、定向测试全绿、本地 merge 待 push 待真机验收；上线后回填「已上线」）

> 本次怎么实现。需求基线见 [`../../../../product/miniprogram/requirements.md`](../../../../product/miniprogram/requirements.md)，
> 静态契约见 [`../../../../product/miniprogram/interface.md`](../../../../product/miniprogram/interface.md)，
> 实现与边界见 [`../../../../product/miniprogram/features/ai-chat.md`](../../../../product/miniprogram/features/ai-chat.md)。
> 跨仓同源：**moon-well R243**（`scene=general` + `agent-chat-system-general`），
> 见 moon-well `docs/project/iterations/2026-11-wx-ai-chat/r243-general-chat/lld.md`。

## 1. 目标与不做什么

- 目标：小程序第二个 tab 换成「伴读」，可发起**不绑定书页**的 SSE 流式对话；生词本页整体下掉。
- 不做：不新增后端端点；不改网页端 / magiclens 的伴读行为；不动生词本数据面；
  不在小程序里做书内问答；不做语音输入 / 朗读（R227 是全站网页能力，未下沉小程序）。

## 2. 用户拍板的三个口径（2026-11-04）

| 分歧 | 结论 |
| --- | --- |
| 现网没有「通用对话」prompt（只有书内 / 网页两套） | 新建 `agent-chat-system-general`，不复用、不改老模板 |
| 「生词本下掉」的程度 | 删 `pages/notebook/*` 并把 tab 换成「伴读」，不是隐藏入口 |
| 对话形态 | 复用 `POST /ai/agent/chat` 的 SSE 流式，不新增接口 |

## 3. 架构与时序

```
微信小程序 pages/chat/chat.js
   │ api.chatStream({ message, conversationId, scene:'general', skipMemoryExtract:true })
   ▼
utils/api.js  wx.request(enableChunked, responseType:arraybuffer, timeout:180000)
   │ onChunkReceived(bytes) → decodeUtf8(carry) → SSE \n\n 分帧 → parseSseBlock
   ▼  delta / tool_call / final / error
页面 setData（单个气泡字段）→ 逐字出字 / 状态提示 / 存 conversationId
   ▲
moon-well POST /ai/agent/chat（SSE，AgentChatController）
   └─ scene=general → agent-chat-system-general + 收窄工具白名单
```

关键取舍：

1. **直连后端，不经 magicbook Python 代理**：小程序已有 `baseUrl` 与 JWT 刷新链，
   再绕一层代理只会多一个 SSE 转发点和一处故障面。
2. **`wx.request` 分块而非轮询 / 短连接**：现网只有 SSE，改成非流式接口是后端大改；
   小程序基础库支持 `enableChunked` + `onChunkReceived`，语义与网页 `fetch` 读流对齐。
3. **`scene` 用可空字符串而非布尔 / 枚举**：老客户端不传这个字段，必须完全向后兼容；
   未知取值回落既有 `bookId` 分支，前端拼错不至于 400。
4. **UTF-8 解码自己实现**：`arraybuffer` 分片不保证码点边界，
   `carry` 是唯一能同时处理中文与 emoji 的办法；Node 侧用故意切断汉字字节的用例钉住。

## 4. 改动清单

| 文件 | 动作 | 要点 |
| --- | --- | --- |
| `miniprogram/app.json` | 改 | `pages/notebook/notebook` → `pages/chat/chat`；tab 文案「生词本」→「伴读」 |
| `miniprogram/pages/chat/chat.{js,json,wxml,wxss}` | 新增 | 欢迎语 / 快捷问题 / 气泡 / 输入栏 / 新会话；`onUnload` abort |
| `miniprogram/pages/notebook/*` | 删除 | 4 个文件，`git rm` |
| `miniprogram/utils/api.js` | 改 | `decodeUtf8` / `parseSseBlock` / `chatStream` 导出；401 单次刷新；错误透传 |
| `miniprogram/config.js` | 改 | `chatTimeout: 180000` |
| `miniprogram/pages/stats/stats.wxml` | 改 | 临时账号提示条从被删的生词本页迁来 |
| `miniprogram/app.wxss` | 改 | `.shadow-tip` / `.shadow-link` 从 `notebook.wxss` 迁来 |
| `miniprogram/pages/login/login.wxml`、`account/*`、`test/*` | 改 | 文案改「网页端生词本」「学习记录」 |
| `miniprogram/project.config.json`、`miniprogram/README.md` | 改 | 工程描述 / 手册重写，写明契约与部署顺序 |
| `tests/test_r280_ai_chat.py` | 新增 | 结构 / 契约 / 文案 / Node 实测解码与分帧 |
| `tests/test_r272_account.py`、`test_r275_home_profile.py` | 改 | 静态锁随页面迁移与 tab 变化更新 |

## 5. 异常与边界

| 场景 | 处理 |
| --- | --- |
| 401 / 403 | 仅流未开始时刷新 token 重试一次；流已开始不重放（重复出字 + 重复计费） |
| HTTP ≥ 400 | 解析 `message` 提示；解析失败回落 `请求失败（HTTP <code>）` |
| `wx.request` fail | 保留 `errMsg`；白名单（带运行时 AppID，R281）/ 超时 / SSL 三类分开 |
| SSE `error` 事件或收尾无正文 | 气泡显示「这次没有收到回复，请重试」，不静默留空白 |
| 低版本基础库无 `onChunkReceived` | 回落 `success` 里的完整响应体，仍能出完整回答（非流式） |
| 中文 / emoji 跨 chunk | `carry` 保留未凑齐字节；坏字节 U+FFFD 兜底 |
| 页面卸载 / 切后台 | `abort()` 掐断流，不给已卸载页面 `setData` |
| 「新会话」 | 只清本地 `mb.chat.conversationId` 与界面消息，不删服务端历史 |

## 6. 部署与现网验证

1. **先上线 moon-well R243**：`scene` 分支 + 新 prompt。
   新 key 在现网缺失时由 `NacosPromptBootstrap` 启动自检 `create + publish`（已在线则 skip，
   在线版本是唯一事实来源）；上线后回读 `GET /v3/console/ai/prompt/list` 与
   `GET /v3/console/ai/prompt/version` 确认 `agent-chat-system-general@1.0.0` 在线。
   - **本机主动发布不可用**：公网 `nacos.haoshenqi.top` 是 v3 **console** 侧，
     实测 `/v3/console/ai/prompt` 只接 `DELETE`（OPTIONS allow=DELETE），
     `publish` / `force-publish` 接 POST，**没有 create 写入口**；
     create 只存在于内网 8848 的 **admin** API（`/nacos/v3/admin/ai/prompt`，
     与 `NacosPromptAdminClient` 同源）。故不绕过 console 强写，交给部署期 bootstrap。
2. **再上传小程序体验版**：旧后端不认 `scene` 会按 `bookId == null` 落到网页伴读 prompt，
   出现「当前页面正文摘录」这类假上下文。
3. 新 AppID 的 **request 合法域名**需含 `https://moon-well.haoshenqi.top`（R281 报错已带运行时 AppID）。

## 7. 验证记录（2026-11-05）

- 小程序静态锁：R271–R281 共 **46 passed**；全量 `pytest tests/` 在本机被 SIGKILL（Flask 集成用例占资源），
  按开发态闸门只跑本次新增 / 受影响用例。
- `node --check`：`api.js` / `chat.js` / `config.js` 通过；`app.json` / `chat.json` / `project.config.json` JSON 解析通过。
- 后端（moon-well R243）：`AgentChatSceneResolverTest` + `AgentChatGeneralSceneIntegrationTest`
  + `MagicbookApplicationTests` 共 **8 passed，BUILD SUCCESS**。
- **未做**：微信开发者工具真机 / 体验版验证——本机没有该工具，
  `enableChunked` 与 `onChunkReceived` 的实际表现列为验收待办。

## 8. 里程碑回填

| 阶段 | 状态 |
| --- | --- |
| 设计 | 已完成（三口径经用户确认） |
| 开发 | 已完成（两仓源码 + 静态锁 + 定向单测） |
| 本地 merge / push | 本地 merge 完成，**未 push、未部署**（等用户 `ok push`） |
| 上线 / 真机验收 | 待办 |
