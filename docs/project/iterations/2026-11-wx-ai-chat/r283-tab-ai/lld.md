# R283 修改意见（挂 R280）：tabBar「伴读」改为「AI」· LLD

状态：已上线待验收（代码与守卫完成、静态锁 54 passed、已 merge/push `origin/develop`；
体验版 `1.0.1` 已上传，65.3 KB / 66,836 Byte；待后台设为体验版并真机验收）

> 本次怎么实现。需求基线见 [`../../../../product/miniprogram/requirements.md`](../../../../product/miniprogram/requirements.md)，
> 静态契约见 [`../../../../product/miniprogram/interface.md`](../../../../product/miniprogram/interface.md)，
> 实现与边界见 [`../../../../product/miniprogram/features/ai-chat.md`](../../../../product/miniprogram/features/ai-chat.md)，
> 上游实现见 [R280 LLD](../r280-miniprogram-ai-chat/lld.md)。

## 1. 需求与范围

用户 2026-11-05 12:32 提出「伴读改为AI」。核查后「伴读」在小程序里有 4 处用户可见文案：
`app.json` 底栏第二项、`pages/chat/chat.json` 导航栏标题、`pages/chat/chat.wxml` 页内标题、
`pages/login/login.wxml` 品牌副标题；另有 README、`project.config.json` 描述与若干代码注释。
交互确认口径为 **只改 tabBar 文案**，其余功能名仍「AI 伴读」，改完立刻重传体验版。
故不全局替换：网页阅读器抽屉、伙伴系统、moon-well 场景名里的「AI 伴读」是另一套能力。

## 2. 实现

- `miniprogram/app.json`：tabBar 第二项 `text` 由 `伴读` 改为 `AI`；
  `pagePath` 仍 `pages/chat/chat`，页面清单、窗口配置、tab 顺序均不动。
- 接口 / 请求体 / prompt / 后端零改动；moon-well R243 不受影响，无需重新部署。

## 3. 守卫（契约形制）

- 新增 `tests/test_r283_tab_ai.py`：
  - 正向：四项文案 `["复习", "AI", "词汇量", "我"]`、第二项 `pagePath` 不变、
    `app.json` 里不再出现 `"text": "伴读"`；
  - 反向（防越界）：`chat.json` 的 `navigationBarTitleText`、`chat.wxml` 的
    `.chat-title`、`login.wxml` 的品牌副标题仍含「AI 伴读」。
- `tests/test_r280_ai_chat.py`：把写死的 `["复习", "伴读", "词汇量", "我"]` 改为新值，
  docstring 标注 R283；`tests/test_r275_home_profile.py` 注释补 R283 标注。
- 设计取舍：文案类改动容易被「顺手全局替换」带偏，所以守卫必须同时钉住
  **改了该改的**与**没改不该改的**，只断言新值是不够的。

## 4. 验证记录（2026-11-05）

- 小程序静态锁 R271–R283（排除 `test_r279_book_submission.py` 后端集成用例）：**54 passed**。
  R279 的 11 个 error 是本机 pytest 临时目录与 WorkBuddy shim 冲突，与本轮无关。
- `node -e JSON.parse(app.json)` 通过，回读 tabBar 四项实值：
  `复习 / AI / 词汇量 / 我`，第二项 `pagePath=pages/chat/chat`。
- 源码扫描确认 3 处用户可见「AI 伴读」按口径保留，未越界。
- **上传后包体对照**：`1.0.1` = 66,836 Byte，R280 的 `1.0.0` = 66,840 Byte，
  正好少 **4 字节**（「伴读」6B → 「AI」2B），反证包内只有这一处文案变化。

## 5. 部署与状态

- **上传实况（已完成）**：上传源为主检出 `develop@a3a205e5`，
  `cli upload --project <主检出>/miniprogram -v 1.0.1 --port 13564`
  → ✔ upload，TOTAL **65.3 KB / 66,836 Byte**；`cli islogin` 仍 `{"login":true}`。
  **不带 `--info-output`**（R280 实测触发 IDE `code 17` 二维码路径报错）。
  上传产生「开发版本」，仍需后台「版本管理」选为体验版。
- 状态回写：修改意见挂 PingCode `MB-239`（`xB0tmxqa`，R280 载体），不新建 idea；
  仍 `In progress`，真机验收通过后才 `Completed` 并清理驻留 worktree。
- worktree：按「一次会话一个 worktree / 验收期驻留续作」复用
  `../magicbook-r280-ai-chat`（`feat/r280-ai-chat`），未新开树。
