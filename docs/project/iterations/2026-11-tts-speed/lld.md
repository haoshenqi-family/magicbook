# LLD — R263 阅读器朗读速度选项（1.0x / 0.75x / 0.5x，TED/博客类初学者降速）

> 状态：已开发待验收（2026-11-01）
> 背景：用户原话「增加一个 0.75 0.5 朗读速度的选项。博客类的对于初学者可能太快了」。TED/博客类书走 R172 整段真人原声伴听，原声是母语者常速语流，初学者跟不上；整本 TTS 连播同受影响。

## 1. 方案选型：客户端 playbackRate，不动服务端

音频缓存键 = SHA-256(段落原文)（moon-well 侧永久缓存设计，见 L1「朗读」），变速若落服务端：同一段文字要么按速度存多份音频（存储×3），要么把速度参数掺进缓存键（击穿全部存量缓存，全量重合成）。浏览器 `playbackRate` 配合 `preservesPitch`（变速不变调）在客户端即时生效、零成本、对真人原声与合成音都适用。档位集合钉死三档（1.0 / 0.75 / 0.5），不做自由输入——初学者听得清的最小集合，且避免任意值喂给 `playbackRate`。

## 2. 实现落点

- **档位存取（reader-core.js）**：`TTS_SPEED_KEY = "calibre.reader.ttsSpeed"`（与 `calibre.reader.ttsEngine` 同命名族），`TTS_SPEED_STEPS = [1, 0.75, 0.5]` 循环；`ttsSpeed()` 白名单校验（脏值回落 1）、`ttsSpeedLabel()`（1.0x / 0.75x / 0.5x）、`cycleTtsSpeed()`（写 localStorage 并返回新 label）、`applyTtsSpeed(audio)`（设 `playbackRate` 并显式钉住 `preservesPitch`/`webkitPreservesPitch`，Safari 旧名兜底）。
- **三条播放链路全部套速**（R263 静态锁 `tests/test_r263_tts_speed.py` 逐条钉住）：
  1. TED/博客类整段原声：`reader-ted-audio.js` `tedAudioStart()` 的 `new Audio` 后；
  2. 整本 TTS 连播：`reader-tts.js` `startAudio()` 每块新建 Audio 后（暂停/继续沿用同一元素，无需重套）；
  3. 单段朗读：`reader-tts.js` activeTts 的 `new Audio` 后；浏览器兜底链路 `SpeechSynthesisUtterance` 无 playbackRate，改 `utterance.rate = 0.95 × 档位`（在播 utterance 不可中途改 rate，下一句生效）。
- **UI（read.html / reader-immersive.js / reader.css）**：顶栏 `#tts-book-stop` 后新增 `#tts-speed`（icon 槽显示当前档位文本，label「语速」= msgid `Reading speed`，仅 zh_Hans_CN 补译，其余 locale 英文回退——R259 同款口径）。绑定在 reader-immersive.js（与 #tts-book 同区），点击循环档位、回显图标并经 `host.applyTtsSpeedToActive()`（epub.js 注入，聚合 RTTS+RT 两模块的 `applyTtsSpeedToActive`）推给在播链路；载入即回显记忆档位，不必等播放。图标字号 15px（「0.75x」五字符不能按 24px 摆）。
- **可用性**：书既无原声也无 TTS 端点时，`tedAudioApplyAvailability()` 隐藏 `#tts-book` 的同一分支把 `#tts-speed` 一并隐藏（无播放能力时语速是死按钮）。窄屏折叠（reader-toolbar.js）只收 bookmark/setting/fullscreen/whole-book-translate 四项，语速与朗读组同留主栏，不动折叠清单。

## 3. 边界与不做

- 不做服务端变速、不做自由速率输入、不把速度掺进音频缓存键（§1）。
- AI 伴读（ai_chat.js）与听写/口语等学习页播放器不在本轮范围（用户口径是阅读页朗读）。
- 速度只影响播放，不影响段间停顿（BOOK_TTS_CHUNK_GAP 260ms 恒定）与时间轴高亮（TED 时间轴按原声时钟走，playbackRate 下 currentTime 同比例变速，命中逻辑无需改）。

## 4. 测试与文档

- 新增 `tests/test_r263_tts_speed.py` 5 条静态锁（按钮存在与位置、档位与白名单、三条链路逐处套速、切档接线、无播放能力隐藏）；定向回归 `test_reader_module_surface / test_i18n_seed_contract / test_ted_audio_proxy` 共 33 passed。
- 文档四问：能力变了（L1 reading.md 朗读条补语速句）、契约没变（无接口改动）、实现边界（本文）、需求基线变更记录加 R263 行。
