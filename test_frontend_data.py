#!/usr/bin/env python
"""
測試前端實際接收到的數據
模擬前端調用統一隊列數據API
"""

import os
import sys
import django
import json
from datetime import datetime
import pytz

# 設置Django環境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'betweencoffee_delivery.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    django.setup()
except Exception as e:
    print(f'❌ Django設置失敗: {e}')
    sys.exit(1)

from django.test import RequestFactory
from eshop.views.queue_views import get_unified_queue_data
from eshop.models import OrderModel

def test_unified_queue_data_api():
    """測試統一隊列數據API返回的數據"""
    print("=== 測試統一隊列數據API ===")
    
    # 創建測試請求
    factory = RequestFactory()
    request = factory.get('/api/queue/unified-data/')
    
    # 模擬用戶登入（這裡使用匿名用戶，實際應該有權限檢查）
    request.user = type('User', (), {'is_authenticated': True, 'is_staff': True})()
    
    try:
        # 調用API
        response = get_unified_queue_data(request)
        
        # 解析響應
        response_data = json.loads(response.content)
        
        print(f"API響應狀態: {response_data.get('success')}")
        print(f"消息: {response_data.get('message')}")
        
        if response_data.get('success'):
            data = response_data.get('data', {})
            
            print(f"\n📊 數據統計:")
            print(f"  等待訂單: {len(data.get('waiting_orders', []))} 個")
            print(f"  製作中訂單: {len(data.get('preparing_orders', []))} 個")
            print(f"  就緒訂單: {len(data.get('ready_orders', []))} 個")
            print(f"  已完成訂單: {len(data.get('completed_orders', []))} 個")
            
            # 檢查訂單 #127 在哪個列表中
            print(f"\n🔍 檢查訂單 #127 的位置:")
            
            # 檢查製作中訂單
            preparing_orders = data.get('preparing_orders', [])
            order_127_in_preparing = any(order.get('id') == 127 for order in preparing_orders)
            
            if order_127_in_preparing:
                print(f"  ❌ 訂單 #127 出現在製作中訂單列表中")
                for order in preparing_orders:
                    if order.get('id') == 127:
                        print(f"    訂單數據: ID={order.get('id')}, 狀態={order.get('status', '未知')}")
                        print(f"    取餐碼: {order.get('pickup_code')}")
                        print(f"    客戶: {order.get('name')}")
                        break
            else:
                print(f"  ✅ 訂單 #127 沒有出現在製作中訂單列表中")
            
            # 檢查就緒訂單
            ready_orders = data.get('ready_orders', [])
            order_127_in_ready = any(order.get('id') == 127 for order in ready_orders)
            
            if order_127_in_ready:
                print(f"  ⚠️ 訂單 #127 出現在就緒訂單列表中")
            else:
                print(f"  ✅ 訂單 #127 沒有出現在就緒訂單列表中")
            
            # 檢查已完成訂單
            completed_orders = data.get('completed_orders', [])
            order_127_in_completed = any(order.get('id') == 127 for order in completed_orders)
            
            if order_127_in_completed:
                print(f"  ✅ 訂單 #127 出現在已完成訂單列表中（正確）")
                for order in completed_orders:
                    if order.get('id') == 127:
                        print(f"    訂單數據: ID={order.get('id')}, 取餐時間={order.get('picked_up_at')}")
                        break
            else:
                print(f"  ⚠️ 訂單 #127 沒有出現在已完成訂單列表中")
            
            # 檢查徽章摘要
            badge_summary = data.get('badge_summary', {})
            print(f"\n📛 徽章摘要:")
            print(f"  等待: {badge_summary.get('waiting', 0)}")
            print(f"  製作中: {badge_summary.get('preparing', 0)}")
            print(f"  就緒: {badge_summary.get('ready', 0)}")
            print(f"  已完成: {badge_summary.get('completed', 0)}")
            
            # 檢查所有訂單的狀態一致性
            print(f"\n🔎 檢查數據一致性:")
            
            # 獲取數據庫中的訂單狀態
            try:
                db_order = OrderModel.objects.get(id=127)
                print(f"  數據庫中訂單 #127 狀態: {db_order.status}")
                print(f"  數據庫中訂單 #127 取餐時間: {db_order.picked_up_at}")
            except OrderModel.DoesNotExist:
                print(f"  ❌ 數據庫中訂單 #127 不存在")
            
        else:
            print(f"❌ API返回失敗: {response_data.get('error')}")
            
    except Exception as e:
        print(f"❌ 測試API失敗: {e}")
        import traceback
        traceback.print_exc()

def check_order_status_inconsistency():
    """檢查訂單狀態不一致問題"""
    print("\n=== 檢查訂單狀態不一致問題 ===")
    
    # 檢查所有訂單的狀態
    orders = OrderModel.objects.all().order_by('-id')[:20]
    
    print(f"最近20個訂單的狀態:")
    for order in orders:
        print(f"  訂單 #{order.id}: 狀態={order.status}, 支付={order.payment_status}, 取餐時間={order.picked_up_at}")
    
    # 檢查 completed 狀態但沒有取餐時間的訂單
    completed_without_pickup = OrderModel.objects.filter(
        status='completed',
        picked_up_at__isnull=True
    )
    
    print(f"\n❌ 發現 {completed_without_pickup.count()} 個 completed 狀態但沒有取餐時間的訂單:")
    for order in completed_without_pickup:
        print(f"  訂單 #{order.id}: 創建時間={order.created_at}")

def check_frontend_rendering_logic():
    """檢查前端渲染邏輯"""
    print("\n=== 檢查前端渲染邏輯 ===")
    
    # 檢查 preparing-orders-renderer.js 中的過濾邏輯
    print("檢查前端渲染器可能問題:")
    print("1. preparing-orders-renderer.js 從 unifiedDataManager 獲取數據")
    print("2. unifiedDataManager 從 /api/queue/unified-data/ 獲取數據")
    print("3. 如果訂單 #127 出現在製作中列表，可能是:")
    print("   a) API返回了錯誤的數據")
    print("   b) 前端緩存了舊數據")
    print("   c) WebSocket推送了錯誤的更新")
    
    # 建議的檢查步驟
    print("\n🔧 建議的檢查步驟:")
    print("1. 檢查瀏覽器控制台日誌")
    print("2. 檢查網絡請求 /api/queue/unified-data/ 的響應")
    print("3. 檢查前端是否有數據緩存")
    print("4. 檢查 WebSocket 消息內容")

def main():
    """主函數"""
    print("=" * 60)
    print("測試前端實際接收到的數據")
    print("=" * 60)
    
    test_unified_queue_data_api()
    check_order_status_inconsistency()
    check_frontend_rendering_logic()
    
    print("\n" + "=" * 60)
    print("測試完成")
    print("=" * 60)
    
    print("\n🎯 總結:")
    print("1. 訂單 #127 狀態為 completed，沒有隊列項")
    print("2. 後端 API 應該不會返回訂單 #127 到製作中列表")
    print("3. 問題可能在前端：")
    print("   - 數據緩存問題")
    print("   - WebSocket 推送問題")
    print("   - 渲染器邏輯錯誤")

if __name__ == "__main__":
    main()