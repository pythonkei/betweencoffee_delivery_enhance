# eshop/tests/test_pickup_time_formatting.py
import os
import django
import sys

# 設置Django環境
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'betweencoffee_delivery.settings')
django.setup()

from eshop.time_utils import (
    get_pickup_time_display_from_choice,
    get_minutes_from_pickup_choice,
    format_pickup_time_for_order
)
from eshop.models import OrderModel
from django.utils import timezone
import pytz

def test_pickup_time_formatting():
    """測試取貨時間格式化函數"""
    
    print("=== 測試取貨時間格式化 ===")
    
    # 測試1：基本轉換
    print("\n1. 測試基本轉換:")
    test_cases = [
        ('5', '5分鐘後'),
        ('10', '10分鐘後'),
        ('15', '15分鐘後'),
        ('20', '20分鐘後'),
        ('30', '30分鐘後'),
        ('', '5分鐘後'),  # 空值
        ('invalid', '5分鐘後'),  # 無效值
    ]
    
    for input_val, expected in test_cases:
        result = get_pickup_time_display_from_choice(input_val)
        status = "✓" if result == expected else "✗"
        print(f"  {status} '{input_val}' -> '{result}' (期望: '{expected}')")
    
    # 測試2：提取分鐘數
    print("\n2. 測試提取分鐘數:")
    test_cases = [
        ('5', 5),
        ('10', 10),
        ('5 分鐘後', 5),
        ('15分鐘後', 15),
        ('', 5),  # 空值
        ('invalid', 5),  # 無效值
    ]
    
    for input_val, expected in test_cases:
        result = get_minutes_from_pickup_choice(input_val)
        status = "✓" if result == expected else "✗"
        print(f"  {status} '{input_val}' -> {result} (期望: {expected})")
    
    # 測試3：創建測試訂單
    print("\n3. 測試訂單格式化:")
    
    try:
        # 創建測試訂單
        order = OrderModel.objects.create(
            name="測試客戶",
            phone="12345678",
            total_price=38.00,
            items=[{
                'type': 'coffee',
                'id': 1,
                'name': '測試咖啡',
                'price': 38.0,
                'quantity': 1
            }],
            payment_status='paid',
            status='waiting'
        )
        
        # 測試純咖啡豆訂單
        order.is_quick_order = False
        beans_only_order = order
        beans_only_order.items = [{
            'type': 'bean',
            'id': 1,
            'name': '測試咖啡豆',
            'price': 100.0,
            'quantity': 1,
            'weight': '200g'
        }]
        
        result = format_pickup_time_for_order(beans_only_order)
        print(f"  純咖啡豆訂單: {result['text'] if result else 'N/A'}")
        
        # 測試快速訂單
        order.is_quick_order = True
        order.pickup_time_choice = '10'
        order.items = [{
            'type': 'coffee',
            'id': 1,
            'name': '測試咖啡',
            'price': 38.0,
            'quantity': 1
        }]
        
        result = format_pickup_time_for_order(order)
        print(f"  快速訂單(10分鐘): {result['text'] if result else 'N/A'}")
        
        # 清理測試數據
        order.delete()
        
    except Exception as e:
        print(f"  測試失敗: {str(e)}")
    
    print("\n=== 測試完成 ===")

if __name__ == '__main__':
    test_pickup_time_formatting()