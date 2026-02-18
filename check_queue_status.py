#!/usr/bin/env python
"""
隊列狀態檢查腳本
用於檢查隊列完整性問題
"""

import os
import sys
import django

# 設置Django環境
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'betweencoffee_delivery.settings')

try:
    django.setup()
    print("✅ Django設置成功")
except Exception as e:
    print(f"❌ Django設置失敗: {e}")
    sys.exit(1)

# 導入模型
try:
    from eshop.models import CoffeeQueue, OrderModel
    from eshop.queue_manager import CoffeeQueueManager
    print("✅ 模型導入成功")
except Exception as e:
    print(f"❌ 模型導入失敗: {e}")
    sys.exit(1)

def check_queue_integrity():
    """檢查隊列完整性"""
    print("\n" + "="*60)
    print("隊列完整性檢查")
    print("="*60)
    
    queue_manager = CoffeeQueueManager()
    
    # 1. 檢查隊列完整性
    print("\n1. 隊列完整性檢查:")
    integrity = queue_manager.verify_queue_integrity()
    
    if integrity['has_issues']:
        print(f"   ❌ 發現 {len(integrity['issues'])} 個問題:")
        for issue in integrity['issues']:
            print(f"      - {issue}")
    else:
        print("   ✅ 隊列完整性正常")
    
    print(f"\n   隊列統計:")
    print(f"     等待中: {integrity['waiting_count']}")
    print(f"     製作中: {integrity['preparing_count']}")
    print(f"     已就緒: {integrity['ready_count']}")
    
    # 2. 檢查ready狀態訂單是否有隊列位置
    print("\n2. 檢查ready狀態訂單是否有隊列位置:")
    ready_with_position = CoffeeQueue.objects.filter(status='ready', position__gt=0)
    if ready_with_position.exists():
        print(f"   ❌ 發現 {ready_with_position.count()} 個ready訂單有隊列位置:")
        for queue in ready_with_position:
            print(f"      - 訂單 #{queue.order.id} - 位置: {queue.position}")
    else:
        print("   ✅ 所有ready訂單都沒有隊列位置")
    
    # 3. 檢查waiting訂單位置是否連續
    print("\n3. 檢查waiting訂單位置是否連續:")
    waiting_queues = CoffeeQueue.objects.filter(status='waiting').order_by('position')
    
    if waiting_queues.exists():
        positions = [q.position for q in waiting_queues]
        expected = list(range(1, len(positions) + 1))
        
        if positions == expected:
            print(f"   ✅ waiting訂單位置連續正常 (共{len(positions)}個)")
        else:
            print(f"   ❌ waiting訂單位置不連續!")
            print(f"      實際位置: {positions}")
            print(f"      期望位置: {expected}")
            
            # 顯示詳細信息
            print(f"\n      詳細檢查:")
            expected_pos = 1
            for queue in waiting_queues:
                if queue.position != expected_pos:
                    print(f"        訂單 #{queue.order.id}: 位置 {queue.position} (期望: {expected_pos})")
                expected_pos += 1
    else:
        print("   ℹ️  沒有等待中的訂單")
    
    # 4. 檢查隊列與訂單狀態同步
    print("\n4. 檢查隊列與訂單狀態同步:")
    issues_found = False
    
    # 檢查所有隊列項目
    all_queues = CoffeeQueue.objects.all()
    for queue in all_queues:
        order = queue.order
        
        # 檢查狀態一致性
        if queue.status == 'waiting' and order.status != 'waiting':
            print(f"   ❌ 訂單 #{order.id}: 隊列狀態='{queue.status}', 訂單狀態='{order.status}'")
            issues_found = True
        
        if queue.status == 'preparing' and order.status != 'preparing':
            print(f"   ❌ 訂單 #{order.id}: 隊列狀態='{queue.status}', 訂單狀態='{order.status}'")
            issues_found = True
        
        if queue.status == 'ready' and order.status != 'ready':
            print(f"   ❌ 訂單 #{order.id}: 隊列狀態='{queue.status}', 訂單狀態='{order.status}'")
            issues_found = True
    
    if not issues_found:
        print("   ✅ 隊列與訂單狀態同步正常")
    
    # 5. 檢查快速訂單優先級
    print("\n5. 檢查快速訂單優先級:")
    waiting_queues = CoffeeQueue.objects.filter(status='waiting').order_by('position')
    
    quick_orders_in_waiting = []
    normal_orders_in_waiting = []
    
    for queue in waiting_queues:
        order = queue.order
        if order.order_type == 'quick':
            quick_orders_in_waiting.append((queue.position, order.id))
        else:
            normal_orders_in_waiting.append((queue.position, order.id))
    
    print(f"   等待中的快速訂單: {len(quick_orders_in_waiting)}個")
    print(f"   等待中的普通訂單: {len(normal_orders_in_waiting)}個")
    
    # 檢查快速訂單是否都在普通訂單前面
    if quick_orders_in_waiting and normal_orders_in_waiting:
        last_quick_position = max(pos for pos, _ in quick_orders_in_waiting)
        first_normal_position = min(pos for pos, _ in normal_orders_in_waiting)
        
        if last_quick_position < first_normal_position:
            print("   ✅ 快速訂單優先級正確（都在普通訂單前面）")
        else:
            print(f"   ⚠️  快速訂單優先級可能不正確")
            print(f"      最後一個快速訂單位置: {last_quick_position}")
            print(f"      第一個普通訂單位置: {first_normal_position}")
    
    return integrity['has_issues']

def fix_queue_issues():
    """修復隊列問題"""
    print("\n" + "="*60)
    print("修復隊列問題")
    print("="*60)
    
    queue_manager = CoffeeQueueManager()
    
    # 1. 修復隊列位置
    print("\n1. 修復隊列位置...")
    try:
        success = queue_manager.fix_queue_positions()
        if success:
            print("   ✅ 隊列位置修復成功")
        else:
            print("   ❌ 隊列位置修復失敗")
    except Exception as e:
        print(f"   ❌ 修復隊列位置時出錯: {e}")
    
    # 2. 同步訂單狀態
    print("\n2. 同步訂單狀態...")
    try:
        success = queue_manager.sync_order_queue_status()
        if success:
            print("   ✅ 訂單狀態同步成功")
        else:
            print("   ❌ 訂單狀態同步失敗")
    except Exception as e:
        print(f"   ❌ 同步訂單狀態時出錯: {e}")
    
    # 3. 重新計算時間
    print("\n3. 重新計算隊列時間...")
    try:
        success = queue_manager.update_estimated_times()
        if success:
            print("   ✅ 隊列時間重新計算成功")
        else:
            print("   ❌ 隊列時間重新計算失敗")
    except Exception as e:
        print(f"   ❌ 重新計算隊列時間時出錯: {e}")
    
    print("\n" + "="*60)
    print("修復完成")
    print("="*60)

def main():
    """主函數"""
    print("隊列狀態檢查工具")
    print("版本: 1.0.0")
    print("="*60)
    
    # 檢查隊列完整性
    has_issues = check_queue_integrity()
    
    if has_issues:
        print("\n" + "="*60)
        print("發現隊列問題，開始自動修復...")
        fix_queue_issues()
        print("\n修復完成，重新檢查隊列狀態...")
        check_queue_integrity()
    else:
        print("\n" + "="*60)
        print("✅ 隊列狀態正常，無需修復")
    
    print("\n檢查完成！")

if __name__ == "__main__":
    main()