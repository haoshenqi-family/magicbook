# 回应归档 · R283–R284（2026-11-05 ～ 2026-11-06）

> 2026-11-27 R295 写入触发轮转搬移：写入前窗口已有 11 节（并行会话累积），
> 本次连同新增 R295 一并压回 10 节，故把最旧两节 R283、R284 原样搬入本文件。
> 只搬移原文，不总结、不改写、不改编号。

---

## R283 · 修改意见（挂 R280）：tabBar「伴读」改为「AI」（2026-11-05）

**对 R283 的回应**：用户 12:32 原话「伴读改为AI」。先核清「伴读」在小程序里的 4 处
用户可见文案（底栏 / 导航栏标题 / 页内标题 / 登录页品牌副标题）与 README、注释里的分布，
再交互确认口径：**只改 tabBar**，其余功能名仍「AI 伴读」；改完立刻重传体验版。

- **为什么不是全局替换**：「AI 伴读」在网页阅读器抽屉、伙伴系统与 moon-well 场景名里
  是既有能力名，全局替换会污染无关模块。本次只是底栏入口标签的用词收敛。
- **改动只有一行**：`app.json` tabBar 第二项 `text: "伴读"` → `"AI"`，`pagePath` 仍是
  `pages/chat/chat`；接口、请求体、prompt 与后端零改动，moon-well 不受影响。
- **守卫同时钉「改了」与「没越界」**：新增 `tests/test_r283_tab_ai.py`，断言四项文案
  `["复习", "AI", "词汇量", "我"]` 与 `pagePath` 不变，并反向断言 `chat.json` /
  `chat.wxml` / `login.wxml` 仍含「AI 伴读」——防止后续顺手把功能名一起改掉造成口径漂移。
  R280 静态锁里写死的「伴读」同步改为「AI」，R275 注释补 R283 标注。
- **验证**：小程序静态锁 **54 passed**（R271–R283，排除 R279 后端集成用例）；
  `app.json` JSON 解析通过，四项 tab 实值回读正确。
- **状态**：**已上线待验收**（复用验收期驻留 worktree `../magicbook-r280-ai-chat`，
  分支 `feat/r280-ai-chat`，已 merge 并 push `origin/develop`；体验版 `1.0.1` 已上传，
  65.3 KB / 66,836 Byte；待后台设为体验版并真机验收，通过后才置 Completed）。
- **状态回写**：修改意见按治理「必须挂到已有需求 / 任务、不做无主修复」，**不新建
  PingCode idea**，挂 `MB-239`（`xB0tmxqa`，R280 载体，仍 `In progress`，
  待真机验收后才置 `Completed`）。本轮虽占号 R283，但 worktree 按
  「一次会话一个 worktree / 验收期驻留续作」复用 r280 树，不新开。
- **部署**：只改小程序包，不涉及后端；上传源为主检出 `develop@a3a205e5`，沿用 CLI
  服务端口 13564，且不带 `--info-output`（R280 实测会触发 IDE `code 17` 二维码路径报错）。
  `cli upload -v 1.0.1` 返回 ✔ upload，TOTAL **65.3 KB / 66,836 Byte**；
  比 R280 的 `1.0.0`（66,840 Byte）少 4 字节，正好是「伴读」6B → 「AI」2B 的差值。

**台账总结**：`requests.md` 第 283 条本处回填；`response.md` 写入前 10 节、本次 11 节，
最旧一节 R273（小程序邮箱登录）原样搬入 `response-archive/response-R273.md` 并在顶部登记索引。

## R284 · 页面引导入口下线，只保留右上角 Help（2026-11-06）

**对 R284 的回应**：用户口径「页面上的引导入口全部下线掉。只保留右上角的帮助的入口」。
修改意见挂 R226 后续，不新建 PingCode idea。

- **唯一入口**：右上角 Help 下拉的 `#top_onboarding`。断开 `onboarding.js`
  `runSegment` 的自动邀请 / 右下常驻按钮与 `showEntryAgainIfNeeded` 的收尾重挂；
  删 `/reading/settings` 引导区块与 `reading-preferences.js` 转发。
- **函数体保留**：`showInvite` / `showReaderHelp` 仍在但不再调用——R111/R226 视觉守卫
  锁其几何与文案形制，删除会让那批守卫失去锚点。`read.html` 挂载点保留，导览从 Help
  启动后仍可跨页续到阅读器段。
- **文案同源**：收尾卡改指右上角 Help，`i18n_seed.html` + zh po/mo 同步；只重编译
  zh_Hans_CN 的 mo（整树编译会撞上 `it` 语既有的 `unknown named placeholder 'nome'`）。
- **验证**：更新 `test_reader_r226_acceptance.py`（R226 断言改「调用链断开」）与
  `test_onboarding_tour.py`（中文种子词条）；定向回归全绿，`node --check` 通过。

**已否决并撤销（12:31，用户「撤销我这两轮改动」）**：同批做过的「恢复生词 hover
释义」（`span.title = gloss`）与「hover 即时释义卡 + 划词翻译兜底 + 去掉
`cursor:help`」两轮改动全部回滚。起因是用户随后给出参考截图，明确期望的是
**MagicLens 扩展的划词气泡**（紫色 `#8b5cf6` 波浪线 + 译/详/🔊/认识/生词/AI/✕），
不是 magicbook 内置 hover 卡片；扩展接管高亮时内置 `markVocabulary` 让位，
内置改动本就不会执行。回滚范围：`epub.js` / `reader.css` / `reader-core.js`
恢复到 R284 之前、删除 `tests/test_r284_hover_gloss.py`、L2 `reading-vocabulary.md`
与 L1 生词条目回退；引导入口下线部分全部保留。生词链路回到 R268 原状。

- **状态**：已上线待验收；worktree `../magicbook-r284-hover-gloss-onboarding` /
  分支 `feat/r284-hover-gloss-onboarding` 原样保留，真机验收通过后才 `worktree remove`
  → `branch -d`。

**台账总结**：`requests.md` 第 284 条本处回填；`response.md` 写入前 10 节、本次 11 节，
按「写入即检查」把最旧一节 R274 原样搬入 `response-archive/response-R274.md`
并在顶部归档索引登记，窗口回到 10 节。冲突记录：无撞号；
唯一口径变更是 R226 的「阅读器右下使用引导」被 R284 取代，已在 L1/L3 标注。

