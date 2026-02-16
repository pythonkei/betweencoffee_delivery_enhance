"""
統一時間服務 - 所有時間計算的單一入口

取代分散在以下檔案的時間計算邏輯：
- time_service.py
- queue_manager.py
- order_status_manager.py
- models.py 中的時間計算方法
"""

import pytz
from datetime import datetime, timedelta
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


class UnifiedTimeService:
    """統一時間服務 - 所有時間計算的單一入口"""
    
    # 常量定義
    HONG_KONG_TZ = pytz.timezone('Asia/Hong_Kong')
    
    # 製作時間配置
    PREPARATION_TIME_CONFIG = {
        'base_minutes': 5,      # 第一杯基礎時間
        'additional_per_cup': 3, # 每增加一杯額外時間
        'max_concurrent': 3,    # 最大並發製作杯數
    }
    
    # 快速訂單時間映射
    QUICK_ORDER_TIME_MAP = {
        '5': 5,   # 5分鐘後
        '10': 10, # 10分鐘後
        '15': 15, # 15分鐘後
        '20': 20, # 20分鐘後
        '30': 30, # 30分鐘後
    }
    
    def __init__(self):
        self._cache = {}  # 簡單緩存
    
    # ========== 核心時間計算方法 ==========
    
    def calculate_preparation_time(self, coffee_count):
        """
        計算咖啡製作時間（分鐘）
        
        Args:
            coffee_count: 咖啡杯數
            
        Returns:
            int: 預計製作時間（分鐘）
        """
        if coffee_count <= 0:
            return 0
        
        base = self.PREPARATION_TIME_CONFIG['base_minutes']
        additional = self.PREPARATION_TIME_CONFIG['additional_per_cup']
        
        # 計算公式：第一杯5分鐘，之後每杯3分鐘
        total_minutes = base + max(0, coffee_count - 1) * additional
        
        logger.debug(f"計算製作時間: {coffee_count}杯 -> {total_minutes}分鐘")
        return total_minutes
    
    def calculate_queue_wait_time(self, queue_position, current_preparing_time=0):
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
        avg_prep_time = self.PREPARATION_TIME_CONFIG['base_minutes']
        
        # 等待時間 = 前面訂單的製作時間總和
        wait_time = current_preparing_time + (queue_position - 2) * avg_prep_time
        
        logger.debug(f"計算隊列等待時間: 位置{queue_position} -> {wait_time}分鐘")
        return wait_time
    
    def calculate_quick_order_times(self, order):
        """
        計算快速訂單的相關時間
        
        Args:
            order: OrderModel實例
            
        Returns:
            dict: 包含所有計算時間的字典
        """
        try:
            current_time = self.get_hong_kong_time()
            
            # 獲取取貨時間選擇
            pickup_choice = order.pickup_time_choice or '5'
            minutes_to_add = self.QUICK_ORDER_TIME_MAP.get(pickup_choice, 5)
            
            # 計算預計取貨時間
            estimated_pickup_time = current_time + timedelta(minutes=minutes_to_add)
            
            # 計算製作時間
            items = order.get_items()
            coffee_count = sum(item.get('quantity', 1) for item in items if item.get('type') == 'coffee')
            preparation_minutes = self.calculate_preparation_time(coffee_count)
            
            # 計算最晚開始時間（考慮緩衝時間）
            buffer_minutes = 2  # 2分鐘緩衝
            latest_start_time = estimated_pickup_time - timedelta(minutes=(preparation_minutes + buffer_minutes))
            
            result = {
                'estimated_pickup_time': estimated_pickup_time,
                'latest_start_time': latest_start_time,
                'preparation_minutes': preparation_minutes,
                'minutes_to_add': minutes_to_add,
                'coffee_count': coffee_count,
                'calculated_at': current_time,
            }
            
            logger.info(f"快速訂單時間計算: 訂單#{order.id}, 取貨{minutes_to_add}分鐘後")
            return result
            
        except Exception as e:
            logger.error(f"計算快速訂單時間失敗: {str(e)}")
            # 返回默認值
            return {
                'estimated_pickup_time': self.get_hong_kong_time() + timedelta(minutes=10),
                'latest_start_time': self.get_hong_kong_time() + timedelta(minutes=5),
                'preparation_minutes': 5,
                'minutes_to_add': 10,
                'coffee_count': 1,
                'calculated_at': self.get_hong_kong_time(),
                'error': str(e)
            }
    
    # ========== 時間格式化方法 ==========
    
    def format_time_for_display(self, datetime_obj, format_type='full'):
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
        
        # 確保時區正確
        dt = self.ensure_hong_kong_timezone(datetime_obj)
        
        if format_type == 'full':
            return dt.strftime('%Y-%m-%d %H:%M')
        elif format_type == 'time_only':
            return dt.strftime('%H:%M')
        elif format_type == 'date_only':
            return dt.strftime('%Y-%m-%d')
        elif format_type == 'relative':
            return self._format_relative_time(dt)
        else:
            return dt.strftime('%Y-%m-%d %H:%M')
    
    def _format_relative_time(self, datetime_obj):
        """格式化相對時間（如"5分鐘前"）"""
        now = self.get_hong_kong_time()
        diff = now - datetime_obj
        
        if diff.total_seconds() < 60:
            return "剛剛"
        elif diff.total_seconds() < 3600:
            minutes = int(diff.total_seconds() / 60)
            return f"{minutes}分鐘前"
        elif diff.total_seconds() < 86400:
            hours = int(diff.total_seconds() / 3600)
            return f"{hours}小時前"
        else:
            days = int(diff.total_seconds() / 86400)
            return f"{days}天前"
    
    # ========== 工具方法 ==========
    
    def get_hong_kong_time(self):
        """獲取當前香港時間"""
        utc_now = timezone.now()
        return utc_now.astimezone(self.HONG_KONG_TZ)
    
    def ensure_hong_kong_timezone(self, datetime_obj):
        """確保datetime對象使用香港時區"""
        if datetime_obj.tzinfo is None:
            # 如果沒有時區信息，假設是UTC
            datetime_obj = pytz.UTC.localize(datetime_obj)
        
        return datetime_obj.astimezone(self.HONG_KONG_TZ)
    
    def calculate_remaining_minutes(self, target_time):
        """計算剩餘分鐘數"""
        if not target_time:
            return 0
        
        now = self.get_hong_kong_time()
        target = self.ensure_hong_kong_timezone(target_time)
        
        if target <= now:
            return 0
        
        diff = target - now
        return max(0, int(diff.total_seconds() / 60))
    
    def is_time_urgent(self, latest_start_time, buffer_minutes=5):
        """
        檢查時間是否緊急（需要立即處理）
        
        Args:
            latest_start_time: 最晚開始時間
            buffer_minutes: 緩衝分鐘數
            
        Returns:
            bool: 是否緊急
        """
        if not latest_start_time:
            return False
        
        now = self.get_hong_kong_time()
        latest = self.ensure_hong_kong_timezone(latest_start_time)
        
        # 如果當前時間已經超過最晚開始時間加上緩衝，則為緊急
        urgent_time = latest + timedelta(minutes=buffer_minutes)
        return now >= urgent_time
    
    # ========== 訂單時間相關方法 ==========
    
    def get_order_time_summary(self, order):
        """
        獲取訂單時間摘要
        
        Args:
            order: OrderModel實例
            
        Returns:
            dict: 時間摘要信息
        """
        items = order.get_items()
        has_coffee = any(item.get('type') == 'coffee' for item in items)
        has_beans = any(item.get('type') == 'bean' for item in items)
        
        summary = {
            'has_coffee': has_coffee,
            'has_beans': has_beans,
            'is_beans_only': has_beans and not has_coffee,
            'requires_preparation': has_coffee,
        }
        
        # 根據訂單類型添加時間信息
        if order.order_type == 'quick' and has_coffee:
            quick_times = self.calculate_quick_order_times(order)
            summary.update({
                'estimated_pickup_time': quick_times['estimated_pickup_time'],
                'latest_start_time': quick_times['latest_start_time'],
                'preparation_minutes': quick_times['preparation_minutes'],
                'display_text': f"{quick_times['minutes_to_add']}分鐘後取貨",
                'is_urgent': self.is_time_urgent(quick_times['latest_start_time']),
            })
        elif has_coffee:
            # 普通咖啡訂單
            coffee_count = sum(item.get('quantity', 1) for item in items if item.get('type') == 'coffee')
            prep_minutes = self.calculate_preparation_time(coffee_count)
            
            summary.update({
                'preparation_minutes': prep_minutes,
                'display_text': f"預計製作時間: {prep_minutes}分鐘",
                'is_urgent': False,
            })
        else:
            # 純咖啡豆訂單
            summary.update({
                'preparation_minutes': 0,
                'display_text': "隨時可取",
                'is_urgent': False,
            })
        
        return summary
    
    def format_pickup_time_for_order(self, order):
        """
        為訂單格式化取貨時間顯示
        
        Args:
            order: OrderModel實例
            
        Returns:
            dict: 包含文本、CSS類和圖標的格式化信息
        """
        try:
            items = order.get_items()
            has_coffee = any(item.get('type') == 'coffee' for item in items)
            has_beans = any(item.get('type') == 'bean' for item in items)
            
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
            if order.order_type == 'quick' and has_coffee:
                if order.pickup_time_choice:
                    choice_map = {
                        '5': '5分鐘後',
                        '10': '10分鐘後',
                        '15': '15分鐘後',
                        '20': '20分鐘後',
                        '30': '30分鐘後',
                    }
                    text = choice_map.get(order.pickup_time_choice, '5分鐘後')
                    
                    # 檢查是否緊急
                    is_urgent = False
                    if order.latest_start_time:
                        is_urgent = self.is_time_urgent(order.latest_start_time)
                    
                    return {
                        'text': text,
                        'css_class': 'text-warning' if is_urgent else 'text-info',
                        'icon': 'fa-clock' if not is_urgent else 'fa-exclamation-triangle',
                        'is_immediate': False,
                        'is_urgent': is_urgent,
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
            
        except Exception as e:
            logger.error(f"格式化訂單取貨時間失敗: {str(e)}")
            return {
                'text': '處理中',
                'css_class': 'text-secondary',
                'icon': 'fa-spinner',
                'is_immediate': False,
                'display_type': 'error'
            }
    
    # ========== 兼容性方法（用於逐步遷移） ==========
    
    def calculate_times_based_on_pickup_choice(self, order):
        """
        兼容性方法：根據取貨時間選擇計算相關時間
        
        用於替換 order.calculate_times_based_on_pickup_choice() 方法
        """
        if not order.is_quick_order:
            return None, None
        
        result = self.calculate_quick_order_times(order)
        return result['estimated_pickup_time'], result['latest_start_time']
    
    def get_total_preparation_minutes(self, order):
        """
        兼容性方法：計算總製作時間（分鐘）
        
        用於替換 order.get_total_preparation_minutes() 方法
        """
        items = order.get_items()
        coffee_count = sum(item.get('quantity', 1) for item in items if item.get('type') == 'coffee')
        return self.calculate_preparation_time(coffee_count)
    
    def should_be_in_queue_by_now(self, order):
        """
        兼容性方法：檢查是否應該已經在隊列中
        
        用於替換 order.should_be_in_queue_by_now() 方法
        """
        if not order.latest_start_time:
            return True
        
        return self.get_hong_kong_time() >= order.latest_start_time