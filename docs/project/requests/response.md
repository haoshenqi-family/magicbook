# 对话回应记录

> 含每个需求的回应、冲突说明及两个文件的总结。
> **归档规则**：本文件仅保留最近 10 个 request 的回应；更早内容原样归档至 `response-archive/`（按 request 区间分文件），需要历史细节时按编号检索归档目录，不要读全量历史。

**归档索引**

- `response-archive/response-R274.md`：R274 · 登录页表单 UI 修正（2026-11-03）——2026-11-06 R284 写入触发轮转搬移，原样搬移不改写

- `response-archive/response-R273.md`：R273 · 小程序登录页：密码绑定改为邮箱验证绑定（2026-11-03）——2026-11-05 R283 写入触发轮转搬移，原样搬移不改写

- `response-archive/response-R272.md`：R272 小程序账号体系（自动建号 + 账号页）——2026-11-05 R282 写入触发轮转搬移，原样搬移不改写

- `response-archive/response-R271.md`：R271 微信小程序（生词本/复习/词汇量/学习数据）——2026-11-05 R279 merge develop 写入触发轮转搬移，原样搬移不改写

- `response-archive/response-R270.md`：R270 阅读器 bookUrl 大小写致 /show 404——2026-11-05 R280 写入触发轮转搬移，原样搬移不改写

- `response-archive/response-R269.md`：R269 顶栏信息架构收敛——2026-11-04 先由 R279 写入轮转（response-R269.md 含 R269 一节），2026-11-05 R281 再轮转时被 develop 侧同名文件覆盖合并——两侧均为 R269 原文，无内容差异

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





## R275 · 首页改复习、「数据」改「我」、新增主站入口（2026-11-03）

**对 R275 的回应**：三条一起做，因为都落在同一份 `app.json` / 同一个页面结构上。

- **复习置首**：四页里只有复习是「每天都有明确下一步」的动作（队列有限、有终点），
  生词本与词汇量是「想起来才点」。工具型小程序打开成本高，首页必须是不用思考就能开始的那个。
  连带把登录成功后的 4 处 `switchTab` 全改成复习——不改的话用户登录完落在第二屏，每天多点一次。
- **「数据」→「我」**：这一页本来同时是账号入口（绑定邮箱、退出），只叫「数据」会让人找不到换绑。
  结构顺势重排为「身份卡（点进账号页）→ 网页版入口 → 学习数据 → 退出登录」：
  身份卡置顶，退出从头部小胶囊移到页面末尾——不可逆动作不该放在拇指最容易误触的位置。
- **主站入口用「复制链接」而不是 web-view**：小程序不能直接调起浏览器；web-view 里跑 OIDC
  拿不到浏览器会话，进去就是登录页，且要额外配置业务域名校验文件。产品口径本来也是「阅读留在
  网页」，塞进 web-view 只是把网页装进更小的框。域名只写在 `config.js` 的 `siteUrl`，
  登录页页脚那句写死的域名也一并去掉（静态锁守着「域名只允许出现在 config.js」）。
- **验证**：`tests/test_r275_home_profile.py` 5 例静态锁；与 R271–R274 合计 **27 passed**；
  全部 `.js` 过 `node --check`、`.json` 过 `JSON.parse`。**未真机**：需确认改顺序后首次进入落在复习、
  以及两张卡片的点击热区没被 flex 挤掉。
- **已知边界**：从「复制链接」跳出去的人数拿不到（没有外链点击上报）；链接本身仍要浏览器登录态。

**台账总结**：`requests.md` 第 274、275 条本处回填；`response.md` 写入前 10 节，
本次连同新增两条压回 10 节，最旧两节 R260/R261 原样搬入
`response-archive/response-R260-R261.md` 并在顶部登记索引。R274 与 R275 共用同一分支与 worktree
（`../magicbook-r274-login-ui`，`feat/r274-login-ui`），两条改动无文件冲突。

## R276 · 小程序切正式 AppID wx7b31b435be6beae3（2026-11-03）

**对 R276 的回应**：开发者工具弹「测试号 AppId 无法使用当前功能」。换正式号
`wx7b31b435be6beae3`，后端同步改（moon-well R242）。

- **换号不是改字符串**：`openid` 是 AppID 维度的——同一个微信在新号下是新 openid，
  `app_user_wechat` 里的旧绑定永远匹配不到。所以换号后第一次登录会落到一个新账号，
  得用「我已有账号，用邮箱登录」认领回原账号（归并时空壳账号被删、目标账号旧绑定被替换）。
  这不是我们的 bug，是微信的身份模型，写进了手册与 LLD。
- **合法域名也是按 AppID 存的**：新号要重新在「开发管理 → 开发设置 → 服务器域名」加
  `https://moon-well.haoshenqi.top`，旧号的配置不会继承。这条最容易漏，真机直接报
  「不在合法域名列表」。
- **静态锁只锁本仓这一侧**：理想是「小程序 appid == 后端默认 appid」一条测试守住，
  但两仓在 CI 里分开检出，跨仓断言要么恒跳过（假绿）要么恒失败（假红）。改成两侧各锁自己，
  magicbook 锁正式号字面量与格式，moon-well 的 `WechatAppIdConfigTest` 锁默认值。
- **验证**：`tests/test_r276_appid.py`（2 例）+ R271 既有锁 → **8 passed**。
  后端线上实测：新 appid + 新 secret 后 `/auth/wx/login` 传假 code 得到微信 `40029`
  （说明凭证有效、只是 code 伪造），且未重启（Nacos 热更新）。
  对照实验同时确认：新 appid + 旧 secret → `40125 invalid appsecret`。
- **未真机**：本机没有开发者工具，预览/真机、域名白名单、登录全流程要你在工具里走一遍。

**台账总结**：`requests.md` 第 276 条本处回填；`response.md` 写入前 10 节，本次压回 10 节，
最旧一节 R263（朗读速度选项）原样搬入 `response-archive/response-R263.md` 并登记索引。

## R277 · 请求失败必须自己说清原因（2026-11-03）

**对 R277 的回应**：开发者工具里一切正常，发布体验版后所有请求失败、提示「请检查网络」。

- **先排除服务端**：`moon-well.haoshenqi.top` 解析到公网 116.62.200.90，证书链完整
  （`Verify return code: 0`）、TLS 1.2、单次请求 0.2s。不是超时、不是证书、不是内网域名。
- **问题在我们自己的错误处理**：`wx.request` 的 `fail` 回调原本直接抛「请检查网络」，
  把 `errMsg` 丢了。而体验版最典型的失败——`request:fail url not in domain list`——
  **只存在于 `errMsg` 里**。抹掉之后，「白名单没配」被显示成「网络有问题」，
  方向直接反了；旧文案还顺带建议「在开发者工具关闭域名校验」，可体验版根本没有这个开关。
- **改法**：`describeNetworkError()` 三分——白名单（直接给出后台路径 + 实际域名）、
  超时、链路/证书；认不出来就原样带出 `errMsg`。同时 `console.error` 留一行，
  体验版打开调试就能在 vConsole 里看到原始原因。
- **给手册加了「请求失败怎么查」**，第一条就是那句最容易误解的：**「不校验合法域名」
  只对开发版生效**，真机与体验版一律严格校验。
- **验证**：`tests/test_r277_network_error.py` 4 例静态锁（fail 必须收 err、白名单必须单独识别、
  兜底必须带 raw、旧文案必须消失）；`node --check` 通过。**未真机**。

**台账总结**：`requests.md` 第 277 条本处回填；`response.md` 写入前 10 节，本次压回 10 节，
最旧一节 R265（站内信类型与来源文案）原样搬入 `response-archive/response-R265.md` 并登记索引。

## R278 · 身份只显示邮箱，不再露账号 ID（2026-11-03）

**对 R278 的回应**：账号页原来写着「账号 ID 123 · 邮箱 x@y」，副标题还回显自动生成的
`wx_xxx` 用户名；「我」页标题也拿 username 兜底。

- **删的是两处，不是一处**：用户看到的「ID」其实有两份——真正的 `userId`，和自动生成的
  `username`。只删前者，后者照样出现在标题与副标题里，而且看起来更像「账号」。
- **身份表达改成「昵称 → 邮箱 → 微信用户」**：有昵称先显示昵称（那是用户自己的名字），
  没有就用邮箱（那是他要认的东西），都没有才用中性占位。`username` 退回存储层，
  只在下一次登录时被覆盖，不参与任何展示计算——头像首字也不再取它。
- **副标题不再回显邮箱**：邮箱已经占住标题位，副标题重复一遍就是噪音。现在它只说状态：
  微信临时账号 / 已绑定邮箱 / 邮箱未验证 / 已登录。
- **长邮箱要截断**：邮箱比用户名长得多，`ellipsis` 加在标题与副标题上，卡片里 `grow` 已有
  `min-width: 0`，不会把右侧标签挤出去。
- **验证**：`tests/test_r278_identity.py` 4 例静态锁（模板不得出现 `user.userId`/`user.username`、
  「账号 ID」文案不得回来、身份用邮箱表达、身份计算不碰 username）。
  最后一条是给自己的：注释里写「不显示账号 ID」也会被它抓到，所以那句注释改了措辞——
  宁可让锁严一点。

**台账总结**：`requests.md` 第 278 条本处回填；`response.md` 写入前 10 节，本次压回 10 节，
最旧一节 R267（重写 GitHub README）原样搬入 `response-archive/response-R267.md` 并登记索引。

## R281 · 报错要自己说清「是哪个 AppID 在跑」（2026-11-04）

**对 R281 的回应**：后台白名单配了、代码 appid 也是正式号，体验版仍报「请求域名未配置白名单」。

- **先确认事实**：代码里（主检出 `miniprogram/project.config.json` 与 develop）都是
  `wx7b31b435be6beae3`；开发者工具的项目记录读出来也是 `wx7b31b435be6beae3`。
  所以「代码用哪个 appid」这个问题本身是确定的，卡住的是另一件事——**白名单是按 AppID 存的，
  而代码里的 appid 不等于这个安装包上传时用的 appid**。改完文件没重新上传，或工具里项目还是旧号
  就上传了，都会出现「我明明配了」的错觉。
- **证据**：11-03 15:39 开发者工具曾把 `project.config.json` 改回旧测试号
  （`wxd511f98508dc9cee`），当时被我 stash 了。说明工具的项目 AppID 与文件内容会互相覆盖，
  「文件是对的」不等于「包里是对的」。
- **改法**：`runtimeAppId()` 从 `wx.getAccountInfoSync().miniProgram.appId` 取运行时 AppID
  （基础库 2.11.2+，取不到就容错返回空串，不影响请求逻辑），白名单报错直接写成
  「当前 AppID wx…：请为这个 AppID 添加 moon-well.haoshenqi.top」，`console.error` 同步带 appid。
  这样下一次报错会自己指认嫌疑人，不用再靠猜。
- **验证**：`tests/test_r281_runtime_appid.py` 3 例 + R277 的 4 例 → **7 passed**；`node --check` 通过。
  **未真机**：这条要重新上传体验版才看得到效果。

**台账总结**：`requests.md` 第 281 条本处回填；`response.md` 写入前 10 节，本次压回 10 节，
最旧一节 R269（顶栏信息架构收敛）原样搬入 `response-archive/response-R269.md` 并登记索引。

## R280 · 小程序接入 AI 伴读通用对话，生词本页下掉（2026-11-05）

**对 R280 的回应**：用户原话「微信小程序接入AI伴读（对话）功能，加载通用对话prompt。生词本功能下掉。」
三个口径先问清楚才动手：现网**没有**名为「通用对话」的 prompt（只有书内 `agent-chat-system`
与网页 `agent-chat-system-web`），用户拍板新建；「下掉」是删页面换 tab；对话复用现网 SSE。

- **为什么不能复用那两套 prompt**：书内模板要 `bookTitle` / `chapter` / `pageContext`，网页模板要
  「当前页面正文摘录」——小程序里既没有书也没有网页，套上去模型只能凭空编一个书名和一段页面原文。
  用户要的「通用对话」是第三种场景，所以新开 `agent-chat-system-general`（moon-well R243），
  正文明确「不假设用户手边有文本、不提书名章节页码」，并剔除批注 / 段落译文这类依赖书页的工具。
- **`scene` 是显式声明，不是靠 `bookId` 猜**：网页 Buddy 与 magiclens 也传 `bookId=null`，
  若把 null 当通用，会把网页场景一起改坏。故 `scene=general` 优先于老判定，空值 / 未知值原样回落，
  老客户端零改动。
- **小程序没有 fetch/EventSource**：走 `wx.request` 的 `enableChunked + onChunkReceived`。
  这里最容易翻车的是 UTF-8——分片按 TCP 边界切，一个汉字 3 字节、emoji 4 字节完全可能被切开，
  直接转会满屏乱码。所以自己写 `decodeUtf8(bytes, carry)`，凑不齐的字节留到下一块；
  再用 `\n\n` 分帧解析 `event:` / `data:`。静态锁里用 Node 故意切断汉字字节做实测，
  不只是 grep 代码里有没有函数名。
- **401 只在流开始前重试一次**：流一旦开始就回滚不了已发的 `delta`，重放会重复出字、重复计费。
  其余失败保留 `wx.request` 原始 `errMsg`（白名单 / 超时 / SSL 分开说），不抹成「请检查网络」。
- **删页面不能顺手删掉功能**：生词本页没了，挂在它上面的「微信临时账号」提示条也就没了——
  而这条提示是唯一告诉用户「换手机就找不回来」的地方。故迁到「我」页，`.shadow-tip` 样式迁到
  `app.wxss`；登录/账号/测试页文案统一改「网页端生词本」，避免指向一个不存在的入口。
- **Nacos 发布口径（上一轮卡住的点，已查清）**：公网 `nacos.haoshenqi.top` 是 v3 **console** 侧，
  `/v3/console/ai/prompt` 的 OPTIONS 返回 `allow=DELETE,OPTIONS`，POST 报
  `Request method 'POST' is not supported`；`publish` / `force-publish` 接 POST，`version` / `list` 只读
  ——**console 根本没有 create 写入口**。create 只存在于内网 8848 的 admin API
  （`/nacos/v3/admin/ai/prompt`，与仓内 `NacosPromptAdminClient` 同源）。所以不再从公网强写，
  按设计交给后端部署期的 `NacosPromptBootstrap` 自动 `create + publish`，上线后回读 online 版本与正文。
  **上线实况（2026-11-05 回填）**：push `develop` 自动触发 fnOS 发版链，10:13:04 后端部署 SUCCESS
  （blue→green healthy）；bootstrap create 成功但 publish 被 Nacos 审批流水线拦下
  `20002 Pipeline not approved: 1.0.0`，稍后手动 `publish` 返回 `code=0`，
  回读 `latestVersion=1.0.0` / `onlineCnt=1`、在线正文 851 字符与代码模板逐字一致。
  runtime 首次 `findTemplate` 拉在线模板并订阅推送，无需重启。
- **验证**：拉齐 R282 基线后小程序 R271–R282 静态锁 **52 passed**；`node --check` / JSON 解析通过。
  后端 R243 定向 + 上下文测试 **8 passed / BUILD SUCCESS**。全量 `pytest tests/` 在本机被
  SIGKILL，按开发态闸门只跑受影响子集，未冒充「全量通过」。
  **体验版已上传（2026-11-05 11:35）**：用户先在开发者工具「设置 → 安全设置」开启服务端口
  （端口 **13564**、CLI 访问令牌留空），`cli islogin` 返回 `{"login":true}`，随后
  `cli upload --project <主检出>/miniprogram -v 1.0.0 --port 13564` 成功，
  TOTAL **65.3 KB / 66,840 Byte**。两点留痕：① 上传源用主检出 `develop@6db0aba2`
  （含 R280 + R282），worktree 当时落后 10 个提交、缺 R282 的请求 URL 诊断；
  ② 带 `--info-output` 会触发 IDE `code 10 / 17 二维码输出路径无效或不存在`，
  去掉该参数即成功。`cli upload` 产生「开发版本」，体验版仍需后台「版本管理」指定。
  **真机 `enableChunked` 表现仍未验**，是唯一剩余验收待办。
- **部署顺序是硬的**：先 moon-well R243，再发小程序体验版。老后端不认 `scene` 会把通用对话
  落到网页伴读 prompt，用户会看到「当前页面正文摘录」这种小程序里不存在的东西。
- **状态**：**已上线待验收**（worktree `../magicbook-r280-ai-chat`，分支 `feat/r280-ai-chat`，
  已 merge 并 push `origin/develop`；后端 moon-well R243 于 10:13 上线、Nacos 新 prompt 在线；
  小程序体验版 `1.0.0` 于 11:35 上传成功，待后台设为体验版并真机验收。
  真机验收通过后本条才置 Completed、worktree 才清理）。
- **状态回写**：PingCode idea `MB-239`（`xB0tmxqa`，<https://haoshenqi.pingcode.com/ship/ideas/xB0tmxqa>）。
  本轮占号后漏建 idea，按 `ops/AGENTS.md`「状态必回写」于开发完成待验收阶段补建并置
  `In progress`；**验收通过后才置 `Completed`**，worktree 才清理。moon-well R243 是同源后端，
  按「后端跟随 magicbook、不单独建载体」共用这一条，不另建。
- **冲突记录**：开工后 `origin/develop` 前进了 R281（同改 `utils/api.js`），已 `git merge origin/develop`
  自动合并，两处函数（`runtimeAppId` 与 `chatStream`）共存、静态锁 46 例复跑通过，未撞号。
  `requests.md` 第 280 条占号标题原误写「R279」（R279 已被投稿书籍需求占用），本次按实际编号更正文字，
  编号本身不动。

**台账总结**：`requests.md` 第 280 条本处回填（含三口径、契约、部署顺序与验证结果）；
`response.md` 写入前 10 节，本次压回 10 节，最旧一节 R270（阅读器 bookUrl 大小写致 /show 404）
原样搬入 `response-archive/response-R270.md` 并在顶部登记索引。

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

## R284 · 恢复生词 hover 释义 + 页面引导入口下线（2026-11-06）

**对 R284 的回应**：用户看完上一轮排查后拍板「①恢复 hover 释义。页面上的引导入口全部下线掉。
只保留右上角的帮助的入口」。

- **先钉死「不是回归」**：线上 `magicbook.haoshenqi.top/static/js/reading/reader-core.js`
  与 `origin/develop@3413afa0` sha256 同为 `c9b4765c…`，R268 注入未丢。问号来自
  父页 `reader.css` 的 `cursor: help`（8/12 起就有），R268 才把它随波浪线注入 iframe；
  而 hover 释义自 R42 下线 `span.title`、R261 删掉残留注释后一直没恢复，两者叠加
  就是「只有问号、没有内容」。所以这次是**补回缺失的那半边**，不是修回退。
- **hover 释义**：`markVocabulary` 在 `record.gloss`（R236 词典中文首义项）非空时写
  `span.title`；不拼「上次：书 · 章节」（R42 下线理由），不复活 R139 删除的
  `translation`，词典无文档就不设 title。原生 tooltip 不依赖父页 CSS，iframe 内可见，
  与 R146 划词气泡让位、R261 行内小字开关互不干扰。
- **引导入口**：右上角 Help 下拉的 `#top_onboarding` 是唯一入口。断开 `runSegment`
  的自动邀请 / 右下常驻按钮与 `showEntryAgainIfNeeded` 的收尾重挂；删
  `/reading/settings` 引导区块与 `reading-preferences.js` 转发。
  `showInvite` / `showReaderHelp` 函数体保留但不再调用——R111/R226 视觉守卫仍锁其
  几何与文案形制，删除会让那批守卫失去锚点。`read.html` 的挂载点保留，导览从 Help
  启动后仍可跨页续到阅读器段。
- **文案同源**：收尾卡改指右上角 Help，`i18n_seed.html` + zh po/mo 同步；只重编译
  zh_Hans_CN 的 mo（整树编译会撞上 `it` 语既有的 `unknown named placeholder 'nome'`，
  与本轮无关，未动其它语言）。
- **验证**：新增 `tests/test_r284_hover_gloss.py` 4 例；更新 `test_reader_r226_acceptance.py`
  （R226 断言改为「调用链断开」）与 `test_onboarding_tour.py`（中文种子词条）。
  定向 **106 passed / 0 failed**，`node --check` 三个改动 JS 全过。**未真机**：
  hover 原生 tooltip 延迟与深色主题表现、从 Help 启动导览的跨页 handoff 待线上验收；
  开发态闸门下未跑全量。
- **状态**：开发完成待验收。worktree `../magicbook-r284-hover-gloss-onboarding`、
  分支 `feat/r284-hover-gloss-onboarding`，merge 后原样保留；**本轮未 push**
  （push `develop` 会触发 fnOS 自动部署，等用户点头）。修改意见按治理挂
  R268/R226 后续，不新建 PingCode idea。

**台账总结**：`requests.md` 第 284 条本处回填；`response.md` 写入前 10 节、本次 11 节，
按「写入即检查」把最旧一节 R274 原样搬入 `response-archive/response-R274.md`
并在顶部归档索引登记，窗口回到 10 节。冲突记录：无撞号；
唯一口径变更是 R226 的「阅读器右下使用引导」被 R284 取代，已在 L1/L3 标注。
