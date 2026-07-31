#!/bin/bash
# Calibre-Web 容器启动脚本
# 职责：权限检查 → 初始化配置目录 → 启动主进程
set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log()   { echo -e "${GREEN}[entrypoint]${NC} $*"; }
warn()  { echo -e "${YELLOW}[entrypoint]${NC} $*"; }
error() { echo -e "${RED}[entrypoint]${NC} $*" >&2; }

# 当容器以 root 运行时（例如需要挂载宿主机目录修正权限），重新修正数据目录属主
if [ "$(id -u)" = "0" ]; then
    log "以 root 运行，修正数据目录权限..."
    chown -R calibre:calibre /app /calibre-library /config 2>/dev/null || true
    exec gosu calibre python /app/cps.py
fi

# 非 root 模式直接启动
log "启动 Calibre-Web (端口 ${CALIBRE_PORT:-8083})"
log "配置目录: ${CALIBRE_DBPATH:-/config}"
log "书库目录: ${CALIBRE_LIBRARY:-/calibre-library}"

# 若书库目录为空，提示用户挂载
if [ -d "${CALIBRE_LIBRARY:-/calibre-library}" ] && [ -z "$(ls -A "${CALIBRE_LIBRARY:-/calibre-library}" 2>/dev/null)" ]; then
    warn "书库目录为空，请将 Calibre metadata.db 所在目录挂载到 ${CALIBRE_LIBRARY:-/calibre-library}"
    warn "首次启动后，需登录管理员账号在 /admin/dbconfig 页面确认书库路径"
fi

exec python /app/cps.py
