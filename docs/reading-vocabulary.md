# 阅读单词学习

EPUB 阅读器支持识别当前可见页面的英文单词，并将学习上下文交给 `moon-well` 保存。

## 功能

- 阅读器把**当前页完整文本**上报给 moon-well。
- `moon-well` 负责分词、提取句子上下文、判定陌生词与查询释义。
- 陌生词在阅读器中以波浪下划线标识，悬停或点击可查看释义及上次学习信息。
- 每次遇到单词都会保存：单词、句子、用户、书籍 ID/名称、章节、页码、EPUB CFI、学习时间和次数。
- 历史记录使用 Elasticsearch 的 `reading_vocabulary` 索引保存；原有 `vocabulary` 索引继续提供词汇释义。

## 接口设计

**请求**（magicbook `/ajax/reading-vocabulary` → moon-well `POST /reading-vocabulary/analyze`）：

```jsonc
{
  "userKey": "跨应用稳定标识（Authentik sub / UUID）",
  "bookId": 7,
  "bookName": "Sample Book",
  "chapter": "Chapter 1",
  "page": "3/120",
  "cfi": "epubcfi(...)",
  "pageText": "当前页完整文本（由 moon-well 分词）"
}
```

> 说明：早期版本由前端逐词上报 `words: [{word, sentence}]`，一页数十词使 payload 过大。
> 当前改为只上报整页文本，**分词、句子上下文提取、查词归档全部由 moon-well 完成**。

**响应**（moon-well → magicbook → 前端标注）：

```jsonc
{
  "success": true,
  "code": 200,
  "result": [
    { "word": "serendipity", "translation": "好运", "lastBookName": "...",
      "lastChapter": "...", "lastPage": "...", "lastStudyTime": "...",
      "studyTimes": 2, "unknown": true }
  ]
}
```

前端仅在 `unknown: true` 时用波浪线标注该词。

## 配置

在 magicbook 进程配置：

```bash
MOON_WELL_READING_URL=https://moon-well.example.com
MOON_WELL_INTEGRATION_TOKEN=replace-with-a-long-random-token
```

在 moon-well 进程配置同一个令牌：

```bash
MAGICBOOK_INTEGRATION_TOKEN=replace-with-a-long-random-token
```

magicbook 通过自己的 Flask 登录会话确定用户，并在服务端代理请求；令牌不会下发到浏览器。moon-well 的 `/reading-vocabulary/**` 是集成接口，使用 `X-Magicbook-Token` 校验令牌。

`userKey` 是 magicbook 的**跨应用稳定标识 `user_key`**（非自增 `user.id`）：

- Authentik/OIDC 用户：`user_key` = Authentik `sub`（与 moon-well 侧 `app_user.oidc_subject` 一致，两端据此映射为同一人）。
- 本地用户：`user_key` = 创建时生成的 UUID4。
- 存量用户由启动迁移回填（OIDC 用户沿用 sub，其余生成 UUID），幂等。

> 历史数据迁移：升级前以 `user.id` 上报的 ES 记录，需用 `docs/temp/scripts/export_user_key_map.py` 导出 `{old_id: user_key}` 映射，交由 moon-well 侧 `migrate_reading_vocabulary_userkey.py` 重写（见 sso-user-unification 设计文档 §7）。

## 当前范围

第一版接入 EPUB/KEPUB 阅读器，因为 epub.js 能直接访问当前章节 iframe 的 HTML 文本和 CFI 位置。PDF、TXT、漫画和音频阅读器尚未接入这套识词流程。

如果没有配置 moon-well 地址或令牌，阅读器保持原有行为，不显示错误弹窗。
