# Calibre-Web AI 伴读版 部署指南

## 快速部署

### 1. 准备 Calibre 书库

确保宿主机上有 Calibre 书库目录（含 `metadata.db`）：
```bash
ls /path/to/your/calibre-library/metadata.db
```

### 2. 配置环境变量

```bash
cd /path/to/calibre-web
cp .env.example .env
vi .env
```

关键字段：
```bash
CALIBRE_PORT=8083
CALIBRE_LIBRARY_PATH=/path/to/your/calibre-library   # 必须指向含 metadata.db 的目录
CONFIG_PATH=./config                                   # 应用配置目录
LOG_PATH=./logs
```

### 3. 一键部署

```bash
./deploy/deploy.sh
```

其他命令：
```bash
./deploy/deploy.sh up       # 启动
./deploy/deploy.sh down     # 停止
./deploy/deploy.sh restart  # 重启
./deploy/deploy.sh pull     # 仅拉取镜像
./deploy/deploy.sh logs     # 查看日志
./deploy/deploy.sh ps       # 查看状态
```

### 4. 首次配置

1. 访问 `http://your-host:8083/`
2. 默认账号 `admin / admin123`，**请立即修改密码**
3. 若数据库未配置，访问 `/admin/dbconfig`，填写书库路径
4. 以管理员登录后访问 `/ai/admin` 配置 AI：
   - 勾选 `Enable AI Companion`
   - 勾选 `Enable long-term memory`
   - 在 DeepSeek provider 处填入 API Key
   - 保存

## 架构

```
宿主机
  └─ docker-compose
       └─ magicbook 容器 (:8083)
            ├─ /calibre-library  ← 挂载 Calibre 书库
            ├─ /config           ← 挂载应用配置 (app.db 等)
            └─ /app/logs         ← 挂载日志
```

- 镜像基于 `python:3.11-slim`，内置 `calibre`（提供 `ebook-convert`）、`ghostscript`、`imagemagick`
- 以 root 启动 → entrypoint 自动修正挂载卷权限 → `gosu` 降权到非 root 用户运行
- `tini` 作为 PID 1，正确转发 SIGTERM 信号实现优雅停止

## 日志接入 Elasticsearch（app-log-magicbook）

应用日志通过 filebeat sidecar 采集进 ES（与 moon-well 统一为 `app-log-*` 索引）：

- **日志位置**：Calibre-Web 默认把日志写在配置目录（容器内 `/config`，即 `.env` 的 `CONFIG_PATH`）：`calibre-web.log`（应用日志）与 `access.log`（访问日志，管理后台开启后生成）。注意日志级别设为 DEBUG 时应用改走容器 stdout，不落盘。
- **采集**：compose 内 `filebeat` 服务只读挂载配置目录，写入索引 **`app-log-magicbook`**，文档带 `module: magicbook` 字段。
- **配置**：`.env` 中设置 `LOG_ES_HOSTS`（默认 `https://es.haoshenqi.top:443`）、`LOG_ES_USERNAME`、`LOG_ES_PASSWORD`；文件见 `deploy/filebeat.yml`。
- **模板与保留**：`app-log-*` 统一索引模板（1 分片 0 副本）+ ILM 策略（默认保留 180 天自动删除），由 `deploy/init-app-log-es.sh` 一次性初始化（幂等，可重跑更新保留天数）：

  ```bash
  cd deploy
  ES_PASSWORD=<你的 ES 密码> ./init-app-log-es.sh
  # 调整保留天数：RETENTION_DAYS=60 ./init-app-log-es.sh
  ```

- **验证**：

  ```bash
  docker compose logs -f filebeat                                    # 采集是否正常
  curl -u elastic:<密码> http://192.168.31.9:9200/app-log-magicbook/_count
  ```

- **注意**：filebeat 镜像默认 `docker.elastic.co/beats/filebeat:8.11.3`（与 ES 8.11.3 同版本）；fnOS 拉取慢时在 `.env` 配置 `FILEBEAT_IMAGE` 指向国内镜像代理地址。部署位置：飞牛 NAS `/vol1/1000/app/magicbook`（2026-09-21 从 Ubuntu 迁入）。

## CI/CD

> ⚠️ **2026-10-06 03:39 实测更正：本仓库当前走的不是 GitHub Actions，而是 fnOS webhook-builder。**
> 判据三条（都是只读查出来的，别再按下面的 workflow 文本推断）：
> ① `GET /repos/haoshenqi-family/magicbook/actions/workflows` → `Build and Push to Aliyun` 状态是
>    **`disabled_manually`**（可随时恢复）；
> ② 仓库 webhook（id 683576412）`https://webhook.haoshenqi.top/github`、events=`push`、`active=true`，
>    2026-10-06 03:35:17Z 那次 push 的投递返回 **202**，而 GitHub Actions **没有产生任何 run**
>    （`gh run list` 最新一条仍停在 2026-09-23）；
> ③ 线上约 2 分钟后就出现了新构建的产物（`/static/js/vocab-test.js` 返 200 / 19,252 B），
>    说明部署确实由另一条链完成。
> 权威口径见项目组运维手册 `ops/apps/app-magicbook.md` §部署 与 `ops/runbook.md` §1：
> **push `develop`/`main` → `webhook.haoshenqi.top`（Server 2 Traefik）→ Tailscale → fnOS `:9877`
> 的 `webhook-builder` systemd 服务 → `build-magicbook.sh` 本地 buildx → 推 ACR `magichouse/magicbook`
> → 回调 controller `project-update` 部署 → Bark**；构建日志在 fnOS `/app/codelib/logs/magicbook.log`，
> 手动重跑 `/app/codelib/webhook-builder/build-magicbook.sh <ref> <完整sha>`。

下面这段是 **workflow 文件本身的行为**（当前处于停用状态，恢复 GHA 后才会生效，届时仍需复核是否两条链并存）：
推送到 `develop` 后（workflow 的 `on.push.branches` 写的是 `[develop, main]`，
但**本仓库没有 `main` 分支**，远端只有 `develop` 与 `master`，所以实际只有 `develop` 会触发；
注意发布用的 `master` **不在触发列表里**，合并到 `master` 不会构建，需要 `workflow_dispatch` 手动跑）：

1. 读取 `deploy/.snapshot-version` 作为版本号
2. 构建并推送镜像到阿里云镜像仓库（双 tag：版本号 + `latest`）
3. 调用 app-manager webhook 触发部署：`POST https://ctl.haoshenqi.top/api/webhooks/project-update`
   （`build-and-push.yml:72-76`；该步**没有分支条件**，`develop` 与 `main` 的 push 都会让线上容器重建）。
   旧的「SSH 到部署服务器执行 `docker compose pull && up -d`」已停用，改由 app-manager 统一接管
   （见 `build-and-push.yml:79` 注释），下表 `DEPLOY_SSH_*` 三个 Secret 因此不再被这一步使用。
4. Bark 推送构建结果通知

### 必需的 GitHub Secrets

| Secret | 说明 |
|--------|------|
| `ALIYUN_USERNAME` | 阿里云镜像仓库用户名 |
| `ALIYUN_PASSWORD` | 阿里云镜像仓库密码 |
| `DEPLOY_SSH_HOST` | 部署服务器 IP |
| `DEPLOY_SSH_USER` | 部署服务器 SSH 用户 |
| `DEPLOY_SSH_KEY` | 部署服务器 SSH 私钥 |
| `DEPLOY_PATH` | 部署目录（含 docker-compose.yml） |
| `BARK_KEY` | Bark 推送 key（可选） |

### 版本管理

- `deploy/.version`：人工维护的 release 版本（如 `0.1.0`）
- `deploy/.snapshot-version`：CI 构建版本号（格式 `版本-时间戳`）

更新版本：
```bash
echo "0.2.0" > deploy/.version
echo "0.2.0-$(TZ=Asia/Shanghai date '+%Y%m%d.%H%M%S')" > deploy/.snapshot-version
```

## 本地构建（不通过 CI）

```bash
# 构建镜像
docker build -t magicbook:local .

# 运行
docker run -d \
  --name magicbook \
  -p 8083:8083 \
  -v /path/to/calibre-library:/calibre-library \
  -v ./config:/config \
  magicbook:local
```

## 与 Traefik 集成（可选）

在 `docker-compose.yml` 取消注释 `labels` 部分，按需修改域名。或在外部 Traefik 动态配置中添加：

```yaml
http:
  routers:
    calibre:
      rule: Host(`book.example.com`)
      service: calibre
      entryPoints:
        - websecure
      tls:
        certResolver: letsencrypt
  services:
    calibre:
      loadBalancer:
        servers:
          - url: http://magicbook:8083
```
