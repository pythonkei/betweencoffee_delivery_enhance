# eshop/tests/final_verification_test.py

import os
import sys
from datetime import datetime, timedelta

import django

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../..'))
sys.path.insert(0, project_root)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'betweencoffee_delivery.settings')
django.setup()

import pytz

from eshop.models import CoffeeQueue, OrderModel
from eshop.time_utils import format_pickup_time_for_order
from eshop.views.queue_views import (
    process_completed_orders,
    process_preparing_queues,
    process_ready_orders,
    process_waiting_queues,
)


def final_verification_test():
    """最終驗證測試 - 確保所有功能正常工作"""
    
    print("=" * 70)
    print("最終驗證測試 - 咖啡店訂單管理系統")
    print(f"測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    test_results = {
        'passed': 0,
        'failed': 0,
        'warnings': 0
    }
    
    # 測試1：基本功能測試
    print("\n1. 基本功能測試:")
    
    try:
        # 檢查數據庫連接
        from django.db import connection
        connection.ensure_connection()
        print("   ✓ 數據庫連接正常")
        test_results['passed'] += 1
    except Exception as e:
        print(f"   ✗ 數據庫連接失敗: {str(e)}")
        test_results['failed'] += 1
    
    try:
        # 檢查模型加載
        order_count = OrderModel.objects.count()
        print(f"   ✓ 訂單模型加載正常 (總數: {order_count})")
        test_results['passed'] += 1
    except Exception as e:
        print(f"   ✗ 訂單模型加載失敗: {str(e)}")
        test_results['failed'] += 1
    
    # 測試2：統一時間格式化測試
    print("\n2. 統一時間格式化測試:")
    
    try:
        # 創建測試訂單
        test_order = OrderModel.objects.create(
            name="最終測試客戶",
            phone="99999999",
            total_price=38.00,
            items=[{
                'type': 'coffee',
                'id': 1,
                'name': '測試咖啡',
                'price': 38.0,
                'quantity': 1
            }],
            payment_status='paid',
            status='waiting',
            is_quick_order=True,
            pickup_time_choice='10'
        )
        
        # 測試時間格式化
        time_info = format_pickup_time_for_order(test_order)
        if time_info and 'text' in time_info:
            print(f"   ✓ 時間格式化正常: {time_info['text']}")
            test_results['passed'] += 1
        else:
            print("   ✗ 時間格式化失敗")
            test_results['failed'] += 1
        
        # 清理測試訂單
        test_order.delete()
        
    except Exception as e:
        print(f"   ✗ 時間格式化測試失敗: {str(e)}")
        test_results['failed'] += 1
    
    # 測試3：隊列處理函數測試
    print("\n3. 隊列處理函數測試:")
    
    hk_tz = pytz.timezone('Asia/Hong_Kong')
    now = datetime.now().astimezone(hk_tz)
    
    functions_to_test = [
        ("process_waiting_queues", process_waiting_queues),
        ("process_preparing_queues", process_preparing_queues),
        ("process_ready_orders", process_ready_orders),
        ("process_completed_orders", process_completed_orders),
    ]
    
    for func_name, func in functions_to_test:
        try:
            result = func(now, hk_tz)
            if isinstance(result, list):
                print(f"   ✓ {func_name}: 正常 (返回 {len(result)} 條記錄)")
                test_results['passed'] += 1
            else:
                print(f"   ✗ {func_name}: 返回類型錯誤")
                test_results['failed'] += 1
        except Exception as e:
            print(f"   ✗ {func_name}: 執行失敗 - {str(e)}")
            test_results['failed'] += 1
    
    # 測試4：數據庫索引檢查
    print("\n4. 數據庫索引檢查:")
    
    required_indexes = [
        ('eshop_ordermodel', 'idx_order_quick_status'),
        ('eshop_ordermodel', 'idx_order_payment_created'),
        ('eshop_ordermodel', 'idx_order_pickup_choice'),
        ('eshop_coffeequeue', 'idx_queue_status_position'),
        ('eshop_coffeequeue', 'idx_queue_est_start'),
    ]
    
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT tablename, indexname 
            FROM pg_indexes 
            WHERE schemaname = 'public' 
            AND tablename IN ('eshop_ordermodel', 'eshop_coffeequeue');
        """)
        
        existing_indexes = cursor.fetchall()
        existing_index_set = {f"{table}_{name}": True for table, name in existing_indexes}
        
        missing_count = 0
        for table, index in required_indexes:
            key = f"{table}_{index}"
            if key in existing_index_set:
                print(f"   ✓ {table}.{index}")
            else:
                print(f"   ✗ {table}.{index} (缺失)")
                missing_count += 1
        
        if missing_count == 0:
            print(f"   ✓ 所有必需索引都存在")
            test_results['passed'] += 1
        else:
            print(f"   ⚠️  缺少 {missing_count} 個索引")
            test_results['warnings'] += 1
    
    # 測試5：系統性能測試
    print("\n5. 系統性能測試:")
    
    import time
    
    performance_tests = [
        ("簡單查詢", lambda: OrderModel.objects.filter(payment_status='paid').count()),
        ("條件查詢", lambda: OrderModel.objects.filter(is_quick_order=True, status='waiting').count()),
        ("隊列查詢", lambda: CoffeeQueue.objects.filter(status='waiting').count()),
    ]
    
    all_passed = True
    for name, test_func in performance_tests:
        start_time = time.time()
        try:
            result = test_func()
            elapsed = (time.time() - start_time) * 1000
            if elapsed < 100:  # 100ms 為閾值
                print(f"   ✓ {name}: {result} 條記錄，{elapsed:.2f}ms")
            else:
                print(f"   ⚠️  {name}: {result} 條記錄，{elapsed:.2f}ms (較慢)")
                all_passed = False
        except Exception as e:
            print(f"   ✗ {name}: 失敗 - {str(e)}")
            all_passed = False
    
    if all_passed:
        test_results['passed'] += 1
    else:
        test_results['warnings'] += 1
    
    # 測試結果總結
    print("\n" + "=" * 70)
    print("測試結果總結:")
    print("=" * 70)
    
    print(f"\n✅ 通過: {test_results['passed']} 項")
    print(f"❌ 失敗: {test_results['failed']} 項")
    print(f"⚠️  警告: {test_results['warnings']} 項")
    
    if test_results['failed'] == 0:
        if test_results['warnings'] == 0:
            print("\n🎉 所有測試通過！系統準備就緒。")
        else:
            print("\n👍 基本功能正常，但有少量警告需要關注。")
    else:
        print("\n🚨 發現失敗的測試，需要修復。")
    
    print("\n📋 建議:")
    if test_results['failed'] > 0:
        print("   1. 修復失敗的測試")
    if test_results['warnings'] > 0:
        print("   2. 檢查警告項目")
    
    print("   3. 運行完整的功能測試套件")
    print("   4. 進行壓力測試")
    print("   5. 準備生產環境部署")
    
    print("\n" + "=" * 70)
    print("最終驗證測試完成")
    print("=" * 70)
    
    return test_results

if __name__ == '__main__':
    final_verification_test()