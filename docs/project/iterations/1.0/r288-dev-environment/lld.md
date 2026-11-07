# LLD — magicbook dev 测试环境（R288）

> 状态：**已上线待验收**（2026-11-07 dev 链 END OK + 容器 healthy :8085；浏览器端 OIDC 登录验收后回填 Completed）
> 关联：ops R177（主号设计文档 `ops/docs/dev-environment-2026-11.md`）、moon-well R246（同源双环境改造）

## 1. 需求

push `develop` 部署到 dev 测试环境（不再直发生产），push `release` 才部署生产；`master` 冻结；dev 与生产共用书库等数据（用户拍板），域名 `dev-magicbook.haoshenqi.top`。

## 2. 部署形态

| 项 | 值 |
| --- | --- |
| 容器 | `magicbook-dev`（host 网络）:8085，无 filebeat（dev 日志不接 ES，用户拍板） |
| 镜像 | `magichouse/magicbook:dev`（生产仍 `:latest`） |
| 部署 | fnOS `/app/magicbook-dev/`，agent 全权执行该目录 `deploy.sh`（ACR 独立 DOCKER_CONFIG / code-digest 判等同生产） |
| 仓库源 | `deploy/dev/{compose.yaml,deploy.sh,.env.example,README.md}` |

## 3. 数据边界（本仓代码零改动）

1. **独立 `CONFIG_PATH=/app/magicbook-dev/config`**：app.db 复制自生产（用户拍板）。硬前提三条——`config_port` 存 DB 会覆盖 `CALIBRE_PORT`（不独立则端口改不动）；SECRET_KEY/Fernet `.key`、调度开关（`schedule_*` 存 DB）随库走；整本翻译任务台账独立、`_live_workers` 进程内判据 → 两实例不双跑。
2. **初始化 SQL**：`config_port=8085` + 关 `schedule_metadata_backup`/`schedule_reconnect`/`schedule_generate_book_covers`/`schedule_generate_series_covers`（夜间任务会写共享 metadata.db 与 thumbnail 表）。
3. **书库共享只读姿态**：`CALIBRE_LIBRARY_PATH=/app/magicbook/calibre-library`；纪律上禁元数据编辑/投稿入库/calibredb 写。
4. **moon-well 指向 dev**：`MOON_WELL_READING_URL=http://fnos:8084`（R246 dev 实例），形成完整 dev 链路。
5. **OIDC**：issuer/client 与生产同值（同一 Authentik provider），redirect 指 dev 域（Authentik 白名单加条目）；账号互通（绑定关系随 app.db 复制）。
6. `AI_DATABASE_URL` 留空 → 本地 SQLite 隔离。

## 4. 不改代码的依据

前端零域名依赖（模板 `url_for` 相对路径 + 服务端 env 注入 moon-well base）；dev 独立子域 → cookie 天然隔离（无需 `COOKIE_PREFIX`）； APScheduler 是内存 jobstore 每重启重建、调度窗口配置在独立 app.db → 无跨实例双跑。

## 5. 验收（AC）

1. dev 容器 healthy、`https://dev-magicbook.haoshenqi.top` 首页 200（端口 8085 生效）。
2. dev 登录（OIDC）→ 阅读页划词翻译/TTS，流量落在 moon-well-dev。
3. push `develop` 代码提交 → `logs/magicbook-dev.log` `build END OK` + dev 容器更新 + Bark；纯文档 push 两环境均 SKIPPED。
4. push `release` → 生产链正常；生产域名无回归。
