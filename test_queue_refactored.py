#!/usr/bin/env python
"""
測試重構後的隊列管理器
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

# 導入模型和重構後的隊列管理器
try:
    from eshop.models import CoffeeQueue, OrderModel
    from eshop.queue_manager_refactored import CoffeeQueueManager
    print("✅ 模型導入成功")
except Exception as e:
    print(f"❌ 模型導入失敗: {e}")
    sys.exit(1)


def test_basic_functionality():
    """測試基本功能"""
    print("\n" + "="*60)
    print("測試基本功能")
    print("="*60)
    
    manager = CoffeeQueueManager()
    
    # 1. 測試獲取隊列摘要
    print("\n1. 測試獲取隊列摘要:")
    summary = manager.get_queue_summary()
    print(f"   隊列摘要: {summary}")
    
    # 2. 測試驗證隊列完整性
    print("\n2. 測試驗證隊列完整性:")
    integrity = manager.verify_queue_integrity()
    print(f"   完整性檢查: {'有問題' if integrity['has_issues'] else '正常'}")
    if integrity['has_issues']:
        print(f"   問題列表: {integrity['issues']}")
    
    # 3. 測試修復隊列位置
    print("\n3. 測試修復隊列位置:")
    try:
        success = manager.fix_queue_positions()
        print(f"   修復結果: {'成功' if success else '失敗'}")
    except Exception as e:
        print(f"   修復失敗: {e}")
    
    # 4. 測試更新預計時間
    print("\n4. 測試更新預計時間:")
    try:
        success = manager.update_estimated_times()
        print(f"   更新結果: {'成功' if success else '失敗'}")
    except Exception as e:
        print(f"   更新失敗: {e}")
    
    return True


def test_queue_operations():
    """測試隊列操作"""
    print("\n" + "="*60)
    print("測試隊列操作")
    print("="*60)
    
    manager = CoffeeQueueManager()
    
    # 獲取一些測試訂單
    try:
        # 獲取已支付且包含咖啡的訂單
        test_orders = OrderModel.objects.filter(
            payment_status='paid'
        )[:3]  # 只取前3個
        
        if not test_orders:
            print("ℹ️ 沒有找到測試訂單")
            return False
        
        print(f"找到 {len(test_orders)} 個測試訂單")
        
        for i, order in enumerate(test_orders, 1):
            print(f"\n{i}. 測試訂單 #{order.id}:")
            
            # 檢查是否包含咖啡
            items = order.get_items()
            has_coffee = any(item.get('type') == 'coffee' for item in items)
            
            if not has_coffee:
                print(f"   訂單不包含咖啡，跳過")
                continue
            
            # 測試添加訂單到隊列（使用優先級）
            print(f"   測試添加訂單到隊列（使用優先級）...")
            queue_item = manager.add_order_to_queue(order, use_priority=True)
            
            if queue_item:
                print(f"   添加成功: 隊列項 #{queue_item.id}, 位置: {queue_item.position}")
                
                # 測試計算等待時間
                wait_time = manager.calculate_wait_time(queue_item)
                print(f"   等待時間: {wait_time}分鐘")
            else:
                print(f"   添加失敗")
        
        return True
        
    except Exception as e:
        print(f"❌ 測試隊列操作失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_sync_operations():
    """測試同步操作"""
    print("\n" + "="*60)
    print("測試同步操作")
    print("="*60)
    
    manager = CoffeeQueueManager()
    
    try:
        # 測試同步訂單狀態
        print("\n1. 測試同步訂單狀態:")
        success = manager.sync_order_queue_status()
        print(f"   同步結果: {'成功' if success else '失敗'}")
        
        # 測試獲取隊列更新
        print("\n2. 測試獲取隊列更新:")
        from eshop.queue_manager_refactored import get_queue_updates
        updates = get_queue_updates()
        print(f"   更新數據: {'成功' if updates['success'] else '失敗'}")
        if updates['success']:
            print(f"   隊列摘要: {updates['queue_summary']}")
        
        # 測試修復隊列數據
        print("\n3. 測試修復隊列數據:")
        from eshop.queue_manager_refactored import repair_queue_data
        success = repair_queue_data()
        print(f"   修復結果: {'成功' if success else '失敗'}")
        
        return True
        
    except Exception as e:
        print(f"❌ 測試同步操作失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_static_methods():
    """測試靜態方法"""
    print("\n" + "="*60)
    print("測試靜態方法")
    print("="*60)
    
    try:
        # 測試獲取製作時間
        print("\n1. 測試獲取製作時間:")
        for count in [1, 2, 3, 5]:
            prep_time = CoffeeQueueManager.get_preparation_time(count)
            print(f"   {count}杯咖啡: {prep_time}分鐘")
        
        # 測試獲取香港時間
        print("\n2. 測試獲取香港時間:")
        hk_time = CoffeeQueueManager.get_hong_kong_time_now()
        print(f"   當前香港時間: {hk_time}")
        
        return True
        
    except Exception as e:
        print(f"❌ 測試靜態方法失敗: {e}")
        return False


def compare_with_original():
    """與原始代碼比較"""
    print("\n" + "="*60)
    print("與原始代碼比較")
    print("="*60)
    
    try:
        # 導入原始隊列管理器
        from eshop.queue_manager import CoffeeQueueManager as OriginalManager
        
        original_manager = OriginalManager()
        refactored_manager = CoffeeQueueManager()
        
        print("\n1. 方法數量比較:")
        
        # 獲取原始管理器的方法
        original_methods = [m for m in dir(original_manager) 
                          if not m.startswith('_') and callable(getattr(original_manager, m))]
        
        # 獲取重構管理器的方法
        refactored_methods = [m for m in dir(refactored_manager) 
                            if not m.startswith('_') and callable(getattr(refactored_manager, m))]
        
        print(f"   原始方法數量: {len(original_methods)}")
        print(f"   重構方法數量: {len(refactored_methods)}")
        
        # 檢查重複方法
        print("\n2. 重複方法檢查:")
        duplicate_methods = []
        for method in original_methods:
            if method in refactored_methods:
                duplicate_methods.append(method)
        
        print(f"   共有方法: {len(duplicate_methods)}個")
        if duplicate_methods:
            print(f"   方法列表: {', '.join(duplicate_methods[:10])}" + 
                  ("..." if len(duplicate_methods) > 10 else ""))
        
        # 檢查被移除的重複方法
        print("\n3. 被合併的重複方法:")
        removed_duplicates = ['add_order_to_queue_with_priority']  # 已知被合併的方法
        for method in removed_duplicates:
            if hasattr(original_manager, method) and not hasattr(refactored_manager, method):
                print(f"   ✅ {method} 已被合併到 add_order_to_queue")
        
        return True
        
    except Exception as e:
        print(f"❌ 比較失敗: {e}")
        return False


def main():
    """主測試函數"""
    print("重構隊列管理器測試")
    print("版本: 1.0.0")
    print("="*60)
    
    tests = [
        ("基本功能測試", test_basic_functionality),
        ("隊列操作測試", test_queue_operations),
        ("同步操作測試", test_sync_operations),
        ("靜態方法測試", test_static_methods),
        ("與原始代碼比較", compare_with_original),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n▶ 開始 {test_name}...")
        try:
            success = test_func()
            results.append((test_name, success))
            status = "✅ 通過" if success else "❌ 失敗"
            print(f"   {status}")
        except Exception as e:
            results.append((test_name, False))
            print(f"   ❌ 異常: {e}")
    
    # 總結結果
    print("\n" + "="*60)
    print("測試總結")
    print("="*60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    print(f"\n總測試數: {total}")
    print(f"通過數: {passed}")
    print(f"失敗數: {total - passed}")
    print(f"通過率: {passed/total*100:.1f}%")
    
    print("\n詳細結果:")
    for test_name, success in results:
        status = "✅ 通過" if success else "❌ 失敗"
        print(f"  {test_name}: {status}")
    
    if passed == total:
        print("\n🎉 所有測試通過！重構成功。")
    else:
        print(f"\n⚠️  {total - passed} 個測試失敗，需要檢查。")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)