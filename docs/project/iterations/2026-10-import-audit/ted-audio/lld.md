# TED 原声伴听链路修正（magicbook R200 / R202）· LLD

**状态**：已 push 上线（magicbook `8a09af81` / moon-well `8a64094`，2026-10-21），worktree 驻留待用户验收；MAGICBOOK-211 未流转 Completed

## 1. 现象与根因

线上症状与 R172/R173 事故同形：代码已部署、TED 书仍播 TTS 机器音。

本次定位到的根因不是前端分流判据（R172 已修为「运行时探测 `audioUrl`」），而是**探测本身永远空手而归**：

| 侧 | 传/收 | 语义 |
| --- | --- | --- |
| magicbook `reader-ted-audio.js` | 传 `calibre.bookId` | **Calibre** `metadata.db` 的书号 |
| magicbook `cps/web.py::_ted_audio_book_id` | 注释明示「Calibre 书号」 | — |
| moon-well `/book/ted-audio` | `TedAudioService.findByBookId` → `bookRepository.findById` | **moon-well 自有 book 表**主键 |

两套自增序列只有**巧合对齐**才命中；错位时 `findMeta` 拿错书名 → 段落注册表查不到 →
`result=null` → 前端按设计静默回落整本 TTS。learning 模块 R139/R149 已踩过同款坑，
本次是同一反模式在 book 域的复现。

## 2. 修法：改用「书名 + 作者」作跨服务身份

段落注册表本就按 `title` + `author` 索引，按名查可彻底绕开 ID 空间不一致；`bookId` 入参保留兼容
（moon-well 内部调用方与历史前端仍可用）。

### 2.1 magicbook 侧（本仓）

- `cps/web.py`：`_ted_audio_book_id()` → `_ted_book_identity()`，返回 `(book_name, author, error)`。
  用 `calibre_db.get_book(int(raw))` 取 `title` 与 `authors`（多作者 `" & ".join`，与 moon-well 导入时写入的 author 一致）。
- `cps/routes/reading.py`：两个代理改发 `{"bookName": ..., "author": ...}`，并做错误映射。

**错误语义（新增，此前脏串会直接进上游 `Long.valueOf` 变 500）**：

| 情形 | 状态码 | 说明 |
| --- | --- | --- |
| `bookId` 非数字 / 缺失 | 400 `bookId must be a number` | 脏串绝不进上游 |
| 本地 Calibre 库无此书 | 404 `book not found` | 不把空书名送去上游当「未缓存」——那是两回事 |
| 上游不可达 | 503（`_moonwell_proxy` 既有语义） | — |

### 2.2 moon-well 侧（跨仓 R197）

`TedAudioQueryDTO` 去掉 `@NotBlank bookId`，改为 `bookId` / `bookName` / `author` 三字段 +
`hasBookId()` / `hasBookIdentity()`；`BookController.tedAudio()` 二选一分派，都缺则抛业务异常
（形制仍是统一 `Result`，短信封套不变）。`TedAudioService` 抽出 `findMetaVo(bookName, author)`，
`findByTitleAuthor` 与 `findByBookId`（后者改为 `findById` 后 flatMap 同一段元信息拼装）共用。

## 3. 为什么不上「ID 映射表」

- 映射表要跟着 TED 导入的每一次去重/重建走，任一侧漏更新就退化成同款静默错位，且错误从「查不到」变成「查到别的书」，更难发现。
- 标题+作者是**业务身份**，注册表、去重规则（同作者同标题复用）、Calibre 书目都用它，不需要第二套真源。

## 4. 测试

- `tests/test_ted_audio_proxy.py`（17 passed）：`calibre_stub` 桩掉 `cps.web.calibre_db`，断言转发体
  **恰为** `{"bookName": "Talk A", "author": "Speaker"}` 且不含 `bookId`；新增 404 用例（上游零调用）、
  负向静态锁 `test_proxy_never_sends_calibre_book_id_as_moonwell_bookid`（源码里不得再出现 `"bookId": book_id`）。
- moon-well `TedAudioServiceTest` 新增 `findByTitleAuthorBypassesBookIdSequence`、`findByTitleAuthorBlankOrMissingMetaReturnsEmpty`。

## 5. 未修（R202 / MAGICBOOK-213）

1. TED 书在 magicbook 书库**无封面**：moon-well `EpubBuilder` 不写封面、`CalibreService.insertBook` 固定 `has_cover=0`，`coverUrl` 有值但没同步。
2. 「原声未缓存」的 TED 书与普通小说书在探测上不可区分 ⇒ 仍会静默回落机器音（R172 想避免的语义错误在这一小类里残留）。要区分得让上游对「TED 但未缓存」返回可判别的标记，而不是 `null`。
3. 原声伴听无播放进度持久化、无倍速。
