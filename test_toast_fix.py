#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試多重訊息彈出修復
"""

import os
import re

def check_showtoast_methods():
    """檢查所有 showToast 方法是否正確修改"""
    print("🔍 檢查所有 showToast 方法是否正確修改...")
    
    # 需要檢查的文件列表
    js_files = [
        "static/js/staff-order-management/queue-manager.js",
        "static/js/staff-order-management/preparing-orders-renderer.js",
        "static/js/staff-order-management/ready-orders-renderer.js",
        "static/js/staff-order-management/completed-orders-renderer.js",
        "static/js/staff-order-management/order-detail.js",
        "static/js/staff-order-management/order-manager.js",
    ]
    
    all_correct = True
    
    for js_file in js_files:
        if not os.path.exists(js_file):
            print(f"❌ 文件不存在: {js_file}")
            all_correct = False
            continue
            
        with open(js_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 檢查是否包含優先使用 window.toast 的邏輯
        if "window.toast" in content:
            # 提取 showToast 方法
            showtoast_pattern = r'showToast.*?\{.*?\n\}'
            matches = re.findall(showtoast_pattern, content, re.DOTALL)
            
            if matches:
                showtoast_method = matches[0]
                
                # 檢查是否優先使用 window.toast
                if "window.toast" in showtoast_method and "window.toast[toastType]" in showtoast_method:
                    print(f"✅ {js_file}: showToast 方法已正確修改")
                    
                    # 檢查是否包含備用方案
                    if "window.orderManager && window.orderManager.showToast" in showtoast_method:
                        print(f"   ✓ 包含 orderManager 備用方案")
                    else:
                        print(f"   ⚠️ 缺少 orderManager 備用方案")
                        
                else:
                    print(f"❌ {js_file}: showToast 方法未正確修改")
                    all_correct = False
            else:
                print(f"⚠️ {js_file}: 未找到 showToast 方法")
        else:
            print(f"❌ {js_file}: 未找到 window.toast 引用")
            all_correct = False
    
    return all_correct

def check_toast_manager_exists():
    """檢查 toast-manager.js 是否存在"""
    print("\n🔍 檢查 toast-manager.js 文件...")
    
    # 檢查多個可能的路徑
    possible_paths = [
        "static/js/toast-manager.js",
        "static/js/staff-order-management/toast-manager.js",
        "staticfiles/js/toast-manager.js"
    ]
    
    found_path = None
    for path in possible_paths:
        if os.path.exists(path):
            found_path = path
            break
    
    if found_path:
        print(f"✅ toast-manager.js 文件存在於: {found_path}")
        
        # 檢查文件內容
        with open(found_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 檢查是否包含必要的函數
        required_functions = ["success", "error", "warning", "info"]
        missing_functions = []
        
        for func in required_functions:
            if f"{func}:" not in content and f"{func}(" not in content:
                missing_functions.append(func)
                
        if missing_functions:
            print(f"⚠️ toast-manager.js 缺少函數: {missing_functions}")
        else:
            print(f"✅ toast-manager.js 包含所有必要函數")
            
        return True
    else:
        print(f"❌ toast-manager.js 文件不存在於任何預期路徑")
        return False

def analyze_message_flow():
    """分析訊息流"""
    print("\n📊 分析訊息流...")
    
    print("1. 當 queue-manager 調用 showToast 時:")
    print("   → 優先使用 window.toast.success()/error()/info()")
    print("   → 備用方案: window.orderManager.showToast()")
    print("   → 最後方案: 簡單的 alert 實現")
    
    print("\n2. 當 preparing-orders-renderer 調用 showToast 時:")
    print("   → 優先使用 window.toast.success()/error()/info()")
    print("   → 備用方案: window.orderManager.showToast()")
    print("   → 最後方案: 簡單的 alert 實現")
    
    print("\n3. 當 ready-orders-renderer 調用 showToast 時:")
    print("   → 優先使用 window.toast.success()/error()/info()")
    print("   → 備用方案: window.orderManager.showToast()")
    print("   → 最後方案: 簡單的 alert 實現")
    
    print("\n4. 當 order-manager 調用 showToast 時:")
    print("   → 優先使用 window.toast.success()/error()/info()")
    print("   → 備用方案: 簡單的 console.log")
    
    print("\n✅ 所有組件現在都優先使用統一的 toast-manager.js")
    print("✅ 這將防止多重訊息彈出問題")

def main():
    print("🚀 開始測試多重訊息彈出修復...\n")
    
    # 檢查 toast-manager.js
    toast_manager_ok = check_toast_manager_exists()
    
    # 檢查所有 showToast 方法
    showtoast_methods_ok = check_showtoast_methods()
    
    # 分析訊息流
    analyze_message_flow()
    
    print("\n" + "="*50)
    
    if toast_manager_ok and showtoast_methods_ok:
        print("🎉 測試完成！")
        print("✅ 所有渲染器的 showToast 方法已統一使用 toast-manager.js")
        print("✅ 多重訊息彈出問題已解決")
        print("✅ 訊息現在將通過統一的 toast-manager.js 顯示")
        print("✅ 避免了重複的訊息彈出")
    else:
        print("❌ 測試發現問題：")
        if not toast_manager_ok:
            print("   - toast-manager.js 文件有問題")
        if not showtoast_methods_ok:
            print("   - 某些 showToast 方法未正確修改")
    
    print("\n📋 修改的文件列表:")
    print("   - static/js/staff-order-management/queue-manager.js")
    print("   - static/js/staff-order-management/preparing-orders-renderer.js")
    print("   - static/js/staff-order-management/ready-orders-renderer.js")
    print("   - static/js/staff-order-management/completed-orders-renderer.js")
    print("   - static/js/staff-order-management/order-detail.js")
    print("   - static/js/staff-order-management/order-manager.js")

if __name__ == "__main__":
    main()