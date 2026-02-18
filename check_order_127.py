#!/usr/bin/env python
"""
簡單檢查訂單 #127 狀態
"""

import os
import sys
import django

# 設置Django環境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'betweencoffee_delivery.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    django.setup()
except Exception as e:
    print(f'❌ Django設置失敗: {e}')
    sys.exit(1)

from eshop.models import OrderModel, CoffeeQueue

print('=== 檢查訂單 #127 狀態 ===')
try:
    order = OrderModel.objects.get(id=127)
    print(f'✅ 訂單 #{order.id} 存在')
    print(f'  狀態: {order.status}')
    print(f'  支付狀態: {order.payment_status}')
    print(f'  訂單類型: {order.order_type}')
    print(f'  創建時間: {order.created_at}')
    print(f'  就緒時間: {order.ready_at}')
    print(f'  取餐時間: {order.picked_up_at}')
    
    # 檢查隊列狀態
    try:
        queue_item = CoffeeQueue.objects.get(order=order)
        print(f'✅ 訂單 #{order.id} 有隊列項 #{queue_item.id}')
        print(f'  隊列狀態: {queue_item.status}')
        print(f'  隊列位置: {queue_item.position}')
        print(f'  咖啡杯數: {queue_item.coffee_count}')
        print(f'  製作時間: {queue_item.preparation_time_minutes}分鐘')
        
        # 檢查狀態一致性
        if order.status == 'completed' and queue_item.status != 'ready':
            print(f'❌ 狀態不一致: 訂單狀態=completed, 隊列狀態={queue_item.status}')
            print(f'  建議: 刪除隊列項或更新隊列狀態為ready')
        elif order.status == 'ready' and queue_item.status != 'ready':
            print(f'❌ 狀態不一致: 訂單狀態=ready, 隊列狀態={queue_item.status}')
            print(f'  建議: 更新隊列狀態為ready')
        elif order.status == 'preparing' and queue_item.status != 'preparing':
            print(f'❌ 狀態不一致: 訂單狀態=preparing, 隊列狀態={queue_item.status}')
            print(f'  建議: 更新隊列狀態為preparing')
        else:
            print(f'✅ 訂單與隊列狀態一致')
            
    except CoffeeQueue.DoesNotExist:
        print(f'⚠️ 訂單 #{order.id} 沒有對應的隊列項')
        if order.status in ['preparing', 'ready']:
            print(f'❌ 問題: {order.status}狀態的訂單應該有隊列項')
        
except OrderModel.DoesNotExist:
    print('❌ 訂單 #127 不存在')
except Exception as e:
    print(f'❌ 檢查訂單失敗: {e}')
    import traceback
    traceback.print_exc()

print('\n=== 檢查隊列中的 completed 訂單 ===')
try:
    # 查找隊列中所有 completed 訂單
    completed_in_queue = []
    all_queue_items = CoffeeQueue.objects.all()
    
    for queue_item in all_queue_items:
        order = queue_item.order
        if order.status == 'completed':
            completed_in_queue.append({
                'order_id': order.id,
                'queue_status': queue_item.status,
                'queue_position': queue_item.position
            })
    
    if completed_in_queue:
        print(f'❌ 發現 {len(completed_in_queue)} 個 completed 訂單仍在隊列中:')
        for item in completed_in_queue:
            print(f'  訂單 #{item["order_id"]}: 隊列狀態={item["queue_status"]}, 位置={item["queue_position"]}')
    else:
        print(f'✅ 隊列中沒有 completed 訂單')
        
except Exception as e:
    print(f'❌ 檢查隊列失敗: {e}')