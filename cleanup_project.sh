#!/bin/bash
# 項目清理腳本
# 安全清理臨時測試檔案和報告檔案

set -e  # 遇到錯誤時停止

echo "=========================================="
echo "      Between Coffee 項目清理工具"
echo "=========================================="
echo ""

# 創建備份目錄
BACKUP_DIR="backup_cleanup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
echo "✅ 創建備份目錄: $BACKUP_DIR"
echo ""

# 記錄開始時間
START_TIME=$(date +%s)

# 定義清理函數
cleanup_files() {
    local pattern=$1
    local description=$2
    local exclude_paths=$3
    
    echo "🔍 尋找 $description..."
    
    # 構建 find 命令
    local find_cmd="find . -name \"$pattern\" -type f"
    
    # 添加排除路徑
    if [ -n "$exclude_paths" ]; then
        find_cmd="$find_cmd $exclude_paths"
    fi
    
    # 執行查找並處理
    local file_count=0
    eval "$find_cmd" | while read file; do
        # 跳過備份目錄本身
        if [[ "$file" == ./$BACKUP_DIR/* ]] || [[ "$file" == ./$BACKUP_DIR ]]; then
            continue
        fi
        
        echo "   📦 移動: $file"
        mv "$file" "$BACKUP_DIR/" 2>/dev/null || echo "   ⚠️  無法移動: $file"
        ((file_count++))
    done
    
    if [ $file_count -gt 0 ]; then
        echo "   ✅ 移動了 $file_count 個檔案"
    else
        echo "   ℹ️  沒有找到匹配的檔案"
    fi
    echo ""
}

# 記錄清理前的狀態
echo "📊 清理前檔案統計:"
echo "   測試 Python: $(find . -name 'test_*.py' -type f ! -path "./$BACKUP_DIR/*" | wc -l)"
echo "   測試 JS: $(find . -name 'test_*.js' -type f ! -path "./$BACKUP_DIR/*" | wc -l)"
echo "   測試 HTML: $(find . -name 'test_*.html' -type f ! -path "./$BACKUP_DIR/*" | wc -l)"
echo "   報告 MD: $(find . -name '*報告.md' -type f ! -path "./$BACKUP_DIR/*" | wc -l)"
echo ""

echo "🚀 開始清理操作..."
echo ""

# 1. 清理根目錄的測試檔案（排除 tests/ 目錄）
cleanup_files "test_*.py" "根目錄 Python 測試檔案" "! -path \"./tests/*\" ! -path \"./$BACKUP_DIR/*\""
cleanup_files "test_*.js" "根目錄 JavaScript 測試檔案" "! -path \"./tests/*\" ! -path \"./$BACKUP_DIR/*\""
cleanup_files "test_*.html" "根目錄 HTML 測試檔案" "! -path \"./tests/*\" ! -path \"./$BACKUP_DIR/*\""

# 2. 清理驗證檔案
cleanup_files "verify_*" "驗證檔案" "! -path \"./$BACKUP_DIR/*\""

# 3. 清理修復和調試檔案
cleanup_files "fix_*.py" "Python 修復檔案" "! -path \"./$BACKUP_DIR/*\""
cleanup_files "debug_*.py" "Python 調試檔案" "! -path \"./$BACKUP_DIR/*\""

# 4. 清理報告檔案（但保留重要報告）
echo "🔍 處理報告檔案..."
important_reports=(
    "綜合工作總結與遷移報告.md"
    ".clinerules-配置完成報告.md"
    ".clinerules-配置與使用指南.md"
)

# 先移動所有報告檔案到備份目錄
find . -name "*報告.md" -type f ! -path "./$BACKUP_DIR/*" | while read file; do
    filename=$(basename "$file")
    
    # 檢查是否為重要報告
    is_important=0
    for important in "${important_reports[@]}"; do
        if [[ "$filename" == "$important" ]]; then
            is_important=1
            break
        fi
    done
    
    if [ $is_important -eq 1 ]; then
        echo "   💾 保留重要報告: $file"
        # 如果是 .clinerules 相關報告，移動到 docs 目錄
        if [[ "$filename" == ".clinerules-"* ]]; then
            mv "$file" "docs/" 2>/dev/null || echo "   ⚠️  無法移動到 docs: $file"
        fi
    else
        echo "   📦 移動報告: $file"
        mv "$file" "$BACKUP_DIR/" 2>/dev/null || echo "   ⚠️  無法移動: $file"
    fi
done
echo ""

# 5. 清理 staticfiles 中的測試檔案
echo "🔍 清理 staticfiles 中的測試檔案..."
find ./staticfiles -name "test_*.html" -type f ! -path "./$BACKUP_DIR/*" 2>/dev/null | while read file; do
    echo "   📦 移動: $file"
    mv "$file" "$BACKUP_DIR/" 2>/dev/null || echo "   ⚠️  無法移動: $file"
done
echo ""

# 6. 清理 templates 中的測試檔案
echo "🔍 清理 templates 中的測試檔案..."
find ./templates -name "*test_*.html" -type f ! -path "./$BACKUP_DIR/*" 2>/dev/null | while read file; do
    echo "   📦 移動: $file"
    mv "$file" "$BACKUP_DIR/" 2>/dev/null || echo "   ⚠️  無法移動: $file"
done
echo ""

# 記錄結束時間
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

# 統計結果
echo "=========================================="
echo "           清理完成報告"
echo "=========================================="
echo ""
echo "📊 清理後檔案統計:"
echo "   測試 Python: $(find . -name 'test_*.py' -type f ! -path "./$BACKUP_DIR/*" | wc -l)"
echo "   測試 JS: $(find . -name 'test_*.js' -type f ! -path "./$BACKUP_DIR/*" | wc -l)"
echo "   測試 HTML: $(find . -name 'test_*.html' -type f ! -path "./$BACKUP_DIR/*" | wc -l)"
echo "   報告 MD: $(find . -name '*報告.md' -type f ! -path "./$BACKUP_DIR/*" | wc -l)"
echo ""
echo "💾 備份資訊:"
echo "   備份目錄: $BACKUP_DIR"
echo "   備份檔案數: $(find "$BACKUP_DIR" -type f 2>/dev/null | wc -l)"
echo "   備份大小: $(du -sh "$BACKUP_DIR" 2>/dev/null | cut -f1)"
echo ""
echo "⏱️  執行時間: ${DURATION} 秒"
echo ""
echo "🔧 重要保留檔案:"
echo "   ✅ .clinerules - AI 助理配置"
echo "   ✅ 綜合工作總結與遷移報告.md - 項目狀態報告"
echo "   ✅ docs/.clinerules-* - 配置文檔"
echo "   ✅ tests/ 目錄 - 正式測試檔案"
echo "   ✅ eshop/, cart/, socialuser/ - 核心源代碼"
echo ""
echo "⚠️  注意事項:"
echo "   1. 備份檔案保留 7 天，之後可以手動刪除"
echo "   2. 如果需要恢復檔案: cp -r $BACKUP_DIR/* ."
echo "   3. 建議運行基本測試驗證系統功能"
echo ""
echo "✅ 清理完成！項目現在更加整潔了。"
echo "=========================================="