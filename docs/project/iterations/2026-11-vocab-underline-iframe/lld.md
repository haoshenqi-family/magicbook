# LLD · 阅读器生词波浪线未注入 EPUB iframe（R268）

- 状态：开发中
- 关联需求：R268（requests.md 占号 2026-11-02）
- 报告来源：Feishu「播客刚点进去阅读不会显示生词，手动刷新才显示」，后补充 `/ajax/reading-vocabulary` 200 返回生词、刷新无效、启用 MagicLens 重新扫描本页才出现。

## 1. 现象与定位

线上阅读页请求 `/ajax/reading-vocabulary` 已 200 返回生词，前端 `markVocabulary` 也已按 `record.unknown` 把词包成 `span.reading-vocabulary-unknown`，但页面看不到波浪下划线；刷新不恢复，只有 MagicLens 高亮引擎重新扫描（它自行向 iframe 注入样式）后才可见。

根因：EPUB 正文由 epub.js 渲染在**同源 iframe**（`about:srcdoc`，`sandbox="allow-same-origin"`）中；`.reading-vocabulary-unknown` 的波浪下划线/悬停规则只写在父页 `cps/static/css/reader.css`。父页样式表不跨文档作用到 iframe，因此 iframe 内的 span 计算样式为 `text-decoration: none`，视觉上等于「生词不显示」。控制台 `Blocked script execution in 'about:srcdoc' … allow-scripts` 是 epub.js 内容沙箱对书内脚本的既有告警（R175 已判定无害），与本问题无因果。

本地复现（真实 magicbook 实例 + 测试 EPUB + mock analyze）：`decoration = none|solid`；手动向 iframe 注入该规则后立即变为 `underline|wavy|rgb(217,139,0)`。

## 2. 修复

把基础规则加入 `cps/static/js/reading/reader-core.js` 的 `READER_TOOLS_STYLE`（该样式由 `injectReaderToolsStyle(doc)` 经 `rendered` 链路注入每个正文 iframe，与 R261 gloss 的 `::after` 规则同源）：

```
.reading-vocabulary-unknown{text-decoration:underline wavy #d98b00 1px;text-decoration-skip-ink:none;cursor:help}
.reading-vocabulary-unknown:hover{background:rgba(217,139,0,.16)}
```

父页 `reader.css` 的同名规则保留（父页自身仍可能需要），不影响 iframe。

## 3. 验证

- 真实浏览器（Chrome 148 + Selenium）本地复现：修复前 iframe 内 span=3000 且 `text-decoration:none`（不可见）；修复后首次进入即 `text-decoration:underline wavy`（可见），无需刷新。
- Before/After 见 `evidence/before.png`、`evidence/after.png`（同一本地实例、同一测试书与视口，仅切换分支版本；基线为修复前提交 ff8073dd，改为本分支）。
- 静态锁：`tests/test_r268_vocab_underline_iframe.py`（3 条）。
- 定向回归：`test_r268… + test_r261_jinshu_borrow` 11 passed；`test_reading_vocabulary + test_reader_module_surface + test_r263_tts_speed` 47 passed。

## 4. 边界

- 仅影响内置高亮；MagicLens 接管时 `markVocabulary` 仍按 R146 让位，不受影响。
- 本地无法拉取线上 book 444 的 EPUB（阅读页需登录），故用结构等价的测试 EPUB 复现同一渲染链路；线上验收请用该播客书确认。
