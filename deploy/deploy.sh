#!/bin/bash
set -euo pipefail

# Calibre-Web AI 伴读版 部署脚本
# 用法: ./deploy.sh [deploy|up|down|restart|pull|logs|ps]
#
# 前置条件:
#   - .env 文件已配置（从 .env.example 复制）
#   - 宿主机上有 Calibre 书库目录（含 metadata.db）

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log()   { echo -e "${GREEN}[INFO]${NC} $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*" >&2; }

# 检查 .env 文件
check_env() {
    if [ ! -f .env ]; then
        error ".env 文件不存在，请执行: cp .env.example .env"
        error "并修改 CALIBRE_LIBRARY_PATH 指向你的 Calibre 书库目录"
        exit 1
    fi
    # 加载环境变量
    set -a
    source .env
    set +a

    # 校验书库路径
    if [ ! -d "${CALIBRE_LIBRARY_PATH:-./calibre-library}" ]; then
        warn "书库目录 ${CALIBRE_LIBRARY_PATH:-./calibre-library} 不存在，将自动创建（首次启动需在 /admin/dbconfig 配置）"
        mkdir -p "${CALIBRE_LIBRARY_PATH:-./calibre-library}"
    fi

    # 自动创建配置与日志目录
    mkdir -p "${CONFIG_PATH:-./config}" "${LOG_PATH:-./logs}"
}

# 拉取最新镜像
pull_images() {
    log "拉取最新镜像..."
    docker compose pull
    log "镜像拉取完成"
}

# 启动服务
start_services() {
    log "启动服务..."
    docker compose up -d
    log "服务启动完成"
    echo ""
    docker compose ps
}

# 停止服务
stop_services() {
    log "停止服务..."
    docker compose down
    log "服务已停止"
}

# 重启服务
restart_services() {
    log "重启服务..."
    docker compose restart
    log "服务重启完成"
    echo ""
    docker compose ps
}

# 查看日志
show_logs() {
    docker compose logs -f --tail=100
}

# 完整部署 (拉取 + 重启)
deploy() {
    check_env
    pull_images
    stop_services
    start_services
    echo ""
    log "部署完成！"
    log "访问地址: http://localhost:${CALIBRE_PORT:-8083}/"
    log "首次登录: admin / admin123（请立即修改密码）"
    log "AI 配置:  http://localhost:${CALIBRE_PORT:-8083}/ai/admin"
}

# 显示帮助
usage() {
    echo "用法: $0 [命令]"
    echo ""
    echo "命令:"
    echo "  deploy    拉取镜像并重启服务 (默认)"
    echo "  up        启动服务"
    echo "  down      停止服务"
    echo "  restart   重启服务"
    echo "  pull      仅拉取镜像"
    echo "  logs      查看日志"
    echo "  ps        查看服务状态"
    echo ""
    echo "首次部署:"
    echo "  1. cp .env.example .env"
    echo "  2. 修改 .env 中的 CALIBRE_LIBRARY_PATH"
    echo "  3. $0 deploy"
}

# 主逻辑
case "${1:-deploy}" in
    deploy)  deploy ;;
    up)      check_env && start_services ;;
    down)    check_env && stop_services ;;
    restart) check_env && restart_services ;;
    pull)    check_env && pull_images ;;
    logs)    check_env && show_logs ;;
    ps)      check_env && docker compose ps ;;
    *)       usage ;;
esac
