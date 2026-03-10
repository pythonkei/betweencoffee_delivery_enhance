#!/bin/bash
# 智能分配系統部署狀態檢查腳本
# 版本: 1.0.0
# 生成日期: 2026年3月9日

set -e  # 遇到錯誤時退出

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日誌函數
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 顯示標題
show_title() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

# 檢查服務狀態
check_service_status() {
    local service_name=$1
    local display_name=$2
    
    log_info "檢查 $display_name 服務狀態..."
    
    if systemctl is-active --quiet $service_name; then
        log_success "$display_name 服務運行正常"
        return 0
    else
        log_error "$display_name 服務未運行"
        return 1
    fi
}

# 檢查端口監聽
check_port_listening() {
    local port=$1
    local service_name=$2
    
    log_info "檢查 $service_name 端口 $port 監聽..."
    
    if ss -tuln | grep -q ":$port "; then
        log_success "$service_name 端口 $port 監聽正常"
        return 0
    else
        log_error "$service_name 端口 $port 未監聽"
        return 1
    fi
}

# 檢查API端點
check_api_endpoint() {
    local url=$1
    local endpoint_name=$2
    
    log_info "檢查 $endpoint_name API..."
    
    if curl -s -o /dev/null -w "%{http_code}" $url | grep -q "200"; then
        log_success "$endpoint_name API 正常響應"
        return 0
    else
        log_error "$endpoint_name API 響應異常"
        return 1
    fi
}

# 檢查數據庫連接
check_database_connection() {
    log_info "檢查數據庫連接..."
    
    if python -c "
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'betweencoffee_delivery.settings')
django.setup()
from django.db import connection
try:
    connection.ensure_connection()
    print('SUCCESS: 數據庫連接正常')
except Exception as e:
    print(f'ERROR: 數據庫連接失敗: {e}')
" 2>/dev/null | grep -q "SUCCESS"; then
        log_success "數據庫連接正常"
        return 0
    else
        log_error "數據庫連接失敗"
        return 1
    fi
}

# 檢查智能分配系統配置
check_smart_allocation_config() {
    log_info "檢查智能分配系統配置..."
    
    # 檢查環境變量
    if grep -q "SMART_ALLOCATION_ENABLED=true" .env 2>/dev/null; then
        log_success "智能分配系統已啟用"
    else
        log_warning "智能分配系統未啟用"
    fi
    
    # 檢查模塊導入
    if python -c "
try:
    from eshop.smart_allocation import get_smart_allocator
    print('SUCCESS: 智能分配模塊導入正常')
except ImportError as e:
    print(f'ERROR: 智能分配模塊導入失敗: {e}')
" 2>/dev/null | grep -q "SUCCESS"; then
        log_success "智能分配模塊導入正常"
    else
        log_error "智能分配模塊導入失敗"
    fi
}

# 檢查數據庫表結構
check_database_schema() {
    log_info "檢查數據庫表結構..."
    
    if python -c "
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'betweencoffee_delivery.settings')
django.setup()
from django.db import connection

# 檢查Barista表是否有智能分配相關字段
with connection.cursor() as cursor:
    cursor.execute(\"\"\"
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'eshop_barista' 
        AND column_name IN ('efficiency_factor', 'max_concurrent_orders', 'is_active')
    \"\"\")
    columns = [row[0] for row in cursor.fetchall()]
    
    required_columns = ['efficiency_factor', 'max_concurrent_orders', 'is_active']
    missing_columns = [col for col in required_columns if col not in columns]
    
    if missing_columns:
        print(f'WARNING: 缺少字段: {missing_columns}')
    else:
        print('SUCCESS: 所有智能分配字段都存在')
" 2>/dev/null | grep -q "SUCCESS"; then
        log_success "數據庫表結構正常"
        return 0
    else
        log_warning "數據庫表結構不完整"
        return 1
    fi
}

# 檢查系統性能
check_system_performance() {
    log_info "檢查系統性能..."
    
    # 檢查CPU使用率
    cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
    if (( $(echo "$cpu_usage < 80" | bc -l) )); then
        log_success "CPU使用率正常: ${cpu_usage}%"
    else
        log_warning "CPU使用率較高: ${cpu_usage}%"
    fi
    
    # 檢查內存使用率
    mem_usage=$(free | grep Mem | awk '{print $3/$2 * 100.0}')
    if (( $(echo "$mem_usage < 85" | bc -l) )); then
        log_success "內存使用率正常: ${mem_usage}%"
    else
        log_warning "內存使用率較高: ${mem_usage}%"
    fi
    
    # 檢查磁盤使用率
    disk_usage=$(df -h . | tail -1 | awk '{print $5}' | sed 's/%//')
    if (( disk_usage < 90 )); then
        log_success "磁盤使用率正常: ${disk_usage}%"
    else
        log_warning "磁盤使用率較高: ${disk_usage}%"
    fi
}

# 主函數
main() {
    show_title "🔍 智能分配系統部署狀態檢查"
    log_info "開始時間: $(date)"
    log_info "工作目錄: $(pwd)"
    
    # 初始化檢查結果
    local total_checks=0
    local passed_checks=0
    local failed_checks=0
    
    # 1. 檢查系統服務
    show_title "1. 系統服務檢查"
    
    # 檢查PostgreSQL
    if check_service_status "postgresql" "PostgreSQL"; then
        ((passed_checks++))
    else
        ((failed_checks++))
    fi
    ((total_checks++))
    
    # 檢查Redis
    if check_service_status "redis" "Redis"; then
        ((passed_checks++))
    else
        ((failed_checks++))
    fi
    ((total_checks++))
    
    # 檢查Gunicorn
    if check_service_status "gunicorn" "Gunicorn"; then
        ((passed_checks++))
    else
        ((failed_checks++))
    fi
    ((total_checks++))
    
    # 檢查Nginx
    if check_service_status "nginx" "Nginx"; then
        ((passed_checks++))
    else
        ((failed_checks++))
    fi
    ((total_checks++))
    
    # 2. 檢查網絡端口
    show_title "2. 網絡端口檢查"
    
    # 檢查PostgreSQL端口
    if check_port_listening "5432" "PostgreSQL"; then
        ((passed_checks++))
    else
        ((failed_checks++))
    fi
    ((total_checks++))
    
    # 檢查Redis端口
    if check_port_listening "6379" "Redis"; then
        ((passed_checks++))
    else
        ((failed_checks++))
    fi
    ((total_checks++))
    
    # 檢查HTTP端口
    if check_port_listening "80" "HTTP"; then
        ((passed_checks++))
    else
        ((failed_checks++))
    fi
    ((total_checks++))
    
    # 3. 檢查數據庫
    show_title "3. 數據庫檢查"
    
    # 檢查數據庫連接
    if check_database_connection; then
        ((passed_checks++))
    else
        ((failed_checks++))
    fi
    ((total_checks++))
    
    # 檢查數據庫表結構
    if check_database_schema; then
        ((passed_checks++))
    else
        ((failed_checks++))
    fi
    ((total_checks++))
    
    # 4. 檢查應用功能
    show_title "4. 應用功能檢查"
    
    # 檢查系統狀態API
    if check_api_endpoint "http://localhost:8081/eshop/api/system/status/" "系統狀態"; then
        ((passed_checks++))
    else
        ((failed_checks++))
    fi
    ((total_checks++))
    
    # 檢查工作負載API
    if check_api_endpoint "http://localhost:8081/eshop/api/queue/barista-workload/" "工作負載"; then
        ((passed_checks++))
    else
        ((failed_checks++))
    fi
    ((total_checks++))
    
    # 檢查智能分配配置
    if check_smart_allocation_config; then
        ((passed_checks++))
    else
        ((failed_checks++))
    fi
    ((total_checks++))
    
    # 5. 檢查系統性能
    show_title "5. 系統性能檢查"
    check_system_performance
    
    # 6. 顯示檢查結果
    show_title "6. 檢查結果總結"
    
    echo "檢查項目總數: $total_checks"
    echo "通過檢查數: $passed_checks"
    echo "失敗檢查數: $failed_checks"
    echo ""
    
    # 計算通過率
    if (( total_checks > 0 )); then
        pass_rate=$(( passed_checks * 100 / total_checks ))
        echo "檢查通過率: ${pass_rate}%"
    fi
    
    # 顯示總體狀態
    if (( failed_checks == 0 )); then
        log_success "✅ 所有檢查通過！系統狀態正常"
        echo ""
        echo "建議下一步:"
        echo "1. 運行測試: python test_smart_allocation_simulation.py"
        echo "2. 測試員工界面: 訪問員工管理頁面"
        echo "3. 監控系統日誌: tail -f /var/log/django/smart_allocation.log"
        echo "4. 進行用戶培訓"
    elif (( failed_checks <= 2 )); then
        log_warning "⚠️ 有少量檢查失敗，但不影響核心功能"
        echo ""
        echo "建議下一步:"
        echo "1. 修復失敗的檢查項目"
        echo "2. 運行測試確認核心功能"
        echo "3. 監控系統運行狀態"
    else
        log_error "❌ 有多個檢查失敗，需要修復"
        echo ""
        echo "緊急行動:"
        echo "1. 立即修復失敗的檢查項目"
        echo "2. 檢查系統日誌查找問題"
        echo "3. 考慮回滾到穩定版本"
    fi
    
    # 顯示詳細建議
    show_title "詳細建議"
    
    echo "1. 部署後監控:"
    echo "   - 監控系統日誌: tail -f /var/log/django/smart_allocation.log"
    echo "   - 監控錯誤率: 檢查應用錯誤日誌"
    echo "   - 監控性能指標: CPU、內存、響應時間"
    echo ""
    echo "2. 用戶培訓:"
    echo "   - 培訓員工使用新系統"
    echo "   - 提供使用手冊和故障排除指南"
    echo "   - 建立支持渠道"
    echo ""
    echo "3. 持續優化:"
    echo "   - 收集用戶反饋"
    echo "   - 監控系統性能"
    echo "   - 定期更新和優化"
    
    log_info "檢查完成時間: $(date)"
    
    # 返回退出碼
    if (( failed_checks == 0 )); then
        exit 0
    else
        exit 1
    fi
}

# 執行主函數
main "$@"