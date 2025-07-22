#!/bin/bash

# 销售趋势API测试脚本
# 使用curl命令测试API接口

API_URL="http://localhost:8000/api/v1/dashboard/trending/sales-trend"
PROJECT_ID="d2c02b80-4c82-44cc-8093-56708a7883f7"
ASIN="B08SJ3Z8XD"

echo "====================================="
echo "销售趋势API测试"
echo "API端点: $API_URL"
echo "====================================="

echo ""
echo "1. 基础请求测试"
curl -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "'$PROJECT_ID'",
    "asin": "'$ASIN'",
    "metric_type": "sales",
    "aggregation": "daily"
  }' | jq .

echo ""
echo "2. 带筛选条件的请求测试"
curl -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "'$PROJECT_ID'",
    "filters": {
      "categories": ["Light Switches"],
      "brands": ["Leviton"],
      "segments": ["Premium"],
      "extend_fields": {
        "is_bestseller": true
      }
    },
    "date_range": {
      "start_date": "2024-07-01",
      "end_date": "2024-12-31"
    },
    "asin": "'$ASIN'",
    "metric_type": "revenue",
    "aggregation": "daily"
  }' | jq .

echo ""
echo "3. 项目汇总请求测试（无指定ASIN）"
curl -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "'$PROJECT_ID'",
    "filters": {
      "categories": ["Light Switches"]
    },
    "date_range": {
      "start_date": "2024-01-01",
      "end_date": "2024-12-31"
    },
    "metric_type": "sales",
    "aggregation": "monthly"
  }' | jq .

echo ""
echo "4. 价格分析请求测试"
curl -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "'$PROJECT_ID'",
    "asin": "'$ASIN'",
    "date_range": {
      "start_date": "2024-07-19",
      "end_date": "2025-07-19"
    },
    "metric_type": "price",
    "aggregation": "daily"
  }' | jq .

echo ""
echo "5. 错误请求测试（缺少project_id）"
curl -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "asin": "'$ASIN'",
    "metric_type": "sales"
  }' | jq .

echo ""
echo "====================================="
echo "测试完成"
echo "=====================================" 