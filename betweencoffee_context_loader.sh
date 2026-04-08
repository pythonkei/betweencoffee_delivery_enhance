#!/bin/bash
# Between Coffee 上下文自動加載器
# 用於在 Cline 啟動時自動加載項目上下文

set -e

# 配置
PROJECT_DIR="/home/kei/Desktop/betweencoffee_delivery_enhance"
CONTEXT_FILE="/tmp/betweencoffee_context_$(date +%Y%m%d_%H%M%S).txt"
LOG_FILE="/tmp/betweencoffee_context_loader.log"

# 顏色輸出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# 檢查項目目錄
check_project_dir() {
    if [ ! -d "$PROJECT_DIR" ]; then
        log_error "項目目錄不存在: $PROJECT_DIR"
        return 1
    fi
    
    if [ ! -f "$PROJECT_DIR/.clinerules" ]; then
        log_warning ".clinerules 文件不存在"
    else
        log_info "找到 .clinerules 文件"
    fi
    
    if [ ! -d "$PROJECT_DIR/betweencoffee_memory_bank" ]; then
        log_warning "Memory Bank 目錄不存在"
    else
        log_info "找到 Memory Bank 目錄"
    fi
    
    return 0
}

# 加載上下文
load_context() {
    log_info "開始加載 Between Coffee 上下文..."
    
    # 切換到項目目錄
    cd "$PROJECT_DIR" || {
        log_error "無法切換到項目目錄"
        return 1
    }
    
    # 檢查 Python 腳本
    if [ ! -f "load_betweencoffee_context.py" ]; then
        log_error "加載腳本不存在: load_betweencoffee_context.py"
        return 1
    fi
    
    # 運行加載腳本
    log_info "運行上下文加載腳本..."
    python load_betweencoffee_context.py --output "$CONTEXT_FILE"
    
    if [ $? -eq 0 ] && [ -f "$CONTEXT_FILE" ]; then
        # 檢查文件大小
        FILE_SIZE=$(wc -c < "$CONTEXT_FILE")
        FILE_SIZE_KB=$((FILE_SIZE / 1024))
        
        # 檢查內容
        LINE_COUNT=$(wc -l < "$CONTEXT_FILE")
        
        log_success "上下文加載成功!"
        log_info "文件: $CONTEXT_FILE"
        log_info "大小: ${FILE_SIZE} 字符 (~${FILE_SIZE_KB} KB)"
        log_info "行數: ${LINE_COUNT} 行"
        
        # 設置環境變量
        export BETWEENCOFFEE_CONTEXT_FILE="$CONTEXT_FILE"
        export BETWEENCOFFEE_CONTEXT_LOADED="true"
        export BETWEENCOFFEE_CONTEXT_TIMESTAMP="$(date +%s)"
        
        log_info "環境變量已設置"
        
        # 顯示預覽
        log_info "上下文預覽 (前5行):"
        head -5 "$CONTEXT_FILE"
        
        return 0
    else
        log_error "上下文加載失敗"
        return 1
    fi
}

# 清理舊的上下文文件
cleanup_old_contexts() {
    log_info "清理舊的上下文文件..."
    
    # 刪除超過1天的文件
    find /tmp -name "betweencoffee_context_*.txt" -mtime +1 -delete 2>/dev/null || true
    
    # 刪除超過100MB的日誌文件
    find /tmp -name "betweencoffee_context_loader.log" -size +100M -delete 2>/dev/null || true
    
    log_info "清理完成"
}

# 驗證加載結果
validate_context() {
    log_info "驗證上下文加載結果..."
    
    if [ -z "$BETWEENCOFFEE_CONTEXT_FILE" ] || [ ! -f "$BETWEENCOFFEE_CONTEXT_FILE" ]; then
        log_error "上下文文件未找到"
        return 1
    fi
    
    # 檢查關鍵內容
    local has_clinerules=$(grep -c "項目規範 (.clinerules)" "$BETWEENCOFFEE_CONTEXT_FILE" || true)
    local has_memory_bank=$(grep -c "Between Coffee 系統 - 上下文摘要" "$BETWEENCOFFEE_CONTEXT_FILE" || true)
    local has_tech_stack=$(grep -c "技術棧" "$BETWEENCOFFEE_CONTEXT_FILE" || true)
    local has_priority=$(grep -c "高優先級任務" "$BETWEENCOFFEE_CONTEXT_FILE" || true)
    
    if [ "$has_clinerules" -gt 0 ]; then
        log_success "✅ 包含 .clinerules 內容"
    else
        log_warning "⚠️  缺少 .clinerules 內容"
    fi
    
    if [ "$has_memory_bank" -gt 0 ]; then
        log_success "✅ 包含 Memory Bank 摘要"
    else
        log_warning "⚠️  缺少 Memory Bank 摘要"
    fi
    
    if [ "$has_tech_stack" -gt 0 ]; then
        log_success "✅ 包含技術棧信息"
    else
        log_warning "⚠️  缺少技術棧信息"
    fi
    
    if [ "$has_priority" -gt 0 ]; then
        log_success "✅ 包含優先任務信息"
    else
        log_warning "⚠️  缺少優先任務信息"
    fi
    
    # 總體驗證
    if [ "$has_clinerules" -gt 0 ] && [ "$has_memory_bank" -gt 0 ]; then
        log_success "✅ 上下文驗證通過"
        return 0
    else
        log_error "❌ 上下文驗證失敗"
        return 1
    fi
}

# 顯示使用說明
show_usage() {
    echo "Between Coffee 上下文自動加載器"
    echo ""
    echo "使用方法:"
    echo "  $0 [選項]"
    echo ""
    echo "選項:"
    echo "  --load      加載上下文（默認）"
    echo "  --validate  驗證當前上下文"
    echo "  --cleanup   清理舊的上下文文件"
    echo "  --test      測試加載和驗證"
    echo "  --help      顯示此幫助信息"
    echo ""
    echo "環境變量:"
    echo "  PROJECT_DIR     項目目錄路徑"
    echo "  CONTEXT_FILE    上下文文件路徑"
    echo ""
    echo "示例:"
    echo "  $0 --load"
    echo "  $0 --test"
    echo "  PROJECT_DIR=/path/to/project $0 --validate"
}

# 主函數
main() {
    local action="load"
    
    # 解析參數
    if [ $# -gt 0 ]; then
        case "$1" in
            --load)
                action="load"
                ;;
            --validate)
                action="validate"
                ;;
            --cleanup)
                action="cleanup"
                ;;
            --test)
                action="test"
                ;;
            --help)
                show_usage
                exit 0
                ;;
            *)
                log_error "未知參數: $1"
                show_usage
                exit 1
                ;;
        esac
    fi
    
    log_info "========================================"
    log_info "Between Coffee 上下文加載器啟動"
    log_info "操作: $action"
    log_info "時間: $(date)"
    log_info "========================================"
    
    case "$action" in
        load)
            check_project_dir && load_context
            ;;
        validate)
            validate_context
            ;;
        cleanup)
            cleanup_old_contexts
            ;;
        test)
            log_info "執行完整測試..."
            check_project_dir && load_context && validate_context
            if [ $? -eq 0 ]; then
                log_success "✅ 所有測試通過!"
            else
                log_error "❌ 測試失敗"
                exit 1
            fi
            ;;
    esac
    
    local exit_code=$?
    
    log_info "========================================"
    log_info "操作完成，退出碼: $exit_code"
    log_info "========================================"
    
    exit $exit_code
}

# 執行主函數
main "$@"