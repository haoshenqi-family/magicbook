#!/bin/bash
# magicbook-dev FNOS 部署脚本（R288 dev 测试环境，2026-11-07）。
#
# app-manager agent 的 updateProjectCompose 发现项目目录（/app/magicbook-dev/）里有
# deploy.sh 就交给它全权部署。与生产 /app/magicbook/deploy.sh 同构，差异：
# 镜像 :dev 分 tag、服务键 magicbook-dev、无 filebeat（dev 不接 ES）。
set -e
cd "$(dirname "$0")"

# 读取 .env 中的 ACR 凭据
set -a
source .env
set +a

# fnOS 的 Docker 管理面板会重写 ~/.docker/config.json 清掉登录态，
# 把 docker 配置目录指到独立位置，登录凭据不再被覆盖
export DOCKER_CONFIG="${ACR_DOCKER_CONFIG:-/etc/docker-acr}"
mkdir -p "$DOCKER_CONFIG"

if [ -n "$ACR_USERNAME" ] && [ -n "$ACR_PASSWORD" ]; then
  echo "[0/3] 登录 ACR..."
  docker login registry.cn-hangzhou.aliyuncs.com --username "$ACR_USERNAME" --password "$ACR_PASSWORD" >/dev/null 2>&1 \
    || { echo "ACR 登录失败，请检查 .env 中的 ACR_USERNAME / ACR_PASSWORD"; exit 1; }
else
  echo "警告: .env 缺少 ACR_USERNAME / ACR_PASSWORD，跳过自动登录"
fi

echo "[1/3] 拉取最新镜像..."
docker compose pull magicbook-dev

# 部署前判等（R155）：house.code-digest 相同即跳过重启
NEW_DIGEST="$(docker image inspect registry.cn-hangzhou.aliyuncs.com/magichouse/magicbook:dev \
  --format '{{index .Config.Labels "house.code-digest"}}' 2>/dev/null || true)"
RUNNING_DIGEST="$(docker inspect magicbook-dev \
  --format '{{index .Config.Labels "house.code-digest"}}' 2>/dev/null || true)"
echo "  代码指纹: running=${RUNNING_DIGEST:-<none>} 新镜像=${NEW_DIGEST:-<none>}"
if [ -n "$NEW_DIGEST" ] && [ "$NEW_DIGEST" != "unknown" ] \
   && [ -n "$RUNNING_DIGEST" ] && [ "$RUNNING_DIGEST" != "unknown" ] \
   && [ "$NEW_DIGEST" = "$RUNNING_DIGEST" ]; then
  echo "  镜像代码指纹未变 -> 跳过重启（未停容器、未 up -d）"
  docker compose ps
  echo "完成（跳过重启，镜像内容与 dev 线上一致）。"
  exit 0
fi

echo "[2/3] 启动/更新容器..."
docker compose up -d

echo "[3/3] 验证状态..."
docker compose ps

echo "完成。dev-magicbook.haoshenqi.top -> 宿主 8085。查看日志: docker compose logs -f magicbook-dev"
