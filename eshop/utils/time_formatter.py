"""
時間格式化工具 - 統一處理時間格式化的共用模塊
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Union, Dict, Any
import pytz

logger = logging.getLogger(__name__)


class TimeFormatter:
    """時間格式化工具 - 統一處理時間格式化的共用邏輯"""
    
    @staticmethod
    def format_for_display(dt: datetime, tz: pytz.timezone) -> str:
        """
        統一時間格式化為顯示格式
        
        參數:
            dt: 日期時間對象
            tz: 時區對象
            
        返回:
            格式化後的時間字符串 (HH:MM)
        """
        if not dt:
            return '--:--'
        
        try:
            if dt.tzinfo is None:
                dt = pytz.UTC.localize(dt)
            dt_local = dt.astimezone(tz)
            return dt_local.strftime('%H:%M')
        except Exception as e:
            logger.error(f"時間格式化失敗: {str(e)}")
            return '--:--'
    
    @staticmethod
    def format_iso(dt: datetime, tz: pytz.timezone) -> Optional[str]:
        """
        格式化為ISO格式
        
        參數:
            dt: 日期時間對象
            tz: 時區對象
            
        返回:
            ISO格式字符串或None
        """
        if not dt:
            return None
        
        try:
            if dt.tzinfo is None:
                dt = pytz.UTC.localize(dt)
            dt_local = dt.astimezone(tz)
            return dt_local.isoformat()
        except Exception as e:
            logger.error(f"ISO時間格式化失敗: {str(e)}")
            return None
    
    @staticmethod
    def calculate_time_diff(now: datetime, target_time: datetime) -> int:
        """
        計算時間差（秒）
        
        參數:
            now: 當前時間
            target_time: 目標時間
            
        返回:
            時間差（秒），負數表示目標時間已過
        """
        if not target_time:
            return 0
        
        try:
            # 確保兩個時間都有時區信息
            if now.tzinfo is None:
                now = pytz.UTC.localize(now)
            if target_time.tzinfo is None:
                target_time = pytz.UTC.localize(target_time)
            
            # 轉換到相同時區
            now_utc = now.astimezone(pytz.UTC)
            target_utc = target_time.astimezone(pytz.UTC)
            
            time_diff = target_utc - now_utc
            return int(time_diff.total_seconds())
        except Exception as e:
            logger.error(f"計算時間差失敗: {str(e)}")
            return 0
    
    @staticmethod
    def format_time_diff(seconds: int) -> str:
        """
        格式化時間差為可讀格式
        
        參數:
            seconds: 時間差（秒）
            
        返回:
            可讀的時間差字符串
        """
        if seconds <= 0:
            return "刚刚"
        
        if seconds < 60:
            return f"{seconds}秒前"
        elif seconds < 3600:
            minutes = seconds // 60
            remaining_seconds = seconds % 60
            if remaining_seconds > 0:
                return f"{minutes}分{remaining_seconds}秒前"
            else:
                return f"{minutes}分鐘前"
        elif seconds < 86400:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            if minutes > 0:
                return f"{hours}小時{minutes}分前"
            else:
                return f"{hours}小時前"
        else:
            days = seconds // 86400
            return f"{days}天前"
    
    @staticmethod
    def calculate_wait_time(now: datetime, start_time: datetime) -> Dict[str, Any]:
        """
        計算等待時間
        
        參數:
            now: 當前時間
            start_time: 開始時間
            
        返回:
            等待時間信息字典
        """
        wait_seconds = TimeFormatter.calculate_time_diff(now, start_time)
        wait_seconds = max(0, wait_seconds)
        
        wait_minutes = max(0, int(wait_seconds / 60))
        
        return {
            'wait_seconds': wait_seconds,
            'wait_minutes': wait_minutes,
            'wait_display': f"{wait_minutes}分鐘",
            'wait_display_short': f"{wait_minutes}分",
        }
    
    @staticmethod
    def calculate_remaining_time(now: datetime, completion_time: datetime) -> Dict[str, Any]:
        """
        計算剩餘時間
        
        參數:
            now: 當前時間
            completion_time: 完成時間
            
        返回:
            剩餘時間信息字典
        """
        remaining_seconds = TimeFormatter.calculate_time_diff(now, completion_time)
        remaining_seconds = max(0, remaining_seconds)
        
        remaining_minutes = max(0, int(remaining_seconds / 60))
        
        return {
            'remaining_seconds': remaining_seconds,
            'remaining_minutes': remaining_minutes,
            'remaining_display': f"{remaining_minutes}分鐘",
            'remaining_display_short': f"{remaining_minutes}分",
        }
    
    @staticmethod
    def format_created_at(order, tz: pytz.timezone) -> Dict[str, str]:
        """
        格式化創建時間
        
        參數:
            order: 訂單對象
            tz: 時區對象
            
        返回:
            創建時間信息字典
        """
        from django.utils import timezone
        
        created_at = order.created_at
        if not created_at:
            return {
                'iso': None,
                'display': '--:--',
                'full': '--',
            }
        
        try:
            if created_at.tzinfo is None:
                created_at = timezone.make_aware(created_at, tz)
            created_at_local = created_at.astimezone(tz)
            
            return {
                'iso': created_at_local.isoformat(),
                'display': created_at_local.strftime('%H:%M'),
                'full': created_at_local.strftime('%Y-%m-%d %H:%M'),
            }
        except Exception as e:
            logger.error(f"格式化創建時間失敗: {str(e)}")
            return {
                'iso': None,
                'display': '--:--',
                'full': '--',
            }
    
    @staticmethod
    def format_ready_time(order, tz: pytz.timezone) -> Dict[str, str]:
        """
        格式化就緒時間
        
        參數:
            order: 訂單對象
            tz: 時區對象
            
        返回:
            就緒時間信息字典
        """
        from django.utils import timezone
        
        ready_at = order.ready_at
        if not ready_at:
            return {
                'iso': None,
                'display': '--:--',
            }
        
        try:
            if ready_at.tzinfo is None:
                ready_at = timezone.make_aware(ready_at, tz)
            ready_at_local = ready_at.astimezone(tz)
            
            return {
                'iso': ready_at_local.isoformat(),
                'display': ready_at_local.strftime('%H:%M'),
            }
        except Exception as e:
            logger.error(f"格式化就緒時間失敗: {str(e)}")
            return {
                'iso': None,
                'display': '--:--',
            }
    
    @staticmethod
    def format_picked_up_time(order, tz: pytz.timezone) -> Dict[str, str]:
        """
        格式化取餐時間
        
        參數:
            order: 訂單對象
            tz: 時區對象
            
        返回:
            取餐時間信息字典
        """
        from django.utils import timezone
        
        picked_up_at = order.picked_up_at
        if not picked_up_at:
            return {
                'iso': None,
                'display': '--:--',
            }
        
        try:
            if picked_up_at.tzinfo is None:
                picked_up_at = timezone.make_aware(picked_up_at, tz)
            picked_up_at_local = picked_up_at.astimezone(tz)
            
            return {
                'iso': picked_up_at_local.isoformat(),
                'display': picked_up_at_local.strftime('%H:%M'),
            }
        except Exception as e:
            logger.error(f"格式化取餐時間失敗: {str(e)}")
            return {
                'iso': None,
                'display': '--:--',
            }
    
    @staticmethod
    def get_hong_kong_time() -> datetime:
        """
        獲取香港當前時間
        
        返回:
            香港當前時間
        """
        try:
            from eshop.time_calculation import unified_time_service
            return unified_time_service.get_hong_kong_time()
        except ImportError:
            # 備用方案
            hk_tz = pytz.timezone('Asia/Hong_Kong')
            return datetime.now(hk_tz)


# 簡化函數接口
def format_for_display(dt: datetime, tz: pytz.timezone) -> str:
    """簡化接口：格式化時間為顯示格式"""
    return TimeFormatter.format_for_display(dt, tz)


def format_iso(dt: datetime, tz: pytz.timezone) -> Optional[str]:
    """簡化接口：格式化為ISO格式"""
    return TimeFormatter.format_iso(dt, tz)


def calculate_time_diff(now: datetime, target_time: datetime) -> int:
    """簡化接口：計算時間差"""
    return TimeFormatter.calculate_time_diff(now, target_time)


def format_time_diff(seconds: int) -> str:
    """簡化接口：格式化時間差"""
    return TimeFormatter.format_time_diff(seconds)


def get_hong_kong_time() -> datetime:
    """簡化接口：獲取香港當前時間"""
    return TimeFormatter.get_hong_kong_time()