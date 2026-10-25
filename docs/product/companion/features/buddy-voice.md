# 伴读语音（Buddy 语音输入与回复朗读）

> 读者：改 `ai_chat.js` / `learning-voice.js` / `ai_chat_panel.html` 或伴读面板语音行为的人。
> 状态：现行（2026-10-25 R227，开发完成待真机验收）。
> 需求基线：[`../requirements.md`](../requirements.md) R227；本次实现：[`../../../project/iterations/1.0/r227-buddy-voice/lld.md`](../../../project/iterations/1.0/r227-buddy-voice/lld.md)。

## 实现方式

### 1. 语音输入（全站可用）

- 面板输入区有一个麦克风按钮（`#ai-chat-mic`）+ 状态行（`#ai-chat-voice-status`），
  面板在 `layout.html` 与三个 read 模板里挂载，因此**任何页面**都能用。
- 录音链路不在 `ai_chat.js` 里重写，而是 `learning-voice.js`：
  WebAudio 采集 → 16k 单声道 WAV → `POST /ajax/learning/asr/transcribe`（magicbook 代理，
  登录鉴权，≤10MB，60s 预算）→ 回调 `onRecording({wav,text,durationMs})`。
- `ai_chat.js` 的 `initVoiceInput()` 只做三件事：挂按钮、把转写文本写进输入框（有草稿时
  空格拼接）、显示「转写完成，可编辑后发送」。**不自动发送**。
- `learning-voice.js` 已从「学习中枢专用」解耦：`MBLearning`/`learningUrls` 缺失时回退到
  `window.mbT` + `window.MBApi.csrfToken()` + 字面量路由；学习页行为不变。

### 2. 回复朗读

- 每条**助手**消息末尾挂「朗读本条」按钮（`attachSpeakButton`）。流式期间消息内容每帧重写，
  按钮必须等 `finishMessage` 之后再挂，否则下一个 `delta` 就把它抹掉。
- 正文取自渲染后的 DOM（`speechTextOf`）：剔除工具芯片 / tokens 计数 / 思考占位 / `⚠` 告警行，
  并把 `<br>` 与块级元素还原成换行——否则 `text()` 会把两行粘成 `line oneLine two`。
- 播放走 **Web Audio**（`fetch` 取字节 → `decodeAudioData` → `AudioBufferSourceNode`），
  不用 `URL.createObjectURL` + `<audio>`。原因：`media-src` 只在阅读页/口语页放行 `blob:`，
  而面板是全站的；走 `fetch`（`connect-src` 回退 `default-src 'self'`）不需要动任何 CSP。
- 分段：`SPEECH_SEGMENT_MAX = 1800`（`/tts/speak` 上限 2000），先空行、再句末标点、最后硬切；
  逐段合成顺序播放，状态行显示「朗读中 n/m」。
- 合成端点：`/ajax/reading-tts` → moon-well `/tts/speak`。计费按 moon-well R213 口径：**命中缓存 1 积分/段**；**首次生成按字符**计（50 字符 = 1 积分，≈2 元/万字符）。一条 1800 字的新回复首读约 36 积分，重听 1 积分。
  **不带** `bookName`/`chapter`，音频落「AI 临时语音」档（7 天清理），不写书籍段落永久缓存。
- 停止：再点按钮 / 关抽屉 / 切会话 / 新建会话都会 `stopSpeech()`（递增 token 使在途请求作废）。

### 3. 伴读工具的既有朗读（`synthesize_tts`）

`audio` SSE 事件拿到朗读原文后调 `/ajax/reading-tts-cached`（只读缓存、不计费）。该路径与
回复朗读共用同一套 Web Audio 基元——副作用是**修掉了它在非阅读页被 CSP 拦截的既有静默故障**。

## 边界条件

- 麦克风是**点击开始 / 点击停止**，不是按住说话（沿用 R221）。
- 录音 <1 秒或峰值低于 −46dB（全静音）不送转写，直接提示重录（R159 阈值）。
- 转写结果必须可编辑；发送时以输入框最终内容为准。
- 发送期间麦克风禁用（转写结果无处安放）。
- 分段是**计费分段**：2000 字回复 ≈ 2 次 `/tts/speak`，首读按两段字符累加（约 40 积分），重听各 1 积分。按钮文案与「朗读中 n/m」都要如实反映在播。
- 同一时刻只播一条；播新的先停旧的。
- 朗读按钮只挂助手消息，不挂用户消息与提示行。
- 新增文案必须用 `ai_chat.js` 的 `t(id)`（调用时取词），不能用顶层 `mbT`——后者在脚本载入时
  已被固定成恒等函数（`i18n_seed` 在面板之后 include）。

## 失败与降级

| 场景 | 行为 |
| --- | --- |
| 浏览器不支持麦克风 | 提示「Microphone unavailable」，可打字 |
| 录音过短 / 全静音 | 不转写，提示重录 |
| ASR 无人声 / 失败 | 提示「未检测到语音」或上游 message，草稿保留 |
| 转写地址不可用（未登录/代理挂） | 提示可读错误，不吞成「没反应」 |
| 朗读 400（超 2000 字） | 正常不发生（1800 分段）；发生则状态行红字可见 |
| 朗读上游失败 / 缓存缺字节 | 状态行 `⚠` 提示，不静默 |
| **积分不足（`precheckSufficient` 拒绝）** | 状态行直接显示上游 message（「积分不足，无法使用AI功能」）；失败体是 Result 信封，必须先读文本再解析，**不能**当音频去 decode（否则用户看到的是「解码失败」） |
| 浏览器拦自动播放（仅 `audio` 事件路径） | 提示「浏览器拦截了自动播放，请先与页面交互」 |
| 旧浏览器无 `AudioContext` | 提示「朗读音频不可用」，文字回答不受影响 |

## 测试锚点

- `tests/test_buddy_voice.py`：面板挂载与脚本顺序、模块解耦、转写不自动发送、朗读不带书籍
  上下文、朗读不用 blob 媒体、分段上限 <2000、`t()` 词条在种子/PO/MO 三处齐全。
- `tests/test_i18n_seed_contract.py`：全部 `mbT()` 字面量必须进种子（新增词条走 `t()`，由上面那条补位）。
- `tests/test_csp_media.py`：反向守卫——非阅读页/口语页仍不得出现 `media-src`，本轮没有放宽。
