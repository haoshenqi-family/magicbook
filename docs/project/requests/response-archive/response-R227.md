# response 归档：R227（2026-10-25）

> 从 response.md 原样搬移（2026-10-28 R238 写入使窗口超 10 条，按「写入即检查」搬最早条目）。只搬移原文，未总结、未改写、未改编号。

## 2026-10-25（R227：Buddy 对话复用口语陪练语音能力——全站语音提问 + 每条回复手动朗读）

### R227（用户：「我想要 AI 伴读 Buddy 对话也可以复用 AI 口语陪练 陪练的语音能力。」）

- **任务定位**：需求（跨功能复用，不是缺陷）；**单仓交付**——moon-well 侧零改动，ASR 与 TTS 端点都已在线（R221 前端 / moon-well R212 后端）。
- **四问四答拍板（2026-10-25）**：① 范围＝**输入+朗读双向**（不是只做输入或只做朗读）；② 回复朗读＝**每条手动点「朗读本条」**（不自动播——回复普遍 800–2000 字，自动播既慢又按次扣费）；③ 用户语音＝**只转成文字**、不留可回放语音条（否则要给 `ai_message` 加音频字段 + 走 MinIO 上传，跨仓改动不划算）；④ 生效面＝**全站**（Buddy 自 R220 起是全站助手）。
- **复用面（先查后写，不是凭印象）**：`learning-voice.js`（WebAudio→16k wav→ASR，R158/R159/R160 三处坑都在里面）、`/ajax/learning/asr/transcribe`（登录鉴权、10MB、60s、不扣积分）、`/ajax/reading-tts`→moon-well `/tts/speak`（**1 积分/次含命中**、≤2000 字、65s）、`/ajax/reading-tts-cached`（只读缓存不计费）。**不复用**：录音上传/语音条（要改 `ai_message`）、教练回复的服务端同步合成（Buddy 是 SSE 流式，会把 `final` 拖长且长回复必撞 2000 字上限）。
- **三处不能照搬，各自有解**：① `learning-voice.js` 原硬依赖 `window.MBLearning`（`if (!MB) return;`），Buddy 面板在全站挂载、没有 learning-common → **依赖降级为「有则用、无则回退」**（`window.mbT` / `window.MBApi.csrfToken()` / `options.asrUrl`），学习页零改动；另补 `clearNode` 回退——缺 `MBLearning` 时 `MB.clear(select)` 会在设备下拉处直接 TypeError。② 朗读不能用 `<audio src=blob:>`：`media-src blob:` 目前只在阅读页/口语页放行，照搬要把 CSP 铺到全站，而 `test_non_reader_pages_still_block_blob_media` 正是拦这条的守卫 → **改走 Web Audio**（`fetch` 取字节 + `decodeAudioData`，受 `connect-src` 回退 `default-src 'self'` 约束，**不受 media-src 管辖**），`web.py` **一行未改**。③ 长回复撞 2000 字上限 → 分段 1800（空行→句末标点→硬切），顺序播放并在状态行显示「朗读中 n/m」。
- **顺带修掉一个既有静默故障**：伴读工具 `synthesize_tts` 的 `audio` SSE 事件原本也用 `new Audio(blob:)`，在非阅读页会被 CSP 拦掉且几乎没有可见提示（R220 把面板铺到全站之后就该暴露）。改成同一条 Web Audio 路径后，全站都能响。
- **缓存档位**：朗读**不带** `bookName`/`chapter`，让 moon-well 按「AI 临时语音」档（7 天清理）落盘，不把一次性回复写进书籍段落的永久缓存；与 `synthesize_tts` 的既有口径一致。
- **一处存量缺陷（本轮不擅自改）**：`ai_chat.js` 顶部的 `var mbT = window.mbT || identity` 在脚本载入时就被固定成恒等函数——`layout.html` 把 `i18n_seed.html` 排在 `ai_chat_panel.html` **之后**，所以面板既有动态文案实际上是英文。修法只有一行（改成调用时解析），但会让一批既有文案突然变中文，属可见行为变化，需单独一轮带验收。本轮新增文案改用本地 `t(id)`，词条手工进种子（生成器只扫 `mbT(`），并由新测试同时守种子/PO/MO。
- **测试**：新增 `tests/test_buddy_voice.py` 7 条（面板挂载与脚本顺序、录音模块解耦、转写不自动发送、朗读不带书籍上下文、朗读不用 blob 媒体、分段上限 <2000、`t()` 词条三处齐全）；定向回归 **117 passed / 0 failed**（buddy 两套 + 页面冒烟 + i18n 契约 + CSP + 阅读器 R226/R215 + 学习页静态 + common api + 引导）；`node --check` 两个 JS；`splitForSpeech` 另用 node 直跑边界（1900 字无标点→[1800,101,223]、纯中文 3000 字→2 段、空串→[]）。
- **真机验收未做（6 项）**：阅读页录音转写并编辑发送、首页同样可录可转（验证全站而非只在阅读页）、点朗读出声/再点停止、长回复两段连播、关抽屉即停、中文界面下按钮与状态行为中文。
- **文档四问**：能力→L1 `readme/companion.md` 增「说话提问」「朗读回复」；契约→无接口变化（复用既有代理，故未改 L2）；实现/边界→新建 L3 `companion/features/buddy-voice.md`；本次实现→`iterations/1.0/r227-buddy-voice/lld.md`（状态：开发完成待验收）。另按「模块无基线则补建」新建需求基线 `companion/requirements.md`（R227 起）。
- **台账与驻留**：R227 由 `claim.sh` 占号并 push（`a7eecd0c`，纯台账）；worktree `../magicbook-r227-buddy-voice`（分支 `feat/r227-buddy-voice`，基线 `origin/develop` `a7eecd0c`）已于 2026-10-26 用户确认收尾时删除（`worktree remove` + `branch -d`，删前仅清掉 `.pytest_cache/` 测试缓存），无残留、无未合并提交。
- **窗口**：写入前已有 10 节，按「写入即检查」把最早 R212 整节原样搬至 `response-archive/response-R212.md` 并登记索引，窗口保持 10。
- **总结**：requests.md 条目 227 已从占位回填；本条为回应。冲突记录：无撞号；唯一保留项是 `mbT` 冻结问题（存量、影响面大，另立一轮），不在本轮顺带改。
- **上线实况（2026-10-25 21:27）**：用户令「上线」→ 主检出 `develop` 上 `a7eecd0c..cb198e00` 快进合并并 push（17 files / +774）。fnOS 自动构建，约 35 秒后生产静态资源即为新版：`/static/js/ai_chat.js` 含 `decodeAudioData` 与 `ai-chat-speak`、`/static/js/learning-voice.js` 含 `window.MBLearning || {}` 且旧 `if (!MB) return` 已消失、`ai_chat.css` 含 `.ai-chat-mic`、`/login` 渲染出的 i18n 种子里有 `Read reply aloud`（顺带证明模板没被字典改动搞坏）。`/` 仍 302 → `/login?next=%2F`，与改动前一致。
- **补丁（同日 21:3x，计费拒绝要说人话）**：核账时发现「积分不足」的失败体是 HTTP 500 + `Result` 信封，原实现只看 `resp.ok` 就直接 `arrayBuffer()` 去 decode，用户会看到「解码失败」——把计费拒绝伪装成播放器坏了。`fetchSpeechBytes` 改为：成功且 `Content-Type` 是音频才解字节，否则读文本、取 `Result.message` 抛出（典型文案「积分不足，无法使用AI功能」）；新增第 8 条守卫钉住「失败分支必须走 `.text()`」。属同一需求内的缺陷修补，不另占号。
- **计费口径变更（2026-10-25 晚，承接 moon-well R213）**：用户指正「1 积分/段只针对缓存命中，真实生成走正常计费，TTS/ASR 都要收，参考阿里云标价」。moon-well 侧据此改成：**命中 1 积分/段、首次生成按 50 字符/积分**（cosyvoice-v3-flash 1 元/万字符 ×2）、**ASR 22 秒/积分且最少 1 积分**，并修掉「真实合成双扣」「预检在调用之后」「ASR 实际从未收费」三处缺陷。magicbook 侧代码零改动（费率由 `/credit/billing` 下发、朗读走既有代理），只更新 L1/L3/LLD 的计费描述；**用户可见变化**：一条 1800 字新回复首读约 36 积分、重听 1 积分，一句语音提问约 1 积分，整本任务面板的朗读预估因费率真源变化会放大约 20 倍（预期行为，非缺陷）。
