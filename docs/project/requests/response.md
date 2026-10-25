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
---

> 归档索引：[response-R01-R31.md](response-archive/response-R01-R31.md) · [response-R32-R49.md](response-archive/response-R32-R49.md) · [response-R50.md](response-archive/response-R50.md) · [response-R51-R70.md](response-archive/response-R51-R70.md) · [response-R70-R80.md](response-archive/response-R70-R80.md) · [response-R81-R101.md](response-archive/response-R81-R101.md) · [response-R102-R110.md](response-archive/response-R102-R110.md) · [response-R111-R119.md](response-archive/response-R111-R119.md)（2026-10-08 R129 补账搬移）· [response-R120-R125.md](response-archive/response-R120-R125.md)（2026-10-08 R135 写入触发搬移，含 R134 登记的窗口欠账补账）· [response-R126-R131.md](response-archive/response-R126-R131.md)（2026-10-09 R141 写入触发轮转搬移）· [response-R132-R133.md](response-archive/response-R132-R133.md)（2026-10-10 R143 写入触发轮转搬移） · [response-R134.md](response-archive/response-R134.md)（2026-10-10 R144 写入触发轮转搬移） · [response-R135-R137.md](response-archive/response-R135-R137.md)（2026-10-10 R147 写入触发轮转搬移，含 R145/R146 两次写入的窗口欠账补账） · [response-R138.md](response-archive/response-R138.md)（2026-10-11 R152 写入触发轮转搬移） · [response-R139.md](response-archive/response-R139.md)（2026-10-11 R153 写入触发轮转搬移） · [response-R140.md](response-archive/response-R140.md)（2026-10-11 R153 复核后的补搬——R152 写入时搬走 R138 后窗口仍为 11） · [response-R141-R142.md](response-archive/response-R141-R142.md)（2026-10-11 R155 集成时窗口超限搬移） · [response-R144-R153.md](response-archive/response-R144-R153.md)（2026-10-12 R161 写入触发轮转搬移，清并行欠账 R144–R153） · [response-R154.md](response-archive/response-R154.md)（2026-10-12 R165 写入触发轮转搬移） · [response-R155-R156.md](response-archive/response-R155-R156.md)（2026-10-13 R166 写入触发轮转搬移，含同日同编号「细筛」那条） · [response-R157.md](response-archive/response-R157.md)（2026-10-13 R166 分支 merge origin/develop 后窗口仍达 11，续搬最旧一节） · [response-R156-mic.md](response-archive/response-R156-mic.md) · [response-R158.md](response-archive/response-R158.md)（2026-10-13 R168 写入触发轮转搬移）（2026-10-13 R167 写入触发轮转搬移；与 response-R155-R156.md 里的同编号「细筛」条目不同事） · [response-R160-R164.md](response-archive/response-R160-R164.md)（2026-10-14 R172 写入触发轮转搬移，窗口转入 R161 起） · [response-R161-R162.md](response-archive/response-R161-R162.md)（2026-10-14 R173 写入触发轮转搬移，窗口转入 R165 起） · [response-R165-R173.md](response-archive/response-R165-R173.md)（2026-10-15 R183 写入触发轮转搬移，窗口转入 R174 起） · [response-R174-R177.md](response-archive/response-R174-R177.md)（2026-10-16 R185 写入触发轮转搬移，窗口转入 R178 起） · [response-R175.md](response-archive/response-R175.md)（2026-10-16 R188 写入触发轮转搬移）

## 2026-10-23（R212：入口层换皮之品牌资产与字样收敛——一枚圆章两条通道）

- **承接**：用户令「MB-11 authentik 的第 2 项（logo/背景）改成跟 magicbook 统一风格的，看看 magicbook 有没有什么要改的，都使用哈利波特系列风格」。查 MB-11 描述得待办第 1 项即 `branding_logo` / `branding_default_flow_background` 仍是官方默认。
- **先否证「统一风格」的前提**：实测 magicbook **没有任何图形品牌资产**——站内唯一品牌是文字 wordmark（`style.css:223` Grand Hotel 手写体 + 青绿 `#45b29d`），`cps/static/img/` 只有功能图标，`/login` 是裸 Bootstrap `.well`。所以「跟 magicbook 统一」无从取齐，本轮是**新建**图形标识、再让两边共用，不是把 authentik 对齐到某个既有图形。
- **三问三答拍板**：托管＝MinIO `brand/`；标识＝圆章版雪鸮立旧书；范围＝改名 + 挂徽章 + favicon（登录页换皮、整站换色不做）。
- **authentik 侧实测**（决定托管路线）：容器源码 `/authentik/brands/models.py:34` 把 `branding_logo` 等定成 `TextField`，全仓无 `MediaAvatar`、`root/urls.py` 不挂 `/media/`（`/media/`、`/files/` 线上 404）——**没有上传接口，只能填 URL**；登录页 CSP 头实测**不存在**，故跨源图可放行；15 条 flow 的 `background` 列全空 → 改 brand 一处覆盖登录/注册/改密。两条 brand（`authentik-default` / `account.haoshenqi.top`）三个字段现均为内置默认路径。
- **一处主动收紧（对我自己上一轮的方案）**：我先前把「同源一份资产」当成默认前提，实测本仓 CSP 是 `img-src 'self' data:`，且 `tests/test_csp_media.py::test_buddy_image_origin_not_opened_site_wide` 显式断言「其余页面不放行 MinIO」（R181 窄面口径）。为顶栏一枚徽章去放宽全站 img-src 等于推翻一条有意收紧的守卫，不值。故**站内走同源静态文件**（`cps/static/img/brand/`，128px/30KB），认证域走 MinIO，两份产物由 `vibe_images/build_brand_assets.py` 一次生成、不手改。
- **交付项 2 的实测修正**：台账原写「站内 6 处 Calibre-Web」——那是只扫模板。按 `_()`/`N_()` 全量扫，用户可见面 **13 处**（模板 6 + `admin.py` 4 + `helper.py` 5 + `kobo_auth.py` 1 + `search.py` 1，其中 3 处是注册欢迎邮件与测试邮件，站内根本看不见、只有收邮件时看得见）。逐行精确替换，**日志行与文件头许可证署名保留**（前者断了 ES `app-log-magicbook` 文本检索，后者是上游署名）。`stats.html` 的 "powered by Calibre-Web" 亦保留——真实归属，抹掉等于谎报来源。
- **i18n 联动**：改 msgid 必须成对改 `zh_Hans_CN/messages.po` 并重编 `.mo`，否则中文退回英文、看起来像「翻译丢了」。10 条有译文词条成对更新（顺带修上游 `Caliebre` 拼写与 `Catalog`→「路径」两处误译）；3 条无译文的与改前行为一致。
- **顶栏偏移是量出来的**：headless Chrome 实测圆章中线与文字盒中线差 **-0.4px**（35px Grand Hotel 的字形中线低于行框中线），故 `margin: -6px 8px 0 0` 而非直接 `vertical-align: middle`。
- **测试**：新增 `tests/test_brand_consistency.py` 5 例（模板无残留 / 无 `_(...)` 带上游品牌 / 10 词条必须出中文 / 资产存在且被引用且 CSS 有规则 / 配置默认值形态）。**反向变异两处已做**：还原 `http_error.html` + 还原 `.mo` → 2 例即红；复原后 5 passed。开发态合计 **138 passed**（含 `test_csp_media` 8 例，证明没碰坏窄面口径）。全量属发布闸门，留用户指令。
- **不做**：不改 `apple-touch-icon`（140×140 与 64px 素材不匹配，且非本轮范围）；不改 `cli.py --help` 与调试包文件名（运维面）；不给认证页加素材兜底；不放宽 CSP。
- **风险登记**：认证域 logo/背景是**新的对外可见面**，随 `docs/product/companion/features/buddy-ip-risk.md` 同一登记处置（内测可接受、公开注册前换原创）；本轮素材为原创构图，未用电影原图/校徽/闪电字标。
- **上线顺序（不可颠倒）**：moon-well R209 先上线（bucket 策略只在启动时写，不重启 `brand/` 一直 403）→ 传对象并实测 200 → magicbook push → authentik 写三字段 + `restart server worker`（改 brand 有缓存）→ 现网核验。生产 `app.db` 的 `config_calibre_web_title` 现值仍是 `Calibre-Web`（代码默认值改动不影响存量），改它属运维写操作，留用户放行。
- **台账与驻留**：本轮不占新号（属 R212 交付项 2/5 的执行，按「不做无主修复」挂在 MB-11 下）；worktree `../magicbook-r212-brand-assets`（分支 `feat/r212-brand-assets`，基线 `e649a785`）驻留待验收；**push 闸门留用户**。跨仓：moon-well R209（`../moon-well-r209-brand-assets`）。
- **窗口**：本条写入使回应节数达 11，按「写入即检查」把最旧一节 **R205**（单词编故事 Hub 卡）原样搬至 `response-archive/response-R205.md` 并登记索引，窗口回 10。
- **补记（2026-10-24 生产实况）**：authentik 侧**已换皮生效**——两条 brand × 三字段 `UPDATE 2`（改前值备份 `/root/authentik-brands-backup-20261024-r212.json`）+ `restart server worker`（约 10s 回 healthy），headless Chrome 真页面截图确认 `--ak-flow-background` 与 logo/favicon 均指向新对象、圆章实际渲染在卡片正中约 150px（我 mock 里画的左上角小图是错的，素材按 256px 出是对的）。**本仓代码仍未 push**，顶栏徽章/字样收敛只在分支上。另查清一处**非本轮**缺陷：登录按钮仍是英文「Log in」（真人中文浏览器实测，非探针假象），但它不在任何配置面里——2025.10 的 `authentik_flows_flow` 无 `submit_button_text` 列、`flowstagebinding` 无 `label` 列（均实测 schema），R162 中文化覆盖的是 prompt 的 label/placeholder。要改得动上游前端包，另立条目。
- **补记 2（2026-10-24 08:09 已 push 上线）**：用户令「1，2 push，3 改掉吧」→ `8842d1c2..195ab0d7` 快进推 develop（同样从 worktree 直推，主检出有并行会话未提交改动，不碰）。fnOS `build END OK`、基线推进。**线上实测**：`<title>magicbook | Login</title>`、顶栏圆章 + Grand Hotel wordmark 渲染正确（headless Chrome 截图）、`/static/img/brand/{logo,favicon}.png` 双 200。站点标题也按第 3 项改掉：`app.db` → `settings.config_calibre_web_title` = `magicbook`（取拉丁文，Grand Hotel 无中文字形）；该值启动时读入内存，改完当下线上仍吐旧值，由本次部署重启生效——**「改了 DB 就以为好了」是这个坑的标准形态**。
- **合并实况与新基线复跑**：推前 origin 又被并行会话甩开两次（r215 段尾字形、r206 伙伴拖拽）。第一次带来 `messages.mo` **二进制冲突**——正解不是 `--ours/--theirs` 二选一，而是**用合并后的 `.po` 重编**（`.mo` 是产物）；`.po` 侧自动合并后校验「无冲突标记 / 残留 Calibre-Web msgid=0 / 我方 magicbook 词条 11 条」才提交。第二次干净合并。两轮各跑全量：`pytest tests/` = **819 passed / 0 failed**。
- **总结**：requests.md 的 R212 条目追加第二轮拍板与两处实测修正；response.md 增一节、轮转一节。冲突记录：无撞号。

## 2026-10-24（R214 子项 C：整本任务代价面板）

### R214-C（承接「继续」→ 子项 C 开发）

- **任务定位**：R214 收口件，PJM MB-13 / Ship MAGICBOOK-221。三个整本入口（翻译/朗读/详解）
  从「点一下就下单」改成「先看代价再决定」，落 LLD §4.3/§5/§6/§7。
- **后端**：`reading_insight/service.py` 补 `estimate()` + `active_jobs()`；`routes/book_detail.py`
  加 `POST /ajax/whole-book-estimate`（admin + `_llm_task_admin_gate`）；`web.py` 加
  `_credit_billing_rates()`（moon-well `/credit/billing`，5 分钟进程内缓存，取不到回 None）
  与 show_book 的活跃批次快照注入。
- **实现修正（与 LLD 原文不同，已回填 §4.3 表）**：
  ① `units.billable` 新增——翻译/朗读台账的 item 都按 `text_hash` 唯一，拿全书段落数当工作量
  会把重复段算两遍，耗时与积分一起虚高；`paragraphs` 仍保留书目真实段数。
  ② `activeJobs` 新增——§7.5 要的「页面初始进度态」需要服务端承载字段，估算与首屏共用同一个
  `active_jobs()`，两条路径 `total/done` 不会分叉。
  ③ `duration.known` 显式化 + **详解没有常量兜底**（无实测支撑秒/词，样本不足就明说不知道）。
  ④ `credits.rate` 只回传本条链路用到的字段。
  ⑤ 详解覆盖率直接分批调 cached-check，不走 `preview()`（后者会重抽一遍正文；`notWordLike`
  只在预览页有解释位）。
- **前端**：新增 `partials/whole_book_panel.html`（三 tab + 卡片 + 进度条 + 全部文案在 data-*）
  与 `whole-book-panel.js`（切 tab 拉估算并按 kind 缓存、主按钮二次确认带预计时长/积分、
  进度轮询 4s/5s/30s、有活跃批次直接进进度态）；`detail.html` 三个并列按钮合并为单个
  「整本任务」入口并把内联 jQuery 整体迁出；`book-detail.css` 补面板与吸顶进度条样式。
  **详解保持两步式**：面板主按钮只跳 `word_detail_batch_page`，不替管理员下单（R176 边界）。
- **测试**：新增 `tests/test_whole_book_estimate.py` ×10（去重计费单位、朗读不探缓存、
  详解只走 cached-check、lookup 失败不报 0、费率不可得、tts 关闭计费专属原因、历史中位数优先、
  活跃批次透传、非法 kind、空段落）；`test_book_detail_r214.py` 补 5 条（入口 admin 门禁、
  面板三 tab、旧并列按钮不许复活、「不修改原书文件」可见、模板真渲染 + endpoint 存在、
  估算端点只读守卫）。**改了两条既有守卫**：R176 的「三个整本按钮各一处」（形制已合并，
  改判「入口一处 + 面板三 tab」）、R214 自己的 `test_whole_book_buttons_admin_gated`（同因）。
  全量 **804 passed / 0 failed**。
- **未做**：真机验收未跑（面板要真书 + admin 账号）；push 闸门留给你——本节代码在
  `feat/r214-book-detail` 分支上，未合 develop、未 push。
- **窗口**：本条写入后 `## ` 节数再 +1。按上一轮约定（R218 条已说明）轮转待统一整理，
  避免与并行会话的归档改动撞车，本轮不搬移。

## 2026-10-24（R214-C 验收缺陷：入口按钮落进书卡弹层 + 估算 500）

- **现象**：点「整本任务」后页面错乱（整页被套进「书籍详情」弹层）；Console 两条硬事实——
  `/ajax/whole-book-estimate` **500**、`isotope` 报错（后者是弹层里套整页带出来的噪音）。
- **定位一（错乱的真因）**：列表页点书卡是 **XHR 片段**——`show_book` 把 `detail.html`
  渲染成 `fragment.html`，片段没有 `block js`，面板 modal + JS 整块不下发，但按钮在
  `block body` 里照旧渲染。于是 `data-target` 选不到 `#whole-book-panel`，Bootstrap
  data-api 空转并与既有的 `#bookDetailsModal` 抢这次点击 ⇒ 整页被塞进弹层。
  **修**：按钮加 `not is_xhr` 门禁（整本任务只在完整详情页出现）+ 改 JS 显式绑定
  （`preventDefault` / `stopPropagation`），不再依赖 data-api。
- **定位二（500）**：估算链路两处**辅助查询**裸奔——`_history_rate`（台账采样）与
  `active_jobs`（活跃批次）。任一抛错就把整块面板打成 500，而 `.fail` 收到的是 HTML，
  界面只剩「估算失败：500 Internal Server Error」，既不知原因也不知该不该重试。
  **修**：两处各自 try/except 降级（没有样本 / 没有活跃批次 + 落 warning）；路由补兜底
  `except Exception`，落 `traceback.format_exc()` 并把 `类型: 消息` 回给前端——下次再失败，
  面板上会直接写着原因，不用再靠猜。
- **定位三（顺带修的形制级 bug）**：`data-t-start-wordDetail` 属性名带大写，被 HTML
  解析器小写成 `...worddetail`，而 JS 用 `t('start-' + kind)` 取 camelCase ⇒ 详解 tab
  的主按钮文案是空的。模板改全小写、JS 侧 `toLowerCase()`。
- **测试**：新增 5 条（data-api 禁用 / is_xhr 门禁 / 显式绑定 / 键名小写 / 路由兜底源码守卫）
  + 2 条降级行为测试（query 抛错时 `_history_rate` 回 `(None, 0)`、`active_jobs` 回全 None）。
  全量 **853 passed / 0 failed**。
- **待确认**：500 的具体异常类型要等这次上线后看面板上的那行红字（已含异常类型与消息），
  本轮先把「不可读的失败」变成「可读的失败」，再按实际原因收口。

## 2026-10-24（R213-C：首页 `/home` 组装——继续阅读/今日计划/分级推荐/随机发现 + 登录落点开关；A 的侧边栏分组按拍板本迭代不做）

### R213-C（用户令：「A 的侧边栏分组 这个迭代不改，下个迭代再说。直接做C」）

- **范围锁定**：本轮只做 C。R213-A 的「侧边栏四组分组」按用户拍板**本迭代不实施、下个迭代再说**（LLD §5 保留设计与约束，不删不实现），A 以「除分组外已上线」结项。
- **开发第一步先核实 LLD 的两个前置假设**（不猜字段名）：① `writing/history` 是否真带 `createdAt` —— 读 moon-well `WritingVO.HistoryItem` 确认 `createdAt` + `lastDraftNo` 都在，**方案②（moon-well 加 `writingPending`）不启用，跨仓改动为零**；② 待复习词数该取哪个字段 —— `/learning` 页的「到期」用的是 `srs/stats.dueNow`（`learning-hub.js::renderStats`），而 `plan/today` 的 `reviews` 被 `dailyMinutes` 推出的 `reviewCap` **截断**（`LearningPlanService.today()`），拿它会把「到期 40」显示成「到期 20」，直接违反 AC C2。落地取 **`reviewTotal`**——它与 `dueNow` 是同一个 `countDueBetween(MIN, now)` 查询，**数值恒等**，这条同源关系是 C2 的实证依据（不是「大概一致」）。
- **四处对 LLD 原案的修正**（照原文写会错，已回填 LLD §4.3）：见上；另两处是**落点判据抽成 `cps/landing.py::landing_endpoint()` 单点**（四处消费：登录页 `next` 默认值 / 本地登录成功 / OIDC `oidc_next` 默认值 / 已登录再访问登录页；写进 `web.py` 会让 `oidc.py` 只能函数内 import 绕环形依赖）、以及**卡片宏参数化到 7 个参数**（`index.html` 两个循环本来就有差异，不参数化就会在重构中改掉既有观感）。
- **卡片只留一份实现**：新增 `cps/templates/partials/_book_card.html::book_card()`，`index.html`（随机区/列表区）与 `home.html`（继续阅读/分级推荐/随机发现）共用；差异走 `read_flag` / `show_badges` / `card_id` / `modal` / `music_icon` / `series_plain` / `href` + `caller()`（继续阅读用它挂进度条）。**顺带补上 R213-A 的欠账**：格式徽标当初只进了随机区，列表区一直没有——现在两区同源，不会再漂。
- **落点开关带迁移**：`settings.config_home_landing`（Boolean，默认 `True`）。既有库必须靠 `ub.migrate_home_landing_config()` 启动 `ALTER TABLE settings ADD COLUMN ... DEFAULT 1`——缺列不是「回退默认值」而是**任何配置读取都 OperationalError**（整站 500），所以迁移是功能的一部分。管理端「编辑配置」加勾选框（`_config_checkbox`），取消勾选即回退 `/` 发现页，**回退不需要发版**。
- **首页零阻塞**：今日计划完全不走服务端渲染，`home.js` 并行拉两个既有代理端点，单块失败只让该数字显示 `–`，两块都失败才整卡降级为「今日学习页」提示（AC C3）；随机发现沿用 `/` 的 `generate_linked_query + common_filters`，受限书/归档书不会漏出来。文案全部由模板 `_()` 注入 `data-*`，JS 只填数字——**没有第二个取词入口，也就没有「mbT 词条漏进种子」的静默回退面**（`test_home_js_passes_text_through_data_attributes` 钉住）。
- **测试**：新增 `tests/test_home_route.py` 27 例——登录门禁、四块空态不渲染、`阶N` 解析 10 组参数、同阶合并去重、**`阶10` 不排在 `阶2` 前**、已读完不进推荐、书被删跳过、无阶书架进「未分级」尾组、落点开关四种组合、迁移幂等、**真渲染一张卡**（`image.book_cover` / `main_format` 这类过滤器只在渲染时暴露参数不匹配）、**真渲染 index 的一条 entry**（列表区不带格式徽标、带音乐图标）。全量 `pytest tests/` = **873 passed / 0 failed**。
- **两处既有守卫同步更新（有意的结构变更，不是放宽）**：`test_home_nav_shell.py::test_cover_format_badges_present` 与 `test_onboarding_tour.py::test_browse_step_anchors_exist_in_templates` 原来断言 `index.html` 源码里有卡片外层 class / 格式徽标——现在是「index 复用宏」的结构，断言跟着实现移到 `partials/_book_card.html`，并各自加了「index 必须复用宏」这条更强的约束。
- **i18n**：新增 7 条 msgid（Continue Reading / Go to Learning / Recommended by level / Words due for review / Writing tasks to finish / 降级提示 / 配置项标签），`pybabel compile` 重编 `messages.mo`（**msgfmt 报 po 里有三处历史重复词条**：`Save` / `Close` / `Vocabulary` 各定义两次——既有问题，本轮不顺手改，记录备查）。
- **文档四问**：能力变了吗 → L1 `product/readme/library.md` 增「首页（`/home`）」一条；契约变了吗 → **无新对外接口**（`/home` 是页面路由，今日计划复用既有 `/ajax/learning/*` 代理），站点配置新增一项；实现/边界变了吗 → 新建 L3 `product/library/features/home-ia.md`（取数口径、归阶规则、卡片宏、边界与坑）；本次怎么实现 → LLD `project/iterations/1.0/r213-home-ia/lld.md` 补 §4.3 实现修正 + §4.4 验收对应表，状态行改为「A 分组按拍板本迭代不做 / C 已开发待验收」。AC `ac/acceptance.md` C1–C6 逐条勾选并注明判据落点。
- **窗口与合并冲突**：本轮两次触发轮转——① 写入前窗口已 11 节，先把最旧的 **R206 + R207** 原样搬至 `response-archive/response-R206-R207.md`，窗口回 10；② 之后合 `origin/develop`（`d1db8268`，带 R214-C 验收缺陷节）时本文件**必冲突**（双方都往末尾追加），按「两节都保留、按写入时间序 R214-C 在前 / R213-C 在后」解冲突，窗口再达 11，把最旧的 **R208** 搬至 `response-archive/response-R208.md`，窗口回 10。两次均只搬移不改写，索引各登记一行。
- **AC 与台账回填（本轮实际改动的文件，不是只在回应里说）**：`ac/acceptance.md` 状态行改「A 除分组外已上线 / B 已验收 / C 已开发待验收」，C1–C6 逐条勾选并附判据落点 + 测试名，C2/C3 行内标「真机待 G1」；G2/G3 勾选；G1 保留待真机。**A1 明确不勾**并写明「本迭代不实施，不是缺口」；A2–A7/B1–B5 段首注明证据位置但**不代勾**（勾选归 MB-16/MB-17 结项轮次，代勾等于替别人宣布验收结论）。`plan.md` 回填 MB-12（A 除分组外已上线 / B 已验收 / C 已开发待验收）、MB-16（分组按 2026-10-24 拍板本迭代不改，`Shelf.kind` 留待下迭代）、MB-18（已开发待验收 + 落地清单）。
- **顺带发现两处文档欠账（已标注、未擅自修）**：① AC **B6** 写的开关 `reading_progress_enabled` 在仓库里**根本不存在**（`cps/`、`tests/`、`_Settings` 均无命中）——R213-B 从未做过 kill switch，进度上报是常开的。按 MB-17 范围处理，留给下轮确认「补开关」还是「改判据」。② 首版我凭印象写了个 `enable_reading_progress`，随即被自己的核查推翻，已在 AC 里改成「查无此开关」的准确表述——这类名字不能猜。
- **驻留与闸门**：已提交 `f4df325a`，并 merge `origin/develop`（`d1db8268`）拉齐基线，全量重跑后推进 develop 指针（**只推本地 develop，不 push**）。worktree `../magicbook-r213-home-ia`（分支 `feat/r213-home-ia`）保留待真机验收；**push 即触发 fnOS 自动上线，按用户闸门执行**。真机验收重点：G1 两档视口（1440×900 / 390×844）截图比对，以及「今日计划」在 moon-well 正常/不可用两种状态下的表现（C2/C3 的最后一段只能在真机看）。

## 2026-10-24（R221：AI 口语陪练语音优先——教练默认语音条 + 用户录音转写预览）

### R221（用户：修复口语陪练 500；随后「教练默认发语音，类似微信，可以点击语音转文字。同理，我发出去的也是语音，也可以转文字，发送之前先转文字看效果」）

- **编号迁移**：本任务最初误占 **R212**（该号已属品牌资产），已按家族占号流程正式迁移为 **R221**；旧 worktree `../magicbook-r212-speaking-voice` 保留为迁移来源，未删除。R210 口语 403 修复已按用户指令放弃，不推送。
- **教练语音**：开场与每轮回复默认语音条，点击播放、点「转文字」展开原文；自动播放只在开聊/发送的用户手势链中尝试，失败不弹误导框。后端复用阅读 TTS 缓存与计费，前端通过 `/ajax/reading-tts-cached` 不计费回读。
- **用户语音**：录音停止 → ASR 转写 → 可编辑预览 → 点击发送才 multipart 上传并调 LLM；保留「Type instead」。发送失败保留预览与已上传对象名，重试不重复上传。历史会话的用户/教练语音均可回放。
- **修正点**：教练语音合成与回读统一截取 1800 字，避免长回复缓存 miss 后重复扣费；语音按钮文案改为 `Tap to speak`，不暗示按住说话。
- **测试**：JS `node --check` 通过；`tests/test_learning_proxy.py`、`test_learning_pages_static.py`、`test_i18n_seed_contract.py` 回归 **106 passed**。新增「发送失败保留预览」源码守卫。i18n 种子、中文 PO 与 `.mo` 已同步重编。
- **验收缺陷（2026-10-24 续修）**：用户真机验收反馈 `/ajax/reading-tts-cached` 返回正常，但教练与用户语音均无法播放；Chrome 控制台为 `Loading media from 'blob:…' violates ... Content Security Policy`。根因是阅读页已显式放行 `media-src … blob:`，而口语页没有 `media-src`，媒体加载回退到不含 `blob:` 的 `default-src`。修法仅为 `web.learning_speaking_page` 增加 `media-src 'self' blob:`，不改 TTS 接口、不放宽全站 `default-src`，也不向口语页带入阅读页的有道 / MinIO 外源。
- **修复回归**：`tests/test_csp_media.py` 新增「口语 endpoint 只允许 self + blob」与「真实 `/learning/speaking` 路由响应头」两条守卫，并保留无媒体页面不得产生 `media-src` 的反向断言。定向四文件 **116 passed**；JS `node --check` 通过；发布态全量 `pytest tests/` **903 passed / 0 failed**。
- **文档四问**：能力变化 → L1 `docs/product/readme/learning.md`；契约变化 → L2 `docs/product/learning/interface.md`；实现与边界 → L3 `docs/product/learning/features/speaking-voice-first.md`；本次实现 → `docs/project/iterations/1.0/r221-speaking-voice/lld.md`。需求基线已追加 R221，迭代 plan 增 MB-19 工作项。
- **驻留与边界（如实）**：worktree `../magicbook-r221-speaking-voice`，分支 `feat/r221-speaking-voice`；语音优先功能已合入 develop，CSP 验收缺陷修复提交后合并并推送 develop 触发自动上线，worktree 保留待真机验收。尚未完成真人登录态录音、自动播放、历史回放验收。
- **总结**：requests.md 条目 221 为已占号需求；本条为回应。冲突记录：原误占 R212，已迁移 R221；R210 已放弃，不推送。

## 2026-10-24（R222：R214 验收缺陷——生成书籍简介 400，上游 Magpie 403 被误报）

### R222（用户：贴出 `POST https://magicbook.haoshenqi.top/ajax/book-summary 400 (Bad Request)`，「修复这个问题」）

- **任务定位**：缺陷，挂 R214 子项 B / PJM MB-13 / Ship MAGICBOOK-221；不做无主修复。
- **证据链（先查 ES 再读码）**：ES `app-log-moon-well` 在 18:33–18:36 连续记录
  `Magpie call failed: HTTP 403`，同 trace 的 `/book/ai/ability/book-intro` 响应为 500；
  Magpie 容器日志同一时段拒绝 `POST /v1/chat/completions from 172.28.0.1: not on the allow list`。
  moon-well 在 `moon-well_moon-well-net`（172.29.0.2），Magpie 在 `magpie_default`（172.28.0.2），
  跨网段请求到宿主端口时以 bridge 网关 `172.28.0.1` 为源地址，而 Magpie `allowIPs` 只有
  `192.0.0.0/8`。因此 400 是两层误报叠加，不是书籍入参/文件问题。
- **应用修复**：`cps/reading_insight/service.py` 新增 `UpstreamServiceError`（携带上游状态码），
  `_unwrap_result()` 对非 2xx / `success:false` / 不可解析 / 空正文统一抛该异常；
  `/ajax/book-summary` 新增 502 分支并记录上游状态与 message，本地入参/文件错误仍为 400。
  `cps/static/js/book-insight.js` 原本已展示 `data.message`，无需改前端。
- **运行修复**：fnOS `/app/magpie/config/magpie/settings.json` 备份为
  `settings.json.bak-r222-20261024-184438`（600），`allowIPs` 增加 `172.28.0.0/16`；
  `docker compose restart magpie` 后 healthcheck rc=0。未使用 `0.0.0.0/0`，未改端口绑定。
- **验证**：`tests/test_book_detail_r222.py` 四条（上游 500→502 且 message 保留 / 成功仍 200 /
  上游 302 不得当成功 / 非法 book_id 仍 400）+ `test_book_insight.py` +
  `test_book_detail_r214.py`，共 **49 passed**。
  真实链路：从 `moon-well-green` 容器带 gateway key 请求 Magpie `GET /v1/models` → HTTP 200；
  Magpie 重启后无新的 allow-list 拒绝。未伪造生产 AI 简介调用（当前会话无管理员 JWT），
  留给验收时在页面点「生成简介」确认最终 200 与简介落库。
- **文档四问**：能力不变；契约变化 → `/ajax/book-summary` 失败状态从一律 400 改为上游故障 502；
  实现/边界 → LLD §14 + §8；AC B5 改为明确要求 502。L1/L2 无需新增条目（用户操作不变）。
- **窗口**：本条写入后窗口为 11 节，按「写入即检查」把最旧的 **R211** 原样搬至
  `response-archive/response-R211.md` 并登记索引，窗口回 10；只搬移不改写。
- **驻留与闸门**：worktree `../magicbook-r222-book-summary-400`，分支
  `fix/r222-book-summary-400`，基线 `origin/develop` `643eddc8`（含 R222 占号提交），
  实现提交 `b28d9240`，台账回填 `a2056ec5`。用户 2026-10-24 明确指令 push，
  `a2056ec5` 已推送 `origin/develop`；fnOS 链构建/部署成功，运行镜像 label
  `house.build-sha=a2056ec5`，容器 `healthy`。当前 worktree 驻留待真人验收；
  验收通过后 `worktree remove` + `branch -d`。
- **总结**：requests.md 条目 222 为已占号需求；本条为回应。冲突记录：无撞号；已有
  `../magicbook-r214-detail-500` 属 R214 子项 A 的独立 worktree，本任务按新编号 R222 另建，
  未改动既有工作树。

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
