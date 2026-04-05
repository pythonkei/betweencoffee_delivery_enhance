#!/bin/bash
# PostgreSQL 環境變量配置 - 用於 MCP Toolbox for Databases

# 從 Django settings.py 獲取的數據庫配置
export POSTGRES_HOST="localhost"
export POSTGRES_PORT="5432"
export POSTGRES_DB="betweencoffee_delivery_db"
export POSTGRES_USER="postgres"
export POSTGRES_PASSWORD="111111"

# 構建 PostgreSQL 連接字符串
export POSTGRES_URL="postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}"

# MCP Toolbox 環境變量
export TOOLBOX_POSTGRES_URL="${POSTGRES_URL}"
export TOOLBOX_LOG_LEVEL="INFO"

echo "PostgreSQL 環境變量已設置："
echo "POSTGRES_URL: ${POSTGRES_URL}"
echo "POSTGRES_HOST: ${POSTGRES_HOST}"
echo "POSTGRES_DB: ${POSTGRES_DB}"
echo "POSTGRES_USER: ${POSTGRES_USER}"

# 測試連接
echo -e "\n測試 PostgreSQL 連接..."
psql "${POSTGRES_URL}" -c "SELECT version();" 2>/dev/null || echo "警告：無法連接到 PostgreSQL，請確保數據庫正在運行"