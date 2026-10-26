# 回应归档 · R221–R222

> 2026-10-26 R232 写入触发轮转搬移，原样搬移不改写。

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
