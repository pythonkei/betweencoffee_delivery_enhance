"""
時間格式化器 - 時間顯示格式的統一處理
"""

import logging
from .constants import TimeConstants

logger = logging.getLogger(__name__)


class TimeFormatters:
    """時間格式化器類"""
    
    @staticmethod
    def format_time_for_display(datetime_obj, format_type='full'):
        """
        格式化時間用於顯示
        
        Args:
            datetime_obj: datetime對象
            format_type: 格式類型 ('full', 'time_only', 'date_only', 'relative')
            
        Returns:
            str: 格式化後的時間字符串
        """
        if not datetime_obj:
            return ''
        
        if format_type == 'full':
            return datetime_obj.strftime(TimeConstants.TIME_FORMAT_FULL)
        elif format_type == 'time_only':
            return datetime_obj.strftime(TimeConstants.TIME_FORMAT_TIME_ONLY)
        elif format_type == 'date_only':
            return datetime_obj.strftime(TimeConstants.TIME_FORMAT_DATE_ONLY)
        elif format_type == 'relative':
            return TimeFormatters._format_relative_time(datetime_obj)
        elif format_type == 'iso':
            return datetime_obj.strftime(TimeConstants.TIME_FORMAT_ISO)
        else:
            return datetime_obj.strftime(TimeConstants.TIME_FORMAT_FULL)
    
    @staticmethod
    def _format_relative_time(datetime_obj):
        """格式化相對時間（如"5分鐘前"）"""
        from django.utils import timezone
        
        now = timezone.now()
        if datetime_obj.tzinfo:
            now = now.astimezone(datetime_obj.tzinfo)
        
        diff = now - datetime_obj
        seconds = diff.total_seconds()
        
        if seconds < TimeConstants.RELATIVE_JUST_NOW:
            return "剛剛"
        elif seconds < TimeConstants.RELATIVE_MINUTES:
            minutes = int(seconds / 60)
            return f"{minutes}分鐘前"
        elif seconds < TimeConstants.RELATIVE_HOURS:
            hours = int(seconds / 3600)
            return f"{hours}小時前"
        else:
            days = int(seconds / 86400)
            return f"{days}天前"
    
    @staticmethod
    def format_duration_minutes(minutes):
        """
        格式化持續時間（分鐘）
        
        Args:
            minutes: 分鐘數
            
        Returns:
            str: 格式化後的持續時間
        """
        if minutes <= 0:
            return "0分鐘"
        
        if minutes < 60:
            return f"{minutes}分鐘"
        
        hours = minutes // 60
        remaining_minutes = minutes % 60
        
        if remaining_minutes == 0:
            return f"{hours}小時"
        else:
            return f"{hours}小時{remaining_minutes}分鐘"
    
    @staticmethod
    def format_pickup_time_display(pickup_choice, is_urgent=False):
        """
        格式化取貨時間顯示
        
        Args:
            pickup_choice: 取貨時間選擇
            is_urgent: 是否緊急
            
        Returns:
            dict: 包含文本、CSS類和圖標的格式化信息
        """
        display_text = TimeConstants.get_quick_order_display(pickup_choice)
        
        if is_urgent:
            return {
                'text': f"{display_text} (緊急)",
                'css_class': 'text-warning',
                'icon': 'fa-exclamation-triangle',
                'is_urgent': True,
            }
        else:
            return {
                'text': display_text,
                'css_class': 'text-info',
                'icon': 'fa-clock',
                'is_urgent': False,
            }
    
    @staticmethod
    def format_order_time_summary(order_type, has_coffee, has_beans):
        """
        格式化訂單時間摘要
        
        Args:
            order_type: 訂單類型 ('quick', 'normal')
            has_coffee: 是否包含咖啡
            has_beans: 是否包含咖啡豆
            
        Returns:
            dict: 時間摘要信息
        """
        # 純咖啡豆訂單
        if has_beans and not has_coffee:
            return {
                'text': '隨時可取',
                'css_class': 'text-success',
                'icon': 'fa-check-circle',
                'is_immediate': True,
                'display_type': 'beans_only'
            }
        
        # 快速訂單
        if order_type == 'quick' and has_coffee:
            return {
                'text': '快速訂單',
                'css_class': 'text-info',
                'icon': 'fa-bolt',
                'is_immediate': False,
                'display_type': 'quick_order'
            }
        
        # 普通咖啡訂單
        if has_coffee:
            return {
                'text': '製作中',
                'css_class': 'text-primary',
                'icon': 'fa-coffee',
                'is_immediate': False,
                'display_type': 'normal_coffee'
            }
        
        # 默認
        return {
            'text': '處理中',
            'css_class': 'text-secondary',
            'icon': 'fa-spinner',
            'is_immediate': False,
            'display_type': 'default'
        }
    
    @staticmethod
    def format_progress_bar(percentage, width=100):
        """
        格式化進度條
        
        Args:
            percentage: 百分比（0-100）
            width: 進度條寬度（像素）
            
        Returns:
            dict: 進度條信息
        """
        percentage = max(0, min(100, percentage))
        
        # 根據百分比決定顏色
        if percentage < 30:
            color_class = 'bg-danger'
        elif percentage < 70:
            color_class = 'bg-warning'
        else:
            color_class = 'bg-success'
        
        return {
            'percentage': percentage,
            'width': width,
            'color_class': color_class,
            'display_text': f"{percentage}%",
            'aria_label': f"進度: {percentage}%",
        }
    
    @staticmethod
    def format_time_range(start_time, end_time):
        """
        格式化時間範圍
        
        Args:
            start_time: 開始時間
            end_time: 結束時間
            
        Returns:
            str: 格式化後的時間範圍
        """
        if not start_time or not end_time:
            return ""
        
        start_str = TimeFormatters.format_time_for_display(start_time, 'time_only')
        end_str = TimeFormatters.format_time_for_display(end_time, 'time_only')
        
        return f"{start_str} - {end_str}"
    
    @staticmethod
    def format_countdown_minutes(minutes):
        """
        格式化倒計時（分鐘）
        
        Args:
            minutes: 剩餘分鐘數
            
        Returns:
            str: 格式化後的倒計時
        """
        if minutes <= 0:
            return "已過期"
        
        if minutes < 60:
            return f"{minutes}分鐘"
        
        hours = minutes // 60
        remaining_minutes = minutes % 60
        
        if remaining_minutes == 0:
            return f"{hours}小時"
        else:
            return f"{hours}小時{remaining_minutes}分鐘"