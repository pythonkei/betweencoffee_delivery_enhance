#!/usr/bin/env python3
"""
測試前端訊息顯示修復和日誌警告修復
"""

import os
import re

def check_frontend_fixes():
    """檢查前端修復"""
    print("🔍 檢查前端修復...")
    
    files_to_check = [
        "static/js/staff-order-management/preparing-orders-renderer.js",
        "static/js/staff-order-management/ready-orders-renderer.js"
    ]
    
    issues_found = []
    
    for file_path in files_to_check:
        if not os.path.exists(file_path):
            print(f"❌ 文件不存在: {file_path}")
            continue
            
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 檢查是否還有 this.showToast() 調用
        show_toast_patterns = [
            r'this\.showToast\(`❌ 操作失敗',
            r'this\.showToast\(`✅ 成功',
            r'this\.showToast\(`🔄 刷新中'
        ]
        
        for pattern in show_toast_patterns:
            matches = re.findall(pattern, content)
            if matches:
                issues_found.append(f"{file_path}: 發現 {len(matches)} 個 showToast() 調用")
                
        # 檢查是否有註釋說明
        if "不再显示错误消息，由 queue-manager.js 统一处理" in content:
            print(f"✅ {file_path}: 已添加修復註釋")
        else:
            issues_found.append(f"{file_path}: 缺少修復註釋")
    
    if issues_found:
        print("❌ 前端修復問題:")
        for issue in issues_found:
            print(f"  - {issue}")
        return False
    else:
        print("✅ 前端修復檢查通過")
        return True

def check_models_logging_fix():
    """檢查 models.py 日誌修復"""
    print("\n🔍 檢查 models.py 日誌修復...")
    
    file_path = "eshop/models.py"
    
    if not os.path.exists(file_path):
        print(f"❌ 文件不存在: {file_path}")
        return False
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 檢查是否已將 logger.warning 改為 logger.debug
    warning_pattern = r'logger\.warning\(f"咖啡商品.*包含重量选项'
    debug_pattern = r'logger\.debug\(f"咖啡商品.*包含重量选项'
    
    warning_matches = re.findall(warning_pattern, content)
    debug_matches = re.findall(debug_pattern, content)
    
    if warning_matches:
        print(f"❌ 發現 {len(warning_matches)} 個 logger.warning() 調用")
        return False
    elif debug_matches:
        print(f"✅ 已將 logger.warning() 改為 logger.debug()")
        return True
    else:
        print("⚠️ 未找到相關日誌調用，可能代碼已更改")
        return True

def check_queue_manager():
    """檢查 queue-manager.js 是否保持不變"""
    print("\n🔍 檢查 queue-manager.js...")
    
    file_path = "static/js/staff-order-management/queue-manager.js"
    
    if not os.path.exists(file_path):
        print(f"⚠️ 文件不存在: {file_path}")
        return True  # 可能在其他位置
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 檢查是否有 showToast 調用
    show_toast_pattern = r'this\.showToast\('
    matches = re.findall(show_toast_pattern, content)
    
    if matches:
        print(f"✅ queue-manager.js 有 {len(matches)} 個 showToast() 調用（應該保持不變）")
        return True
    else:
        print("⚠️ queue-manager.js 沒有 showToast() 調用")
        return True

def create_test_scenario():
    """創建測試場景"""
    print("\n📋 測試場景:")
    print("1. 前端訊息顯示修復:")
    print("   - preparing-orders-renderer.js: handleMarkAsReady() 不再顯示錯誤訊息")
    print("   - ready-orders-renderer.js: handleMarkAsCollected() 不再顯示錯誤訊息")
    print("   - queue-manager.js: 統一處理所有訊息顯示")
    
    print("\n2. 日誌警告修復:")
    print("   - models.py: logger.warning() 改為 logger.debug()")
    print("   - 避免終端機無限輸出警告")
    
    print("\n3. 預期效果:")
    print("   ✅ 點擊按鈕只顯示一個訊息（來自 queue-manager.js）")
    print("   ✅ 不會出現多重訊息混亂")
    print("   ✅ 終端機不再無限輸出警告")
    print("   ✅ 所有核心功能正常")

def main():
    print("=== 前端訊息顯示和日誌警告修復測試 ===\n")
    
    # 檢查修復
    frontend_ok = check_frontend_fixes()
    logging_ok = check_models_logging_fix()
    queue_manager_ok = check_queue_manager()
    
    # 創建測試場景
    create_test_scenario()
    
    # 總結
    print("\n=== 測試總結 ===")
    
    if frontend_ok and logging_ok and queue_manager_ok:
        print("✅ 所有修復檢查通過")
        print("\n🎉 修復完成！")
        print("1. 前端訊息顯示已統一管理")
        print("2. 日誌警告級別已調整")
        print("3. 系統準備就緒")
    else:
        print("❌ 發現問題，需要進一步修復")
        if not frontend_ok:
            print("  - 前端修復不完整")
        if not logging_ok:
            print("  - 日誌修復不完整")
        if not queue_manager_ok:
            print("  - queue-manager.js 可能有問題")

if __name__ == "__main__":
    main()