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
