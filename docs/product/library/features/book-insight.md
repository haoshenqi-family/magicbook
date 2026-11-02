# 书籍内容速览（L3 实现说明）

> 建立：2026-10-29（R247）。读者是**要改书籍详情或内容速览的人**；
> 用户视角见 L1 [`product/readme/library.md`](../../readme/library.md)；
> 本轮缺陷取舍见 LLD
> [`project/iterations/1.0/r214-book-detail/lld.md`](../../../project/iterations/1.0/r214-book-detail/lld.md) §19。

## 1. 数据流

1. `cps/web.py::show_book()` 用 `get_book_read_archived(..., allow_show_archived=True)`
   读取详情；这使归档书与普通书一样能打开 `/book/<id>`。
2. EPUB/KEPUB 书籍进入 `cps/reading_insight/service.py::get_or_build()`；
   `parser.py` 解析 OPF spine、nav/ncx、段落与摘录，结果按
   `(book_id, book_format)` 写入 `book_insight`。
3. 正文指纹由路径、文件大小和 `mtime_ns` 计算；指纹变化时重建 payload，
   但保留已生成的人工触发 AI 简介。
4. 详情页的目录、试读、AI 简介、整本任务估算和缓存齐备标识共用这份 payload
   或同一正文指纹。

## 2. 取书与可见性

- 内容速览的 `_book_file()` 调用
  `JobServiceBase._book_file(..., allow_show_archived=True)`，与详情页的归档可见性一致。
- 因而归档 EPUB 只要文件仍在，就能生成目录、试读、AI 简介上下文、估算和缓存标识，
  不得再误报 `book is unavailable`。
- `JobServiceBase._book_file()` 的默认值仍是 `allow_show_archived=False`。
  整本翻译、整本朗读、全文单词详解继续沿用原归档过滤，不得借内容速览修复顺带放宽。

## 3. 边界

- 仅支持 EPUB / KEPUB；其他格式不进入内容速览。
- 单本解析超过 `MAX_PARSE_BYTES` 时只出目录与统计，不出摘录。
- 解析失败不会拖垮详情页：对应区块显示「解析失败：<原因>」，并尽量把错误写入
  `book_insight.last_error`。
- 归档状态按用户保存；详情和内容速览共享同一可见性口径，但取不到真实文件时仍报
  `book file is unavailable`，不能把文件缺失伪装成空内容。
