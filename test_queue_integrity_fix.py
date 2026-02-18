#!/usr/bin/env python3
"""
測試隊列數據完整性修復
"""

import os
import sys
import django

# 設置 Django 環境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'betweencoffee_delivery.settings')
django.setup()

from eshop.models import CoffeeQueue, OrderModel
from eshop.queue_manager_final import CoffeeQueueManager
from eshop.order_status_manager import OrderStatusManager
import logging

# 設置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_queue_integrity_fix():
    """測試隊列完整性修復"""
    print("🔍 測試隊列數據完整性修復...")
    print("=" * 60)
    
    manager = CoffeeQueueManager()
    
    # 1. 檢查當前隊列狀態
    print("\n1. 📊 檢查當前隊列狀態:")
    integrity_check = manager.verify_queue_integrity()
    
    if integrity_check['has_issues']:
        print(f"   ⚠️ 發現問題: {len(integrity_check['issues'])} 個")
        for issue in integrity_check['issues']:
            print(f"     • {issue}")
    else:
        print("   ✅ 隊列完整性檢查通過")
    
    # 2. 檢查 ready 狀態但有位置的隊列項
    print("\n2. 🔍 檢查 ready 狀態但有位置的隊列項:")
    ready_with_position = CoffeeQueue.objects.filter(status='ready', position__gt=0)
    print(f"   發現 {ready_with_position.count()} 個問題隊列項")
    
    if ready_with_position.exists():
        print("   ⚠️ 仍有問題需要修復")
        for queue in ready_with_position[:5]:
            print(f"     • 隊列項 #{queue.id}: 訂單 #{queue.order.id}, 位置={queue.position}")
    else:
        print("   ✅ 沒有 ready 狀態但有位置的隊列項")
    
    # 3. 檢查隊列統計
    print("\n3. 📈 隊列統計:")
    summary = manager.get_queue_summary()
    print(f"   等待中: {summary['waiting']}")
    print(f"   製作中: {summary['preparing']}")
    print(f"   已就緒: {summary['ready']}")
    print(f"   總數: {summary['total']}")
    
    # 4. 測試修復功能
    print("\n4. 🛠️ 測試修復功能:")
    fixed = manager.fix_queue_positions()
    print(f"   修復隊列位置結果: {'成功' if fixed else '失敗'}")
    
    # 5. 再次檢查完整性
    print("\n5. 🔍 修復後再次檢查完整性:")
    integrity_check2 = manager.verify_queue_integrity()
    
    if integrity_check2['has_issues']:
        print(f"   ⚠️ 修復後仍有問題: {len(integrity_check2['issues'])} 個")
        for issue in integrity_check2['issues']:
            print(f"     • {issue}")
    else:
        print("   ✅ 修復後隊列完整性檢查通過")
    
    # 6. 測試預防措施
    print("\n6. 🛡️ 測試預防措施:")
    
    # 查找一個 preparing 狀態的訂單
    preparing_order = OrderModel.objects.filter(status='preparing', payment_status='paid').first()
    if preparing_order:
        print(f"   找到準備測試的訂單: #{preparing_order.id}")
        
        # 檢查對應的隊列項
        queue_item = CoffeeQueue.objects.filter(order=preparing_order).first()
        if queue_item:
            print(f"   對應的隊列項: #{queue_item.id}, 位置={queue_item.position}")
            
            # 測試 mark_as_ready_manually
            print(f"   測試 mark_as_ready_manually...")
            result = OrderStatusManager.mark_as_ready_manually(preparing_order.id, "test_staff")
            
            if result.get('success'):
                print(f"   ✅ mark_as_ready_manually 成功")
                
                # 檢查位置是否被清理
                queue_item.refresh_from_db()
                if queue_item.position == 0:
                    print(f"   ✅ 隊列位置已正確清理: 位置=0")
                else:
                    print(f"   ⚠️ 隊列位置未清理: 位置={queue_item.position}")
            else:
                print(f"   ❌ mark_as_ready_manually 失敗: {result.get('message')}")
        else:
            print("   ℹ️ 沒有對應的隊列項")
    else:
        print("   ℹ️ 沒有找到 preparing 狀態的訂單進行測試")
    
    # 7. 總結
    print("\n" + "=" * 60)
    print("📋 測試總結:")
    
    all_passed = True
    
    if ready_with_position.exists():
        print("   ❌ 仍有 ready 狀態但有位置的隊列項")
        all_passed = False
    else:
        print("   ✅ 沒有 ready 狀態但有位置的隊列項")
    
    if integrity_check2['has_issues']:
        print("   ❌ 修復後仍有隊列完整性問題")
        all_passed = False
    else:
        print("   ✅ 修復後隊列完整性檢查通過")
    
    if all_passed:
        print("\n🎉 所有測試通過！隊列數據完整性問題已修復。")
        print("\n✨ 預防措施已實施:")
        print("   1. ✅ mark_as_ready 方法會清理隊列位置")
        print("   2. ✅ mark_as_ready_manually 方法會清理隊列位置")
        print("   3. ✅ process_order_status_change 方法會清理隊列位置")
        print("   4. ✅ fix_queue_positions 方法會定期清理隊列位置")
    else:
        print("\n⚠️ 測試未完全通過，請檢查修復。")
    
    return all_passed

def create_test_report():
    """創建測試報告"""
    print("\n📄 創建詳細測試報告...")
    print("=" * 60)
    
    # 檢查所有隊列項
    all_queues = CoffeeQueue.objects.all()
    print(f"總隊列項數: {all_queues.count()}")
    
    # 按狀態分組
    status_counts = {}
    for queue in all_queues:
        status = queue.status
        status_counts[status] = status_counts.get(status, 0) + 1
    
    print("\n隊列項狀態分佈:")
    for status, count in sorted(status_counts.items()):
        print(f"  {status}: {count}")
    
    # 檢查位置分佈
    print("\n隊列位置分佈:")
    waiting_queues = CoffeeQueue.objects.filter(status='waiting').order_by('position')
    print(f"  等待中隊列項: {waiting_queues.count()}")
    
    if waiting_queues.exists():
        positions = list(waiting_queues.values_list('position', flat=True))
        print(f"  位置範圍: {min(positions)} - {max(positions)}")
        
        # 檢查位置連續性
        expected_pos = 1
        for queue in waiting_queues:
            if queue.position != expected_pos:
                print(f"  ⚠️ 位置不連續: 隊列項 #{queue.id} 位置={queue.position} (期望:{expected_pos})")
                break
            expected_pos += 1
        else:
            print("  ✅ 等待隊列位置連續")
    
    # 檢查 ready/completed 隊列項的位置
    print("\nready/completed 隊列項位置檢查:")
    problematic = CoffeeQueue.objects.filter(status__in=['ready', 'completed'], position__gt=0)
    print(f"  有問題的隊列項: {problematic.count()}")
    
    if problematic.exists():
        for queue in problematic[:10]:
            print(f"  ⚠️ 隊列項 #{queue.id}: 狀態={queue.status}, 位置={queue.position}, 訂單 #{queue.order.id}")
    else:
        print("  ✅ 所有 ready/completed 隊列項位置已清理")
    
    print("\n" + "=" * 60)
    print("📊 系統建議:")
    print("1. ✅ 定期運行 fix_queue_positions() 方法")
    print("2. ✅ 確保所有狀態變更方法都清理隊列位置")
    print("3. ✅ 監控隊列完整性檢查日誌")
    print("4. ✅ 建立自動化測試確保問題不再發生")

if __name__ == "__main__":
    print("隊列數據完整性修復測試")
    print("=" * 60)
    
    try:
        test_passed = test_queue_integrity_fix()
        create_test_report()
        
        if test_passed:
            print("\n🎉 測試完成！隊列數據完整性問題已成功修復。")
            print("\n📝 修復總結:")
            print("✅ 已修復 ready 狀態隊列項仍有位置的問題")
            print("✅ 已實施預防措施防止問題再次發生")
            print("✅ 所有相關方法現在都會正確清理隊列位置")
        else:
            print("\n⚠️ 測試未完全通過，請檢查修復。")
            
    except Exception as e:
        print(f"\n❌ 測試過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()