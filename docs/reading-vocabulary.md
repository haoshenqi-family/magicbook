# 阅读单词学习

EPUB 阅读器支持在当前可见页面识别英文单词，并将学习上下文交给 `moon-well` 保存。

## 功能

- 当前页面中的英文单词会被批量识别。
- `moon-well` 根据用户历史返回陌生词和释义。
- 陌生词在阅读器中以波浪下划线标识，悬停或点击可查看释义及上次学习信息。
- 每次遇到单词都会保存：单词、句子、用户、书籍 ID/名称、章节、页码、EPUB CFI、学习时间和次数。
- 历史记录使用 Elasticsearch 的 `reading_vocabulary` 索引保存；原有 `vocabulary` 索引继续提供词汇释义。

## 配置

在 magicbook 进程配置：

```bash
MOON_WELL_READING_URL=https://moon-well.example.com
```

调用 `/reading-vocabulary/**` 时使用 moon-well 标准 `authorization: Bearer <token>` 请求头。moon-well 通过 JWT 的 `UserContext` 确定用户，客户端不能通过 `userKey` 冒充其他用户。

## 当前范围

第一版接入 EPUB/KEPUB 阅读器，因为 epub.js 能直接访问当前章节 iframe 的 HTML 文本和 CFI 位置。PDF、TXT、漫画和音频阅读器尚未接入这套识词流程。

如果没有配置 moon-well 地址或令牌，阅读器保持原有行为，不显示错误弹窗。
