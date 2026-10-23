## 2026-10-21（R191：写作批改 503 复发——代理预算小于后端 LLM 预算）

### R191（用户：近期没有部署，revise 还是 503）

- **证据（moon-well 访问日志）**：`15:43:04` 的 revise 实际返回 **200**、耗时 **104494ms**，而 magicbook 代理 `timeout=90` 先到点 → 统一返回 `learning b1: /learning/writing/revise service unavailable`；`15:49` 另一次 200 / 79814ms；`16:04`、`16:06` 两次在 magpie 150s 预算处超时。前两次是「后端成功、前端假 503」，后两次是「后端 150s 失败、前端 90s 已先 503」。
- **根因**：客户端代理预算（90s）< 后端 LLM 预算（150s，Nacos `moon-well-ai.yaml` 的 `magpie.timeout-ms: 150000`）。与蓝绿部署无关；15:40 那次才是部署停机窗口。
- **改动**：`cps/routes/learning.py` 新增 `_WRITING_LLM_TIMEOUT = 210`（后端 150s + 落库/网络余量），`/ajax/learning/writing/submit` 与 `/revise` 使用；`task/generate` 保持 90s。前端不加自动重试——幂等由 moon-well R193 保证（相同正文复用上一稿批改），自动重试只会放大供应商压力。
- **中间层核对**：Server 2 Traefik 未配置 `readTimeout/writeTimeout`（写超时默认不限）、fnOS Caddy 无响应超时、浏览器 `fetch` 无默认超时，210s 不会被先掐断。
- **测试**：`pytest tests/test_learning_proxy.py` → **52 passed**；新增 `test_writing_review_timeout_covers_backend_llm_budget`，锁住 submit/revise 两个入口的转发超时为 210s。
- **文档**：L1 `docs/product/readme/learning.md` 补「长文批改 1–3 分钟、原样重试不会多一稿」；LLD §5 记录证据、根因与预算口径。
- **收尾**：分支 `fix/r191-writing-timeout`，merge develop **`a070a9fe`**，push 后 fnOS 构建 **END OK**、容器 `Up (healthy)`；`docker exec magicbook grep _WRITING_LLM_TIMEOUT /app/cps/routes/learning.py` 确认线上为 **210**，submit/revise 两处均引用该常量。全量闸门沿用 R190 已复现的本机基线（13 个 Python 3.8/书库 fixture 失败）；本轮定向 `pytest tests/test_learning_proxy.py` **52 passed**。真实 >90s 链路需用户会话 + 长文，未做线上代理计时；预算与中间层超时已在 LLD §5 逐项核对。

- **上线后真实批改复验**：moon-well 同一 task=3 追加一句新正文后调 revise，**71.4s** 返回 `draftNo=4`、`progress=true`；该耗时已超过旧 90s 预算的边缘区间，新 210s 预算可完整承接。代理层未改业务逻辑，幂等复用路径由 moon-well R193 保证。

### R192（部署链纯文档跳过构建/部署）

- **范围**：用户指令「修改一下部署脚本，如果只有文档更新，则不触发部署」；四仓同源 + 「触发但跳过构建/部署」两口径拍板。
- **改动**：`.github/workflows/build-and-push.yml` 新增 `changes` job（compare API 取改动文件 + 文档口径正则），`build` job 加 `needs` / `if` 门禁；纯文档 push 时镜像构建、ACR 推送、`project-update` 部署通知整体跳过，step summary 留痕。
- **文档口径**：`docs/`、`doc/` 下任意文件、`*.md`、`LICENSE`、`.gitignore`、`.gitattributes`。安全侧兜底同上（首次推送 / 手动触发 / API 失败 / ≥300 文件一律走完整构建）。
- **验证**：YAML 解析通过、`bash -n` 通过、桩响应端到端 5 例符合预期（纯文档 true，其余 false）。
- **适用性提醒**：本仓 **GitHub Actions 主链已手动停用、现役是 fnOS webhook-builder 链**（`../ops/runbook.md` §1），因此本次改动属**预案**——恢复 GHA 或切回主链即生效；fnOS 链的同一判据待单独处置（脚本在 fnOS，本轮无 SSH 凭据）。
- **驻留**：worktree `../magicbook-doc-skip-deploy`，分支 `chore/r190-doc-skip-deploy`，合并 commit `a8c2af35`（本地 `develop`，未 push）。
- **补记（2026-10-21 15:55，覆盖面缺口已关闭）**：R153 记的「fnOS 链未加判据，纯文档 push 仍会构建部署」当轮补齐——fnOS `pipeline_lib.sh` 新增 `docs_only_diff` + 基线 marker（`logs/.magicbook.deployed-sha`），`build-magicbook.sh` 在 checkout 后插入 `scope-check`：纯文档时打印 `build SKIPPED (docs-only) (<sha>)` 并 `exit 0`，不构建镜像、不触发 project-update 部署、不发 Bark；`drift-check-build.sh` 已把 SKIPPED 视同 `END OK`。实测 4 例 + 端到端纯文档跳过全符合预期。详见 `../ops/runbook.md` §1 与 ops R154。

### R193（收敛 fnOS 单链 + 部署前按代码指纹判等，2026-10-21）

**背景**：magicbook 的 GHA 早已 `disabled_manually`，现役是 fnOS 链，所以「只留 fnOS」这条对本仓是**补齐代码与事实的一致性**——workflow 文件里还写着 push 触发、还挂着 R190 的 `changes` job，一旦有人 re-enable 就会双链复发。

**改动**

- `.github/workflows/build-and-push.yml`：只留 `workflow_dispatch`，删掉 `changes` job 与 build 门禁。
- 新增 `deploy/fnos/deploy.sh`：这就是 `/app/magicbook/deploy.sh` 的版本化副本——此前它只存在于 fnOS 项目目录，仓库里的 `deploy/deploy.sh` 是另一个 139 行的开发者多功能脚本，两者不是一回事。以后改部署逻辑要改 `deploy/fnos/` 这份并同步过去。
- 判等：`docker compose pull magicbook` 之后比新镜像与在跑容器的 `house.code-digest`，一致则打印「镜像代码指纹未变 -> 跳过重启」并退出——不停容器、不 `up -d`。原来的 `stop` + `start` 有停机窗口，判等直接把这窗口也省掉。

**验证**

- 假 docker 三例：指纹一致→跳过（`up -d` 0 次）；指纹变化→`[2/3]` 部署（1 次）；旧镜像无 label→保守部署（1 次）。
- 真实构建实测（只跑到 push 为止，不触发部署）：镜像 label `code-digest=d73089e559f6bab3`、`build-sha=1b3428d5…`，与 `code_digest HEAD` 算出的值一致。

**状态**：worktree `../magicbook-doc-skip-deploy`（分支 `chore/r191-deploy-skip-unchanged`），未 push。
