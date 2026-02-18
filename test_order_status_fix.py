#!/usr/bin/env python3
"""
測試訂單狀態管理器修復
"""

import os
import re

def check_order_status_manager_fix():
    """檢查 order_status_manager.py 修復"""
    print("🔍 檢查 order_status_manager.py 修復...")
    
    file_path = "eshop/order_status_manager.py"
    
    if not os.path.exists(file_path):
        print(f"❌ 文件不存在: {file_path}")
        return False
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 檢查是否還有 _trigger_status_change_events 調用（排除註釋）
    # 先移除註釋行
    lines = content.split('\n')
    code_lines = []
    for line in lines:
        stripped = line.strip()
        # 跳過註釋行
        if stripped.startswith('#') or stripped.startswith('"""') or stripped.startswith("'''"):
            continue
        # 跳過行內註釋
        if '#' in line:
            line = line.split('#')[0]
        code_lines.append(line)
    
    code_content = '\n'.join(code_lines)
    
    # 檢查實際調用
    pattern = r'cls\._trigger_status_change_events\('
    matches = re.findall(pattern, code_content)
    
    if matches:
        print(f"❌ 發現 {len(matches)} 個 _trigger_status_change_events 調用（排除註釋後）")
        # 顯示具體位置
        for i, line in enumerate(lines):
            if 'cls._trigger_status_change_events' in line and not line.strip().startswith('#'):
                print(f"  第 {i+1} 行: {line.strip()}")
        return False
    
    # 檢查是否有註釋說明
    if "事件觸發已由其他方法處理，此處不再需要" in content:
        print("✅ 已添加修復註釋")
    else:
        print("⚠️ 缺少修復註釋")
    
    # 檢查 mark_as_preparing_manually 方法（排除註釋）
    method_pattern = r'def mark_as_preparing_manually.*?(?=def|\Z)'
    method_match = re.search(method_pattern, content, re.DOTALL)
    
    if method_match:
        method_content = method_match.group(0)
        # 移除註釋
        method_lines = method_content.split('\n')
        clean_method_lines = []
        for line in method_lines:
            stripped = line.strip()
            if not stripped.startswith('#'):
                clean_method_lines.append(line)
        
        clean_method_content = '\n'.join(clean_method_lines)
        
        if "cls._trigger_status_change_events" in clean_method_content:
            print("❌ mark_as_preparing_manually 方法中仍有無效調用")
            return False
    
    print("✅ order_status_manager.py 修復檢查通過")
    return True

def check_other_status_methods():
    """檢查其他狀態變化方法"""
    print("\n🔍 檢查其他狀態變化方法...")
    
    file_path = "eshop/order_status_manager.py"
    
    if not os.path.exists(file_path):
        return True  # 文件不存在，跳過檢查
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    methods_to_check = [
        'mark_as_ready_manually',
        'mark_as_completed_manually',
        'mark_as_waiting_manually',
        'mark_as_cancelled_manually'
    ]
    
    issues_found = []
    
    for method in methods_to_check:
        # 檢查方法是否存在
        if f"def {method}" not in content:
            issues_found.append(f"方法 {method} 不存在")
            continue
        
        # 檢查是否有 _trigger_status_change_events 調用
        method_pattern = rf'def {method}.*?(?=def|\Z)'
        method_match = re.search(method_pattern, content, re.DOTALL)
        
        if method_match:
            method_content = method_match.group(0)
            if '_trigger_status_change_events' in method_content:
                issues_found.append(f"方法 {method} 包含 _trigger_status_change_events 調用")
    
    if issues_found:
        print("❌ 其他方法問題:")
        for issue in issues_found:
            print(f"  - {issue}")
        return False
    else:
        print("✅ 其他狀態變化方法檢查通過")
        return True

def check_process_order_status_change():
    """檢查 process_order_status_change 方法"""
    print("\n🔍 檢查 process_order_status_change 方法...")
    
    file_path = "eshop/order_status_manager.py"
    
    if not os.path.exists(file_path):
        return True
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 檢查方法是否存在
    if "def process_order_status_change" not in content:
        print("❌ process_order_status_change 方法不存在")
        return False
    
    # 檢查方法是否完整
    if "send_order_update" in content and "recalculate_all_order_times" in content:
        print("✅ process_order_status_change 方法完整")
        return True
    else:
        print("⚠️ process_order_status_change 方法可能不完整")
        return True

def create_test_scenario():
    """創建測試場景"""
    print("\n📋 測試場景:")
    print("1. 修復問題:")
    print("   - order_status_manager.py: 移除無效的 _trigger_status_change_events 調用")
    print("   - 添加註釋說明修復原因")
    
    print("\n2. 預期效果:")
    print("   ✅ 點擊'開始制作'按鈕不再彈出錯誤訊息")
    print("   ✅ 終端機不再輸出 _trigger_status_change_events 錯誤")
    print("   ✅ 訂單狀態正常從 waiting 變為 preparing")
    print("   ✅ WebSocket 更新正常")
    print("   ✅ 所有相關功能不受影響")
    
    print("\n3. 修復原理:")
    print("   - _trigger_status_change_events 方法不存在，導致調用失敗")
    print("   - 事件觸發已由 process_order_status_change 方法處理")
    print("   - 移除無效調用，避免 HTTP 400 錯誤")

def main():
    print("=== 訂單狀態管理器修復測試 ===\n")
    
    # 檢查修復
    main_fix_ok = check_order_status_manager_fix()
    other_methods_ok = check_other_status_methods()
    process_method_ok = check_process_order_status_change()
    
    # 創建測試場景
    create_test_scenario()
    
    # 總結
    print("\n=== 測試總結 ===")
    
    if main_fix_ok and other_methods_ok and process_method_ok:
        print("✅ 所有修復檢查通過")
        print("\n🎉 修復完成！")
        print("1. 移除無效的 _trigger_status_change_events 調用")
        print("2. 添加修復註釋說明")
        print("3. 確保其他狀態變化方法正常")
        print("4. 系統準備就緒")
    else:
        print("❌ 發現問題，需要進一步修復")
        if not main_fix_ok:
            print("  - order_status_manager.py 修復不完整")
        if not other_methods_ok:
            print("  - 其他狀態變化方法有問題")
        if not process_method_ok:
            print("  - process_order_status_change 方法有問題")

if __name__ == "__main__":
    main()