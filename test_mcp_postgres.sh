#!/bin/bash
# 測試 MCP PostgreSQL 伺服器

echo "=== 測試 MCP PostgreSQL 伺服器 ==="
echo ""

# 設置環境變量
export POSTGRES_URL="postgresql://postgres:111111@localhost:5432/betweencoffee_delivery_db"
export TOOLBOX_LOG_LEVEL="INFO"

echo "1. 測試 npx 安裝 @toolbox-sdk/server..."
npx -y @toolbox-sdk/server --version 2>&1 | head -5

echo ""
echo "2. 測試 PostgreSQL 連接..."
psql "${POSTGRES_URL}" -c "SELECT version();" 2>/dev/null | head -3

echo ""
echo "3. 測試 MCP 伺服器啟動..."
echo "   注意：這將在後台運行 MCP 伺服器 5 秒鐘"
timeout 5 npx -y @toolbox-sdk/server --prebuilt=postgres --stdio 2>&1 | head -20

echo ""
echo "4. 測試數據庫查詢..."
echo "   查詢訂單數量："
psql "${POSTGRES_URL}" -c "SELECT COUNT(*) as total_orders FROM eshop_ordermodel;" 2>/dev/null

echo ""
echo "5. 測試數據庫表結構..."
echo "   列出所有表："
psql "${POSTGRES_URL}" -c "\dt" 2>/dev/null | head -10

echo ""
echo "=== 測試完成 ==="
echo ""
echo "MCP PostgreSQL 伺服器配置："
echo "  - 包名稱: @toolbox-sdk/server"
echo "  - 預建配置: postgres"
echo "  - 連接字符串: ${POSTGRES_URL}"
echo "  - 傳輸方式: STDIO"
echo ""
echo "要使用此 MCP 伺服器，請確保："
echo "  1. PostgreSQL 數據庫正在運行"
echo "  2. 環境變量已正確設置"
echo "  3. Claude Desktop 或 IDE 已重新加載配置"