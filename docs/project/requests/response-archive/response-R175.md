# response-R175.md — R175 归档

> 从 `response.md` 原样搬移（2026-10-16 R188 写入触发轮转，窗口回 10 条 request 内）；只搬移原文，不总结、不改写、不改编号。

## 2026-10-15（R175：修复 TED 音频仍无声——阅读页 CSP 拦下 MinIO 外网直链）

### R175（用户复测：moon-well R181 直链已就绪，仍报 `Loading media from 'https://home.haoshenqi.top:9001/…' violates … CSP directive: "media-src 'self' blob: https://dict.youdao.com"`）

- **现象**：moon-well R181 已把对外音频基址改为 MinIO 公共 HTTPS 直链（`https://home.haoshenqi.top:9001`）并放开匿名只读，用户复测 TED 音频**仍无法播放**，浏览器控制台给出 CSP 违规报文（media 加载被拦）。
- **根因（CSP media-src 白名单）**：R172 起 TED 原声由浏览器**直连** moon-well 返回的 MinIO 公共直链播放（不经 magicbook 代理），而阅读页 CSP 的 `media-src` 只放行 `'self'` / `blob:`（段落 TTS）/ `https://dict.youdao.com`（划词发音）——跨源 media 未在白名单内即被拦，播放静默失败、服务端无异常日志。与 R181 的「投递」根因**分属两层**：R181 修好「直链对不对」，本条修「阅读页准不准放」。
- **修法（`cps/web.py` 一处，仅阅读页）**：`add_security_headers` 中，`request.endpoint == "web.read_book"` 分支的 `media-src` 追加 `https://home.haoshenqi.top:9001`（沿用有道源同款硬编码先例；非阅读页不 emit media-src，不放宽全局攻击面）。
- **守卫（1 条正向 + 反向变异实测）**：`tests/test_csp_media.py` 新增 `test_reader_page_allows_ted_audio_minio_origin` 正向锁「阅读页 media-src 含 MinIO 外网源」，保留 `test_non_reader_pages_still_block_blob_media` 负向锁；本轮变异实测：摘掉该源 → 1 failed（报文精确指出 directive），还原 → 4 passed。
- **附带澄清（判定无害）**：用户同贴的 `Blocked script execution in 'about:srcdoc' because the document's frame is sandboxed…` 系 epub.js 内容渲染沙箱的既有告警——epub.min.js 默认 `allowScriptedContent: false`，iframe 为 `sandbox="allow-same-origin"`，被拦的是**书内脚本**（非父页 audio），与本次阻塞无关，不改。
- **交付状态**：worktree `../magicbook-ted-audio-csp`，分支 `fix/r175-ted-audio-csp`（基线 `origin/develop` `75987180`）；开发态守卫 4 passed；待 merge → push `develop` 上线后交真机复测（TED 书点「整本朗读」应出真人原声、控制台无 media-src 违规）。
- **对话记录**：requests.md 占号 175；本条为回应；写入前 response.md 窗口 9 个 request（R164 起），写入后 10 个，未触发轮转。冲突记录：主检出 develop 工作区存在并行会话未提交的 R174 文档任务，本树基线止于 R173，按「续编空号」取 R175，无撞号。
