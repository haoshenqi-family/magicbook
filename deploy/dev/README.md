# magicbook dev 测试环境部署指南（R288，2026-11-07）

> push `develop` → fnOS `build-magicbook-dev.sh` → 镜像 `magichouse/magicbook:dev` →
> project-update `magicbook-dev` → agent 执行 `/app/magicbook-dev/deploy.sh`。
> 生产链路（push `release`，`master` 已冻结）见 `deploy/fnos/` 与 `../ops/runbook.md` §1。

## 1. 形态

| 项 | 值 |
| --- | --- |
| 容器 | `magicbook-dev`（host 网络）:**8085**，无 filebeat sidecar |
| 域名 | `dev-magicbook.haoshenqi.top` → fnOS:8085（app-manager 控制面 app 级路由，scheme=http） |
| 镜像 | `magichouse/magicbook:dev`（与生产 `:latest` 分 tag） |
| 目录 | fnOS `/app/magicbook-dev/`（docker-compose.yml + .env + deploy.sh + config/ + logs/） |
| 数据 | **app.db 复制自生产**（独立 CONFIG_PATH）；书库**共享**生产 `/app/magicbook/library/`（⚠️ 真值以生产 .env 为准；ops 文档旧口径 `calibre-library` 是空壳目录，2026-11-07 验收期实测修正） |
| 集成 | `MOON_WELL_READING_URL=http://fnos:8084`（指 dev moon-well）；OIDC issuer/client 与生产同值，账号互通 |

## 2. 为什么必须独立 CONFIG_PATH（硬前提）

- 端口：`settings.config_port`（存 DB）覆盖 `CALIBRE_PORT` 环境变量（`cps/config_sql.py`）——共用 config 目录时端口改不动，dev 会与生产抢 8083。
- 会话密钥 / 调度配置（`schedule_start_time`、四个任务开关存 DB）与生产分离。
- 整本翻译/朗读任务台账（`reading_translation_job*`）独立——dev 与生产互不双跑（`_live_workers` 是进程内判据）。

## 3. 数据边界与纪律

- **书库共享，dev 只读姿态**：禁止元数据编辑、投稿入库、calibredb 写操作；夜间会写 metadata.db 的定时任务已在初始化时关闭（见 §4）。
- AI 会话库 `AI_DATABASE_URL` 留空 → 本地 SQLite 隔离。
- 日志不接 ES（无 filebeat，用户拍板），排障看 `docker logs magicbook-dev`。
- OIDC 账号互通：dev 登录即用生产账号（issuer+subject 绑定关系随 app.db 复制而来）；dev 新建用户只落 dev app.db。

## 4. 首次部署步骤（fnOS）

```bash
mkdir -p /app/magicbook-dev/{config,logs}
cp magicbook/deploy/dev/compose.yaml /app/magicbook-dev/docker-compose.yml
cp magicbook/deploy/dev/deploy.sh    /app/magicbook-dev/deploy.sh && chmod +x /app/magicbook-dev/deploy.sh
cp /app/magicbook/.env /app/magicbook-dev/.env   # 再按 deploy/dev/.env.example 改差异项

# app.db 用 sqlite 在线备份方式复制（生产在跑，不能裸 cp）：
docker exec magicbook python -c "import sqlite3;sqlite3.connect('/config/app.db').backup(sqlite3.connect('/config/dev-app.db'))"
docker cp magicbook:/config/dev-app.db /app/magicbook-dev/config/app.db && docker exec magicbook rm /config/dev-app.db
cp /app/magicbook/config/.key /app/magicbook-dev/config/.key 2>/dev/null || true   # Fernet key（存在才拷）
cp /app/magicbook/config/gdrive.db /app/magicbook-dev/config/ 2>/dev/null || true  # gdrive 凭据（存在才拷）

# 初始化 dev app.db：端口 + 关闭写共享书库的定时任务（列名以 cps/config_sql.py 为准）
sqlite3 /app/magicbook-dev/config/app.db "UPDATE settings SET config_port=8085;
UPDATE settings SET schedule_metadata_backup=0, schedule_reconnect=0,
       schedule_generate_book_covers=0, schedule_generate_series_covers=0;"

cd /app/magicbook-dev && ./deploy.sh
# 控制面确认 agent 已导入 magicbook-dev 项目 → app 级 PATCH 路由（dev-magicbook.haoshenqi.top，scheme=http，targetPort=8085）
```

## 5. 排障

- 日志：`docker logs magicbook-dev`；构建：fnOS `/app/codelib/logs/magicbook-dev.log`。
- 手动补跑：`/app/codelib/webhook-builder/build-magicbook-dev.sh refs/heads/develop <sha>`。
- 端口不对（访问 8085 打到生产内容/404）：查 `sqlite3 /app/magicbook-dev/config/app.db "select config_port from settings"`——config_port 覆盖 env。
