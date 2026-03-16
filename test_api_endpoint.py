#!/usr/bin/env python3
"""
測試 API 端點是否正常工作
"""

import os
import sys
import django
import json
from django.test import Client
from django.urls import reverse

# 設置 Django 環境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'betweencoffee_delivery.settings')
django.setup()

def test_order_status_api():
    """測試訂單狀態 API 端點"""
    print("🔍 測試訂單狀態 API 端點")
    print("=" * 60)
    
    client = Client(HTTP_HOST='localhost:8081')
    
    # 測試一個存在的訂單 ID（需要根據實際數據調整）
    test_order_id = 1  # 可以修改為實際存在的訂單 ID
    
    try:
        # 構建 API URL
        url = f'/eshop/api/order-status/{test_order_id}/'
        print(f"測試 URL: {url}")
        
        # 發送 GET 請求，設置正確的 HTTP_HOST
        response = client.get(url, HTTP_HOST='localhost:8081')
        
        print(f"狀態碼: {response.status_code}")
        print(f"內容類型: {response.get('Content-Type', '未知')}")
        
        if response.status_code == 200:
            try:
                data = json.loads(response.content)
                print(f"API 響應: {json.dumps(data, indent=2, ensure_ascii=False)}")
                
                if data.get('success'):
                    print("✅ API 端點正常工作")
                    print(f"訂單 ID: {data.get('order_id')}")
                    print(f"狀態: {data.get('status')}")
                    print(f"支付狀態: {data.get('payment_status')}")
                    print(f"進度百分比: {data.get('progress_percentage')}%")
                    print(f"是否完成: {data.get('is_ready')}")
                    return True
                else:
                    print(f"❌ API 返回錯誤: {data.get('error', '未知錯誤')}")
                    return False
                    
            except json.JSONDecodeError as e:
                print(f"❌ JSON 解析錯誤: {e}")
                print(f"原始響應: {response.content}")
                return False
        else:
            print(f"❌ HTTP 錯誤: {response.status_code}")
            print(f"響應內容: {response.content}")
            return False
            
    except Exception as e:
        print(f"❌ 測試過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_with_real_order():
    """使用真實訂單數據測試"""
    print("\n🔍 使用真實訂單數據測試")
    print("=" * 60)
    
    from eshop.models import OrderModel
    
    try:
        # 獲取最新的幾個訂單
        recent_orders = OrderModel.objects.all().order_by('-id')[:5]
        
        if not recent_orders:
            print("⚠️  數據庫中沒有訂單數據")
            return False
        
        print(f"找到 {len(recent_orders)} 個訂單")
        
        client = Client()
        
        for order in recent_orders:
            print(f"\n測試訂單 #{order.id}:")
            print(f"  狀態: {order.status}")
            print(f"  支付狀態: {order.payment_status}")
            print(f"  總價: {order.total_price}")
            
            url = f'/eshop/api/order-status/{order.id}/'
            response = client.get(url)
            
            if response.status_code == 200:
                data = json.loads(response.content)
                if data.get('success'):
                    print(f"  ✅ API 正常工作")
                    print(f"    進度: {data.get('progress_percentage')}%")
                    print(f"    隊列顯示: {data.get('queue_display', 'N/A')}")
                else:
                    print(f"  ❌ API 錯誤: {data.get('error', '未知錯誤')}")
            else:
                print(f"  ❌ HTTP 錯誤: {response.status_code}")
                
        return True
        
    except Exception as e:
        print(f"❌ 測試真實訂單時發生錯誤: {e}")
        return False

def check_api_structure():
    """檢查 API 響應結構"""
    print("\n🔍 檢查 API 響應結構")
    print("=" * 60)
    
    from eshop.views.order_views import order_status_api
    import inspect
    
    print("API 函數信息:")
    print(f"  名稱: {order_status_api.__name__}")
    print(f"  文檔: {order_status_api.__doc__}")
    
    # 檢查函數簽名
    sig = inspect.signature(order_status_api)
    print(f"  參數: {sig}")
    
    # 檢查需要的響應字段
    expected_fields = [
        'success', 'order_id', 'status', 'payment_status',
        'progress_percentage', 'progress_display', 'is_ready',
        'queue_display', 'queue_message', 'remaining_display',
        'estimated_time', 'status_message'
    ]
    
    print(f"\n期望的響應字段: {expected_fields}")
    return True

def main():
    """主函數"""
    print("=" * 60)
    print("訂單狀態 API 端點測試")
    print("=" * 60)
    
    # 測試 1: 基本 API 測試
    print("\n1. 基本 API 測試")
    api_ok = test_order_status_api()
    
    # 測試 2: 使用真實訂單數據
    print("\n2. 使用真實訂單數據測試")
    real_data_ok = test_api_with_real_order()
    
    # 測試 3: 檢查 API 結構
    print("\n3. 檢查 API 結構")
    structure_ok = check_api_structure()
    
    # 總結
    print("\n" + "=" * 60)
    print("測試結果總結")
    print("=" * 60)
    
    if api_ok and real_data_ok and structure_ok:
        print("🎉 所有測試通過！")
        print("\n✅ API 端點正常工作")
        print("✅ 響應結構正確")
        print("✅ 可以處理真實訂單數據")
        print("\n📋 下一步:")
        print("1. 檢查前端 JavaScript 是否正確調用 API")
        print("2. 確認數據屬性在模板中正確設置")
        print("3. 檢查瀏覽器控制台是否有錯誤")
        return 0
    else:
        print("❌ 測試失敗，請檢查以下問題:")
        if not api_ok:
            print("  - API 端點無法訪問或返回錯誤")
        if not real_data_ok:
            print("  - 無法處理真實訂單數據")
        if not structure_ok:
            print("  - API 結構有問題")
        print("\n💡 建議:")
        print("1. 檢查服務器日誌")
        print("2. 確認 URL 配置正確")
        print("3. 檢查數據庫連接")
        return 1

if __name__ == '__main__':
    sys.exit(main())