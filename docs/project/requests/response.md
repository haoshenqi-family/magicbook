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
---

> 归档索引：[response-R01-R31.md](response-archive/response-R01-R31.md) · [response-R32-R49.md](response-archive/response-R32-R49.md) · [response-R50.md](response-archive/response-R50.md) · [response-R51-R70.md](response-archive/response-R51-R70.md) · [response-R70-R80.md](response-archive/response-R70-R80.md) · [response-R81-R101.md](response-archive/response-R81-R101.md) · [response-R102-R110.md](response-archive/response-R102-R110.md) · [response-R111-R119.md](response-archive/response-R111-R119.md)（2026-10-08 R129 补账搬移）· [response-R120-R125.md](response-archive/response-R120-R125.md)（2026-10-08 R135 写入触发搬移，含 R134 登记的窗口欠账补账）· [response-R126-R131.md](response-archive/response-R126-R131.md)（2026-10-09 R141 写入触发轮转搬移）· [response-R132-R133.md](response-archive/response-R132-R133.md)（2026-10-10 R143 写入触发轮转搬移） · [response-R134.md](response-archive/response-R134.md)（2026-10-10 R144 写入触发轮转搬移） · [response-R135-R137.md](response-archive/response-R135-R137.md)（2026-10-10 R147 写入触发轮转搬移，含 R145/R146 两次写入的窗口欠账补账） · [response-R138.md](response-archive/response-R138.md)（2026-10-11 R152 写入触发轮转搬移） · [response-R139.md](response-archive/response-R139.md)（2026-10-11 R153 写入触发轮转搬移） · [response-R140.md](response-archive/response-R140.md)（2026-10-11 R153 复核后的补搬——R152 写入时搬走 R138 后窗口仍为 11） · [response-R141-R142.md](response-archive/response-R141-R142.md)（2026-10-11 R155 集成时窗口超限搬移） · [response-R144-R153.md](response-archive/response-R144-R153.md)（2026-10-12 R161 写入触发轮转搬移，清并行欠账 R144–R153） · [response-R154.md](response-archive/response-R154.md)（2026-10-12 R165 写入触发轮转搬移） · [response-R155-R156.md](response-archive/response-R155-R156.md)（2026-10-13 R166 写入触发轮转搬移，含同日同编号「细筛」那条） · [response-R157.md](response-archive/response-R157.md)（2026-10-13 R166 分支 merge origin/develop 后窗口仍达 11，续搬最旧一节） · [response-R156-mic.md](response-archive/response-R156-mic.md) · [response-R158.md](response-archive/response-R158.md)（2026-10-13 R168 写入触发轮转搬移）（2026-10-13 R167 写入触发轮转搬移；与 response-R155-R156.md 里的同编号「细筛」条目不同事） · [response-R160-R164.md](response-archive/response-R160-R164.md)（2026-10-14 R172 写入触发轮转搬移，窗口转入 R161 起） · [response-R161-R162.md](response-archive/response-R161-R162.md)（2026-10-14 R173 写入触发轮转搬移，窗口转入 R165 起） · [response-R165-R173.md](response-archive/response-R165-R173.md)（2026-10-15 R183 写入触发轮转搬移，窗口转入 R174 起） · [response-R174-R177.md](response-archive/response-R174-R177.md)（2026-10-16 R185 写入触发轮转搬移，窗口转入 R178 起） · [response-R175.md](response-archive/response-R175.md)（2026-10-16 R188 写入触发轮转搬移） · [response-R214-C.md](response-archive/response-R214-C.md)（2026-10-25 R229 写入触发轮转搬移：R214 子项 C 整本任务代价面板；与既有 response-R214.md（子项 A）不同事）

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

## 2026-10-26（R232：伴读面板不再显示 token 用量——记录照旧，用量只在设置·积分看）

### R232（用户：「AI 伴读不要显示token 使用量（可以记录，但是不要显示）。积分token用量仅在【设置】【积分】那里查看即可。」）

- **任务定位**：需求（展示口径变更），单仓、纯前端；moon-well 零改动。
- **改了什么**：`ai_chat.js` 的 `final` 分支删掉 `.ai-chat-usage` 渲染（原来读 `obj.usage.promptTokens/completionTokens` 拼 `tokens x/y`），**保留** `conversationIdFromFinal = obj.conversationId`（首条消息回传服务端建会话的唯一来源，删用量时最容易顺手删掉的就是它）；`ai_chat.css` 删对应样式；`speechTextOf()` 的朗读清洗选择器去掉该项（否则会留下一个永远匹配不到的死选择器）。
- **「可以记录」是既成事实，本轮确认未受影响**：moon-well `CreditServiceImpl.consumeForLlmTask` 仍按 `total_tokens` 扣费并落库，流水 `remark = "AI任务消耗 N token、每千 token 折 10 积分"`；SSE `final` 事件里的 `usage` 字段也照旧下发，只是前端不再消费。要排查线上计费，抓包与流水都还在。
- **「只在设置·积分看」也对得上**：`credits.html` 的消耗明细表（时间/类型/**原因**/功能/积分）里，「原因」列就是那条 remark，含 token 数；这一轮把用量的可见入口收敛到唯一一处，面板侧不留入口。守卫里专门钉了这张表不许被删/改名。
- **否决了两种更「贴心」的做法**：① 默认折叠、点开才显示——用户要的是不显示，折叠仍占一行、仍要一句文案；② 悬浮提示（hover 出 token）——藏起来的数字更容易被误读成「这一轮花了多少积分」，而实际扣费口径是每千 token 折 10 积分、TTS 按字符、ASR 按秒，一个数说不清。
- **测试**：新增 `tests/test_buddy_no_token_usage.py` 5 条——面板脚本不得含 `ai-chat-usage`/`promptTokens`/`completionTokens`；**全站** `cps/static/js/*.js` 均不得读这两个字段（面板自 R220 起全站挂载，漏一页就复现）；`final` 分支仍回传会话 id 且不再出现 `obj.usage`；CSS 无残留规则；积分页保留 `#credit-consume-rows` 与「原因/功能/积分」三列。定向回归 22 passed，**全量 986 passed / 0 failed**（`pytest tests/ -q`）。`node --check` 通过。
- **踩坑记录**：CSS 注释里原本写了 `.ai-chat-usage` 类名，被第 4 条守卫直接判红——注释里的类名同样会误导后来者，守卫这种字面量断言的价值就在这。
- **扩展侧：最初误判「无需改」，复查后确认为遗留**。首次用 `grep "a\|b"` 扫 magiclens 得空结果就下了结论，属 BSD grep 不支持 `\|` 交替造成的假阴性；改用 ripgrep 复核，`magiclens/extension/chat.js:366` 确有 `tokens ${promptTokens}+${completionTokens}` 写进消息 `.meta` 行。该仓不共用本面板脚本、且扩展需重新打包分发，故本轮**只记录不夹带修**，等用户决定是否单开一轮（同一坑还差点漏掉 moon-well 的 `CreditServiceTest` 活动倍率用例，已在本轮 R221 一并处理）。
- **文档四问**：能力→L1 `readme/companion.md` 增「聊天里不显示用量」；契约→无变化（SSE 字段与积分接口均未动，故未改 L2）；实现/边界→LLD `iterations/1.0/r232-hide-token-usage/lld.md`；本次实现→同 LLD。需求基线 `REQUIREMENTS.md` 增一行。
- **台账与驻留**：`claim.sh magicbook` 占号 **R232**（`2e48546f`，纯台账，已 push）；worktree `../magicbook-r232-hide-token-usage`（分支 `feat/r232-hide-token-usage`）驻留待验收；push 闸门留用户。
- **窗口**：写入前 11 节（已超窗），写入后 12 节；按「写入即检查」把最早 R221、R222 两节原样搬至 `response-archive/response-R221-R222.md` 并登记索引，窗口回到 10。
- **上线补记（同日，用户令「merge and push」）**：分支并 origin/develop（吸收 R233 的 `f68e39b3`+`a6b16e79` 两笔——合并时共享引用已被并行 fetch 推进到 `a6b16e79`，一并入并）。`ai_chat.js`/`ai_chat.css` 两需求改动无文本重叠、自动合并即语义正确（守卫复验：`ai-chat-usage`/`promptTokens` 零残留、`conversationIdFromFinal` 保留、R233 `normalizeSiteHref` 就位）。台账三处冲突对账：requests.md 取本分支 232 完整条目 + 远端 233 完整条目；`response-R221-R222.md` add/add 双方正文一致、取远端版；`response.md` 两节并存后窗口 11 → 续搬最旧 R223 至 `response-archive/response-R223.md`，窗口回 10。合并基全量 **999 passed / 0 failed**。**主检出 develop 有并行会话未提交的 `messages.po` 改动，快进会被并入的 R230 po 变更（+57 行）覆盖而中止，故按 R209 先例从 worktree 直推 `origin develop`＝`d1d6c84c`——主检出 develop 仍停在 `fe59ad54`（落后远端），messages.po 会话 pull 前需先 stash 该文件**。worktree 驻留待验收。

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
