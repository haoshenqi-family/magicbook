# LLD · R231 去掉 PyPI 镜像的 pip trusted-host（关闭 TLS 校验＝构建链投毒面）

状态：已实现待验收（2026-10-26）｜关联：R231 / PingCode MAGICBOOK 需求池｜基线分支：`fix/r231-pip-trusted-host`

## 这次怎么实现

**根因**（安全扫描高危 6）：`Dockerfile:5-6` 用 `pip config set global.index-url https://...` 之后又设了 `global.trusted-host mirrors.aliyun.com`。`trusted-host` 的语义是**对该 host 跳过证书链与主机名校验**——任何处在构建机与镜像之间的人出示任意证书，pip 都会当成阿里云镜像接受。而构建发生在 fnOS（`../ops/tools/webhook-builder/build-magicbook.sh:74-75`，push develop 即触发），出网走自建出口（`.9:12811` naive / `7891` sing-box），同内网任一设备、构建上任一低权进程、出口本身、以及镜像站上游同步链，都在这条信任路径上。

**改动**：删 `Dockerfile:6` 一行，保留 `index-url`（换源不是问题，关校验才是）。

**为什么可以直接删——两条实测证据**（这行当年可能是为了绕证书错，所以前提必须验）：

1. 基础镜像自带 CA：`python:3.11-slim-bookworm` 上游 Dockerfile 第 22-29 行在 `FROM debian:bookworm-slim` 之后即 `apt-get install -y --no-install-recommends ca-certificates netbase tzdata`；本仓 stage 1（`Dockerfile:9-18`）虽没装 `ca-certificates`（只有 `libssl-dev`），但基础层已有，pip 能取到 CA store。stage 2 的 `ca-certificates`（`Dockerfile:47`）与此无关。
2. 镜像站证书本就正常：本机实测 `curl https://mirrors.aliyun.com/pypi/simple/` → `HTTP 200`、`ssl_verify_result=0`（用系统 CA 校验，未加 `-k`）。

**没做到的验证（诚实边界）**：本机 Docker daemon 未运行，没能真跑一次 `docker build` 证伪。首次 fnOS 构建即为验收点——日志里若出现 `CERTIFICATE_VERIFY_FAILED`，说明上述前提在构建机上不成立（例如代理做了 TLS  interception 却没把企业根证书放进镜像），那时要修的是证书链，不是把 `trusted-host` 加回来。

## 范围之外（本条刻意不做）

同一信任面上的另一半是**没有内容校验**：`Dockerfile:26` 的 `pip install -r requirements.txt` 没有 `--require-hashes`，而 `requirements.txt` 每行都是 range、无 lock 文件——即便 TLS 正常，装什么仍由镜像站当时的返回决定，同一 commit 两次构建可得不同包。彻底收口需要出一份带 hash 的锁文件（`pip-compile` + `--require-hashes`），那会牵动全量依赖解析，属独立需求，不在本条顺手做。基础镜像按 digest 钉、`moon-well/Dockerfile:15` 的 Maven `mirrorOf=*` 同理另排。

## 交付四问

能力未变（用户看不到任何差异）→ L1 不动；契约未变 → L2 不动；实现/边界变了（构建期凭据信任模型）→ 本 LLD + Dockerfile 内注释；无测试覆盖 Dockerfile（本仓 `tests/` 均为 Flask 层用例），验证以上两条实测证据 + 首次构建日志。
