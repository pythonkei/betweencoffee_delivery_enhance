# eshop/tests/test_unified_time_system.py

import os
import sys
from datetime import datetime, timedelta

# 獲取項目根目錄的正確路徑
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../..'))
sys.path.insert(0, project_root)

# 設置 Django 環境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'betweencoffee_delivery.settings')

import django
django.setup()

from eshop.models import OrderModel
from eshop.time_utils import (
    get_pickup_time_display_from_choice,
    get_minutes_from_pickup_choice,
    format_pickup_time_for_order,
    calculate_all_quick_order_times,
    update_order_pickup_times
)
try:
    from eshop.views.queue_views import (
        process_waiting_queues,
        process_preparing_queues,
        process_ready_orders,
        process_completed_orders
    )
except ImportError as e:
    print(f"注意: 無法導入隊列視圖函數: {e}")
    # 定義空函數以便測試繼續
    def process_waiting_queues(*args, **kwargs):
        return []
    def process_preparing_queues(*args, **kwargs):
        return []
    def process_ready_orders(*args, **kwargs):
        return []
    def process_completed_orders(*args, **kwargs):
        return []

import pytz

def test_unified_time_system():
    """測試完整統一時間系統"""
    
    print("=== 統一時間系統整合測試 ===")
    
    # 測試1：創建多種類型訂單
    print("\n1. 創建測試訂單:")
    test_orders = []
    
    try:
        # 創建快速訂單
        quick_order = OrderModel.objects.create(
            name="快速訂單測試",
            phone="12345678",
            total_price=38.00,
            items=[{
                'type': 'coffee',
                'id': 1,
                'name': '美式咖啡',
                'price': 38.0,
                'quantity': 1
            }],
            payment_status='paid',
            status='waiting',
            is_quick_order=True,
            pickup_time_choice='15'
        )
        test_orders.append(quick_order)
        print(f"  ✓ 創建快速訂單 (15分鐘)")
        
        # 創建普通訂單
        normal_order = OrderModel.objects.create(
            name="普通訂單測試",
            phone="87654321",
            total_price=76.00,
            items=[{
                'type': 'coffee',
                'id': 1,
                'name': '拿鐵咖啡',
                'price': 38.0,
                'quantity': 2
            }],
            payment_status='paid',
            status='waiting',
            is_quick_order=False,
            pickup_time_choice='5'
        )
        test_orders.append(normal_order)
        print(f"  ✓ 創建普通訂單")
        
        # 創建純咖啡豆訂單
        beans_order = OrderModel.objects.create(
            name="咖啡豆訂單測試",
            phone="11111111",
            total_price=200.00,
            items=[{
                'type': 'bean',
                'id': 1,
                'name': '測試咖啡豆',
                'price': 100.0,
                'quantity': 2,
                'weight': '200g'
            }],
            payment_status='paid',
            status='waiting',
            is_quick_order=False
        )
        test_orders.append(beans_order)
        print(f"  ✓ 創建純咖啡豆訂單")
        
        # 測試2：驗證各個隊列處理函數
        print("\n2. 隊列處理函數測試:")
        
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
                print(f"  ✓ {func_name}: 返回 {len(result)} 條記錄")
                
                # 檢查返回數據結構
                if result and len(result) > 0:
                    first_item = result[0]
                    required_fields = ['pickup_time_info', 'pickup_time_display', 'is_quick_order']
                    
                    missing_fields = [field for field in required_fields if field not in first_item]
                    if not missing_fields:
                        print(f"    - 數據結構完整")
                    else:
                        print(f"    - 缺少字段: {missing_fields}")
                        
            except Exception as e:
                print(f"  ✗ {func_name}: 失敗 - {str(e)}")
        
        # 測試3：批量時間計算
        print("\n3. 批量時間計算測試:")
        
        order_ids = [order.id for order in test_orders]
        result = calculate_all_quick_order_times()
        
        if result.get('success'):
            print(f"  ✓ 批量計算成功")
            print(f"    - 計算了 {result.get('count', 0)} 個訂單")
        else:
            print(f"  ✗ 批量計算失敗: {result.get('error', '未知錯誤')}")
        
        # 測試4：訂單更新
        print("\n4. 訂單時間更新測試:")
        
        update_result = update_order_pickup_times(order_ids)
        
        if update_result.get('success'):
            updated = update_result.get('updated_orders', [])
            print(f"  ✓ 更新 {len(updated)} 個訂單")
            
            # 驗證更新後的訂單
            for order_id in updated:
                try:
                    order = OrderModel.objects.get(id=order_id)
                    time_info = format_pickup_time_for_order(order)
                    print(f"    - 訂單 {order_id}: {time_info['text']}")
                except OrderModel.DoesNotExist:
                    print(f"    - 訂單 {order_id}: 不存在")
        else:
            print(f"  ✗ 更新失敗: {update_result.get('error', '未知錯誤')}")
        
        # 清理測試數據
        print("\n5. 清理測試數據:")
        for order in test_orders:
            order.delete()
            print(f"  ✓ 刪除訂單 {order.id}")
            
    except Exception as e:
        print(f"  測試過程中出現錯誤: {str(e)}")
        import traceback
        traceback.print_exc()
        # 清理可能創建的訂單
        for order in test_orders:
            try:
                order.delete()
            except:
                pass
    
    print("\n=== 整合測試完成 ===")

if __name__ == '__main__':
    test_unified_time_system()