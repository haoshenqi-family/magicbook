# response-archive：R120–R125（2026-10-02 ～ 2026-10-07）

> 2026-10-08 R135 写入触发「超 10 立即搬移」，连同 R134 登记的窗口欠账一并补账：R120 / R122 / R123 / R124 / R125×2 共六条回应自 response.md 原样搬移，只搬原文、不总结、不改写；response.md 窗口自 R126 起保留最近 10 个 request。
> 注：R120 条目原文挂在残留的「## 2026-10-02（R111 阅读器导览视觉重做：降噪微调，保留挖洞）」日期头下，该头属已归档的 R111 组（response-R111-R119.md），搬移时略去该头，条目正文未动。

## 2026-10-02

### R120（三本《新概念英语85》epub 章节末位整章播放——用户决定放弃）

- **需求**：#102（第三册）/#103（第四册）/#104（第二册）epub 阅读器每章末尾挂整章 mp3。
- **调研结论（阻断性数据事实）**：三本 epub 为外研社 **1985 老版**课文结构，而 nce-audio 美音源自 **1997 修订版**，课序天然不对齐——按编号直接映射第四册仅 4/60 对得上；改按课文标题模糊匹配实测覆盖：二册 93/96（97%）、三册 50/60（83%）、**四册仅 21/60（35%）**。缺口全部是老版特有课文无对应录音，代码无法弥补。
- **决策**：用户选「放弃匹配」，未写实现代码。曾拟方案留档备查：服务端 `/nce/epub/<book_id>/chapters`（读库内 epub 解析 ncx + manifest 标题匹配，返回 {spine href→课号}，进程缓存）+ epub.js rendered 钩子在命中章节末尾注入原生 `<audio controls>`（复用 `/nce/<id>/audio/<num>` 206 流）+ 三本 calibredb 补 series 元数据。若未来取得 85 老版配套音频源（尤其四册 60 课版），方案可直接复用。
- **产出**：三本 epub ncx 标题表与 manifest 匹配率实测脚本（docs/temp，gitignore）。

### 总结

- **requests.md**：占号 R120。
- **response.md**：本条；120%10==0 触发轮转——R102–R110 搬入 `response-archive/response-R102-R110.md`，保留窗口 R111–R120。
- **冲突记录**：无。

## 2026-10-05（划词翻译 6 秒排查）

### R122（/ajax/reading-translate 划词 evidence 耗时 6.13s 归因）

- **现象**：用户读 NCE3 Lesson 1 划词 "evidence"，DevTools Timing：Queueing 0.84ms / Stalled 0.75ms / **Proxy negotiation 0.27ms** / Waiting 6.13s / Download 4.93ms。
- **链路拆解（实测）**：magicbook `/ajax/reading-translate` 是纯代理（`_moonwell_proxy` → `MOON_WELL_READING_URL=http://192.168.31.9:8082` 本机直连）；moon-well `ReadingVocabularyService.translate`：ES 段落缓存查 → 单词走 iciba（3s 超时×2 词形还原）→ miss 才 LLM。
- **moon-well 侧证据（app-log-moon-well，修正 REQ 行时间戳=完成时间）**：
  - 20:31:20.349 到达、**161ms 完成**（source=dictionary：ES 缓存 miss + iciba 命中 + 缓存回写，全部健康）；20:31:53/59、20:33:23 三次重复划词 10/5/13ms（ES 缓存命中）。
  - 反推浏览器发送时刻 ≈ 20:31:14.41 → **~5.94s 丢失在「浏览器发出 → moon-well 入口」之间**，翻译本身无罪。
- **逐一排除（都有证据）**：moon-well 处理慢（同窗口 /llm/task/accept 260-310ms 正常基线，现在也是 ~250ms）；401→refreshToken→重试（HttpLoggingFilter @HIGHEST_PRECEDENCE+10 先于 Spring Security，401 必留痕——早上 08:56 三条 401 可证；20:31 窗口 0 条 401、0 条 /auth 调用）；magicbook 重启（容器 up 自 10-04 15:39）；fnOS 内核/IO 事件（journal 20:29-20:33 干净）；Tailscale 路径劣化/PMTU 黑洞（fnOS↔Server2 有 agent 30s 心跳保温；实测容器内 4KB POST 30ms、宿主机一致）；magicbook 鉴权（本地 session+本机 MySQL，无远程调用）。
- **归因（剩余盲区）**：时间丢在浏览器→Traefik→magicbook→moon-well 入口这段，而这段当前**零观测**（Traefik 无 access log、magicbook 代理层成功请求不打耗时日志、magicbook ES 日志窗口为空）。DevTools 出现 "Proxy negotiation" 行证明浏览器走了本地代理（Clash/Surge 类）——**首选假设：本地代理/家庭网络瞬时抖动**（代理死节点 fallback 超时典型 5-6s，与 6.13s 高度吻合）；次选 Traefik→magicbook（Tailscale）瞬时抖动。事后无法二分定责。
- **建议（未实施，待用户定夺）**：① 本地代理对 `*.haoshenqi.top`/`*.haoyuhang.top` 加 DIRECT 规则再观察；② Traefik 开 access log（一个 flag，拿到每请求后端耗时，补最大盲区）；③ magicbook `_moonwell_proxy` 成功路径记 INFO 耗时（>1s 记 WARN）。
- **交付状态**：纯诊断，未改任何代码。

### 总结

- **requests.md**：占号 R122。
- **response.md**：本条；122%10≠0，无归档轮转。
- **冲突记录**：无。
- **【2026-10-05 补充】R122 根因确认**：用户确认是本地代理问题（与排查结论首选假设一致）。服务端各环节均有证据排除，DevTools "Proxy negotiation" 行是关键指向；建议的 DIRECT 规则仍值得加上以防复发。

## 2026-10-06（R124 阅读器单词详解）

### R124（划词气泡「详」按钮 + 六板块详解面板）

- **回应**：阅读器与 magiclens v0.4.0 同步获得单词详解能力（后端复用已上线的 moon-well R100，magicbook 侧零 LLM/存储改动）：
  - **代理**：`cps/web.py` 增 `POST /ajax/reading-word-detail`（`@user_login_required` + CSRF），校验/归一化与 word_mark 完全同口径（`_READING_WORD_RE`、小写、弯撇号归一、≤64），转发 `GET /vocabulary/detail/{word}`（30s——缓存 miss 时 moon-well 现场生成）。
  - **前端**（epub.js/reader.css/read.html/i18n）：气泡在 🔊/＋/－ 旁挂「详」按钮（仅单个英文单词）；详解面板六板块渲染与 magiclens 同构（lemma 标题、「变体」角标+说明行、不规则金色 chip、空板块隐藏、textContent 组装禁 innerHTML、请求序号防旧响应）。
  - **交互耦合（审查修复）**：P0-1 seq 取号在 closeWordDetailPanel 之前会把自己的响应作废（面板永卡 Loading）→ 先清理后取号；P0-2 主文档 mousedown「点气泡外即收」会把兄弟节点的详解面板连带收走 → 豁免面板内点击；P1-1 气泡 5s 自动隐藏必然杀掉 30s 级生成 → 面板存活期间挂起计时、面板关闭恢复倒计时；P2-1 Esc 捕获层 stopImmediatePropagation（一次 Esc 只关面板这层）。
  - **i18n**：14 个新词条入 i18n_seed.html + zh_Hans_CN po（译文补全）+ pybabel 重编译 .mo，`test_i18n_seed_contract` 五契约全绿。
  - **测试**：新增 5 个 word-detail 测试（登录门禁/非法词 400/归一化转发 GET+30s+禁代理/上游故障 503/阅读器接线契约——含「seq 取号后不得再自增」「非空 innerHTML 禁入」两条防回归断言）；全量 334 通过。
- **总结**：requests.md 占号 R124（撞号更正：本会话初占 123 与并行会话「会话 cookie 持久化」R123 撞号，按纪律不改既有记录、续编 124，重复的 123 条目保留并在 124 中标注）；response.md 本条；冲突记录：编号撞号如上，无需求内容冲突（并行会话改 cps/__init__.py/reverseproxy.py，本任务改 web.py/epub.js 等互不重叠）。未 push——push develop 将触发 fnOS webhook-builder 自动构建部署，待用户确认。

### R124 补记（部署上线）

- **部署链**：push develop（d55a8cd9）→ fnOS webhook-builder 自动构建（11:38:48 推镜像 :latest）→ app-manager deploy SUCCESS → 容器 healthy；`POST /ajax/reading-word-detail` 未登录请求 400（CSRF 门控，对照不存在路由 404 确认路由匹配），登录用户可正常使用。
- **验收提示**：阅读器划词 → 气泡点「详」→ 六板块面板；重点 ran/running 变体还原与二次查询秒回。

### R123 会话 cookie 持久化（修「一天就要重新登录」）

- **根因**（承接 moon-well R101 诊断）：moon-well access/refresh token 存在 magicbook Flask 签名会话 cookie 内，未配 session.permanent → cookie 无 Expires/Max-Age（浏览器会话级），浏览器一关登录态连同 token 全丢。ES 日志佐证：近 30 天 moon-well 服务端 0 次 JWT 过期拦截，而 magicbook 近 16 天中 14 天每天 1–4 次 token exchange（每日重登）。
- **修复**：`PERMANENT_SESSION_LIFETIME` 默认 30 天（`SESSION_PERMANENT_DAYS` 可调）+ `SESSION_REFRESH_EACH_REQUEST=True` 滑动续发 + 全局 before_request 钩子对**非空**会话标记 permanent（空会话不动——permanent setter 写 _permanent 置 modified，会破坏内部 M2M 端点「响应不携带会话 cookie」契约）。与 moon-well JWT access 30 天/refresh 90 天（R101）对齐。
- **顺带修复**：①`ReverseProxied.script_name` 构造期未初始化，session_transaction 等绕过 WSGI 的 save_session 路径会 AttributeError（潜在雷，生产未触发）；②登出 `/logout` 只清 flask-login 身份键不清 moonwell token——持久化后 token 会在 cookie 里滞留 30 天滑动续期，登出改为 `session.clear()`（save_session 对空+modified 会话下发删除头）。
- **审查记录**：独立 agent 交叉审查 1 P1（登出 token 滞留，已随本修复一并修）+ 8 P3（采纳：钩子跳过已标记会话、注释机制描述更正、测试断言相对 config 生效值免受本地 .env 干扰；记录取舍：strong session protection 对 permanent 会话退化为 basic（flask-login 上游刻意设计），个人工具接受；SESSION_COOKIE_SECURE 未加——保留 fnOS 内网 http://192.168.31.9:8083 直连可用性，如确认纯 HTTPS 访问可加）。占号冲突：本会话初占 123 后并行会话「单词详解」也占 123，对方按纪律续编 124（见 requests.md），本任务沿用 123，无文件冲突。
- **测试**：新增 tests/test_session_permanent.py 4 例（config 生效/cookie 带 Expires≈lifetime/钩子注册/登出清空+删除头）；全量 335 通过。已知边界：cw_login remember_token 恢复路径当次请求不标记 permanent，下一请求自愈。
- **部署**：push develop → fnOS webhook-builder 自动构建部署；上线后需重新登录一次（旧 cookie 仍为浏览器会话级），此后浏览器重启不再掉登录。
- **总结**：requests.md 占号 R123（并行撞号已按纪律处置）；response.md 本条 + 收录并行会话 R124 部署补记；冲突记录：编号撞号已注明，无内容冲突。

## 2026-10-06（R125 词汇测试结果页难度推荐 + 一键应用）

### R125（结果页展示推荐难度，一键应用到阅读设置）

- **回应**：词汇量测试完成后，结果页按 moon-well R103 报告新字段 `recommendedHardLevel/Name` 展示推荐并支持一键应用（对应 requests.md R125）：
  - **DOM**：`#vt-result` 内增 `#vt-reco-line`（推荐/确认/失败文案，className 携带 `vt-el` 保 `[hidden]` 兜底）与 `#vt-apply-level` 按钮；按钮 msgid 用 `Apply suggested level`——po 里上游 `"Apply"` 已被误译为「查询」，撞上即回错词。
  - **渲染**（`renderLevelRecommendation`）：旧后端无字段 → 静默不显示（先行部署降级态）；与当前档位一致 → 只显示「当前难度等级与该测试结果一致。」不递按钮；不同 → 「建议难度等级: {name}」+ 按钮。当前档位取 `#hard-level-select`。
  - **应用**：POST `data-level-url`（= 既有 `web.reading_settings_update_hard_level`，**零新代理路由**），复用 `post()` 的 CSRF 头/自愈与 401 判读；成功 `markCurrentLevel` 同步下拉选中值、清各 option `(default)` 后缀、更新 `#rs-current-level` 行、隐藏 `#rs-default-label`，行文案变「难度等级已更新」；失败（网络/业务码）行变红可重试。
  - **交叉审查**（独立 agent）：P1 已修——apply 请求纳入 epoch 作废纪律（发请求捕获 `mine=epoch`；`.then/.catch` 先复位在途锁再判 stale，迟到响应不得写新一轮结果页或吞按钮；stale 但业务成功仍先 `markCurrentLevel` 反映服务端真值）；P2 已修（`(default)` 后缀残留）；P3 采纳 `pendingRecoName` 复位；P3「load_error 态应用成功后设置卡仍显错误横幅」接受不改（浮层内已有确认，功能不受影响）。
  - **i18n**：4 个 mbT 词条入 `i18n_seed.html` + zh_Hans_CN po（补丁脚本 `docs/temp/scripts/vt_r125_i18n_patch_po.py`，width=76 原子口径）+ `pybabel compile` 重编 .mo；`test_i18n_seed_contract` 五契约全绿。
  - **测试**：`test_vocab_test_proxy.py` 增 `test_result_view_renders_level_recommendation_surface`（DOM 面 + `data-level-url` + `rs-current-level` 锚点）并给 `REPORT` fixture 补两字段守透传形状；全量 pytest **336 通过**。
  - **文档**：us4 设计 §4 报告形状补字段 + 新增 §6 R125 增量节；ac 文档新增 G 节 8 条（含端到端待部署后核与交叉审查留痕）。
- **部署**：未 push——push develop 触发 fnOS webhook-builder 自动构建部署，按「提交≠推送」纪律待用户确认；对旧后端已做静默降级，先推前端亦安全。
- **总结**：requests.md 占号 R125（无撞号）；response.md 本条；冲突记录：无。

## 2026-10-07（R125 详解面板粘性）

### R125（面板不因离开/误点关闭 + AI 生成中提示）

- **回应**：详解面板与划词气泡生命周期解耦（epub.js）：
  - 面板仅由 ✕/Esc 关闭；滚动、新选区、翻页、点正文（含 iframe 内）不再误关面板——生成等待期 15~30s 误关一趟就白等。
  - 加载文案改为「AI 正常生成中…（首次查询约 15~30 秒，面板保持打开并自动显示结果）」（i18n seed + zh po/.mo 同步）。
  - 失败态（非鉴权）支持点击重试——后端已缓存结果时重试瞬时命中。
  - 气泡自动隐藏挂起逻辑保留（面板存活期间气泡不消失），面板关闭后气泡恢复倒计时。
  - 契约测试增两条防回归：closeTranslationPopover 不得调用 closeWordDetailPanel；点外关闭监听必须不存在。全量 336 通过。
- **SSE 取舍说明**（用户提议「优先使用 SSE」）：暂缓。详解是单次结构化 JSON 输出，流式到达的半截 JSON 无法优雅增量渲染，逐板块流式需自写增量 JSON 解析器，收益低复杂度高；当前痛点（误关 + 静默等待）已由面板粘性 + 明确提示解决，且 thinking 关闭后生成仅 15~30s。若之后想「逐板块流式呈现」再立项 SSE 版（moon-well 流式接口 + 两端增量解析）。
- **总结**：requests.md 占号 R125；response.md 本条；冲突记录：无。
