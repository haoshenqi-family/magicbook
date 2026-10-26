# 回应归档 · R223

> 2026-10-26 R232 会话合并 origin/develop（并入 R233 一节、保留本分支 R232 一节）后窗口达 11 节，原样搬移不改写。

## 2026-10-24（R223：Buddy 悬浮球化——透明头像 + hover 径向快捷气泡，/buddy 可配置）

- **落点**：FAB 结构改 `#ai-companion-fab-wrap`（定位/拖拽/吸附迁 wrap，localStorage 键不变）+
  按钮本体透明头像态（无头像兜底保留蓝底「AI」文字）；删除「AI 伴读」label 与 hover 浮出规则。
  hover/focus 弹出 `.ai-bubble` 径向气泡，弹簧曲线展开；展开方向按 FAB 吸附侧自适应
  （右半屏向左、左半屏向右、贴顶/底时向下/上偏），tooltip 随侧翻边。
- **配置链**：`GET/POST /ajax/buddy/quick-actions`（`cps/routes/buddy.py`），动作全集
  chat/翻译/朗读/书签/学习页/书库/我的，服务端校验 4–5 个且白名单去重；`/buddy` 页 chip 选择器
  （chat 固定不可取消）。存储 `view_settings['buddy']['quickActions']`。label 请求期 gettext
  （导入期冻结只能拿英文 msgid——code review 修正点；另修正 `flask_login`→`cw_login` 导入，
  本仓无 flask_login，函数内 import 在测试环境必炸）。
- **测试**：新增 `test_buddy_page.py` 3 条（GET 全集/默认、POST 持久化、POST 校验不落库）；
  `test_reader_r215_ui.py` 结构断言随 label 删除同步更新；i18n 契约 5 条全绿（zh po/mo 同步重编，
  **只编 zh**——全量 `pybabel compile -f` 会因 it.po 历史 placeholder 错误失败并顺手改写全部 locale，
  已将误编译的其余 locale .mo 恢复）。JS `node --check` 通过。发布态全量 `pytest tests/` =
  **906 passed / 0 failed**。
- **文档四问**：能力 → L1 `product/readme/companion.md` 悬浮球条目；契约 → 站内
  `/ajax/buddy/quick-actions` 新增（记录 LLD）；实现/边界 →
  `iterations/1.0/r223-buddy-fab-bubbles/lld.md`（含触屏无 hover、工具 id 白名单边界）；
  本次实现 → 同 LLD，状态「已开发待验收」。R220 LLD 状态行回填「已上线」。
- **驻留**：worktree `../magicbook-buddy`（分支 `feat/r206-buddy`，与 R220 同分支续作），
  push 后保留待用户验收。
- **真机验收缺陷与修复（2026-10-24 推送后 Chrome 实测）**：气泡点击与 FAB 点击全无反应。
  根因：`initBuddyFabDrag` 在 `pointerdown` 即对 wrap `setPointerCapture`，捕获把后续
  `click` 重定向到 wrap——阅读页原有「pointerdown 在按钮上 → click 由按钮收」的链路被
  打断，抽屉与气泡动作全部失效（吸附本身正常，故拖拽不暴露）。修法：捕获延迟到真正
  拖动（move 超过 6px 阈值）时设置，`pointermove` 加 `event.buttons & 1` 守卫防悬停误拖；
  守卫测试 `test_FAB拖拽捕获延迟到拖动开始`。修后 `ebf4cec4` 推送部署，Chrome 线上
  全链路复验通过：① 首页 4 默认气泡、左缘向右展开 + tooltip 翻边、贴边不越界；
  ② 「对话」气泡开抽屉、FAB 本体 toggle 关抽屉；③ `/buddy` 勾「每日学习」保存后首页
  5 气泡生效、还原默认后 4 气泡；④ 阅读页气泡转发顶栏工具双向验证（沉浸翻译开关
  两轮、书签图标空↔实）；⑤ CDP 真实鼠标拖拽吸附左/右缘 + 刷新保持；⑥ 控制台 0 error。
- **验收反馈二（2026-10-24）**：「朗读功能气泡点击以后要变成停止朗读，不然不能停」。
  根因：气泡只做一次 click 转发，而顶栏 `#tts-book` 在播放时是「❚❚ 暂停」不是停止，
  用户没有可达的停止入口（`#tts-book-stop` 只在顶栏出现）。修法：气泡以顶栏为唯一状态源
  （`#tts-book.active` / `#tts-book-stop` 可见性）每 250ms 同步，播放中切为红底「■ 停止朗读」
  并直接点 `#tts-book-stop`；空闲恢复「▶ 朗读」。`pagehide` 清理巡检定时器。
  提交 `2b1af29a` + `23b5790a` 已推送，线上 JS 已确认含新逻辑；全量 912 passed。
  本轮 Chrome 扩展持续报 `nodeRepl.fetch request failed`，**真机朗读停止未能复验**，
  CSS/JS 上线与静态断言（`test_朗读气泡播放中变为停止`）已通过，待用户点验。

