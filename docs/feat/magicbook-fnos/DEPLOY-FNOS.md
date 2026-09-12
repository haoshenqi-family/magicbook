# Magicbook 飞牛OS 部署指南

## 概述

本指南帮助你在飞牛OS上以 docker-compose 形式部署 Magicbook（Calibre-Web AI 伴读版）。

## 前提条件

1. 飞牛OS 已安装 Docker 和 Docker Compose
2. 已准备 Calibre 书库目录（包含 `metadata.db`）
3. 已配置 AI 服务（DeepSeek API Key 等）

## 目录结构

在飞牛OS上创建以下目录结构：

```
/vol1/docker/magicbook/
├── calibre-library/    # Calibre 书库（必须包含 metadata.db）
├── config/             # 应用配置（app.db、settings.yaml 等）
├── logs/               # 日志目录（可选）
├── docker-compose.yml  # Docker Compose 配置
└── .env                # 环境变量配置
```

## 步骤 1：创建目录

```bash
# 在飞牛OS文件管理或SSH中创建目录
mkdir -p /vol1/docker/magicbook/calibre-library
mkdir -p /vol1/docker/magicbook/config
mkdir -p /vol1/docker/magicbook/logs
```

## 步骤 2：准备 Calibre 书库

将你的 Calibre 书库（包含 `metadata.db`）复制或挂载到 `/vol1/docker/magicbook/calibre-library/`。

```bash
# 示例：假设你的书库在 /vol2/Books
cp -r /vol2/Books/* /vol1/docker/magicbook/calibre-library/
```

## 步骤 3：创建 docker-compose.yml

在 `/vol1/docker/magicbook/` 目录下创建 `docker-compose.yml`：

```yaml
services:
  calibre-web:
    image: registry.cn-hangzhou.aliyuncs.com/magichouse/magicbook:latest
    container_name: magicbook
    restart: unless-stopped
    ports:
      - "8083:8083"
    environment:
      CALIBRE_PORT: 8083
      CALIBRE_DBPATH: /config
      CALIBRE_LIBRARY: /calibre-library
      TZ: Asia/Shanghai
      CALIBRE_CONFIG_RECONNECT: 0
    env_file:
      - .env
    volumes:
      - /vol1/docker/magicbook/calibre-library:/calibre-library
      - /vol1/docker/magicbook/config:/config
      - /vol1/docker/magicbook/logs:/app/logs
    user: "0:0"
    healthcheck:
      test: ["CMD", "nc", "-z", "localhost", "8083"]
      interval: 30s
      timeout: 10s
      start_period: 40s
      retries: 3
```

## 步骤 4：创建 .env 文件

在 `/vol1/docker/magicbook/` 目录下创建 `.env` 文件：

```bash
# ========== 端口 ==========
CALIBRE_PORT=8083

# ========== 数据卷路径 ==========
CALIBRE_LIBRARY_PATH=/vol1/docker/magicbook/calibre-library
CONFIG_PATH=/vol1/docker/magicbook/config
LOG_PATH=/vol1/docker/magicbook/logs

# ========== AI Reading Companion（可选） ==========
# 如果你需要 AI 功能，配置以下变量
AI_DATABASE_URL=mysql+pymysql://user:password@192.168.31.9:3306/ai_companion?charset=utf8mb4

# ========== Moonwell 集成（可选） ==========
MOON_WELL_TRANSLATION_CALLBACK_URL=http://magicbook:8083/internal/reading-translation/task-completed
MAGICBOOK_INTEGRATION_TOKEN=rxMJz16B-WtO0BXOgoOvlTlfn1ti9u-VaYWFoH0UPo7gfqetssQI4Q7quwEavljL
```

## 步骤 5：启动服务

```bash
cd /vol1/docker/magicbook
docker-compose up -d
```

## 步骤 6：访问 Magicbook

1. 打开浏览器，访问 `http://<飞牛OS_IP>:8083`
2. 默认账号：`admin` / `admin123`
3. **请立即修改密码**
4. 访问 `/admin/dbconfig` 配置书库路径
5. 以管理员登录后访问 `/ai/admin` 配置 AI 功能

## 常用命令

```bash
# 启动
docker-compose up -d

# 停止
docker-compose down

# 重启
docker-compose restart

# 查看日志
docker-compose logs -f

# 查看状态
docker-compose ps

# 拉取最新镜像
docker-compose pull
docker-compose up -d
```

## 与 Moonwell 集成（可选）

如果你已经部署了 Moonwell 翻译服务，可以在 `.env` 中配置：

```bash
# Moonwell 服务地址（如果 moonwell 也在飞牛OS上，使用 localhost）
MOON_WELL_TRANSLATION_CALLBACK_URL=http://localhost:8082/internal/reading-translation/task-completed

# 或者使用飞牛OS的IP地址
MOON_WELL_TRANSLATION_CALLBACK_URL=http://192.168.31.9:8082/internal/reading-translation/task-completed
```

### 网络配置

当前配置使用 `network_mode: host`，magicbook 和 moonwell 都使用主机网络栈，可以通过 `localhost` 或主机 IP 地址直接通信。

## 故障排查

### 1. 镜像下载失败

如果镜像下载失败，可能需要配置 Docker 镜像加速：

```bash
# 在飞牛OS Docker 设置中配置镜像源
# 或者手动修改 Docker daemon 配置
```

### 2. 权限问题

确保目录权限正确：

```bash
chmod -R 755 /vol1/docker/magicbook/calibre-library
chmod -R 755 /vol1/docker/magicbook/config
```

### 3. 端口冲突

如果 8083 端口被占用，修改 `docker-compose.yml` 中的端口映射：

```yaml
ports:
  - "18083:8083"  # 使用 18083 端口
```

然后更新 `.env` 文件：

```bash
CALIBRE_PORT=18083
```

### 4. 查看日志

```bash
docker-compose logs calibre-web
```

## 数据备份

定期备份以下目录：

1. `/vol1/docker/magicbook/calibre-library` - 书库数据
2. `/vol1/docker/magicbook/config` - 应用配置（包含 `app.db`）

```bash
# 备份脚本示例
tar -czf magicbook-backup-$(date +%Y%m%d).tar.gz \
  /vol1/docker/magicbook/calibre-library \
  /vol1/docker/magicbook/config
```

## 更新服务

```bash
cd /vol1/docker/magicbook
docker-compose pull
docker-compose up -d
```

## 注意事项

1. **书库路径**：`calibre-library` 目录必须包含 `metadata.db` 文件
2. **配置备份**：`config` 目录包含应用配置和数据库，务必定期备份
3. **网络配置**：如果需要与其他服务（如 Moonwell）通信，确保它们在同一 Docker 网络中
4. **性能考虑**：飞牛OS 的性能取决于硬件配置，建议至少 4GB 内存