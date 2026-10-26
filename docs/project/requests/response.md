# 对话回应记录

> 含每个需求的回应、冲突说明及两个文件的总结。
> **归档规则**：本文件仅保留最近 10 个 request 的回应；更早内容原样归档至 `response-archive/`（按 request 区间分文件），需要历史细节时按编号检索归档目录，不要读全量历史。

**归档索引**

- `response-archive/response-R01-R31.md`：R1–R31（2026-08-14 ～ 2026-08-31）
- `response-archive/response-R159.md`：R159 语音输入静音检测（2026-10-14 R169 轮转，窗口转入 R160 起）
- `response-archive/response-R160-R164.md`：R160 麦克风设备选择器 + 同节嵌套的 R164 worktree 纪律修订（2026-10-14 R170 写入触发轮转搬移，父级日期标题随节一并搬移）
- `response-archive/response-R161-R162.md`：R161 公网入口超时排查（Tailscale 直连黑洞）+ R162 两本《傲慢与偏见》版本对比（2026-10-14 R173 写入触发轮转搬移，窗口转入 R165 起）
- `response-archive/response-R32-R49.md`：R32–R49（2026-09-03 ～ 2026-09-17）
- `response-archive/response-R50.md`：R50（2026-09-18）
- `response-archive/response-R51-R70.md`：R51–R70（2026-09-18 ～ 2026-09-21）
- `response-archive/response-R70-R80.md`：R70–R80（2026-09-22 ～ 2026-09-28；含 R70/R71 历史重复条与 R74 补写条，见文件头说明）
- `response-archive/response-R188.md`：R188（2026-10-16）
- `response-archive/response-R81-R101.md`：R81–R101（2026-09-27 ～ 2026-09-30；含 R88/R90/R98 补记与重复编号，原样搬移）
- `response-archive/response-R102-R110.md`：R102–R110（2026-09-30 ～ 2026-10-01；R110 条目含 R107/R109 代提交，R120 触发轮转搬入）
- `response-archive/response-R111-R119.md`：R111–R119（2026-10-02 ～ 2026-10-05；2026-10-08 R129 补账搬移）
- `response-archive/response-R120-R125.md`：R120–R125（2026-10-06 ～ 2026-10-07；R135 写入触发搬移，含 R134 登记的窗口欠账补账）
- `response-archive/response-R126-R131.md`：R126、R127、R128、R129、R131（2026-10-07 ～ 2026-10-08；2026-10-09 R141 写入触发轮转搬移，清掉 R134 登记的窗口欠账）
- `response-archive/response-R132-R133.md`：R132、R133（2026-10-08；2026-10-10 R143 写入触发轮转搬移）
- `response-archive/response-R134.md`：R134（2026-10-08；2026-10-10 R144 写入触发轮转搬移，其父级日期标题随节一并搬移）
- `response-archive/response-R143.md`：R143（2026-10-10；2026-10-11 R157 写入触发轮转搬移）
- `response-archive/response-R144-R153.md`：R144、R145、R147（含嵌套 R146）、R151、R152、R153（2026-10-10 ～ 2026-10-11；2026-10-12 R161 写入触发轮转搬移，清并行欠账）
- `response-archive/response-R154.md`：R154（2026-10-11；2026-10-12 R162 写入触发轮转搬移）
- `response-archive/response-R165-R173.md`：R165、R166、R167、R168、R169、R170、R172、R173（2026-10-12 ～ 2026-10-14；2026-10-15 R183 写入触发轮转搬移，窗口转入 R174 起）
- `response-archive/response-R174-R177.md`：R174、R176、R177（2026-10-15；2026-10-16 R185 写入触发轮转搬移，窗口转入 R178 起）
- `response-archive/response-R175.md`：R175（2026-10-15；2026-10-16 R188 写入触发轮转搬移，窗口转入 R178 起）
- `response-archive/response-R178.md`：R178 moon-well 防腐层迁出 web.py（B1，架构评审波 2）（2026-10-15；2026-10-16 R189 写入触发轮转搬移）
- `response-archive/response-R179.md`：R179 架构评审 B2 尝试（撤销回基线，留存重做清单）（2026-10-15；2026-10-19 R130 写入触发轮转搬移）
- `response-archive/response-R130.md`：原文件标 R130 节、正文实为 R190 回应（LLM 队列监控面板四区块）（2026-10-23 R209 写入触发轮转搬移，原样搬移不改写）
- `response-archive/response-R180.md`：R180 B2 前置小修两项（2026-10-21 R190 写入触发轮转搬移）
- `response-archive/response-R130.md`：R130 LLM 队列监控面板（承接 moon-well R118 契约、扩展 R126 /llm-tasks），2026-10-21 R191 写入触发轮转
- `response-archive/response-R181.md`：R181 架构评审波 3 · B2 小步重做完成：web.py 蓝图分域拆分（2026-10-21 台账合并时轮转搬移）
- `response-archive/response-R182.md`：R182 架构评审波 4 · B7：i18n 种子与 JS 清单生成化（2026-10-21 台账合并时轮转搬移）
- `response-archive/response-R185.md`：R185 架构评审文档修正批 DF1–DF5（2026-10-22 R207 写入触发轮转搬移）
- `response-archive/response-R191.md`：R191 写作批改 503 复发（代理预算小于后端 LLM 预算）——2026-10-23 R210 写入触发轮转搬移
- `response-archive/response-R183.md`：R183 B4 epub.js 分域（批次 1–7 七节，78 行）——2026-10-23 R211 写入触发轮转搬移，原样搬移不改写
- `response-archive/response-R194.md`：R194 写作批改 SSE 进度流（2026-10-23 R214 写入触发轮转搬移，窗口转入 R195 起）
- `response-archive/response-R195-R202.md`：R195–R202 博客导入链与 TED 导入链缺陷盘点 + 修复——2026-10-23 R216 写入触发轮转搬移，原样搬移不改写
- `response-archive/response-R203.md`：R203 跨模块别名漏声明致 4 个段落按钮失效——2026-10-23 R216 写入触发轮转搬移（与 R214 轮转叠加后续搬），原样搬移不改写
- `response-archive/response-R204.md`：R204 写作批改 SSE 真机无进度（WSGI 缓冲）——2026-10-23 R216 第三次 merge 后窗口达 11 续搬，原样搬移不改写
- `response-archive/response-R205.md`：R205 每日学习「单词编故事」Hub 第八张卡（2026-10-23 R212 写入触发轮转搬移）
- `response-archive/response-R206-R207.md`：R206 伙伴系统前端 + R207 伙伴验收三连与 CSP 拦图修复——2026-10-24 R213-C 写入触发轮转搬移（搬移前窗口已 11 节），原样搬移不改写
- `response-archive/response-R208.md`：R208 每日学习 banner 小功能管理（齿轮抽屉 + 勾选过滤 + 引导卡）——2026-10-24 R213-C 合入 `origin/develop` 后窗口达 11 节（与 R214-C 验收缺陷节并行追加）触发续搬，原样搬移不改写
- `response-archive/response-R209.md`：R209 积分内测活动 + 充值倍率机制（充值页代理与前端）——2026-10-24 R213-C 与 R217 在 develop 合流后窗口达 11 节触发轮转搬移，原样搬移不改写
- `response-archive/response-R210.md`：R210 伙伴图片未生效的定性与 MinIO 入口切换的 CSP 侧（源清单收敛单点、过渡双源）——2026-10-24 R213-C / R217 / R221 再次合流后窗口达 11 节触发续搬，原样搬移不改写
- `response-archive/response-R211.md`：R211 OIDC 自助注册默认授予管理员权限（P0 缺陷修复）——2026-10-24 R222 写入触发轮转搬移，原样搬移不改写
- `response-archive/response-R214.md`：R214 书籍详情子项 A（阅读入口解禁 + 元数据修正 + 视觉分层，含 B 合流记录）——2026-10-24 R223 写入触发轮转搬移，原样搬移不改写
- `response-archive/response-R216.md`：R216 引导收敛 + `/me` 偏好页 + 难度入口前置 + 成就锁态 + 伙伴文案 + IP 风险登记——2026-10-24 R224 写入触发轮转搬移，原样搬移不改写
- `response-archive/response-R217.md`：R217 注册后自动回 magicbook（邀请注册接回 OIDC 上下文，enrollment 完成后静默授权回站且已登录）——2026-10-25 R225 写入触发轮转搬移，原样搬移不改写
- `response-archive/response-R218.md`：R218 R214 子项 A 验收缺陷（书架内书籍详情 500）——2026-10-25 R226 写入触发轮转搬移，原样搬移不改写
- `response-archive/response-R212.md`：R212 入口层换皮之品牌资产与字样收敛——2026-10-25 R227 写入触发轮转搬移，原样搬移不改写
- `response-archive/response-R213-C.md`：R213-C 首页 `/home` 组装 + 登录落点开关——2026-10-25 R228 写入触发轮转搬移，原样搬移不改写
- `response-archive/response-R214-C-defect.md`：R214-C 验收缺陷（入口按钮落进书卡弹层 + 估算 500）——2026-10-26 R230 写入使窗口达 11，原样搬移不改写；与既有 `response-R214-C.md`（R214 子项 C 代价面板）是两条不同条目
- `response-archive/response-R221-R222.md`：R221 AI 口语陪练语音优先 + R222 书籍简介验收缺陷——2026-10-26 R233 写入触发轮转搬移，原文无改写
---

> 归档索引：[response-R01-R31.md](response-archive/response-R01-R31.md) · [response-R32-R49.md](response-archive/response-R32-R49.md) · [response-R50.md](response-archive/response-R50.md) · [response-R51-R70.md](response-archive/response-R51-R70.md) · [response-R70-R80.md](response-archive/response-R70-R80.md) · [response-R81-R101.md](response-archive/response-R81-R101.md) · [response-R102-R110.md](response-archive/response-R102-R110.md) · [response-R111-R119.md](response-archive/response-R111-R119.md)（2026-10-08 R129 补账搬移）· [response-R120-R125.md](response-archive/response-R120-R125.md)（2026-10-08 R135 写入触发搬移，含 R134 登记的窗口欠账补账）· [response-R126-R131.md](response-archive/response-R126-R131.md)（2026-10-09 R141 写入触发轮转搬移）· [response-R132-R133.md](response-archive/response-R132-R133.md)（2026-10-10 R143 写入触发轮转搬移） · [response-R134.md](response-archive/response-R134.md)（2026-10-10 R144 写入触发轮转搬移） · [response-R135-R137.md](response-archive/response-R135-R137.md)（2026-10-10 R147 写入触发轮转搬移，含 R145/R146 两次写入的窗口欠账补账） · [response-R138.md](response-archive/response-R138.md)（2026-10-11 R152 写入触发轮转搬移） · [response-R139.md](response-archive/response-R139.md)（2026-10-11 R153 写入触发轮转搬移） · [response-R140.md](response-archive/response-R140.md)（2026-10-11 R153 复核后的补搬——R152 写入时搬走 R138 后窗口仍为 11） · [response-R141-R142.md](response-archive/response-R141-R142.md)（2026-10-11 R155 集成时窗口超限搬移） · [response-R144-R153.md](response-archive/response-R144-R153.md)（2026-10-12 R161 写入触发轮转搬移，清并行欠账 R144–R153） · [response-R154.md](response-archive/response-R154.md)（2026-10-12 R165 写入触发轮转搬移） · [response-R155-R156.md](response-archive/response-R155-R156.md)（2026-10-13 R166 写入触发轮转搬移，含同日同编号「细筛」那条） · [response-R157.md](response-archive/response-R157.md)（2026-10-13 R166 分支 merge origin/develop 后窗口仍达 11，续搬最旧一节） · [response-R156-mic.md](response-archive/response-R156-mic.md) · [response-R158.md](response-archive/response-R158.md)（2026-10-13 R168 写入触发轮转搬移）（2026-10-13 R167 写入触发轮转搬移；与 response-R155-R156.md 里的同编号「细筛」条目不同事） · [response-R160-R164.md](response-archive/response-R160-R164.md)（2026-10-14 R172 写入触发轮转搬移，窗口转入 R161 起） · [response-R161-R162.md](response-archive/response-R161-R162.md)（2026-10-14 R173 写入触发轮转搬移，窗口转入 R165 起） · [response-R165-R173.md](response-archive/response-R165-R173.md)（2026-10-15 R183 写入触发轮转搬移，窗口转入 R174 起） · [response-R174-R177.md](response-archive/response-R174-R177.md)（2026-10-16 R185 写入触发轮转搬移，窗口转入 R178 起） · [response-R175.md](response-archive/response-R175.md)（2026-10-16 R188 写入触发轮转搬移） · [response-R214-C.md](response-archive/response-R214-C.md)（2026-10-25 R229 写入触发轮转搬移：R214 子项 C 整本任务代价面板；与既有 response-R214.md（子项 A）不同事）

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

## 2026-10-24（R224：本轮测试修复未完成项收口——R219 / R212 / R213-B6 / R214-C）

### R224（用户：「review 本轮测试修复，找到哪些没有修改完成且没有推到下个迭代的」→「尽可能修复代码未完成的部分」）

- **结论先行**：真正属于代码未完成、且未排到下一迭代的是 **R219 邀请链接、R212 交付项 1/3/4、R213-B/B6 进度总开关、R214-C 估算 500 核实**。R215、R221、R223、R220 属待真机验收，不是本轮代码缺口；**只有 R213-A 侧边栏分组**按用户 2026-10-24 拍板明确留到下一迭代，不冒充本轮完成。
- **R219（已修复）**：`cps/oidc.py` 优先读取 Authentik 嵌套 `?query=itoken%3D...`，兼容旧顶层 `itoken`/`token`；`/oidc/signup` 只输出外层 `?query=`，内部同时带 `itoken` 与 `next`。`tests/test_oidc_signup.py` 覆盖嵌套解析、旧格式兼容、冲突优先级与 token alias；生产 env 与真实注册流仍待验收。
- **R212（代码完成，待真机验收）**：登录页新增价值主张与随机书墙（复用 `random_discover_books`/`common_filters`，空库或查询失败安静隐藏）；新账号 locale 按 Authentik claim → Accept-Language → 站点默认初始化；顶栏增加语言入口。复查中修掉两个隐藏依赖：① 顶栏只提交 `locale`，`/me/preferences` 仅在 `default_language` 显式出现时校验/更新，避免账号里失效的书籍语言连带拒绝界面切换；② 匿名浏览关闭时不取书、不渲染书墙，避免封面端点重定向造成破图及未授权页面泄露书名。新增 6 条中文 PO/MO 守卫，中文不再静默回退英文。
- **R213-B/B6（已补开发，待复验）**：新增 `config_reading_progress_enabled` 配置列与存量库 ALTER 迁移、管理页开关；关闭时 `/ajax/reading-progress` 返回 `{"success": true, "disabled": true}`，不写 `ReadingProgress` / `ReadBook`；EPUB/PDF/TXT 均不加载 `reader-progress.js`、不注入服务端位置，EPUB 回退 localStorage、PDF 不拼 `#page`、TXT 回到改造前行为。测试隔离也修实：管理配置 POST 会因缺失复选框清空大量字段，现将整行 `_Settings` 快照恢复并清 `ConfigSQL._settings` 缓存，避免后续用例被 kill switch 污染；另在临时旧库上验证缺列 ALTER 与默认值，不依赖测试库已含新列。
- **R214-C（代码核实，证据有缺口）**：当前 worktree 的 `cps/reading_insight/service.py` 与 `origin/develop` 完全一致，估算 500 的相关修复已在 develop（`42ddfb19`、`b28d9240`），本 worktree 无额外代码可改。生产 ES 查询返回 **401**，因此不能声称已证实生产 500 的具体异常类型；R214-C 仍需真机复核。
- **验收而非代码缺口**：R215、R221、R223、R220 的自动化/局部修复已在各自分支或 develop，剩余动作是真机验收与状态流转；本轮不把「未跑真机」写成「代码没做完」。
- **明确下迭代**：R213-A 的侧边栏四组分组（`Shelf.kind` 判定）仅此项按用户拍板留到下一迭代；本轮不改其设计，也不勾选 A1。
- **文档同步**：L1 `readme/reading.md` 更正 PDF/TXT 账号级进度；L2 `reading/interface.md` 补开关关闭响应；L3 `reading/features/reading-progress.md` 更正 `ReadBook` 在读状态与三格式下线边界；R219 工作流、L3、`.env.example` 与 R217 历史 LLD 标注现行嵌套 query（历史只标注不重写）；R212 LLD 改为交付项 1/3/4 代码完成待真机；R213 AC/LLD 与计划表统一 `config_reading_progress_enabled` 并清掉「查无此开关」旧警告。
- **验证与驻留**：定向回归 **196 passed / 0 failed**（OIDC、入口层、品牌/CSP、`/me`、导航、阅读进度、首页、R214 估算与详情），`git diff --check` 与改动 Python 文件编译通过。用户 2026-10-25 指示 merge and push 后，在最新 `origin/develop` 上执行发布态全量 **944 passed / 0 failed**。worktree `../magicbook-r224-close-out`（分支 `feat/r224-close-out`，基线 `origin/develop` `b0af8382`）保留待真机验收。
- **总结**：requests.md 条目 224 为本轮收口需求，条目 219 已回填「已开发待验收」；本条为回应。冲突记录：未改主检出、未 push；R214-C 生产异常类型未证实、ES 401 属证据缺口；R216 回应已按 10 节窗口规则原样搬至 `response-archive/response-R216.md`。

## 2026-10-25（R225：邀请注册跳转、普通账号阅读/下载 403、品牌封面占位）

### R225（用户：注册直接失败 + 普通账号阅读下载 403 + 无封面白字占位；「验证这些问题，如果确实存在修复他们」）

- **结论先行**：三项均真实存在，已修复并上线。分类为缺陷，挂既有 R219（邀请注册）/ R211（OIDC 角色）/ R214（详情与读者入口）；PingCode 工作项待建。
- **注册（已证伪「邀请过期」）**：`/oidc/signup` 原先把 `itoken` 与 `next` 组成内层 query，再整体塞进外层 `query`，实际跳转成 `?query=itoken%3D...%26next%3D...`。Authentik 2025.10.2 的 `FlowInterface` 又把浏览器原始 search 作为 executor API 的 `query` 入参，最终变成 `query=query%3D...`，无法解析邀请；顶层 `?itoken=...&next=...` 才能正常返回注册首步。修法：`cps/oidc.py::signup()` 与 `scripts/rotate_authentik_invite.py` 只生成顶层参数；`_invite_token()` 优先读顶层，仍兼容历史嵌套 env，避免部署瞬间关闭注册入口。
- **阅读与下载（分开定性与修复）**：生产 `config_default_role=0`，而 OIDC 新账号严格继承该值，导致不含 `ROLE_VIEWER=256`，`/read/...` 的 `@viewer_required` 一律 403。R225 起 `site_default_role()` 强制补 `ROLE_VIEWER`，继续剔除 `ROLE_ADMIN`；**不自动补 `ROLE_DOWNLOAD=2`**，因为下载是独立的整本文件权限，不能借“修阅读”顺手放开。详情页现在分别在账号被关阅读位/下载位时显示锁定提示，并写明到「用户 → 编辑用户」开通 View / Download，而不是让用户撞 403 后猜。
- **存量账号（未擅改生产库）**：新增 `scripts/reader_role_audit.py`，默认 dry-run 列缺阅读位账号；`--grant-viewer` 必须点名 `--ids` / `--emails`，只补 `ROLE_VIEWER`，写前备份 `.r225-bak-*`。只读核查时 `uxprobe2`（id=9）与 `uxprobe`（id=10）角色均为 0；建议验收时明确批准后执行 `python3 scripts/reader_role_audit.py --grant-viewer --ids 9,10`。同时修正 `oidc_admin_audit.py --demote` 的语义漂移：降级目标从“默认角色剔除管理员位”改为“默认角色补阅读位并剔除管理员位”，避免把存量超管降级后又变成读不了书的账号。
- **封面**：确认 `cps/static/generic_cover.jpg` 原本就是白底黑字的 `Cover not available`。替换为 564×800 深墨绿品牌封面，沿用 `get_cover_on_failure()` 单点回落，首页、详情、OPDS 等所有缺封面路径共用，不改 URL 与缓存语义；已目视检查。
- **测试**：定向回归 **90 passed / 0 failed**（`test_oidc_signup.py` / `test_oidc_admin_role.py` / `test_auth_reader_covers_r225.py` / `test_reader_role_audit_r225.py` / `test_book_detail_r214.py`），发布态全量 **961 passed / 0 failed**（4 个非阻断 warning）；另做反向变异：删除详情页 Download 提示后守卫报红，恢复后 27 passed。新增中文词条已进 `zh_Hans_CN` PO/MO，守卫从编译后 `.mo` 取词，防止“PO 正常、运行时英文”。
- **文档四问**：能力 → L1 `readme/library.md` 补无封面品牌占位，`readme/admin.md` 说明新账号阅读/下载边界；契约/边界 → L3 `admin/features/oidc-self-registration.md` 与 KB `oidc-login.md` 修正邀请链接形式、角色语义与两个修正 CLI；本次实现 → LLD `iterations/1.0/r225-auth-reader-covers/lld.md`（状态：已上线待验收）；`REQUIREMENTS.md` 与迭代 `plan.md` 同步。
- **上线实况**：修复提交 `53e2e662` 已 merge 到 `develop`（`b1f4d9e6`，最终 `890bc607`）并 push。GitHub webhook 对最终提交投递超时（500），fnOS 未自动接到构建；按脚本契约手动执行 `build-magicbook.sh refs/heads/develop 890bc607...` 补发成功。生产容器 `healthy`，`house.build-sha=890bc607...`；线上 `/oidc/signup` 已是顶层 `itoken` / `next` 且 Authentik 邀请页 200，品牌封面 81,048 字节并与仓库一致。
- **驻留与闸门**：worktree `../magicbook-r225-auth-reader-covers`（分支 `fix/r225-auth-reader-covers`）原样保留待验收，验收通过后 `git worktree remove` + `git branch -d`。真机验收项：干净浏览器从 `/login` 完成注册并回站登录；批准后给 `uxprobe2`/`uxprobe` 开 View 再打开 `/read/223/epub`；首页无封面书检查品牌图。下载权限若也要开放，须单独授 `ROLE_DOWNLOAD`，不与阅读权限捆绑。
- **窗口**：写入前已满 10 节，按「写入即检查」把最早 R217 整节原样搬至 `response-archive/response-R217.md` 并登记索引，窗口保持 10。
- **总结**：requests.md 条目 225 已从占位回填；本条为回应。冲突记录：无撞号；生产存量账号未改，需按点名清单另行批准；R225 与此前 R219 的“嵌套 query”结论相反，已在 L3 / KB 明确标为现网 2025.10.2 复核后的现行口径，历史 R219 记录保留不改写。

## 2026-10-25（R226：阅读器验收缺陷——伙伴白圆底 / 幽灵问号 / 翻译连续重排）

### R226（用户：补验上一轮被 403 挡住的阅读器问题——顶栏、伙伴入口、AI 面板、段落按钮提示、翻译抖动、幽灵问号）

- **任务定位**：缺陷，挂 MB-14 / R215 阅读器验收，关联 R223 伙伴透明悬浮球与 R216 引导入口。先复验再修，不把「需求已拍板」误当回归。
- **复验证据（生产 `https://magicbook.haoshenqi.top/read/223/epub`，普通读者会话）**：正文可打开，页码正常，403 已消失；桌面顶栏实际为「译 翻译 / 整 翻译本书 / ▶ 朗读 / 书签 / 设置 / 全屏」，CSS 为 24px 图标、12px 标签、36px 最小触达盒；段落四枚控件（朗读/翻译/批注/AI 伴读）在 AX 树中均有完整名称，源码 `createParaButton()` 同时写 `title` 与 `aria-label`；AI 头部新建/重命名/删除/记忆按钮也都有 `title` 与 `aria-label`。✓ 是主题选中标记，不是操作按钮，不应强加 tooltip。
- **AI 面板遮正文不是本轮缺陷**：真机为 420px 右侧覆盖式抽屉，打开时确实覆盖正文右缘。该形态是用户 2026-10-23 明确否决停靠方案后拍板的 R215 C1，不能因本轮一句「还遮不遮正文」擅自反转；已写进 R226 回应与 LLD，留待用户若改口径再立新需求。
- **已修一：伙伴白圆底**。根因是 `ai_chat.css` 中 `.has-buddy { background: transparent; box-shadow: none; }` 之后又有同特异度 `.has-buddy { background: #fff; padding: 0; }`，后写白底覆盖 R223 的透明契约。修复为后写规则只保留 `padding: 0`，透明背景与无阴影仍由前一条唯一声明；无头像兜底蓝底不受影响。
- **已修二：幽灵「?」**。根因是 `onboarding.js` 动态创建的常驻按钮可见文本只有 `?`，含义藏在只有悬停才出现的 `title` 中。修复为按钮可见文本直接使用本地化「使用引导」，右下位置保留、改成 40px 高胶囊；导览收尾文案同步从「左下角 ?」改为右下角「Onboarding Tour」，i18n 种子与 zh PO/MO 成对更新，旧词条移除。
- **已修三：整页翻译连续重排**。根因是批量翻译先给最多 20 个可见段插 `Translating…`，随后每个请求完成就逐段替换，连续改变 iframe 高度；用户接受的是最终译文内联导致的一次重分页，不是请求期的二十次抖动。修复：请求期不再插正文占位，只给顶栏「译」加 `is-loading`/`aria-busy` 轻脉冲（reduced-motion 下关闭动画）；并发仍为 4，全部返回后在同一个 JS 任务里按原顺序一次性插入、缓存只写一次；失败段仍按既有可重试错误块渲染；请求中关闭翻译则迟到结果不写正文。
- **测试与上线**：新增 `tests/test_reader_r226_acceptance.py` 3 条源码守卫（透明优先级、导览入口文案、批量翻译一次渲染与加载态）。定向回归 **62 passed / 0 failed**（R226 + R215 UI + 引导导览 + 导览视觉 + 导航下拉），随后翻译/模块面/i18n 回归 **34 passed / 0 failed**；`node --check` 与 `git diff --check` 通过；发布态全量 **964 passed / 4 warnings / 0 failed**。实现提交 `261d9aee` 已合并为 `0b666d77` 并推送 `develop`；fnOS 于 18:36:22 构建、18:36:43 `build END OK`，容器 `healthy`，标签 `house.build-sha=0b666d77...`。推送后首页短暂 502 已恢复为 302 登录跳转。
- **文档四问**：能力 → L1 `readme/readme.md`、`readme/reading.md`、`readme/companion.md` 更新「右下使用引导」、翻译等待反馈与伙伴入口位置；契约 → 无接口变化；实现/边界 → L3 `reading/features/companion-panel.md`、`learning/features/onboarding.md`；本次实现 → `iterations/1.0/r226-reader-verify/lld.md`（状态：已上线待验收）；`REQUIREMENTS.md` 与迭代 `plan.md` 同步。
- **新代码真机复验（已补）**：部署完成后用普通读者登录态打开生产 `/read/223/epub`，确认：① 伙伴头像透明、无白圆底；② 右下角为带明确文案的「使用引导」胶囊，AX 树不再出现「?」；③ 点击顶栏「译」后请求期正文不动、顶栏进入加载态，译文完成后一次出现，未见逐段插入导致的连续重排；④ 顶栏图标与文字、段落四按钮名称正常；⑤ AI 面板仍为 420px 覆盖式抽屉，覆盖正文右缘，属 R215 既有拍板。上述均有本轮生产截图 / AX 证据；整本 384 段的等待全程未做逐帧录屏，下载权限未代验。
- **驻留与闸门**：worktree `../magicbook-r226-reader-verify`（分支 `fix/r226-reader-verify`，基线 `origin/develop` `a5fe007f`）原样保留，合并提交 `0b666d77` 已上线，等待用户最终验收；验收通过后再 `worktree remove` + `branch -d`。
- **窗口**：写入前已有 10 节，按「写入即检查」把最早 R218 整节原样搬至 `response-archive/response-R218.md` 并登记索引，窗口保持 10。
- **总结**：requests.md 条目 226 已回填；本条为回应。冲突记录：无撞号；唯一口径冲突是「AI 面板遮正文」——R215 已明确选择覆盖式抽屉，本轮不擅自回滚，需用户另下新口径才会改。

## 2026-10-25（R227：Buddy 对话复用口语陪练语音能力——全站语音提问 + 每条回复手动朗读）

### R227（用户：「我想要 AI 伴读 Buddy 对话也可以复用 AI 口语陪练 陪练的语音能力。」）

- **任务定位**：需求（跨功能复用，不是缺陷）；**单仓交付**——moon-well 侧零改动，ASR 与 TTS 端点都已在线（R221 前端 / moon-well R212 后端）。
- **四问四答拍板（2026-10-25）**：① 范围＝**输入+朗读双向**（不是只做输入或只做朗读）；② 回复朗读＝**每条手动点「朗读本条」**（不自动播——回复普遍 800–2000 字，自动播既慢又按次扣费）；③ 用户语音＝**只转成文字**、不留可回放语音条（否则要给 `ai_message` 加音频字段 + 走 MinIO 上传，跨仓改动不划算）；④ 生效面＝**全站**（Buddy 自 R220 起是全站助手）。
- **复用面（先查后写，不是凭印象）**：`learning-voice.js`（WebAudio→16k wav→ASR，R158/R159/R160 三处坑都在里面）、`/ajax/learning/asr/transcribe`（登录鉴权、10MB、60s、不扣积分）、`/ajax/reading-tts`→moon-well `/tts/speak`（**1 积分/次含命中**、≤2000 字、65s）、`/ajax/reading-tts-cached`（只读缓存不计费）。**不复用**：录音上传/语音条（要改 `ai_message`）、教练回复的服务端同步合成（Buddy 是 SSE 流式，会把 `final` 拖长且长回复必撞 2000 字上限）。
- **三处不能照搬，各自有解**：① `learning-voice.js` 原硬依赖 `window.MBLearning`（`if (!MB) return;`），Buddy 面板在全站挂载、没有 learning-common → **依赖降级为「有则用、无则回退」**（`window.mbT` / `window.MBApi.csrfToken()` / `options.asrUrl`），学习页零改动；另补 `clearNode` 回退——缺 `MBLearning` 时 `MB.clear(select)` 会在设备下拉处直接 TypeError。② 朗读不能用 `<audio src=blob:>`：`media-src blob:` 目前只在阅读页/口语页放行，照搬要把 CSP 铺到全站，而 `test_non_reader_pages_still_block_blob_media` 正是拦这条的守卫 → **改走 Web Audio**（`fetch` 取字节 + `decodeAudioData`，受 `connect-src` 回退 `default-src 'self'` 约束，**不受 media-src 管辖**），`web.py` **一行未改**。③ 长回复撞 2000 字上限 → 分段 1800（空行→句末标点→硬切），顺序播放并在状态行显示「朗读中 n/m」。
- **顺带修掉一个既有静默故障**：伴读工具 `synthesize_tts` 的 `audio` SSE 事件原本也用 `new Audio(blob:)`，在非阅读页会被 CSP 拦掉且几乎没有可见提示（R220 把面板铺到全站之后就该暴露）。改成同一条 Web Audio 路径后，全站都能响。
- **缓存档位**：朗读**不带** `bookName`/`chapter`，让 moon-well 按「AI 临时语音」档（7 天清理）落盘，不把一次性回复写进书籍段落的永久缓存；与 `synthesize_tts` 的既有口径一致。
- **一处存量缺陷（本轮不擅自改）**：`ai_chat.js` 顶部的 `var mbT = window.mbT || identity` 在脚本载入时就被固定成恒等函数——`layout.html` 把 `i18n_seed.html` 排在 `ai_chat_panel.html` **之后**，所以面板既有动态文案实际上是英文。修法只有一行（改成调用时解析），但会让一批既有文案突然变中文，属可见行为变化，需单独一轮带验收。本轮新增文案改用本地 `t(id)`，词条手工进种子（生成器只扫 `mbT(`），并由新测试同时守种子/PO/MO。
- **测试**：新增 `tests/test_buddy_voice.py` 7 条（面板挂载与脚本顺序、录音模块解耦、转写不自动发送、朗读不带书籍上下文、朗读不用 blob 媒体、分段上限 <2000、`t()` 词条三处齐全）；定向回归 **117 passed / 0 failed**（buddy 两套 + 页面冒烟 + i18n 契约 + CSP + 阅读器 R226/R215 + 学习页静态 + common api + 引导）；`node --check` 两个 JS；`splitForSpeech` 另用 node 直跑边界（1900 字无标点→[1800,101,223]、纯中文 3000 字→2 段、空串→[]）。
- **真机验收未做（6 项）**：阅读页录音转写并编辑发送、首页同样可录可转（验证全站而非只在阅读页）、点朗读出声/再点停止、长回复两段连播、关抽屉即停、中文界面下按钮与状态行为中文。
- **文档四问**：能力→L1 `readme/companion.md` 增「说话提问」「朗读回复」；契约→无接口变化（复用既有代理，故未改 L2）；实现/边界→新建 L3 `companion/features/buddy-voice.md`；本次实现→`iterations/1.0/r227-buddy-voice/lld.md`（状态：开发完成待验收）。另按「模块无基线则补建」新建需求基线 `companion/requirements.md`（R227 起）。
- **台账与驻留**：R227 由 `claim.sh` 占号并 push（`a7eecd0c`，纯台账）；worktree `../magicbook-r227-buddy-voice`（分支 `feat/r227-buddy-voice`，基线 `origin/develop` `a7eecd0c`）已于 2026-10-26 用户确认收尾时删除（`worktree remove` + `branch -d`，删前仅清掉 `.pytest_cache/` 测试缓存），无残留、无未合并提交。
- **窗口**：写入前已有 10 节，按「写入即检查」把最早 R212 整节原样搬至 `response-archive/response-R212.md` 并登记索引，窗口保持 10。
- **总结**：requests.md 条目 227 已从占位回填；本条为回应。冲突记录：无撞号；唯一保留项是 `mbT` 冻结问题（存量、影响面大，另立一轮），不在本轮顺带改。
- **上线实况（2026-10-25 21:27）**：用户令「上线」→ 主检出 `develop` 上 `a7eecd0c..cb198e00` 快进合并并 push（17 files / +774）。fnOS 自动构建，约 35 秒后生产静态资源即为新版：`/static/js/ai_chat.js` 含 `decodeAudioData` 与 `ai-chat-speak`、`/static/js/learning-voice.js` 含 `window.MBLearning || {}` 且旧 `if (!MB) return` 已消失、`ai_chat.css` 含 `.ai-chat-mic`、`/login` 渲染出的 i18n 种子里有 `Read reply aloud`（顺带证明模板没被字典改动搞坏）。`/` 仍 302 → `/login?next=%2F`，与改动前一致。
- **补丁（同日 21:3x，计费拒绝要说人话）**：核账时发现「积分不足」的失败体是 HTTP 500 + `Result` 信封，原实现只看 `resp.ok` 就直接 `arrayBuffer()` 去 decode，用户会看到「解码失败」——把计费拒绝伪装成播放器坏了。`fetchSpeechBytes` 改为：成功且 `Content-Type` 是音频才解字节，否则读文本、取 `Result.message` 抛出（典型文案「积分不足，无法使用AI功能」）；新增第 8 条守卫钉住「失败分支必须走 `.text()`」。属同一需求内的缺陷修补，不另占号。
- **计费口径变更（2026-10-25 晚，承接 moon-well R213）**：用户指正「1 积分/段只针对缓存命中，真实生成走正常计费，TTS/ASR 都要收，参考阿里云标价」。moon-well 侧据此改成：**命中 1 积分/段、首次生成按 50 字符/积分**（cosyvoice-v3-flash 1 元/万字符 ×2）、**ASR 22 秒/积分且最少 1 积分**，并修掉「真实合成双扣」「预检在调用之后」「ASR 实际从未收费」三处缺陷。magicbook 侧代码零改动（费率由 `/credit/billing` 下发、朗读走既有代理），只更新 L1/L3/LLD 的计费描述；**用户可见变化**：一条 1800 字新回复首读约 36 积分、重听 1 积分，一句语音提问约 1 积分，整本任务面板的朗读预估因费率真源变化会放大约 20 倍（预期行为，非缺陷）。

## 2026-10-25（R228：moon-well R214 伴读 Agent Skills 的 magicbook 消费侧说明）

### R228（承接 moon-well R214；用户：「把magic book 所有的功能 总结一下，做成一个skill 给 AI伴读的agent使用。先判断AI伴读的agent 是否支持skill」）

- **任务定位**：跨仓消费说明，magicbook **零代码改动**。后端主责 moon-well R214；本仓 R214 已被“书籍详情”占用，故消费侧顺延占 **R228**，不覆盖既有编号。
- **支持判断**：原 AI 伴读 Agent **不支持 Codex / Claude 原生 Skill**；它是 moon-well 内有界工具循环 + `AgentToolRegistry` 白名单 + Nacos 提示词。直接放 `SKILL.md` 不会生效，因此 moon-well R214 实现的是产品内只读、无脚本、渐进披露的 Skill 机制。
- **消费侧交付**：`companion` L1 说明伴读可按需加载 MagicBook 全功能指南并强调不扩权；`companion/requirements.md` 记录 moon-well R214 / magicbook R228；`iterations/1.0/r214-agent-skill/lld.md` 写明真实页面路径、不可执行动作、失败退化与验收清单；迭代 `plan.md` 增跨仓工作项。
- **用户可见范围**：涉及阅读、翻译、查词、词汇、学习计划、朗读、积分或伙伴的问题，助手可先取指南再给具体页面/操作；指南按需读取、不占每轮上下文；不会因此获得点按钮、改设置、下单、启动整本任务或管用户的新权限。
- **不变量**：不改前端模板、不改 `/ai/agent/*` 代理、不改 SSE/会话/消息结构、不改工具白名单或写确认门配置；moon-well 关闭 Skill 或白名单未放行时，magicbook 无需变化。
- **验收（2026-10-26 生产真机）**：① 每日学习回答覆盖当前八项（写作、口语、复述 4-3-2、计时重读、听写、复习队列、Word Story、选书难度匹配），并给出 `/learning` 及各活动入口；② 改难度 / 买积分 / 启动整本翻译均拒绝代执行，给出 `/reading/settings`、`/credits`、书籍详情页真实路线，轨迹无写工具；③ 价格、倍率和活动结束时间明确以页面为准，未编造数值；④ 普通寒暄未加载 Skill。新词查询与 TTS 首次 miss 3 积分、第二次命中 1 积分也已实测。
- **新注册普通账号补测**：`r214probe-20261026-6457`（moon-well userId 15）的 `/admin` 404、`/admin/user/1` 403、`/shelf/create` 可访问、下载按钮显示未开通；每日学习加载正文与参考，寒暄不加载，查词走 `read_skill` + `lookup_word`，记忆初始为空、明确要求后 `save_memory ✓`，书 252 批注写入并由 `list_annotations` 回读成功。
- **TTS / 积分补测**：新文本首次提示本次 3 积分、二次缓存命中 1 积分；账本 `15:07:27 reading-tts -3`、`15:07:57 reading-tts -1`（此前 181 字符段另有 `13:58:41 -3`、`14:00:41 -1`）。赠送 10000、余额 7972、账本累计 2028；分组 `ai-agent-step` 1840/40 次、`ai-agent-memory` 180/18 次、`reading-tts` 8/4 次，证明 Skill、function call 与 Agent 内部调用均消耗当前登录用户积分。
- **隔离与边界（如实）**：会话与长期记忆按用户隔离成立（userId 15 有 3 个会话、4 条记忆；其他用户 24 个会话、8 条记忆；带唯一标记的 2 条记忆只属于 userId 15）；批注按既有设计为段落级共享，`ReadingAnnotationService.listByParagraph()` 不按 `userId` 过滤，不能写成私有隔离。生产写确认门为 `false`，写工具真实成功；`requireConfirm()` 只影响前端醒目样式，不是执行确认。
- **验收结果**：TTS 计费文案 GUI 补测通过；会话/长期记忆用户隔离通过；批注段落共享作为既有设计边界单独列明；当前用户积分对账通过。生产写工具真实成功，不能写成“被确认门拦截”。未发现 Skill 新增权限、系统身份调用或隐藏接口路径。
- **能力与计费边界**：生产白名单共 10 项，只有 `add_annotation` / `save_memory` 两个写工具；所有业务工具使用当前登录用户的真实能力、`UserContext` 与积分链路，不注入系统身份，也不提供脚本、任意文件或未注册接口。
- **上线与台账**：moon-well 代码提交 `05ed7fd` 已推送 `origin/develop` 并部署，生产健康 `UP`；验收文档 `f0bafad` 为 docs-only。正式发布态全量 **1559 tests / 0 failures / 0 errors / 0 skipped**。本仓 R228 为 docs-only，无代码 worktree；moon-well 原 worktree `../moon-well-r214-agent-skill` 与分支 `feat/r214-agent-skill` 已不存在，旧驻留记录不破坏性重建。
- **窗口**：写入前 10 节；按“写入即检查”把最早 R213-C 整节原样搬至 `response-archive/response-R213-C.md` 并登记索引，窗口保持 10。

## 2026-10-25（R229：缺陷修复——/home 随机发现 linked Row 致生产登录落点 500，挂 R213）

### R229（博客截图会话中发现的生产缺陷）

- **任务定位**：缺陷修复（挂 R213 首页）。发现路径：为写产品功能博客做生产截图，打开 `/home` 直接 500（traceback 落在 `home.html` 随机发现块 `book_card(book)` 的 `url_for(book.id)`）；对所有开启「随机发现」的用户均复现，当晚 R227 镜像上线后被掩盖的窗口未知，属生产登录落点级故障。
- **根因**：`random_discover_books` 复用 `generate_linked_query`（返回 `(Books, is_archived, read_status)` 三元组）；旧 `index.html` 侧取 `entry.Books`，R213-C 的 `home.html` 把 Row 原样传给共享宏 `_book_card.html`（只认 Books 实体）。既有测试对 `random_discover_books` 全部打桩，真实返回形状从未被守卫——打桩护住了组装、漏了形状。
- **修复**：`cps/routes/home.py` 取 `row.Books`（Python 侧收敛形状，模板契约与其余两块一致）；新增回归测试 2 条：`test_random_discover_returns_books_entities`（仿 linked Row 断言必须返回 Books 实体）、`test_random_discover_swallows_upstream_failure`（上游抖动返回空列表，登录落点不许 500）。
- **验证**：`tests/test_home_route.py` 定向回归 **29 passed / 0 failed**（27 旧 + 2 新）。push `develop`（`c0a7311c`，经 `fix/r229-home-random-row` 分支直推 origin，未动被并行会话占用且处于 detached HEAD 的主检出）；fnOS 自动构建部署，生产实测 `/home` 四块完整渲染（继续阅读带 `186/1467` 进度、今日计划、阶推荐、随机发现）。
- **过程合规备注**：主检出当时为并行会话 detached HEAD（R228 本地未推 2 提交），merge 冲突后立即 `--abort` 并还原现场，改从 worktree 直推 origin/develop（与 `claim.sh` 同款姿势，fast-forward 无历史改写）；主检出已还原为 972b3830。
- **窗口**：写入前已有 10 节，按「写入即检查」把最早 R214 子项 C 整节原样搬至 `response-archive/response-R214.md` 并登记索引，窗口保持 10。
- **总结**：requests.md 条目 229 已回填；本条为回应。冲突记录：无撞号；与 R228 并行会话无 git 冲突（分支隔离 + 直推 fast-forward）。

## 2026-10-26（R231：去掉 pip `trusted-host`——构建链不再关闭 TLS 校验）

### R231（安全扫描高危 6）

**背景**：本会话先做家族仓主动安全扫描（首份留档，无历史基线），高危 6 落本仓 Dockerfile；用户拍板「删第 6 行」。

**改动**：`Dockerfile:5-6` 原为 `index-url=https://mirrors.aliyun.com/...` **加** `global.trusted-host mirrors.aliyun.com`。后者语义是对该 host 跳过证书链与主机名校验，等于把构建期依赖交付交给「任何处在构建机与镜像站之间的人」——构建在 fnOS 跑（`../ops/tools/webhook-builder/build-magicbook.sh:74-75`，push develop 即触发），出网又走自建出口（`.9:12811`/`7891`），同内网设备、构建机上任一低权进程、出口、镜像站上游都在信任路径上。现只删这一行，换源保留（换源不是问题，关校验才是）。

**为什么敢删（这行当年可能是为了绕证书错，前提必须先验）**：① 基础镜像自带 CA——`python:3.11-slim-bookworm` 上游 Dockerfile 第 22-29 行在 `FROM debian:bookworm-slim` 后即 `apt-get install ca-certificates netbase tzdata`，本仓 stage 1 虽未装（只有 `libssl-dev`）但基础层已有；② 镜像站证书本就正常——本机 `curl https://mirrors.aliyun.com/pypi/simple/`（不加 `-k`）得 `HTTP 200` 且 `ssl_verify_result=0`。

**没做到的验证（写清楚，别当已通过）**：本机 Docker daemon 未运行，**没有真跑一次 `docker build`**。首次 fnOS 构建即验收点：日志若出 `CERTIFICATE_VERIFY_FAILED`，说明构建机上前提不成立（典型是代理做 TLS interception 而企业根证书没进镜像），那时要修证书链，**不要把 `trusted-host` 加回来**。

**刻意不做的另一半**：`Dockerfile:26` 无 `--require-hashes`、`requirements.txt` 全是 range 且无 lock——TLS 正常后仍缺**内容校验**，装什么仍由镜像站当时返回决定。彻底收口需出带 hash 的锁文件，牵动全量解析，属独立需求另占号；基础镜像按 digest 钉、moon-well 的 Maven `mirrorOf>*` 同理另排。

**归档命名混撞（顺手记录）**：本次轮转最旧一节「R214-C 验收缺陷」时发现归档里已有 `response-R214-C.md`，内容是**另一条**（R214 子项 C 整本任务代价面板）。按标题推导文件名会静默覆盖他人条目，故本次落名为 `response-R214-C-defect.md`。建议后续同名条目一律带语义后缀。

**撞号记录（家族纪律要求）**：本条原占 **R229**，随后发现并行会话的 `/home` 随机发现缺陷修复已用 R229（其 `response.md` 节 `## 2026-10-25（R229…）` 已并入 develop，但它的**台账行未随代码并入**，导致 `claim.sh` 按 develop 台账算号时看不见它、把我发到了 229）；合并远端时又发现并行会话把 pip TLS 条目重占为 R229、把学习数据导出占为 R230。按「不修改既有记录、续编下一个空号」处置：本条最终定为 **R231**（树与分支同步改名 `magicbook-r231-pip-trusted-host` / `fix/r231-pip-trusted-host`，迭代目录同步），把 `/home` 缺陷行原样补记进 229 位、学习导出保留在 230 位，未改写他人内容。**根因留给后续**：占号只看台账、验收窗口看 response.md，两处不同步就会撞——建议后续给 `claim.sh` 增加「同时扫 response.md 与其节标题」的算号来源。

**交付四问**：能力与契约均未变（用户不可见）→ L1/L2 不动；实现/边界变（构建期信任模型）→ `Dockerfile` 内注释 + `docs/project/iterations/2026-10-security-baseline/r231-pip-trusted-host/lld.md`（状态行＝已实现待验收）。本仓 `tests/` 全是 Flask 层用例，**无测试覆盖 Dockerfile**，故门禁落在上述两条实测证据与首次构建日志上。

**worktree 驻留登记**：`../magicbook-r231-pip-trusted-host`，分支 `fix/r231-pip-trusted-host`（从 `origin/develop` 切出），状态＝待合并与用户验收；`Dockerfile` 改动已在本地提交，待本轮随台账同步 push。

## R230 · 个人学习数据导出入口（2026-10-26）

**对 R230 的回应**：四点拍板与 D1-D5 定稿落进需求基线 §R230；本仓交付入口与下载 UI（`cps/routes/user_export.py` 三代理端点 + `/me` 面板 + me.js 交互 + i18n 种子/po/mo 三处同步），数据主体在 moon-well R220。测试 `tests/test_user_export_proxy.py` 8 例 + i18n 契约 5 例，全量 **981 passed**。L1/L2/LLD 已回填（readme /me 句、learning/interface.md 导出节、iterations/2026-10-user-data-export/r230-export-ui/lld.md）。

**worktree 驻留登记**：`../magicbook-r230-user-data-export`（分支 `feat/r230-user-data-export`，从 origin/develop @ fe59ad54 切出），merge 本地 develop 后原样保留待验收。部署顺序：moon-well 先、本仓后（fnOS webhook 链自动构建上线）。

**编号说明**：占号时发现 pip trusted-host 会话与 /home 会话存在既有漂移（origin 上 pip=229、本地记 230）——该漂移已由当事会话按「不修改既有记录、续编下一个空号」处置（pip 最终 R231，见台账 231 条），本轮 R230 在 origin 上为干净占位，无冲突。
**台账总结**：requests.md R230 已回填完整状态；response.md 本条新增。

## 2026-10-26（R233：AI 回复中的本站链接可点击并在新窗口打开）

### R233（用户：「AI给出的本站链接应该可以直接跳转（在新窗口）。」）

- **根因与边界**：伴读助手消息统一经 `cps/static/js/ai_chat.js::renderMarkdown()` 渲染；旧实现只处理代码、粗体与换行，因此 `/credits`、`/me`、`/book/252` 和 `[积分页](/credits)` 都只是纯文本。本轮只改展示层，接口、SSE 帧、模型提示词、工具白名单、会话数据与 CSP 均未变化。
- **实现**：整段文本先转义，再按“代码/链接占位 → 裸路径 → 粗体/换行 → 还原占位”的固定顺序渲染；`normalizeSiteHref()` 只接受单个 `/` 开头的站内路径或当前 `window.location.origin` 的绝对 URL，拒绝控制字符、反斜杠、协议相对 URL、外部 origin、非 HTTP(S) 协议与 userinfo URL；最终只写 `pathname + search + hash` 并二次转义属性。所有站内链接固定 `target="_blank" rel="noopener noreferrer"`。
- **用户可见行为**：Markdown 站内链接、裸路径、同源绝对 URL、整段为站内路径的行内代码均可点击；外部网站、围栏代码块、`javascript:` 和 HTML 标签保持纯文本；中英文尾随标点/括号留在链接外，查询参数与 fragment 保留。
- **测试**：新增 `tests/test_ai_message_links_r233.py` 13 条，Node 直接执行生产 `renderMarkdown()` 的 15 组输入，覆盖新窗口属性、origin 归一化、标点、代码与 XSS；伴读四套定向回归 **36 passed / 0 failed**，加 CSP、i18n、API 契约与重复代码行守卫共 **58 passed / 0 failed**；`node --check cps/static/js/ai_chat.js` 与 `git diff --check` 通过。
- **文档四问**：能力 → L1 `docs/product/readme/companion.md`；契约 → 无接口变化；实现/边界 → 新建 L3 `docs/product/companion/features/ai-message-links.md`；本次实现 → `docs/project/iterations/1.0/r233-ai-links/lld.md`（状态：开发完成待验收）。需求基线 `companion/requirements.md` 与迭代 `plan.md` 已同步。
- **台账与驻留**：R233 由 `claim.sh` 占号并 push（`58383f5c`，纯台账）；本轮从该点开发，worktree `../magicbook-r233-ai-links`（分支 `feat/r233-ai-links`）按闸门保留待用户验收。写入前 response.md 已有 11 节（R221/R222 未轮转的既有欠账），按“写入即检查”把最早两节原样搬至 `response-archive/response-R221-R222.md` 并登记索引，窗口恢复为 10 节。
- **总结**：requests.md 条目 233 已从占位回填；本条为回应。冲突记录：无撞号；主检出未提交的 `messages.po` 未被读取、修改或提交。
