# 归档 — R210 伙伴图片与 MinIO CSP 源清单收敛

> 2026-10-24 R213-C / R217 / R221 在 develop 合流后窗口达 11 节触发轮转搬移，原样搬移不改写。

## 2026-10-23（R210：伙伴图片未生效的定性与 MinIO 入口切换的 CSP 侧——源清单收敛单点、过渡双源）

### R210（用户：「伙伴的图片似乎没有起作用」→「我知道了，我的网络会拦截 https://home.haoshenqi.top:9001。minio地址改为 https://minio.haoshenqi.top，只是入口不同，后端一样」）

- **根因**：不是鉴权、不是 CSP 写错，而是**出口入口本身被用户网络拦**。伙伴头像与 TED 原声都按 moon-well 的 `minio.public-url`（现网＝`home.haoshenqi.top:9001`）拼直链，浏览器取不到对象；magicbook 侧 CSP 又硬编码同一源，所以「换入口」天然是两仓联动改动。
- **入口等价性实测**：同一 TED 对象经两入口 HEAD 得 `Content-Length=10391127`、`ETag=f39b066b…-2` 完全相同；小 PNG 另比 sha256 亦相同 ⇒ 确认「只是入口不同，后端一样」。DNS 侧 `minio.haoshenqi.top`→8.139.5.79（VPS，443 经 lucky 反代），`home.haoshenqi.top`→61.153.123.227（仅 :9001 可达）。
- **本仓改动**（commit `4944b350`）：`cps/web.py` 新增 `MINIO_PUBLIC_ORIGINS` 单点清单，`media-src`（R181 TED 原声）与 `img-src`（R207 伙伴头像）都由它拼——原先两处各写一遍同一个源，这正是「改基址必然两处同坏」的结构性原因。**过渡期两源并列**：magicbook 先松 CSP，moon-well 再翻配置，避免翻转窗口内 TED 原声与伙伴图同时被拦；待再无任何响应产出旧源，删旧条目单独一笔收窄（注释里写死了这条后续动作，别夹进功能改动）。
- **测试**：TED 用例改为断言两源并列；伙伴用例改为参数化断言两源；反向守卫加严——`web.index` 不得出现任一 MinIO 源，另加一条「img-src 不得被放宽成通配 / 不得混入无关源」。全量 `.venv/bin/python -m pytest tests/` = **700 passed / 0 failed**（含并行会话 R208 banner 用例与本轮新增）。
- **排查过程里我的两次探针失误（如实记）**：① 内置浏览器打开 `/buddy` 显示「Failed to load」、`ajax/buddy/catalog` 回 401，我几乎据此判成 buddy 专属缺陷——跑对照组发现**同一会话里 `ajax/achievements-summary|detail|pending` 也全 401**，那只是内置浏览器会话的 moon-well 令牌失效，证据无效；真正可用的是服务端 `mk-` 系统身份直探 `/buddy/catalog`（回 200 且 imageUrl 正常下发）。② 第一次比两入口我用 `curl -m 20` 直接下载，10MB 对象被**我自己的超时**截成 8.69MB，差点报成「两入口内容不一致」；改用 HEAD 比 `Content-Length`/`ETag` 才对。另有一次把「docker logs 里查不到 buddy 请求」当成「前端没发请求」——magicbook 根本不按请求写 stdout（访问日志在 ES），是探针无效而非事实。
- **跨仓同源**：moon-well R206——`minio.public-url` 三处消费方原为 `@Value` 且全仓无 `@RefreshScope`，配置发布后日志照打 `Refresh keys changed` 却不生效，叠上部署侧「代码指纹相同→跳过重启」，**只改配置会永久卡旧值**；改走仓内既有范式 `@ConfigurationProperties`。
- **台账与驻留**：requests.md 首占 R209（11:45，commit `0cd89023`），12:51 并行会话在 `26526677`（承接 moon-well R205）里也用了 R209；其记录已入 develop，本方按「后到者让号」续编 **R210**，他们记录一字未动。两轮撞号的共同根因：双方未推分支上的号彼此不可见，「先占即提交」只防已推侧。；分支 `feat/r206-buddy` 复用同一 worktree `../magicbook-buddy`，先 merge `origin/develop` 拉齐基线；worktree 原样驻留待真机验收。**本轮改动尚未 push**（等确认；顺序：先推本仓松 CSP → 再推 moon-well → 最后翻 Nacos 配置）。
- **发布完成（2026-10-23 13:5x）**：全量 `pytest tests/` = **700 passed / 0 failed**（合并基线，含并行会话 R209 充值前端用例与本轮 CSP 用例）；push `163b9784` → fnOS `13:51:58 START → 13:52:15 END OK`，代码指纹 `221ec91c… → 06ba7c25…` 不等故完整部署、`deploy SUCCESS`。**线上头级验证**：`/buddy` 的 `img-src 'self' data: https://minio.haoshenqi.top https://home.haoshenqi.top:9001`（双源到位、新源在前），反向对照 `/login` 仍是 `'self' data:`（窄面未被放宽）。moon-well 侧随后翻 `minio.public-url`，catalog 已改吐新入口（详见 moon-well R206 补记）。合并时又撞一次：我方条目最终 R210（详见「台账与驻留」）。**余下唯一未验项仍是带鉴权的肉眼验收**——头级证据只能证明「不拦」，不能证明「画出来了」。

- **窗口（重复轮转已作废）**：我方写入时分支窗口仍带着那节标题壳为「2026-10-16（R130…）」、正文实为 `### R190` 的块，我把它另立成 `response-archive/response-R190.md`——但**并行会话早已把同一节并入 `response-R130.md`**（我方自己的索引第 32 行就记着这件事），我那份是重复副本，合并时**删除副本、以 develop 为准**。以 develop 为基追加本条后窗口达 11 条，真正该搬的是最旧的 **R191**，已原样搬至 `response-archive/response-R191.md` 并登记索引，窗口回 10。根因与本轮两次撞号同源：**未推分支上的窗口态与编号都互相不可见**，搬移/占号前必须对 develop 复核。
