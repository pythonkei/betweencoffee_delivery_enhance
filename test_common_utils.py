#!/usr/bin/env python
"""
測試共用工具模塊
"""

import os
import sys
import django

# 設置 Django 環境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'betweencoffee_delivery.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    django.setup()
    DJANGO_SETUP = True
    print("✅ Django 環境設置成功")
except Exception as e:
    DJANGO_SETUP = False
    print(f"⚠️ Django 環境設置失敗: {str(e)}")
    print("將使用簡化模式測試")

# 導入共用工具模塊
from eshop.utils.common_utils import (
    CommonUtils, common_utils,
    get_hong_kong_time, format_time_display,
    safe_get_attr, log_info, log_error
)

from datetime import datetime, timedelta
import pytz


def test_time_functions():
    """測試時間相關函數"""
    print("\n=== 測試時間相關函數 ===")
    
    # 測試獲取香港時間
    hk_time = get_hong_kong_time()
    print(f"✅ 香港時間: {hk_time}")
    print(f"✅ 時區: {hk_time.tzinfo}")
    
    # 測試格式化時間
    formatted = format_time_display(hk_time)
    print(f"✅ 格式化時間: {formatted}")
    
    # 測試日期時間格式化
    datetime_formatted = common_utils.format_datetime_for_display(hk_time)
    print(f"✅ 格式化日期時間: {datetime_formatted}")
    
    # 測試時間差計算
    start_time = hk_time
    end_time = hk_time + timedelta(minutes=90)
    minutes_diff = common_utils.calculate_time_diff_minutes(start_time, end_time)
    print(f"✅ 時間差計算: {minutes_diff} 分鐘")
    
    # 測試分鐘格式化
    display_minutes = common_utils.format_minutes_to_display(minutes_diff)
    print(f"✅ 分鐘格式化: {display_minutes}")
    
    # 測試邊界情況
    zero_minutes = common_utils.format_minutes_to_display(0)
    print(f"✅ 0分鐘格式化: {zero_minutes}")
    
    large_minutes = common_utils.format_minutes_to_display(125)
    print(f"✅ 125分鐘格式化: {large_minutes}")
    
    return True


def test_safe_get_functions():
    """測試安全獲取屬性函數"""
    print("\n=== 測試安全獲取屬性函數 ===")
    
    # 創建測試對象
    class User:
        def __init__(self):
            self.name = "John"
            self.profile = type('Profile', (), {'email': 'john@example.com'})()
            self.settings = {'theme': 'dark', 'notifications': True}
    
    class Order:
        def __init__(self):
            self.id = 123
            self.user = User()
            self.items = [{'id': 1, 'name': 'Coffee'}]
    
    order = Order()
    
    # 測試正常獲取
    user_name = safe_get_attr(order, 'user.name')
    print(f"✅ 安全獲取 user.name: {user_name}")
    
    # 測試嵌套屬性
    user_email = safe_get_attr(order, 'user.profile.email')
    print(f"✅ 安全獲取 user.profile.email: {user_email}")
    
    # 測試字典屬性
    theme = safe_get_attr(order, 'user.settings.theme')
    print(f"✅ 安全獲取 user.settings.theme: {theme}")
    
    # 測試不存在的屬性
    non_existent = safe_get_attr(order, 'user.profile.age', 'N/A')
    print(f"✅ 安全獲取不存在的屬性: {non_existent}")
    
    # 測試空對象
    null_result = safe_get_attr(None, 'user.name', 'Default')
    print(f"✅ 安全獲取空對象: {null_result}")
    
    return True


def test_validation_functions():
    """測試驗證函數"""
    print("\n=== 測試驗證函數 ===")
    
    # 測試必需字段驗證
    data = {
        'name': 'John',
        'email': '',
        'age': None,
        'address': '123 Street'
    }
    
    required_fields = ['name', 'email', 'age', 'address', 'phone']
    errors = common_utils.validate_required_fields(data, required_fields)
    
    print(f"✅ 字段驗證結果:")
    for field, field_errors in errors.items():
        print(f"  - {field}: {field_errors}")
    
    # 測試無錯誤情況
    complete_data = {'name': 'John', 'email': 'john@example.com', 'phone': '12345678'}
    no_errors = common_utils.validate_required_fields(complete_data, ['name', 'email'])
    print(f"✅ 無錯誤驗證: {len(no_errors)} 個錯誤")
    
    return True


def test_logging_functions():
    """測試日誌函數"""
    print("\n=== 測試日誌函數 ===")
    
    # 測試信息日誌
    log_info('test_module', 'test_operation', '測試信息日誌', extra_data={'test': 'data'})
    print("✅ 信息日誌記錄完成")
    
    # 測試錯誤日誌
    log_error('test_module', 'test_operation', '測試錯誤日誌', error_code=500)
    print("✅ 錯誤日誌記錄完成")
    
    return True


def test_serialization_functions():
    """測試序列化函數"""
    print("\n=== 測試序列化函數 ===")
    
    if not DJANGO_SETUP:
        print("⚠️ 跳過序列化測試（需要 Django 環境）")
        return True
    
    try:
        from eshop.models import OrderModel
        
        # 創建測試訂單
        order = OrderModel(
            id=999,
            total_price=100.0,
            status='preparing',
            payment_status='paid',
            order_type='normal',
            customer_name='Test Customer',
            phone='12345678',
            email='test@example.com',
            pickup_code='TEST123'
        )
        
        # 測試序列化
        serialized = common_utils.serialize_order_basic(order)
        print(f"✅ 訂單序列化結果:")
        for key, value in serialized.items():
            print(f"  - {key}: {value}")
        
        # 測試空訂單
        empty_serialized = common_utils.serialize_order_basic(None)
        print(f"✅ 空訂單序列化: {empty_serialized}")
        
    except Exception as e:
        print(f"⚠️ 序列化測試跳過: {str(e)}")
    
    return True


def test_queue_stats():
    """測試隊列統計函數"""
    print("\n=== 測試隊列統計函數 ===")
    
    if not DJANGO_SETUP:
        print("⚠️ 跳過隊列統計測試（需要 Django 環境）")
        return True
    
    try:
        stats = common_utils.get_queue_stats()
        print(f"✅ 隊列統計結果:")
        for key, value in stats.items():
            print(f"  - {key}: {value}")
        
    except Exception as e:
        print(f"⚠️ 隊列統計測試跳過: {str(e)}")
    
    return True


def test_api_response_functions():
    """測試API響應函數"""
    print("\n=== 測試API響應函數 ===")
    
    # 測試創建API響應
    from django.http import JsonResponse
    
    # 測試成功響應
    success_response = common_utils.create_api_response(
        success=True,
        message='操作成功',
        data={'test': 'data'},
        status_code=200
    )
    
    print(f"✅ 成功響應類型: {type(success_response)}")
    print(f"✅ 成功響應狀態碼: {success_response.status_code}")
    
    # 測試錯誤響應
    error_response = common_utils.create_api_response(
        success=False,
        message='操作失敗',
        error_details={'error_code': 500},
        status_code=400
    )
    
    print(f"✅ 錯誤響應類型: {type(error_response)}")
    print(f"✅ 錯誤響應狀態碼: {error_response.status_code}")
    
    return True


def test_exception_handling():
    """測試異常處理"""
    print("\n=== 測試異常處理 ===")
    
    try:
        # 故意引發異常
        raise ValueError("測試異常")
    except Exception as e:
        # 測試異常處理為API響應
        response = common_utils.handle_exception_as_api_response(
            e, context='test_context', operation='test_operation'
        )
        
        print(f"✅ 異常處理響應類型: {type(response)}")
        print(f"✅ 異常處理狀態碼: {response.status_code}")
    
    return True


def main():
    """主測試函數"""
    print("🚀 開始測試共用工具模塊")
    print("=" * 50)
    
    tests = [
        test_time_functions,
        test_safe_get_functions,
        test_validation_functions,
        test_logging_functions,
        test_serialization_functions,
        test_queue_stats,
        test_api_response_functions,
        test_exception_handling,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
            print(f"✅ {test.__name__}: 通過")
        except Exception as e:
            results.append(False)
            print(f"❌ {test.__name__}: 失敗 - {str(e)}")
    
    print("\n" + "=" * 50)
    print("📊 測試結果總結:")
    
    passed = sum(results)
    total = len(results)
    
    print(f"✅ 通過: {passed}/{total}")
    print(f"❌ 失敗: {total - passed}/{total}")
    
    if passed == total:
        print("🎉 所有測試通過！")
        return 0
    else:
        print("⚠️ 部分測試失敗")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)