"""
時間計算器 - 各種時間計算的具體實現
"""

from datetime import timedelta
import logging
from .constants import TimeConstants

logger = logging.getLogger(__name__)


class TimeCalculators:
    """時間計算器類"""
    
    @staticmethod
    def calculate_preparation_time(coffee_count):
        """
        計算咖啡製作時間（分鐘）
        
        Args:
            coffee_count: 咖啡杯數
            
        Returns:
            int: 預計製作時間（分鐘）
        """
        if coffee_count <= 0:
            return 0
        
        base = TimeConstants.PREPARATION_BASE_MINUTES
        additional = TimeConstants.PREPARATION_ADDITIONAL_PER_CUP
        
        # 計算公式：第一杯5分鐘，之後每杯3分鐘
        total_minutes = base + max(0, coffee_count - 1) * additional
        
        logger.debug(f"計算製作時間: {coffee_count}杯 -> {total_minutes}分鐘")
        return total_minutes
    
    @staticmethod
    def calculate_queue_wait_time(queue_position, current_preparing_time=0):
        """
        計算隊列等待時間
        
        Args:
            queue_position: 隊列位置（1-based）
            current_preparing_time: 當前正在製作訂單的剩餘時間
            
        Returns:
            int: 預計等待時間（分鐘）
        """
        if queue_position <= 1:
            return current_preparing_time
        
        # 假設每個訂單平均製作時間
        avg_prep_time = TimeConstants.DEFAULT_AVG_PREPARATION_TIME
        
        # 等待時間 = 前面訂單的製作時間總和
        wait_time = current_preparing_time + (queue_position - 2) * avg_prep_time
        
        logger.debug(f"計算隊列等待時間: 位置{queue_position} -> {wait_time}分鐘")
        return wait_time
    
    @staticmethod
    def calculate_remaining_minutes(target_time, current_time):
        """
        計算剩餘分鐘數
        
        Args:
            target_time: 目標時間
            current_time: 當前時間
            
        Returns:
            int: 剩餘分鐘數
        """
        if not target_time:
            return 0
        
        if target_time <= current_time:
            return 0
        
        diff = target_time - current_time
        return max(0, int(diff.total_seconds() / 60))
    
    @staticmethod
    def calculate_estimated_completion_time(start_time, preparation_minutes):
        """
        計算預計完成時間
        
        Args:
            start_time: 開始時間
            preparation_minutes: 製作分鐘數
            
        Returns:
            datetime: 預計完成時間
        """
        if not start_time or preparation_minutes <= 0:
            return None
        
        return start_time + timedelta(minutes=preparation_minutes)
    
    @staticmethod
    def calculate_latest_start_time(target_time, preparation_minutes, buffer_minutes=None):
        """
        計算最晚開始時間
        
        Args:
            target_time: 目標完成時間
            preparation_minutes: 製作分鐘數
            buffer_minutes: 緩衝分鐘數（默認使用常量）
            
        Returns:
            datetime: 最晚開始時間
        """
        if not target_time or preparation_minutes <= 0:
            return None
        
        if buffer_minutes is None:
            buffer_minutes = TimeConstants.BUFFER_MINUTES
        
        total_minutes = preparation_minutes + buffer_minutes
        return target_time - timedelta(minutes=total_minutes)
    
    @staticmethod
    def calculate_quick_order_times(pickup_choice, coffee_count, current_time):
        """
        計算快速訂單的相關時間
        
        Args:
            pickup_choice: 取貨時間選擇（'5', '10', '15', '20', '30'）
            coffee_count: 咖啡杯數
            current_time: 當前時間
            
        Returns:
            dict: 包含所有計算時間的字典
        """
        try:
            # 獲取取貨分鐘數
            minutes_to_add = TimeConstants.get_quick_order_minutes(pickup_choice)
            
            # 計算預計取貨時間
            estimated_pickup_time = current_time + timedelta(minutes=minutes_to_add)
            
            # 計算製作時間
            preparation_minutes = TimeCalculators.calculate_preparation_time(coffee_count)
            
            # 計算最晚開始時間
            latest_start_time = TimeCalculators.calculate_latest_start_time(
                estimated_pickup_time, preparation_minutes
            )
            
            result = {
                'estimated_pickup_time': estimated_pickup_time,
                'latest_start_time': latest_start_time,
                'preparation_minutes': preparation_minutes,
                'minutes_to_add': minutes_to_add,
                'coffee_count': coffee_count,
                'calculated_at': current_time,
            }
            
            logger.info(f"快速訂單時間計算: 取貨{minutes_to_add}分鐘後, {coffee_count}杯")
            return result
            
        except Exception as e:
            logger.error(f"計算快速訂單時間失敗: {str(e)}")
            # 返回默認值
            return {
                'estimated_pickup_time': current_time + timedelta(minutes=10),
                'latest_start_time': current_time + timedelta(minutes=5),
                'preparation_minutes': 5,
                'minutes_to_add': 10,
                'coffee_count': coffee_count,
                'calculated_at': current_time,
                'error': str(e)
            }
    
    @staticmethod
    def calculate_progress_percentage(start_time, estimated_completion_time, current_time):
        """
        計算製作進度百分比
        
        Args:
            start_time: 開始時間
            estimated_completion_time: 預計完成時間
            current_time: 當前時間
            
        Returns:
            int: 進度百分比（0-100）
        """
        if not start_time or not estimated_completion_time:
            return 0
        
        if current_time <= start_time:
            return 0
        
        if current_time >= estimated_completion_time:
            return 100
        
        total_duration = estimated_completion_time - start_time
        elapsed = current_time - start_time
        
        if total_duration.total_seconds() <= 0:
            return 0
        
        percentage = (elapsed.total_seconds() / total_duration.total_seconds()) * 100
        return min(100, max(0, int(percentage)))
    
    @staticmethod
    def is_time_urgent(latest_start_time, current_time, buffer_minutes=None):
        """
        檢查時間是否緊急（需要立即處理）
        
        Args:
            latest_start_time: 最晚開始時間
            current_time: 當前時間
            buffer_minutes: 緩衝分鐘數（默認使用常量）
            
        Returns:
            bool: 是否緊急
        """
        if not latest_start_time:
            return False
        
        if buffer_minutes is None:
            buffer_minutes = TimeConstants.URGENT_BUFFER_MINUTES
        
        # 如果當前時間已經超過最晚開始時間加上緩衝，則為緊急
        urgent_time = latest_start_time + timedelta(minutes=buffer_minutes)
        return current_time >= urgent_time