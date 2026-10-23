# 译文栏（translation rail）· L3 实现说明

> 状态：R215（MB-14）已实现，待验收（2026-10-23）
> 读者：修改阅读器翻译行为的人。用户可见说明见 [reading.md](../../readme/reading.md)；本次设计见 [r215 HLD](../../../project/iterations/1.0/r215-reader-ai-panel/hld.md)。

## 实现方式

- **模式开关**：`#immersive-translate`（`reader-immersive.js`）只切换 `calibre.reader.translationRailMode`。开启 = 打开右栏 + 进入点段翻译模式；关闭 = 收起右栏、清除选中。旧键 `calibre.reader.immersiveTranslate` 初始化时删除，不再读取。
- **选中**：每个渲染帧由 `epub.js` 的 `rendered` 钩子调用 `RI.bindContent(content)`，在 iframe document 上挂 `click`。模式关闭、存在选区、命中链接/按钮/段尾工具时直接返回；否则取最近的叶子段落交给 `selectParagraph`。
- **译文栏**：`read.html` 的 `#translation-rail` 固定在外层文档（不进入 iframe）。桌面占 `clamp(300px, 32vw, 420px)`，≤900px 改为 50vh 底部抽屉；`body[data-side-panel="translation"]` 让 `#main.reader-main` 缩宽。
- **请求与缓存**：选中段落后先查 `localStorage['calibre.reader.translation.<bookKey>']`（`{paragraphHash: text}`），miss 才 POST `readingTranslateBatchUrl`（单段 `paragraphs:[text]`，带 `bookName`/`chapter`）。响应按 `railRequestSeq` 与 `selectedEl` 双重校验，后选覆盖先选；成功写缓存。
- **零插入**：译文只写 `#translation-rail-body` 的 `textContent`，正文 iframe 内不插入任何译文节点；段尾工具条保持在段落尾部行内（R215 验收修订：绝对定位浮层会压字，已回退）。

## 边界条件

- 翻页/换章**不清空**右栏：保留上次选中段与译文；另选段落或关闭模式才替换。元素已脱离文档时，右栏保留文本并追加「该段已不在当前页」。
- 关闭 AI 面板时若翻译模式仍开启，右栏自动恢复；打开 AI 面板时右栏只收起、模式保留。
- 请求失败显示上游文案 + 重试；CSRF 过期走 `ReaderCore.reloadIfCsrfBlocked` 的整页自愈。
- PDF/TXT 阅读器没有本模块，不提供译文栏；它们的 AI 面板仍按 R215 改造。
- 整本翻译任务写入的段落缓存与本功能共用同一 key，因此整本任务完成后点段即可看译文，不再自动插入正文。
