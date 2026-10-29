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
- `response-archive/response-R230.md`：R230 个人学习数据导出入口与任务下载 UI——2026-10-29 R241 写入使窗口达 11 节，原样搬移不改写；R247 轮转把原误置于 R234 后的 R230 验收清理段归回本节
- `response-archive/response-R232.md`：R232 伴读面板不再显示 token 用量——2026-10-29 R243 合并 R244 后窗口达 11 节，原样搬移不改写
- `response-archive/response-R233.md`：R233 AI 回复中的本站链接可点击并在新窗口打开——2026-10-29 R246 写入使窗口达 11 节，原样搬移不改写
- `response-archive/response-R234.md`：R234 悬浮球快捷动作 AI 对话恒首位——2026-10-29 R247 写入使窗口达 11 节，原样搬移不改写
- `response-archive/response-R236.md`：R236 弹层恢复「整本任务」入口——跳完整详情页的普通链接（2026-10-29 R248 写入触发轮转搬移，原样搬移不改写）。
- `response-archive/response-R237.md`：R237 整本朗读 proxy 三元组解包 + 白屏修复与部署重启后的「继续」恢复入口——2026-10-29 R249 写入触发轮转搬移，原样搬移不改写。
- `response-archive/response-R238.md`：R238 全文单词详解预览卡死——所有书共有的 jQuery 顺序缺陷 + 后台预计算（2026-10-29 R252 写入触发轮转搬移，原样搬移不改写）。

---

> 归档索引：[response-R01-R31.md](response-archive/response-R01-R31.md) · [response-R32-R49.md](response-archive/response-R32-R49.md) · [response-R50.md](response-archive/response-R50.md) · [response-R51-R70.md](response-archive/response-R51-R70.md) · [response-R70-R80.md](response-archive/response-R70-R80.md) · [response-R81-R101.md](response-archive/response-R81-R101.md) · [response-R102-R110.md](response-archive/response-R102-R110.md) · [response-R111-R119.md](response-archive/response-R111-R119.md)（2026-10-08 R129 补账搬移）· [response-R120-R125.md](response-archive/response-R120-R125.md)（2026-10-08 R135 写入触发搬移，含 R134 登记的窗口欠账补账）· [response-R126-R131.md](response-archive/response-R126-R131.md)（2026-10-09 R141 写入触发轮转搬移）· [response-R132-R133.md](response-archive/response-R132-R133.md)（2026-10-10 R143 写入触发轮转搬移） · [response-R134.md](response-archive/response-R134.md)（2026-10-10 R144 写入触发轮转搬移） · [response-R135-R137.md](response-archive/response-R135-R137.md)（2026-10-10 R147 写入触发轮转搬移，含 R145/R146 两次写入的窗口欠账补账） · [response-R138.md](response-archive/response-R138.md)（2026-10-11 R152 写入触发轮转搬移） · [response-R139.md](response-archive/response-R139.md)（2026-10-11 R153 写入触发轮转搬移） · [response-R140.md](response-archive/response-R140.md)（2026-10-11 R153 复核后的补搬——R152 写入时搬走 R138 后窗口仍为 11） · [response-R141-R142.md](response-archive/response-R141-R142.md)（2026-10-11 R155 集成时窗口超限搬移） · [response-R144-R153.md](response-archive/response-R144-R153.md)（2026-10-12 R161 写入触发轮转搬移，清并行欠账 R144–R153） · [response-R154.md](response-archive/response-R154.md)（2026-10-12 R165 写入触发轮转搬移） · [response-R155-R156.md](response-archive/response-R155-R156.md)（2026-10-13 R166 写入触发轮转搬移，含同日同编号「细筛」那条） · [response-R157.md](response-archive/response-R157.md)（2026-10-13 R166 分支 merge origin/develop 后窗口仍达 11，续搬最旧一节） · [response-R156-mic.md](response-archive/response-R156-mic.md) · [response-R158.md](response-archive/response-R158.md)（2026-10-13 R168 写入触发轮转搬移）（2026-10-13 R167 写入触发轮转搬移；与 response-R155-R156.md 里的同编号「细筛」条目不同事） · [response-R160-R164.md](response-archive/response-R160-R164.md)（2026-10-14 R172 写入触发轮转搬移，窗口转入 R161 起） · [response-R161-R162.md](response-archive/response-R161-R162.md)（2026-10-14 R173 写入触发轮转搬移，窗口转入 R165 起） · [response-R165-R173.md](response-archive/response-R165-R173.md)（2026-10-15 R183 写入触发轮转搬移，窗口转入 R174 起） · [response-R174-R177.md](response-archive/response-R174-R177.md)（2026-10-16 R185 写入触发轮转搬移，窗口转入 R178 起） · [response-R175.md](response-archive/response-R175.md)（2026-10-16 R188 写入触发轮转搬移） · [response-R214-C.md](response-archive/response-R214-C.md)（2026-10-25 R229 写入触发轮转搬移：R214 子项 C 整本任务代价面板；与既有 response-R214.md（子项 A）不同事） · [response-R238.md](response-archive/response-R238.md)（2026-10-29 R252 写入触发轮转搬移，原样搬移不改写）

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
- **分享链接增补（2026-10-29）**：卡密操作拆为「复制卡密」「复制并分享」。分享链接为 `/credit-card/share#key=...&credits=...`，bearer key 只走 fragment，不进入服务端请求、反向代理和访问日志；分享页公开但禁缓存/索引/Referer，展示三步兑换说明且不自动兑换。已登录用户直达积分页并自动填充，匿名用户登录后从同标签页 `sessionStorage` 恢复。生产核验发现 Flask `_external=True` 生成 `http://`，改为模板下发相对路径、前端按当前 origin 组装。定向与契约回归 35 passed，两个前端脚本 `node --check` 与 `git diff --check` 通过。
- **分享发布验证（2026-10-29）**：GitHub webhook 本轮未投递，按 runbook 手动补跑构建；提交 `79261d2b` 构建 `END OK`、app-manager `deploy SUCCESS`，容器 `running/healthy` 且 `house.build-sha=79261d2bc53956e922934f625e421d966b59c50a`。生产 `/credit-card/share` 返回 200 与三项安全头；测试卡密页面显示金额、卡密、复制按钮和「登录→粘贴→兑换」三步说明；点击「去积分页兑换」后 URL 为无 fragment 的 `/credits`，兑换框已自动填入，未点击兑换、未消耗卡密。分享基地址实测为 `https://magicbook.haoshenqi.top/credit-card/share`。
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

**对 R243 的回应**：前端已完成并上线，与 moon-well R228 后端组成完整的**伙伴邮差 + 持久站内信**链路；当前处于**已上线待用户真机验收**。

- **代理与契约**：新增 `cps/routes/mail.py` 四条 `/ajax/mail/*` 薄代理，统一登录门禁并保持 `_moonwell_proxy` 三元组；`pageNo/pageSize` 本地归一，`read` 只透传正整数 id，不接收或猜测 `userId`。管理员积分代理透传 `notify` 与 `notificationMessage`，既有字段不变。
- **统一状态层**：`MBMail` 作为 FAB、设置菜单、抽屉页签和 `/mail` 的唯一未读来源，支持初始化、页面可见、窗口聚焦、打开 Mail 页签与 `pageshow` 刷新，不设 `setInterval`。数字 badge 只在成功取得计数时展示；列表加载失败只影响列表局部，保留最近一次成功未读供 FAB 信封判断，不把全局状态误降级为空。
- **伙伴与抽屉**：Buddy FAB 增加 `pointer-events:none` 信封角标，不另盖点击层；抽屉关闭时有未读进 Mail、无未读进 Chat，抽屉已打开仍按原行为关闭；“对话”快捷气泡始终显式进 Chat。AI 抽屉新增 Chat/Mail 双页签，Mail 展示最近 5 封，展开单封才已读，提供全部已读与“查看全部”，打开页签本身不标已读。
- **独立邮件页**：新增登录保护的 `/mail`，倒序分页、单封展开/已读、全部已读、空态、加载态、错误态与重试；正文按结构化参数本地化，服务端字符串只作文本节点，不拼 `innerHTML`；跳转严格限定 `/buddy`、`/achievements`、`/credits`。已解决邮件保留历史但不计未读。
- **设置与管理员**：设置菜单新增 `top_mail` 与未读 badge；积分管理员表单新增“同时发送到账通知”和可选纯文本正文，负数时禁用并清空，成功后与 FAB/设置/抽屉同步计数。`layout`、`read`、`readtxt`、`readpdf` 均已接入；`readcbr` 当前未挂 Buddy 面板，本轮明确不扩展。
- **验证**：合并最新基线后正式发布态全量 **1109 passed / 0 failed / 4 warnings**；合并前邮件/积分/API/i18n/Buddy/阅读器两批定向回归合计 **172 passed / 0 failed**；合并 R244 后重跑 **137 passed / 0 failed**，另 R233 链接/阅读器结构 **19 passed**。`node --check cps/static/js/mail.js`、`ai_chat.js`、`credits.js` 与 `git diff --check` 均通过。moon-well R228 后端全量 **1663 tests** 全绿。
- **文档四问**：能力 → `docs/product/readme/companion.md`；契约 → `docs/product/companion/interface.md`；实现/边界 → `docs/product/companion/features/mail-inbox.md`；本次实现 → `docs/project/iterations/1.0/r243-mail-inbox/`（HLD/LLD/AC 已回填“前后端已实现，待验收”）。
- **R244 语义合并**：再次合并 `origin/develop` 时吸收 R242 收银台和 R244 伙伴隐藏/收信动画。`ai_chat_panel.html` 同时保留 R243 信封/页签与 R244 隐藏、唤回、飞信节点；`ai_chat.js` 的 `openDrawer(tab)` 保留 R243 页签分流并清理 R244 一次性角标；`credits.js` 同时保留 R243 i18n 与 R242 滚动提示。R243/R244 交界采用“同一未读、按可见性映射”：可见 FAB 只显示 R243 信封，伙伴隐藏后显示唤回药丸红点，避免重复提示；信封移到左上避让右上隐藏 ✕。详见 R243 LLD §4.4。
- **发布状态**：merge/push `af9987bb`（`9c6c76dd..af9987bb -> develop`）；fnOS `build END OK`，镜像 `house.code-digest=aafe102a754b1001`，容器 `running/healthy`。生产 `/home` 返回 200；匿名 `/mail` 与 `/ajax/mail/unread-count` 均按预期 302 到登录页。部署时 drift-check 与 webhook 同 sha 双触发，首个 deploy 因容器名竞争失败，构建链自动重试后成功；最终容器 label 与目标 commit 一致。
- **状态与驻留**：worktree `../magicbook-r243-mail-inbox`，分支 `feat/r243-mail-inbox`；实现 `82688cd2`、列表失败隔离修复 `78581165`、前次基线合并 `bf4b6e1a`、R244 合并 `a241f287`、最新基线合并 `79e66e40`、发布提交 `af9987bb`。R243 已上线待用户真机验收；worktree 按验收闸门保留，验收后再清理。
- **窗口与总结**：本条写入时窗口 10 节；合并 R244 后增至 11，按「写入即检查」把最旧 R232 原样搬至 `response-archive/response-R232.md`，窗口恢复 10，并合并 R229/R231 的并行重复索引。requests.md 条目 243 已回填；冲突记录：无撞号，magicbook R228 为另一条既有需求，与本功能无关。

## 2026-10-29（R246：整本任务进度条补齐任务类型与状态）

### R246（用户：「进度条什么都不显示，不知道是哪个任务的进度条」）

- **结论先行**：已修复并上线待验收。截图的 `735 / 990` 是全文单词详解任务；进度条并非没有数据，而是左侧任务标题取空，只剩百分比与计数。
- **根因**：R214 子项 C 的进度标题复用按钮文案 `t('start-' + kind)`。详解的 `kind` 是 camelCase `wordDetail`，但浏览器把 `data-t-start-wordDetail` 属性名解析成小写 `data-t-start-worddetail`，键名不一致使 `t()` 返回空串；即使补上小写，按钮动作「打开详解页面」也不是任务名。
- **修复**：模板新增独立的 `data-t-progress-kind-{translate,tts,worddetail}` 与四种状态句式；`renderProgress()` 先将 `kind` 小写化，再渲染「全文单词详解 · 进行中」等标题，并对缺键保留回退，避免未来新增链路再次出现空标题。三条整本 job 的端点、轮询频率、缓存与计费均未改。
- **测试**：新增 `test_progress_title_names_task_and_status`，钉住三类任务名、四种状态句式、小写化与缺键回退；定向回归 10 个相关文件 **155 passed / 0 failed**，`node --check cps/static/js/whole-book-panel.js` 与 `git diff --check` 通过。
- **文档四问**：能力 → L1 `docs/product/readme/library.md` 补进度条标识说明；契约 → 无变化；实现/边界 → 新建 L3 `docs/product/library/features/whole-book-progress.md`；本次实现 → R214 LLD §18 与 AC C10。需求基线、迭代 `plan.md`、requests.md R246 已同步。
- **上线**：实现 `fad1be71` 已推 `origin/develop`；fnOS `build END OK`，app-manager `deploy SUCCESS`，容器 `running/healthy` 且 `house.build-sha=fad1be7155fec3c4ff30f1b18bdcf0c6d9b99521`。生产静态 JS 与镜像内模板均已确认包含 `progress-kind-*`、`progress-running` 和 `kind.toLowerCase()`。
- **真机验收点**：管理员打开任意书详情页，运行任一整本任务；吸顶进度条应分别显示「整本翻译 / 整本朗读 / 全文单词详解 · 进行中」，结束后显示已完成、有失败段落或已取消。截图对应的详解任务应显示「全文单词详解 · 进行中」。
- **窗口与驻留**：写入前 10 节，新增后达 11 节；按「写入即检查」把最早 R233 整节原样搬至 `response-archive/response-R233.md` 并登记索引，窗口恢复 10。worktree `../magicbook-r246-wholebook-progress-label`（分支 `fix/r246-wholebook-progress-label`）按闸门保留待验收，验收通过后删除。
- **总结**：requests.md 条目 246 已从占位回填；本条为回应。冲突记录：无撞号。

## 2026-10-29（R247：归档书内容速览误报 `book is unavailable`）

### R247（用户：「报错了」；截图为归档书 `/book/145` 的内容速览错误）

- **结论先行**：已修复，归档书不是数据损坏。`/book/145` 的详情页明确允许查看归档书，但内容速览复用了整本任务默认的取书过滤，导致同一本书在详情页可见、在内容速览中却报 `book is unavailable`；影响所有归档 EPUB。
- **根因**：`show_book()` 使用 `get_book_read_archived(..., allow_show_archived=True)`；内容速览的 `reading_insight.service._book_file()` 则调用 `JobServiceBase._book_file()` 的默认路径，最终走到 `calibre_db.get_filtered_book(book_id)`，默认排除归档书。内容速览、AI 简介、估算、活跃批次和缓存标识共用这个入口，所以错误不只出现在首屏解析。
- **修复**：`JobServiceBase._book_file()` 新增可选参数 `allow_show_archived=False`；默认分支保持原调用，整本翻译/朗读/详解边界不变。内容速览入口显式传 `allow_show_archived=True`，与详情页可见性对齐，一次覆盖速览、简介、估算、活跃批次与缓存标识。
- **测试**：新增 `test_archived_book_can_build_insight`，从生产同款 `book is unavailable` 红灯转为成功生成章节；新增 `test_book_file_default_keeps_archived_filter_for_whole_book_jobs`，确认整本任务仍排除归档书。内容速览、详情、估算、缓存标识与三条任务链路相关回归 **174 passed / 0 failed**；后续执行 `git diff --check`。
- **文档四问**：能力 → L1 `docs/product/readme/library.md` 明确归档书仍可看内容速览；契约 → 无变化；实现/边界 → 新建 L3 `docs/product/library/features/book-insight.md`，并修正缓存标识 L3 的归档口径；本次实现 → R214 LLD §19、AC B9、R214 需求基线与迭代 `plan.md`。
- **驻留**：worktree `../magicbook-r247-archived-insight`（分支 `fix/r247-archived-insight`）按闸门保留待用户验收；挂 R214 修复，不建独立 idea。
- **生产验收**：修复已随 `dfe30ed4` 上线，容器 `running/healthy`。刷新生产 `/book/145` 后，原 `内容速览解析失败：book is unavailable` 已消失，简介、目录（5 章 / 1393 段）与首章试读正常显示；同一页的整本任务进度条显示「全文单词详解 · 进行中」。
- **窗口与总结**：写入前 10 节，新增后达 11 节；按「写入即检查」把最早 R234 整节原样搬至 `response-archive/response-R234.md` 并登记索引，窗口恢复 10。requests.md 条目 247 已从占位回填；本条为回应。冲突记录：无撞号。

## 2026-10-29（R248：整本任务进度条只在书籍详情页显示）

### R248（用户：「进度条不应该显示在这里啊。应该显示在书籍详情页，全文任务那里」；截图为书架页/书卡弹层顶部的进度条）

- **结论先行**：已修复，进度条不再挂在书架页或书卡弹层的全局顶部；现在只在完整书籍详情页的「整本任务」按钮下方出现。
- **根因**：`detail.html` 的整本任务 partial 原先只受管理员门禁控制，XHR 书卡弹层也会加载它；`whole-book-panel.js` 初始化时又把 `#whole-book-progress` 移到 `body > .navbar` 之后。于是弹层片段被插入书架页后，进度条脱离书籍详情上下文，出现在书架页面顶部。
- **修复**：详情页新增专用 `#whole-book-progress-slot`，slot、partial 和 JS 统一加 `not is_xhr` 门禁；JS 只把进度条追加到该 slot，不再挂全局导航；进度条改为详情页内联布局，有活跃批次时隐藏「整本任务」按钮，收起后恢复按钮，收起状态在轮询期间保持。
- **边界**：只改进度条挂载与显示位置；三条整本任务的 start/status/retry 端点、轮询频率、缓存、计费与归档取书语义均未变。书卡弹层内的「整本任务」入口仍跳完整详情页。
- **测试**：新增 slot 双门禁、XHR 片段不下发 partial、进度条挂载到详情页 slot、收起后不被轮询重新弹出四条守卫；相关定向回归 **123 passed / 0 failed**，`node --check cps/static/js/whole-book-panel.js` 与 `git diff --check` 通过。
- **文档四问**：能力 → L1 `docs/product/readme/library.md` 明确进度条位置；契约 → 无变化；实现/边界 → L3 `docs/product/library/features/whole-book-progress.md`；本次实现 → R214 LLD §20、AC C11、需求基线与迭代 `plan.md`。
- **生产验收**：修复 `c2d5efa5` 已推 `origin/develop`，fnOS 构建 `END OK`、app-manager `deploy SUCCESS`，容器 `running/healthy` 且 `house.build-sha=c2d5efa5cf111f6e53be0bd5c463c08bda8c5777`。生产 `/shelf/5` 已无整本任务进度条；`/book/145` 的进度条位于工具栏下方、书名上方，并显示「全文单词详解 · 进行中」。
- **状态与驻留**：worktree `../magicbook-r248-progress-detail-only`（分支 `fix/r248-progress-detail-only`）已上线待用户验收；挂 R214 修复，不建独立 idea。
- **窗口与总结**：写入前 10 节，新增后达 11 节；按「写入即检查」把最早 R236 整节原样搬至 `response-archive/response-R236.md` 并登记索引，窗口恢复 10。requests.md 条目 248 已从占位回填；本条为回应。冲突记录：无撞号。

## 2026-10-29（R249：整本朗读 worker 复用请求会话，批次停在进行中）

### R249（用户：「book 145 的整本朗读不是已经完成了吗？为什么显示未完成，我点击还可以继续」；追加：「搜索 es 缓存 确定一下」）

- **结论先行**：用户的直觉对了一半。ES/MinIO 里的整本音频缓存此前已经基本齐全，但批次台账确实没有完成；`RUNNING 207/1348` 不是缓存被清空，而是后台 worker 在请求线程关闭数据库事务后崩溃，剩余 1141 段一直没有被台账收口。
- **ES/缓存核验（修复前）**：按 book 145 当前批次的 1348 个 `text_hash` 查 `magicbook-read-paragraph`，命中 1347 个文档且全部带 `audioObject`；对应 1347 个 `reading-tts/<hash>.mp3` 在 MinIO 中全部存在、均非空，只有第 1117 段缺失。1347 条音频的 `bookName` 全是 `Matilda`，生成日期为 2026-10-09/10，所以用户看到过整本朗读效果，但 2026-10-29 新批次尚未收口。
- **根因**：生产 `init_db()` 把普通 `Session` 实例赋给 `ub.session`，整本朗读 daemon 与 HTTP 请求线程共用它。请求线程提交/关闭事务后，worker 于 11:41:59 下一轮 autoflush 抛 `sqlalchemy.exc.ResourceClosedError: This transaction is closed`；线程被花名册注销，但 job 仍为 `RUNNING`，且还有 PENDING 段，因此接口返回 `canResume=true`，页面显示「继续」。
- **为什么 207 次请求无异常**：`app-log-moon-well` 同时间窗内 `source=book-tts-batch` 的 `/tts/speak` 正好 207 次且无 ERROR，均命中旧缓存；台账只有逐段请求成功后才标 `DONE`，所以缓存已存在的 1140 段仍显示 `PENDING`。缓存齐备不等于批次完成，二者不能混为同一状态。
- **修复**：`WholeBookTtsService._synth_worker()` 改用 `_thread_db_session()` 的独立 engine + 线程作用域会话，逐段 `_commit_with_retry()`；每轮 `expire_all()` 让请求线程写入的 `CANCELLED` 可见；`_refresh_counts()` 显式接收 worker session；请求侧 `progress()` 提交后 `refresh(job)`，避免返回旧 `RUNNING` 快照。start/status/retry/cancel 契约、轮询、缓存与计费口径不变。
- **测试**：新增 `test_synth_worker_never_uses_request_session`，把 `ub.session` 换成任何访问都会报错的哨兵，worker 仍用独立会话跑到 `COMPLETED`。相关回归 **268 passed / 0 failed**，`git diff --check` 通过。
- **上线与生产验收**：实现 `39759318` 已快进推送 `origin/develop`；fnOS 构建并部署成功，容器 `running/healthy`，镜像 label `house.build-sha=39759318a53cd35f8d877c0afffd6783e861ba0d`。生产点击「继续」后从 207 段续跑至 `COMPLETED`，最终 `done=1348 / failed=0 / pending=0`，日志记录 `finished (done=1348 failed=0)`，部署后无新的 `worker crashed` 或 `ResourceClosedError`。
- **缓存补齐**：续跑后 ES `magicbook-read-paragraph` 为 1348/1348 段音频引用，MinIO 对应 1348 个对象全部存在且非空。`/book/145` 页面显示「整本朗读 · 已完成」「100%」「1,348 / 1,348」，「继续」按钮消失；刷新后出现「整本朗读已缓存」标识。
- **文档四问**：能力 → L1 `docs/product/readme/library.md` 明确后台任务不随页面请求中断；契约 → 无变化；实现/边界 → L3 `docs/product/library/features/whole-book-progress.md` 增加 worker 独立会话与「台账/缓存双口径」；本次实现 → R214 LLD §21、AC C12、需求基线、迭代 `plan.md` 与 requests.md R249。
- **窗口与驻留**：写入前 10 节，新增后达 11 节；按「写入即检查」把最早 R237 整节原样搬至 `response-archive/response-R237.md` 并登记索引，窗口恢复 10。worktree `../magicbook-r249-tts-worker-session`（分支 `fix/r249-tts-worker-session`）按闸门保留待用户验收，验收通过后再清理。
- **总结**：requests.md 条目 249 已从占位回填；本条为回应。冲突记录：无撞号。迁移债务：本修复只隔离 R240 迁移前的存量 daemon 会话，整本朗读后续仍须迁入统一 async-task runtime 的租约、心跳与 fencing。

## 2026-10-29（R252：书籍详情页展示整本朗读与翻译费用及缓存费用）

### R252（用户：「书籍详情页写一下完整听完大概需要多少token，完整翻译完大概需要积分，如果已经缓存了就写缓存需要的积分加原始需要的积分，比如 【完整朗读预计花费1（100）积分】1是缓存 100是全文朗读预计。详情也写一下。」）

- **结论先行**：已实现，书籍详情页在缓存齐备标识后固定显示两行成本摘要。用户例子里的「1（100）」信息结构保留为「缓存值（全文原价）」，但数字按真实计费口径计算，不把整本朗读缓存总价机械写成 1。
- **口径纠正**：翻译按 token，`chars/4` 粗估后用 moon-well R222 公式 `ceil(tokens × creditsPer1kToken / 1000)`；翻译命中缓存不调用模型，缓存阅读为 **0 积分**。TTS **不按 token**，全文生成按字符 `floor(chars / charsPerCredit)`；已缓存收听按 moon-well R213 的 **1 积分/段**，所以页面写「约 N 字符（TTS 不按 token）」与「缓存收听 A 积分（全文生成原价约 M 积分）」。
- **实现**：`reading_insight/parser.py` 在速览解析时顺带记录去重后的 `billableParagraphCount` / `billableCharCount`，不解析第二遍 EPUB；新增 `reading_insight/cost.py::build_book_cost_summary()` 纯函数；`show_book()` 复用 `entry.insight` 与 `entry.cache_readiness`，读取 moon-well `/credit/billing`（沿用 5 分钟进程缓存，详情页超时 2 秒）。详情页不调用 `find-translations`、`cached-check` 或逐段 TTS 探针，费率故障只让积分暂缺，不拦页面。旧速览快照没有去重字段时回退到 `charCount` / `paragraphCount`。
- **展示**：未缓存时只显示全文生成原价；翻译已缓存时显示「缓存阅读 0 积分（全文生成原价约 M 积分）」；朗读已缓存时显示「缓存收听 A 积分（全文生成原价约 M 积分）」，其中 `A = readiness.tts.total × 1`。费率不可得显示「暂不可得」，TTS 费率字段缺失也不会伪装成 0；明确 `tts.enabled=false` 时才显示全文生成 0。
- **同步修正**：`/ajax/whole-book-estimate` 的翻译积分从旧的「不足千按千」回正为 R222 比例计费并向上取整；定向测试中 22 字 / 5.5 token 从错误的 10 积分改为 1 积分，上界 2。
- **测试**：新增成本纯函数与模板/接线守卫，覆盖未缓存、翻译已缓存、朗读已缓存、两者已缓存、费率不可得、TTS 关闭、TTS 字段缺失、旧快照回退、2 秒费率超时；同时补 parser 去重规模断言。相关定向回归 **118 passed / 0 failed**，全量 **1133 passed / 0 failed / 4 warnings**，`py_compile` 与 `git diff --check` 通过。
- **文档四问**：能力 → L1 `docs/product/readme/library.md` 新增「整本费用预估」；契约 → 无对外 HTTP 契约变化；实现/边界 → 新建 L3 `docs/product/library/features/book-cost-summary.md`；本次实现 → R252 LLD 与 AC、需求基线、`REQUIREMENTS.md`、迭代 `plan.md`。LLD 状态为「已上线待验收」。
- **上线**：实现提交 `004c6a1f` 已快进推送 `origin/develop`；fnOS 构建 `END OK`，app-manager 部署 `SUCCESS`，容器 `healthy` 且 `house.build-sha=004c6a1fc7ea89f2756b3dba116e7df870afa025`，线上 `/login` 返回 200。worktree 原样保留待用户验收。
- **窗口与驻留**：写入前窗口 10 节，新增后达 11；按「写入即检查」把最早 R238 整节原样搬至 `response-archive/response-R238.md` 并登记索引，窗口恢复 10。worktree `../magicbook-r252-book-cost-summary`（分支 `feat/r252-book-cost-summary`）按闸门保留待验收。
- **总结**：requests.md 条目 252 已从占位回填；本条为回应。冲突记录：无撞号；本轮按用户「多少 token」的提问明确区分了翻译 token 与 TTS 字符口径。
