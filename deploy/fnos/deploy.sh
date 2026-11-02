#!/bin/bash
# magicbook FNOS 部署脚本：登录 ACR -> 拉取最新镜像 -> 判等 -> 启动/更新
#
# 这份是 fnOS 项目目录（/app/magicbook/deploy.sh）实际执行的那份：app-manager agent 的
# updateProjectCompose 发现项目目录里有 deploy.sh 就交给它全权部署。
# 仓库根的 deploy/deploy.sh 是开发者本地用的多功能脚本（deploy/up/down/restart/logs），两者不通用。
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
docker compose pull magicbook   # 只拉应用镜像；filebeat 镜像已 pin(8.11.3)且在本地，elastic.co 直连常被墙勿整体 pull

# 部署前判等（R155）：镜像内容没真的变就不重启。
# Why: 镜像 ID / manifest digest 含构建时间戳，同源码重构建必变，比 ID 永远判「变了」；
#      构建时打进镜像的 house.code-digest 才回答得了「代码到底变没变」。
# 保守侧：任一侧取不到指纹 / 值为 unknown / 容器不存在，都按「变了」走完整部署。
NEW_DIGEST="$(docker image inspect registry.cn-hangzhou.aliyuncs.com/magichouse/magicbook:latest \
  --format '{{index .Config.Labels "house.code-digest"}}' 2>/dev/null || true)"
RUNNING_DIGEST="$(docker inspect magicbook \
  --format '{{index .Config.Labels "house.code-digest"}}' 2>/dev/null || true)"
echo "  代码指纹: running=${RUNNING_DIGEST:-<none>} 新镜像=${NEW_DIGEST:-<none>}"
if [ -n "$NEW_DIGEST" ] && [ "$NEW_DIGEST" != "unknown" ] \
   && [ -n "$RUNNING_DIGEST" ] && [ "$RUNNING_DIGEST" != "unknown" ] \
   && [ "$NEW_DIGEST" = "$RUNNING_DIGEST" ]; then
  echo "  镜像代码指纹未变 -> 跳过重启（未停容器、未 up -d）"
  docker compose ps
  echo "完成（跳过重启，镜像内容与线上一致）。"
  exit 0
fi

echo "[2/3] 启动/更新容器..."
docker compose up -d

echo "[3/3] 验证状态..."
docker compose ps

echo "完成。查看日志: docker compose logs -f magicbook"
