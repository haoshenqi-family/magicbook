# 回应归档 · R263

## R263 · 阅读器朗读速度选项：TED/博客类原声与整本连播支持 0.75x/0.5x（2026-11-01）

### 修订轮（同日用户验收：「这个UI 不太好」）

- **意见① 语速显隐时机**：改为起播后出现（与「停止」同进退）。落点=共用渲染点 `ttsButtonsRender`：无播放态 `display:none`、有播放态显示；模板默认隐藏。单段朗读不经该函数，与「停止」按钮行为一致，档位沿用记忆值。
- **意见② 三钮分组**：`read.html` 包 `<span id="tts-group" class="tb-group">`，CSS 分段控件（共享浅底胶囊 + `.tb-tool + .tb-tool` 分隔线——display:none 不改 DOM 邻接，停止隐藏时语速左缘分隔线仍在）；未播放时组内仅朗读一颗。
- **意见③ 收纳**：书签（自动记录阅读进度后冗余）与整本翻译常驻「更多」菜单；reader-toolbar.js 拆 `MENU_ALWAYS=[bookmark, whole-book-translate]` / `MENU_NARROW_ONLY=[setting, fullscreen]`，宽屏也收，「更多」常显；导览撤书签步骤（onboarding.js + 锚点测试）。
- **自检与测试**：真实 CSS 拼 mock 双状态截图（桌面+390px）自检通过（窄屏折算 ≈292px 放得下）；修订静态锁 5 条并入 test_r263_tts_speed.py，定向 45 + 回归 153 = **198 passed**。修订实现 `6dfe2975`。

### R263（用户：「增加一个 0.75 0.5 朗读速度的选项。博客类的对于初学者可能太快了」）

- **结论先行**：阅读器顶栏新增「语速」按钮（`#tts-speed`，位于「停止」之后），点击在 1.0x → 0.75x → 0.5x 循环并即时生效，选择存 localStorage（`calibre.reader.ttsSpeed`）跨会话记忆；TED/博客类真人原声伴听、整本 TTS 连播、单段朗读三条链路统一套速，`preservesPitch` 变速不变调。
- **方案选型**：客户端 `playbackRate`，不动服务端——音频缓存键=SHA-256(段落原文)（moon-well 永久缓存设计），服务端变速要么同文三份音频要么把速度掺进缓存键击穿全部存量缓存。档位钉死三档不做自由输入，`ttsSpeed()` 白名单校验脏值回落 1。
- **链路覆盖**（静态锁逐条钉住）：原声 `tedAudioStart()` 的 `new Audio` 后套速（用户点名的初学者主场景）；连播 `startAudio()` 每块新建 Audio 重套（暂停/继续沿用原元素无需重套）；单段朗读 activeTts 同；浏览器兜底 `utterance.rate = 0.95 × 档位`（utterance 不可中途改 rate，下一句生效）。TED 时间轴高亮按原声时钟走，`currentTime` 随 playbackRate 同比例变速，命中逻辑零改动。
- **UI 细节**：图标槽显示当前档位（15px 加粗，「0.75x」五字符不能按 24px 摆）；载入即回显记忆档位；书既无原声也无 TTS 端点时随 `#tts-book` 一并隐藏；窄屏折叠清单（reader-toolbar.js）不动，语速与朗读组同留主栏。
- **测试**：新增 `tests/test_r263_tts_speed.py` 5 条静态锁；定向回归 `test_reader_module_surface + test_i18n_seed_contract + test_ted_audio_proxy + test_nav_settings_dropdown + test_reader_theme_sync + test_design_plan_r257` 共 49 passed，第二批 `test_reader_r226_acceptance + test_reader_lens_handoff + test_onboarding_tour + test_onboarding_reader_visual + test_r261_jinshu_borrow + test_common_api_contract + test_learning_pages_static + test_mail_ui_r243` 共 128 passed，合计 **177 passed / 0 failed**。
- **文档四问**：能力 → L1 `readme/reading.md` 朗读条补「语速三档」句；契约 → 无 HTTP 契约变化；实现/边界 → LLD `iterations/2026-11-tts-speed/lld.md`；需求 → `REQUIREMENTS.md` 变更记录加 R263 行。
- **上线**：实现 `6cf91a65` + 台账 `f8ec9187` 快进推送 `origin/develop`（`7e65f174..f8ec9187`）；fnOS `build END OK (f8ec9187)`、app-manager `deploy SUCCESS`、容器 `running/healthy`。
- **窗口与驻留**：写入前窗口 9 节（本会话先按「写入即检查」把最旧 R253 整节搬至 `response-archive/response-R253.md` 并登记索引），本条写入后窗口 10。worktree `../magicbook-r263-tts-speed`（分支 `feat/r263-tts-speed`）按闸门保留待验收。
- **总结**：requests.md 条目 263 已从占位回填；本条为回应。冲突记录：占号时 262 已被并行会话（整本成本摘要修正）占走，自动顺延 263，无撞号。
