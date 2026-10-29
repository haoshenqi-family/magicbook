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
- `response-archive/response-R221-R222.md`：R221 口语陪练语音优先 + R222 生成书籍简介 400（2026-10-26 R232 写入触发轮转搬移，原样搬移不改写）
- `response-archive/response-R225.md`：R225 邀请注册跳转 + 普通账号阅读/下载 403 + 品牌封面占位（2026-10-28 R236 写入触发轮转搬移，原样搬移不改写）
- `response-archive/response-R226.md`：R226 阅读器验收缺陷——伙伴白圆底/幽灵问号/翻译连续重排（2026-10-28 R237 写入触发轮转搬移，原样搬移不改写）
- `response-archive/response-R227.md`：R227 Buddy 语音提问与回复朗读（2026-10-28 R238 写入触发轮转搬移，原样搬移不改写）
- `response-archive/response-R228.md`：R228 moon-well R214 伴读 Agent Skills 的 magicbook 消费侧说明——2026-10-28 R239 写入触发轮转搬移，原样搬移不改写
- `response-archive/response-R229.md`：R229 `/home` 随机发现 linked Row 致生产登录落点 500——2026-10-28 R242 / R244 并行写入均轮转到本节，保留单份，原样搬移不改写
- `response-archive/response-R231.md`：R231 去掉 pip `trusted-host`（构建链恢复 TLS 校验）——2026-10-29 R243 / R244 并行写入均轮转到本节，保留单份，原样搬移不改写
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
- `response-archive/response-R223.md`：R223 Buddy 悬浮球化（透明头像 + hover 径向快捷气泡）——2026-10-26 R232 会话合并 origin/develop（R233 一节并入）后窗口达 11 节，原样搬移不改写
- `response-archive/response-R224.md`：R224 本轮测试修复未完成项收口（R219 / R212 / R213-B6 / R214-C）——2026-10-26 R234 写入触发轮转搬移，原样搬移不改写
- `response-archive/response-R230.md`：R230 个人学习数据导出入口与任务下载 UI——2026-10-29 R241 写入使窗口达 11 节，原样搬移不改写
- `response-archive/response-R232.md`：R232 伴读面板不再显示 token 用量——2026-10-29 R243 合并 R244 后窗口达 11 节，原样搬移不改写

---

> 归档索引：[response-R01-R31.md](response-archive/response-R01-R31.md) · [response-R32-R49.md](response-archive/response-R32-R49.md) · [response-R50.md](response-archive/response-R50.md) · [response-R51-R70.md](response-archive/response-R51-R70.md) · [response-R70-R80.md](response-archive/response-R70-R80.md) · [response-R81-R101.md](response-archive/response-R81-R101.md) · [response-R102-R110.md](response-archive/response-R102-R110.md) · [response-R111-R119.md](response-archive/response-R111-R119.md)（2026-10-08 R129 补账搬移）· [response-R120-R125.md](response-archive/response-R120-R125.md)（2026-10-08 R135 写入触发搬移，含 R134 登记的窗口欠账补账）· [response-R126-R131.md](response-archive/response-R126-R131.md)（2026-10-09 R141 写入触发轮转搬移）· [response-R132-R133.md](response-archive/response-R132-R133.md)（2026-10-10 R143 写入触发轮转搬移） · [response-R134.md](response-archive/response-R134.md)（2026-10-10 R144 写入触发轮转搬移） · [response-R135-R137.md](response-archive/response-R135-R137.md)（2026-10-10 R147 写入触发轮转搬移，含 R145/R146 两次写入的窗口欠账补账） · [response-R138.md](response-archive/response-R138.md)（2026-10-11 R152 写入触发轮转搬移） · [response-R139.md](response-archive/response-R139.md)（2026-10-11 R153 写入触发轮转搬移） · [response-R140.md](response-archive/response-R140.md)（2026-10-11 R153 复核后的补搬——R152 写入时搬走 R138 后窗口仍为 11） · [response-R141-R142.md](response-archive/response-R141-R142.md)（2026-10-11 R155 集成时窗口超限搬移） · [response-R144-R153.md](response-archive/response-R144-R153.md)（2026-10-12 R161 写入触发轮转搬移，清并行欠账 R144–R153） · [response-R154.md](response-archive/response-R154.md)（2026-10-12 R165 写入触发轮转搬移） · [response-R155-R156.md](response-archive/response-R155-R156.md)（2026-10-13 R166 写入触发轮转搬移，含同日同编号「细筛」那条） · [response-R157.md](response-archive/response-R157.md)（2026-10-13 R166 分支 merge origin/develop 后窗口仍达 11，续搬最旧一节） · [response-R156-mic.md](response-archive/response-R156-mic.md) · [response-R158.md](response-archive/response-R158.md)（2026-10-13 R168 写入触发轮转搬移）（2026-10-13 R167 写入触发轮转搬移；与 response-R155-R156.md 里的同编号「细筛」条目不同事） · [response-R160-R164.md](response-archive/response-R160-R164.md)（2026-10-14 R172 写入触发轮转搬移，窗口转入 R161 起） · [response-R161-R162.md](response-archive/response-R161-R162.md)（2026-10-14 R173 写入触发轮转搬移，窗口转入 R165 起） · [response-R165-R173.md](response-archive/response-R165-R173.md)（2026-10-15 R183 写入触发轮转搬移，窗口转入 R174 起） · [response-R174-R177.md](response-archive/response-R174-R177.md)（2026-10-16 R185 写入触发轮转搬移，窗口转入 R178 起） · [response-R175.md](response-archive/response-R175.md)（2026-10-16 R188 写入触发轮转搬移） · [response-R214-C.md](response-archive/response-R214-C.md)（2026-10-25 R229 写入触发轮转搬移：R214 子项 C 整本任务代价面板；与既有 response-R214.md（子项 A）不同事）

## 2026-10-26（R233：AI 回复中的本站链接可点击并在新窗口打开）

### R233（用户：「AI给出的本站链接应该可以直接跳转（在新窗口）。」）

- **根因与边界**：伴读助手消息统一经 `cps/static/js/ai_chat.js::renderMarkdown()` 渲染；旧实现只处理代码、粗体与换行，因此 `/credits`、`/me`、`/book/252` 和 `[积分页](/credits)` 都只是纯文本。本轮只改展示层，接口、SSE 帧、模型提示词、工具白名单、会话数据与 CSP 均未变化。
- **实现**：整段文本先转义，再按“代码/链接占位 → 裸路径 → 粗体/换行 → 还原占位”的固定顺序渲染；`normalizeSiteHref()` 只接受单个 `/` 开头的站内路径或当前 `window.location.origin` 的绝对 URL，拒绝控制字符、反斜杠、协议相对 URL、外部 origin、非 HTTP(S) 协议与 userinfo URL；最终只写 `pathname + search + hash` 并二次转义属性。所有站内链接固定 `target="_blank" rel="noopener noreferrer"`。
- **用户可见行为**：Markdown 站内链接、裸路径、同源绝对 URL、整段为站内路径的行内代码均可点击；外部网站、围栏代码块、`javascript:` 和 HTML 标签保持纯文本；中英文尾随标点/括号留在链接外，查询参数与 fragment 保留。
- **测试**：新增 `tests/test_ai_message_links_r233.py` 13 条，Node 直接执行生产 `renderMarkdown()` 的 15 组输入，覆盖新窗口属性、origin 归一化、标点、代码与 XSS；伴读四套定向回归 **36 passed / 0 failed**，加 CSP、i18n、API 契约与重复代码行守卫共 **58 passed / 0 failed**；`node --check cps/static/js/ai_chat.js` 与 `git diff --check` 通过。
- **文档四问**：能力 → L1 `docs/product/readme/companion.md`；契约 → 无接口变化；实现/边界 → 新建 L3 `docs/product/companion/features/ai-message-links.md`；本次实现 → `docs/project/iterations/1.0/r233-ai-links/lld.md`（状态：已上线待验收）。需求基线 `companion/requirements.md` 与迭代 `plan.md` 已同步。
- **台账与驻留**：R233 由 `claim.sh` 占号并 push（`58383f5c`，纯台账）；本轮从该点开发，worktree `../magicbook-r233-ai-links`（分支 `feat/r233-ai-links`）按闸门保留待用户验收。写入前 response.md 已有 11 节（R221/R222 未轮转的既有欠账），按“写入即检查”把最早两节原样搬至 `response-archive/response-R221-R222.md` 并登记索引，窗口恢复为 10 节。
- **生产验收**：实现已推送 `origin/develop`（`f68e39b3`），fnOS 构建后的生产 `ai_chat.js` 含 `normalizeSiteHref`、`target="_blank"` 与 `noopener noreferrer`。在 `/book/252` 的真实 AI 回复中，裸 `/credits` 与 Markdown `[我的页面](/me)` 均显示为链接；逐一点击后分别打开 `/credits`、`/me` 新标签，目标页渲染正常。两个锚点实测为 `target="_blank" rel="noopener noreferrer"`；新标签无法取得源页面 `window.opener`（In-app Browser 将其暴露为不可访问的 `undefined`）。定向测试补跑 **13 passed / 0 failed**。
- **总结**：requests.md 条目 233 已从占位回填；本条为回应。冲突记录：无撞号；主检出未提交的 `messages.po` 未被读取、修改或提交。

**修订轮（2026-10-26 晚，用户拍板「用户也可以不设置导出密码」）**：create 代理空/缺省密码转发空 payload（非字符串仍本地 400）；me 表单密码框去必填、帮助文案改双形态说明；任务行按 `encrypted` 显示「未加密」；i18n 种子 +2（"Not encrypted" 与新帮助句）+ po/mo 重编译。`test_user_export_proxy.py` 8→9 例（新增空密码转发），全量 **1000 passed**。文档：requirements §R230 修订段、learning/interface.md、LLD 状态行。moon-well R220 同步修订（`encrypted` 列 + 不加密打包路径，见其 response.md）。


**修订轮 2（2026-10-26 晚，用户两点：文件名带时间 + 导出说明改中文）**：① download 代理改为**透传上游
attachment 文件名**（moon-well 生成 `my-learning-data-<yyyyMMdd-HHmm>-<id>.zip`），上游未给回退本仓缺省；
RecordingProxy 支持三元 headers，新增回退与透传两断言（代理 8→9 例）。② me.html 导出面板与 me.js 导出段
**中文直写**（不经 `_()`/`mbT`——账号 locale=en 时 gettext 回退英文，用户要求恒中文；种子/po 既有词条留存，
i18n 契约 5 例仍全绿）。worktree 说明：原树被大清理删除后本轮按原命名重建（`feat/r230-user-data-export`
自 origin/develop @ e861c0e7 切出），继续驻留待验收。
## 2026-10-26（R234：悬浮球快捷动作——AI 对话恒在第一位且不可删除，升级为服务端不变量）

### R234（用户：「伙伴悬浮球快捷动作，AI 对话始终在第一位切不可删除」）

- **结论先行**：这条铁律此前只由前端保证（`/buddy` 页 chat chip 固定选中不可取消 + `renderBubbles` 恒把 chat 排第一位），服务端 POST 不校验 chat——直连 API 可把 chat 存成缺失（气泡渲染成 6 个，突破 4–5 口径）或末位，存量旧值读回也不归一。本轮把「恒第一位、不可删」落为**服务端不变量**，用户可见行为不变。
- **实现**：`cps/routes/buddy.py` 新增 `_pin_chat_first()`（白名单过滤 + 保序去重 + chat 钉首位）。POST 归一后落库：缺 chat 补首位、错位前移；数量口径连 chat 一起算（4–5），发 5 个非 chat＝6 个，**400 拒绝而非静默截断**。`current_user_view_settings()` 读回对存量旧值（R223 期写入）同样归一并截上限 5，归一后不足 4 个或含白名单外动作回落默认四项——无需数据迁移的惰性纠正。常量 `QUICK_ACTION_PINNED/MIN/MAX` 钉口替代裸数字。
- **前端零行为改动**：仅更正 `buddy.js` 注释（「勾选 2-5 个」实为 4-5 个）；`renderBubbles` 的 `["chat"].concat(...)` 保留作双保险。
- **测试**：`tests/test_buddy_page.py` +3——`test_quick_actions_post_pins_chat_first`（缺 chat 补位 / chat 中位前移，均读回归一结果）、`test_quick_actions_post_rejects_over_max_counting_pinned_chat`（5 个非 chat 400 且不落库）、`test_quick_actions_read_normalizes_legacy_values`（直写 view_settings 模拟三类存量旧值 + 坏数据回落默认）。定向回归 **26 passed**（buddy 页 + R215 结构 + i18n 契约）、buddy 全家 **50 passed**；`git diff --check` 通过。既有 R223 三条校验用例语义不变（2 个 / 未知 / 重复仍 400）。
- **文档四问**：能力 → L1 `readme/companion.md` 悬浮球条目补「恒在第一位且不可删除（R234）」；契约 → 端点形制不变（POST 语义收紧已写进基线）；实现/边界 → 新建 L3 `companion/features/buddy-quick-actions.md`；本次实现 → `iterations/1.0/r234-buddy-qa-chat-first/lld.md`。需求基线 `companion/requirements.md` §R234、R223 LLD 边界两条标注〔已被 R234 取代〕、迭代 `plan.md` 已同步。
- **台账与驻留**：R234 由 `claim.sh` 占号并 push（`500a7316`，纯台账）；实现 `bbd482ae`。写入前 response.md 已有 10 节，按「写入即检查」把最早 R224 节原样搬至 `response-archive/response-R224.md` 并登记索引，窗口恢复 10 节。worktree `../magicbook-r234-buddy-qa-chat-first`（分支 `feat/r234-buddy-qa-chat-first`）按闸门驻留待用户验收。
- **总结**：requests.md 条目 234 已从占位回填；本条为回应。冲突记录：无撞号；主检出未提交的 `messages.po` 改动（去掉积分说明里「约每千 token 消耗 1 积分」一句）经核对与 origin/develop 中 R230 `eecc514b` 已合入的同一 hunk 逐字一致（重复劳动），ff 拉齐前以 stash 挪开、push 后确认该改动已在 HEAD 中，**stash 条目保留未动**（如为并行会话在途工作可自行处置）。


**验收与清理（2026-10-26 晚）**：用户确认「可以了」，验收通过。驻留 worktree 与分支已按闸门清理（本轮功能跨两仓，登记于此两处）：`moon-well-r220-user-data-export`（feat/r220-user-data-export @ df72cc4）与 `magicbook-r230-user-data-export`（feat/r230-user-data-export @ eecc514b）均已 `git worktree remove` + `git branch -d`（-d 通过=确认已合并），树与分支核验清净。PingCode MB-230 → Completed。
## 2026-10-28（R236：弹层恢复「整本任务」入口——跳完整详情页的普通链接）

### R236（用户：「弹层里恢复『整本任务』按钮。不要做其他的」）

- **结论先行**：已完成并上线待验收。范围严格限定为用户点名的这一件事：弹层里恢复入口；未动弹层书名链接、未做「面板进弹层」方案、未改门禁拍板。
- **定性**：R214 子项 C 的修复 `42ddfb19`（开面板按钮加 `not is_xhr` 门禁）引入的可达性回退——完整详情页在 UI 里没有普通左键可达路径（书卡封面/书名链接全部被 `data-toggle="modal"` 截去 `#bookDetailsModal`），管理员入口事实不可达。挂 R214 修复，不建独立 idea。
- **实现**（`detail.html`，最小 diff）：原开面板按钮行（`whole-book-panel-open`）原样不动；紧随其后新增 `{% if current_user.role_admin() and is_xhr %}` 分支渲染普通链接 `<a class="btn btn-default" id="whole-book-panel-link" href="{{ url_for('web.show_book', book_id=entry.id) }}">整本任务</a>`。同 URL 不带 `X-Requested-With` 头即渲染完整详情页，面板在完整页内照常打开；不挂 `data-toggle`/`data-target`（data-api 与 `#bookDetailsModal` 抢点击，`42ddfb19` 同款教训）。门禁不变：仍是管理员专属（R214 拍板①）。
- **守卫**：新增 `test_xhr_modal_entry_is_full_page_link`（链接指向 `web.show_book`、无 data-api、`role_admin` + `is_xhr` 双门禁，反向变异报红）；既有四条守卫（admin 门禁 / data-api 禁用 / XHR 隐藏开面板按钮 / 旧三按钮不复活）原样通过、语义未动。
- **测试**：定向回归 `test_book_detail_r214.py` + `test_whole_book_estimate.py` 50 passed；detail/show_book 相关全量 4 文件（含 `test_word_detail_batch_r176.py`、`test_onboarding_tour.py`、`test_auth_reader_covers_r225.py`）108 passed / 0 failed。
- **文档四问**：能力/契约未变（入口可达性恢复，L1/L2 无需动）；实现与边界 → LLD `iterations/1.0/r214-book-detail/lld.md` §15 + 状态行回填。
- **驻留与闸门**：worktree `../magicbook-r236-wholebook-modal-entry`（分支 `fix/r236-wholebook-modal-entry`，实现 `6180c6bc`，基线 origin/develop `ffc70a3e`）merge 后原样保留待验收；验收通过后 `git worktree remove` + `git branch -d`。真机验收项：管理员账号在书库列表点开任意 epub 书弹层 → 按钮行出现「整本任务」→ 点击落在完整详情页且页内「整本任务」按钮可开面板；普通账号弹层内不出现该入口。
- **窗口**：写入前 10 节已满，按「写入即检查」把最早 R225 整节原样搬至 `response-archive/response-R225.md` 并登记索引，窗口保持 10。
- **总结**：requests.md 条目 236 已从占位回填；本条为回应。冲突记录：无撞号（claim.sh 占号 `ffc70a3e`）；R235 为并行会话占号，未触碰。

## 2026-10-28（R237：整本朗读批次全灭——proxy 三元组被二元组解包；兼答「开始整本朗读后白屏」）

### R237（用户报告：「点击开始整本朗读后白屏」）

- **结论先行**：同一请求下有两个独立缺陷，均已修复：①整本朗读批次 100% 全灭（proxy 三元组被二元组解包）；②进度条外层被浮动列撑成整屏透明层，正文看似白屏、实际是被它覆盖并截走点击。前一轮把白屏仅归因于批次资源耗尽的判断已被 CSSOM/盒模型实测推翻，以下补记真因。
- **证据链**：①生产日志 `voice select failed (too many values to unpack (expected 2))`；②moon-well 侧每段两次 `/tts/speak`（第一次 2~10s 真合成、约 1s 后同文本 6ms 缓存命中）＝worker 重试环的指纹；③app.db 批次台账 done=0 / failed 全量增长；④`MoonWellClient.proxy` 源码恒返回 `(body, status, headers)` 三元组，`cps/reading_tts/service.py` 两处按二元组解包。
- **单测为何漏网**：桩 proxy 也只回二元组——桩没有镜像真实契约，service 的二元解包在单测里永远通过、一到生产就炸。本轮把三个桩全部改为三元组并新增契约守卫（反向变异实测 3 failed）。
- **止血**：发现时 book 50（HP1，3007 段）批次已烧 208 段全 FAILED，已直接置 CANCELLED 停止空转；已合成的音频都在 moon-well 段落缓存里，重新发起批次将全部缓存命中、几乎零成本走完。
- **白屏真因（R237 验收追加）**：生产页 DOM 实测 `.wb-progress` 位于详情页 `.container-fluid` 内；容器中的 Bootstrap 浮动列高 775px 且未清除。进度条外层从容器顶部起算、内层被浮动推到底部：外层 `813px` 高、内层仅 `37px` 且在 y=846，页面中心的 `elementFromPoint()` 命中进度条。正文没有丢失，只是被透明层覆盖；`clear:both` 试验可恢复 38px，但会把吸顶条落到文档底部。
- **白屏修法**：`whole-book-panel.js` 初始化时执行 `$progress.insertAfter($nav)`，把 `#whole-book-progress` 从浮动容器移到导航栏之后，保留原 sticky 吸顶语义。实测重挂后外层 38px、内层 37px、页面中心重新命中 `.book-meta`；新增守卫 `test_progress_bar_is_moved_out_of_float_layout`。
- **测试**：detail 39 passed；整本估算 + tts 5 文件 62 passed；i18n / 重复 JS 行 6 passed。既有反向变异仍成立：worker 解包改回二元组 → 3 failed。
- **合并与部署**：实现 `8c388234` 已 fast-forward 合入 `origin/develop`；推送约 30 秒后生产静态资源包含新逻辑。用该生产资源在真实详情页结构内重放：进度条父节点为 `BODY.book`，外层 38px、内层 37px，页面中心命中 `.book-meta`。
- **文档**：LLD `iterations/1.0/r214-book-detail/lld.md` §16 + 状态行。
- **驻留与闸门**：worktree `../magicbook-r237-tts-proxy-unpack`（分支 `fix/r237-tts-proxy-unpack`，基线 origin/develop `a23c91ba`，实现 `f4d8b934` + `8c388234`）已合并、原样驻留待验收。真机验收项：打开 `/book/50` 发起整本朗读后正文仍完整可点，进度条吸在导航栏下方且高度正常；批次 done 稳定增长、failed 不再全量增长；moon-well 每段仅一次 `/tts/speak`。
- **验收追加（部署重启后批次失联）**：上线后 `book 50` 批次停在 `RUNNING 1239/3007`，`PENDING 1768`、`FAILED 0`；最后推进 14:15:32，14:15:53 与 14:33:00 两次容器重启均发生在批次运行期间。根因是 worker 为进程内 daemon，重启即消失，而台账与页面仍显示 RUNNING；「开始」又被活跃批次禁用，前端无恢复入口。修法：`/ajax/reading-tts-book/status` 增发服务端判定的 `canResume`（未终态 + 有 PENDING + 本进程无活 worker），进度条据此显示「继续」，点击调用既有 retry 原地续跑；失败原因留在进度条内。新增服务/路由/模板 JS 守卫，恢复不新建台账、不重置进度、已完成段与音频缓存继续复用。
- **继续入口合并与部署**：实现 `b48a29ed` 已快进推送 `origin/develop`（`bb6c66f6..a2a1e88f`）。fnOS 于 16:36 完整构建（非 docs-only），app-manager 返回 `deploy SUCCESS`；生产容器 `healthy`，镜像 label `house.build-sha=a2a1e88f...`，线上 `whole-book-panel.js` 已核验包含 `canResume`、`ttsRetry` 与 `.wb-progress-resume` 点击接线。待真机在 `/book/50` 的失联批次上点「继续」，确认 done 从 1239/3007 继续增长且 PENDING 下降。
- **窗口**：写入前 10 节已满，按「写入即检查」把最早 R226 整节原样搬至 `response-archive/response-R226.md` 并登记索引，窗口保持 10。
- **总结**：requests.md 条目 237 已从占位回填；本条为回应。冲突记录：无撞号（claim.sh 占号 `a23c91ba`）。遗留登记：估算面板对 `reading_word_detail_job` 表缺失只 WARN 降级（该表在首次全文详解时由 `_ensure_tables` 创建），暂不处理。

## 2026-10-28（R238：全文单词详解预览卡死——所有书共有的 jQuery 顺序缺陷 + 后台预计算）

### R238（用户：「magicbook 全文单词详解 卡在预览加载中。booi_id=145 这是为什么？所有的书是否都会这样？能否加一个异步任务，后天提前把这个算出来」）

- **结论先行**：卡住的主因不是 `book_id=145`，也不是计算慢，而是页面脚本根本没执行。模板把预览脚本放在 `{% block body %}`，早于 `layout.html` 底部 jQuery；浏览器控制台报 `ReferenceError: $ is not defined`，`/ajax/word-detail-preview` 一次都没发出，所以开始按钮永远禁用。该模板为所有书共用，**所有书都会中招**，只是短书、缓存或人工验证可能没把问题暴露出来。
- **慢链路是第二层问题**：修掉脚本后，原实现仍会在请求线程解析整本 EPUB，再按 2000 词一批串行调用 moon-well `cached-check`；moon-well 每次检查又会做索引级扫描，期间没有持久化快照或中间进度。即使最终能算，体验也可能长时间只有静态「预览加载中…」。
- **实现（`5bb6336e`）**：① 内联脚本移入 `{% block js %}`，由实际渲染顺序守卫钉住「jQuery 先于本页脚本」；② 新增 `reading_word_detail_preview` 快照表（按 `(book_id, book_format)` 唯一）与后台 worker，首请求只校验书目/指纹并立即返回 `RUNNING`，页面每 2.5 秒轮询 `EXTRACTING/CHECKING` 与已检查词数；③ `READY` 10 分钟内直接复用，`FAILED` 60 秒内复用失败，`force=true` 可绕过；④ `start()` 复用同指纹、新鲜 READY 的 `missing_json` 与计数，不再二次解析整本、重扫缓存；⑤ 建表通过 `JobServiceBase.extra_tables` 扩展，保持 B6「建表原语只有一份」。
- **费用与只读边界**：后台预计算只调用 `cached-check`，不会自动生成单词详解；真正生成仍需管理员看过数字后二次确认。没有对全库做自动预热，只有实际打开某本书预览页才计算该书，避免「看管理页就产生全库扫描」。
- **测试**：定向台账/估算/公共骨架 **68 passed / 0 failed**；扩展回归（详解、整本估算、书籍详情、翻译/朗读共用骨架、i18n）**179 passed / 0 failed**；`py_compile`、`pybabel compile`、`git diff --check` 通过。新增守卫覆盖渲染顺序、首请求不跑上游、READY/TTL/force、FAILED 退避、start 复用、迟到 worker 不重算、2000 词分批与建表原语不外叉。
- **文档四问**：能力 → L1 `docs/product/readme/vocabulary.md`；契约 → L2 `docs/product/vocabulary/interface.md`（新增 RUNNING/READY/FAILED、force、10 分钟 TTL、60 秒失败退避）；实现/边界 → L3 `docs/product/vocabulary/features/word-detail-preview.md`；本次实现 → `docs/project/iterations/1.0/r238-word-detail-preview/lld.md`（状态：已上线待用户最终验收）。另补建 vocabulary 需求基线并同步 `plan.md`。
- **驻留与上线**：R238 占号为 `c90ce790`，实现 `5bb6336e`，merge `9577c541`。用户已授权全量测试、push 与生产验收；正式发布态全量 **1014 passed / 0 failed / 4 warnings**，merge 后定向 **68 passed / 0 failed**。已 push `origin/develop`（`c0f4f598`），fnOS build `c0f4f5982d02de4c1e41e05ebb2da5939255db04` 于 2026-10-28 14:33 部署成功，容器 running，build SHA 与登记一致。worktree `../magicbook-r238-word-detail-preview`（分支 `fix/r238-word-detail-preview`）按闸门保留，待用户最终验收后再清理。
- **生产验收（2026-10-28）**：`book_id=145&book_format=epub` 从「正在读取正文」自动进入 READY，去重 4,345 / 已有 1,952 / 待生成 2,043，开始按钮启用；另一本 `book_id=50&book_format=epub` 为 6,111 / 2,269 / 3,411，按钮启用。两本书均实际发出预览 AJAX 并落库，控制台无 `$ is not defined`。`book_id=50` 在 10 分钟窗口内刷新后立即显示 READY，数据库 `computed_at=2026-10-28 06:36:00.278545` 未变化，确认命中同一快照。验收未点击「开始补缺」，未触发生成或 token 费用。
- **后续**：moon-well `cachedLookupKeys()` 的全索引扫描优化未夹带在本任务，建议另立跨仓编号改为按输入词表 `terms` 查询或加短 TTL 缓存。
- **窗口**：写入前 10 节已满，按「写入即检查」把最早 R227 整节原样搬至 `response-archive/response-R227.md` 并登记索引，窗口保持 10。
- **总结**：requests.md 条目 238 已从占位回填；本条为回应。冲突记录：无撞号；本轮把用户所写「后天」按「后台」理解。

## 2026-10-28（R239：全文单词详解预览屈折词覆盖漏算）

### R239（用户：「这个计算不对，完全没有考虑曲折变形。」）

- **结论先行**：用户判断正确。R238 的后台 worker 与页面轮询没有失败，错的是它读取的
  moon-well 覆盖率：`cachedLookupKeys()` 的 ES `_source` 只取 `forms.form`，把判定所需的
  `forms.type` 裁掉了，`books / children / going / beasts / witches / revolting` 等因此全部
  被列为缺失。扫描是全局词库视图，**所有含屈折形式的书都会高估待生成量**，不是 book 145 单书问题。
- **为什么详情面板是对的**：交互查词读完整文档，能按 `forms.type` 把 `books` 还原为 `book`；
  预览走全索引扫描，受另一条投影限制，两条链路口径分叉。详情面板显示“books 是 book 的三单”
  恰好证明缓存内容存在。
- **修复归属**：主责 moon-well R226，扫描同时投影 `forms.form` 与 `forms.type`。magicbook
  **零代码**：不复制屈折规则、不改 worker/快照/分批，也不新增生成调用。
- **快照边界**：READY 有 10 分钟 TTL；moon-well 部署后可能短暂显示旧数字。验收必须用
  `{book_id:145, book_format:"epub", force:true}` 强制刷新，再看 `missingSample` 与新计数。
  这不是再算错一次，而是既有快照尚未过期。
- **测试**：本仓无功能代码，保留预览链路定向回归
  `test_word_detail_batch_r176.py + test_job_service_base.py`：**56 passed / 0 failed**。
  上游修复的请求投影与七类屈折回归由 moon-well R226 的 54 例覆盖。
- **文档四问**：能力形态未变，L1 不改；契约补充 → L2 `vocabulary/interface.md` 的覆盖率权威；
  实现/边界 → L3 `vocabulary/features/word-detail-preview.md`；需求与本次实现 →
  `vocabulary/requirements.md` R239 与 `iterations/1.0/r239-word-detail-inflection/lld.md`。
  R238 LLD 只加“R226 后续修复”注记，不改写当时范围。
- **调用方经验沉淀**：L2 新增 §5.1“调用方使用清单”，L3 新增 §6“覆盖率消费规则”，
  明确本站只抽字面词且只信 `cached-check`；给出
  `原始去重词数 = cachedWords + targetWords + notWordLike` 的可复算关系，禁止用
  “原始词数 − cached”反推目标数，也禁止在前端复制屈折规则补救后端口径分叉。
- **驻留与闸门**：R239 占号 `463c2f4d`；worktree
  `../magicbook-r239-word-detail-inflection`（分支 `fix/r239-word-detail-inflection`）保留。
  R238 worktree `../magicbook-r238-word-detail-preview` 另待验收，未复用、未清理。
- **待验**：moon-well 上线后 force 刷新 book 145，确认六个代表词移出缺失样例，
  `cachedWords` 上升、`targetWords` 下降，预览仍不产生 token 费用。
- **冲突记录**：无撞号；与 moon-well R226 是同一缺陷的两仓记录，算法权威只在 moon-well。

## 2026-10-28（R244：伙伴动效——隐藏消失动画（金光消散）+ 收信动画（站内信预留钩子，纯 CSS））

### R244（用户：「伙伴增加一个消失的动画和一个收到信件的动画」；三项拍板 1B / 2 后续站内信 / 3 金光·纯 CSS）

- **任务定位**：需求（展示层动效），单仓纯前端（`ai_chat.css` + `ai_chat.js` + `ai_chat_panel.html`），moon-well 零改动。伙伴＝全站悬浮球（R223 FAB），现状已有 idle 呼吸 / thinking 起伏 / sleep 打盹三态，但无「消失」与「收信」。
- **三问三答**：① 消失触发＝**B**（用户点悬浮球上的隐藏 ✕，播动画后收起，右缘留唤回小标签，可逆）；② 收信＝**为后续站内信（R243）预留**，本轮只做展示层 + 可调用钩子，不接数据源；③ 视觉＝**纯 CSS + 一点金光**，不引新素材。
- **消失**：悬浮球右上角小 ✕（hover/focus 才显形，平时不抢视线）→ `buddy-vanish`（缩小旋转淡出）+ `buddy-poof`（一圈金色光晕向外扩散消散）→ 收起、右缘 `#ai-companion-restore` 小药丸（✦ + hover 展开「AI Companion」）。隐藏态记 `localStorage calibre.ai.buddy.hidden`，跨页保持；点药丸 `buddy-appear` 反向 materialize 复原。
- **收信**：`#ai-companion-letter` 金边纸 + 火漆印从右上屏外飞入球心（`buddy-letter-fly`），落定后球轻 `buddy-peek` 一下，并落一个红色未读角标（`buddy-has-letter::before`），开抽屉即清。钩子＝`window.AICompanion.showLetter()` + 自定义事件 `mb:buddy-letter`，未来站内信有信时调用即可；伙伴已隐藏时不演飞信，只在唤回药丸上打角标（避免主体动画看不见却让用户以为没到信）。
- **复用仓内范式**：动效族沿用 R206 头像 keyframes / R223 气泡的 transform 分层（外圈 hover 缩放走 button、内圈动效走 img/子元素，互不打架）；未读角标是 R223 气泡 `is-playing` 同类的状态类。
- **i18n 零改动**：隐藏 ✕ 复用 `_('Close')`、唤回标签复用 `_('AI Companion')`，信封/角标纯图形 `aria-hidden`——不新增 msgid，故 i18n 种子/po/mo 与 `test_i18n_seed_contract` 全不动。
- **可访问性/降级**：`prefers-reduced-motion: reduce` 下五个新动画全关、信封 `display:none`；消失/复原除 `animationend` 外都挂 `BUDDY_ANIM_MS` 兜底超时，防 animationend 丢失导致球永久隐藏（fail-safe）。
- **测试**：新增 `tests/test_buddy_animations_r244.py` 6 条源码守卫（keyframes 齐 / reduced-motion 覆盖三个新状态类 / 信封基础态禁 `visibility:hidden`——实测踩过该坑 / 面板三元素齐 / JS 暴露 showLetter+事件+localStorage+兜底 / 不引入新 JS 词条）。开发态回归 `test_buddy_page`+`no_token`+`voice`+`ai_links`+`i18n_seed`+`reader_r226`+本套 = **48 passed**；全量 **1026 passed / 0 failed**。
- **视觉自检**：本机 headless Chrome 载真实 `ai_chat.css` 搭 mock，`--virtual-time-budget` 抓中间帧——✕ 显形、金光消散、金信封（静态帧确认本体样式）、唤回药丸+红角标均正确；mock 仅用于人眼核对，不入仓。
- **交付四问**：能力→用户可见（隐藏/唤回/收信提示），L1 `readme/companion.md` 待补一句；契约→无接口变化（未新增路由/端点）；实现/边界→本 LLD + 守卫注释；本次实现→`iterations/1.0/r244-buddy-animations/lld.md`。
- **台账与驻留**：`claim.sh magicbook` 占号 **R244**（`6462ab70`，纯台账）；worktree `../magicbook-r244-buddy-animations`（分支 `feat/r244-buddy-animations`）驻留待验收；**push 闸门留用户**。窗口：写入前 10 节，按「写入即检查」把最旧 R229 整节原样搬至 `response-archive/response-R229.md` 并登记索引，窗口回 10。冲突记录：无撞号；与 R243（站内信，仅占号未实现）是「动画层 vs 数据层」的分工，本轮只交动画钩子。

## 2026-10-28（R242：积分卡购买、兑换与管理员发卡入口）

### R242（用户：「我想增加一个积分兑换卡服务……也可以在积分页面买积分卡送人」）

- **交付**：积分页新增兑换框、三档购卡、已购卡密复制与管理员发卡面板。购卡复用既有支付宝二维码和轮询状态机，`orderType=CARD` 支付成功只生成一张卡，买家积分不变；按 `purchaseOrderNo` 定位并高亮新卡。
- **代理**：`cps/routes/credit.py` 新增九条 `/ajax/credit/card/*` 路由；用户端点登录保护，兑换与建单限流 10/min；五个管理员端点在代理层先 `role_admin()` 403，moon-well 白名单再校验。
- **安全**：本仓不保存卡密、不生成卡密、不计算价格；页面只显示文本与复制按钮，不渲染二维码/图片。复制优先 Clipboard API，失败回退 `execCommand('copy')` 并给可见错误。
- **管理员**：批量发卡默认 30 天，可设 1–3650 天或长期；批次列表、查看卡密、作废未使用卡、下载 `credit-cards-batch-<id>.txt` 全部接通。
- **i18n**：模板新增词条已补 `zh_Hans_CN/messages.po` 并只重编译中文 `messages.mo`；JS 动态文案直写中文；`CARD_REDEEM` 显示「积分卡兑换」。
- **测试与发布**：正式发布态全量 `1033 passed / 0 failed / 4 warnings`；`tests/test_credit_card.py + test_credit_consume.py` 23 passed、契约/i18n 11 passed，`node --check cps/static/js/credits.js` 与 `git diff --check` 通过。远端新增 R243 文档后合并为 `8e0efe95` 并 push `origin/develop`；fnOS 于 2026-10-29 09:41:54 返回 `deploy SUCCESS`、`build END OK (8e0efe95...)`。
- **文档四问**：L1 `readme/credit.md`、L2 `credit/interface.md`、L3 `credit/features/credit-card.md`、需求基线 `credit/requirements.md`、本次 HLD/LLD/AC 与迭代 `plan.md` 均已回填。
- **状态与驻留**：R242 已上线待验收。现网 `magicbook` 容器 `running/healthy`，`house.build-sha=8e0efe95...`；`/credits` 与卡密代理按预期重定向登录，生产的 `credits.js` 已包含兑换、购卡与管理导出接线。PingCode MB-233 保持 `In progress`；worktree `../magicbook-r242-credit-card`（分支 `feat/r242-credit-card`）保留待真机验收，验收后再清理。
- **验收缺陷修复（2026-10-29）**：用户反馈点击「购买并赠送」无感知。生产 DOM 实测订单已创建，但原收银台顶部位于 `1292px`、视口仅 `886px`，页面没有自动滚动，属于可见性缺陷而非接口失败。改为 Bootstrap 模态收银台：点击后按钮就地显示「正在创建订单...」，二维码生成后立即弹窗；建单失败会滚动到可见告警。首轮上线后发现页面全局样式使 Bootstrap 浮动栅格高度塌陷，正文溢出遮罩，已改用 Flex 双列布局。定向与契约回归 34 passed，`node --check`、`git diff --check` 通过。
- **弹窗发布验证（2026-10-29）**：修复提交 `12555764` 已 push `origin/develop`；fnOS 构建 `END OK`，app-manager `deploy SUCCESS`，容器 `running/healthy`，`house.build-sha=125557644f1047809304399fa166049ac51a703d`。生产页真实点击「购买并赠送」后弹窗正常打开，二维码 `200×200`、倒计时 `29:53` 启动、正文高度 `230px` 且无溢出，控制台无 error/warn。
- **窗口**：写入前 10 节，按「写入即检查」把最早 R229 整节原样搬至 `response-archive/response-R229.md` 并登记索引，窗口保持 10。
- **总结**：requests.md 条目 242 已从占位回填；本条为回应。冲突记录：无撞号。

## 2026-10-29（R241：整本能力缓存齐备标识——三项缓存都备齐时告诉读者「这本书学起来便宜」）

### R241（用户：「magicbook 增加一个功能，如果整本翻译，整本朗读，全文单词详解 都已经有缓存了，则每个都有一个特殊的标识，让用户知道这本书可以较为便宜的学习了。」）

- **任务定位**：需求（用户可见能力新增），单仓（magicbook）、moon-well 零改动、无新接口、无数据库迁移。
- **交付**：书籍详情页（含书卡点开的详情弹层）在难度标签之后给出缓存齐备信息——整本翻译 / 整本朗读 / 全文单词详解各一枚分项小标（哪项备齐亮哪项，悬停给出 `n/m` 与计费口径），三项齐备时追加「低成本学习」总标；整本任务面板的三个页签在对应缓存备齐时挂「已缓存」小标（同一份快照）。标识面向**普通读者**（`role_viewer()`），三个整本入口仍只给管理员（R214 拍板①不变）。
- **判定口径**：取本仓三条整本链路台账 `reading_translation_job` / `reading_tts_job` / `reading_word_detail_job`，要求 `status=COMPLETED` + 跑满（`completed_count/done_count/covered_words` 达到总量）+ `book_fingerprint` 与当前正文一致 + `book_format` 一致（SQL 侧 `lower()` 兜住大小写）；零上游调用、零 EPUB 解析。实现 `cps/reading_insight/readiness.py::book_readiness()`，`show_book` 注入 `entry.cache_readiness` 并复用速览 payload 已算好的指纹（不重复取书/stat）。
- **已知边界（已写入 LLD §3 / L3）**：① 不是实时探测，缓存被上游清掉会滞后；② 翻译与详解的 `COMPLETED` 依赖整本面板/批量进度页轮询时做缓存懒回收（R78 起不做常驻轮询），点完立刻关页面且之后不再打开的书会暂不亮标；③ 只认本仓发起过的整本批次；④ 归档书不亮标；⑤ 详解小标的计数是「本次补缺词数」，悬停改用全书去重词数表述。
- **测试**：新增 `tests/test_cache_readiness.py` **18 passed**（判定 15 条 + 面板真渲染 1 条 + 结构守卫 2 条）；定向回归 `test_book_detail_r214` / `r222` / `test_book_insight` / `test_i18n_seed_contract` / `test_job_service_base` / `test_reading_translation*` / `test_translate_all_r77` / `test_translate_concurrency_r78` / `test_word_detail_batch_r176` / `test_common_api_contract` 合计 **157 passed / 0 failed**。交叉审查（correctness reviewer）5 条发现已逐条处置：计数口径、归档书、重复取书/查询下推、大小写与未收敛边界补测。
- **文档**：LLD `docs/project/iterations/1.0/r241-cache-ready-badge/lld.md`（状态＝开发完成待验收）、L3 `docs/product/library/features/cache-ready-badge.md`（新建）、L1 `docs/product/readme/library.md`、需求基线 `docs/product/library/requirements.md` §R241、`docs/product/REQUIREMENTS.md` 变更记录、迭代 `plan.md`。
- **上线**：实现提交 `7d837dc8`，合并后 `f10d543d` 已推 `origin/develop`，fnOS 构建链自动部署（本次非纯文档 push）。**真机验收点**：找一本三项都跑满的书，详情页应出现「低成本学习」+ 三枚分项；只跑满一两项时只亮对应分项；普通读者账号可见、整本任务按钮仍仅管理员；从未跑过整本任务的书无标识且页面无报错。
- **worktree 驻留登记**：`../magicbook-r241-cache-ready-badge`（分支 `feat/r241-cache-ready-badge`，从 `origin/develop` 切出）按闸门保留待验收，验收通过后删除。
- **台账总结**：`requests.md` R241 已于开工时占号（`c16f1318`）；本条为 `response.md` 新增；同轮把最旧的 R230 一节原样搬入 `response-archive/response-R230.md` 维持 10 节窗口。

## 2026-10-29（R243：站内信前端——伙伴信封、抽屉 Mail、设置入口与独立收件箱）

### R243（用户：「伙伴来接受通知，有通知的时候伙伴头上会出现一个信封，用户点击伙伴可以收信。有个专门的【邮件】（站内信）功能。」）

**对 R243 的回应**：前端已完成，与 moon-well R228 后端组成完整的**伙伴邮差 + 持久站内信**链路；当前整体处于**待用户验收**，未 push、未部署。

- **代理与契约**：新增 `cps/routes/mail.py` 四条 `/ajax/mail/*` 薄代理，统一登录门禁并保持 `_moonwell_proxy` 三元组；`pageNo/pageSize` 本地归一，`read` 只透传正整数 id，不接收或猜测 `userId`。管理员积分代理透传 `notify` 与 `notificationMessage`，既有字段不变。
- **统一状态层**：`MBMail` 作为 FAB、设置菜单、抽屉页签和 `/mail` 的唯一未读来源，支持初始化、页面可见、窗口聚焦、打开 Mail 页签与 `pageshow` 刷新，不设 `setInterval`。数字 badge 只在成功取得计数时展示；列表加载失败只影响列表局部，保留最近一次成功未读供 FAB 信封判断，不把全局状态误降级为空。
- **伙伴与抽屉**：Buddy FAB 增加 `pointer-events:none` 信封角标，不另盖点击层；抽屉关闭时有未读进 Mail、无未读进 Chat，抽屉已打开仍按原行为关闭；“对话”快捷气泡始终显式进 Chat。AI 抽屉新增 Chat/Mail 双页签，Mail 展示最近 5 封，展开单封才已读，提供全部已读与“查看全部”，打开页签本身不标已读。
- **独立邮件页**：新增登录保护的 `/mail`，倒序分页、单封展开/已读、全部已读、空态、加载态、错误态与重试；正文按结构化参数本地化，服务端字符串只作文本节点，不拼 `innerHTML`；跳转严格限定 `/buddy`、`/achievements`、`/credits`。已解决邮件保留历史但不计未读。
- **设置与管理员**：设置菜单新增 `top_mail` 与未读 badge；积分管理员表单新增“同时发送到账通知”和可选纯文本正文，负数时禁用并清空，成功后与 FAB/设置/抽屉同步计数。`layout`、`read`、`readtxt`、`readpdf` 均已接入；`readcbr` 当前未挂 Buddy 面板，本轮明确不扩展。
- **验证**：合并前邮件/积分/API/i18n/Buddy/阅读器两批定向回归合计 **172 passed / 0 failed**；合并 R244 后重跑 **137 passed / 0 failed**，另 R233 链接/阅读器结构 **19 passed**（均含 2 条既有 warning）。`node --check cps/static/js/mail.js`、`ai_chat.js`、`credits.js` 与 `git diff --check` 均通过。moon-well R228 后端定向 **81 tests** 全绿。
- **文档四问**：能力 → `docs/product/readme/companion.md`；契约 → `docs/product/companion/interface.md`；实现/边界 → `docs/product/companion/features/mail-inbox.md`；本次实现 → `docs/project/iterations/1.0/r243-mail-inbox/`（HLD/LLD/AC 已回填“前后端已实现，待验收”）。
- **R244 语义合并**：再次合并 `origin/develop` 时吸收 R242 收银台和 R244 伙伴隐藏/收信动画。`ai_chat_panel.html` 同时保留 R243 信封/页签与 R244 隐藏、唤回、飞信节点；`ai_chat.js` 的 `openDrawer(tab)` 保留 R243 页签分流并清理 R244 一次性角标；`credits.js` 同时保留 R243 i18n 与 R242 滚动提示。R243/R244 交界采用“同一未读、按可见性映射”：可见 FAB 只显示 R243 信封，伙伴隐藏后显示唤回药丸红点，避免重复提示；信封移到左上避让右上隐藏 ✕。详见 R243 LLD §4.4。
- **状态与驻留**：worktree `../magicbook-r243-mail-inbox`，分支 `feat/r243-mail-inbox`；实现 `82688cd2`、列表失败隔离修复 `78581165`、前次基线合并 `bf4b6e1a`、R244 合并 `a241f287`。按验收闸门保留 worktree，**未 push、未部署**；部署顺序 moon-well R228 先、本仓 R243 后。
- **窗口与总结**：本条写入时窗口 10 节；合并 R244 后增至 11，按「写入即检查」把最旧 R232 原样搬至 `response-archive/response-R232.md`，窗口恢复 10，并合并 R229/R231 的并行重复索引。requests.md 条目 243 已回填；冲突记录：无撞号，magicbook R228 为另一条既有需求，与本功能无关。
