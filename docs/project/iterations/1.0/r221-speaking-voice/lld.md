# R221 AI 口语陪练语音优先 · LLD

> 状态：**开发完成，待真人端到端验收**（2026-10-24）
> 工作项：R221（magicbook 前端与代理）· 跨仓 moon-well R212（后端与存储/契约主责）
> 迭代：magicbook 1.0 · 设计文档路径 `docs/project/iterations/1.0/r221-speaking-voice/`
> 编号说明：本任务最初误占 R212（该号已属品牌资产），2026-10-24 已正式迁移为 R221。

## 1. 目标与不做什么

**目标**

1. 教练开场与每轮回复默认语音条，文字折叠；点击可播放、可展开原文。
2. 用户录音先 ASR 转写，可编辑确认后发送；发送成功后展示用户语音条。
3. 历史会话支持语音回放与文字展开。
4. 保留打字入口。

**非目标**

- 不做按住说话、实时语音对话、音素级发音评分。
- 不改教练提示词、反馈结构、报告逻辑。
- 不把 MinIO 直链暴露给浏览器。

## 2. 架构与端点

```text
页面 learning_speaking.html
  ├── learning-common.js   信封解包 / CSRF / busy
  ├── learning-voice.js    WebAudio 录音 + ASR + onRecording
  └── learning-speaking.js 会话状态 / 语音条 / 上传 / 代理调用

magicbook 代理
  ├── /ajax/learning/speaking/session
  ├── /ajax/learning/speaking/recording/upload
  ├── /ajax/learning/speaking/recording/audio
  ├── /ajax/learning/speaking/message
  ├── /ajax/learning/speaking/messages
  └── /ajax/reading-tts-cached

moon-well
  ├── LearningSpeakingController
  ├── LearningSpeakingService
  ├── LearningSpeakingRecordingService → MinIO
  └── ReadingTtsService → TTS + 持久缓存
```

代理层只做本地明显非法输入拦截与鉴权转发：

- 消息端点白名单 `sessionId,text,voice,audioObject,durationMs`；
- 上传端点在本地校验数字 `sessionId`、非空文件、≤10MB；
- 回读端点以二进制透传，不解码 JSON。
- `session/message/report` 统一给 210s 预算：后端 LLM 单项预算 120s，回复后还要同步
  合成教练 TTS；90s 会让后端仍成功时先被代理截成 503。

## 3. 前端状态机

```text
idle
  -- 点击麦克风 --> recording
recording
  -- 点击停止 --> transcribing
transcribing
  -- ASR 成功 --> preview {wav,text,durationMs}
  -- ASR 失败 --> idle（可重录）
preview
  -- 编辑文本 --> preview
  -- 点击发送 --> uploading（如无 audioObject）-> sending
  -- 改成打字 --> typing
uploading
  -- 成功 --> sending（缓存 audioObject）
  -- 失败 --> preview（保留文本/录音）
sending
  -- 成功 --> idle + 渲染用户/教练消息
  -- 失败 --> preview（保留文本/录音/对象名）
typing
  -- 点击发送 --> sending（voice=false）
```

## 4. 交互细节

- 语音条：时长按 `durationMs` 展示；无时长时按文本长度估算，仅作视觉占位。
- 转文字按钮默认 `Show text`，展开后切换为 `Hide text`；原文用 `textContent`。
- 教练开场 `greetingAudioUrl` 与回复 `replyAudioUrl` 由后端返回；如果为 null，
  语音条仍显示，点击时走缓存回读/补合成并显示失败提示。
- 发送失败使用页面状态行显示错误，不使用 alert；textarea 与 pending 保持可编辑。
- `finally` 中按 textarea 当前是否有内容恢复发送按钮可用性；失败时保留转写，
  用户可直接重试，成功后由 `resetCompose()` 清空并禁用发送。

## 5. 权限与安全

- 不信任客户端 userId；所有请求带当前 session 的 moon-well bearer。
- 录音对象名只来自上传端点响应；前端不自行拼路径。
- 回读端点仍由 moon-well 校验用户/会话/对象前缀；magicbook 只透传。
- 文本与消息内容走 DOM `textContent`，不拼 HTML。

## 6. 失败与边界

| 场景 | 行为 |
| --- | --- |
| 录音过短/静音 | 不转写，提示重录 |
| ASR 空文本 | 保留录音，提示未检测到语音 |
| 上传失败 | 预览保留，重试重新上传 |
| 消息失败 | 预览与 audioObject 保留，重试不重复上传 |
| 教练 TTS 失败 | 文字与反馈照常；语音播放失败可见 |
| 自动播放被浏览器拦截 | 静默失败，用户可点击播放 |
| 旧历史消息 | 无语音字段时按文字气泡渲染 |

## 7. 测试与验收

**自动测试**

- `test_learning_proxy.py`：上传字段、语音元数据白名单、失败保留预览、页面 URL。
- `test_learning_pages_static.py`：脚本顺序与 URL 注册。
- `test_i18n_seed_contract.py`：新增词条与中文译文完整。
- JS 语法：`node --check cps/static/js/learning-speaking.js` 与 `learning-voice.js`。

**真人验收（未完成）**

1. 开聊后教练开场自动播放，点击语音条可重播、转文字可展开/收起。
2. 说一句英文，停止后出现转写预览；修改一两个词再发送成功。
3. 每轮教练回复自动播放；失败时文字反馈仍在。
4. 刷新后打开历史会话，用户与教练语音都能回放。
5. 模拟网络失败：预览不丢，恢复后直接重试成功。

## 8. 交付状态与驻留

- worktree：`../magicbook-r221-speaking-voice`，分支 `feat/r221-speaking-voice`。
- 业务代码与文档提交在本分支，**未 merge、未 push**，驻留待验收。
- 旧 `../magicbook-r212-speaking-voice` 为误占号的迁移来源，未删除、未清理。
- 尚未完成真人登录态录音与播放验收。
