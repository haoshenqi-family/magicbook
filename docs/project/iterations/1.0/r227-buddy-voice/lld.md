# R227 Buddy 对话复用口语陪练语音能力 · LLD

> 状态：**已上线、已收尾**（2026-10-25 开发并上线；2026-10-26 用户确认收尾，worktree 与分支已删除）
> 工作项：R227（magicbook 单仓交付）· 迭代 1.0 · 目录 `docs/project/iterations/1.0/r227-buddy-voice/`
> 用户原话：「我想要 AI 伴读 Buddy 对话也可以复用 AI 口语陪练陪练的语音能力。」
> 第二轮拍板（四问四答）：① 范围＝**输入+朗读双向**；② 回复朗读＝**每条手动点**（不自动播）；③ 用户语音＝**只转成文字**，不留可回放语音条；④ 生效面＝**全站**。

## 1. 承接与范围

口语陪练（R221 前端 / moon-well R212 后端）已经有一套跑通的语音链路。本次不是再造一套，而是把其中**可复用的两段**接到 Buddy 面板上：

| 复用 | 不复用（及原因） |
| --- | --- |
| `learning-voice.js` 录音→16k wav→ASR 转写 | 录音上传 MinIO + 语音条回放：`ai_message` 无音频字段，为用户一句口头提问加一列跨仓改动不划算（本轮拍板只转文字） |
| `/ajax/learning/asr/transcribe`（登录鉴权、10MB、60s） | 教练回复**服务端同步合成 TTS**：Buddy 是 SSE 流式，服务端合成会把 `final` 拖长，且长回复整段合成必然撞 2000 字上限 |
| `/ajax/reading-tts`（`/tts/speak`，1 积分/次）与 `/ajax/reading-tts-cached` | 口语页的语音条 UI（气泡+转文字折叠）：Buddy 消息是 markdown 富文本，套语音气泡会同时压掉正文 |

**非目标**：按住说话 / 实时全双工语音对话 / 音素级发音评分（沿用 R221 的非目标口径）；不改伴读提示词、不改 `ai_message` 表结构、不新增 moon-well 端点。

## 2. 三处「不能直接照搬」与对应决策

### D1 · 录音模块不能硬依赖学习中枢

`learning-voice.js` 原本第一行就是 `var MB = window.MBLearning; if (!MB) return;`，而 Buddy 面板自 R220 起在 `layout.html` 全站挂载，那里既没有 `learning-common.js` 也没有 `window.learningUrls`。照搬＝除了阅读页和学习页，麦克风在所有站内页静默失效（按钮在、点了没反应，无任何报错）。

**做法**：依赖降级为「有则用、无则回退」，学习页零改动——
- 取词：`MB.mbT` → `window.mbT`（`i18n_seed` 全站）→ 恒等；
- CSRF：`MB.csrfToken()` → `window.MBApi.csrfToken()`（`common/api.js` 全站载入）；
- 设备下拉清空：`MB.clear` → 本地 `clearNode`（缺 `MBLearning` 时 `MB.clear(select)` 会直接 TypeError）；
- 转写地址：`options.asrUrl` → `window.learningUrls.asrTranscribe` → 字面量 `/ajax/learning/asr/transcribe`。

**Why 不另写一个 buddy-voice.js**：R158（同步段抛错必须复位按钮）、R159（全静音录音判定）、R160（站内设备选择）三处坑都沉淀在这 200 行里，复制一份等于把坑一起复制，而且以后修一处漏一处。

### D2 · 朗读不能用 `<audio src=blob:>`

口语页与阅读页播放 TTS 都用 `URL.createObjectURL(blob)`，因此 CSP 必须为这两类页面显式声明 `media-src 'self' blob:`（R181 / R221）。Buddy 面板是全站的：照搬就得把 `media-src blob:` 铺到所有 HTML 页面，等于为了一个播放器把安全面整体放宽，而 `tests/test_csp_media.py` 的 `test_non_reader_pages_still_block_blob_media` 正是拦这条的守卫。

**做法**：`fetch` 取字节 → `AudioContext.decodeAudioData` → `AudioBufferSourceNode` 播放。
- 字节来自 `fetch`，受 `connect-src`（回退 `default-src`，含 `'self'`）约束，**不受 `media-src` 管辖**，播放能力与页面无关；
- 顺带修掉一个既有静默故障：伴读工具 `synthesize_tts` 的 `audio` SSE 事件在非阅读页原本会被 CSP 拦掉（`new Audio(blob:)` 被拒，`play()` 的 reject 只在部分浏览器可见），现在同一条 Web Audio 路径，全站都能响；
- `web.py` 的 CSP 一行未改。

### D3 · 朗读走计费端点，但不带书籍上下文

`/ajax/reading-tts` → moon-well `/tts/speak`：**命中缓存 1 积分/段、首次生成按字符**（50 字符 = 1 积分，moon-well R213 口径），单次 ≤2000 字。moon-well 的缓存分级以「调用方是否携带 `bookName`/`chapter`」判档：带＝书籍段落、MinIO 永久；不带＝AI 临时语音、7 天清理。

**做法**：朗读一律**不带** `bookName`/`chapter`。AI 回复是一次性文本，落永久档只会污染书籍段落缓存。代价是同一段回复在 7 天后重播会重新计费——可接受，且与既有 `synthesize_tts` 的口径一致。

### D4 · 长回复必须分段播放

伴读回复常见 800–2000+ 字，直接送 `/tts/speak` 会被 400（代理与 moon-well 双端都校验 2000 字）。

**做法**：`SPEECH_SEGMENT_MAX = 1800`，先按空行分段，段仍超长再按句末标点（中英文标点都认）切，最后才硬切；逐段合成、顺序播放，状态行显示「朗读中 2/3」。分段意味着**一段一句积分**：2000 字回复 ≈ 2 次计费，用户点之前看到的是显式按钮，点之后看到的是分段进度，不做静默扣费。

### D5 · 新增文案必须调用时取词

`ai_chat.js` 顶部的 `var mbT = window.mbT || identity;` 在脚本载入时就固定成恒等函数——`layout.html` 把 `i18n_seed.html` 排在 `ai_chat_panel.html` **之后**。因此 Buddy 面板的既有动态文案（「思考中」「新会话就绪」等）实际上恒回英文，这是一个**存量缺陷**，影响全部既有文案、需要单独一轮改并验收，本轮不动。

**做法**：本轮新增文案走本地 `t(id)`，调用时读 `window.mbT`，中文立刻生效；词条手工登记进 `i18n_seed.html`（生成器只扫 `mbT(` 字面量，扫不到 `t(`），并由 `tests/test_buddy_voice.py::test_new_voice_strings_are_seeded_and_translated` 同时守种子 / PO / 编译后的 MO 三处。

## 3. 实现落点

| 文件 | 改动 |
| --- | --- |
| `cps/static/js/learning-voice.js` | 依赖降级（D1）；`attach` 新增 `options.asrUrl`；新增 `csrfToken()`/`clearNode()` 回退 |
| `cps/templates/ai_chat_panel.html` | 输入区加麦克风按钮（`.sw-mic-label`，learning-voice 按该 class 读写文案）+ 状态行 `#ai-chat-voice-status`；`learning-voice.js` 在 `ai_chat.js` 之前载入 |
| `cps/static/js/ai_chat.js` | 语音播放基元（D2）、分段朗读（D4）、`initVoiceInput()`（转写只填输入框）、每条助手消息挂「朗读本条」按钮 |
| `cps/static/css/ai_chat.css` | 麦克风按钮（录音红底呼吸点）、状态行、朗读按钮（播放中红底可点停）；移动端 44px 触达盒 |
| `cps/templates/i18n_seed.html` + zh `po`/`mo` | 3 条新词条 |
| `tests/test_buddy_voice.py` | 7 条源码/词表守卫 |

交互口径：
- 麦克风**点击开始 / 点击停止**（沿用 R221，不写「按住说话」）；
- 转写结果**追加**到输入框（有草稿时用空格连接，不覆盖），焦点落到末尾，状态行提示「转写完成，可编辑后发送」；**不自动发送**；
- 发送期间麦克风禁用（输入框已清空、上一条正在落库，转写结果无处安放）；
- 朗读按钮只挂**助手**消息（读自己的提问没意义）；播放中再点是停止；关抽屉 / 切会话 / 新建会话都先 `stopSpeech()`，避免「念着但找不到停止入口」；
- 朗读正文取自渲染后的 DOM，剔除工具芯片、tokens 计数、思考占位与 `⚠` 告警行，`<br>`/块级元素还原成换行（否则 `text()` 会把两行粘成 `line oneLine two`，TTS 既没停顿又粘词）。

## 4. 边界与失败

| 场景 | 行为 |
| --- | --- |
| 浏览器不支持麦克风 | `learning-voice` 原有提示「Microphone unavailable」，可继续打字 |
| 录音过短（<1s）/ 全静音 | 不转写，alert 提示重录（R159 阈值 −46dB） |
| ASR 失败 / 空文本 | 保留草稿，不发送，可重录 |
| 转写成功但用户不发送 | 文字留在输入框，无副作用（录音不入库） |
| 朗读请求 400（段超限） | 理论不发生（1800 < 2000）；发生则状态行红字可见 |
| 朗读 404 / 上游 TTS 失败 | 状态行「⚠ 朗读音频不可用」，不静默 |
| 积分不足（`precheckSufficient` 在扣费前拒绝） | 失败体是 moon-well 的 `Result` 信封（HTTP 500 + JSON），前端先读文本取 `message` 再抛，状态行显示「积分不足，无法使用AI功能」；不做 `arrayBuffer` 直解，否则会伪装成「解码失败」 |
| 浏览器拦截自动播放 | 手动点朗读是手势链，正常可播；`audio` SSE 事件在 suspended 上下文下提示「浏览器拦截了自动播放」 |
| 长回复分段 | 状态行「朗读中 n/m」，播完自动收起按钮态 |
| 关闭抽屉 / 切会话 | 立即停止播放并复位按钮 |

## 5. 测试与验收

**自动测试**

- `tests/test_buddy_voice.py`（新增 8 条）：面板挂载与脚本顺序、录音模块解耦、转写不自动发送、朗读不带书籍上下文、朗读不用 blob 媒体、分段上限 <2000、失败要带出上游 message、新词条在种子/PO/MO 三处齐全。
- 回归：`test_buddy_site_assistant.py` / `test_buddy_page.py` / `test_i18n_seed_contract.py` / `test_csp_media.py` / `test_reader_r226_acceptance.py` / `test_reader_r215_ui.py` / `test_learning_pages_static.py` / `test_common_api_contract.py` / `test_onboarding_tour.py` 共 **117 passed / 0 failed**。
- JS：`node --check ai_chat.js`、`node --check learning-voice.js`；`splitForSpeech` 另用 node 直接跑边界（1900 字无标点、纯中文、空串、双段）。

**真人验收（待做）**

1. 阅读页打开伴读抽屉，点麦克风说一句英文 → 停止 → 输入框出现转写文字，可编辑后发送成功。
2. 站内页（首页 `/`）同样可录可转（验证全站生效，不是只在阅读页）。
3. 助手回复底部出现「朗读本条」，点一下出声；再点停止。
4. 长回复（>1800 字）状态行显示「朗读中 1/2 → 2/2」，两段连续播完。
5. 关抽屉时声音立即停止。
6. 中文界面下按钮与状态行为中文（验证 `t()` 取词生效）。

## 6. 遗留（不在本轮）

- **`ai_chat.js` 的 `mbT` 冻结**：载入早于 `i18n_seed`，既有动态文案恒回英文。修法是把 `mbT` 改成调用时解析（一行），但会让面板里一批既有文案突然变中文，属可见行为变化，需单独一轮带验收。
- 用户语音留痕（可回放语音条）：需要 moon-well `ai_message` 加字段 + 录音上传通道，等真实需求再说。
- 自动朗读（语音对话模式）：本轮明确不做；若要做，应先解决「长回复自动念完 = 多次计费」的告知问题。

## 7. 交付与驻留

- worktree：`../magicbook-r227-buddy-voice`，分支 `feat/r227-buddy-voice`，基线 `origin/develop` `a7eecd0c`（占号 commit）。
- 占号：`claim.sh magicbook` → **R227**（`a7eecd0c`，已 push）。
- push 闸门留用户；验收通过后再 `git worktree remove` + `git branch -d`。
