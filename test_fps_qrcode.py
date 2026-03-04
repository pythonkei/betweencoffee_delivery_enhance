#!/usr/bin/env python3
"""
FPS QR Code 添加驗證測試
檢查 order_confirm.html 中是否正確添加了 FPS QR code 圖片
"""

import os
import re

def check_fps_qrcode():
    """檢查 FPS QR code 是否正確添加"""
    file_path = "eshop/templates/eshop/order_confirm.html"
    
    if not os.path.exists(file_path):
        print(f"❌ 文件不存在: {file_path}")
        return False
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("🔍 開始檢查 FPS QR code 添加情況")
    print("=" * 60)
    
    # 檢查關鍵元素
    checks = [
        {
            "name": "FPS QR code 圖片標籤",
            "pattern": r'<img src="{% static \'images/fps_qrcode_v2\.png\' %}"',
            "description": "檢查是否使用正確的圖片文件"
        },
        {
            "name": "QR code 容器",
            "pattern": r'<div class="fps-qrcode-container mt-3 text-center">',
            "description": "檢查 QR code 容器是否存在"
        },
        {
            "name": "圖片樣式",
            "pattern": r'style="max-width: 100%; border: 1px solid #ddd; border-radius: 8px; padding: 15px; background-color: white; display: block; margin: 0 auto;"',
            "description": "檢查圖片樣式是否正確"
        },
        {
            "name": "說明文字",
            "pattern": r'請使用手機銀行App<br>掃描此QR code進行支付',
            "description": "檢查說明文字是否存在"
        },
        {
            "name": "FPS 支付方式選項",
            "pattern": r'<span class="payment-modern-name">FPS 轉數快</span>',
            "description": "檢查 FPS 支付選項是否存在"
        }
    ]
    
    passed = 0
    total = len(checks)
    
    for check in checks:
        if re.search(check["pattern"], content):
            print(f"✅ {check['name']}: 通過")
            print(f"   描述: {check['description']}")
            passed += 1
        else:
            print(f"❌ {check['name']}: 失敗")
            print(f"   描述: {check['description']}")
            print(f"   模式: {check['pattern']}")
    
    print("=" * 60)
    print(f"📊 測試結果: {passed}/{total} 通過")
    
    if passed == total:
        print("🎉 FPS QR code 添加成功！")
        return True
    else:
        print("⚠️  部分檢查失敗，請檢查修改")
        return False

def check_image_file():
    """檢查圖片文件是否存在"""
    image_path = "static/images/fps_qrcode_v2.png"
    
    if os.path.exists(image_path):
        print(f"✅ 圖片文件存在: {image_path}")
        # 獲取文件大小
        size = os.path.getsize(image_path)
        print(f"   文件大小: {size:,} bytes ({size/1024:.1f} KB)")
        return True
    else:
        print(f"❌ 圖片文件不存在: {image_path}")
        print("   請確保 static/images/fps_qrcode_v2.png 存在")
        return False

def main():
    """主測試函數"""
    print("🚀 FPS QR Code 添加驗證測試")
    print("=" * 60)
    
    # 檢查圖片文件
    print("\n📄 檢查圖片文件:")
    image_ok = check_image_file()
    
    # 檢查 HTML 修改
    print("\n📝 檢查 HTML 修改:")
    html_ok = check_fps_qrcode()
    
    print("\n" + "=" * 60)
    print("📋 最終總結:")
    
    if image_ok and html_ok:
        print("🎉 所有檢查通過！FPS QR code 已成功添加。")
        print("\n✅ 下一步:")
        print("   1. 啟動 Django 開發服務器")
        print("   2. 訪問 http://localhost:8000/eshop/order/confirm/")
        print("   3. 選擇 FPS 轉數快支付方式")
        print("   4. 確認 QR code 正確顯示")
        return True
    else:
        print("⚠️  測試失敗，請檢查問題")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)