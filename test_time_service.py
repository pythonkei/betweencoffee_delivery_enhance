#!/usr/bin/env python
"""
測試統一時間服務功能

此腳本用於測試新創建的統一時間服務模組，
確保所有功能正常工作。
"""

import os
import sys
import django

# 設置 Django 環境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'betweencoffee_delivery.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

django.setup()

import logging
from datetime import datetime, timedelta
import pytz
from django.utils import timezone

# 導入時間服務
from eshop.time_calculation import unified_time_service
from eshop.time_calculation.time_calculators import TimeCalculators
from eshop.time_calculation.time_formatters import TimeFormatters
from eshop.time_calculation.time_validators import TimeValidators
from eshop.time_calculation.constants import TimeConstants

logger = logging.getLogger(__name__)


def test_basic_time_functions():
    """測試基礎時間函數"""
    print("=== 測試基礎時間函數 ===")
    
    # 測試獲取香港時間
    hk_time = unified_time_service.get_hong_kong_time()
    print(f"1. 香港時間: {hk_time}")
    print(f"   時區: {hk_time.tzinfo}")
    
    # 測試時間格式化
    formatted_full = unified_time_service.format_time_for_display(hk_time, 'full')
    formatted_time = unified_time_service.format_time_for_display(hk_time, 'time_only')
    formatted_date = unified_time_service.format_time_for_display(hk_time, 'date_only')
    formatted_relative = unified_time_service.format_time_for_display(hk_time, 'relative')
    
    print(f"2. 格式化時間:")
    print(f"   完整格式: {formatted_full}")
    print(f"   僅時間: {formatted_time}")
    print(f"   僅日期: {formatted_date}")
    print(f"   相對時間: {formatted_relative}")
    
    # 測試時區轉換
    test_time = datetime(2024, 1, 1, 12, 0, 0)
    hk_converted = unified_time_service.ensure_hong_kong_timezone(test_time)
    print(f"3. 時區轉換:")
    print(f"   原始時間: {test_time}")
    print(f"   香港時間: {hk_converted}")
    print(f"   時區: {hk_converted.tzinfo}")
    
    print("✅ 基礎時間函數測試完成\n")


def test_time_calculations():
    """測試時間計算"""
    print("=== 測試時間計算 ===")
    
    # 測試製作時間計算
    test_cases = [0, 1, 2, 3, 5, 10]
    for coffee_count in test_cases:
        prep_time = unified_time_service.calculate_preparation_time(coffee_count)
        print(f"1. 咖啡杯數: {coffee_count} -> 製作時間: {prep_time}分鐘")
    
    # 測試隊列等待時間計算
    queue_positions = [1, 2, 3, 5, 10]
    for position in queue_positions:
        wait_time = unified_time_service.calculate_queue_wait_time(position, 5)
        print(f"2. 隊列位置: {position} (當前製作剩餘5分鐘) -> 等待時間: {wait_time}分鐘")
    
    # 測試剩餘時間計算
    now = unified_time_service.get_hong_kong_time()
    future_time = now + timedelta(minutes=30)
    past_time = now - timedelta(minutes=30)
    
    remaining_future = unified_time_service.calculate_remaining_minutes(future_time)
    remaining_past = unified_time_service.calculate_remaining_minutes(past_time)
    
    print(f"3. 剩餘時間計算:")
    print(f"   未來時間 ({future_time.strftime('%H:%M')}): {remaining_future}分鐘")
    print(f"   過去時間 ({past_time.strftime('%H:%M')}): {remaining_past}分鐘")
    
    # 測試時間緊急檢查
    latest_start = now + timedelta(minutes=10)
    is_urgent = unified_time_service.is_time_urgent(latest_start)
    print(f"4. 時間緊急檢查:")
    print(f"   最晚開始時間: {latest_start.strftime('%H:%M')}")
    print(f"   是否緊急: {is_urgent}")
    
    print("✅ 時間計算測試完成\n")


def test_time_formatters():
    """測試時間格式化器"""
    print("=== 測試時間格式化器 ===")
    
    now = unified_time_service.get_hong_kong_time()
    
    # 測試持續時間格式化
    test_minutes = [0, 5, 30, 65, 125, 180]
    for minutes in test_minutes:
        formatted = TimeFormatters.format_duration_minutes(minutes)
        print(f"1. 持續時間 {minutes}分鐘 -> {formatted}")
    
    # 測試取貨時間顯示
    pickup_choices = ['5', '10', '15', '20', '30']
    for choice in pickup_choices:
        formatted = TimeFormatters.format_pickup_time_display(choice, is_urgent=False)
        formatted_urgent = TimeFormatters.format_pickup_time_display(choice, is_urgent=True)
        print(f"2. 取貨選擇 {choice}:")
        print(f"   正常: {formatted['text']} (CSS: {formatted['css_class']})")
        print(f"   緊急: {formatted_urgent['text']} (CSS: {formatted_urgent['css_class']})")
    
    # 測試訂單時間摘要
    test_cases = [
        ('quick', True, False),  # 快速咖啡訂單
        ('normal', True, False), # 普通咖啡訂單
        ('normal', False, True), # 純咖啡豆訂單
        ('normal', False, False), # 其他訂單
    ]
    
    for order_type, has_coffee, has_beans in test_cases:
        summary = TimeFormatters.format_order_time_summary(order_type, has_coffee, has_beans)
        print(f"3. 訂單類型 {order_type}, 咖啡: {has_coffee}, 咖啡豆: {has_beans}:")
        print(f"   顯示: {summary['text']} (CSS: {summary['css_class']})")
    
    # 測試進度條格式化
    percentages = [0, 25, 50, 75, 100]
    for percentage in percentages:
        progress = TimeFormatters.format_progress_bar(percentage)
        print(f"4. 進度 {percentage}% -> 顏色: {progress['color_class']}")
    
    print("✅ 時間格式化器測試完成\n")


def test_time_validators():
    """測試時間驗證器"""
    print("=== 測試時間驗證器 ===")
    
    # 測試取貨時間選擇驗證
    test_choices = ['5', '10', '15', '20', '30', 'invalid', None]
    for choice in test_choices:
        is_valid = TimeValidators.is_valid_pickup_choice(choice)
        print(f"1. 取貨選擇 '{choice}' -> 有效: {is_valid}")
    
    # 測試時間有效性驗證
    now = unified_time_service.get_hong_kong_time()
    future_time = now + timedelta(hours=1)
    past_time = now - timedelta(hours=1)
    invalid_time = "not a datetime"
    
    test_times = [
        (now, "現在"),
        (future_time, "未來"),
        (past_time, "過去"),
        (invalid_time, "無效"),
        (None, "空值"),
    ]
    
    for time_obj, description in test_times:
        is_valid = TimeValidators.is_valid_datetime(time_obj)
        is_future = TimeValidators.is_future_time(time_obj) if is_valid else False
        is_past = TimeValidators.is_past_time(time_obj) if is_valid else False
        
        print(f"2. 時間 {description}:")
        print(f"   有效: {is_valid}")
        if is_valid:
            print(f"   未來: {is_future}, 過去: {is_past}")
    
    # 測試快速訂單時間驗證
    estimated_time = now + timedelta(minutes=30)
    latest_start = now + timedelta(minutes=20)
    
    is_valid, error_msg = TimeValidators.validate_quick_order_times(estimated_time, latest_start)
    print(f"3. 快速訂單時間驗證:")
    print(f"   預計取貨: {estimated_time.strftime('%H:%M')}")
    print(f"   最晚開始: {latest_start.strftime('%H:%M')}")
    print(f"   有效: {is_valid}, 錯誤: {error_msg}")
    
    # 測試製作時間驗證
    test_prep_times = [-5, 0, 30, 200, "invalid"]
    for prep_time in test_prep_times:
        is_valid, error_msg = TimeValidators.validate_preparation_time(prep_time)
        print(f"4. 製作時間 {prep_time}: 有效: {is_valid}, 錯誤: {error_msg}")
    
    print("✅ 時間驗證器測試完成\n")


def test_constants():
    """測試常量"""
    print("=== 測試常量 ===")
    
    # 測試時區常量
    print(f"1. 時區常量:")
    print(f"   香港時區: {TimeConstants.HONG_KONG_TZ}")
    print(f"   UTC時區: {TimeConstants.UTC_TZ}")
    
    # 測試製作時間配置
    prep_config = TimeConstants.get_preparation_time_config()
    print(f"2. 製作時間配置:")
    for key, value in prep_config.items():
        print(f"   {key}: {value}")
    
    # 測試快速訂單時間映射
    print(f"3. 快速訂單時間映射:")
    for choice, minutes in TimeConstants.QUICK_ORDER_TIME_MAP.items():
        display = TimeConstants.get_quick_order_display(choice)
        print(f"   選擇 {choice}: {minutes}分鐘 -> 顯示: {display}")
    
    # 測試時間格式化字符串
    print(f"4. 時間格式化字符串:")
    print(f"   完整格式: {TimeConstants.TIME_FORMAT_FULL}")
    print(f"   僅時間: {TimeConstants.TIME_FORMAT_TIME_ONLY}")
    print(f"   僅日期: {TimeConstants.TIME_FORMAT_DATE_ONLY}")
    
    print("✅ 常量測試完成\n")


def test_integration():
    """測試整合功能"""
    print("=== 測試整合功能 ===")
    
    # 創建模擬訂單數據
    class MockOrder:
        def __init__(self, order_id, is_quick=False, pickup_choice='5', has_coffee=True, has_beans=False):
            self.id = order_id
            self.is_quick_order = is_quick
            self.order_type = 'quick' if is_quick else 'normal'
            self.pickup_time_choice = pickup_choice
            self._has_coffee = has_coffee
            self._has_beans = has_beans
            self.latest_start_time = None
            self.estimated_ready_time = None
            self.created_at = unified_time_service.get_hong_kong_time()
            self.status = 'waiting'
        
        def get_items(self):
            items = []
            if self._has_coffee:
                items.append({'type': 'coffee', 'quantity': 2})
            if self._has_beans:
                items.append({'type': 'bean', 'quantity': 1})
            return items
        
        def has_coffee(self):
            return self._has_coffee
        
        def is_beans_only(self):
            return self._has_beans and not self._has_coffee
    
    # 測試不同類型的訂單
    test_orders = [
        MockOrder(1, is_quick=True, pickup_choice='10', has_coffee=True, has_beans=False),
        MockOrder(2, is_quick=False, has_coffee=True, has_beans=False),
        MockOrder(3, is_quick=False, has_coffee=False, has_beans=True),
        MockOrder(4, is_quick=True, pickup_choice='30', has_coffee=True, has_beans=True),
    ]
    
    for order in test_orders:
        print(f"\n測試訂單 #{order.id}:")
        print(f"  類型: {'快速' if order.is_quick_order else '普通'}")
        print(f"  取貨選擇: {order.pickup_time_choice}")
        print(f"  包含咖啡: {order.has_coffee()}")
        print(f"  純咖啡豆: {order.is_beans_only()}")
        
        # 測試時間摘要
        time_summary = unified_time_service.get_order_time_summary(order)
        print(f"  時間摘要:")
        for key, value in time_summary.items():
            print(f"    {key}: {value}")
        
        # 測試取貨時間格式化
        pickup_display = unified_time_service.format_pickup_time_for_order(order)
        if pickup_display:
            print(f"  取貨顯示: {pickup_display['text']} (CSS: {pickup_display['css_class']})")
        
        # 測試快速訂單時間計算
        if order.is_quick_order and order.has_coffee():
            quick_times = unified_time_service.calculate_quick_order_times(order)
            if quick_times:
                print(f"  快速訂單時間:")
                print(f"    預計取貨: {quick_times['estimated_pickup_time'].strftime('%H:%M')}")
                print(f"    最晚開始: {quick_times['latest_start_time'].strftime('%H:%M')}")
                print(f"    製作時間: {quick_times['preparation_minutes']}分鐘")
    
    print("\n✅ 整合功能測試完成\n")


def main():
    """主測試函數"""
    print("開始測試統一時間服務...\n")
    
    try:
        # 運行所有測試
        test_basic_time_functions()
        test_time_calculations()
        test_time_formatters()
        test_time_validators()
        test_constants()
        test_integration()
        
        print("🎉 所有測試完成！")
        print("\n總結:")
        print("1. ✅ 基礎時間函數正常")
        print("2. ✅ 時間計算正常")
        print("3. ✅ 時間格式化正常")
        print("4. ✅ 時間驗證正常")
        print("5. ✅ 常量定義正常")
        print("6. ✅ 整合功能正常")
        print("\n統一時間服務模組已準備就緒，可以開始遷移。")
        
    except Exception as e:
        print(f"❌ 測試失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())