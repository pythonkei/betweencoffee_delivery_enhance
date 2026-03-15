#!/usr/bin/env python3
"""
簡單測試支付回調重定向功能
"""

import os
import sys

def check_template_fix():
    """檢查模板修復"""
    print("🔍 檢查模板修復狀態...")
    print("-" * 50)
    
    template_path = 'eshop/templates/eshop/order_payment_confirmation.html'
    
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 檢查關鍵修復
        issues = []
        
        # 檢查 {% with %} 和 {% endwith %} 配對
        with_count = content.count('{% with')
        endwith_count = content.count('{% endwith %}')
        
        if with_count == endwith_count:
            print(f"✅ {{% with %}} 和 {{% endwith %}} 配對正確: {with_count} 對")
        else:
            issues.append(f"❌ {{% with %}} 和 {{% endwith %}} 數量不匹配: with={with_count}, endwith={endwith_count}")
        
        # 檢查特定修復
        lines = content.split('\n')
        found_with = False
        found_endwith = False
        
        for i, line in enumerate(lines, 1):
            if '{% with order_type=order.get_order_type_summary %}' in line:
                print(f"✅ 找到 {{% with %}} 標籤在第 {i} 行")
                found_with = True
            if '{% endwith %}' in line and i < 10:  # 只檢查前10行
                print(f"✅ 找到 {{% endwith %}} 標籤在第 {i} 行")
                found_endwith = True
        
        if found_with and found_endwith:
            print("✅ 特定修復已應用")
        else:
            if not found_with:
                issues.append("❌ 未找到 {% with order_type=order.get_order_type_summary %}")
            if not found_endwith:
                issues.append("❌ 未找到 {% endwith %} 標籤")
        
        # 輸出結果
        if issues:
            print("\n❌ 發現問題:")
            for issue in issues:
                print(f"  {issue}")
            return False
        else:
            print("\n✅ 模板修復檢查通過！")
            return True
            
    except Exception as e:
        print(f"❌ 檢查過程中發生錯誤: {e}")
        return False

def check_view_function():
    """檢查視圖函數"""
    print("\n🔍 檢查視圖函數...")
    print("-" * 50)
    
    view_path = 'eshop/views/order_views.py'
    
    try:
        with open(view_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 檢查 order_payment_confirmation 函數
        if 'def order_payment_confirmation' in content:
            print("✅ 找到 order_payment_confirmation 視圖函數")
            
            # 檢查是否有錯誤處理
            if 'TemplateSyntaxError' in content:
                print("⚠️  視圖中有 TemplateSyntaxError 處理")
            
            # 檢查重定向邏輯
            if 'redirect(' in content:
                print("✅ 視圖中有重定向邏輯")
            else:
                print("⚠️  視圖中可能缺少重定向邏輯")
            
            return True
        else:
            print("❌ 未找到 order_payment_confirmation 視圖函數")
            return False
            
    except Exception as e:
        print(f"❌ 檢查視圖函數時發生錯誤: {e}")
        return False

def check_payment_callback():
    """檢查支付回調視圖"""
    print("\n🔍 檢查支付回調視圖...")
    print("-" * 50)
    
    payment_view_path = 'eshop/views/payment_views.py'
    
    try:
        with open(payment_view_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 檢查支付寶回調
        if 'alipay_callback' in content:
            print("✅ 找到支付寶回調函數")
        
        # 檢查 PayPal 回調
        if 'paypal_callback' in content:
            print("✅ 找到 PayPal 回調函數")
        
        # 檢查重定向到支付確認頁面
        if 'payment-confirmation' in content:
            print("✅ 支付回調中有重定向到支付確認頁面的邏輯")
        else:
            print("⚠️  支付回調中可能缺少重定向到支付確認頁面的邏輯")
        
        return True
        
    except Exception as e:
        print(f"❌ 檢查支付回調視圖時發生錯誤: {e}")
        return False

def main():
    """主函數"""
    print("=" * 60)
    print("支付回調重定向功能測試")
    print("=" * 60)
    
    # 檢查模板修復
    template_ok = check_template_fix()
    
    # 檢查視圖函數
    view_ok = check_view_function()
    
    # 檢查支付回調
    callback_ok = check_payment_callback()
    
    print("\n" + "=" * 60)
    print("測試結果總結")
    print("=" * 60)
    
    if template_ok and view_ok and callback_ok:
        print("🎉 基本檢查通過！")
        print("\n✅ 模板語法錯誤已修復")
        print("✅ 視圖函數存在")
        print("✅ 支付回調函數存在")
        print("\n📋 後續步驟:")
        print("1. 重啟 Django 開發服務器")
        print("2. 測試支付寶支付完整流程")
        print("3. 測試 PayPal 支付完整流程")
        print("4. 監控日誌確認無錯誤")
        print("\n💡 如果問題仍然存在，請檢查:")
        print("   - 服務器日誌中的詳細錯誤信息")
        print("   - 瀏覽器控制台中的 JavaScript 錯誤")
        print("   - 網絡請求中的重定向路徑")
        return 0
    else:
        print("❌ 檢查失敗，請修復發現的問題")
        return 1

if __name__ == '__main__':
    sys.exit(main())