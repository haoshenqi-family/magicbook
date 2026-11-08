# 回应归档 · R280–R281（2026-11-04 ～ 2026-11-05）

> 2026-11-08 R290 写入触发轮转搬移：写入前窗口已有 11 节（并行会话累积），
> 本次连同新增 R290 一并压回 10 节，故把最旧两节 R281、R280 原样搬入本文件。
> 只搬移原文，不总结、不改写、不改编号。

---

## R281 · 报错要自己说清「是哪个 AppID 在跑」（2026-11-04）

**对 R281 的回应**：后台白名单配了、代码 appid 也是正式号，体验版仍报「请求域名未配置白名单」。

- **先确认事实**：代码里（主检出 `miniprogram/project.config.json` 与 develop）都是
  `wx7b31b435be6beae3`；开发者工具的项目记录读出来也是 `wx7b31b435be6beae3`。
  所以「代码用哪个 appid」这个问题本身是确定的，卡住的是另一件事——**白名单是按 AppID 存的，
  而代码里的 appid 不等于这个安装包上传时用的 appid**。改完文件没重新上传，或工具里项目还是旧号
  就上传了，都会出现「我明明配了」的错觉。
- **证据**：11-03 15:39 开发者工具曾把 `project.config.json` 改回旧测试号
  （`wxd511f98508dc9cee`），当时被我 stash 了。说明工具的项目 AppID 与文件内容会互相覆盖，
  「文件是对的」不等于「包里是对的」。
- **改法**：`runtimeAppId()` 从 `wx.getAccountInfoSync().miniProgram.appId` 取运行时 AppID
  （基础库 2.11.2+，取不到就容错返回空串，不影响请求逻辑），白名单报错直接写成
  「当前 AppID wx…：请为这个 AppID 添加 moon-well.haoshenqi.top」，`console.error` 同步带 appid。
  这样下一次报错会自己指认嫌疑人，不用再靠猜。
- **验证**：`tests/test_r281_runtime_appid.py` 3 例 + R277 的 4 例 → **7 passed**；`node --check` 通过。
  **未真机**：这条要重新上传体验版才看得到效果。

**台账总结**：`requests.md` 第 281 条本处回填；`response.md` 写入前 10 节，本次压回 10 节，
最旧一节 R269（顶栏信息架构收敛）原样搬入 `response-archive/response-R269.md` 并登记索引。

## R280 · 小程序接入 AI 伴读通用对话，生词本页下掉（2026-11-05）

**对 R280 的回应**：用户原话「微信小程序接入AI伴读（对话）功能，加载通用对话prompt。生词本功能下掉。」
三个口径先问清楚才动手：现网**没有**名为「通用对话」的 prompt（只有书内 `agent-chat-system`
与网页 `agent-chat-system-web`），用户拍板新建；「下掉」是删页面换 tab；对话复用现网 SSE。

- **为什么不能复用那两套 prompt**：书内模板要 `bookTitle` / `chapter` / `pageContext`，网页模板要
  「当前页面正文摘录」——小程序里既没有书也没有网页，套上去模型只能凭空编一个书名和一段页面原文。
  用户要的「通用对话」是第三种场景，所以新开 `agent-chat-system-general`（moon-well R243），
  正文明确「不假设用户手边有文本、不提书名章节页码」，并剔除批注 / 段落译文这类依赖书页的工具。
- **`scene` 是显式声明，不是靠 `bookId` 猜**：网页 Buddy 与 magiclens 也传 `bookId=null`，
  若把 null 当通用，会把网页场景一起改坏。故 `scene=general` 优先于老判定，空值 / 未知值原样回落，
  老客户端零改动。
- **小程序没有 fetch/EventSource**：走 `wx.request` 的 `enableChunked + onChunkReceived`。
  这里最容易翻车的是 UTF-8——分片按 TCP 边界切，一个汉字 3 字节、emoji 4 字节完全可能被切开，
  直接转会满屏乱码。所以自己写 `decodeUtf8(bytes, carry)`，凑不齐的字节留到下一块；
  再用 `\n\n` 分帧解析 `event:` / `data:`。静态锁里用 Node 故意切断汉字字节做实测，
  不只是 grep 代码里有没有函数名。
- **401 只在流开始前重试一次**：流一旦开始就回滚不了已发的 `delta`，重放会重复出字、重复计费。
  其余失败保留 `wx.request` 原始 `errMsg`（白名单 / 超时 / SSL 分开说），不抹成「请检查网络」。
- **删页面不能顺手删掉功能**：生词本页没了，挂在它上面的「微信临时账号」提示条也就没了——
  而这条提示是唯一告诉用户「换手机就找不回来」的地方。故迁到「我」页，`.shadow-tip` 样式迁到
  `app.wxss`；登录/账号/测试页文案统一改「网页端生词本」，避免指向一个不存在的入口。
- **Nacos 发布口径（上一轮卡住的点，已查清）**：公网 `nacos.haoshenqi.top` 是 v3 **console** 侧，
  `/v3/console/ai/prompt` 的 OPTIONS 返回 `allow=DELETE,OPTIONS`，POST 报
  `Request method 'POST' is not supported`；`publish` / `force-publish` 接 POST，`version` / `list` 只读
  ——**console 根本没有 create 写入口**。create 只存在于内网 8848 的 admin API
  （`/nacos/v3/admin/ai/prompt`，与仓内 `NacosPromptAdminClient` 同源）。所以不再从公网强写，
  按设计交给后端部署期的 `NacosPromptBootstrap` 自动 `create + publish`，上线后回读 online 版本与正文。
  **上线实况（2026-11-05 回填）**：push `develop` 自动触发 fnOS 发版链，10:13:04 后端部署 SUCCESS
  （blue→green healthy）；bootstrap create 成功但 publish 被 Nacos 审批流水线拦下
  `20002 Pipeline not approved: 1.0.0`，稍后手动 `publish` 返回 `code=0`，
  回读 `latestVersion=1.0.0` / `onlineCnt=1`、在线正文 851 字符与代码模板逐字一致。
  runtime 首次 `findTemplate` 拉在线模板并订阅推送，无需重启。
- **验证**：拉齐 R282 基线后小程序 R271–R282 静态锁 **52 passed**；`node --check` / JSON 解析通过。
  后端 R243 定向 + 上下文测试 **8 passed / BUILD SUCCESS**。全量 `pytest tests/` 在本机被
  SIGKILL，按开发态闸门只跑受影响子集，未冒充「全量通过」。
  **体验版已上传（2026-11-05 11:35）**：用户先在开发者工具「设置 → 安全设置」开启服务端口
  （端口 **13564**、CLI 访问令牌留空），`cli islogin` 返回 `{"login":true}`，随后
  `cli upload --project <主检出>/miniprogram -v 1.0.0 --port 13564` 成功，
  TOTAL **65.3 KB / 66,840 Byte**。两点留痕：① 上传源用主检出 `develop@6db0aba2`
  （含 R280 + R282），worktree 当时落后 10 个提交、缺 R282 的请求 URL 诊断；
  ② 带 `--info-output` 会触发 IDE `code 10 / 17 二维码输出路径无效或不存在`，
  去掉该参数即成功。`cli upload` 产生「开发版本」，体验版仍需后台「版本管理」指定。
  **真机 `enableChunked` 表现仍未验**，是唯一剩余验收待办。
- **部署顺序是硬的**：先 moon-well R243，再发小程序体验版。老后端不认 `scene` 会把通用对话
  落到网页伴读 prompt，用户会看到「当前页面正文摘录」这种小程序里不存在的东西。
- **状态**：**已上线待验收**（worktree `../magicbook-r280-ai-chat`，分支 `feat/r280-ai-chat`，
  已 merge 并 push `origin/develop`；后端 moon-well R243 于 10:13 上线、Nacos 新 prompt 在线；
  小程序体验版 `1.0.0` 于 11:35 上传成功，待后台设为体验版并真机验收。
  真机验收通过后本条才置 Completed、worktree 才清理）。
- **状态回写**：PingCode idea `MB-239`（`xB0tmxqa`，<https://haoshenqi.pingcode.com/ship/ideas/xB0tmxqa>）。
  本轮占号后漏建 idea，按 `ops/AGENTS.md`「状态必回写」于开发完成待验收阶段补建并置
  `In progress`；**验收通过后才置 `Completed`**，worktree 才清理。moon-well R243 是同源后端，
  按「后端跟随 magicbook、不单独建载体」共用这一条，不另建。
- **冲突记录**：开工后 `origin/develop` 前进了 R281（同改 `utils/api.js`），已 `git merge origin/develop`
  自动合并，两处函数（`runtimeAppId` 与 `chatStream`）共存、静态锁 46 例复跑通过，未撞号。
  `requests.md` 第 280 条占号标题原误写「R279」（R279 已被投稿书籍需求占用），本次按实际编号更正文字，
  编号本身不动。

**台账总结**：`requests.md` 第 280 条本处回填（含三口径、契约、部署顺序与验证结果）；
`response.md` 写入前 10 节，本次压回 10 节，最旧一节 R270（阅读器 bookUrl 大小写致 /show 404）
原样搬入 `response-archive/response-R270.md` 并在顶部登记索引。
