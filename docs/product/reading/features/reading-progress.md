# L3 · 账号级阅读位置（reading-progress）

> 建立：2026-10-23（R213-B / PJM MB-17）。读者＝改这块代码的人。
> 接口契约见 [L2 §3](../interface.md)；本次实现细节见 [`project/iterations/1.0/r213-home-ia/lld.md`](../../../project/iterations/1.0/r213-home-ia/lld.md)。

## 实现方式

| 层 | 落点 | 职责 |
| --- | --- | --- |
| 表 | `cps/ub.py` `ReadingProgress`（`reading_progress`） | `(user_id, book_id, book_format)` 唯一；`position`（EPUB=CFI）/`progress_percent`/`page_current`/`page_total`/`last_read_at` |
| 端点 | `cps/routes/reading.py` `reading_progress()` | `POST /ajax/reading-progress`，登录门禁 + upsert + 入参防御 |
| 采集 | `cps/static/js/reading/reader-progress.js` | 节流（≥10s 或翻 ≥5 页）+ `pagehide`/隐藏时 keepalive 补发；只采集不恢复 |
| 恢复 | `cps/static/js/reading/epub.js`（`book.ready` 链路） | 服务端位置优先，其次 localStorage；沿用原两级安全落位（先 spine 序号、再 CFI 精调） |
| 取数 | `cps/web.py` `recent_reading(user_id, limit)` | 首页「继续阅读」：`last_read_at` 倒序，排除已读完与被删书 |

## 边界与坑

- **不写 `ub.ReadBook`**：`read_status` 只由原有逻辑维护；本表不参与「已读」判定，也不被 `render_read_books` 读取。
- **不写 `KoboReadingState`**：那是 Kobo 协议私有结构，网页写入会让设备端读到脏位置。
- **`ReadBook.last_time_started_reading` 不可用**：只有 `cps/kobo.py:804` 写它，网页读者恒为空。
- **页码同源**：`page_current/page_total` 必须取自 `book.locations.locationFromCfi(cfi)` 与 `locations.length()`——与阅读器顶部显示的 `37/125` 同源，另算一次会出现首页与阅读器两个页码。
- **越界百分比夹取不拒绝**：书结构异常时 epub.js 会算出 >100，拒绝等于整条记录丢掉。
- **老账号回填**：服务端无记录时用 localStorage 位置，首次 `relocated` 上报即自然写入，不跑迁移脚本。
- **格式覆盖**：EPUB/KEPUB（reader-core 链路）、PDF（readpdf.html 内联脚本挂 `PDFViewerApplication.eventBus`，恢复走 `#page=N` 片段，viewer.js 是 vendored 文件不改动）、TXT（txt_reader.js 按位移计页，首次接入——TXT 此前没有任何进度记忆）。CBR/CBZ 未接。
- **失败可见性**：前端只 `console.warn`，不弹 toast（进度不是关键路径）；但服务端一律返回 4xx + JSON，不做静默吞。
