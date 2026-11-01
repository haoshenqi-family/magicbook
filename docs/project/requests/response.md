# 对话回应记录

> 含每个需求的回应、冲突说明及两个文件的总结。
> **归档规则**：本文件仅保留最近 10 个 request 的回应；更早内容原样归档至 `response-archive/`（按 request 区间分文件），需要历史细节时按编号检索归档目录，不要读全量历史。

**归档索引**

- `response-archive/response-R251.md`：R251（MagicBook UI 信息架构、导航分组与账号/管理 L2 拆页）——2026-11-01 R265 写入触发轮转搬移，原样搬移不改写
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
- `response-archive/response-R230.md`：R230 个人学习数据导出入口与任务下载 UI——2026-10-29 R241 写入使窗口达 11 节，原样搬移不改写；R247 轮转把原误置于 R234 后的 R230 验收清理段归回本节
- `response-archive/response-R232.md`：R232 伴读面板不再显示 token 用量——2026-10-29 R243 合并 R244 后窗口达 11 节，原样搬移不改写
- `response-archive/response-R233.md`：R233 AI 回复中的本站链接可点击并在新窗口打开——2026-10-29 R246 写入使窗口达 11 节，原样搬移不改写
- `response-archive/response-R234.md`：R234 悬浮球快捷动作 AI 对话恒首位——2026-10-29 R247 写入使窗口达 11 节，原样搬移不改写
- `response-archive/response-R236.md`：R236 弹层恢复「整本任务」入口——跳完整详情页的普通链接（2026-10-29 R248 写入触发轮转搬移，原样搬移不改写）。
- `response-archive/response-R237.md`：R237 整本朗读 proxy 三元组解包 + 白屏修复与部署重启后的「继续」恢复入口——2026-10-29 R249 写入触发轮转搬移，原样搬移不改写。
- `response-archive/response-R238.md`：R238 全文单词详解预览卡死——所有书共有的 jQuery 顺序缺陷 + 后台预计算（2026-10-29 R250 / R252 并行写入均轮转到本节，保留单份，原样搬移不改写）。
- `response-archive/response-R239.md`：R239 全文单词详解预览屈折词覆盖漏算（2026-10-29 R250 / R252 合并后窗口达 11 节，原样搬移不改写）。
- `response-archive/response-R244.md`：R244 伙伴动效——隐藏消失动画（金光消散）+ 收信动画（站内信预留钩子，纯 CSS）（2026-10-29 R250 / R252 合并后窗口达 11 节，原样搬移不改写）。
- `response-archive/response-R242.md`：R242 积分卡购买、兑换与管理员发卡入口（2026-10-29 R251 写入触发轮转搬移，原样搬移不改写）。
- `response-archive/response-R241.md`：R241 整本能力缓存齐备标识（2026-10-29 R245 写入触发轮转搬移，原样搬移不改写）。
- `response-archive/response-R243.md`：R243 站内信前端——伙伴信封、抽屉 Mail、设置入口与独立收件箱（2026-10-29 R254 写入触发轮转搬移，原样搬移不改写）。
- `response-archive/response-R245.md`：R245 积分页分区、充值活动 400 与明细可读性（2026-10-29 R255 写入触发轮转搬移，原样搬移不改写）。
- `response-archive/response-R246.md`：R246 整本进度标签——任务详情页进度文案仅保留整本口径（2026-10-30 R256 写入触发轮转搬移，原样搬移不改写）。
- `response-archive/response-R247.md`：R247 归档洞察（2026-10-31 R257 写入触发轮转搬移，原样搬移不改写）。
- `response-archive/response-R248.md`：R248 整本任务进度条只在书籍详情页显示——2026-10-31 R259 写入触发轮转搬移，原样搬移不改写
- `response-archive/response-R248.md`：R248 整本进度仅留详情（2026-10-31 R258 写入触发轮转搬移，原样搬移不改写）。
- `response-archive/response-R249-R250.md`：R249 整本朗读后台线程共享会话崩溃 + R250 管理员运营站内信（2026-10-31 R260 写入触发轮转搬移，原样搬移不改写）。
- `response-archive/response-R252.md`：R252（2026-10-29）——2026-11-01 R261 写入触发轮转搬移，原样搬移不改写

---

> 归档索引：[response-R01-R31.md](response-archive/response-R01-R31.md) · [response-R32-R49.md](response-archive/response-R32-R49.md) · [response-R50.md](response-archive/response-R50.md) · [response-R51-R70.md](response-archive/response-R51-R70.md) · [response-R70-R80.md](response-archive/response-R70-R80.md) · [response-R81-R101.md](response-archive/response-R81-R101.md) · [response-R102-R110.md](response-archive/response-R102-R110.md) · [response-R111-R119.md](response-archive/response-R111-R119.md)（2026-10-08 R129 补账搬移）· [response-R120-R125.md](response-archive/response-R120-R125.md)（2026-10-08 R135 写入触发搬移，含 R134 登记的窗口欠账补账）· [response-R126-R131.md](response-archive/response-R126-R131.md)（2026-10-09 R141 写入触发轮转搬移）· [response-R132-R133.md](response-archive/response-R132-R133.md)（2026-10-10 R143 写入触发轮转搬移） · [response-R134.md](response-archive/response-R134.md)（2026-10-10 R144 写入触发轮转搬移） · [response-R135-R137.md](response-archive/response-R135-R137.md)（2026-10-10 R147 写入触发轮转搬移，含 R145/R146 两次写入的窗口欠账补账） · [response-R138.md](response-archive/response-R138.md)（2026-10-11 R152 写入触发轮转搬移） · [response-R139.md](response-archive/response-R139.md)（2026-10-11 R153 写入触发轮转搬移） · [response-R140.md](response-archive/response-R140.md)（2026-10-11 R153 复核后的补搬——R152 写入时搬走 R138 后窗口仍为 11） · [response-R141-R142.md](response-archive/response-R141-R142.md)（2026-10-11 R155 集成时窗口超限搬移） · [response-R144-R153.md](response-archive/response-R144-R153.md)（2026-10-12 R161 写入触发轮转搬移，清并行欠账 R144–R153） · [response-R154.md](response-archive/response-R154.md)（2026-10-12 R165 写入触发轮转搬移） · [response-R155-R156.md](response-archive/response-R155-R156.md)（2026-10-13 R166 写入触发轮转搬移，含同日同编号「细筛」那条） · [response-R157.md](response-archive/response-R157.md)（2026-10-13 R166 分支 merge origin/develop 后窗口仍达 11，续搬最旧一节） · [response-R156-mic.md](response-archive/response-R156-mic.md) · [response-R158.md](response-archive/response-R158.md)（2026-10-13 R168 写入触发轮转搬移）（2026-10-13 R167 写入触发轮转搬移；与 response-R155-R156.md 里的同编号「细筛」条目不同事） · [response-R160-R164.md](response-archive/response-R160-R164.md)（2026-10-14 R172 写入触发轮转搬移，窗口转入 R161 起） · [response-R161-R162.md](response-archive/response-R161-R162.md)（2026-10-14 R173 写入触发轮转搬移，窗口转入 R165 起） · [response-R165-R173.md](response-archive/response-R165-R173.md)（2026-10-15 R183 写入触发轮转搬移，窗口转入 R174 起） · [response-R174-R177.md](response-archive/response-R174-R177.md)（2026-10-16 R185 写入触发轮转搬移，窗口转入 R178 起） · [response-R175.md](response-archive/response-R175.md)（2026-10-16 R188 写入触发轮转搬移） · [response-R214-C.md](response-archive/response-R214-C.md)（2026-10-25 R229 写入触发轮转搬移：R214 子项 C 整本任务代价面板；与既有 response-R214.md（子项 A）不同事） · [response-R238.md](response-archive/response-R238.md)（2026-10-29 R250 / R252 并行写入轮转，原样搬移不改写） · [response-R239.md](response-archive/response-R239.md)（2026-10-29 R250 / R252 合并后窗口达 11 节轮转） · [response-R244.md](response-archive/response-R244.md)（2026-10-29 R250 / R252 合并后窗口达 11 节轮转） · [response-R243.md](response-archive/response-R243.md)（2026-10-29 R254 写入触发轮转搬移） · [response-R246.md](response-archive/response-R246.md)（2026-10-30 R256 写入触发轮转搬移） · [response-R247.md](response-archive/response-R247.md)（2026-10-31 R257 写入触发轮转搬移） · [response-R248.md](response-archive/response-R248.md)（2026-10-31 R258 写入触发轮转搬移） · [response-R253.md](response-archive/response-R253.md)（2026-11-01 R263 写入触发轮转搬移）





## 2026-10-29（R254：伙伴邮件弹层与 AI 对话抽屉分离）

### R254（用户：「邮件不要出现在AI伴读对话框中。当新邮件到达的时候，点击伙伴弹框显示邮件而不是跟AI伴读公用一个弹框」）

**对 R254 的回应**：已完成并上线。邮件已从 AI 对话抽屉彻底拆为独立伙伴邮件弹层；有未读时点击伙伴进邮件，无未读时进 AI 对话，两个浮层互斥。

- **结构拆分**：`ai_chat_panel.html` 删除 `#ai-companion-tabs`、`#ai-tab-chat`、`#ai-tab-mail`、`#ai-mail-pane` 与抽屉内邮件骨架；AI 抽屉只保留 `#ai-chat-pane`、会话工具与记忆面板。登录态新增独立 `#buddy-mail-popover`（`role=dialog`），含关闭、未读数、全部已读、加载/空/错误/列表与“查看全部”。
- **FAB 路由**：纯函数 `chooseFabTarget(panelOpen, unread)` 保持可执行守卫；无浮层且有未读时 `openBuddyMail()`，无未读时 `openDrawer()`，任一浮层已开时再点 FAB 关闭当前浮层。快捷气泡“对话”仍直接 `openDrawer("chat")`，不复用 FAB 分流。
- **互斥与邮件事务**：`openBuddyMail()` 先关 AI 抽屉，`openDrawer()` 先关邮件弹层；打开弹层只拉最近 5 封，不标已读，展开单封才调用 `MBMail.markRead(id)`；“全部已读”复用 `MBMail.markAllRead()` 并刷新本地预览。设置入口、完整 `/mail`、FAB 信封、伙伴隐藏唤回提示与统一 `MBMail` 未读状态全部保留。
- **视觉与可达性**：桌面为右下独立浮层（宽 `min(420px, calc(100vw - 48px))`，底部给 FAB 留位），移动端 ≤600px 全屏；关闭与全部已读触控目标 ≥44px，列表内部滚动，`[hidden]` 强制隐藏，未新增动画或第二套状态。用真实登录态模板生成本地 Chromium 快照，桌面与移动布局均通过目检。
- **文档四问**：能力 → `docs/product/readme/companion.md`；契约 → `docs/product/companion/interface.md`；实现/边界 → `docs/product/companion/features/mail-inbox.md` 与 `admin-mail.md`；本次实现 → 新建 `docs/project/iterations/1.0/r254-buddy-mail-popover/`（LLD/AC）。需求基线新增 R254，R243 的“双页签抽屉”与 R250 的“抽屉 Mail”历史正文只加被取代/展示注记，不改写原文。
- **验证**：邮件 UI、邮件代理、管理员发信、伙伴动效、i18n、账号 IA、首页壳与 API 契约定向 **138 passed / 0 failed / 2 warnings**；正式发布态全量 **1203 passed / 0 failed / 4 warnings**。`node --check cps/static/js/ai_chat.js`、`mail.js` 与 `git diff --check` 通过；模板/JS 守卫覆盖匿名不渲染、有未读进邮件、无未读进对话、快捷气泡直达 Chat、浮层互斥、打开弹层不标已读、展开单封才已读。
- **上线**：实现提交 `96a756114232d7f1e4e535724549c081cea6a122` 已推送 `origin/develop`（`d7933131..96a75611`）；fnOS `build END OK (96a756114232d7f1e4e535724549c081cea6a122)`，app-manager `deploy SUCCESS`，容器 `running/healthy` 且 `house.build-sha=96a756114232d7f1e4e535724549c081cea6a122`。生产 `/login` 200，匿名 `/buddy` 302 到 `/login?next=%2Fbuddy`。
- **状态与驻留**：**已上线待验收**。worktree `../magicbook-r254-buddy-mail-popover`，分支 `fix/r254-buddy-mail-popover`，实现与部署提交 `96a75611`；按闸门保留待用户验收，验收通过后再清理。
- **窗口与总结**：写入前窗口 10 节，新增后 11；按「写入即检查」把最早 R243 整节原样搬至 `response-archive/response-R243.md` 并在两处归档索引登记，窗口恢复 10。requests.md 条目 254 已从占位回填；冲突记录：无撞号，本轮不改 moon-well 契约。

## 2026-10-29（R255：注销后 remember_token 未清除，用户被自动登回）

### R255（用户 sunny：「接口401 注销功能失效，无法正确注销」；补充：「资料与身份可以正常显示用户名和邮箱 authentik 正常登录」）

- **结论先行**：注销链路确实失效，但根因不是 Authentik、不是账号资料，也不在 moon-well；是本站 R123 会话持久化改动引入的 cookie 清理顺序回归。
- **复现路径**：OIDC 登录（`login_user(user, remember=True)`）→ 点击顶栏「注销」→ 到 `/login` 后被自动 302 回首页，仍是原账号。服务端会话记录已删、session cookie 已删，所以从接口看会伴随一次 401；但 `remember_token` 没删，下一次请求立刻把用户登回来。
- **根因**：`cps/web.py::logout()` 先 `logout_user()` 再 `flask_session.clear()`。`cw_login.logout_user()` 靠 session 里的 `_remember="clear"` 通知 `after_request` 删除 `remember_token`，而 `clear()` 把这个标记一起清掉了；cookie 仍在，`_load_user()` 从 remember cookie 恢复用户并 `confirm_login()`。
- **修复**：调整顺序为「删除服务端 user_session → `flask_session.clear()` → `logout_user()`」。moonwell access/refresh token 仍被清空，R123 的安全目标不变；`logout_user()` 重新写入 clear 标记，`remember_token` 随响应删除。
- **测试**：`tests/test_session_permanent.py` 的登录 fixture 改为带 `remember_me`，新增断言：注销响应必须删除 `remember_token`、后续 `GET /login` 必须 200 而不是 302。修复前红灯（`remember_del == []`），修复后 4 passed；再跑 OIDC 相关 `test_oidc.py`、`test_oidc_admin_role.py`、`test_login_invite_link.py`、`test_oidc_signup.py` 共 52 passed / 0 failed。
- **文档四问**：能力 → 无变化（恢复「注销能退出」的既定能力）；契约 → 无变化；实现/边界 → 新建 L3 `docs/product/admin/features/session-logout.md`；本次实现 → `docs/project/iterations/1.0/r255-logout-remember/lld.md`。
- **边界（需拍板）**：本站注销只结束 magicbook 会话，不结束 `account.haoshenqi.top` 的 SSO 会话；注销后若再点「Log in」，Authentik 仍会静默授权。若用户期望「注销 = 连统一账号中心一起退出」，需要另立需求做 RP-initiated logout（`end_session_endpoint` + `id_token_hint`），这会影响四个应用，不能夹在本次缺陷修复里擅自改。
- **上线**：merge/push `81356579` 已进 `origin/develop`；fnOS 镜像 `house.build-sha=81356579e064a820238ef41fbe9eabd3698c04e3`，容器 `running/healthy`（2026-10-29T23:25:23+08:00）；容器内 `/app/cps/web.py` 已确认是新顺序。
- **状态与驻留**：已上线待验收。worktree `../magicbook-r255-logout-remember`（分支 `fix/r255-logout-remember`）按闸门保留；验收通过后再删除。
- **窗口与总结**：写入前 10 节，新增后 11 节；按「写入即检查」把最旧 R245 整节原样搬至 `response-archive/response-R245.md` 并登记索引，窗口恢复 10。requests.md 条目 255 已从占位回填；冲突记录：无撞号。

## 2026-10-30（R256：黑盒体验报告四项缺陷——OIDC 建号侧栏位/空书架/已读歧义/实体解码）

### R256（用户全流程指令：黑盒测试 magicbook → 体验报告 → 设计方案 → 修复缺陷）

- **结论先行**：新用户临时账号（mbtester1030）全功能遍历产出体验报告（4 Bug+9 疑惑点+10 设计不合理）；本轮修复其中 4 项有代码级根因且可测的缺陷。
- **根因与修复**：B1 OIDC 建号漏设 sidebar_view（列默认值 1 只含 DETAIL_RANDOM 位），浏览路由 check_visibility 位缺失 abort(404)——修法=收拢 `oidc.create_oidc_user`（角色/语言/侧栏位一次取齐，侧栏位取 config_default_show 与本地注册同口径），生产实验已闭环验证因果（恢复 262143 后 /author 立即 200，2 分钟复查无改写者）。B2 create_edit_shelf 补空标题校验（flash+redirect）。B4 详情页阅读状态开关 label 弃用 msgid "Read" 改 Reading status（po/mo 同步「阅读状态」），msgid "Read" 原译保留给筛选器场景。B5 learning-common.js 新增 decodeHtmlEntities，loadMaterials 的 title/author 进 textContent 前解码（听写/复述/重读共用）。
- **修复范围裁决**：B3（删除书架 div 按钮无反应——main.js:787 绑定存在）/B6（听写载入段落无响应）在自动化环境无法证伪，报告存疑待真机复核，本轮不修。九项疑惑点的设计方案（专名误判黄金区、生词本入口、管理员文案分离等）在 `magicbook-产品设计方案-2026-10-30.md`，未夹带开发。
- **测试**：新增 `tests/test_newuser_sidebar404_r256.py` 10 用例（建号位组合/九浏览位覆盖/config 未初始化/helper 三项取齐/空标题参数化+正常对照/po+mo 双侧/JS 解码契约）；`TestCallbackContract` 2 用例随收拢结构演进（意图不变）。定向回归：oidc 全家+home/shell+detail+advsearch+i18n 契约+learning 三件套全绿（最后一批 33 passed）。
- **文档四问**：能力→无变化；契约→无变化；实现/边界→`docs/project/iterations/1.0/r256-newuser-sidebar404/lld.md`；本次实现→同 LLD。**存量数据修复 SQL 在 LLD §2.1**（上线后需在 fnOS 执行一次：sidebar_view=1 的存量 OIDC 用户回填 config_default_show）。
- **状态与驻留**：**已 merge 待 push/待验收**。主检出 develop `c3badf9e`（含占号 db3f445f）；worktree `../magicbook-r256-newuser-sidebar404`（分支 `fix/r256-newuser-sidebar404`）按闸门保留。push 触发 fnOS 自动部署+存量 SQL 待执行，本轮按「外向动作先确认」等用户拍板后再推。
- **窗口与总结**：写入前 10 节，新增后 11；按「写入即检查」把最旧一节（R246）原样搬至 `response-archive/response-R246.md` 并登记索引，窗口恢复 10。冲突记录：无撞号。

## 2026-10-31（R257：按产品设计方案实施七个可落地项）

### R257（用户拍板「按照设计方案修复」）

- **结论先行**：设计方案十个方案按文档自身 ⚡/🏗 标记与「不做什么」原则裁剪——本轮实施一/三/四/六/七/八/九，二/五/十（跨仓生词判定/充值卡重排/已读数据诊断）登记待拍板，未夹带。
- **实现要点**：①render_template 删除非管理员 Downloaded Books else 分支（books_list download 页双门槛必 404）；②review 空态改排程解释+测试结果旁直达复习队列（vt-notebook-link-row）；③detail 下载/阅读两处权限提示去「Users → Edit User」后台路径；④credits.js 三处 t() + buddy.js 稀有度字面量映射 + seed 脚本自动/手动补 7 词条 + po 8 条；语言菜单收敛（常用三项+当前语言直出、其余折叠、完整列表留 /me）；⑤index.html 移除难度横幅 include（模板保留）；⑥update_preferences 分场景 flash+next 白名单（防 openredirect）；⑦删除书架 div→button（form 内显式 type）+侧栏/详情页空名兜底「未命名书架」。
- **认知修正**：体验报告 B3「删除书架无反应」系自动化环境假阴性——main.js confirmDialog 确认流程原本存在；本轮仅做语义修复。
- **测试**：新增 test_design_plan_r257.py 20 用例；契约演进 4 处（横幅移除/权限文案 ×2/R212 locale 钉到 create_oidc_user——R212 文件系 R256 收尾漏跑，本轮全量暴露后一并钉住）。全量回归 **1228 passed / 0 failed**（跳过 test_ai_agent_proxy 网络依赖与 slow）。
- **文档四问**：能力→readme 随验收回填；契约→/me/preferences 新增可选 next 字段（站内白名单）；实现/边界→`docs/project/iterations/1.0/r257-design-plan-fixes/lld.md`。
- **状态与驻留**：**已 merge 待 push/待验收**。develop `5e03f189`；worktree `../magicbook-r257-design-plan-fixes`（分支 `feat/r257-design-plan-fixes`）按闸门保留；push 触发 fnOS 部署，等用户拍板。
- **窗口与总结**：写入后 11 节，按「写入即检查」把最旧一节（R247）原样搬至 `response-archive/response-R247.md` 并登记索引，窗口恢复 10。冲突记录：无撞号。

## 2026-10-31（R259：设置页生词提示语对齐 moon-well R232 新口径——「该等级及以上」）

### R259（承接 moon-well R232；用户原话「判定逻辑改为大于等于，当前用户的难度等级+1……」）

- **结论先行**：moon-well R232 把生词判定兜底改为「词档 ≥ 用户档位」（档位=学习目标线）并做存量档位 +1 迁移。本仓零判定逻辑改动，只同步用户可见表述：设置页提示语从「高于该等级的词会被标记为生词」改为「该等级及以上的词会被标记为生词」，消除文案与行为的漂移（数值同源纪律）。
- **实现**：`cps/templates/reading_settings.html:46` msgid 改「Words at or above this level are marked as unknown while reading. Default: CET4.」；`cps/translations/zh_Hans_CN/LC_MESSAGES/messages.po` 同步 msgid + msgstr「阅读时该等级及以上的词会被标记为生词。默认：CET4。」；`pybabel compile` 重建 messages.mo（运行时读 .mo，不编译则中文不生效）。其余 27 个 locale 无此条翻译，走英文源文回退（源文已正确表达新语义）。
- **文档**：L1 `docs/product/readme/vocabulary.md` 档位句补「档位代表你正在学的目标水平：该档及以上的词默认判为生词」；需求基线 `vocabulary/requirements.md` 变更记录加 R259 行。判定矩阵权威仍在 moon-well `docs/product/vocabulary/interface.md`（R232 已更新）。
- **测试**：定向 `test_nav_settings_dropdown.py + test_i18n_seed_contract.py + test_me_preferences.py + test_common_api_contract.py` 共 **28 passed**（i18n 种子契约与设置页回归均绿）；旧 msgid 全仓 grep 归零。
- **状态与驻留**：**已 merge 待验收**。worktree `../magicbook-r259-judge-tooltip`（分支 `feat/r259-judge-tooltip`）按闸门保留待验收；验收通过后删除。跨仓主线：moon-well R232（判定翻转 + 迁移 SQL，SQL 执行前线上行为与改前一致）。
- **窗口与总结**：写入前 10 节，写入后 11 节；按「写入即检查」把最旧一节（R248）原样搬至 `response-archive/response-R248.md` 并登记索引，窗口恢复 10。requests.md 条目 259 已从占位回填。冲突记录：无撞号。
## 2026-10-31（R258：设计方案五充值卡五段式 + 方案十已读三态口径）

### R258（用户拍板「方案五按照你的设计修改。方案十按你的设计开始」；方案二提问已答复）

- **方案五**：moon-well 套餐字段已结构化（credits/baseCredits/multiplier/price/promotionEndTimeEpochMs），renderPackages 纯前端重排五段式：价格大字→所得构成（内测 N 倍 = 基础额度，说人话）→活动倒计时→单一中文主按钮→单价辅助行（≈ 每万积分 ¥x，不足一万的测试档不显示）。formatCredits 口语化（≥1万→x 万积分）；pkg-name/pkg-base 独立行退场，R242 契约同步演进。
- **方案十（诊断+修正）**：生产 book_read_link 无脏数据（mbtester1031 零记录=「未读」口径成立；hsq/sunny 状态均为真实痕迹）——B4 确认系 R256 已修的 label 歧义，**无需数据修复**。诊断发现的真缺口：show_book 把三态压成布尔，「在读」（阅读器入口写 IN_PROGRESS，生产 10 本在状态）在详情页与未读无差别——修正为三态透出 + 「在读」label-info 标签；高级搜索三态同源不受影响；listenmp3 同款 checkbox 挂在无 read_status 的 entry 上属历史死状态，不夹带。
- **方案二（答复存档）**：专名判定四层过滤（形态统计/高频词表 top50k/Calibre 元数据强排除/LLM 批量复核兜底），不采用 spaCy NER 主路径；落点 R147 密度估算 tokenize（moon-well 侧），实施待拍板（LLD §3）。
- **测试**：新增 test_plan5_plan10_r258.py 9 用例；R242 契约演进 1 处。全量 **1237 passed / 0 failed**。
- **文档四问**：能力→credit L1 随验收回填；契约→无；实现/边界→`docs/project/iterations/1.0/r258-plan5-plan10/lld.md`。
- **状态与驻留**：**已 merge 待 push/待验收**。develop `d34c6968`；worktree `../magicbook-r258-plan5-plan10`（分支 `feat/r258-plan5-plan10`）保留；push 待用户拍板。
- **窗口与总结**：写入后 11 节，按「写入即检查」把最旧一节（R248）原样搬至 `response-archive/response-R248.md` 并登记索引，窗口恢复 10。冲突记录：无撞号。

## 2026-10-31（R260：AI 了解我——用户自我介绍与系统提示词注入）

### R260（用户：「AI应该了解用户才能更好的跟他聊天，帮助他。AI伴读那里增加一个用户填写自我介绍的部分，并把这部分内容放到系统提示词里。」）

- **结论先行**：已在 AI 伴读记忆面板顶部增加「AI 了解我」，保存后由 moon-well 在书内与网页伴读的每次问答中注入系统提示词。用户主动声明的背景与 AI 自动抽取的长期记忆保持分层，互不覆盖；当前状态为**已上线待验收**。
- **后端（moon-well R234）**：新增 `ai_user_profile`，每用户一行、上限 2000 字符、清空即删行；`POST /ai/agent/profile` 读取、`POST /ai/agent/profile/save` 保存，身份只取 `UserContext`，统一返回显式 `Result` 包装。`/ai/agent/profile*` 整路径排除 HTTP 请求/响应日志。
- **提示词注入**：两套默认模板、Nacos 在线模板与渲染异常兜底路径均支持 `{{userProfile}}`。先补伙伴名、最后回填用户正文，防止正文中的伙伴名压掉名称段；用户正文中的 `{{memory}}` 等变量保持字面值，`& < >` 转义后放入 `<user_profile>`，并声明其不能改变角色、权限、工具或安全规则。空档案不留下空标题，旧在线模板缺段时安全补注一次。
- **前端（magicbook R260）**：记忆面板支持加载、编辑、实时 2000 字计数、保存、二次确认清空以及加载/保存/清空错误态；新增两条薄代理连接 moon-well。用户文本只用 `.val()` 渲染，不拼 HTML；固定提示不要填写密码、密钥、证件号等敏感信息。新文案已进入 i18n seed、中文 `.po` 与编译后的 `.mo`。
- **测试**：后端 5 类定向回归 **49 tests / 0 failures / 0 errors / 0 skipped / BUILD SUCCESS**（JDK 25.0.2），正式发布态全量 **1715 tests / 0 failures / 0 errors / 0 skipped / BUILD SUCCESS**；前端 `test_ai_agent_proxy.py` + `test_ai_user_profile_r260.py` **14 passed**，正式发布态全量 **1251 passed / 0 failed / 4 warnings**，`node --check cps/static/js/ai_chat.js` 通过。
- **测试环境**：按用户最终确认口径从 fnOS `/app/moon-well/.env` 取得依赖环境，MinIO 使用群晖 `http://192.168.31.10:9000`；本轮功能测试不实际读写 MinIO，该地址与现网 `.env` 和 `/ops` 一致。
- **文档四问**：能力 → `docs/product/readme/companion.md`；契约 → `docs/product/companion/interface.md`；实现/边界 → 新建 `docs/product/companion/features/user-profile.md`；本次实现 → `docs/project/iterations/1.0/r260-ai-user-profile/lld.md` 与迭代 `plan.md`。后续结构化档案与 AI 摘要方案记录在 LLD §8，不阻塞本轮首版。
- **上线**：已按 moon-well 代码 → magicbook 代码 → Nacos 提示词的顺序完成。moon-well `dd471fc8ad4234d49fd0a6acf0015a387f349dbf` 与 magicbook `7b96323e2f5ce04d7d06bbffb41b42e829b61862` 均已推 `origin/develop`；两仓 fnOS 构建均 `END OK`、部署 `SUCCESS`，moon-well 蓝绿切到 `moon-well-blue`、magicbook 容器 `running/healthy`。moon-well 镜像 `house.code-digest=5d04b43e275e5f44`，magicbook 镜像 `house.code-digest=92f502a325ca3318`。
- **Nacos / MinIO**：`agent-chat-system` 与 `agent-chat-system-web` 均从 `1.2.0` 发布到 `1.3.0`，逐字预检与回读 PASS，字符数分别为 917 / 943；Nacos 审批流水线返回 20002 时按脚本既定逻辑回落 `force-publish`。MinIO 保持群晖 `192.168.31.10:9000`，未改生产 `.env`；下一轮结构化档案 + AI 摘要优化本轮不做。
- **状态与驻留**：两仓均为**已上线待验收**。PingCode Ship 需求 `MB-237`、PJM 用户故事 `MB-22` 均为进行中，待验收通过后流转完成。moon-well worktree `../moon-well-r234-ai-user-profile`，分支 `feat/r234-ai-user-profile`；magicbook worktree `../magicbook-r260-ai-user-profile`，分支 `feat/r260-ai-user-profile`，按闸门保留。
- **窗口与总结**：写入前 `response.md` 为 11 节；按「写入即检查」把最早 R249、R250 两节原样搬至 `response-archive/response-R249-R250.md` 并登记索引，新增 R260 后恢复 10 节。requests.md 条目 260 已从占位回填；本条为回应，冲突记录已并入上面的 MinIO 环境项。

## R261 · Jinshu 借鉴三件套：行内生词释义/Book Fit 话术/复习小件（2026-11-01）

### R261（用户：Jinshu 调研后拍板「gloss 做成可选功能默认不启用；纠错上报不做我们有 AI；Book Fit 话术借鉴；复习 UX 小件做到学习模块默认不开启；墨水屏不做」）

- **结论先行**：三项全部实现并开发态全绿，待验收。A=阅读器行内小字释义（设置弹窗开关 localStorage 默认关，`markVocabulary` 双守卫挂 `data-gloss`，READER_TOOLS_STYLE 注入 iframe 的 `::after` attr 渲染不占文档流，切换 `ReaderVocabGloss.remark` 缓存重标零新请求；数据接 moon-well R236 analyze `gloss`）；B=选书页「~N 个重复出现的超纲词」行（`repeatedUnknownCount` null 容错隐藏）+ 样例词放宽 正合适/挑战读；C=学习抽屉「复习小件」两开关（复习卡来源书 chip 只亮书名 / 学习入口待复习角标镜像判关零请求）。
- **测试**：新增 `test_r261_jinshu_borrow.py` 8 条静态锁；开发态合计 230 passed（i18n 契约 5 + learning 五件 160 + reading_vocabulary/lens_handoff/learning_story 62），改动 JS `node --check` 全过。
- **i18n**：五步链全走，6 新词条（模板 4 + JS 2）入种子/zh po/mo；`generate_i18n_seed.py` 重跑（JS 清单 26 文件、msgid_count 494→517，顺带治愈 develop 漂移）。
- **文档四问**：能力→`readme/reading.md`（行内小字释义）+`readme/learning.md`（复习小件/Book Fit 话术/chip）；契约→`reading-vocabulary.md`（analyze 响应结构 R139 后再更新：+gloss）；实现/边界与本次实现→`project/iterations/2026-11-jinshu-borrow/lld.md`（状态：已开发待验收）。requirements 基线落 `learning/requirements.md`（含两项不做决策）。
- **PingCode**：idea `MB-238`（进行中）。后端 moon-well R236（LLD/SQL/基线权威在那边）。
- **状态与驻留**：开发完成待 merge/验收。worktree `../magicbook-r261-jinshu-borrow`（分支 `feat/r261-jinshu-borrow` @ 989a46d1）。冲突记录：无撞号。requests.md 条目 261 已回填。

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

## R265 · 站内信新增类型与来源文案（承接 moon-well R235，2026-11-01）

**需求**：moon-well R235 把积分到账从「管理员勾选才发」改成「注册赠送/充值/兑换/购卡全部自动发」，并新增余额不足与归零提醒。本仓是消费侧，必须让这些信在收件箱里能被读懂，而不是掉进 `You have a new notification.` 兜底文案。

**做了什么**

1. `describeMail` 的 `CREDIT_GRANTED` 分支按 `params.source` 分流：新人赠送、充值到账（附订单号）、卡兑换（附卡密掩码）；**没有 source 的历史邮件仍走原通用文案**——线上已经存在 13 封 hedwig/积分信，不能因为新增字段就把老信渲染成空白标题。
2. 三个新分支：`CREDIT_CARD_PURCHASED`（面额 + 掩码 + 有效期，无 `expiresAt` 视为长期有效）、`CREDIT_BALANCE_LOW`、`CREDIT_BALANCE_ZERO`，都跳 `/credits`（白名单已含，无需扩）。
3. 15 条新词条同时落 `i18n_seed.html`、`zh_Hans_CN` PO 并重编译 MO。仓库的 `test_mail_js_translations_are_in_seed_po_and_mo` 会把 mail.js 里每个 `t()` 字面量拿去跟 seed/po/mo 三方比对，漏一处就红——这也是为什么不能只在 JS 里写英文。
4. 新增 Node 守卫 `test_credit_mail_variants_render_by_source_and_type`：直接执行生产 `describeMail`，覆盖 4 种来源 + 3 种新类型 + 历史回退，并断言跳转白名单。

**验证**：`test_mail_ui_r243.py` 25 例、`test_mail_proxy_r243.py`、`test_admin_mail_r250.py` 共 101 例全绿；`test_i18n_seed_contract.py`、积分页/积分卡/明细 34 例全绿。

**未做**：管理员「同时发送到账通知」默认勾选。R243 的守卫用例断言了 `syncAdminNotificationState` 里 `prop('checked', false)`，改默认勾选要连守卫一起改；这是 UX 决策而非缺陷，留给你拍板。

**驻留**：worktree `../magicbook-r265-credit-mail-render`，分支 `feat/r265-credit-mail-render`。
