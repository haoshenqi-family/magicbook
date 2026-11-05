# 回应归档 · R270

## R270 · 阅读器 bookUrl 大小写致 /show 404——首页继续阅读打开空白阅读器（2026-11-03）

### R270（缺陷：截图/视频会话中生产实测发现，R229 同款「顺路修复」）

- **结论先行**：`read.html` 的 `bookUrl` 单点加 `|lower`，一行修复 + 两条静态锁定测试。首页「继续阅读」卡片（R213-C 透传阅读进度里的大写格式 `EPUB`）从此不再打开永久空白的阅读器。**已上线待验收**。
- **发现链**：2026-11-03 产品视频录制会话，puppeteer 打开 `/read/145/EPUB`（与首页继续阅读卡片同款链接）epub.js 永不渲染（0 个 iframe）。逐层定位：`/show/145/EPUB/file.epub` → 404（Flask 页），`/show/145/epub/…` → 200（Matilda 2.3MB）；匿名直连容器两种写法都 302（路由都在、非权限问题）；容器内文件 `Matilda - Roald Dahl.epub` 小写扩展名在盘。
- **根因**：`serve_book`（web.py:2050）在大小写敏感文件系统上按 **URL 段原样**拼扩展名（`send_from_directory(..., data.name + "." + book_format)`）。Calibre 落盘扩展名恒小写；`/read/<id>/<book_format>` 的入口里，home.html:22 把进度记录的大写 `EPUB` 原样透传，read.html:186 再透传给 `url_for('web.serve_book')` → 找 `<name>.EPUB` → NotFound → epub.js 拿不到书文件 → 阅读器空白。detail.html 的「首章试读」（`|lower`，L179）与「继续阅读」（`or 'epub'`，L515）两条入口是对的——所以从详情页进阅读正常、从首页卡片进就空白，hsq 日常走详情页入口躲过了它，隐患存活至今。上游引入点是 2024-12-08 `01215aaa`（KEPUB 支持）把字面量 `'epub'` 换成了变量透传。
- **修复**：`cps/templates/read.html` bookUrl 一处 `book_format=book_format|lower`——所有阅读入口共用此模板，单点收口；epub.js `restore:true` 的 IndexedDB 缓存键也随之统一为小写，跨入口命中同一缓存。未动 `serve_book`（保持与上游贴合，URL 侧收口最小）。
- **测试**：新增 `tests/test_reader_bookurl_case_r270.py` 2 例（正向锁定 `|lower` 形态 + 防回退断言「不许再出现原样透传」）；全量 **1274 passed / 0 failed**（1273 基线 + 1 新文件）。
- **上线与核验**：实现 `600fe72b` + merge `276f77ee` 推 `origin/develop`（32e32f58..276f77ee），fnOS 链 `00:06` END OK（`af1cd8f0f78ed85b`），容器 healthy；线上核验 `/read/145/EPUB`（大写入口）渲染出的 bookUrl 已是 `/show/145/epub/file.epub` 且 GET 200、epub iframe 正常渲染（本会话视频/截图全走通）。
- **连带效应**：与 10-28 未结案的「整本朗读后正文空白」（wholebook-whitescreen）是否同源**未证实**（该案症状是「开始朗读后」空白，本案是「打开即空白」），留给原案复测时排除。
- **状态与驻留**：worktree `../magicbook-r270-reader-bookurl-case`，分支 `fix/r270-reader-bookurl-case`，按闸门保留待验收。requests.md 条目 270 已回填。冲突记录：无（claim.sh 得 270）。

