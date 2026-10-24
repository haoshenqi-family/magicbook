# AC — R215 阅读器与 AI 伴读面板

> 状态：**开发中，待逐条验收**（2026-10-23）
> 关联：[hld.md](../hld.md) · [lld.md](../lld.md) · PJM [MB-14](https://haoshenqi.pingcode.com/pjm/workitems/SE5FkqOT) · Ship MAGICBOOK-222
> 回归视口：桌面 1440×900 · 移动 390×844（对应 QA 报告 §五/§八截图重拍对比）
> 拍板口径见 HLD §4；本文件只写「怎么算过」。

## A · 顶栏与段尾控件

- [ ] **A1** GIVEN 桌面 1440×900 WHEN 打开任意 EPUB THEN 顶栏图标字形 ≥24px、每个控件带中文文字标签（翻译/朗读/书签/设置/全屏），基部不透明度不再出现 0.25 的叠加；hover 时对比度提升（守卫：`test_reader_r215_ui.py` 钉住 `.tb-label` 与去双重 opacity）
- [ ] **A2** GIVEN 桌面 WHEN 鼠标移入/移出段落 THEN 段尾出现/隐藏 4 个 24px 图标（朗读/翻译/批注/AI 伴读），点击语义与现状一致
- [ ] **A3** GIVEN 390×844 触屏 WHEN 看段尾 THEN 只显示一个 44×44 的「⋯」按钮；单指点击弹出四项带文字菜单，每项触达 ≥44px，点击任一项行为与桌面图标一致
- [ ] **A4** GIVEN 390×844 WHEN 看顶栏 THEN 主位只留「翻译 / 朗读 / 更多」，其余项收进「更多」菜单；所有可点控件单指可点（≥44px），无横向滚动、书名不挤出视口
- [ ] **A5** GIVEN 窄屏/宽屏来回切换 WHEN 窗口跨过 767px THEN 工具节点在「更多」菜单与顶栏之间搬移，不出现重复 ID、不丢事件监听（`#bookmark` 点击仍生效）

## B · 翻译（2026-10-23 验收回滚：段内内联）

- [ ] **B1** GIVEN 翻译关闭 WHEN 点顶栏「译」THEN 当前可见页段落批量翻译，译文逐段插入各段下方；再点一次移除所有译文
- [ ] **B2** GIVEN 任意段落 WHEN 点段尾「译」THEN 译文插入该段下方；再点一次收回；命中缓存时不发请求、即时显示
- [ ] **B3** GIVEN 翻译请求失败 WHEN 译文块渲染 THEN 显示可点击重试的错误块（原文「Translation failed, click to retry」），不静默空白
- [ ] **B4** GIVEN 译文已显示 WHEN 到达自动隐藏时长 THEN 译文块消失并复位「译」按钮；设置 `Translation display time per 100 words` 改动后生效
- [ ] **B5** GIVEN 翻页 / 换章 WHEN 新页面渲染 THEN 仅回填已缓存译文，不自动发起新请求
- [ ] **B6** GIVEN 整本翻译任务完成 WHEN 再次翻到对应段落 THEN 缓存命中后译文自动显示（整本翻译提示文案保持「完成后阅读时自动显示」）
- [ ] **B7** GIVEN 译文插入/替换 WHEN epub.js 重分页 THEN **允许正文重排**（用户 2026-10-23 明确「宁可重分页」），不因此判失败
- [ ] **B8** GIVEN 译文显示中 WHEN 打开 AI 面板 THEN AI 以 420px 覆盖式抽屉盖在正文上，关闭后原样恢复（二者无联动）

## C · AI 伴读面板

- [ ] **C1** GIVEN 桌面 1440×900 WHEN 打开 AI 面板 THEN 面板为右侧 420px 覆盖式抽屉，正文宽度与阅读位置不变、不触发重分页；关闭后原样露出正文（2026-10-23 验收回滚：原 50vw 停靠方案被否决）
- [ ] **C2** GIVEN 390×844 WHEN 打开 AI 面板 THEN 面板为 100vw×100vh 全屏抽屉，无圆角/拖拽条（恢复 R215 之前形态）
- [ ] **C3** GIVEN 面板头部 WHEN 看 4 个操作按钮 THEN 桌面显示文字标签（新建/重命名/删除/记忆），窄屏显示图标但具备 `title` 与 `aria-label`；关闭按钮触达 ≥44px
- [ ] **C4** GIVEN 阅读器右下角 WHEN 未打开面板 THEN FAB 呈现为带品牌色外环与「伴读」标签的按钮，不再像白色 spinner；头像裂图/未装备时回落「AI」文字；移动端首次打开后标签收起
- [ ] **C5** GIVEN 提问 WHEN 点击发送 THEN **200ms 内**出现「思考中 · 0s」气泡与 FAB thinking 动效，此后每秒计时；首个 delta/tool/final/error 到达即停表并复用同一气泡，不出现双气泡
- [ ] **C6** GIVEN 页面上下文提取超过 1200ms（PDF 大页）WHEN 发送 THEN 仍按超时继续请求（空 `pageText`），不出现「点了没反应」的空白期；上下文按时返回时正常携带

## D · 口径与避让

- [ ] **D1** GIVEN EPUB / PDF / TXT 三种阅读器 WHEN 打开 AI 面板 THEN placeholder 分别为「询问本章内容…」/「询问当前页…」/「询问本文…」，与实际发送范围一致
- [ ] **D2** GIVEN 阅读器界面 WHEN 未打开译文栏 THEN 幽灵「?」位于右下 FAB 上方，不与页码（左下）重叠；译文栏打开时「?」隐藏，关闭后恢复（AI 浮层不隐藏「?」）
- [ ] **D3** GIVEN 顶栏翻译开关 WHEN 开/关 THEN 文案、实心底、`aria-pressed` 三者同步，颜色对比达到可辨识（不再只靠 1px 橙边）

## 全局

- [ ] **G1** 1440×900 与 390×844 两档截图与 QA 报告 `b1-reader.png` / `c2-translate.png` / `c3-ai-panel.png` / `d1-ai-15s.png` / `f2-mobile-reader.png` 逐项对比，验收报告附新截图
- [ ] **G2** 既有能力回归：段落朗读、整本连播、TED 原声、段落批注、AI 批注、划词翻译、整本翻译入口均可用；`tests/test_onboarding_tour.py`、`test_reader_module_surface.py`、`test_reader_lens_handoff.py` 全绿
- [ ] **G3** 新增 `tests/test_reader_r215_ui.py` 全绿，并做反向变异：恢复双重 opacity / 把译文插回正文 / 把「思考中」移回 `streamChat`，三处均须报红
- [ ] **G4** 文档四问回填：L1 `reading.md`（翻译模式与面板行为）、L2 `reading/interface.md`（无接口变化需注明）、L3 新建对应功能说明、LLD 状态行从「设计」改「开发中/已上线」；`plan.md` MB-14 行同步
