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
       └─ calibre-web-ai 容器 (:8083)
            ├─ /calibre-library  ← 挂载 Calibre 书库
            ├─ /config           ← 挂载应用配置 (app.db 等)
            └─ /app/logs         ← 挂载日志
```

- 镜像基于 `python:3.11-slim`，内置 `calibre`（提供 `ebook-convert`）、`ghostscript`、`imagemagick`
- 以 root 启动 → entrypoint 自动修正挂载卷权限 → `gosu` 降权到非 root 用户运行
- `tini` 作为 PID 1，正确转发 SIGTERM 信号实现优雅停止

## CI/CD

推送到 `develop` 或 `main` 分支后，GitHub Actions 自动：

1. 读取 `deploy/.snapshot-version` 作为版本号
2. 构建并推送镜像到阿里云镜像仓库（双 tag：版本号 + `latest`）
3. **仅 develop 分支**：SSH 到部署服务器执行 `docker compose pull && up -d`
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
docker build -t calibre-web-ai:local .

# 运行
docker run -d \
  --name calibre-web-ai \
  -p 8083:8083 \
  -v /path/to/calibre-library:/calibre-library \
  -v ./config:/config \
  calibre-web-ai:local
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
          - url: http://calibre-web-ai:8083
```
