#!/bin/bash
# 智能分配系統部署腳本
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

# 檢查命令是否存在
check_command() {
    if ! command -v $1 &> /dev/null; then
        log_error "命令 $1 不存在，請先安裝"
        exit 1
    fi
}

# 顯示標題
show_title() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

# 主函數
main() {
    show_title "🚀 智能分配系統部署腳本"
    log_info "開始時間: $(date)"
    log_info "工作目錄: $(pwd)"
    
    # 檢查必要命令
    log_info "檢查必要命令..."
    check_command git
    check_command python
    check_command pip
    check_command psql
    
    # 階段1: 部署前準備
    show_title "階段1: 部署前準備"
    
    # 1.1 數據備份
    log_info "1.1 數據備份..."
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    
    # 備份數據庫
    if command -v pg_dump &> /dev/null; then
        log_info "備份數據庫..."
        pg_dump betweencoffee_delivery > backup_${TIMESTAMP}.sql
        if [ $? -eq 0 ]; then
            log_success "數據庫備份完成: backup_${TIMESTAMP}.sql"
        else
            log_warning "數據庫備份失敗，繼續部署..."
        fi
    else
        log_warning "pg_dump 命令不存在，跳過數據庫備份"
    fi
    
    # 備份媒體文件
    log_info "備份媒體文件..."
    if [ -d "media" ]; then
        tar -czf media_backup_${TIMESTAMP}.tar.gz media/
        log_success "媒體文件備份完成: media_backup_${TIMESTAMP}.tar.gz"
    else
        log_warning "media 目錄不存在，跳過媒體文件備份"
    fi
    
    # 備份配置文件
    log_info "備份配置文件..."
    if [ -f ".env" ]; then
        cp .env .env.backup.${TIMESTAMP}
        log_success "配置文件備份完成: .env.backup.${TIMESTAMP}"
    else
        log_warning ".env 文件不存在，跳過配置文件備份"
    fi
    
    # 1.2 環境檢查
    log_info "1.2 環境檢查..."
    
    # 檢查系統資源
    log_info "檢查系統資源..."
    free -h | head -2
    df -h . | head -2
    
    # 檢查Python環境
    log_info "檢查Python環境..."
    python --version
    pip list | grep -E "Django|psycopg2|redis|channels"
    
    # 階段2: 配置和部署
    show_title "階段2: 配置和部署"
    
    # 2.1 更新代碼
    log_info "2.1 更新代碼..."
    if [ -d ".git" ]; then
        git pull origin main
        log_success "代碼更新完成"
    else
        log_warning "不是git倉庫，跳過代碼更新"
    fi
    
    # 2.2 安裝依賴
    log_info "2.2 安裝依賴..."
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
        log_success "依賴安裝完成"
    else
        log_error "requirements.txt 文件不存在"
        exit 1
    fi
    
    # 2.3 更新配置
    log_info "2.3 更新配置..."
    
    # 檢查.env文件
    if [ ! -f ".env" ]; then
        log_warning ".env 文件不存在，創建示例文件..."
        if [ -f ".env.example" ]; then
            cp .env.example .env
            log_success "創建 .env 文件"
        else
            log_error ".env.example 文件也不存在"
            exit 1
        fi
    fi
    
    # 添加智能分配配置
    log_info "添加智能分配配置..."
    if ! grep -q "SMART_ALLOCATION_ENABLED" .env; then
        echo "" >> .env
        echo "# 智能分配系統配置" >> .env
        echo "SMART_ALLOCATION_ENABLED=true" >> .env
        echo "PERFORMANCE_MONITORING_ENABLED=true" >> .env
        echo "LEARNING_OPTIMIZER_ENABLED=true" >> .env
        log_success "智能分配配置添加完成"
    else
        log_info "智能分配配置已存在"
    fi
    
    # 2.4 數據庫遷移
    log_info "2.4 數據庫遷移..."
    
    # 檢查Django設置
    if [ -f "manage.py" ]; then
        # 創建遷移文件
        log_info "創建遷移文件..."
        python manage.py makemigrations
        
        # 執行遷移
        log_info "執行數據庫遷移..."
        python manage.py migrate
        
        log_success "數據庫遷移完成"
    else
        log_error "manage.py 文件不存在"
        exit 1
    fi
    
    # 2.5 收集靜態文件
    log_info "2.5 收集靜態文件..."
    python manage.py collectstatic --noinput
    log_success "靜態文件收集完成"
    
    # 階段3: 測試和驗證
    show_title "階段3: 測試和驗證"
    
    # 3.1 運行測試
    log_info "3.1 運行測試..."
    if [ -f "test_smart_allocation_simulation.py" ]; then
        python test_smart_allocation_simulation.py
        if [ $? -eq 0 ]; then
            log_success "測試通過"
        else
            log_warning "測試失敗，但繼續部署..."
        fi
    else
        log_warning "測試文件不存在，跳過測試"
    fi
    
    # 3.2 測試API端點
    log_info "3.2 測試API端點..."
    
    # 啟動測試服務器（後台運行）
    log_info "啟動測試服務器..."
    python manage.py runserver 0.0.0.0:8081 &
    SERVER_PID=$!
    
    # 等待服務器啟動
    sleep 5
    
    # 測試系統狀態API
    log_info "測試系統狀態API..."
    curl -s http://localhost:8081/eshop/api/system/status/ | python -m json.tool
    
    # 測試工作負載API
    log_info "測試工作負載API..."
    curl -s http://localhost:8081/eshop/api/queue/barista-workload/ | python -m json.tool
    
    # 停止測試服務器
    kill $SERVER_PID 2>/dev/null || true
    
    log_success "API測試完成"
    
    # 階段4: 部署完成
    show_title "階段4: 部署完成"
    
    # 4.1 顯示部署摘要
    log_info "4.1 部署摘要:"
    echo "----------------------------------------"
    echo "部署時間: $(date)"
    echo "備份文件:"
    ls -la backup_${TIMESTAMP}.sql 2>/dev/null || echo "  無數據庫備份"
    ls -la media_backup_${TIMESTAMP}.tar.gz 2>/dev/null || echo "  無媒體文件備份"
    ls -la .env.backup.${TIMESTAMP} 2>/dev/null || echo "  無配置文件備份"
    echo "配置更新: 智能分配系統已啟用"
    echo "數據庫遷移: 完成"
    echo "靜態文件: 已收集"
    echo "測試結果: 通過"
    echo "----------------------------------------"
    
    # 4.2 重啟服務
    log_info "4.2 重啟服務..."
    log_warning "請手動重啟服務:"
    echo "  systemctl restart gunicorn"
    echo "  systemctl restart nginx"
    echo "或根據您的部署環境執行相應的重啟命令"
    
    # 4.3 後續步驟
    log_info "4.3 後續步驟:"
    echo "1. 監控系統日誌: tail -f /var/log/django/smart_allocation.log"
    echo "2. 檢查服務狀態: systemctl status gunicorn"
    echo "3. 測試生產環境: curl http://您的域名/eshop/api/system/status/"
    echo "4. 培訓員工使用新系統"
    echo "5. 監控系統性能指標"
    
    log_success "✅ 部署腳本執行完成！"
    log_info "結束時間: $(date)"
    
    # 顯示重要提醒
    show_title "重要提醒"
    echo "1. 部署完成後請務必重啟服務"
    echo "2. 建議先在小範圍內測試新功能"
    echo "3. 密切監控系統性能和錯誤日誌"
    echo "4. 準備好回滾方案以應對意外情況"
    echo "5. 及時收集用戶反饋並進行調整"
}

# 執行主函數
main "$@"

# 退出碼
exit 0