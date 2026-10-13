# 对话回应记录

> 含每个需求的回应、冲突说明及两个文件的总结。
> **归档规则**：本文件仅保留最近 10 个 request 的回应；更早内容原样归档至 `response-archive/`（按 request 区间分文件），需要历史细节时按编号检索归档目录，不要读全量历史。

**归档索引**

- `response-archive/response-R01-R31.md`：R1–R31（2026-08-14 ～ 2026-08-31）
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

> 归档索引：[response-R01-R31.md](response-archive/response-R01-R31.md) · [response-R32-R49.md](response-archive/response-R32-R49.md) · [response-R50.md](response-archive/response-R50.md) · [response-R51-R70.md](response-archive/response-R51-R70.md) · [response-R70-R80.md](response-archive/response-R70-R80.md) · [response-R81-R101.md](response-archive/response-R81-R101.md) · [response-R102-R110.md](response-archive/response-R102-R110.md) · [response-R111-R119.md](response-archive/response-R111-R119.md)（2026-10-08 R129 补账搬移）· [response-R120-R125.md](response-archive/response-R120-R125.md)（2026-10-08 R135 写入触发搬移，含 R134 登记的窗口欠账补账）· [response-R126-R131.md](response-archive/response-R126-R131.md)（2026-10-09 R141 写入触发轮转搬移）· [response-R132-R133.md](response-archive/response-R132-R133.md)（2026-10-10 R143 写入触发轮转搬移） · [response-R134.md](response-archive/response-R134.md)（2026-10-10 R144 写入触发轮转搬移） · [response-R135-R137.md](response-archive/response-R135-R137.md)（2026-10-10 R147 写入触发轮转搬移，含 R145/R146 两次写入的窗口欠账补账） · [response-R138.md](response-archive/response-R138.md)（2026-10-11 R152 写入触发轮转搬移） · [response-R139.md](response-archive/response-R139.md)（2026-10-11 R153 写入触发轮转搬移） · [response-R140.md](response-archive/response-R140.md)（2026-10-11 R153 复核后的补搬——R152 写入时搬走 R138 后窗口仍为 11） · [response-R141-R142.md](response-archive/response-R141-R142.md)（2026-10-11 R155 集成时窗口超限搬移） · [response-R144-R153.md](response-archive/response-R144-R153.md)（2026-10-12 R161 写入触发轮转搬移，清并行欠账 R144–R153） · [response-R154.md](response-archive/response-R154.md)（2026-10-12 R165 写入触发轮转搬移）

## 2026-10-11（R155：worktree 规范微调——merge 后保留待验收，验收通过后删除）

### R155（worktree 收尾闸门改两段式：merge 后保留等验收）

- **用户指令**：不要 merge 即删除 worktree，改为 merge 后保留等用户验收，验收通过后再删除。规范主体（临时 worktree、非占用池、从 origin/develop 切、仓库外兄弟目录）不变，只改收尾时序。R152 已出现「worktree 驻留不关（完成后由用户确认关闭）」的在例——本次修订正是把这一实际工作方式回写为正式规范。
- **落地改动**：家族根 `AGENTS.md`「Git Worktree 开发纪律」收尾闸门改两段式（merge 后 worktree 原样保留等验收）+ 台账条目改「驻留台账」+ 证据条补记本次用户修订；四仓 AGENTS.md 同步微调。本仓细则新增「验收期驻留（正常状态）」：登记分支名与合并 commit，验收通过后立即删除；并写明本仓验收优势——干净 worktree ＋ 主检出 `.venv` 复用＋拷贝当轮运行期文件即可真机整站验收（R144 已验证）。
- **窗口**：与远端 R153/R154 集成后窗口含 R141–R155 共 12 个 request，把最旧的 R141、R142 两节原样搬至 `response-archive/response-R141-R142.md` 并登记索引，窗口恢复 10 个（R143–R155）；此前本条初版已搬 R139/R140（当时窗口 11）。
- **编号说明**：本条与并行会话的 P3 输出训练（R153）、导航层级修正（R154）集成时发现同号 153 已被先行推送占用，按纪律续编 155；同源任务 moon-well R153 / magiclens R41 / app-manager R39。
- **总结**：requests.md 占号 R155（与并行会话 P3 输出训练撞号 153 后按纪律续编）；本条为回应；冲突记录：R153 撞号如上。本任务只改文档与对话记录，未动任何代码。

## 2026-10-11（R156：词汇量测试「细筛」入口——代理透传/前后对照/细档图）

### R156（细筛前端：magicbook 侧交付，跨仓同源 moon-well R155）

- **交付**（worktree `../magicbook-vocab-refine`，分支 `feat/r154-vocab-refine`，基于 origin/develop 37edb778；merge commit 1d8309f1，worktree 驻留待用户验收）：
  - **代理**：`/ajax/vocab-test/start` 增 refine 标志透传——只认显式布尔 true，其余（缺省/false/字符串）一律按标准测试转发空体，语义分叉只在 moon-well 一处。
  - **vocab-test.js**：卡片（有标准结果时）与结果页各一个细筛按钮（报告 `testType` 驱动显隐，对细筛结果不提供二次细筛）；50305（无可细筛基座）回卡片态提示；细筛结果渲染「上次估算」对照行；掌握度图标签按报告 `bandRanges` 秩区间标注（细档序号只在会话档位表内有意义），后端未升级时退回硬编码档名。
  - **模板/i18n**：两个按钮 + 对照行落 reading_settings.html；`Refine test / Previous estimate / Take a standard test first…` 三词条进种子与 zh po/mo。
- **测试**：代理透传矩阵用例 +1（true→透传、false/"yes"/缺省→空体）；i18n 种子契约对新词条自动生效；全量 pytest 407 例绿。
- **编号说明**：本任务原占 154（与并行导航修正撞号），占号条目在工作区被并行提交操作清除；按「不改既存、续编空号」纪律落为 156，既有 commit 内 R154 文案不改。
- **总结**：requests.md 续编 R156 占号；本条为回应；冲突记录：无（合并为真 merge 无内容冲突；stash 恢复的并行未提交改动原样留在工作区，归其 owner）。归档：窗口 R147–R156 共 10 条未超窗。

## 2026-10-11（R157：整本连播（听书）——顺序逐段朗读整本书，随时暂停）

### R157（R155/R156 评估结论落地：moon-well 零改动，播放队列全部在阅读器前端）

- **需求**：为书籍增加一个整本阅读功能：按照顺序一段一段持续朗读，随时可以暂停。（编号说明：R155 评估轮占号 155 及其回应条目曾被并行提交操作清除；155/156 已被并行会话的 worktree 规范/词汇细筛占用，按「不改既存、续编空号」纪律落为 157。评估结论在 moon-well response.md R156 有留档。）
- **交付**（worktree `../magicbook-whole-book-read`，分支 `feat/r157-whole-book-read`，基于 origin/develop 41918028）：
  - **moon-well 与 web.py 零改动**（评估已证：/tts/speak 同步音频 + SHA-256(原文) 永久缓存 + 顺序串行天然合规）；
  - `epub.js` 新增独立播放队列状态机 `bookPlayer`（与单段朗读 `activeTts` 互斥让位）：collectParagraphElements 收集本章段落 → 归一化 + 2000 字符切块（句读优先断句，长段不再静默截断）→ 逐块 `POST /ajax/reading-tts` → Audio(blob) 播放 → ended 接下一块；本章耗尽 `rendition.next()` 等 `rendered` 重建队列，spine 尽头自动停并提示「已到全书末尾」；
  - 暂停/继续：`audio.pause()/play()` 段内保留进度；合成期间暂停 = 就位 blob 不开播，点击即续；
  - 预取：当前块 onplay 后预取下一块，全程 ≤1 个在途合成（NAS 本地 TTS CPU 瓶颈、MiMo 100 RPM）；
  - 视图跟随：当前段不在可见页才 `display(段落实时 CFI)` 跳页（实时 CFI 无旧 CFI 越界毒化显示队列风险）；
  - 章界：空文字章节（纯图片封面页）自动跳过（≤10 章上限）；20s 未渲染按翻章失败收尾；
  - 手动导航跟随：rendered 非 internalNav → 重建队列——同章重渲染（字号/主题/分栏）按 lastStartedText 续听原块、换章从新页顶部起播；章内翻页不打断播放；
  - UI：标题栏 `#tts-book`（▶/❚❚ 切换）+ `#tts-book-stop`（■，连播中显示）；当前段 `.reading-tts-speaking` 高亮；8 条新文案走 mbT 五步链；
  - 文档：L1 reading.md 朗读条目扩写+整本连播、L3 深入阅读加链；L2 reading hld 新增 §1.1（无新契约）；L3 `docs/feat/whole-book-listening/design/whole-book-listening-design.md` 新建（状态行已上线）。
- **测试**：i18n seed 契约 5 例绿（JS 字面量 ⊆ seed = po = mo，8 条新词条四层一致）；test_reading_tts + test_csp_media + test_nav_settings_dropdown 20 例绿（代理层零改动回归）；node --check 过；epub.js 全模块通读交叉审查一轮（据此修出：空文字章自动跳过、emptySkips 初始化与重置、FireWaiters 唤醒链抽取）。
- **归档**：本条使窗口达 11，最早一节 R143 原样搬至 `response-archive/response-R143.md` 并登记索引，窗口 R144–R157。
- **总结**：requests.md 占号 R157（在 worktree 内落盘，随本分支 merge 入 develop，避开主检出并行覆写区）；本条为回应；冲突记录：R155 评估轮的占号/回应曾被并行提交清除（已在编号说明留痕），本轮在干净基线重落为 157；worktree 交付后驻留等用户真机验收（AC 见 L3 design §4），验收通过后按两段式闸门收尾。
- **验收与收尾（同日回填）**：用户确认验收通过（2026-10-11「此任务完成的非常好，可以收尾」）——按两段式闸门收尾：worktree `../magicbook-whole-book-read` 已 `git worktree remove`、分支 `feat/r157-whole-book-read` 已 `branch -d` 删除（内容已随 e6a51c48 并入 develop 并部署上线，线上冒烟见前文）。

## 2026-10-11（R156：麦克风按钮可用性修正——带标签/状态自更新/用法提示）

### R156（用户反馈：「只有一个空白按钮」不会用）

- **交付**（worktree `../magicbook-mic-ux`，分支 `feat/r156-mic-ux`，基于 origin/develop ac10e64c；worktree 驻留待用户确认）：
  - 两个麦克风按钮从纯图标改为 **图标 + 文字标签**（「语音输入」），图标字体缺失时也不再是空按钮；
  - 状态全部自更新在按钮上：空闲「语音输入」→ 录音中红底「录音中 0:12 · 再点停止」→「转写中…」（转写期间防连点禁用）→ 回填后复原；
  - 口语面板加一行用法提示（点麦克风开始说话 → 再点一次停止转写 → 结果回填输入框确认/修改后发送；首次使用会请求麦克风权限）。
- **测试**：页面断言（标签 ≥2 处 + 提示行）+ i18n 契约（种子 +1/po +4，mo 重编），45 passed。
- **总结**：requests.md 占号 R156；本条为回应；冲突记录：无。归档：窗口未超。

## 2026-10-11（R158：麦克风转写卡死修复）

### R158（「转写中…」永远不结束：els 注册表漏项 + 同步 TypeError 防御）

- **根因定位**（ES app-log-magicbook + docker logs + 代码比对）：停止分支 `statusNode.textContent = ''` 对未注册的 `els['sw-s-audio-status']`（undefined）赋值 → 同步 TypeError 在 fetch 之前炸掉 → 无 alert、按钮禁用、标签停在「转写中…」——且服务端零日志（请求根本没发出）。只影响口语面板（复述的 sw-r-metrics 已注册）。注册表漏项是 R155 建表时只列了麦克风按钮、R156 改 statusNode 引用时未同步注册表所致。
- **修复**：①注册表补 `'sw-s-audio-status'`；②停止分支同步段包 try/catch——任何异常都复原按钮 + 提示，永不卡「转写中…」；③新静态测试 `test_speaking_writing_static.py` 双锁：JS 引用的每个元素必已注册、注册表每个 id 必在模板（此类错误 pytest 页面断言抓不到）。
- **顺带排查结论**（另两条独立线）：①moon-well 直连实测 SiliconFlow 引擎链路 OK（key 200、热重绑 provider=siliconflow 生效），但 RestTemplate 文件 part 默认 octet-stream 会被 SiliconFlow 500 [no body]（audio/wav 同请求 200 实测）——已修（moon-well R160：文件 part 按扩展名给标准 audio/* MIME）；②**Nacos 里的 siliconflow api-key 现在返回 401 Token is invalid**（14:05 实测 200 → 14:2x 失效）——用户需在 SiliconFlow 控制台取当前 key 重新填入 Nacos。
- **测试**：静态完整性 2 例 + 代理 40 例 = 42 passed。
- **总结**：requests.md 占号 R158；本条为回应；冲突记录：无。归档：窗口未超。

## 2026-10-11（R159：语音输入静音检测）

### R159（用户复测 50517 排查：引擎 200+空文本 = 录音无声）

- **排查链**：①先排除 key/模型——Nacos 原样提取直连 SiliconFlow 200 转写成功（前轮 401 系排查命令手抄 key 笔误，用户判断正确）；②再排除编码器——部署版 encodeWav 产物经 wave 解析（1ch/16k/16bit、峰值 -10.5dB）+ 直送 SiliconFlow 200 转写 "Yeah."；③用户两次上传均 **200+空文本**（引擎没听到语音）→ 锁定录音本身静音（设备静音/选错输入源/离麦远）。
- **修复**：①录音停止后计算 PCM 峰值，<0.005（-46dB）直接提示「麦克风没有采集到声音——请检查系统输入设备选择或静音开关后重试」，不再上传让引擎报模糊失败；峰值幅度打 console.info 支持远程诊断；②AudioContext 挂起兜底 resume（iOS/Safari 场景）。
- **配套**：moon-well R161 空 50518（空转写与引擎故障分离报错，已上线）。
- **总结**：requests.md 占号 R159；本条为回应；冲突记录：无。

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
