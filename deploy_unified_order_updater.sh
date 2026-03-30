#!/bin/bash

# deploy_unified_order_updater.sh
# ==================== 統一訂單更新器增強版部署腳本 ====================
# 功能：部署增強版更新器並驗證兼容性

set -e  # 遇到錯誤時停止執行

echo "🚀 開始部署統一訂單更新器增強版"
echo "=========================================="

# ========== 配置變量 ==========

PROJECT_DIR="/home/kei/Desktop/betweencoffee_delivery_enhance"
BACKUP_DIR="${PROJECT_DIR}/backup/websocket_updates"
DEPLOY_DATE=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="${PROJECT_DIR}/logs/deploy_unified_updater_${DEPLOY_DATE}.log"

# 創建必要的目錄
mkdir -p "${BACKUP_DIR}"
mkdir -p "${PROJECT_DIR}/logs"

# ========== 日誌函數 ==========

log() {
    local message="$1"
    local level="${2:-INFO}"
    local timestamp=$(date +"%Y-%m-%d %H:%M:%S")
    echo "[${timestamp}] [${level}] ${message}" | tee -a "${LOG_FILE}"
}

log_success() {
    log "$1" "SUCCESS"
}

log_warning() {
    log "$1" "WARNING"
}

log_error() {
    log "$1" "ERROR"
}

# ========== 備份函數 ==========

backup_file() {
    local file_path="$1"
    local backup_path="${BACKUP_DIR}/$(basename ${file_path})_${DEPLOY_DATE}.bak"
    
    if [ -f "${file_path}" ]; then
        log "備份文件: ${file_path} -> ${backup_path}"
        cp "${file_path}" "${backup_path}"
        return 0
    else
        log_warning "文件不存在，跳過備份: ${file_path}"
        return 1
    fi
}

# ========== 部署步驟 ==========

step1_backup() {
    log "步驟1: 備份現有文件"
    echo "------------------------------------------"
    
    # 備份現有文件
    backup_file "${PROJECT_DIR}/static/js/unified-order-updater.js"
    backup_file "${PROJECT_DIR}/static/js/unified-order-updater-enhanced.js"
    
    log_success "備份完成"
}

step2_deploy_enhanced_version() {
    log "步驟2: 部署增強版更新器"
    echo "------------------------------------------"
    
    # 檢查增強版文件是否存在
    if [ ! -f "${PROJECT_DIR}/static/js/unified-order-updater-enhanced.js" ]; then
        log_error "增強版文件不存在: ${PROJECT_DIR}/static/js/unified-order-updater-enhanced.js"
        return 1
    fi
    
    # 複製增強版到主文件（保持兼容性）
    log "複製增強版到主文件位置"
    cp "${PROJECT_DIR}/static/js/unified-order-updater-enhanced.js" \
       "${PROJECT_DIR}/static/js/unified-order-updater.js"
    
    # 創建符號鏈接（可選）
    log "創建符號鏈接"
    ln -sf "unified-order-updater-enhanced.js" \
           "${PROJECT_DIR}/static/js/unified-order-updater-enhanced.link.js"
    
    log_success "增強版部署完成"
}

step3_update_templates() {
    log "步驟3: 更新模板文件"
    echo "------------------------------------------"
    
    # 查找所有使用統一訂單更新器的模板文件
    TEMPLATE_FILES=$(grep -r "unified-order-updater" "${PROJECT_DIR}/templates" \
                     "${PROJECT_DIR}/eshop/templates" 2>/dev/null | \
                     grep -v ".pyc" | cut -d: -f1 | sort -u)
    
    if [ -z "${TEMPLATE_FILES}" ]; then
        log_warning "未找到使用統一訂單更新器的模板文件"
        return 0
    fi
    
    log "找到 ${#TEMPLATE_FILES[@]} 個模板文件需要檢查"
    
    for template in ${TEMPLATE_FILES}; do
        log "檢查模板: ${template}"
        
        # 檢查是否需要更新
        if grep -q "unified-order-updater.js" "${template}"; then
            log "模板 ${template} 已引用統一訂單更新器"
        fi
    done
    
    log_success "模板檢查完成"
}

step4_run_tests() {
    log "步驟4: 運行測試"
    echo "------------------------------------------"
    
    # 檢查測試文件是否存在
    if [ ! -f "${PROJECT_DIR}/test_unified_order_updater_enhanced.js" ]; then
        log_error "測試文件不存在"
        return 1
    fi
    
    log "運行增強版更新器測試"
    
    # 運行測試
    cd "${PROJECT_DIR}"
    if node test_unified_order_updater_enhanced.js 2>&1 | tee -a "${LOG_FILE}"; then
        log_success "測試通過"
        return 0
    else
        log_error "測試失敗"
        return 1
    fi
}

step5_verify_compatibility() {
    log "步驟5: 驗證兼容性"
    echo "------------------------------------------"
    
    log "檢查API兼容性"
    
    # 檢查舊版API是否存在
    if grep -q "window.UnifiedOrderUpdater" \
       "${PROJECT_DIR}/static/js/unified-order-updater-enhanced.js"; then
        log_success "舊版API兼容性已實現"
    else
        log_error "舊版API兼容性缺失"
        return 1
    fi
    
    # 檢查初始化函數
    if grep -q "initUnifiedOrderUpdater" \
       "${PROJECT_DIR}/static/js/unified-order-updater-enhanced.js"; then
        log_success "初始化函數兼容性已實現"
    else
        log_error "初始化函數兼容性缺失"
        return 1
    fi
    
    log_success "兼容性驗證通過"
}

step6_create_rollback_script() {
    log "步驟6: 創建回滾腳本"
    echo "------------------------------------------"
    
    ROLLBACK_SCRIPT="${PROJECT_DIR}/rollback_unified_updater.sh"
    
    cat > "${ROLLBACK_SCRIPT}" << 'EOF'
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
EOF
    
    chmod +x "${ROLLBACK_SCRIPT}"
    log_success "回滾腳本已創建: ${ROLLBACK_SCRIPT}"
}

step7_create_monitoring_script() {
    log "步驟7: 創建監控腳本"
    echo "------------------------------------------"
    
    MONITOR_SCRIPT="${PROJECT_DIR}/monitor_unified_updater.sh"
    
    cat > "${MONITOR_SCRIPT}" << 'EOF'
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
EOF
    
    chmod +x "${MONITOR_SCRIPT}"
    log_success "監控腳本已創建: ${MONITOR_SCRIPT}"
}

step8_summary() {
    log "步驟8: 部署總結"
    echo "=========================================="
    
    log_success "🎉 統一訂單更新器增強版部署完成！"
    echo ""
    echo "📋 部署摘要:"
    echo "   1. 備份文件已保存到: ${BACKUP_DIR}"
    echo "   2. 增強版已部署到: static/js/unified-order-updater.js"
    echo "   3. 測試報告: test_unified_order_updater_report.json"
    echo "   4. 部署日誌: ${LOG_FILE}"
    echo "   5. 回滾腳本: rollback_unified_updater.sh"
    echo "   6. 監控腳本: monitor_unified_updater.sh"
    echo ""
    echo "🚀 下一步操作:"
    echo "   1. 重啟Django服務以應用更改"
    echo "   2. 運行監控腳本檢查狀態: ./monitor_unified_updater.sh"
    echo "   3. 測試實際訂單更新功能"
    echo ""
    echo "⚠️  注意事項:"
    echo "   - 增強版完全兼容舊版API"
    echo "   - 如果遇到問題，使用回滾腳本: ./rollback_unified_updater.sh"
    echo "   - 定期檢查監控日誌"
}

# ========== 主執行流程 ==========

main() {
    echo ""
    echo "🔧 統一訂單更新器增強版部署流程"
    echo "=========================================="
    echo "項目目錄: ${PROJECT_DIR}"
    echo "部署時間: ${DEPLOY_DATE}"
    echo "日誌文件: ${LOG_FILE}"
    echo ""
    
    # 確認部署
    read -p "確定要部署統一訂單更新器增強版嗎？(y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "取消部署"
        exit 0
    fi
    
    # 執行部署步驟
    local steps=(
        step1_backup
        step2_deploy_enhanced_version
        step3_update_templates
        step4_run_tests
        step5_verify_compatibility
        step6_create_rollback_script
        step7_create_monitoring_script
        step8_summary
    )
    
    local success=true
    
    for step in "${steps[@]}"; do
        if ! $step; then
            log_error "步驟失敗: ${step}"
            success=false
            break
        fi
    done
    
    if $success; then
        log_success "🎉 所有部署步驟完成！"
        echo ""
        echo "✅ 部署成功！"
        echo "請按照總結中的步驟進行後續操作。"
    else
        log_error "❌ 部署失敗！"
        echo ""
        echo "⚠️  部署過程中出現錯誤，請檢查日誌: ${LOG_FILE}"
        echo "如果需要回滾，請手動恢復備份文件。"
        exit 1
    fi
}

# ========== 執行主函數 ==========

main "$@"