#!/bin/bash
# 測試 MCP PostgreSQL 工具可用性

echo "=== 測試 MCP PostgreSQL 工具 ==="
echo ""

# 設置所有必要的環境變量
export POSTGRES_URL="postgresql://postgres:111111@localhost:5432/betweencoffee_delivery_db"
export POSTGRES_USER="postgres"
export POSTGRES_PASSWORD="111111"
export POSTGRES_HOST="localhost"
export POSTGRES_PORT="5432"
export POSTGRES_DB="betweencoffee_delivery_db"
export POSTGRES_DATABASE="betweencoffee_delivery_db"
export TOOLBOX_LOG_LEVEL="INFO"

echo "1. 測試 MCP 伺服器啟動..."
echo "   運行 10 秒鐘測試..."
timeout 10 npx -y @toolbox-sdk/server --prebuilt=postgres --stdio 2>&1 | tee /tmp/mcp_test.log

echo ""
echo "2. 檢查日誌中的工具列表..."
grep -A 5 "Initialized 29 tools" /tmp/mcp_test.log || echo "未找到工具列表"

echo ""
echo "3. 檢查是否有錯誤..."
grep -i "error\|failed\|unable" /tmp/mcp_test.log | head -5

echo ""
echo "4. 測試數據庫直接連接..."
psql "${POSTGRES_URL}" -c "SELECT '數據庫連接正常' as status, COUNT(*) as table_count FROM information_schema.tables WHERE table_schema = 'public';" 2>/dev/null

echo ""
echo "5. 列出可用的 MCP 工具類別..."
echo "   根據日誌，初始化的工具集包括："
echo "   - replication (複製相關)"
echo "   - data (數據查詢)"
echo "   - monitor (監控)"
echo "   - health (健康檢查)"
echo "   - view-config (視圖配置)"
echo "   - default (默認工具)"

echo ""
echo "=== 測試完成 ==="
echo ""
echo "重要工具包括："
echo "  - execute_sql: 執行 SQL 查詢"
echo "  - list_tables: 列出所有表"
echo "  - list_database_stats: 數據庫統計"
echo "  - list_active_queries: 活動查詢"
echo "  - get_query_plan: 查詢計劃"
echo "  - list_table_stats: 表統計信息"
echo ""
echo "要使用這些工具，請："
echo "  1. 重啟 Claude Desktop 或 IDE"
echo "  2. 在對話中輸入 '請幫我查詢今天的訂單數量'"
echo "  3. AI 助手將使用 execute_sql 工具獲取數據"