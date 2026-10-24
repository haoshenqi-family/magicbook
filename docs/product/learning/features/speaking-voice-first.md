# AI 口语陪练语音优先（R221）

> 读者：修改 `learning_speaking.html`、`learning-speaking.js`、`learning-voice.js`
> 或口语代理端点的开发者。
> 状态：现行（2026-10-24 R221，开发完成，待真人端到端验收）。

## 实现方式

### 1. 页面与状态机

- 页面进入后展示场景、教练风格与可选书名；开始会话后隐藏设置区，展示聊天区。
- 前端状态 `speaking.pending` 表示「已转写、未发送」的一段录音，字段为
  `{wav,text,durationMs,audioObject?}`。只有该状态存在时发送才是语音消息。
- 录音流程：点麦克风开始 → 再点停止 → WebAudio 编码 16k 单声道 WAV → ASR 转写 →
  `setPreview()` 把文本写入 textarea 并显示「发送前检查转写」及时长。
- 发送流程：若对象名尚未生成则 multipart 上传录音；随后调用消息端点；成功后渲染
  用户与教练语音条，并清空预览。失败只显示状态行错误，保留预览与对象名。
- 「Type instead」切换到纯文字模式，清空 pending；「Use voice instead」回到语音模式。

### 2. 语音条与播放

- 每条消息由「播放按钮 + 时长 + 转文字按钮 + 默认折叠的原文」组成；不使用
  `innerHTML` 拼接消息正文，全部走 `textContent`。
- 教练语音优先请求 `/ajax/reading-tts-cached`。本轮已返回 `audioUrl` 时，缓存
  miss 视为播放失败，不回退计费端点，避免已合成过又重复扣费；只有后端 TTS
  失败导致 `audioUrl` 为空时，用户主动播放才允许在缓存 miss 后调用计费端点补合成。
- 用户语音请求 `/ajax/learning/speaking/recording/audio`，以 `sessionId` +
  `audioObject` 换二进制；不直接使用 MinIO URL。
- 同一时刻只保留一个 `Audio` 实例，播放新语音前先暂停旧的；播放结束/失败恢复图标。

### 3. 自动播放

- 开聊成功与发送成功处于用户点击手势链中，允许尝试自动播放教练语音。
- 自动播放失败不弹窗；用户主动点击语音条失败才提示，避免浏览器策略造成「功能坏了」
  的误导。

### 4. 代理预算

- `/ajax/learning/speaking/{session,message,report}` 统一使用 210s 超时。
- 原因是后端每轮先等 LLM（120s 预算），成功后再同步合成教练语音；代理若仍用 90s，
  正常慢请求会得到假 503，而 moon-well 侧实际上仍可能完成并产生消息/扣费。

## 边界条件

- 语音按钮为点击开始/点击停止，文案必须是 `Tap to speak`，不能写按住说话。
- 录音过短（<1 秒）或全静音不进入转写；ASR 空文本给出「未检测到语音」提示。
- 预览文本允许修改，发送时以 textarea 最终内容为准；后端不强制与 ASR 原文一致。
- 历史消息中 R212/R221 前的纯文字用户消息走文字气泡兼容分支；语音消息才有
  `durationMs/audioObject`。
- 页面依赖 `learning-voice.js` 的 `onRecording({wav,text,durationMs})` 契约；
  不要在页面里重复实现录音逻辑。

## 失败与降级

| 场景 | 行为 |
| --- | --- |
| 浏览器不支持麦克风 | 提示麦克风不可用，可切打字 |
| ASR 失败/空文本 | 保留录音可重录，不发消息 |
| 上传失败 | 保留预览，重试重新上传 |
| 消息接口失败 | 保留预览与对象名，直接重试 |
| 教练 TTS 失败 | 教练文字与反馈正常展示；语音播放失败可见 |
| 缓存回读 miss | 有预备 audioUrl 时不回退，避免重复扣费；仅有 audioUrl 为空时才允许补合成 |
| 历史录音不可读 | 播放失败提示，不吞成空白消息 |

## 测试锚点

- `tests/test_learning_proxy.py`：上传 multipart 字段、语音元数据白名单、失败保留预览源码守卫。
- `tests/test_learning_pages_static.py`：页面 URL 注入与脚本装配顺序。
- `tests/test_i18n_seed_contract.py`：所有 `mbT()` 字面量必须进种子且中文译文非空。
