#!/bin/bash
# =============================================================
# 初始化 app-log-* 日志索引的 Elasticsearch 模板与保留策略
# 适用：ES >= 7.8（当前环境 8.11.3）
# 覆盖对象：app-log-moon-well、app-log-magicbook（跨项目统一模板）
# 可重复执行（幂等，重跑即更新策略/模板）
#
# 用法：
#   ES_PASSWORD=<ES密码> ./init-app-log-es.sh
# 可选环境变量：
#   ES_URL          默认 https://es.haoshenqi.top:443
#   ES_USERNAME     默认 elastic
#   RETENTION_DAYS  默认 30（app-log-* 索引保留天数，到期自动删除）
# =============================================================
set -euo pipefail

ES_URL="${ES_URL:-https://es.haoshenqi.top:443}"
ES_USERNAME="${ES_USERNAME:-elastic}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
: "${ES_PASSWORD:?请先设置环境变量 ES_PASSWORD=<Elasticsearch 密码>}"

# 1. ILM 保留策略：按索引创建时间到期删除（无 rollover，单索引按年龄删除）
echo "[1/2] 创建 ILM 策略 app-log-policy（app-log-* 保留 ${RETENTION_DAYS} 天）..."
resp=$(curl -sS -u "$ES_USERNAME:$ES_PASSWORD" -H 'Content-Type: application/json' \
  -X PUT "$ES_URL/_ilm/policy/app-log-policy" -d "{
  \"policy\": {
    \"phases\": {
      \"hot\":    { \"min_age\": \"0ms\", \"actions\": {} },
      \"delete\": { \"min_age\": \"${RETENTION_DAYS}d\", \"actions\": { \"delete\": {} } }
    }
  }
}")
echo "  $resp"
echo "$resp" | grep -q '"acknowledged":true' || { echo "ILM 策略创建失败"; exit 1; }

# 2. 索引模板：动态索引 app-log-moon-well / app-log-magicbook 自动套用
echo "[2/2] 创建索引模板 app-log-template（匹配 app-log-*）..."
resp=$(curl -sS -u "$ES_USERNAME:$ES_PASSWORD" -H 'Content-Type: application/json' \
  -X PUT "$ES_URL/_index_template/app-log-template" -d '{
  "index_patterns": ["app-log-*"],
  "template": {
    "settings": {
      "number_of_shards": 1,
      "number_of_replicas": 0,
      "index.lifecycle.name": "app-log-policy"
    },
    "mappings": {
      "properties": {
        "@timestamp": { "type": "date" },
        "message":    { "type": "text" },
        "module":     { "type": "keyword" },
        "log":        { "properties": { "file": { "properties": { "path": { "type": "keyword" } } } } }
      }
    }
  }
}')
echo "  $resp"
echo "$resp" | grep -q '"acknowledged":true' || { echo "索引模板创建失败"; exit 1; }

echo "完成。索引写入后自动套用模板与保留策略。"
echo "验证：curl -u $ES_USERNAME:<密码> $ES_URL/_cat/indices/app-log-*?v"
