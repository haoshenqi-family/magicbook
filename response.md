# 对话回应记录

> 含每个需求的回应、冲突说明及两个文件的总结。
> **归档规则**：本文件仅保留最近 10 个 request 的回应；更早内容原样归档至 `response-archive/`（按 request 区间分文件），需要历史细节时按编号检索归档目录，不要读全量历史。

**归档索引**

- `response-archive/response-R01-R31.md`：R1–R31（2026-08-14 ～ 2026-08-31）
- `response-archive/response-R159.md`：R159 语音输入静音检测（2026-10-14 R169 轮转，窗口转入 R160 起）
- `response-archive/response-R32-R49.md`：R32–R49（2026-09-03 ～ 2026-09-17）
- `response-archive/response-R50.md`：R50（2026-09-18）
- `response-archive/response-R51-R70.md`：R51–R70（2026-09-18 ～ 2026-09-21）
- `response-archive/response-R70-R80.md`：R70–R80（2026-09-22 ～ 2026-09-28；含 R70/R71 历史重复条与 R74 补写条，见文件头说明）
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

---

> 归档索引：[response-R01-R31.md](response-archive/response-R01-R31.md) · [response-R32-R49.md](response-archive/response-R32-R49.md) · [response-R50.md](response-archive/response-R50.md) · [response-R51-R70.md](response-archive/response-R51-R70.md) · [response-R70-R80.md](response-archive/response-R70-R80.md) · [response-R81-R101.md](response-archive/response-R81-R101.md) · [response-R102-R110.md](response-archive/response-R102-R110.md) · [response-R111-R119.md](response-archive/response-R111-R119.md)（2026-10-08 R129 补账搬移）· [response-R120-R125.md](response-archive/response-R120-R125.md)（2026-10-08 R135 写入触发搬移，含 R134 登记的窗口欠账补账）· [response-R126-R131.md](response-archive/response-R126-R131.md)（2026-10-09 R141 写入触发轮转搬移）· [response-R132-R133.md](response-archive/response-R132-R133.md)（2026-10-10 R143 写入触发轮转搬移） · [response-R134.md](response-archive/response-R134.md)（2026-10-10 R144 写入触发轮转搬移） · [response-R135-R137.md](response-archive/response-R135-R137.md)（2026-10-10 R147 写入触发轮转搬移，含 R145/R146 两次写入的窗口欠账补账） · [response-R138.md](response-archive/response-R138.md)（2026-10-11 R152 写入触发轮转搬移） · [response-R139.md](response-archive/response-R139.md)（2026-10-11 R153 写入触发轮转搬移） · [response-R140.md](response-archive/response-R140.md)（2026-10-11 R153 复核后的补搬——R152 写入时搬走 R138 后窗口仍为 11） · [response-R141-R142.md](response-archive/response-R141-R142.md)（2026-10-11 R155 集成时窗口超限搬移） · [response-R144-R153.md](response-archive/response-R144-R153.md)（2026-10-12 R161 写入触发轮转搬移，清并行欠账 R144–R153） · [response-R154.md](response-archive/response-R154.md)（2026-10-12 R165 写入触发轮转搬移） · [response-R155-R156.md](response-archive/response-R155-R156.md)（2026-10-13 R166 写入触发轮转搬移，含同日同编号「细筛」那条） · [response-R157.md](response-archive/response-R157.md)（2026-10-13 R166 分支 merge origin/develop 后窗口仍达 11，续搬最旧一节） · [response-R156-mic.md](response-archive/response-R156-mic.md) · [response-R158.md](response-archive/response-R158.md)（2026-10-13 R168 写入触发轮转搬移）（2026-10-13 R167 写入触发轮转搬移；与 response-R155-R156.md 里的同编号「细筛」条目不同事）

## 2026-10-11（R160：麦克风设备选择器）

### R160（用户场景：合盖外接显示器，iPhone 连续互通麦克风为系统输入；magicbook 页面仍无声）

- **场景定性**：M1 Pro 合盖时 macOS 硬件级禁用内建麦克风（Apple Silicon 安全设计）→ 内建麦全场景无声；用户切 iPhone 连续互通麦克风为系统默认（正确），且 iPhone 麦在其他 Mac 应用有声音——浏览器页面仍无声的最常见原因是 **per-site 设备记忆**：站点钉在旧设备上，系统默认切换不影响已记住的选择。
- **交付**：口语/复述面板各加麦克风设备下拉（enumerateDevices，权限未授予时占位编号），选中值存 localStorage 跨面板同步，getUserMedia 按 `deviceId.exact` 取流；devicechange 监听热刷新；i18n 3 词条（种子/po/mo）。
- **测试**：页面断言 + i18n 契约 + 静态完整性 = 48 passed。
- **总结**：requests.md 占号 R160（worktree 创建时登记）；本条为回应；冲突记录：无。

### R164：worktree 纪律修订——一次会话一个 worktree（手册已写入）

- **用户指令**：一次会话一个 worktree 就够了——R162 重构一个连续任务开了 6 个 worktree（五阶段 5 + NAS 下线 1）是反面做法。
- **手册落地（四仓同源 + 家族根）**：家族根 `AGENTS.md`「Git Worktree 开发纪律」新增**第 7 条：一次会话一个 worktree**（同一会话的多阶段/多子任务复用同一树，阶段 merge 回开发分支后续作前 fetch+merge 拉齐基线；跨会话优先复用台账登记的驻留树；仅并行会话允许多树并存）；moon-well/magicbook/magiclens/app-manager 四仓 AGENTS.md「Git Worktree 使用规范」节同源增补。magicbook push 首次被拒后 rebase --autostash 处理。
- **⚠️ magicbook 主检出警示（并行会话现场）**：该仓工作区有并行会话未提交工作（18 文件 +25/−753，涉及 learning/speaking_writing/i18n_seed 等），被本轮 rebase 的 autostash 收进 `stash@{0}`；恢复 pop 时与远端 R160 已合入内容冲突（UU），已按「不擅自解他人冲突」原则 `git reset --hard` 恢复安全态——**stash@{0} 完整保留对方改动，该会话回来需自行 pop 并人工解决与 614522fd（R160 麦克风选择器）的重叠**。我的 docs 提交（3fc23575）已在远端最新之上，不影响对方。
- **提交**：家族根 AGENTS.md（非 git 直接改）；moon-well 975d048；magicbook 3fc23575；magiclens ec9ae45；app-manager 4ce05bb。
- **六处驻留 worktree 的处置建议（待用户一句话）**：R162 全部代码已 merge+push+部署验证，若确认验收通过，六树可统一清理（`git worktree remove ../moon-well-<slug> && git branch -d <分支>` ×6）；按纪律等用户验收结论，不擅自删。
- **总结**：requests.md 占号 R164；本条为回应；冲突记录：无。

## 2026-10-12（R161：magicbook.haoyuhang.top 公网打不开——Tailscale 直连路径过期黑洞，已恢复）

### R161（排查任务：公网域名超时；根因 Server 2 ↔ fnOS tailnet 数据面单向失效，tailscale ping 重发现后自愈）

- **现象**：https://magicbook.haoyuhang.top/ 打不开。实测：DNS → 116.62.200.90 正常；TLS 正常（Let\'s Encrypt，2026-12-27 到期）；HTTP/2 请求发出后 15s 0 字节超时——Traefik 入口活着、后端无响应。
- **定位链**：①ctl 200 / controller 401 → Traefik 与 Server 2 本机服务正常；②内网直连 192.168.31.9:8083 → 302、容器 healthy → magicbook 服务本身正常；③moon-well.haoshenqi.top 同样超时（两站后端同为 fnOS）；④Server 2 Traefik 配置：magicbook-5771 / moon-well-5762 后端均为 `http://fnos.taila6fff7.ts.net:8083|8082`（MagicDNS）；⑤Server 2 宿主机 curl fnos :8080/:8082/:8083 全部超时、ping 192.168.31.9 100% 丢包 → tailnet 数据面断。nacos.haoshenqi.top 的「通」是假象：静态 nacos-redirect.yml priority 100 的 redirectRegex 在 Traefik 层直接 302，请求根本没到后端。
- **根因**：Server 2 ↔ fnOS WireGuard 直连路径过期未自愈——fnOS 侧家庭 NAT 重绑定（disco pong 实测端点 60.186.214.140:41641 → :45946），Server 2 仍向旧映射发包 → 单方向黑洞；两侧 `tailscale ping`（用户态 disco，不走内核路由）与 fnOS → Server 2 反向 TCP（controller 401 秒回）均正常，呈典型单向失效，自建 DERP 兜底未接管。在 Server 2 执行 `tailscale ping fnos` 强制端点重发现后数据面立即恢复（内核 ping 10ms、curl fnos:8083 302）。
- **恢复佐证**：magicbook.haoyuhang.top 连续 4 次 302（0.12–0.21s），302 → /login 全链 200（0.31s）；moon-well.haoshenqi.top 404（其对根路径的固有响应，链路已通）。旁证：magicbook/moon-well 容器当日 15:56/16:02 CST 重启过（fnOS docker daemon 自 09-25 未动，属容器级重启，与本故障相关性未证实）；fnOS dockerd 21:01 仍有容器 DNS 经 100.100.100.100 的 i/o timeout 记录，提示 fnOS 侧 tailscale DNS 代理间歇异常，建议后续观察。
- **顺带发现（独立问题，未处置）**：Server 2 tailscale `--accept-routes=false`（health check 持续告警 peers advertising routes），external-services.yml 的 vpe/nas/fn/opencode 与 es 等走 192.168.31.x 裸 IP 的后端因此无路可达（es.haoshenqi.top、nas.haoshenqi.top 实测同样超时）。改 accept-routes 还是改走 MagicDNS 属基础设施决策，待用户定夺。
- **复发风险与加固建议（均为 ops 变更，未经确认不动）**：①Server 2 加 systemd timer 定时 `tailscale ping fnos` 保活/快速重发现；②排查自建 DERP（derp.haoshenqi.top）为何未兜底；③确认 fnOS 侧 NAT 重绑定诱因（光猫/路由重拨）。
- **改动面**：零代码、零配置变更；排查中唯一「写」动作是 Server 2 上的 `tailscale ping`（无副作用的恢复动作）。
- **归档**：本条写入前窗口实存 16 条（R144–R164，含并行会话未轮转欠账），按写入即检查把 R144、R145、R147（含嵌套 R146）、R151、R152、R153 七节原样搬至 `response-archive/response-R144-R153.md` 并登记归档索引，窗口恢复 10 条。
- **总结**：requests.md 占号 R161；本条为回应；冲突记录：无撞号（R161 为空号）。requests.md 总结：追加 R161 占号条目；response.md 总结：搬移 7 节归档后写入本条，窗口 10 条。

## 2026-10-12（R162：书库两本《傲慢与偏见》对比——原著 vs 书虫改写版）

### R162（问答：book 128 为原著全文，book 337 为书虫·第6级英汉双语改写版——简化重写而非同一内容）

- **核对方式**：两本书详情页元数据（登录态浏览器抓取）＋牛津 Bookworms／外研社公开出版信息交叉验证。阅读器正文未能打开（浏览器面板中途离线），但版本定性不依赖正文。
- **结论**：
  - **book 128《Pride and Prejudice》** = Jane Austen 原著全文（纯英文，EPUB 24.8 MB，书架「英文分级·阶5（6500–9000词）」；出版日期 1998-06 与 Project Gutenberg 电子书 #1342 发布时间吻合，即 R136 批次的公版导入）。
  - **book 337《傲慢与偏见》** = 书虫·牛津英汉双语读物（第6级，外研社出版，EPUB 1.3 MB，书架「书虫·牛津英汉双语读物」；元数据系列「书虫·第6级」第 2 册为库内系列编号，非上下册分卷）——牛津 Bookworms 系列改写本（Clare West 改写），全文 29,455 词（约为原著 1/4），词汇控制在 2,500 headwords（CEFR B2/C1），英汉双语。主线情节与人物保留，但文字全部重写，**不是删节、更不是原文**。按本库分级口径：书虫 6 级约 2500 词族 ≈ 阶2–阶3；原著挂在阶5。
- **改动面**：零代码、零配置；仅对话记录（requests.md 占号 + 本条 + R154 节归档搬移 + requests.md 头部「当前最大」指针更新为 R162）。
- **归档**：本条写入前窗口 10 条，写入后超窗，最早一节 R154 原样搬至 `response-archive/response-R154.md` 并登记两处归档索引，窗口恢复 10 条。
- **总结**：requests.md 占号 R162；本条为回应；冲突记录：无撞号（追加时 requests.md 全文无 162/163 条目；注：response.md 存在并行会话 R164 回应条而其 requests.md 占号条未见，疑被并行写覆盖——按「不改既存」纪律不处理，仅留痕）。

## 2026-10-12（R165：单词详解面板头部吸顶——长内容滚动时 ✕ 不再被带走）

### R165（bug 修复：单词详解面板滚动时丢失 ✕）

- **根因**：`.reading-word-detail` 面板自身是滚动容器（`max-height: min(70vh, 560px)` + `overflow-y: auto`），词目与 ✕ 位于滚动内容之内的 `.wd-head`，滚到底时头部整体移出可视区；面板关闭路径只有 ✕ 与 Esc（R125 起无点外关闭），于是「看到最后没法关」。
- **修复**：`.wd-head` 改 `position: sticky; top: 0` 吸顶，白底铺满整行内宽。**两个坑都靠实测纠出**：① sticky 的吸顶边界是「滚动容器 padding 内缩后的区域」，第一版用 `margin-top: -12px` 把头部顶进面板那 12px 上内边距被约束回弹（头部仍停在 133px），那 12px 反成头部上方一条漏字的缝——改为把面板的 `padding-top` 移交 `.wd-head`（面板 `padding: 0 14px 12px`）；② 交叉审查指出头部的 8px 下内边距若再用 `margin-bottom: -8px` 收回（本想换取未滚动时逐像素不变），带 z-index 的白底板会压住下一行——变体说明行只有 2px 上边距，`elementFromPoint` 在变体行 top+2 处返回的是头部（gap −6px），故最终不收回负 margin，下方各行下移 8px 换零遮挡。
- **改动面**：仅 `cps/static/css/reader.css`（`epub.js` 零改动，面板 DOM 结构不变）。
- **验证**：① 同源复刻页（真实 `reader.css` + epub.js 同款面板 DOM，含变体说明行）在 headless Chrome 154 跑三态对照（控制组 develop 未修版 / 初版 `-8px` / 最终版）——滚到底时 ✕ 的 `elementFromPoint` 判定 `clickable=true`（控制组 false，✕ 落在 −1321px）；未滚动时 `head.bottom` 与变体行 `top` 的 gap 为控制组 +2 / 初版 −6 / 最终 +2；截图确认头部常驻、变体行字顶不被白底板盖住、圆角未被破坏。② 开发态单测 `tests/test_reading_vocabulary.py` 32 passed（CSS-only 改动，按两级闸门只跑受影响模块）。真机整站验收待用户在阅读器内实测。
- **L1**：`docs/readme/reading.md` 划词查词条目补「滚动时词目与 ✕ 常驻顶部」。
- **交付（上线）**：用户批准「merge + push（等于上线）」。**未走主检出 merge**——那里 `requests.md`/`response.md` 有并行会话未提交改动（R162/R163 占号与回应、还另建了一个同名 `response-archive/response-R154.md`），merge 需 autostash，正是 R164 警示过的现场；改从本 worktree `git push origin HEAD:develop`，推送前 `merge-base --is-ancestor` 验得 fast-forward，远端 `8a4eb153..2a344579`。fnOS webhook-builder 约 40 秒完成构建+部署，公网 `https://magicbook.haoyuhang.top/static/css/reader.css` 已实测到 `.wd-head` 的 `position: sticky` 规则（上线判据）。
- **上线闸门**：集成后的新基线（含并行会话 R161）全量单测 `pytest tests/` **417 passed / 0 failed**（退出码读 pytest 末行，不用管道末端）。
- **worktree 驻留待验收**：`../magicbook-sticky-detail-head`（分支 `fix/r165-sticky-detail-head`，HEAD `2a344579`）。验收方式：阅读器里划一个变体词（如 ran）→「详」→ 滚到底，词目与 ✕ 应常驻顶部且变体说明行字顶不被遮。主检出的 develop 现落后于远端，由该会话自行 rebase/pull。
- **同源**：magiclens R42 同一修法（其分支 `fix/r42-sticky-detail-head`，版本 0.8.9-202610122121），两仓详解面板继续保持同构。
- **顺带发现（未改）**：`docs/reading/hld/hld.md` 接口表仍写「R141 起内置「详」面板入口随气泡下线、本端点暂无调用方」，但 R146 起让位已改为探测 `data-magiclens-selection`，未装/旧版扩展时内置「详」与 `/ajax/reading-word-detail` 是活的——该行表述与现网行为有漂移，属并行会话文档口径，本条只记录不擅改。
- **总结**：requests.md 占号 R165；本条为回应；冲突记录：无撞号（165 为空号），但**基线漂移一次**——本分支从 fa7b9cfc 切出后，并行会话把 R161（公网超时排查）推上 develop 并**已先把 R144–R153 归档**，我这边同批归档与之撞车；按纪律 `git merge origin/develop` 拉齐后，归档文件取对方版本（正文与我的逐字节相同，仅头部注记不同），requests/response 两侧并存，合并后窗口达 11 条故再搬出最旧的 R154 至 `response-archive/response-R154.md`，窗口回到 10（R155–R165）。


## 2026-10-13（R164 续：P3 批次主体交付 + push 上线 + 部署确认）

### R164 开发与上线回应（feat/r164-whole-book-tts，worktree 驻留待验收）

- **P3 交付（commit 25489563，P1/P2 在 moon-well 侧见其 response.md R166）**：`cps/reading_tts/` 新模块——`extractor.py` 朗读口径提取器（逐条复刻 epub.js：PARAGRAPH_SELECTOR 嵌套双收、DIV 含块级后代跳过、textContent 归一、连播切块后 1/3 窗口句读；Why 不复用翻译 parser：口径差=缓存键差=整本白合成）+ `models.py`（reading_tts_job/item 镜像翻译批次表）+ `service.py`（start 幂等复用/僵尸自愈 30min/daemon 串行 0.8s≈75RPM<MiMo 100/失败重试 1 次/取消/整本选角先行且失败不阻断）；路由四件套（/ajax/reading-tts-book[/status|/retry|/cancel]，admin 门禁，身份闭包请求线程定格）+ detail.html「整本朗读」按钮（确认弹窗含积分口径说明）。**口径契约测试双锁**（设计 §3.3）：epub.js 三常量+切块算法特征静态锁、样例 EPUB 提取序列行为锁——前端口径漂移即红。
- **测试**：新增 21 例（extractor 11/service 5/routes 5）+ 相邻回归 **47 例全绿**；push 前集成基线全量 **438 passed / 0 failed**（417+21）。
- **上线**：用户指令 push。主检出代提交并行会话工作区记录（R153 先例）→ 合入 origin R165 轮 5 提交（冲突三处：requests.md 本会话二轮 edit 失误致 163 条重复——去重如实记录；归档索引取 origin 权威版；R162/R165 回应两节并存）→ merge feat 分支 → push `87e9067a..313af994`。fnOS 构建 ~1 分钟，容器健康。
- **部署确认（moon-well 侧联动）**：Nacos `tts-book-voice` 1.0.1 同步+生产选角冒烟通过（book 145《Matilda》→ voice=Mia、风格指令「轻快明亮温暖俏皮…睡前故事」——元信息进 prompt 实证）；端到端批量合成（AC②）待真机浏览器登录态验收。
- **worktree 台账（验收期驻留）**：`feat/r164-whole-book-tts`（`../magicbook-whole-book-tts`）已 merge 本地 develop 并 push；验收通过后 `worktree remove` + `branch -d`。
- **总结**：requests.md R163/R164；本条为开发+上线回应；冲突记录：R165 轮并行 push 一次基线漂移（其 response.md 已自记），本轮 merge 按「两侧并存」收敛；163 重复条系本会话二轮 edit 锚点失误，已去重并如实记录。


## 2026-10-13（R164 续二：用户验收通过，worktree 清理完成）

### R164 收尾回应

- 用户指令「清理」= 真机验收通过。两树全干净（0 modified / 0 untracked）后 worktree remove + branch -d 成功：feat/r164-whole-book-tts（P3 止于 25489563，均已并入 develop 并 push）。
- **总结**：本条为收尾回应；冲突记录：无。R164（整本朗读 magicbook 侧）闭环：朗读口径提取器（契约双锁）+批次服务+路由+入口按钮已上线，moon-well 侧选角冒烟通过（voice=Mia），端到端批量合成与扣费流水由用户浏览器验收。

## 2026-10-13（R166：每日学习中枢化——说与写并入 banner 卡片，七个功能各自子页面）

### R166（优化每日学习模块，把说与写也包括进去；banner 循环卡片 + 标题/图片/详细描述）

- **现状核对（先证后改）**：七个功能**全部已存在**，本轮不是补能力缺口而是信息架构重构——
  复习队列与选书难度匹配是 `/learning` 的两个面板，写作工坊/AI 口语陪练/复述 4-3-2/计时重读/
  听写是 `/learning/speaking-writing` 的五个 tab（模板 339 行 + `speaking_writing.js` 1097 行
  共用一套 els 注册表）。moon-well 后端与 `/ajax/learning/*` 契约**零改动**。
- **交付**（worktree `../magicbook-learning-hub`，分支 `feat/r166-learning-hub`，基线
  `origin/develop fb34c1b3`）：中枢 `/learning` = banner 轮播 + 今日计划 + 复习摘要卡 + 本周四股；
  七个子页面 `/learning/{review,match,writing,speaking,retell,reread,dictation}`；
  旧 `/learning/speaking-writing` 302 回中枢；一级导航撤掉 Speaking & Writing（R154 才提上来，
  按新 IA 收回）。
- **四项决策由用户拍板**（AskUserQuestion 四问）：全 7 项子页面化 + 中枢留复习摘要卡 /
  单卡整幅轮播（图左文右）/ 移除一级项 + 旧 URL 302 / **JS 拆成 7 个功能模块 + 公共 lib**
  （放弃低风险「守卫式复用旧大文件」，选彻底那档）。
- **前端拆分**：`learning-common.js`（HTTP 信封/CSRF/show/busy/四股字段口径表/听力素材下拉）+
  `learning-voice.js`（WebAudio 录音→16k wav→ASR，只口语与复述载）+ 中枢 + 七个功能模块，
  每页只载 common + 自己那份；删 `learning.js`、`speaking_writing.js`。元素 id 原样保留
  （`ln-*`/`sw-*`），只把 CSRF 隐藏域统一成 `lh-csrf`。
- **banner 卡片**：ImageGen 出 7 张统一风格扁平插画（4:3、画面内不放文字），`cwebp -crop
  0 0 1024 698 -resize 640 436 -q 72` 压成 webp，7 张合计 **52KB**，落
  `cps/static/img/learning/`；生成与压缩脚本在 `docs/temp/scripts/`（不跟踪）。
  **水印处理待你确认**：ImageGen 产物右下角带「Qoder AI 生成」字样，落在画面下方空白带，
  本轮按裁切底部 70px 去除（未触碰画面）；若你要求保留生成标识，改回不裁切即可。
  每张卡 = 插画 + 标题 + 详细描述（是什么/怎么玩/多久/计入哪股）+ **今日进度徽章** + CTA；
  6s 自动轮播、悬停与聚焦暂停、圆点/箭头/键盘/横滑、`prefers-reduced-motion` 关自动播；
  **今日欠账最多的那股自动排到最前**（缺口只算一次，之后不打断用户手动翻页）。
- **顺带修掉三个既有缺陷**：① **`learning.js:167` 引用从未声明的 `urls.week`** →
  严格模式 ReferenceError 被计划请求的 `.catch` 静默吞掉，**今日计划行与四股周视图自 R153
  （commit 76691314）起就不渲染**，页面照常 200、单测照常绿；本轮拆分后每模块显式声明
  `var urls = window.learningUrls || {}` 并加静态锁兜底。② 麦克风按钮录完后标签从中文跳回
  硬编码英文 `'Voice input'`，改为 attach 时读当前文案作复位值。③ 计时重读「推荐段落」入口
  三遍读完后不重置 Begin/Stop 按钮，会留下无按钮可点的死面板，现与手选段落走同一条复位路径。
- **i18n**：卡片文案走 Jinja `_()`（英文 msgid），zh po 补 **31 条**译文 + `pybabel compile`；
  6 条 JS 取词进 `i18n_seed.html`。po 改动采「构造全文→tmp→os.replace」原子替换，且**只追加
  不重写**——实测 babel 2.18 的 `write_po` 无论 width=76/None/0 都无法原样 round-trip 本仓 po
  （139,327 → 138,980/139,400 字节），重写会凭空多出上百行折行 diff，正撞并行会话冲突面。
  最终 diff：**93 行纯新增、0 删除、重复 msgid 0**。
- **测试**：新增 `tests/test_learning_pages_static.py`（替 `test_speaking_writing_static.py`：
  R158 两条锁按「模块 ↔ 它自己的模板」逐页参数化 + `urls` 声明锁 + common 先载锁 + 死脚本引用
  防回流）、`tests/test_learning_hub_cards.py`（七卡标题/配图/描述/股别/顺序、href 与 `url_for`
  一致且可打开、图文件存在且 <200KB、旧 URL 302、**卡片文案逐条向 `.mo` 取词**）；
  改 `test_i18n_seed_contract.py`（JS_FILES 换 10 个新模块）、`test_nav_settings_dropdown.py`
  （一级项不回流）、`test_learning_proxy.py`（中枢/子页面/麦克风断言按新 IA 重写）。
  开发态闸门实跑 **134 passed / 0 failed**（10 个测试文件）。另因本轮删了两份被多页共用的
  大文件，随手复跑一次全量兜底：**498 passed / 0 failed**（23.5s，非发布态闸门，
  发布态全量仍以你显式指令为准）。
- **UI 验收（本机真实 Flask + 假上游 + 无头 Chrome）**：`docs/temp/run_learning_hub_check.py`
  加 `?probe=1`（几何探针供 `--dump-dom` 读）与 `?stub=1`（替 `_moonwell_proxy` 喂固定 Result
  信封）。实证：计划行「四股时间预算（每天 40 分钟）：阅读输入 6/20min · 词汇学习 2/10min ·
  说与写 0/5min · 流利度训练 5/5min」+ 今日新词 + 摘要卡 3/20·14·212·91% +「现在有 9 个词到期。」
  + 周视图 7 行全部渲染（①的直接证据）；缺口排序首卡=听写（language 缺 8min）✓；徽章
  `今日已复习 3/20 · 到期 9`、`今日 2/10 分钟`、选书卡隐藏 ✓；13s 时轮播停在第 3 张 ✓；
  1440/768/500 三档 `scrollW ≤ innerWidth` 无横向溢出 ✓（500px 档媒体盒 220×150 纵向堆叠）；
  七个子页面与静态资源全 200。**过程中修掉一处真实缺陷**：移动端卡片图靠 `max-height` 收不动——
  `style.css:134` 的 `.container-fluid img{max-height:100%}` 与本文件同特异度且
  `layout.html` 把 header 块放在该 link 之前（18 vs 19 行），后来居上；改为给媒体盒定宽。
- **未验（需你线上真数据验收）**：真实 moon-well 下四股入账折算、七个子页面的实际练习流程
  （出题/批改/会话/朗读/听写词级 diff）、深色主题与 caliBlur 下的 banner 观感。
  本机无 calibre 书库且无合法 OIDC 令牌，这两类只能在生产验。
- **上线（同日 21:20 完成）**：用户指令「merge and push 我来验收」。merge 已在开发分支完成
  （develop FF 到 `771923c4`）；push 前在**推送基线**上复跑全量 **498 passed / 0 failed**
  （发布态闸门），随后 `git push origin develop` → `cf152a5a..771923c4`。
- **上线核验与一次自愈**：首跑 fnOS 构建成功但 **deploy 阶段失败**——`deploy.sh` 拉
  filebeat sidecar 镜像时 `docker.elastic.co/v2/` 被 `connection reset by peer`，
  两次重试后 GIVE UP（`stage=deploy-via-app-manager rc=1`），自动进 AI 修复闭环
  （streak 1）。elastic 恢复后修复链路重跑成功：`21:20:09 app-manager deploy SUCCESS` +
  `build END OK (771923c4)`。判据实测：内网 `192.168.31.9:8083` 与公网
  `magicbook.haoyuhang.top` 上 `learning-common.js`/`learning-hub.js`/
  `img/learning/*.webp` 全 200，七个子页面路由 302（受保护路由存在，非 404）。
  **本轮未动任何生产配置**，只读 ssh tail 定位根因。
- **worktree 台账（验收期驻留）**：`feat/r166-learning-hub`（`../magicbook-learning-hub`）
  已 merge develop 并 push 上线；验收通过后 `git worktree remove ../magicbook-learning-hub`
  + `git branch -d feat/r166-learning-hub`。**注**：本条上线补记与 L3 状态行回填
  （`us1-hub-banner-lld.md` 开发完成 → 已上线 771923c4）只提交在本地 develop，
  未随 push——再推一次会让容器在用户验收窗口内重启，收益仅一行文档；随下轮 push 带走。
- **总结**：requests.md 占号 R166；本条为回应；冲突记录：无撞号（追加时 requests.md 全文无
  166 条目）。归档：本条写入前窗口 11 节、写入后 12，按写入即检查把最旧的 R155、R156（细筛）
  两节原样搬至 `response-archive/response-R155-R156.md` 并登记索引，窗口恢复 10 节；
  merge `origin/develop`（并行会话的「R164 续二」收尾节）后窗口又达 11，续搬最旧的 R157
  一节至 `response-archive/response-R157.md` 并登记索引，最终窗口 10 节。
  另注：主检出工作区此前已手工追加过同一条 R166 占号文本（未提交），merge 时以本分支版本为准、
  工作区那份丢弃，不产生内容分叉。

## 2026-10-13（R167：复习队列接近义词题、判分改按 answer——同源 moon-well R171 的前端半）

- **需求**：承接 moon-well R171。后端把干扰项改成三源随机抽并新增 `DISCRIMINATE`（题干是词面、正确项是该词的同义词），前端不接就会「选对被判错」——老判分是 `picked === current.word`，而辨析题的 `word` 既不是正确项也不在选项里。
- **交付**：worktree `../magicbook-review-distractor` @ `fix/r171-review-distractor`，提交 `a8b86438`（9 文件 / +130 −34）。**未 merge、未 push**。
- **改动清单**：
  1. `learning-review.js`：判分与答后高亮改按 `answer`（老后端不发该字段时回退 `word`，行为与改动前逐字一致）；答后新增辨析说明显示。
  2. **呈现态 `mode` 与后端 `questionType` 分离**（设计外的结构决定）：旧代码就地篡改 `current.questionType` 做降级，一旦要回传题型，就会把降级后的假题型记进答题日志，且 `SELF` 是后端不认识的值。现 `mode` 只驱动渲染，回传的是后端当初发下来的题型。
  3. **未知题型兜底成 `SELF`**：原实现对不认识的 `questionType` 三个作答区都不亮，是一张没有任何作答入口的死卡；前后端发布不可能永远同刻到位，这条是那个窗口的保底。
  4. 缺释义不再误杀辨析题（R137 的「缺释义→SELF」只对释义题干成立，本类题干就是词面本身）。
  5. `learning_review.html` 新增 `ln-note` 位（不复用 `ln-feedback`——那里要被「下次再见」的调度文案覆盖）+ `learning_sub_css.html` 一行轻样式。
  6. `i18n_seed.html` + `messages.po` 新文案「下面哪个词和它的意思最接近？」，`.mo` 已 `pybabel compile` 重编译。
  7. 作答回传 `questionType`。
- **⚠️ 抓到一条会让整个「回传题型」静默失效的坑**：`cps/web.py` 的 `learning_srs_answer` 代理是**逐字段重建 body** 的，新字段不补就是无声丢弃——页面照常、后端照常返回、单测照常绿，只有答题日志的题型永远走重算（辨析题随机混出，重算会错一半），正是这次要修掉的东西。已补透传 + 三条回归锁（发则大写透传、不发则 body 形状不变、非法值本地 400 不打上游）。**通用教训**：薄透传代理每加一个契约字段，必须配一条「这个字段真的上去了」的断言。
- **命名收口**：用户界面新题型定名**「近义词题」**。本仓 L1 早就把既有的 `CHOOSE`（看释义四选一）称作「辨析题」，新题型再叫辨析题会两个题同名把人绕晕；`docs/readme/learning.md` 复习队列节一并改成 四选一 / 近义词题 / 回忆题 / 拼写题。代码常量仍是 `DISCRIMINATE`。
- **验证（不止跑绿）**：无头 Chrome 真渲染夹具（桩 `fetch` 喂队列、脚本自动点题、读 DOM 判定）跑 7 场景全部符合预期——正确同义词标绿并显示辨析、点错标红、CHOOSE 不泄词面、老后端无 `answer` 时回退判分、未知题型成可答的自评卡、缺释义不误杀、缺选项降级回忆。**变异检验**：把判分改回 `current.word` 重跑，DISCRIMINATE 场景如期把用户选对的 `trek` 标成 `btn-danger` 并弹「正确项已高亮」；还原后恢复 `btn-success`。pytest `test_learning_pages_static + test_learning_proxy + test_i18n_seed_contract + test_learning_hub_cards` → **111 例全绿**。
- **探针自身踩到的两个坑**（记下来免得重犯）：① 夹具只截 `#ln-card` 那个 div 会让模块在 `addEventListener of null` 上炸——`ln-retry`/`ln-continue` 在卡片外面，而 JS 在模块尾部无条件绑事件；② 桩 `fetch` 按 `url === '/q'` 精确匹配收不到请求，真实调用带 `?limit=20`，队列被误判成空数组、页面显示「今日达标」，表现为「卡片从不渲染」，极易误判成产品 bug。
- **worktree 台账**：`../magicbook-review-distractor` @ `fix/r171-review-distractor`（基线 `771923c4`，提交 `a8b86438`）**驻留待 P3 真机验收**；moon-well 侧配套树 `../moon-well-review-distractor` @ 同名分支（提交 `31f85a6` + `fa65b31`）同样驻留。两仓须**同批或前端先行**发布（后端先发会让老前端把近义词题判错）。
- **冲突记录**：无撞号（R167 为空号）。
- **对话记录**：requests.md 占号 167；response.md 追加本条后窗口达 11 节，续搬最旧的 R156「麦克风按钮可用性修正」一节至 `response-archive/response-R156-mic.md`（与既有 `response-R155-R156.md` 里的同编号「细筛」条目是两回事，故文件名带 `-mic` 后缀区分）并登记索引，窗口回到 10 节。

### R167 续（用户指令「推送，由我验证」= 上线：全量闸门 + push + 部署核验）

- **发布态全量闸门**：merge 进 develop 后在**新基线**重跑 `pytest tests/` → **501 passed, 0 failed**（R166 记录的是 498，多出的 3 例即本次新增的代理透传锁）。
- **merge**：`--no-ff` 提交 `c4ff5476`（前端仓 4 个提交随分支并入，含账本提交 `f56079e2`）。
- **推送**：`origin/develop 771923c4..c4ff5476`，推前 `merge-base --is-ancestor` 验得 fast-forward。**按发布顺序硬约束走前端先行**——先推 magicbook，确认线上 JS 已是新版后才推 moon-well。
- **上线判据**：`https://magicbook.haoyuhang.top/static/js/learning-review.js` 已含 `current.answer || current.word`。该串是本次新写的判分逻辑，旧构建不可能包含，因此命中的不是缓存。
- **后端侧同步核验**（moon-well 容器）：`Up (healthy)`、`Started MagicbookApplication in 20.7s`、无 ERROR 行。
- **worktree 台账**：`../magicbook-review-distractor` @ `fix/r171-review-distractor`（`a8b86438`）**驻留待用户真机验收**，验收通过后 `worktree remove` → `branch -d`。
- **交用户的验收动作**：复习队列连做 ≥10 题——①干扰项每题都变；②出现「下面哪个词和它的意思最接近？」的近义词题，选同义词应判绿并显示辨析；③四选一仍不泄露词面。
- **冲突记录**：无。

## 2026-10-13（R168：写作工坊续写——历史行可点装回任务，顶部一键继续未写完的稿子）

### R168（用户：写作历史运行继续完成上一次未完成的写作；同源 moon-well R172）

- **现状核对**：草稿正文一直存在 `learning_writing_submission.text`，但
  `GET /learning/writing/history` 从不往外带，所以历史只是摘要、没有「接着写」的路径。
  四项岔路口经 AskUserQuestion 拍板：入口＝历史行可点 + 顶部一键；取数＝新增任务详情端点
  （不在列表里塞正文）；`tips` 加列落库；已交初稿的连上次批改一起恢复。
- **交付**（worktree `../magicbook-learning-hub` 续作，基线 `origin/develop 20589dc8`）：
  - 代理 `GET /ajax/learning/writing/task`——`taskId` 只认数字（防把任意串拼进转发路径），
    非法本地 400 不打上游；合法时 GET 透传、超时 20s。
  - **提交路径收敛**：撤掉批改面板内的「修订框 + 提交修订按钮」，正文只在上层编辑区改，
    按钮文案与目标端点跟着 `lastDraftNo` 走（null→提交批改/submit、1→提交修订稿/revise、
    2→两稿已完成且禁用）。Why：续写把第 1 稿装回来后，两条路径会同时可提交同一稿，
    第二条还会撞上游 50513。
  - 历史行加状态标签（还没开始写 / 已交第 N 稿·待修订 / 两稿已完成）并可点击续写；
    顶部「继续上次未完成的写作」取列表里第一条没写完的（列表按创建时间倒序），
    全部写完则整条隐藏。
  - `applyTask` 一次铺回：mode/cefr/书名 + 题目 + 要求 + 提示 + 最新稿正文 + 该稿批改结果
    （复用 `renderReview`，不另起渲染口径）。
- **旧任务限制如实写进 L1**：R172 之前出题时 `tips` 从未落库，那些任务续写时提示行是空的
  （题目、要求、正文都在），属数据缺失而非缺陷，补不回来。
- **测试**：`test_learning_proxy.py` +4 例（登录门禁、GET 透传不裁字段、非数字 taskId 本地
  400 且不打上游、续写 UI 装配面含「旧修订框已移除」）；`test_learning_pages_static.py`
  自动覆盖新 els（`sw-w-resume*`）与模板的双向锁；i18n 种子契约覆盖 10 条新 JS 词条。
  开发态相关 116 例绿，全量 **505 passed / 0 failed**。
- **交互验收（这一步真正抓到问题）**：交互态静态断言看不见——harness
  （`docs/temp/run_learning_hub_check.py`，不跟踪）加 `probe=2` 交互探针与写作桩数据，
  无头 Chrome `--dump-dom` 读三步快照，据此抓出并修掉四个真缺陷：
  ① `armResumeBar` 写成 `if (candidate || …)`，命中后仍继续覆盖 → 一键续写挑到的是
  **最后一条**（已写完的任务）；② `refreshSubmitButton` 的 done 分支把基准文案写回初稿
  文案 → 交满两稿后按钮仍显示「提交批改」；③ `busy(btn,false)` 在 `.finally` 无条件解禁，
  把「两稿已完成」的 disabled 冲掉；④ 二次提交后状态行停留在「已恢复第 1 稿」。
  修后快照：initial `提交批改/可点/正文 0` → after-resume `提交修订稿/可点/正文 174/批改面板
  已开/overall 与逐句都在` → after-second-submit `两稿已完成/禁用/正文 212`。版面截图另看
  续写条、题目区、编辑区、批改面板、历史状态五块正常。
- **文档**：L1 `docs/readme/learning.md` 写作工坊段加续写与旧任务限制；
  L3 新增 `docs/feat/learning-hub/design/us2-writing-resume-lld.md`（含状态机表与四缺陷记录）。
- **未验**：真实账号下的续写体验与生产 `lastDraftNo` 分布需你线上验收。
- **上线（2026-10-14 08:1x）**：用户指令「推」。发布态闸门在推送基线 `ffadd9fb` 上复跑全量
  **505 passed / 0 failed**；按依赖顺序 **moon-well 先推**（`f8892fd..1ef990f`，判据＝
  `/learning/writing/task` 由 404 翻成 401，中途一次 000 是容器重启窗口，也反证 `tips`
  加列没让启动失败），再推 magicbook（`20589dc8..ffadd9fb`）。上线判据：内网
  `192.168.31.9:8083/static/js/learning-writing.js` 约 40s 后由 5,870 字节变 10,662 字节
  且含 `armResumeBar`，公网 `magicbook.haoyuhang.top` 同判据通过；moon-well 公网
  `moon-well.haoshenqi.top/learning/writing/task` 返回 401（路由在、要鉴权）。
- **worktree 台账（验收期驻留）**：本会话按「一次会话一树」复用 R166 那棵
  `../magicbook-learning-hub`（分支 `feat/r166-learning-hub`），先 `git fetch` 并 merge
  `origin/develop 20589dc8` 拉齐基线再续作；R166 与 R168 均已上线，**待你真机验收**，
  通过后 `git worktree remove ../magicbook-learning-hub` + `git branch -d
  feat/r166-learning-hub`。
- **总结**：requests.md 占号 R168（原计划记 R167，merge 新基线时发现已被并行会话的复习
  干扰项前端占用，按「不改既存、续编空号」续编；moon-well 侧 R172 条目里当时写的
  「magicbook R167」以本条为准更正为 R168）；本条为回应；冲突记录：无撞号。
  归档：本条写入使窗口达 11，把最旧的 R158 一节原样搬至 `response-archive/` 并登记索引。

## 2026-10-14（R169：整本朗读批次修复——元数据崩溃不再吃掉台账 + 停摆自愈，已 merge 未 push）

- **需求**：按方案 C 修复（①`_book_meta` 的 `book.language` AttributeError；②元数据/选角整段不得阻断批次；③retry 与 reuse 遇「停滞且有 PENDING」补线程）。现场＝《Animal Farm》(book 143) 批次 RUNNING 21 小时、0/307、307 条 item 全 PENDING 且 updated_at 冻结在创建那一刻。
- **worktree**：`../magicbook-tts-batch-fix`，分支 `fix/r169-tts-batch-preselect-selfheal`，基线 `origin/develop` ffadd9fb（切树前已 fetch）。
- **三项修法落点**（`cps/reading_tts/service.py`）：
  1. 语言改走 `book.languages` 关系，**列名是 `Languages.lang_code`（db.py:327）**——本仓 `Books` 无 `language` 标量列（关系在 db.py:428）。
  2. `_spawn_synth_worker` 改为无条件执行：元数据 + 选角整段包异常（这两步是「音色增强」而非执行依赖，崩溃最多退化成默认音色）。顺带把 `self._proxy = proxy or self._proxy` 提到选角之前——原顺序下模块级单例**首次**点击时 `self._proxy` 仍是构造期的 `None`，选角恒抛 `'NoneType' object is not callable` 被吞成默认音色（单测从构造函数注入 proxy，看不见这个洞）。
  3. 自愈判据换成**本进程线程花名册** `_live_workers` + `_needs_worker`（无活线程且有 PENDING）：`start` 的复用分支与 `retry` 都改为「原地补线程续跑」，不再「判死旧批次 + 新建台账」（那会把已合成段重走 HTTP、进度条回 0，违背批次表即断点台账的 §3.1 设定）；停滞时钟只保留「停滞且无 PENDING → 关闭旧批次」的终态收尾用途。依据：magicbook 单进程起服务（entrypoint.sh 末行 `exec python /app/cps.py`），进程内字典是权威判据；而「至少 30 分钟没 bump」证明不了当下——R169 正是创建 5 秒后线程从未起成。
- **独立 Agent 交叉审查抓出的 2 条阻断 + 3 条应修，已全部修**（这是本轮最贵的部分）：
  - 🔴 我第一版把语言列写成 `l.lang`（真列名 `lang_code`）⇒ 生产会被守卫吞成 language **恒空**，修法 1 实际未生效；更打脸的是测试夹具 `_Lang(lang=...)` 原样复制了这个编造属性——**正是本轮要根治的「替模型编造不存在的属性」问题类型**。已改代码 + 夹具 + 断言。
  - 🔴 同型存量洞：`book.comments` 是 Comments **关系列表**（db.py:218，惯用法 `comments[0].text`），旧代码把列表喂给 `re.sub` ⇒ TypeError 被吞、选角输入 summary 生产恒空。已一并修。
  - 🟡 TOCTOU 双起：Tornado 把视图跑在真线程池（`cps/server.py:251`），两个并发请求可同时通过 `_needs_worker` 预检各起一条线程 ⇒ 抢同一段、双合成双扣字符。判活与登记已合入同一把锁（`_spawn_synth_worker` 返回 bool）。
  - 🟡 注释失实：`_is_stalled` 的「补线程唯一闸门」表述、以及不存在的 `cps/web_server.py` 引用，均已更正为 `cps/server.py`。
  - 🟡 `retry()` 口径矛盾：旧实现「有 FAILED 就把 CANCELLED 批次拨回 RUNNING」与「纯 PENDING 不复活」相反；现 CANCELLED 直接拒绝并记日志。
- **测试**：`tests/test_reading_tts_service.py` 11 例，本轮新增 11 项覆盖（语言走关系、summary 取关系正文、元数据崩溃仍 spawn、首次点击选角用本次 proxy、retry 无活线程补线程、retry 有活线程不双起、spawn 原子性、CANCELLED 不复活、原地续跑不新增台账行、缺关系属性容错）。夹具 `_Book` 改为镜像真模型形状。开发态闸门：**相邻 5 个文件 59 passed**（service/routes/tts/extractor/translation/settings），worktree 与 merge 后的主检出各跑一遍同为 59 passed。
- **文档**：L3 `docs/feat/whole-book-tts/design/whole-book-tts-design.md` 新增 §12 事故复盘（含「Why 花名册而不是停滞时钟」的论证与新增 AC ⑪⑫⑬），并回填状态行——原滞留「设计定稿 v3」，实际 P3 于 10-12 提交（25489563）、10-13 已在生产实跑；L1 `docs/readme/reading.md` 补「整本预生成 + 重试原地续跑」的用户可见口径（此前该能力在 L1 完全缺位）。
- **未扩范围、等你拍板的两条**（已记入 §12 遗留③④）：① resume 分支不重做**整本选角**——评审更正了机制：speak payload 从不带 voice，音色由 moon-well 按 bookName 查 `tts_book_voice`，该批次崩溃在选角之前 ⇒ 续跑会走 `/tts/speak` 的**懒选角**（按书名+第一段定夺整本书音色并首写者锁死），比整本样本选角粗糙；补一次选角的代价是一回交互档 LLM 调用。② 建台账到首次 commit 之间的秒级并发双击会建出两个批次（存量），可加进程内 `(user, book, fingerprint)` 创建锁。
- **上线前必读**：moon-well 朗读本地后端 `qwen3-tts.service` 当前 **inactive**（8086 无监听）。不先恢复它，救起的批次会整批 FAILED。存量 Animal Farm 批次在本改动上线后点「重试」即可原地续跑。
- **交付状态**：commit `f519ea1a`，merge 进本地 develop＝`3c6689c0`，**未 push**。⚠️ 本地 develop 现领先 `origin/develop` 两个提交（我的 merge + 并行会话未推的 docs 提交 `82d2c39d`），我 push 会连带把那条一并发布，需你确认。
- **对话记录**：requests.md 占号 169；response.md 追加本条，条目 10+1 → 轮转 R159 至 `response-archive/response-R159.md` 并登记索引。冲突记录：无。
- **worktree 台账**：`../magicbook-tts-batch-fix`（分支 `fix/r169-tts-batch-preselect-selfheal`）merge 后驻留待验收；验收通过后 `git worktree remove` + `git branch -d`。
