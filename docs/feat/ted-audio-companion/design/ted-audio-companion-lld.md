# TED 原声伴听 + 全文同步高亮（R172）

状态：已实现并上线（方案 A，待真机验收）；2026-10-14 首版判据修正已并入（见 §9 变更记录）
同源：moon-well R178 TED 交付链（TXT→EPUB）；**本轮 moon-well 零改动**。

## 0. 一句话

给 TED/博客类书在阅读器里加「跟着原声读」：整段原声连续播放，当前段落实时高亮并自动跟随翻页，点段落即跳到该段原声位置；普通小说书仍走原有 TTS 整本朗读。二者按**是否探测到整段原声**分流（运行时探测，非书籍文件格式），互斥。

## 1. 为什么必须分流（需求本质）

- **TED/博客**：内容本质是**一段连续录音**（`ted-audio/<slug>.aac`，ADTS AAC）；文本段落只是这段录音上的**时间轴切片**。
- **小说类书**：**没有原声**，只能靠 `reading_tts` 按段落文本逐段合成（缓存键 = SHA-256(段落原文)）再拼接连播。
- 若不分流：TED 点「整本朗读」会用**机器音念文本**，而非播真人原声——语义错误，且整本逐段合成**白烧算力与积分**（一场 39 分钟 TED 数万字）。故本功能 = **入口分流 + 原声播放**，不是给 TED 做 TTS。

## 2. 范围

- 做：magicbook EPUB 阅读器（`cps/templates/read.html` + `cps/static/js/reading/epub.js`）；有整段原声的书（探测 `POST /book/ted-audio` 的 `audioUrl`）。整段原声播放、当前段落高亮、段落级切播、暂停/继续/停止、跨页/跨章视图跟随。
- 不做：TXT/PDF 阅读器；逐段片段文件（`ted-audio/<slug>/<order>.aac`）的播放；播放进度持久化（刷新后从当前阅读位置重新起播）；倍速。

## 3. 现状（已核实的契约与设施）

### 3.1 moon-well（零改动，均已交付）

- `POST /book/ted-audio`，body `{"bookId":"..."}` → `Result<TedAudioVO>`：
  `slug, bookId, title, author, durationSeconds, sizeBytes, audioObject(整段对象名 ted-audio/<slug>.aac), audioUrl(整段 MinIO 绝对地址), audioQuality, segmentStatus(NONE/PARTIAL/DONE/FAILED/UNSUPPORTED), segmentCount`。未缓存 / 未建注册表时 data 为 `null`。
- `POST /book/paragraph/list`，body `{"bookId":"..."}`（或 `bookName+author`）→ `Result<{meta, paragraphs[]}>`：
  - `meta` = `BookParagraphMetaVO`（`slug, durationSeconds, totalParagraphs, audioObject, segmentStatus`）。
  - `paragraphs[]` = `BookParagraphVO`（order 升序、排除 p0）：`order, chapterOrder, chapterTitle, text, translation, tedAudioObject(该段片段对象 ted-audio/<slug>/<order>.aac), tedAudioStart, tedAudioEnd`。后两者 = 该段在**整段原声**中的全局毫秒偏移。
- **段落口径与 EPUB 段落 1:1**（关键前提）：TED 章节正文由 `TedImportService.buildChaptersFromTimings` 生成，段落间以 `\n\n` 分隔；`EpubBuilder` 按 `\n` 切+丢空行 ⇒ 同一批段落、一段一 `<p>`。故 **EPUB 段落文本 == 注册表 `text`**。
- 章节标题：TED 章节标题形如 `书名 · 第 N 段`（唯一），`EpubBuilder` 写入 `toc.ncx` navLabel。
- 整段音频为 ADTS AAC；片段由 `TedAudioSegmenter` 按帧**无损**切（不重编码）。

### 3.2 magicbook（可复用设施）

- 代理基建：`cps/web.py` 的 `_moonwell_proxy(path, payload, timeout, label, binary=False, method="POST", system_identity=False, bearer_token=None)`，用户身份走会话 `moonwell_access_token`（`Authorization: Bearer`）；端点装饰器 `@user_login_required`。
- 阅读器注入：`read.html` 的 `window.calibre` 已含 `bookFormat / bookId / bookName / readingTtsUrl`。
- R157 整本连播 `bookPlayer` 的可复用件：
  - `collectParagraphElements(doc)`（L1019）段落元素收集；`paragraphSpeechText(el)`（L1027）讲解文本归一化。
  - 高亮：`.reading-tts-speaking`（琥珀底 + 左竖条，CSS L1004）+ `bookPlayerHighlight(el)` / `bookPlayerClearHighlight()`。
  - 视图跟随：`bookPlayerFollowPage(el)`（L1366）——仅当段落不在可见页内才 `rendition.display` 跳页。
  - 按钮：`#tts-book`（▶/❚❚ 切换）、`#tts-book-stop`（■）+ `bookPlayerUpdateButtons()`（L1238）。
  - 当前章节标题：`currentChapterTitle()`（L2597，优先取 `toc.ncx` label）。
  - 翻章等待：`bookPlayerNextChapter()`（L1550）。
  - 互斥与停止：`bookPlayerToggle()` / `bookPlayerStop(reachedEnd)`。

## 4. 方案（前端为主 + web.py 两个薄代理；moon-well 零改动）

### 4.1 分流判据

**运行时探测「是否有整段原声」**（2026-10-14 修订，事故复盘见 §9 变更记录）：阅读器启动即拉
`POST /ajax/ted-audio`，`result.audioUrl` 非空 → 启用**原声伴听**；否则维持 R157 TTS 连播。

- `#tts-book` 点击统一走 `bookListenToggle()`：先确保探测完成（复用同一 Promise，首次点击
  等待一次往返），再决定 `tedAudioToggle()` 或 `bookPlayerToggle()`。
- 探测完成前按钮**不定语义**；无原声且无 `readingTtsUrl` 才隐藏按钮。
- **不得**用 `calibre.bookFormat === 'TED'` 当判据：它是 Calibre **文件格式**（`epub/pdf/txt`，
  `read.html` 里来自 URL 的 `book_format` 段），与 moon-well `BookFormatEnum.TED` **同名不同义**；
  TED 书在 Calibre 里同样是 `epub` ⇒ 该判据恒 false。
- 探测无法区分「普通小说书」与「TED 但未缓存原声」：两者都回落 TTS，且不再提示
  「原声未缓存」（提示会误伤普通书）。
- **两模式互斥**：启动原声前先 `bookPlayerStop(true)`；启动 TTS 连播前若原声在播先停。

### 4.2 代理（web.py，沿用 `_moonwell_proxy`）

| 前端端点 | moon-well | 说明 |
| --- | --- | --- |
| `POST /ajax/ted-audio`（body `{bookId}`） | `POST /book/ted-audio` | 返回 `Result<TedAudioVO>`；未缓存 data=null |
| `POST /ajax/ted-audio-paragraphs`（body `{bookId}`） | `POST /book/paragraph/list` | 返回 `Result<{meta, paragraphs}>` |

两代理均 `@user_login_required`、`timeout=15`、`Content-Type: application/json`（沿用既有代理形制）。

### 4.3 前端状态机 `tedAudioPlayer`（epub.js，与 `bookPlayer` 并列）

进入 TED 书阅读器 → 并发拉 `/ajax/ted-audio` 与 `/ajax/ted-audio-paragraphs`，建状态：

```
tedAudioPlayer = {
  audio: new Audio(tedAudio.audioUrl),   // 一次装载整段，绝不逐段 fetch
  segments: [{order, startMs, endMs, el}],  // el 由段落 DOM 对齐回填
  currentIdx: -1, paused: false, highlightEl: null
}
```

- **播放/暂停/继续/停止**：`audio.play() / pause()`；停止 = 清高亮 + `audio.currentTime = 0`。复用 `#tts-book` / `#tts-book-stop` 按钮，`bookPlayerUpdateButtons` 增加原声态文案。
- **时间轴驱动高亮**：`audio.ontimeupdate`（节流 ≤ 4 次/秒）→ 在 `segments` 上按 `currentTime*1000` 命中当前段 → `tedAudioHighlight(el)`（复用 `.reading-tts-speaking`）+ `bookPlayerFollowPage(el)`（跨页/跨章自动跟随）。
- **段落级切播**：段落元素点击委托——若 `tedAudioPlayer` 激活，则 `audio.currentTime = startMs/1000` 并从该段起高亮（不打断播放）。
- **结束**：`audio.onended` → 停止 + 清高亮。
- **生命周期**：离开阅读页 / 换书 → `audio.pause()` + `audio.src = ''` 释放。

### 4.4 段落 ↔ 时间轴对齐（关键实现点）

`/book/paragraph/list` 的 `order` 是**全书全局序**，而阅读器一次只渲染一个 spine 章节。对齐策略：

- **主：章节标题 + 段内序**。从 `paragraphs[]` 按 `chapterTitle` 分组（TED 章节标题唯一）→ 得 `chapterTitle → [段记录]`；阅读器渲染某章时取 `currentChapterTitle()` 查组，组内第 k 个段落元素 ↔ 该章第 k 条记录（EpubBuilder 保证「一章 xhtml = 该章全部段落、一段一 `<p>`」）。
- **兜底：归一化文本匹配**。章节标题查不到（缺失/异常）时，退回「归一化文本 → 段记录队列」，阅读器段落 `textContent` 同口径归一化后按出现序消费。两侧文本同源，理论上必中；重复文本按阅读顺序一一消费。
- **降级判据**：某章对齐失败段落占比 > 20% → 该章「仅整段播放、不高亮 / 不切播」，并 `console.warn`（**不静默失败**）。

### 4.5 多章跟随

整段原声是**全书连续时间轴**，播放中会跨越多个章节：`timeupdate` 命中的段 `el` 若属于下一章，需先 `rendition.next()` 等 `rendered` 再高亮——复用 `bookPlayerNextChapter` 的翻章等待与超时形态（空章跳过、20s 未渲染按失败收尾）。

## 5. 边界与降级

| 情形 | 行为 |
| --- | --- |
| `audioUrl` 为 null（普通小说书 / 原声未缓存 / 未建注册表） | 不启用原声；回落 R157 整本 TTS（有 `readingTtsUrl` 时按钮保留）；两者皆无才隐藏按钮。**不再提示**「原声未缓存」——探测区分不了普通书与未缓存 TED，提示会误伤普通书 |
| `segmentStatus = NONE/FAILED/UNSUPPORTED`（无时间轴） | 整段原声可听；**无高亮 / 切播**；按钮照常（仅 ▶/❚❚/■） |
| `paragraphs[]` 为空 | 同上（仅整段播放） |
| 浏览器拦截自动播放 | 转暂停态，点击恢复（同 `bookPlayer` 形态） |
| 浏览器不支持 ADTS `.aac` 直放 | **验收项实测**；不支持则回退方案 B（§7） |
| moon-well 不可达 / 超时 | 提示原声不可用；单段朗读（有浏览器兜底）与整本翻译不受影响 |

## 6. 测试与验收

### 6.1 守卫测试（TestContract，静态双锁）

1. `web.py` 新增两路由存在，且 path/method 映射到 `/book/ted-audio`、`/book/paragraph/list`（防代理指向漂移）。
2. 前端新增文案全部走 `mbT()`；JS 字面量 ⊆ i18n seed = po = 编译后 mo（R157 同款五步链契约）。
3. 分流判据 = **运行时探测 `/book/ted-audio` 的 `audioUrl` 是否为空**（静态锁）；并**负向锁**禁止再用 `calibre.bookFormat` 作判据（那是文件格式，恒 ≠ 'TED'）。

### 6.2 反向变异（确认测试有效；2026-10-14 已实测三条）

- 把探测判据回退成 `calibre.bookFormat === 'TED'` → 分流锁须红（实测：1 failed）。
- 去掉 `audioUrl` 探测判据（改成恒 true）→ 分流锁须红（实测：1 failed）。
- `#tts-book` 静态直连 `tedAudioToggle`（绕过探测）→ 接线锁须红（实测：1 failed）。
- 删掉当前段高亮调用 → 高亮相关断言须红。
- 代理 path 改成错误端点 → 路由映射断言须红。

### 6.3 真机 AC

① 探测到整段原声的书点 ▶ 播**真人原声**（非机器音）；② 当前段随播放高亮并自动翻页 / 翻章跟随；③ 点任一段跳播到该段原声位置；④ 暂停 / 继续段内续听、停止复位；⑤ 普通小说书仍走 TTS 整本朗读（不受影响）；⑥ 无原声的书按钮保留并回落 TTS（不再提示「原声未缓存」）。

## 7. 备选方案 B（仅当整段 `.aac` 浏览器直放不可用）

逐段片段连播：复用 `bookPlayer` 队列骨架，逐段 fetch `tedAudioObject`（`<order>.aac`）播放，高亮 = 当前段元素。代价：多次请求、需确认浏览器可放 ADTS 片段。**默认采用方案 A（整段）**，B 仅为回退。

## 8. 影响面 / 文档联动（交付前回填）

- L1 `docs/readme/reading.md`：补「TED 原声伴听」一句（用户可见能力变化）。
- L2 `docs/reading/hld/hld.md`：补两个代理端点映射（对外行为变化）。
- `requests.md` R172 占号；完成后写 `response.md`。

## 9. 变更记录

### 2026-10-14 判据事故（首版线上无效）

- **现象**：R172 代码已随 develop 部署上线（线上 `epub.js` 实测含 `tedAudioToggle`），但用户实测 TED 书 **仍播 AI 合成音**，非原声。
- **根因**：首版分流判据 `calibre.bookFormat === 'TED'` **恒为 false**。`read.html` 注入的
  `bookFormat` 是 Calibre **文件格式**（`read.html` 里来自 URL 的 `book_format` 段，
  `"epub"/"pdf"/"txt"`，同文件 L327 还拿它当 `book_format` 提交给 Calibre），
  与 moon-well `BookFormatEnum.TED`（内容形态）**同名不同义**；TED 书在 Calibre 里同样是 `epub`。
  ⇒ 分流从未生效，一直走 R157 逐段 TTS。
- **修法**：判据改为**运行时探测** `POST /ajax/ted-audio` 的 `result.audioUrl` 是否为空；
  `#tts-book` 点击统一走 `bookListenToggle()`（先确保探测完成再定分流）。
  同步取消「原声未缓存 → 隐藏按钮 + 提示」——探测区分不了「普通小说书」与「TED 但未缓存」，
  该提示会误伤普通书；改为无原声即回落 TTS（无 `readingTtsUrl` 才隐藏）。
- **教训**：同名字段跨服务不必然同义；**"字段存在"要验到它的赋值来源**，不能只验字符串在场
  （首版静态锁锁的正是那个恒 false 的表达式，测试全绿却功能失效 —— 静态锁只能锁"代码形态"，
  锁不住"语义正确性"；跨服务语义对齐必须实测或读上游定义）。
- **守卫**：`test_shunt_is_runtime_probe_not_file_format`（正向锁探测置位 + **负向锁**禁止再用
  `bookFormat`）、`test_tts_book_button_routed_through_probe`；三条反向变异已实测报红（§6.2）。
