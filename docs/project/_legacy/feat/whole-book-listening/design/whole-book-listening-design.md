# 整本连播（听书）设计（R157）

状态：已上线（2026-10-11，feat/r157-whole-book-read 并入 develop）
需求：R157「为书籍增加一个整本阅读功能：按照顺序一段一段持续朗读，随时可以暂停」——R155/R156 评估轮结论落地：moon-well 侧零改动，全部工作在阅读器前端。

## 1. 需求与范围

按顺序一段一段持续朗读整本书，随时暂停/继续/停止。范围：EPUB/KEPUB 阅读器（read.html）；PDF（canvas 渲染无段落）不做；TXT 阅读器结构简单，可后续低成本追加。

## 2. 方案要点

- **复用既有朗读链路**：`POST /ajax/reading-tts` → moon-well `POST /tts/speak`（音频二进制、永久缓存键=SHA-256(段落原文)、顺序串行天然合规 MiMo 100 RPM）。**moon-well 与 web.py 零改动**。
- **独立播放队列状态机**（epub.js 内 `bookPlayer`，与单段朗读 `activeTts` 互斥让位）：`collectParagraphElements` 收集本章段落 → 归一化文本 + 2000 字符切块（优先句读断句）→ 逐块 `Audio(blob)` 播放 → `ended` 接下一块 → 本章耗尽 `rendition.next()` 等 `rendered` 重建队列 → spine 尽头自动停。
- **暂停/继续**：暂停 = `audio.pause()`（段内保留进度；在途合成请求继续，落库 blob 不开播）；继续 = `audio.play()` 或续跑队列。
- **预取**：当前块 `onplay` 后预取下一块音频，全程 ≤1 个在途合成；进块按文本命中 `nextReady` 复用，未命中即 revoke（服务端永久缓存不白做）。缓存未命中时掩盖合成等待（NAS 本地 TTS RTF≈0.73）。
- **视图跟随**：当前段落不在可见页内才 `rendition.display(段落CFI)` 跳页；CFI 由段落元素实时计算，无旧 CFI 越界毒化显示队列的风险（IndexSizeError 事故只发生在恢复历史保存位置场景）。
- **章界与空章**：spine 下一项存在才翻章；空文字章节（纯图片封面页等）自动跳过（≤10 章，防 spine 异常死循环）；20s 未渲染完成按翻章失败收尾。
- **手动导航跟随**：`rendered` 时非播放器发起（`internalNav` 标记区分）→ 重建队列——同章重渲染（字号/主题/分栏）按 `lastStartedText` 从原块续听；换章从新页顶部起播；章内翻页不触发 `rendered`、不打断播放。
- **互斥**：单段朗读让位连播（`speakParagraph` 先停连播）、连播让位单段（Start 先 `stopTts()`）；切换朗读引擎直接结束连播。
- **UI**：标题栏 `#tts-book`（▶ 起播 / ❚❚ 暂停切换）+ `#tts-book-stop`（■，连播中显示）；当前段加 `.reading-tts-speaking` 高亮（琥珀底 + 左竖条，主题无关）；全部文案走 `mbT()` 五步链（seed/po/mo/契约测试）。

## 3. 已知边界

- 未听过的段落首次合成有等待（新书首听每段几秒到几十秒）；永久缓存越听越快。零等待可先跑 fnOS `tts-warm` 脚本整本预热（book 145《Matilda》先例）。
- 浏览器拦截自动播放时自动转暂停态，点击即恢复（点击即新手势）。
- 不做：播放进度持久化（刷新后从当前阅读位置重新起播）、倍速、TXT/PDF 版本。

## 4. 测试与验收

- i18n 契约测试 5 条全绿（JS 字面量 ⊆ seed = po = 编译后 mo）。
- 代理层回归：test_reading_tts / test_csp_media / test_nav_settings_dropdown 共 20 例绿（web.py 零改动）。
- 真机验收 AC：① 从当前页起播逐段连续播放；② 暂停/继续段内续听；③ 停止后单段朗读照常；④ 章末自动翻章、空章跳过、书末提示；⑤ 高亮跟随与页外跳页；⑥ 手动翻章跟随重建（同章重渲染续听原块）；⑦ 刷新后从当前阅读位置可重新起播。
