"""
時間驗證器 - 時間相關的驗證邏輯
"""

import logging
from datetime import datetime, timedelta
from django.utils import timezone
from .constants import TimeConstants

logger = logging.getLogger(__name__)


class TimeValidators:
    """時間驗證器類"""
    
    @staticmethod
    def is_valid_pickup_choice(choice):
        """
        驗證取貨時間選擇是否有效
        
        Args:
            choice: 取貨時間選擇
            
        Returns:
            bool: 是否有效
        """
        valid_choices = ['5', '10', '15', '20', '30']
        return choice in valid_choices
    
    @staticmethod
    def is_valid_datetime(datetime_obj):
        """
        驗證datetime對象是否有效
        
        Args:
            datetime_obj: datetime對象
            
        Returns:
            bool: 是否有效
        """
        if not datetime_obj:
            return False
        
        try:
            # 檢查是否為datetime類型
            if not isinstance(datetime_obj, datetime):
                return False
            
            # 檢查是否在合理範圍內（1900-2100年）
            if datetime_obj.year < 1900 or datetime_obj.year > 2100:
                return False
            
            return True
            
        except Exception:
            return False
    
    @staticmethod
    def is_future_time(target_time, current_time=None):
        """
        驗證目標時間是否在未來
        
        Args:
            target_time: 目標時間
            current_time: 當前時間（默認為現在）
            
        Returns:
            bool: 是否在未來
        """
        if not TimeValidators.is_valid_datetime(target_time):
            return False
        
        if current_time is None:
            current_time = timezone.now()
        
        if target_time.tzinfo:
            current_time = current_time.astimezone(target_time.tzinfo)
        
        return target_time > current_time
    
    @staticmethod
    def is_past_time(target_time, current_time=None):
        """
        驗證目標時間是否在過去
        
        Args:
            target_time: 目標時間
            current_time: 當前時間（默認為現在）
            
        Returns:
            bool: 是否在過去
        """
        if not TimeValidators.is_valid_datetime(target_time):
            return False
        
        if current_time is None:
            current_time = timezone.now()
        
        if target_time.tzinfo:
            current_time = current_time.astimezone(target_time.tzinfo)
        
        return target_time < current_time
    
    @staticmethod
    def is_within_time_range(target_time, start_time, end_time):
        """
        驗證目標時間是否在時間範圍內
        
        Args:
            target_time: 目標時間
            start_time: 開始時間
            end_time: 結束時間
            
        Returns:
            bool: 是否在範圍內
        """
        if not all([TimeValidators.is_valid_datetime(t) for t in [target_time, start_time, end_time]]):
            return False
        
        return start_time <= target_time <= end_time
    
    @staticmethod
    def validate_quick_order_times(estimated_pickup_time, latest_start_time):
        """
        驗證快速訂單時間的合理性
        
        Args:
            estimated_pickup_time: 預計取貨時間
            latest_start_time: 最晚開始時間
            
        Returns:
            tuple: (是否有效, 錯誤消息)
        """
        if not TimeValidators.is_valid_datetime(estimated_pickup_time):
            return False, "預計取貨時間無效"
        
        if not TimeValidators.is_valid_datetime(latest_start_time):
            return False, "最晚開始時間無效"
        
        # 檢查時間順序
        if latest_start_time >= estimated_pickup_time:
            return False, "最晚開始時間必須早於預計取貨時間"
        
        # 檢查時間差是否合理（至少5分鐘）
        time_diff = estimated_pickup_time - latest_start_time
        if time_diff.total_seconds() < 300:  # 5分鐘
            return False, "取貨時間和開始時間之間至少需要5分鐘"
        
        # 檢查是否在未來
        current_time = timezone.now()
        if estimated_pickup_time.tzinfo:
            current_time = current_time.astimezone(estimated_pickup_time.tzinfo)
        
        if estimated_pickup_time <= current_time:
            return False, "預計取貨時間必須在未來"
        
        return True, ""
    
    @staticmethod
    def validate_preparation_time(minutes):
        """
        驗證製作時間是否合理
        
        Args:
            minutes: 製作分鐘數
            
        Returns:
            tuple: (是否有效, 錯誤消息)
        """
        if not isinstance(minutes, (int, float)):
            return False, "製作時間必須是數字"
        
        if minutes < 0:
            return False, "製作時間不能為負數"
        
        if minutes > 180:  # 3小時
            return False, "製作時間不能超過3小時"
        
        return True, ""
    
    @staticmethod
    def validate_queue_position(position):
        """
        驗證隊列位置是否合理
        
        Args:
            position: 隊列位置
            
        Returns:
            tuple: (是否有效, 錯誤消息)
        """
        if not isinstance(position, int):
            return False, "隊列位置必須是整數"
        
        if position < 1:
            return False, "隊列位置必須大於0"
        
        if position > TimeConstants.MAX_QUEUE_POSITION:
            return False, f"隊列位置不能超過{TimeConstants.MAX_QUEUE_POSITION}"
        
        return True, ""
    
    @staticmethod
    def is_time_urgent_for_quick_order(latest_start_time, buffer_minutes=None):
        """
        檢查快速訂單是否緊急
        
        Args:
            latest_start_time: 最晚開始時間
            buffer_minutes: 緩衝分鐘數
            
        Returns:
            tuple: (是否緊急, 剩餘分鐘數)
        """
        if not TimeValidators.is_valid_datetime(latest_start_time):
            return False, 0
        
        if buffer_minutes is None:
            buffer_minutes = TimeConstants.URGENT_BUFFER_MINUTES
        
        current_time = timezone.now()
        if latest_start_time.tzinfo:
            current_time = current_time.astimezone(latest_start_time.tzinfo)
        
        # 計算剩餘時間
        time_remaining = latest_start_time - current_time
        remaining_minutes = max(0, int(time_remaining.total_seconds() / 60))
        
        # 如果剩餘時間小於緩衝時間，則為緊急
        is_urgent = remaining_minutes <= buffer_minutes
        
        return is_urgent, remaining_minutes
    
    @staticmethod
    def validate_order_timing(order):
        """
        驗證訂單時間安排的合理性
        
        Args:
            order: OrderModel實例
            
        Returns:
            dict: 驗證結果
        """
        result = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'is_urgent': False,
            'remaining_minutes': 0,
        }
        
        try:
            items = order.get_items()
            has_coffee = any(item.get('type') == 'coffee' for item in items)
            has_beans = any(item.get('type') == 'bean' for item in items)
            
            # 純咖啡豆訂單不需要時間驗證
            if has_beans and not has_coffee:
                return result
            
            # 快速訂單驗證
            if order.order_type == 'quick' and has_coffee:
                # 驗證取貨時間選擇
                if not order.pickup_time_choice:
                    result['is_valid'] = False
                    result['errors'].append("快速訂單必須選擇取貨時間")
                elif not TimeValidators.is_valid_pickup_choice(order.pickup_time_choice):
                    result['is_valid'] = False
                    result['errors'].append("無效的取貨時間選擇")
                
                # 驗證時間字段
                if order.latest_start_time:
                    is_urgent, remaining = TimeValidators.is_time_urgent_for_quick_order(
                        order.latest_start_time
                    )
                    result['is_urgent'] = is_urgent
                    result['remaining_minutes'] = remaining
                    
                    if is_urgent:
                        result['warnings'].append(f"訂單緊急，剩餘{remaining}分鐘")
            
            # 普通咖啡訂單驗證
            elif has_coffee:
                # 檢查是否應該已經開始製作
                if order.latest_start_time and order.latest_start_time < timezone.now():
                    result['warnings'].append("訂單應該已經開始製作")
            
            return result
            
        except Exception as e:
            logger.error(f"驗證訂單時間失敗: {str(e)}")
            result['is_valid'] = False
            result['errors'].append(f"驗證失敗: {str(e)}")
            return result
    
    @staticmethod
    def is_business_hours(target_time=None):
        """
        檢查是否在營業時間內（示例：8:00-22:00）
        
        Args:
            target_time: 目標時間（默認為現在）
            
        Returns:
            bool: 是否在營業時間內
        """
        if target_time is None:
            target_time = timezone.now()
        
        # 轉換為香港時間
        hk_time = target_time.astimezone(TimeConstants.HONG_KONG_TZ)
        
        # 營業時間：8:00-22:00
        business_start = hk_time.replace(hour=8, minute=0, second=0, microsecond=0)
        business_end = hk_time.replace(hour=22, minute=0, second=0, microsecond=0)
        
        return business_start <= hk_time <= business_end