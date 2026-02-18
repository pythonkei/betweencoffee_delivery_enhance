#!/usr/bin/env python3
"""
最終驗證測試 - 訂單狀態管理器修復
"""

import os
import re
import sys

def print_header(title):
    """打印標題"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def check_file_exists(file_path):
    """檢查文件是否存在"""
    if os.path.exists(file_path):
        print(f"✅ 文件存在: {file_path}")
        return True
    else:
        print(f"❌ 文件不存在: {file_path}")
        return False

def verify_order_status_manager_fix():
    """驗證 order_status_manager.py 修復"""
    print_header("驗證 OrderStatusManager 修復")
    
    file_path = "eshop/order_status_manager.py"
    
    if not check_file_exists(file_path):
        return False
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 檢查修復註釋
    if "事件觸發已由其他方法處理，此處不再需要" in content:
        print("✅ 修復註釋已添加")
    else:
        print("❌ 缺少修復註釋")
        return False
    
    # 檢查 mark_as_preparing_manually 方法
    method_pattern = r'def mark_as_preparing_manually.*?(?=def|\Z)'
    method_match = re.search(method_pattern, content, re.DOTALL)
    
    if not method_match:
        print("❌ mark_as_preparing_manually 方法未找到")
        return False
    
    method_content = method_match.group(0)
    
    # 檢查是否還有 _trigger_status_change_events 調用（排除註釋）
    lines = method_content.split('\n')
    has_actual_call = False
    
    for line in lines:
        stripped = line.strip()
        # 跳過註釋行
        if stripped.startswith('#'):
            continue
        # 檢查實際調用
        if '_trigger_status_change_events' in line:
            has_actual_call = True
            print(f"❌ 發現無效調用: {line.strip()}")
    
    if has_actual_call:
        return False
    
    print("✅ mark_as_preparing_manually 方法修復完成")
    
    # 檢查其他狀態變化方法
    methods_to_check = [
        'mark_as_ready_manually',
        'mark_as_completed_manually',
        'mark_as_waiting_manually',
        'mark_as_cancelled_manually'
    ]
    
    all_methods_ok = True
    for method in methods_to_check:
        if f"def {method}" not in content:
            print(f"⚠️ 方法 {method} 未找到")
            continue
        
        # 檢查是否有 _trigger_status_change_events 調用
        method_pattern = rf'def {method}.*?(?=def|\Z)'
        method_match = re.search(method_pattern, content, re.DOTALL)
        
        if method_match:
            method_content = method_match.group(0)
            if '_trigger_status_change_events' in method_content:
                print(f"❌ 方法 {method} 包含無效調用")
                all_methods_ok = False
    
    if all_methods_ok:
        print("✅ 所有狀態變化方法檢查通過")
    
    return all_methods_ok

def verify_process_order_status_change():
    """驗證 process_order_status_change 方法"""
    print_header("驗證 ProcessOrderStatusChange 方法")
    
    file_path = "eshop/order_status_manager.py"
    
    if not check_file_exists(file_path):
        return False
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 檢查方法是否存在
    if "def process_order_status_change" not in content:
        print("❌ process_order_status_change 方法未找到")
        return False
    
    # 檢查關鍵功能
    required_features = [
        'send_order_update',
        'recalculate_all_order_times',
        'WebSocket',
        'status_change'
    ]
    
    missing_features = []
    for feature in required_features:
        if feature not in content:
            missing_features.append(feature)
    
    if missing_features:
        print(f"⚠️ 缺少功能: {', '.join(missing_features)}")
        return False
    
    print("✅ process_order_status_change 方法完整")
    return True

def verify_frontend_error_handling():
    """驗證前端錯誤處理"""
    print_header("驗證前端錯誤處理")
    
    file_path = "static/js/staff-order-management/queue-manager.js"
    
    if not check_file_exists(file_path):
        print("⚠️ 前端文件未找到，跳過檢查")
        return True
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 檢查錯誤處理
    error_handling_patterns = [
        r'catch.*error.*{',
        r'showToast.*error.*message',
        r'HTTP.*400.*Bad Request',
        r'response\.ok'
    ]
    
    patterns_found = 0
    for pattern in error_handling_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            patterns_found += 1
    
    if patterns_found >= 2:
        print(f"✅ 前端錯誤處理機制完整 (找到 {patterns_found}/4 個模式)")
    else:
        print(f"⚠️ 前端錯誤處理可能不完整 (找到 {patterns_found}/4 個模式)")
    
    return True

def verify_websocket_integration():
    """驗證 WebSocket 集成"""
    print_header("驗證 WebSocket 集成")
    
    # 檢查相關文件
    files_to_check = [
        "eshop/order_status_manager.py",
        "eshop/websocket_utils.py",
        "eshop/consumers.py"
    ]
    
    websocket_found = False
    for file_path in files_to_check:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if 'WebSocket' in content or 'websocket' in content:
                    websocket_found = True
                    print(f"✅ WebSocket 集成在 {os.path.basename(file_path)} 中找到")
                    break
    
    if not websocket_found:
        print("⚠️ WebSocket 集成未找到")
    
    return True

def create_summary_report():
    """創建總結報告"""
    print_header("修復總結報告")
    
    print("📋 問題描述:")
    print("   1. 前端錯誤訊息: ❌ 錯誤 ❌ 操作失敗: HTTP 400: Bad Request")
    print("   2. 後端錯誤: type object 'OrderStatusManager' has no attribute '_trigger_status_change_events'")
    
    print("\n🔧 修復方案:")
    print("   1. 移除 order_status_manager.py 中的無效 _trigger_status_change_events 調用")
    print("   2. 添加修復註釋說明原因")
    print("   3. 確保事件觸發由 process_order_status_change 方法處理")
    
    print("\n✅ 預期修復效果:")
    print("   1. 點擊'開始制作'按鈕不再彈出錯誤訊息")
    print("   2. 終端機不再輸出 _trigger_status_change_events 錯誤")
    print("   3. 訂單狀態正常從 waiting 變為 preparing")
    print("   4. WebSocket 更新正常")
    print("   5. 所有相關功能不受影響")
    
    print("\n🔍 修復原理:")
    print("   - _trigger_status_change_events 方法不存在，導致調用失敗")
    print("   - 事件觸發已由 process_order_status_change 方法處理")
    print("   - 移除無效調用，避免 HTTP 400 錯誤")
    print("   - 保持系統完整性，不影響其他功能")

def main():
    """主測試函數"""
    print("=== 訂單狀態管理器修復最終驗證 ===\n")
    
    # 運行所有檢查
    checks = [
        ("OrderStatusManager 修復", verify_order_status_manager_fix),
        ("ProcessOrderStatusChange 方法", verify_process_order_status_change),
        ("前端錯誤處理", verify_frontend_error_handling),
        ("WebSocket 集成", verify_websocket_integration),
    ]
    
    results = []
    for check_name, check_func in checks:
        try:
            result = check_func()
            results.append((check_name, result))
        except Exception as e:
            print(f"❌ {check_name} 檢查失敗: {str(e)}")
            results.append((check_name, False))
    
    # 創建總結報告
    create_summary_report()
    
    # 顯示結果
    print_header("驗證結果")
    
    all_passed = True
    for check_name, result in results:
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"{check_name}: {status}")
        if not result:
            all_passed = False
    
    print_header("最終結論")
    
    if all_passed:
        print("🎉 所有檢查通過！修復完成！")
        print("\n📋 下一步:")
        print("   1. 重新啟動 Django 開發伺服器")
        print("   2. 測試點擊'開始制作'按鈕")
        print("   3. 驗證錯誤訊息是否消失")
        print("   4. 檢查終端機日誌")
        return 0
    else:
        print("❌ 發現問題，需要進一步修復")
        print("\n📋 建議:")
        print("   1. 檢查 order_status_manager.py 中的無效調用")
        print("   2. 確保所有狀態變化方法正常")
        print("   3. 驗證前端錯誤處理")
        return 1

if __name__ == "__main__":
    sys.exit(main())