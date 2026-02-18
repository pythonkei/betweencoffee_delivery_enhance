#!/usr/bin/env python
"""
測試 process_preparing_queues 函數邏輯
"""

import os
import sys
import django
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

from eshop.models import OrderModel, CoffeeQueue
from django.utils import timezone

def test_process_preparing_logic():
    """測試 process_preparing_queues 函數邏輯"""
    print("=== 測試 process_preparing_queues 函數邏輯 ===")
    
    # 獲取香港時區與當前時間
    hk_tz = pytz.timezone('Asia/Hong_Kong')
    now = timezone.now().astimezone(hk_tz)
    
    # 模擬 process_preparing_queues 函數的邏輯
    preparing_queues = CoffeeQueue.objects.filter(status='preparing')
    print(f"隊列狀態為 preparing 的隊列項: {preparing_queues.count()} 個")
    
    # 檢查訂單 #127 是否在隊列中
    try:
        order_127 = OrderModel.objects.get(id=127)
        print(f"\n訂單 #127 詳細信息:")
        print(f"  狀態: {order_127.status}")
        print(f"  支付狀態: {order_127.payment_status}")
        print(f"  取餐時間: {order_127.picked_up_at}")
        
        # 檢查是否有隊列項
        try:
            queue_item = CoffeeQueue.objects.get(order=order_127)
            print(f"  隊列項狀態: {queue_item.status}")
            print(f"  隊列位置: {queue_item.position}")
            
            # 檢查是否會被 process_preparing_queues 函數處理
            if queue_item.status == 'preparing':
                print(f"  ⚠️ 訂單 #127 有 preparing 狀態的隊列項，會被 process_preparing_queues 處理")
                
                # 模擬函數中的邏輯
                if order_127.status != 'preparing':
                    print(f"  ⚠️ 訂單狀態為 {order_127.status}，但隊列狀態為 preparing")
                    print(f"  ⚠️ 根據 queue_views.py 第 200-210 行邏輯，會自動將訂單狀態改為 preparing")
                    
                    if order_127.status == 'completed':
                        print(f"  ❌ 嚴重問題：訂單已完成，但會被錯誤地改為 preparing 狀態！")
                    elif order_127.status == 'ready':
                        print(f"  ❌ 嚴重問題：訂單已就緒，但會被錯誤地改為 preparing 狀態！")
                        
            else:
                print(f"  ✅ 訂單 #127 的隊列狀態不是 preparing，不會被 process_preparing_queues 處理")
                
        except CoffeeQueue.DoesNotExist:
            print(f"  ✅ 訂單 #127 沒有隊列項，不會被 process_preparing_queues 處理")
            
    except OrderModel.DoesNotExist:
        print("❌ 訂單 #127 不存在")
    
    # 檢查所有 preparing 隊列項的訂單狀態
    print(f"\n=== 檢查所有 preparing 隊列項的訂單狀態 ===")
    
    status_counts = {}
    for queue_item in preparing_queues:
        order = queue_item.order
        status = order.status
        status_counts[status] = status_counts.get(status, 0) + 1
        
        if status != 'preparing':
            print(f"  ⚠️ 隊列項 #{queue_item.id} (訂單 #{order.id}): 隊列狀態={queue_item.status}, 訂單狀態={status}")
    
    print(f"\n📊 狀態統計:")
    for status, count in status_counts.items():
        print(f"  {status}: {count} 個")
    
    # 檢查是否有 completed 或 ready 狀態的訂單在 preparing 隊列中
    problematic_statuses = ['completed', 'ready', 'waiting']
    for status in problematic_statuses:
        if status in status_counts:
            print(f"\n❌ 發現問題：有 {status_counts[status]} 個 {status} 狀態的訂單在 preparing 隊列中")
            print(f"  這些訂單會被 process_preparing_queues 函數錯誤地改為 preparing 狀態")

def check_unified_queue_data():
    """檢查統一隊列數據API"""
    print("\n=== 檢查統一隊列數據API ===")
    
    # 模擬 get_unified_queue_data 函數的邏輯
    try:
        from eshop.views.queue_views import process_preparing_queues
        
        hk_tz = pytz.timezone('Asia/Hong_Kong')
        now = timezone.now().astimezone(hk_tz)
        
        preparing_orders = process_preparing_queues(now, hk_tz)
        
        print(f"process_preparing_queues 返回的訂單數量: {len(preparing_orders)} 個")
        
        # 檢查訂單 #127 是否在返回的數據中
        order_127_in_list = any(order['id'] == 127 for order in preparing_orders)
        
        if order_127_in_list:
            print(f"❌ 訂單 #127 出現在 process_preparing_queues 返回的數據中")
            
            # 找到訂單 #127 的數據
            for order in preparing_orders:
                if order['id'] == 127:
                    print(f"  訂單數據: {order}")
                    break
        else:
            print(f"✅ 訂單 #127 沒有出現在 process_preparing_queues 返回的數據中")
            
    except Exception as e:
        print(f"❌ 檢查統一隊列數據API失敗: {e}")
        import traceback
        traceback.print_exc()

def main():
    """主函數"""
    print("=" * 60)
    print("測試 process_preparing_queues 函數邏輯")
    print("=" * 60)
    
    test_process_preparing_logic()
    check_unified_queue_data()
    
    print("\n" + "=" * 60)
    print("測試完成")
    print("=" * 60)

if __name__ == "__main__":
    main()