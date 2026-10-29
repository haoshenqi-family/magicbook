# response 归档：R231（2026-10-26）

> 2026-10-29 R243/R244 并行写入均轮转到本节，正文一致；保留单份，原样搬移不改写。

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
