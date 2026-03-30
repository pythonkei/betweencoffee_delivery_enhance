#!/bin/bash

# rollback_unified_updater.sh
# ==================== 統一訂單更新器回滾腳本 ====================

set -e

echo "🔄 開始回滾統一訂單更新器"
echo "=========================================="

PROJECT_DIR="/home/kei/Desktop/betweencoffee_delivery_enhance"
BACKUP_DIR="${PROJECT_DIR}/backup/websocket_updates"

# 查找最新的備份文件
LATEST_BACKUP=$(ls -t "${BACKUP_DIR}"/*unified-order-updater.js*.bak 2>/dev/null | head -1)

if [ -z "${LATEST_BACKUP}" ]; then
    echo "❌ 找不到備份文件"
    exit 1
fi

echo "找到備份文件: ${LATEST_BACKUP}"

# 確認回滾
read -p "確定要回滾到備份版本嗎？(y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "取消回滾"
    exit 0
fi

# 執行回滾
echo "執行回滾..."
cp "${LATEST_BACKUP}" "${PROJECT_DIR}/static/js/unified-order-updater.js"

echo "✅ 回滾完成"
echo "請重啟服務以應用更改"
