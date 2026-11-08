# 对话回应记录

> 含每个需求的回应、冲突说明及两个文件的总结。
> **归档规则**：本文件仅保留最近 10 个 request 的回应；更早内容原样归档至 `response-archive/`（按 request 区间分文件），需要历史细节时按编号检索归档目录，不要读全量历史。

**归档索引**

- `response-archive/response-R280-R281.md`：R280（小程序 AI 伴读通用对话 + 生词本下掉）+ R281（白名单报错带运行时 AppID）——2026-11-08 R290 写入前窗口已有 11 节，连同本次新增一并压回 10 节，原样搬移不改写

- `response-archive/response-R277.md`：R277 · 请求失败必须自己说清原因（2026-11-03）——2026-11-06 R287 写入触发轮转搬移，原样搬移不改写

- `response-archive/response-R276.md`：R276 · 小程序切正式 AppID wx7b31b435be6beae3（2026-11-03）——2026-11-06 R285/R286 并行会话 merge 后窗口 11 节续搬最旧一节；同日 R287 写入时复核，与 R287 轮转同一文件，原样搬移不改写

- `response-archive/response-R275.md`：R275 · 首页改复习、「数据」改「我」、新增主站入口（2026-11-03）——2026-11-06 R286 写入触发轮转搬移，原样搬移不改写

- `response-archive/response-R274.md`：R274 · 登录页表单 UI 修正（2026-11-03）——2026-11-06 R284 写入触发轮转搬移，原样搬移不改写

- `response-archive/response-R273.md`：R273 · 小程序登录页：密码绑定改为邮箱验证绑定（2026-11-03）——2026-11-05 R283 写入触发轮转搬移，原样搬移不改写

- `response-archive/response-R272.md`：R272 小程序账号体系（自动建号 + 账号页）——2026-11-05 R282 写入触发轮转搬移，原样搬移不改写

- `response-archive/response-R271.md`：R271 微信小程序（生词本/复习/词汇量/学习数据）——2026-11-05 R279 merge develop 写入触发轮转搬移，原样搬移不改写

- `response-archive/response-R270.md`：R270 阅读器 bookUrl 大小写致 /show 404——2026-11-05 R280 写入触发轮转搬移，原样搬移不改写

- `response-archive/response-R269.md`：R269 顶栏信息架构收敛——2026-11-04 先由 R279 写入轮转（response-R269.md 含 R269 一节），2026-11-05 R281 再轮转时被 develop 侧同名文件覆盖合并——两侧均为 R269 原文，无内容差异

- `response-archive/response-R278.md`：R278 身份只显示邮箱，不再露账号 ID——2026-11-08 R289 写入触发轮转搬移，原样搬移不改写
- `response-archive/response-R267.md`：R267 重写 GitHub README——2026-11-03 R278 写入触发轮转搬移，原样搬移不改写

- `response-archive/response-R265.md`：R265 站内信新增类型与来源文案——2026-11-03 R277 写入触发轮转搬移，原样搬移不改写

- `response-archive/response-R263.md`：R263 阅读器朗读速度选项——2026-11-03 R276 写入触发轮转搬移，原样搬移不改写

- `response-archive/response-R260-R261.md`：R260（AI 了解我——自我介绍与提示词注入）+ R261（Jinshu 借鉴三件套）——2026-11-03 R274/R275 写入前窗口 10 节，连同本次两条新增一并压回 10 节，原样搬移不改写

- `response-archive/response-R258.md`：2026-10-31（R258：设计方案五充值卡五段式 + 方案十已读三态口径） —— 2026-11-03 R273 写入触发轮转搬移，原样搬移不改写

- `response-archive/response-R259.md`：R259 设置页生词提示语对齐 moon-well R232 新口径——2026-11-03 R272 写入触发轮转搬移，原样搬移不改写

- `response-archive/response-R256-R257.md`：R256（黑盒体验四项缺陷）+ R257（按设计方案实施七项）——2026-11-03 R271 写入前窗口已达 11 节，连同本次新增一并压回 10 节窗口，原样搬移不改写

- `response-archive/response-R251.md`：R251（MagicBook UI 信息架构、导航分组与账号/管理 L2 拆页）——2026-11-01 R265 写入触发轮转搬移，原样搬移不改写
- `response-archive/response-R255.md`：R255（注销后 remember_token 未清除，用户被自动登回）——2026-11-02 R269 写入触发轮转搬移，原样搬移不改写
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

> 归档索引：[response-R01-R31.md](response-archive/response-R01-R31.md) · [response-R32-R49.md](response-archive/response-R32-R49.md) · [response-R50.md](response-archive/response-R50.md) · [response-R51-R70.md](response-archive/response-R51-R70.md) · [response-R70-R80.md](response-archive/response-R70-R80.md) · [response-R81-R101.md](response-archive/response-R81-R101.md) · [response-R102-R110.md](response-archive/response-R102-R110.md) · [response-R111-R119.md](response-archive/response-R111-R119.md)（2026-10-08 R129 补账搬移）· [response-R120-R125.md](response-archive/response-R120-R125.md)（2026-10-08 R135 写入触发搬移，含 R134 登记的窗口欠账补账）· [response-R126-R131.md](response-archive/response-R126-R131.md)（2026-10-09 R141 写入触发轮转搬移）· [response-R132-R133.md](response-archive/response-R132-R133.md)（2026-10-10 R143 写入触发轮转搬移） · [response-R134.md](response-archive/response-R134.md)（2026-10-10 R144 写入触发轮转搬移） · [response-R135-R137.md](response-archive/response-R135-R137.md)（2026-10-10 R147 写入触发轮转搬移，含 R145/R146 两次写入的窗口欠账补账） · [response-R138.md](response-archive/response-R138.md)（2026-10-11 R152 写入触发轮转搬移） · [response-R139.md](response-archive/response-R139.md)（2026-10-11 R153 写入触发轮转搬移） · [response-R140.md](response-archive/response-R140.md)（2026-10-11 R153 复核后的补搬——R152 写入时搬走 R138 后窗口仍为 11） · [response-R141-R142.md](response-archive/response-R141-R142.md)（2026-10-11 R155 集成时窗口超限搬移） · [response-R144-R153.md](response-archive/response-R144-R153.md)（2026-10-12 R161 写入触发轮转搬移，清并行欠账 R144–R153） · [response-R154.md](response-archive/response-R154.md)（2026-10-12 R165 写入触发轮转搬移） · [response-R155-R156.md](response-archive/response-R155-R156.md)（2026-10-13 R166 写入触发轮转搬移，含同日同编号「细筛」那条） · [response-R157.md](response-archive/response-R157.md)（2026-10-13 R166 分支 merge origin/develop 后窗口仍达 11，续搬最旧一节） · [response-R156-mic.md](response-archive/response-R156-mic.md) · [response-R158.md](response-archive/response-R158.md)（2026-10-13 R168 写入触发轮转搬移）（2026-10-13 R167 写入触发轮转搬移；与 response-R155-R156.md 里的同编号「细筛」条目不同事） · [response-R160-R164.md](response-archive/response-R160-R164.md)（2026-10-14 R172 写入触发轮转搬移，窗口转入 R161 起） · [response-R161-R162.md](response-archive/response-R161-R162.md)（2026-10-14 R173 写入触发轮转搬移，窗口转入 R165 起） · [response-R165-R173.md](response-archive/response-R165-R173.md)（2026-10-15 R183 写入触发轮转搬移，窗口转入 R174 起） · [response-R174-R177.md](response-archive/response-R174-R177.md)（2026-10-16 R185 写入触发轮转搬移，窗口转入 R178 起） · [response-R175.md](response-archive/response-R175.md)（2026-10-16 R188 写入触发轮转搬移） · [response-R214-C.md](response-archive/response-R214-C.md)（2026-10-25 R229 写入触发轮转搬移：R214 子项 C 整本任务代价面板；与既有 response-R214.md（子项 A）不同事） · [response-R238.md](response-archive/response-R238.md)（2026-10-29 R250 / R252 并行写入轮转，原样搬移不改写） · [response-R239.md](response-archive/response-R239.md)（2026-10-29 R250 / R252 合并后窗口达 11 节轮转） · [response-R244.md](response-archive/response-R244.md)（2026-10-29 R250 / R252 合并后窗口达 11 节轮转） · [response-R243.md](response-archive/response-R243.md)（2026-10-29 R254 写入触发轮转搬移） · [response-R246.md](response-archive/response-R246.md)（2026-10-30 R256 写入触发轮转搬移） · [response-R247.md](response-archive/response-R247.md)（2026-10-31 R257 写入触发轮转搬移） · [response-R248.md](response-archive/response-R248.md)（2026-10-31 R258 写入触发轮转搬移） · [response-R253.md](response-archive/response-R253.md)（2026-11-01 R263 写入触发轮转搬移） · [response-R254.md](response-archive/response-R254.md)（2026-11-02 R267 写入触发轮转搬移）

## R279 · 普通用户投稿书籍：暂存 MinIO，管理员审核后入库（2026-11-04）

**对 R279 的回应**：需求是「给普通用户一个新的上传图书接口，仅上传到 MinIO，管理者审核后可以解析入库」，operator 已确认开工。

- **没有复用 `/upload`**：那条链路的权限位 `ROLE_UPLOAD` 会直写共享书库，`upload_book_formats` 甚至能覆盖任意书目的格式文件。新链路把写权限收回管理员：用户提交只进 MinIO 私有暂存区并落一条 PENDING 台账，**入库只发生在管理员点「通过」之后**。
- **暂存前缀 `book-submissions/<user_id>/<uuid>.<ext>`**：不进匿名只读 Statement（现在只放开 `buddy/`、`ted-audio/`）。预览走同源代理、不生成预签名直链，仓库侧有守卫测试锁死。
- **审核页** `/admin/submissions`（管理 → 内容与 AI → 书籍投稿）：列表、预览、通过、驳回；通过后后台线程 `app.app_context()` + 线程作用域会话解析入库，状态写 `INGESTED` 并回填 `book_id`；驳回删对象留备注。失败置 `FAILED` 可重审。
- **用户侧**：`/me` 新增「建议一本书」面板，提交前必须勾选「我有权分享此文件」；文件先入私有暂存区，审核通过前不出现在书库。支持 epub/pdf/txt/mobi/azw3/fb2/docx 等，单文件上限 100MB。
- **未做**：站内信通知、对象定期清理/孤儿扫描、「只对投稿者可见」的 owner 模型——均记入 LLD §8，需另立需求。
- **验证**：`tests/test_r279_book_submission.py` 20 例（提交/声明/白名单/音视频拒绝/匿名/去重/权限/通过入库/驳回/状态机/安全守卫/导航归属 + 3 条 E2E 回归守卫）全绿；**真实上传测试**用一本真实 EPUB 走完「提交→暂存→审核→入库」：`book_id=1`、暂存对象已删、`calibredb list` 可见「E2E 投稿测试书 / 测试作者 / EPUB」；这次 E2E 抓出并修掉三个单测桩覆盖不到的缺陷（后台线程需 `test_request_context`、入库前需 `create_functions`、add-or-get 不能用 `merge`）。生产 MinIO 凭据本机不可得，E2E 用本地 S3 兼容端点走真实 minio SDK，生产真机验证待合并部署后补。`test_account_admin_ia_r251` 契约演进 14→15 管理页；i18n 种子契约与相关导航/账号回归全绿。**全量 1315 passed / 21 failed（21 项在 origin/develop 基线同样失败，属本机无 calibre 书库的环境性失败，非本次回归）**。画面证据见 `docs/project/iterations/2026-11-book-submission/evidence/`。

**台账总结**：`requests.md` 第 279 条本处回填；`response.md` 写入前窗口与 R280/R281 并行增长，merge develop 后按 10 节窗口把最旧一节 R271（微信小程序）原样搬入 `response-archive/response-R271.md` 并登记索引（R270 由 develop 侧 R280 写入轮转、R269 由 R279/R281 先后轮转，见归档索引）。

## R282 · 报错必须说出「实际请求的完整 URL」（2026-11-05）

**对 R282 的回应**：白名单三处都对（后台、「项目配置 → 域名信息」、工具本地缓存里
`RequestDomain` 含 `https://moon-well.haoshenqi.top`，appid 为正式号、`isTrusted: true`），
服务端也实测可达、无跳转、带小程序 UA 返回业务 JSON，可请求仍报 `url not in domain list`。

- **这一轮没能定位根因，但拿掉了「靠猜」的那部分。** 之前所有排查都建立在我们自己的提示上，
  而那条提示只打印 `CONFIG.baseUrl`——**它永远显示那个「本该正确」的域名**。于是无论真实原因
  是什么（路径拼接错、baseUrl 带隐藏字符、请求发往别处），用户看到的都是「添加
  moon-well.haoshenqi.top」，看起来完全正确，人就被引去反复确认后台。这是提示的设计缺陷，
  不是运气差。
- **改法**：`rawRequest` 先把 `const url` 算出来，`wx.request`、日志、错误文案共用同一个值；
  白名单文案变成三段——「为这个 AppID 添加 `<被拦域名>`｜实际请求 `<完整 URL>`｜微信原文
  `<errMsg>`」。被拦域名从**真实 URL** 里取（`hostOf()`），不再从 `CONFIG.baseUrl` 取，
  这样两者不一致才会暴露出来。SSE 的 `chatStream` 同步带上 `chatUrl`。
- **`hostOf()` 保留端口**：白名单不接受端口，若 URL 真带了端口，提示里必须原样显示，
  否则又会变成一个「看起来对」的域名。
- **本次已排除**：开发者工具项目记录与缓存（单条记录、appid 正确、域名齐全）、
  `project.config.json` 的 `appid`、`baseUrl` 的字符构成（纯 ASCII 31 字符）、所有请求路径
  均以 `/` 开头、服务端 301/302（四个路径全部直连）、网关对小程序 UA 的拦截。
- **验证**：`tests/test_r282_requrl.py` 6 例（URL 只算一次并复用、日志打 URL 不打 path、
  文案含真实 URL 与 errMsg 原文、两处调用点都传 url、`hostOf` 行为）+ R277/R281 既有锁，
  合计 **13 passed**；`hostOf` 经 Node 实测含 null/空串/带端口。
- **状态**：**已上线**（`d83cf2ae` 合入 develop 并推送）。用户于 2026-11-05 11:22 确认开发调试恢复。
  **根因未确证**——白名单三处与运行时 AppID 全部正确、服务端无跳转，恢复也可能来自工具侧配置刷新；
  这条改动本身只负责「下次报错能自证」，不解决故障。

**台账总结**：`requests.md` 第 282 条本处回填；`response.md` 写入前 9 节（上一轮已归档 R272 之外的
旧条目），本次回到 10 节，最旧一节 R272（小程序账号体系）原样搬入
`response-archive/response-R272.md` 并登记索引。

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

## R285 · Buddy 头顶滚动复习气泡（2026-11-06）

**对 R285 的回应**：用户要「AI buddy 头顶定时播放一段话，内容是最近划词的单词详情」。两轮只读核查后先纠正两个事实再动手：用户点名的「单词学习表」确实存在（`vocabulary_notebook` / `vocabulary_study_history` / `learning_review_schedule` / `learning_answer_log`），但查词历史只写不读、无倒序接口、划词路径不写入，不需要也不该新建表；「点认识算复习」在代码里不成立——`GET /vocabulary/known/{word}` 只把 SRS 调度行异步毕业 `MASTERED`，不写 `learning_answer_log`、不涨 x/20。用户据此拍板：词源改取 SRS 到期队列、认识复用已有端点、只做被动展示。

- **交付**：登录态全站 FAB 头顶一张纯文字词卡，8 秒轮播 20 个到期词（前端洗牌），显示 `word + meaning + contextSentence`；页面不可见 / 窗口不活跃 / 伙伴隐藏 / 快捷气泡 / 抽屉 / 邮件弹层时暂停；气泡自带暂停·继续与收起·展开，状态记本机 localStorage；点「认识」复用 `/ajax/reading-word-mark {unknown:false}`，成功后只从本地轮播移除。**`cps/routes/*` 与 moon-well 零改动、零新增表、零新增端点、零 TTS / 详解 / 评分调用、零计费**。
- **实现要点**：卡片挂 `#ai-companion-root` 而非 `fab-wrap`，fixed 按 FAB rect 定位（`is-left` / `is-below` 自适应），避开 hover 快捷气泡与拖拽命中区；所有服务端字段 `textContent`；解包与 CSRF 委托 `MBApi`（R177 单点）。
- **交叉审查**：独立 Agent 视角发现并修复 6 处——标记请求跨 8s tick 会删错词（`markedIndex` + `inFlight` 暂停）、bfcache 返回轮播停摆（`pageshow` 重建 timer）、EPUB iframe 焦点被 `hasFocus()` 误判为不活跃、拖拽吸附过渡期间定位错位（`transitionend` + 260ms 兜底）、`markError` 跨词残留、移动端触达盒补 44px；测试同步补强到 12 例。
- **验证**：`node --check` 通过、`pybabel compile -f` 通过；定向 **129 passed**；全量 `1296 passed / 80 errors`，errors 全是干净 worktree 的 pytest tmp 目录 `FileExistsError` 竞态（R144 同类），独立 `--basetemp` 复验三个报错文件 **25 passed**，与本轮改动无关；i18n 13 个 key 中文齐全。**未真机验收**。
- **文档四问**：L1 `readme/companion.md`、L2 `companion/interface.md` §滚动复习、L3 `companion/features/rolling-review.md`、需求基线 `companion/requirements.md` §6；HLD/LLD/AC/plan 落 `iterations/2026-11-rolling-review/r285-rolling-review/`，`iterations/1.0/plan.md` 补行。
- **已知前置缺陷**：`readpdf.html` 未引入 jQuery 却 include 面板，`ai_chat.js` 以 `jQuery` 为实参会抛 `ReferenceError`——R285 之前 Buddy 面板在 PDF 阅读器就不可用。本轮不扩范围，AC 单列真机确认项，若属实另立需求。

**台账总结**：`requests.md` 第 285 条本处回填（占号 2026-11-06，`6bbc4738`）；`response.md` 写入前 10 节、本次 11 节，按「写入即检查」把最旧一节 R275 原样搬入 `response-archive/response-R275.md` 并在顶部归档索引登记，窗口回到 10 节。冲突记录：无撞号；R285 与并行会话 R286 的三份台账文件冲突，merge 时按编号顺序合并两节、R275 归档沿用 R286 会话版本，并续搬最旧一节 R276 回 10 节窗口；源码文件无重叠（R286 动 `reader-selection.js` / 阅读器样式，R285 动 `ai_chat.*` / i18n）。worktree `../magicbook-r285-rolling-review` / 分支 `feat/r285-rolling-review` merge 后原样保留待验收，**未 push 上线**（等用户下令）。

## R286 · 生词悬停释义卡：去掉「问号指针」，悬停即出释义（2026-11-06）

**对 R286 的回应**：用户 12:41 截图「magicbook 划词翻译显示问号」，并在四个形态里选定
「悬停弹 MagicLens 同款气泡」。R284 否决的是**形态**（原生 tooltip / 自绘小卡），
本轮按参考图重做，并把用户实际看到的「问号」这一层一并处理。

- **「问号」不是文案，是指针**：`.reading-vocabulary-unknown{cursor:help}` 让鼠标一停生词
  就变成问号指针；而 `span.title` 自 R268 已下线，悬停没有任何释义落点。父页 `reader.css`
  与注入 iframe 的 `READER_TOOLS_STYLE` 两处同改 `pointer`（R268 的教训：只改一处等于没改）。
- **卡片形态**：`.reading-vocab-card`（白卡 + 词条 + 释义 + `译/详/🔊/认识/生词/AI/✕` 胶囊），
  挂父页 body、坐标按 `frameElement` 换算，与划词气泡同一套口径；悬停 140ms 确认后弹出，
  触屏点一下弹出。关闭路径：✕ / Esc / 翻页 / 点卡外 / 正文 mousedown / 正文滚动 /
  「标认识」成功后；与划词气泡互斥（开卡收气泡，拖选出译文收卡）。
- **顺手挖出一个真 bug**：`ReaderSelection.setHost` 只接了 `markVocabulary` /
  `buildSpeechUtterance`，装配层一直在传的 `getWordRecord` / `applyWordRecord` /
  `startWholeBookProgressPolling` 被静默丢弃——于是「＋标生词」不画波浪线、「－标认识」
  不拆线、＋/－ 高亮永不亮，卡片也读不到 `record.gloss`。本轮补接三条通道，
  并把气泡 ＋/－ 与卡片「认识/生词」收敛到同一个 `markWord()`。
- **计费边界**：卡片释义取 analyze 回传的词典首义项（零请求零计费）；缺释义时**不**自动
  发翻译请求（单词未命中词典会走 LLM 计费，悬停不能悄悄扣积分），由用户点「译」显式触发。
- **验证**：`tests/test_r286_vocab_hover_card.py` 6 例；定向回归 25 passed；阅读器/词汇
  子集 273 passed（`test_reading_tts_service.py` 的 44 例为 pytest tmpdir 在沙箱里的
  `FileExistsError`，develop 上同样复现，与本轮无关）；无头 Chrome 加载真实 JS/CSS 冒烟，
  卡片形态与参考图一致。**未真机**：真实 EPUB 分栏、深色主题对比度、触屏点按待线上验收。

**台账总结**：`requests.md` 第 286 条本处回填；`response.md` 写入前 10 节、本次 11 节，
按「写入即检查」把最旧一节 R275 原样搬入 `response-archive/response-R275.md` 并在顶部
归档索引登记，窗口回到 10 节。编号：285 已被「Buddy 头顶滚动复习气泡」占号（并行会话），
本轮取 286；无撞号、无冲突分支。

## R287 · 划词翻译与生词划线拆成两条独立功能（2026-11-06）

**对 R287 的回应**：R286 上线半小时后用户补全口径——不是修 bug，是纠形：

> 「划词翻译和生词划线是两个功能。生词划线仅自动标识生词即可，若用户打开了生词自动翻译
> 显示开关，生词后（里）显示词义。划词翻译适用于任何地方，不仅限于生词。未标注生词的单词
> 也可以。划词如果是英文单词，自动翻译。如果非英文单词，需要点击译字才翻译（避免用户只是
> 为了选中复制等其他非翻译场景浪费 token）。」

对照代码，R286 有三处不符，本轮全部改掉：

- **两条功能解耦**：`translateSelection` 去掉 `readingVocabularyEnabled` 依赖——关掉生词功能，
  划词翻译照常可用（此前被生词开关绑死）。
- **单词自动、非单词点译**：新增 `openTranslationFor()` 作为唯一入口。单个英文单词打开即请求；
  非单词只出原文预览 + `译`/`AI`，**一个请求都不发**，点「译」才发。此前任何选区都直接送 LLM，
  用户框选长段只为复制时也照烧 token。
- **悬停生词不再另造 UI**：删除 R286 的 `.reading-vocab-card`（DOM/样式/状态/导出 + `epub.js`
  三处钩子），`bindVocabHover` 140ms 确认后把 span 矩形喂给 `openTranslationFor`——内容就是
  那一次划词翻译的结果，同一个气泡、同一份自动隐藏与关闭路径。触屏点一下等价于悬停。
- 保留 R286 的两项附带修复：`cursor:help → pointer`（父页 + 注入 iframe 两处）、`setHost`
  补接 `getWordRecord`/`applyWordRecord`/`startWholeBookProgressPolling`。

**验证**：`tests/test_r287_selection_vs_vocab.py` 7 例；定向回归 26 passed。无头 Chrome 加载
真实 JS/CSS 冒烟（`$.ajax` 打桩计数）：悬停生词 1 条 POST 并出译文；选中英文句子 0 条 POST，
只出 `译`/`AI`；选中中文 0 条 POST；点「译」后 1 条 POST 出结果。**未真机**：触屏点按与真实
EPUB 分栏定位待线上验收。

**文档**：`reading-vocabulary.md` 重写为「两条独立功能 + 一条链路两种触发 + 历史沿革」，把
三处过期事实一并修正——① 概述里的「学习记录」（字段 R139 已删）；② 「三端点暂无前端调用方」
（一直有调用方）；③ §2 里与悬停并存的「点击弹释义 + 上次：书·章节」（2026-09-14 就下线了）。
L1 `readme/reading.md` 拆成两条用户文案；L2 `reading/interface.md` 同步修正。R286 的 LLD
与需求基线小节均标注「已被 R287 取代」，不重写正文。

**台账总结**：`requests.md` 第 287 条本处回填；`response.md` 写入前 10 节、本次 11 节，把最旧
一节 R277 原样搬入 `response-archive/response-R277.md` 并登记索引，窗口回到 10 节
（R276 早已由并行会话的 R285/R286 merge 轮转归档，本轮复核未重复）。

**补记（14:20，用户当场纠正）**：上文「扩展侧没有 hover」是我的错判，纠正三点——
① magiclens **R20/R21 本来就实现了「悬浮生词即出划词气泡」**（`highlight.js` 的
`onMouseMove` → `__magicLensShowWordBubble(word, rect, 'hover')`，200ms 稳定延迟 / 150ms
离词宽限），② **R24 起支持同源 iframe 内悬浮**（书页正文正是这种 iframe，矩形按 `frameElement`
叠加到顶层视口），③ 命中范围与内置一致，只对**已高亮（生词）**的 `nodeRaws` 生效。
所以「扩展接管高亮 → 内置不画线 → 悬停没人管」这个担心不成立：接管期间悬停也归扩展，
用户那句「两者功能一致，留一个」正是现状——同一页面任何时候只有一个气泡属主。
改动仅文档：修正 R287 LLD 的错句、在 `reading-vocabulary.md` 的历史沿革里记下扩展侧悬停的
版本坐标（R20/R21、R24、R37、R57），免得下次又把「扩展没悬停」当成待办重新实现一遍。

**补记（14:25，口径落定）**：扩展接管高亮时「生词行内释义」开关不生效——用户判定为**不重要、
默认也不启用**，只把结论写进文档，不改代码、不给扩展加浮层、也不在正文里插 span（那会扰乱
扩展的 token 区间）。已记入 L1 `readme/reading.md`、L3 `reading-vocabulary.md` §2.1 与概述表、
需求基线 §R287 第 5 条，作为**已知限制**（不是待办）。

---

## 2026-11-07 · R288 新增 dev 测试环境（dev-magicbook）与双环境发版流程

**对 R288 的回应**：用户指令「增加测试环境。新增两个 dev 容器 moon-well 和 magicbook，域名加 dev- 前缀。
数据库等使用同样的即可。修改发布流程，merge develop 发 dev 环境、merge release 发正式环境。先更新所有文档，
再改发布流程。」本仓承载 magicbook 侧 dev 环境资产与 AGENTS.md 分支口径；主号=ops R177
（`ops/docs/dev-environment-2026-11.md` 整体设计），moon-well 同源号 R246。

- **本仓改动（应用代码零改动）**：① `deploy/dev/` 四件套——compose.yaml（`magicbook-dev` host 网络
  :8085、独立 `CONFIG_PATH`、书库共享、无 filebeat）、deploy.sh（:dev 分 tag + code-digest 判等）、
  .env.example、README.md；② AGENTS.md「Git 分支管理」改 **develop→dev / release→生产 / master 冻结**
  （R288 取代 master 的发布语义，worktree 规范 L46 引用同步）；③ DEPLOY.md CI/CD 节补双环境口径；
  ④ LLD 落 `iterations/1.0/r288-dev-environment/`。
- **独立 CONFIG_PATH 是硬前提**：`settings.config_port` 存 DB 会覆盖 `CALIBRE_PORT` 环境变量
  （`cps/config_sql.py`），共用 config 目录时 dev 端口改不动；SECRET_KEY/调度开关（存 DB）随库走。
- **app.db 复制自生产（用户拍板）**：初始化 = sqlite 在线备份复制 + `UPDATE settings SET config_port=8085`
  + 关闭 `schedule_metadata_backup`/`schedule_reconnect`/`schedule_generate_book_covers`/
  `schedule_generate_series_covers`（防夜间任务写共享 metadata.db）；账号/OIDC 绑定关系随库复制，登录即用。
- **书库共享只读姿态**：`CALIBRE_LIBRARY_PATH=/app/magicbook/calibre-library`；dev 禁元数据编辑/投稿
  入库/calibredb 写操作。
- **MOON_WELL_READING_URL=http://fnos:8084**：指向 dev moon-well（R246），形成完整 dev 链路；
  OIDC issuer/client 与生产同值，redirect 指向 dev 域（Authentik 白名单加条目）。
- **门禁说明**：本改动无应用代码变更，pytest 不适用；验证以部署端到端 AC 为准（LLD §5）。

**驻留登记**：worktree `../magicbook-r288-dev-environment`，分支 `chore/r288-dev-environment`，
基线 `64753f0e`（origin/develop 最新点，R288 占号提交），状态=待 fnOS 落地与端到端验收；
验收通过后 `worktree remove` → `branch -d`。

**台账总结**：`requests.md` 第 288 条占号行本处对应；`response.md` 本次追加 1 节，窗口计算以
merge 回主检出时为准（不足归档阈值）。

## R289 · 滚动复习正文升级为单词详情分页轮播（2026-11-08）

**对 R289 的回应**：用户原话「滚动复习的功能，改为显示单词详情。但是每次只显示一部分，
每次显示不超过3行」；两问拍板——只用**已缓存详解**（零计费），每词展示「基本意思 +
一个随机模块」避免太长，同词连翻多页。

- **数据面**：新增薄代理 `POST /ajax/vocabulary/detail-cached-batch`（`routes/vocab.py`，
  `@user_login_required`）→ moon-well R248 `POST /vocabulary/detail/cached-batch`
  （只读缓存批量端点，miss 不出现在结果里、绝不触发生成）。词表归一（trim/弯撇号/
  小写/去重/`_READING_WORD_RE` 白名单）、上限 50 与上游同口径；空/全非法词表本地短路
  不打上游。**逐词详解代理 `/ajax/reading-word-detail` 仍是禁区**（miss 即计费），
  R285 守卫测试把两条计费路径一起钉死。
- **前端分页**：`ai_chat.js` R285 块内新增页装配（基本意思前 2 义项 + 随机模块 ≤2 页、
  每词 ≤4 页）与 `review.pages/page` 状态；tick 先在词内翻页、翻完换词；词源按句切页
  （~60 字/页）；`.ai-review-detail` 用 `-webkit-line-clamp: 3` 硬钳 3 行。
  无缓存词与详情接口失败一律回退 R285 简卡（增强层语义，可观测性在代理日志）。
- **i18n**：新增 4 词条（Collocations/Word forms/Slang/Fun facts）走种子+PO+MO
  三方并 `pybabel compile -f`；Etymology/Synonyms/Antonyms 复用存量。
- **验证**：定向 `test_r285_rolling_review(13) + test_r289_detail_cached_batch_proxy(8)
  + test_i18n_seed_contract + test_vocab_test_proxy` 共 **52 passed**；相关面回归
  （R280 伴读/R244 动画/R227 语音/公共解包/learning 代理/CSP/词详解批量）**155 passed**；
  `node --check` 与 `pybabel` 通过。守卫测试新增 R289 分页专项
  （翻页优先于换词/页数上限/3 行钳制/失败回退）。
- **文档四问**：L1 `readme/companion.md` 滚动复习段改写；L2 `companion/interface.md`
  端点表 +1 行与口径；L3 `companion/features/rolling-review.md` 增 R289 节与降级行；
  需求基线 §6.1 + 变更记录；LLD 落 `iterations/2026-11-rolling-review/r289-detail-pages/`。
**驻留登记**：worktree `../magicbook-r289-review-detail-pages`，分支 `feat/r289-review-detail-pages`，
基线 `7b748bc0`（含占号提交），merge 后保留待验收；验收通过后 `worktree remove` → `branch -d`。
**台账总结**：`requests.md` 第 289 条已回填；`response.md` 本次追加 1 节并轮转搬移最旧 1 节
（R278 → `response-archive/response-R278.md`），窗口恢复 10 节。

## R290 · 小程序每日复习页空题面死卡（2026-11-08）

**对 R290 的回应**：用户截图报障「修复这个小程序的bug」——「每日复习」第 1/20 张只有一行
「看下面的提示，回想这个词」+「揭示答案」，没有任何可回想的内容。

- **复现**：小程序不在容器里跑、本机也没有微信开发者工具，所以复现走真代码渲染——
  `before` 取 `origin/develop`(`38dfb494`) 整棵 `miniprogram/`，用 `miniprogram-simulate`
  （微信官方 `wcc` 模板编译器 + `j-component`）编译**仓库里的 WXML**，再用 `driver.js`
  加载**真实的 `review.js`**（替换 `wx`/`Page` 运行时）跑 `showCard`，把 `setData` 后的 data
  交给模板，套真 `app.wxss`+`review.wxss` 无头 Chrome 截图。**渲染结果与用户截图同形**：
  一句灰字提示语，没有题干。
- **根因（两层）**：① `review.wxml` 把题干只挂在 `mode === 'CHOOSE' || mode === 'SPELL'`
  两个分支上，而 `review.js#pickMode` 只对这两种题型返回具体值，`RECALL`
  （后端自适应与 legacy 梯度最常用的档位）被降成 `SELF` 落进 `wx:else` 的提示语——
  后端下发的 `meaning` 就在手里，前端从未渲染它；② `SELF` 分支也不亮词面（词面只在
  `revealed` 后出现），所以释义缺失（详解缓存未命中 `meaning=null`）时提示语、释义、词面
  三者全无，卡片是白板。`contextClozeSentence` 同样从未被当题干用过。
- **改法**：呈现态判定抽成纯函数 `utils/review-card.js#presentCard`（与网页端
  `learning-review.js` 同口径）：四选一需释义 + ≥2 选项、拼写需释义、语境完形用挖空句、
  **其余有释义的一律「回忆」且释义即题干**、都没有才退到「自评」（直接亮词面）。
  WXML 改为渲染统一 `stem`（`stemCloze` 决定挖空样式），词面与语境按「已揭示 or SELF」显隐，
  「揭示答案」对回忆与拼写都给（拼写卡不能把人卡在输入框上）。
- **边界**：不补生成释义（只读缓存、不烧积分）、不改后端题型策略、作答回传的
  `questionType` 仍是后端原值（调度口径不变，R271 定下的边界）。
- **验证**：新增 `tests/test_r290_review_card_stem.py` 4 例——Node 跑 `presentCard` 的
  11 组输入矩阵（含释义缺失 / 选项不足 / 未知题型 / 空白释义）、断言「任何队列项必须露出
  题干或词面之一」、WXML 与页面静态锁；小程序静态锁全绿 **58 passed**
  （R271–R283 合计 54 + 本轮 4）；`node --check` 与全部 `.json` 解析通过。
- **视觉证据**（`iterations/2026-11-wx-review-card/r290-review-card-stem/evidence/`）：
  `user-report.jpg`（用户原始截图）、`before-after-recall.png`（回忆卡：左只有提示语 / 右释义即题干）、
  `before-after-no-meaning.png`（缺释义：左空白 / 右亮词面自评）、
  `before-after-recall-revealed.png`（揭示后两边都亮词面与语境）、
  `before-after-choose.png`（四选一无回归）。基线 `develop@38dfb494`，改动为本轮工作区。
- **未做**：**未真机、未在微信开发者工具编译**（本机没有该工具，与 R271–R283 同）；
  证据来自官方模板编译产物 + 真 WXSS，与真机差异只在系统字体与安全区。
- **文档四问**：L1 `readme/miniprogram.md` 复习段补题干来源与缺释义口径；L2 无接口变化；
  L3 新建 `product/miniprogram/features/review.md`；需求基线新增 §R290；
  LLD `iterations/2026-11-wx-review-card/r290-review-card-stem/lld.md`。
- **冲突记录**：本轮占号 `R290` 时 develop 无并行占号；开工后无其他会话改动
  `miniprogram/pages/review/*`，无冲突。
- **状态**：**开发完成待验收**（分支 `agent/fix-miniprogram-review-bug-36fb2af0b54b`，
  PR 见本轮 push 后的 GitHub 链接；小程序需重新上传体验版才能在真机看到修复）。

**台账总结**：`requests.md` 第 290 条已回填；`response.md` 写入前窗口已有 11 节
（R281、R280 两节由并行会话累积未轮转），本次连同新增 R290 一并压回 10 节——
最旧两节 R281、R280 原样搬入 `response-archive/response-R280-R281.md` 并在顶部登记索引。
