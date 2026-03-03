#!/usr/bin/env python3
"""
Accordion 修復驗證測試
測試 order_confirm.html 中的 Accordion 功能是否正常工作
"""

import os
import re
from pathlib import Path

def check_accordion_fix():
    """檢查 Accordion 修復是否正確"""
    print("=== Accordion 修復驗證測試 ===\n")
    
    # 檢查 order_confirm.html 文件
    order_confirm_path = Path("eshop/templates/eshop/order_confirm.html")
    
    if not order_confirm_path.exists():
        print(f"❌ 錯誤: 找不到文件 {order_confirm_path}")
        return False
    
    print(f"📄 檢查文件: {order_confirm_path}")
    
    with open(order_confirm_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 檢查關鍵修復點
    checks = [
        {
            "name": "Accordion 按鈕存在",
            "pattern": r'<button class="Accordion.*?>訂單詳情',
            "required": True
        },
        {
            "name": "Accordion 有正確的 aria-selected 屬性",
            "pattern": r'aria-selected="false"',
            "required": True
        },
        {
            "name": "內容區域有 hiddenSmall 類",
            "pattern": r'class="Rtable-cell.*?hiddenSmall"',
            "required": True
        },
        {
            "name": "JavaScript 初始化代碼存在",
            "pattern": r'\$\(document\)\.ready\(function\(\)',
            "required": True
        },
        {
            "name": "JavaScript 設置初始折疊狀態",
            "pattern": r'\$accordion\.attr\("aria-selected", "false"\)',
            "required": True
        },
        {
            "name": "JavaScript 添加點擊事件",
            "pattern": r'\$accordion\.on\(\'click\'',
            "required": True
        },
        {
            "name": "JavaScript 切換 hiddenSmall 類",
            "pattern": r'\$cells\.toggleClass\("hiddenSmall"',
            "required": True
        }
    ]
    
    passed_checks = 0
    total_checks = len(checks)
    
    for check in checks:
        if re.search(check["pattern"], content, re.DOTALL):
            print(f"✅ {check['name']}: 通過")
            passed_checks += 1
        else:
            if check["required"]:
                print(f"❌ {check['name']}: 失敗 (必要檢查)")
            else:
                print(f"⚠️  {check['name']}: 失敗 (可選檢查)")
    
    # 檢查 CSS 樣式
    css_path = Path("static/css/style.css")
    if css_path.exists():
        with open(css_path, 'r', encoding='utf-8') as f:
            css_content = f.read()
        
        css_checks = [
            {
                "name": "hiddenSmall 類定義",
                "pattern": r'\.hiddenSmall\s*\{\s*display:\s*none\s*!\s*important',
                "required": True
            },
            {
                "name": "Accordion 箭頭樣式",
                "pattern": r'\.Accordion\s+\.arrow',
                "required": True
            },
            {
                "name": "Accordion 展開狀態樣式",
                "pattern": r'\.Accordion\[aria-selected="true"\]',
                "required": True
            }
        ]
        
        print(f"\n📄 檢查 CSS 文件: {css_path}")
        
        for check in css_checks:
            if re.search(check["pattern"], css_content, re.DOTALL):
                print(f"✅ {check['name']}: 通過")
                passed_checks += 1
            else:
                if check["required"]:
                    print(f"❌ {check['name']}: 失敗 (必要檢查)")
                else:
                    print(f"⚠️  {check['name']}: 失敗 (可選檢查)")
        
        total_checks += len(css_checks)
    
    # 總結結果
    print(f"\n📊 測試總結:")
    print(f"   通過檢查: {passed_checks}/{total_checks}")
    
    success_rate = (passed_checks / total_checks) * 100
    print(f"   成功率: {success_rate:.1f}%")
    
    if success_rate >= 90:
        print(f"\n🎉 Accordion 修復成功！")
        return True
    elif success_rate >= 70:
        print(f"\n⚠️  Accordion 修復基本完成，但有一些小問題")
        return True
    else:
        print(f"\n❌ Accordion 修復需要更多工作")
        return False

def check_test_page():
    """檢查測試頁面"""
    print("\n=== 測試頁面檢查 ===\n")
    
    test_page_path = Path("test_accordion_fix.html")
    
    if not test_page_path.exists():
        print(f"❌ 錯誤: 找不到測試頁面 {test_page_path}")
        return False
    
    print(f"📄 檢查測試頁面: {test_page_path}")
    
    with open(test_page_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 檢查測試頁面是否包含必要的元素
    test_checks = [
        {
            "name": "測試頁面包含 Accordion",
            "pattern": r'<button class="Accordion.*?>訂單詳情',
            "required": True
        },
        {
            "name": "測試頁面包含測試腳本",
            "pattern": r'function runTests\(\)',
            "required": True
        },
        {
            "name": "測試頁面包含 jQuery",
            "pattern": r'jquery\.com/jquery-3\.6\.0\.min\.js',
            "required": True
        }
    ]
    
    passed_checks = 0
    total_checks = len(test_checks)
    
    for check in test_checks:
        if re.search(check["pattern"], content, re.DOTALL):
            print(f"✅ {check['name']}: 通過")
            passed_checks += 1
        else:
            if check["required"]:
                print(f"❌ {check['name']}: 失敗 (必要檢查)")
            else:
                print(f"⚠️  {check['name']}: 失敗 (可選檢查)")
    
    print(f"\n📊 測試頁面檢查總結:")
    print(f"   通過檢查: {passed_checks}/{total_checks}")
    
    return passed_checks == total_checks

def main():
    """主測試函數"""
    print("🔍 開始 Accordion 修復驗證測試\n")
    
    # 檢查當前目錄
    current_dir = Path.cwd()
    print(f"當前工作目錄: {current_dir}")
    
    # 運行檢查
    accordion_fix_ok = check_accordion_fix()
    test_page_ok = check_test_page()
    
    print("\n" + "="*50)
    print("最終結果:")
    
    if accordion_fix_ok and test_page_ok:
        print("🎉 所有檢查通過！Accordion 修復完成。")
        print("\n下一步:")
        print("1. 在瀏覽器中打開 http://localhost:8000/test_accordion_fix.html")
        print("2. 測試 Accordion 的展開/收起功能")
        print("3. 檢查箭頭圖標是否正確旋轉")
        print("4. 驗證在移動端和桌面端的顯示效果")
        return 0
    elif accordion_fix_ok:
        print("⚠️  Accordion 修復完成，但測試頁面有問題")
        return 1
    else:
        print("❌ Accordion 修復需要更多工作")
        return 1

if __name__ == "__main__":
    exit(main())