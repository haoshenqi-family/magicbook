# 对话回应记录

> 含每个需求的回应、冲突说明及两个文件的总结。
> **归档规则**：本文件仅保留最近 10 个 request 的回应；更早内容原样归档至 `response-archive/`（按 request 区间分文件），需要历史细节时按编号检索归档目录，不要读全量历史。

**归档索引**

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


## R267 · 重写 GitHub README：核心功能与入门用法（2026-11-02）

### R267（用户：「修改一下 github magicbook 和magiclens的 readme。把核心功能 入门用法讲明白」）

- **做了什么**：仓库根 `README.md` 原样是上游 Calibre-Web 的 README（徽章/安装/排障全是上游内容），整体重写为本仓产品 README：一句话定位 + 在线站点与邀请制、项目三件套表（magicbook / moon-well 私有 / MagicLens）、核心功能按 书库/阅读器/词汇/每日学习/AI 伴读/积分账号 六组、快速上手七步（登录→引导→词汇量定档→分级选书→查词听书→每日复习→可选装扩展）、架构 mermaid（ES/MinIO 缓存、NAS 本地 Qwen3-TTS、LLM 网关）、本地开发四行命令、fork 致谢与 GPL-3.0 声明保留。内容口径以 L1（`docs/product/readme/`）与功能地图为准，未新增能力描述。
- **push 决策（用户拍板）**：本地 develop 有 10 个未 push 提交（R262/R264/R265，前序会话「push 即自动部署待验收」留置），用户选择**连同一起 push 上线**。push 前按正式发布态闸门跑全量单测。
- **闸门（全量 1270 passed / 0 failed）**：首跑 1 failed——`test_auth_reader_covers_r225.py::test_permission_hints_are_compiled_into_chinese_catalog`。定性：**预存破损**（origin/develop 同样失败，非本批 10 个提交引入）：R257 改权限提示文案后，同文件顶部 `R225_MSGIDS` 仍列 3 条已被移除的旧串（`.po` 中已是 `#~` 废弃条目），断言 `.mo` 含其译文必红。修复=把断言列表对齐 R257 现行 4 条文案（`detail.html` 实测 + `.po` 激活译文逐条核对），`31e87b6e`。
- **上线**：`711f6065..4454e9f2` push `origin/develop`（含 R262 计费修正 / R264 BBC 原声近似高亮 / R265 积分站内信渲染 + README + 闸门修复），fnOS 链构建部署（含代码，不属 docs-only 跳过）；R263 此前已在线。**GitHub 落地页 README 显示的是 `master`**，README 提交 `4454e9f2` 经临时 worktree cherry-pick 至 master（`a712694c..5b01c880`，只带 docs 提交，未做 792 提交的正式发布 merge——master 上另有 2026-09-08 两个旧提交，正式合并留作单独发布决策）。
- **台账顺手处置**：① 本次 merge origin/develop 时发现 requests.md 内嵌**上次 merge（6bd15ec7）提交时残留的冲突标记**（HEAD vs feat/r264 嵌套块），已在合并解决中清掉，264 完整条目去重为一次；② 发现 **258 编号重复**（占号条与完成条并存）为两边既有历史，按「不修改既有记录」纪律未动，留此存证。
- **magiclens 同题**：用户同指令改 magiclens README，见 magiclens 仓 response.md R58（随 r57 一起 push develop，未触发 Release）。
- **追加（同日用户指令「都 push 到 master」）**：执行正式发布合并——临时 worktree `../magicbook-r267-release-master` 内 `merge origin/develop` 成 `61deacf7` push `origin/master`（`5b01c880..61deacf7`），master 从落后 792 提交变为全量发布态。冲突裁决：`epub.js` 以 develop 为准（master 独有的 2026-09 `a712694c` 章节标题修复已被 develop `currentChapterTitle()` 取代，生产数月即跑此实现，复活旧补丁会双写且偏离已验证行为）；`docs/reading-vocabulary.md` 按 develop 删除（已迁 `docs/product/`）。README 两侧同内容自动归一。合并点全量单测 **1273 passed / 0 failed**（含并行 R268 新增 3 条）。同轮事实：magiclens 无 master 分支（landing=develop 已生效，遗留 main=init 骨架落后 94 提交未动）。

- **总结**：requests.md 条目 267 已回填；R254 回应整节搬至 `response-archive/response-R254.md` 并登记行内索引，本条写入后窗口 10。冲突记录：requests.md 与 origin/develop 台账冲突已按并集解决（本地完成条 + 远端 266/267 占号行）。


## R269 · 顶栏信息架构收敛：搜索/上传只在书库、任务列表归管理、语言与注销归账号（2026-11-02）

### R269（用户：「搜索只在书库有就可以了其他四个主入口不要。同样的上传书籍也是。最右边的用户跟主用户重复了，是相同的功能，还有注销按钮，和语言按钮，只放到账号中。任务列表只放到管理权限中。右上角只留帮助按钮」）

- **结论先行**：顶栏从「全站工具栏」改成「按域说话」——搜索与上传只在书库域出现，右上只剩帮助；语言、注销归账号页，任务列表归管理页头。判定用 `current_domain` 而不是页面白名单，跟着 R251 的域归属一起漂移才不会二次分叉。
- **搜索与上传（书库域专属）**：`layout.html` 的搜索表单与 `#form-upload` 各加一个 `current_domain == 'library'` 条件；上传保留原来的 `role_upload()` + `g.allow_upload` 双重门控。书库首页 `/`、各 Browse 页、`/search`、`/advsearch`、`/book/<id>`、`/shelf/*` 都算 library，所以「在书库里随时能搜、能传」的体验没变，只是不再跟着你去首页、学习、账号、管理。
- **右上只留帮助**：删掉登录态的 `#top_user`（用户名链接，和「账号」一级域同一件事）与 `#logout`。匿名分支保留一个登录入口——`g.allow_registration` 关掉时下方 login/register 不渲染，它是唯一去处，不能一起删。
- **语言与注销归账号**：顶栏 `#top_language` 整块撤掉（含 R257 方案六的「更多语言」折叠菜单，元素没了开关也一并删）；语言继续用 `/me` 的 `#me-language` 面板（全量语言 `<select>` + 书籍语言）。注销在 A1 资料面板下新增 `#me-logout`，复用既有 msgid `Logout`/「注销」，零新词条。
- **任务列表归管理**：顶栏 `#top_tasks` 删除；`ADMIN_L2_GROUPS` 的「系统」组首位新增 `admin-tasks`（M8，`/tasks`），管理页数 13 → 14（M9–M14 顺延）。`/tasks` 进 `ADMIN_PATH_PREFIXES`，管理员在任务页会点亮「管理」并在 L2 上看到高亮。
- **权限边界（本轮特别处理）**：`/tasks` 的访问权限没动（仍是 `user_login_required`），普通用户从书签直达仍可用自己的任务页；但管理域 L2 加了 `current_user.role_admin()` 守卫——否则非管理员会在 `/tasks` 上看到一串点进去就 403 的管理链接。
- **测试**：新增 `tests/test_topbar_ia_r269.py` 14 例（书库域有/其他三域无 `#query`+`#form-upload`；登录态顶栏无 `top_tasks/top_language/logout` 且保留帮助；`/me` 有 `me-logout`+`me-language`；管理员 `/tasks` 有 `admin-tasks` 且点亮管理域；普通用户 `/tasks` 拿不到管理链接）。三处旧契约演进而非删断言：R212 语言入口改断「顶栏无、`/me` 有」，R257 方案八/方案六改断「表单在账号域、折叠菜单下线、`next` 白名单仍在」，R251 管理 L2 计数 13 → 14 并补 `/tasks` 归属。定向 8 个文件 **121 passed**；全量 `pytest tests/` **1287 passed / 0 failed**（默认沙箱 tmp 会让 69 个 `tmp_path` 用例 `FileExistsError`，改 `TMPDIR` 后全绿，与本轮改动无关）。
- **文档四问**：能力 → L1 `readme/library.md`（顶栏控件跟域走）、`readme/account.md`（A1 含注销 + 语言/注销只在此页）、`readme/admin.md`（14 页 + 任务列表条）；契约 → 无 HTTP 契约变化，导航契约进 L3 `library/features/ui-information-architecture.md` 新增 §5「顶栏控件归属」；实现/边界 → 同 L3（非管理员 `/tasks`、匿名登录分支、上传模态降级）；本次实现 → `docs/project/iterations/1.0/r269-topbar-ia/lld.md`；需求基线 → `library/requirements.md` R269 条 + `REQUIREMENTS.md` 变更记录。
- **未做 / 留给验收**：主题 1（CaliBlur）只在头像下拉里删了注销一项，其余皮肤结构不动（`caliBlur.css` 有大量 `#main-nav > li:nth-child(n)` 定位，动结构风险高于收益）；普通用户失去任务列表的顶栏入口是有意为之，如果还想让他们看到自己的任务队列，再单独加一条。
- **状态与驻留**：**已上线待验收**。用户 2026-11-02 21:42 指令「push」后推 `origin/develop`（`fc3a9154..066bb8e9`，含实现 `49406fe8` + merge `066bb8e9`），fnOS 链自动构建部署；线上核验：`/static/js/main.js` `last-modified 2026-11-02T13:42:54Z`（即部署时刻）、已无 `mb-lang-more-toggle`，`/static/css/style.css` 已含 R269 注记，站点 `/` 302 → `/login`（应用在服务）。worktree `../magicbook-r269-topbar-ia`，分支 `feat/r269-topbar-ia`，按闸门保留待验收。
- **窗口与总结**：写入前窗口 10 节，新增后 11；按「写入即检查」把最旧 R255 整节原样搬至 `response-archive/response-R255.md` 并登记索引，窗口恢复 10。requests.md 条目 269 已从占位回填。冲突记录：无撞号（claim.sh 对 `origin` 台账算号得 269）。

## R270 · 阅读器 bookUrl 大小写致 /show 404——首页继续阅读打开空白阅读器（2026-11-03）

### R270（缺陷：截图/视频会话中生产实测发现，R229 同款「顺路修复」）

- **结论先行**：`read.html` 的 `bookUrl` 单点加 `|lower`，一行修复 + 两条静态锁定测试。首页「继续阅读」卡片（R213-C 透传阅读进度里的大写格式 `EPUB`）从此不再打开永久空白的阅读器。**已上线待验收**。
- **发现链**：2026-11-03 产品视频录制会话，puppeteer 打开 `/read/145/EPUB`（与首页继续阅读卡片同款链接）epub.js 永不渲染（0 个 iframe）。逐层定位：`/show/145/EPUB/file.epub` → 404（Flask 页），`/show/145/epub/…` → 200（Matilda 2.3MB）；匿名直连容器两种写法都 302（路由都在、非权限问题）；容器内文件 `Matilda - Roald Dahl.epub` 小写扩展名在盘。
- **根因**：`serve_book`（web.py:2050）在大小写敏感文件系统上按 **URL 段原样**拼扩展名（`send_from_directory(..., data.name + "." + book_format)`）。Calibre 落盘扩展名恒小写；`/read/<id>/<book_format>` 的入口里，home.html:22 把进度记录的大写 `EPUB` 原样透传，read.html:186 再透传给 `url_for('web.serve_book')` → 找 `<name>.EPUB` → NotFound → epub.js 拿不到书文件 → 阅读器空白。detail.html 的「首章试读」（`|lower`，L179）与「继续阅读」（`or 'epub'`，L515）两条入口是对的——所以从详情页进阅读正常、从首页卡片进就空白，hsq 日常走详情页入口躲过了它，隐患存活至今。上游引入点是 2024-12-08 `01215aaa`（KEPUB 支持）把字面量 `'epub'` 换成了变量透传。
- **修复**：`cps/templates/read.html` bookUrl 一处 `book_format=book_format|lower`——所有阅读入口共用此模板，单点收口；epub.js `restore:true` 的 IndexedDB 缓存键也随之统一为小写，跨入口命中同一缓存。未动 `serve_book`（保持与上游贴合，URL 侧收口最小）。
- **测试**：新增 `tests/test_reader_bookurl_case_r270.py` 2 例（正向锁定 `|lower` 形态 + 防回退断言「不许再出现原样透传」）；全量 **1274 passed / 0 failed**（1273 基线 + 1 新文件）。
- **上线与核验**：实现 `600fe72b` + merge `276f77ee` 推 `origin/develop`（32e32f58..276f77ee），fnOS 链 `00:06` END OK（`af1cd8f0f78ed85b`），容器 healthy；线上核验 `/read/145/EPUB`（大写入口）渲染出的 bookUrl 已是 `/show/145/epub/file.epub` 且 GET 200、epub iframe 正常渲染（本会话视频/截图全走通）。
- **连带效应**：与 10-28 未结案的「整本朗读后正文空白」（wholebook-whitescreen）是否同源**未证实**（该案症状是「开始朗读后」空白，本案是「打开即空白」），留给原案复测时排除。
- **状态与驻留**：worktree `../magicbook-r270-reader-bookurl-case`，分支 `fix/r270-reader-bookurl-case`，按闸门保留待验收。requests.md 条目 270 已回填。冲突记录：无（claim.sh 得 270）。

## R271 · 微信小程序：生词本 / 每日复习 / 词汇量测试 / 学习数据（2026-11-03）

**对 R271 的回应**：按「工具型、最低、全是标准列表交互」的口径交付一个原生微信小程序，只做四页，
阅读留在网页。

- **边界先钉死**：不渲染任何正文。阅读需要长注意力与大屏，塞进小程序只会得到更差的阅读器；
  而这四件事正好是「掏手机刷几张卡」的动作。这条写进了 L1 与 LLD，避免后续被「顺手加个阅读吧」拉扯。
- **为什么直连 moon-well**：网页端的 `/ajax/*` 代理依赖 Flask 会话（OIDC 登录态），小程序没有；
  而数据本来就在 moon-well（生词本、复习调度、测试、四股台账），网页只是薄代理。直连少一跳、少一处
  会话依赖，代价是要把 `moon-well.haoshenqi.top` 加进小程序后台的 request 合法域名。
- **登录**：微信身份 + 一次账号绑定（AppID `wxd511f98508dc9cee`）。首次绑定要求输入网页端账号密码
  ——不新建账号，否则生词本与复习进度会劈成两半。绑定后免密，token 落 storage、401 自动续期一次。
- **四页**：生词本（筛选带角标 / 前缀搜索 / 上滑加载 / 点词改标记）、复习（四选一·拼写·回忆三态，
  始终回传后端下发的原始题型，因为它是四技能统计的底座）、词汇量（作答→交卷确认→报告→推荐难度
  一键应用）、数据（四股 / 复习摘要 / 近 7 天 / 最近词汇量）。
- **工程位置**：`magicbook/miniprogram/`，原生小程序、无框架、无云开发；`baseUrl` 收在 `config.js`。
  **不参与容器构建**（不被 Dockerfile COPY、`cps/` 不引用），push develop 不会把它带上线；上线走
  微信开发者工具上传提审。
- **验证如实记录**：全部 `.js` 过 `node --check`、全部 `.json` 过 `JSON.parse`、接口路径与 DTO 字段
  逐项比对；**本机未装微信开发者工具，因此没有编译/模拟器/真机验证过**——首次打开需关注
  tabBar（纯文字无图标）与 WXML 表达式（`counts[item.key]`、三元嵌套）这两处。
- **依赖**：后端 moon-well R239（两步式微信登录 + `GET /vocabulary/notebook` 分页）——**已上线**
  （容器 `sha=6c1433cd`，`/auth/wx/login` 与 `/vocabulary/notebook` 均已生效）。只差人工把 Nacos
  `app.wx.secret` 从占位换成正式 AppSecret；发布即生效、无需重启（已双向实测）。
- **状态**：**已上线待验收**（worktree `../magicbook-r271-miniprogram`，分支 `feat/r271-miniprogram`，
  保留待验收）。`dc3c6ce3` 已推 `origin/develop`，fnOS 构建完成、容器 `sha=dc3c6ce3`、站点 302 正常。
  小程序源码不进镜像，因此对网页服务只是文档级变化；小程序对外可见仍需微信开发者工具导入后
  「上传 + 提审」。真机验收时重点看 tabBar（纯文字无图标）与 WXML 表达式两处。
- **冲突记录**：无撞号（本体 R271，后端 R239）。未触碰 calibre 原生代码，与待验收的 R270/R269 等
  条目无文件交集（本仓既有改动全在 `cps/`、`tests/`，本次只新增 `miniprogram/` 与文档）。

**台账总结**：`requests.md` 新增并回填 R271；`response.md` 写入前窗口已 11 节，本次连同新增压回
10 节，R256/R257 两节原样搬入 `response-archive/response-R256-R257.md` 并在顶部登记索引。

## R272 · 小程序账号体系：自动建号 + 账号页（绑定邮箱 / 认领老账号）（2026-11-03）

**对 R272 的回应**：R271 的登录要求「首次必须输网页端账号密码」，把第一次用小程序的人
挡在一张他没有密码可填的表单前。本次改成「先给一个能用的账号，再用邮箱认领」。

- **登录页两条路**：主按钮「微信一键登录」→ 后端未绑定即自动建**微信临时账号**并直接进主界面
  （`doLogin(false)`）；次按钮「我已有账号，用密码绑定」→ `linkExisting=true` 只拿票据，
  输密码后绑到老账号（`doLogin(true)`），不产生空账号。两条路写反会让新用户看到密码表单，
  静态锁专门守这两个调用。
- **账号页 `pages/account`**：显示当前身份（微信临时账号 / 已绑定邮箱）、绑定邮箱表单（发码 →
  60 秒倒计时 → 输 6 位码）、退出登录。归并成功后用 `auth.persist(新 token)` **整份替换**本地
  登录态——归并后 userId 变了，沿用旧 token 会「登录着但数据全空」。
- **50512 必须二次确认**：临时账号里已有数据时后端返回摘要（如「生词本 12 条」），
  前端弹 `wx.showModal` 摆出后果，用户点「放弃并合并」才带 `discardShadowData=true` 重提。
  默认拒绝丢弃：用户背过的词不该被一次点击抹掉。
- **提示条不抢首屏**：生词本页顶部一条窄提示（仅临时账号显示），点进账号页；数据页页尾加
  「账号与绑定」入口。没做成强制拦截弹窗——工具型小程序的第一次体验不该被表单打断。
- **部署顺序**：必须**先发 moon-well R240、再发小程序**。旧后端（R239）会对主按钮回
  `bindRequired=true`，新用户会被带到「绑定已有账号」表单（旧版行为），不会数据错乱但会卡住；
  小程序本身有审核周期，先发后端天然安全。
- **验证**：新增 `tests/test_r272_account.py` 7 例静态锁（账号页四件套与注册、登录页两条路径
  不写反、`linkExisting` 透传、邮箱端点路径、50512 二次确认、归并后换 token、临时账号提示条），
  与 R271 的 7 例一起 **14 passed**；全部 `.js` 过 `node --check`、全部 `.json` 过 `JSON.parse`。
  **本机仍无微信开发者工具，未编译、未真机**——首次打开重点看账号页倒计时与 50512 弹窗文案换行。
- **状态**：**开发完成待验收，未 push**（worktree `../magicbook-r272-account`，分支 `feat/r272-account`）。
- **冲突记录**：未撞号（本体 R272 / 后端 R240）。改动只在 `miniprogram/`、`tests/`、文档，
  不碰 `cps/` 与 calibre 原生代码，与待验收的 R269/R270/R271 无文件交集。

**台账总结**：`requests.md` 第 272 条本处回填；`response.md` 写入前 10 节，本次压回 10 节，
最旧一节 R259（设置页生词提示语对齐 moon-well R232）原样搬入 `response-archive/response-R259.md`
并登记索引。

## R273 · 小程序登录页：密码绑定改为邮箱验证绑定（2026-11-03）

**对 R273 的回应**：用户要求「已有网页端账号不要用密码绑定，直接用邮箱+验证码」。
配合 moon-well R241 的未登录态邮箱验证，登录页第二入口整条换掉。

- **流程**：点「我已有账号，用邮箱登录」→ `auth.login(true)` 只拿 10 分钟票据（**不建号**）→
  填邮箱 → 发码 → 6 位码 → `/auth/wx/email/verify` → 直接登进老账号，同时把当前微信绑上去。
  全程不出现密码输入框。
- **三态状态机** `idle / email / code`，倒计时取后端 `resendAfter`，不硬编码 60 秒。
- **两个必须回收的错误**：`50514`（该邮箱没有账号）回 `idle` 并提示去用微信一键登录建号；
  `50403`（票据过期）同样回 `idle` 刷新——不回收的话用户会拿着废票据反复点，得到的是同一个错。
- **删掉的东西**：登录页的用户名/密码输入与处理逻辑全部移除。后端 `/auth/wx/bind` 端点保留
  （兜底能力，界面不暴露），理由写进 LLD：存量账号里有人没有邮箱，将来若需要密码认领，
  端点还在，不必再发一次版。
- **测试**：新增 `tests/test_r273_email_login.py` 4 例静态锁（登录页不得再有密码框、三态齐全、
  邮箱入口不得走建号分支、端点与 50514/50403 处理），并同步修正 R272 的两条断言；
  与 R271/R272 合计 **18 passed**；全部 `.js` 过 `node --check`、`.json` 过 `JSON.parse`。
- **验证边界**：本机无微信开发者工具，**未编译、未真机**。首次真机重点看：邮箱表单的键盘遮挡、
  验证码倒计时与「重新发送」的互斥。
- **部署顺序**：先 moon-well R241（含 `r241-email-scope.sql`），再发小程序。
  旧后端没有 `/auth/wx/email/*`，点了会 404。
- **状态**：**开发完成待验收，未 push**（worktree `../magicbook-r273-email-login`，分支 `feat/r273-email-login`）。

**台账总结**：`requests.md` 第 273 条本处回填；`response.md` 写入前 10 节，本次压回 10 节，
最旧一节 R258（设计方案五充值卡五段式）原样搬入 `response-archive/response-R258.md` 并登记索引。
