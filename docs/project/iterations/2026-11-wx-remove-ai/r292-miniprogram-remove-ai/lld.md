# R292 小程序移除 AI 伴读能力（微信上架合规）· LLD

状态：开发完成待验收（代码与静态锁完成并 merge `develop`；**尚未用微信开发者工具编译、
未上传新代码包、未提审**——上传与提审是对外动作，等用户下令）

> 本次怎么实现。需求基线见 [`../../../../product/miniprogram/requirements.md`](../../../../product/miniprogram/requirements.md) §R292，
> 现行契约见 [`../../../../product/miniprogram/interface.md`](../../../../product/miniprogram/interface.md)。
> 被移除功能的设计与实现记录：[R280 LLD](../../2026-11-wx-ai-chat/r280-miniprogram-ai-chat/lld.md)、
> [R283 LLD](../../2026-11-wx-ai-chat/r283-tab-ai/lld.md)、
> [L3 ai-chat](../../../../product/miniprogram/features/ai-chat.md)（已标下线）。

## 1. 需求与范围

用户 2026-11-11 原话「移除小程序的AI能力，否则无法上架」。

小程序里的 AI 能力只有一处：R280 接入、R283 改名的「AI」tab（通用对话）。复习、词汇量测试、
学习数据、账号四块都不调用任何模型——复习卡的中文释义只读词条详解缓存，缺了就亮词面，
不会触发生成（R290）。所以范围就是把这一个功能从代码包里拿干净。

**取「删除」而不是「隐藏入口」**：审核面对的是上传的代码包，不只是界面。摘掉 tab 但留着
对话页与流式通道，包里仍有一整套 AI 对话实现，结论取决于审核是否扫到，不可控；
而留着它也没有任何用户价值。恢复成本很低——`git show 5a49872f:miniprogram/` 即可取回。

## 2. 改动清单

| 文件 | 改动 |
| --- | --- |
| `miniprogram/pages/chat/`（4 个文件） | 整目录删除 |
| `miniprogram/app.json` | `pages` 去掉 `pages/chat/chat`；`tabBar.list` 去掉「AI」项，剩「复习 / 词汇量 / 我」 |
| `miniprogram/utils/api.js` | 删除 `decodeUtf8`、`parseSseBlock`、`chatStream` 三个函数及其导出（432 → 241 行） |
| `miniprogram/config.js` | 删除 `chatTimeout`；注释去掉「AI 伴读 agent」 |
| `miniprogram/pages/login/login.wxml` | 品牌副标题改为「每日复习 · 词汇量测试 · 学习数据」 |
| `miniprogram/project.config.json` | `description` 去掉「AI 伴读」 |
| `miniprogram/sitemap.json` | `desc` 的模板残留文案改为本项目说明 |
| `miniprogram/README.md` | 删 AI 伴读章节，交代移除原因；顺手更正接口表里一个从未被调用的端点 |

`decodeUtf8` 与 `parseSseBlock` 只服务于 SSE，没有其他调用方，随 `chatStream` 一起删，
不留「以后也许有用」的死代码。`describeNetworkError` 等普通请求层的件不动。

## 3. 不改什么

- **moon-well**：`POST /ai/agent/chat`、`scene=general` 分支与 `agent-chat-system-general`
  prompt 全部保留。接口本就是网页端与扩展共用的；通用 prompt 没有消费者后留着无害，
  删它反而要动后端启动自检，与本次目的无关。
- **服务端会话历史**：小程序里产生的会话（`bookId=0` 站点会话）不删，仍可在网页端查看。
- **本地存储**：老版本写过的 `mb.chat.conversationId` 不做清理。它只是一个孤立的数字 id，
  没有代码再读它；为清它专门留一行带 `chat` 字样的代码不值得。
- **tabBar 三项**：微信要求 2–5 项，三项合规；页面顺序不变，默认仍落「复习」。

## 4. 测试

静态锁（`tests/`，小程序不进容器、无运行时测试环境）：

- **新增** `test_r292_miniprogram_remove_ai.py` 7 例：对话页目录与注册消失且底栏恰为三项；
  请求层无对话通道八个特征串、普通请求层的件仍在；**代码包全部 `.js/.json/.wxml/.wxss`
  不含 AI 相关字样**（`\bAI\b`、伴读、`/ai/`、`agent-chat` 等）；登录页与工程描述为三项；
  README 不把已删除的件写成现役；生词本页不复活（2 例，自 R280 测试迁入）。
- **删除** `test_r280_ai_chat.py`、`test_r283_tab_ai.py`：断言全部以对话页存在为前提
  （R283 那份还专门锁「页面标题必须叫 AI 伴读」），与本需求正相反。R280 里仍然成立的
  两条生词本锁已迁入 R292 测试文件。
- **修改** `test_r275_home_profile.py`（第二个 tab 断言改为词汇量测试）、
  `test_r282_requrl.py`（去掉对 SSE 调用点的断言）。

结果见 §5。另：全部 `.js` 过 `node --check`、全部 `.json` 过 `JSON.parse`。

## 5. 验证结果与未验证项

- 小程序相关 12 个测试文件合计 **57 passed**（开发态部分单测；全量未跑，本次不涉及 `cps/`）。
- **未验证**：没有用微信开发者工具编译，也没有真机运行。静态锁能保证的是「引用的页面都存在、
  JSON 合法、JS 语法正确、包里没有 AI 字样」，保证不了 WXML 渲染与 tabBar 三项的实际观感。

## 6. 上线步骤（需人工）

小程序不进镜像（`Dockerfile` 不 COPY、`cps/` 零引用），push `develop` 对网页服务没有行为变化。

1. 微信开发者工具导入 `magicbook/miniprogram`，编译，确认底栏三项、各页正常；
2. 上传新版本（版本号高于 `1.0.1`），在后台选为体验版真机过一遍；
3. 检查小程序后台的**名称 / 简介 / 服务类目 / 审核备注**里是否还有 AI 相关描述——
   这些不在代码仓里，代码改完不会自动变；
4. 提交审核。
