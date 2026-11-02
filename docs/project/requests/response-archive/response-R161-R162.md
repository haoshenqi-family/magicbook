# response-archive：R161–R162（2026-10-12）

> 原样搬移自 `response.md`（2026-10-14 R173 写入触发轮转，窗口转入 R165 起）。

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
