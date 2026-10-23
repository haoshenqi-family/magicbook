> 归档：R203（B4 拆分漏带跨模块别名致 4 个段落按钮失效）原样搬移自 `response.md`。
> 2026-10-23 R216 写入触发轮转搬移（与 R214 的轮转叠加后窗口仍达 11，续搬最旧一节），只搬移原文、不总结、不改写。

## 2026-10-21（R203：验收时报 `RT is not defined`——B4 拆分漏带跨模块别名，4 个段落按钮失效）

### R203（用户验收 R200 时贴出：`reader-tts.js:657 Uncaught (in promise) ReferenceError: RT is not defined at bookPlayerStart`）

- **不是本轮改动引入的**：`git log -L` 定位到 `d2a00fff`（2026-10-16，R183 B4 批次 7 把段落朗读与整本连播整块迁出 epub.js）。迁移时 `RT.` / `RI.` / `AN.` 三处跨模块调用连前缀一起搬走，但这三个别名原本是 epub.js 的**函数作用域**变量（`var RT = window.ReaderTedAudio`），新文件里没有重新声明。每个 reader 模块是独立 IIFE，拿不到别人的闭包 → 运行时 `ReferenceError`。
- **影响面比报障更大（4 个按钮，全部「点了没反应」）**：① 段落「朗读」——**所有书**（`speakParagraph` → `RT.isActive()`）；② 整本连播在 TED 无原声回落时（`bookPlayerStart`，用户报障点）；③ 段落「译」按钮（`RI.translateParagraph`）；④ 批注 / AI 批注按钮（`AN.openPopover`）。后两个是加守卫时顺手扫出来的，不在报障范围内。
- **为什么两把静态锁都没响**（已写进新用例 docstring）：① `test_每个跨模块调用都在导出面上` 读的是**拼接后的 blob**——epub.js 段里的 `var RT` 让 reader-tts.js 段的 `RT.` 照样对得上号；② `test_模块不得直接引用_epubjs_闭包内的符号` 只扫**小写开头且长度 ≥5** 的标识符（`RT` 三条都不满足），还被 `_GLOBALS` 白名单兜住。教训：静态锁的**粒度**和**字符类**本身就是漏检来源，「拼接后检查」不能替代「单文件检查」。
- **修法**：`reader-tts.js` 补 `var RI/AN/RT = window.Reader*`；RT 用空实现兜底（让位类调用空转优于连累朗读），RI/AN 不兜底（用户动作空转就是本类事故本身，宁可让 epub.js 的模块缺失检查把话说明白）；顺手删掉重复的 `var TTS_ENGINE_KEY`。
- **守卫**：`tests/test_reader_module_surface.py` 新增 `test_跨模块别名必须在所属文件内声明`——按**单文件**粒度检查，先剥离注释与字符串（避免「注释里提到 `RS.setHost`」误报），别名清单复用 `ALIASES` 自动纳入新模块。**反向变异**（删掉 RT 声明）实测报红，确认这条锁真的会响。
- **测试**：`test_reader_module_surface.py` 6 passed；reader/朗读/TED 定向 **60 passed**；合并后全量 `pytest -q` **648 passed / 0 failed**（较上轮 +1，即新增守卫）。
- **上线**：branch `fix/r203-rt-alias`，merge develop **`a9ebfd58`**，push `11d041b9..a9ebfd58`。**线上实证**：部署窗口后 `curl https://magicbook.haoyuhang.top/static/js/reading/reader-tts.js` → HTTP 200、35,950 字节，文件内含 `var RT = window.ReaderTedAudio`（第 24 行起 `var RI = window.ReaderImmersive`）——这次拿到了「线上真跑新代码」的直接证据，不再是只靠可达性。
- **边界（如实）**：只做了静态与测试层验证 + 线上文件比对，**没有在浏览器里逐一点击 4 个按钮**；TED 书若原声未缓存，现在会正常走 TTS 连播（不会再崩），但仍是机器音——那是 MAGICBOOK-213 的未修项，不是本 bug。
- **台账**：R203（PingCode **MAGICBOOK-214**，进行中，待用户验收）。
