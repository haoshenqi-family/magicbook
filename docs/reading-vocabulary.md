# 阅读单词学习

EPUB 阅读器支持在当前可见页面识别英文单词，并将学习上下文交给 `moon-well` 保存。

## 功能

- 当前页面中的英文单词会被批量识别。
- `moon-well` 根据用户历史返回陌生词和释义。
- 陌生词在阅读器中以波浪下划线标识，悬停或点击可查看释义及上次学习信息。
- 每次遇到单词都会保存：单词、句子、用户、书籍 ID/名称、章节、页码、EPUB CFI、学习时间和次数。
- 历史记录使用 Elasticsearch 的 `reading_vocabulary` 索引保存；原有 `vocabulary` 索引继续提供词汇释义。

## 章节（chapter）正确性

`analyze` 请求中的 `chapter` 取自阅读器标题栏的 `#chapter-title`。曾存在缺陷：epubjs 自带
`MetaController` 会把作者（creator）一次性写入 `#chapter-title` 且翻页时不更新，导致发送的
`chapter` 与实际视口章节错位（例如第一章的文本被标记为第三章）。

已修复（`cps/static/js/reading/epub.js`）：

- 初始化时加载书籍 navigation TOC 并递归展平。
- 在 epubjs `rendered` 事件中，根据当前渲染 section 的 `href` 匹配 TOC 条目，动态更新
  `#chapter-title` 为真实章节标题；TOC 匹配不到时回退用章节文件名。
- 初始化时清空 `MetaController` 写入的错误值。

> 2026-09-08 修复后，曾写入错误章节的历史数据已备份并删除
> （`reading_vocabulary` / `reading_paragraph_cache` 备份至 `*_bak_20260908`），
> 由前端修复后重新生成。

## 配置

在 magicbook 进程配置：

```bash
MOON_WELL_READING_URL=https://moon-well.example.com
```

调用 `/reading-vocabulary/**` 时使用 moon-well 标准 `authorization: Bearer <token>` 请求头。moon-well 通过 JWT 的 `UserContext` 确定用户，客户端不能通过 `userKey` 冒充其他用户。

## 当前范围

第一版接入 EPUB/KEPUB 阅读器，因为 epub.js 能直接访问当前章节 iframe 的 HTML 文本和 CFI 位置。PDF、TXT、漫画和音频阅读器尚未接入这套识词流程。

如果没有配置 moon-well 地址或令牌，阅读器保持原有行为，不显示错误弹窗。
