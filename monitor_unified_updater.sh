#!/bin/bash

# monitor_unified_updater.sh
# ==================== 統一訂單更新器監控腳本 ====================

PROJECT_DIR="/home/kei/Desktop/betweencoffee_delivery_enhance"
LOG_DIR="${PROJECT_DIR}/logs"
MONITOR_LOG="${LOG_DIR}/unified_updater_monitor_$(date +%Y%m%d).log"

# 創建日誌目錄
mkdir -p "${LOG_DIR}"

monitor() {
    echo "📊 統一訂單更新器監控"
    echo "=========================================="
    echo "監控開始時間: $(date)"
    echo ""
    
    # 檢查文件存在性
    echo "1. 文件檢查:"
    if [ -f "${PROJECT_DIR}/static/js/unified-order-updater.js" ]; then
        echo "   ✅ unified-order-updater.js 存在"
        FILE_SIZE=$(stat -c%s "${PROJECT_DIR}/static/js/unified-order-updater.js")
        echo "       文件大小: ${FILE_SIZE} 字節"
    else
        echo "   ❌ unified-order-updater.js 不存在"
    fi
    
    if [ -f "${PROJECT_DIR}/static/js/unified-order-updater-enhanced.js" ]; then
        echo "   ✅ unified-order-updater-enhanced.js 存在"
    else
        echo "   ❌ unified-order-updater-enhanced.js 不存在"
    fi
    
    echo ""
    
    # 檢查版本信息
    echo "2. 版本信息:"
    if grep -q "增強版" "${PROJECT_DIR}/static/js/unified-order-updater.js"; then
        echo "   ✅ 當前運行的是增強版"
    else
        echo "   ℹ️  當前運行的是舊版"
    fi
    
    echo ""
    
    # 檢查錯誤日誌
    echo "3. 錯誤檢查:"
    ERROR_COUNT=$(find "${LOG_DIR}" -name "*.log" -type f -exec grep -l "ERROR\|失敗" {} \; | wc -l)
    if [ "${ERROR_COUNT}" -gt 0 ]; then
        echo "   ⚠️  發現 ${ERROR_COUNT} 個包含錯誤的日誌文件"
    else
        echo "   ✅ 未發現錯誤日誌"
    fi
    
    echo ""
    
    # 檢查備份
    echo "4. 備份檢查:"
    BACKUP_COUNT=$(find "${PROJECT_DIR}/backup/websocket_updates" -name "*.bak" -type f 2>/dev/null | wc -l)
    if [ "${BACKUP_COUNT}" -gt 0 ]; then
        echo "   ✅ 有 ${BACKUP_COUNT} 個備份文件"
        LATEST_BACKUP=$(find "${PROJECT_DIR}/backup/websocket_updates" -name "*.bak" -type f -printf "%T@ %p\n" | sort -n | tail -1 | cut -d' ' -f2-)
        echo "       最新備份: $(basename "${LATEST_BACKUP}")"
    else
        echo "   ⚠️  沒有備份文件"
    fi
    
    echo ""
    echo "監控結束時間: $(date)"
    echo "=========================================="
}

# 執行監控並記錄日誌
monitor 2>&1 | tee -a "${MONITOR_LOG}"

echo ""
echo "📄 監控日誌已保存: ${MONITOR_LOG}"
