# eshop/time_service_new.py
"""
新的統一時間服務模組 - 兼容層

此模組提供與舊版 time_service.py 兼容的接口，
但內部使用新的統一時間計算模組。

使用方式：
1. 將現有代碼中的 `from eshop.time_service import time_service` 替換為
   `from eshop.time_service_new import time_service`
2. 逐步遷移到新的統一時間服務模組
"""

import logging
from eshop.time_calculation import unified_time_service

logger = logging.getLogger(__name__)


class UnifiedTimeServiceCompat:
    """
    統一時間服務兼容類
    
    提供與舊版 UnifiedTimeService 相同的接口，
    但內部使用新的統一時間計算模組。
    """
    
    # ==================== 基礎時間函數 ====================
    
    @staticmethod
    def get_hong_kong_time():
        """獲取當前香港時間 - 統一入口"""
        return unified_time_service.get_hong_kong_time()
    
    @staticmethod
    def format_time_for_display(dt, include_date=False):
        """統一的時間格式化"""
        if not dt:
            return "--:--"
        
        try:
            if include_date:
                return unified_time_service.format_time_for_display(dt, 'full')
            else:
                return unified_time_service.format_time_for_display(dt, 'time_only')
        except Exception as e:
            logger.error(f"格式化時間失敗: {str(e)}")
            return "--:--"
    
    @staticmethod
    def is_time_ready(target_time):
        """檢查目標時間是否已到達"""
        if not target_time:
            return True
        
        current_hk = unified_time_service.get_hong_kong_time()
        target_hk = unified_time_service.ensure_hong_kong_timezone(target_time)
        return current_hk >= target_hk
    
    # ==================== 剩餘時間計算函數 ====================
    
    @staticmethod
    def get_remaining_minutes(target_time):
        """獲取剩餘分鐘數（向上取整）"""
        return unified_time_service.calculate_remaining_minutes(target_time)
    
    @staticmethod
    def calculate_remaining_time(target_time):
        """計算剩餘時間（秒）"""
        minutes = unified_time_service.calculate_remaining_minutes(target_time)
        return minutes * 60
    
    @staticmethod
    def format_remaining_time(seconds):
        """格式化剩餘時間顯示"""
        from eshop.time_calculation.time_formatters import TimeFormatters
        
        if seconds < 60:
            return f"{seconds}秒"
        
        minutes = seconds // 60
        return TimeFormatters.format_duration_minutes(minutes)
    
    # ==================== 進度計算函數 ====================
    
    @staticmethod
    def calculate_progress_percentage(order):
        """計算訂單製作進度百分比"""
        if order.status in ['ready', 'completed']:
            return 100
        
        if not order.estimated_ready_time:
            return 0
        
        from eshop.time_calculation.time_calculators import TimeCalculators
        from django.utils import timezone
        
        now = timezone.now()
        created_time = order.created_at
        estimated_time = order.estimated_ready_time
        
        return TimeCalculators.calculate_progress_percentage(
            created_time, estimated_time, now
        )
    
    # ==================== 統一製作時間計算 ====================
    
    @staticmethod
    def calculate_preparation_time(coffee_count):
        """統一製作時間計算"""
        return unified_time_service.calculate_preparation_time(coffee_count)
    
    # ==================== 隊列等待時間計算（核心）====================
    
    @staticmethod
    def _calculate_queue_wait_time():
        """計算當前隊列總等待時間（分鐘）"""
        from eshop.models import CoffeeQueue
        
        try:
            waiting_items = CoffeeQueue.objects.filter(status='waiting').order_by('position')
            preparing_items = CoffeeQueue.objects.filter(status='preparing')
            total_wait_time = 0.0
            
            # 1. 正在製作的訂單：剩餘時間
            for item in preparing_items:
                if item.estimated_completion_time:
                    remaining = unified_time_service.calculate_remaining_minutes(
                        item.estimated_completion_time
                    )
                    total_wait_time += remaining
                else:
                    total_wait_time += item.preparation_time_minutes
            
            # 2. 等待隊列的訂單：完整的製作時間
            total_wait_time += sum(item.preparation_time_minutes for item in waiting_items)
            
            return round(total_wait_time, 1)
        except Exception as e:
            logger.error(f"計算隊列等待時間失敗: {str(e)}")
            return 0.0
    
    @staticmethod
    def _get_queue_size():
        """獲取當前隊列大小（等待+製作）"""
        from eshop.models import CoffeeQueue
        return CoffeeQueue.objects.filter(status__in=['waiting', 'preparing']).count()
    
    # ==================== 訂單時間估算 ====================
    
    @staticmethod
    def estimate_order_time(order, include_queue_wait=True):
        """
        估算訂單的完成時間
        
        參數:
            order: OrderModel 實例
            include_queue_wait: 是否包含隊列等待時間（默認 True）
        
        返回:
            dict: 時間估算結果
        """
        try:
            # 使用新的統一時間服務
            time_summary = unified_time_service.get_order_time_summary(order)
            
            if not include_queue_wait:
                return {
                    'estimated_minutes': time_summary.get('preparation_minutes', 0),
                    'queue_position': None,
                    'is_immediate': time_summary.get('is_beans_only', False),
                    'message': time_summary.get('display_text', ''),
                    'queue_wait_minutes': 0,
                    'preparation_minutes': time_summary.get('preparation_minutes', 0)
                }
            
            # 計算隊列等待時間
            wait_minutes = UnifiedTimeServiceCompat._calculate_queue_wait_time()
            total_minutes = time_summary.get('preparation_minutes', 0) + wait_minutes
            
            # 獲取隊列位置
            queue_position = None
            if hasattr(order, 'queue_item') and order.queue_item:
                queue_position = order.queue_item.position
            else:
                queue_position = UnifiedTimeServiceCompat._get_queue_size() + 1
            
            # 生成友好消息
            message = UnifiedTimeServiceCompat._generate_time_message(
                total_minutes, wait_minutes, 
                time_summary.get('preparation_minutes', 0), 
                queue_position
            )
            
            return {
                'estimated_minutes': int(total_minutes),
                'queue_position': queue_position,
                'is_immediate': time_summary.get('is_beans_only', False),
                'message': message,
                'queue_wait_minutes': int(wait_minutes),
                'preparation_minutes': time_summary.get('preparation_minutes', 0)
            }
            
        except Exception as e:
            logger.error(f"估算訂單 {order.id} 時間失敗: {str(e)}")
            return {
                'estimated_minutes': 0,
                'queue_position': None,
                'is_immediate': False,
                'message': '無法估算時間',
                'queue_wait_minutes': 0,
                'preparation_minutes': 0
            }
    
    @staticmethod
    def estimate_new_order_time(coffee_count):
        """
        估算新訂單（尚未創建）的完成時間
        用於訂單確認頁面的即時提示
        """
        wait_minutes = UnifiedTimeServiceCompat._calculate_queue_wait_time()
        preparation_minutes = unified_time_service.calculate_preparation_time(coffee_count)
        total_minutes = wait_minutes + preparation_minutes
        estimated_position = UnifiedTimeServiceCompat._get_queue_size() + 1
        
        return {
            'total_minutes': int(total_minutes),
            'queue_wait_minutes': int(wait_minutes),
            'preparation_minutes': preparation_minutes,
            'estimated_position': estimated_position,
            'message': f"預計 {total_minutes:.0f} 分鐘後可取（隊列 #{estimated_position}）"
        }
    
    @staticmethod
    def _generate_time_message(total_time, wait_time, prep_time, queue_position):
        """生成時間友好消息"""
        if total_time <= 0:
            return "立即可取"
        
        messages = []
        if wait_time > 0:
            messages.append(f"隊列等待約 {wait_time:.0f} 分鐘")
        if prep_time > 0:
            messages.append(f"製作時間約 {prep_time:.0f} 分鐘")
        if queue_position:
            messages.append(f"隊列位置: #{queue_position}")
        
        base = f"預計 {total_time:.0f} 分鐘後完成"
        if messages:
            base += " (" + "，".join(messages) + ")"
        
        return base
    
    # ==================== 訂單綜合時間信息 ====================
    
    @staticmethod
    def calculate_estimated_times(order):
        """
        統一計算訂單的所有預估時間
        此方法為 `estimate_order_time` 的別名，保留向後兼容
        """
        return UnifiedTimeServiceCompat.estimate_order_time(order, include_queue_wait=True)
    
    # ==================== 快速訂單時間函數 ====================
    
    @staticmethod
    def calculate_quick_order_pickup_time(order):
        """計算快速訂單取貨時間"""
        try:
            if not order or not order.is_quick_order:
                return None
            
            # 使用新的統一時間服務
            quick_times = unified_time_service.calculate_quick_order_times(order)
            
            if not quick_times:
                return None
            
            now_hk = unified_time_service.get_hong_kong_time()
            estimated_pickup_time = quick_times['estimated_pickup_time']
            
            remaining_seconds = max(0, (estimated_pickup_time - now_hk).total_seconds())
            remaining_minutes = max(0, int(remaining_seconds / 60))
            
            return {
                'minutes_to_add': quick_times['minutes_to_add'],
                'pickup_time_display': f"{quick_times['minutes_to_add']}分鐘後",
                'estimated_pickup_time': estimated_pickup_time,
                'estimated_pickup_display': unified_time_service.format_time_for_display(
                    estimated_pickup_time, 'full'
                ),
                'latest_start_time': quick_times['latest_start_time'],
                'latest_start_display': unified_time_service.format_time_for_display(
                    quick_times['latest_start_time'], 'full'
                ) if quick_times['latest_start_time'] else None,
                'remaining_minutes': remaining_minutes,
                'remaining_seconds': int(remaining_seconds),
                'remaining_display': UnifiedTimeServiceCompat.format_remaining_time(remaining_seconds),
                'is_past_due': now_hk >= estimated_pickup_time,
            }
            
        except Exception as e:
            logger.error(f"計算快速訂單取貨時間失敗: {str(e)}")
            return None
    
    # ==================== 快速訂單時間函數（公開版本）====================
    
    @staticmethod
    def get_minutes_from_pickup_choice(pickup_time_choice):
        """從取貨時間選擇中提取分鐘數（公開方法）"""
        from eshop.time_calculation.constants import TimeConstants
        
        try:
            if isinstance(pickup_time_choice, str) and '分鐘' in pickup_time_choice:
                import re
                match = re.search(r'(\d+)', pickup_time_choice)
                if match:
                    return int(match.group(1))
            return int(pickup_time_choice) if pickup_time_choice else 5
        except (ValueError, TypeError):
            return 5
    
    @staticmethod
    def get_pickup_time_display_from_choice(pickup_time_choice):
        """統一處理取貨時間選擇的顯示（公開方法）"""
        from eshop.time_calculation.constants import TimeConstants
        
        if not pickup_time_choice:
            return '5分鐘後'
        
        return TimeConstants.get_quick_order_display(str(pickup_time_choice).strip())
    
    # ==================== 訂單取貨時間格式化 ====================
    
    @staticmethod
    def format_pickup_time_for_order(order):
        """為訂單統一格式化取貨時間信息"""
        if not order:
            return None
        
        # 使用新的統一時間服務
        return unified_time_service.format_pickup_time_for_order(order)
    
    # ==================== 批量處理函數 ====================
    
    @staticmethod
    def calculate_all_quick_order_times():
        """計算所有快速訂單的時間信息"""
        try:
            from eshop.models import OrderModel
            
            quick_orders = OrderModel.objects.filter(
                is_quick_order=True,
                payment_status='paid',
                status__in=['waiting', 'preparing']
            )
            
            results = {}
            for order in quick_orders:
                try:
                    time_info = UnifiedTimeServiceCompat.calculate_quick_order_pickup_time(order)
                    if time_info:
                        results[order.id] = time_info
                except Exception as e:
                    logger.error(f"計算訂單 {order.id} 時間失敗: {str(e)}")
                    continue
            
            return {
                'success': True,
                'count': len(results),
                'results': results,
                'timestamp': unified_time_service.get_hong_kong_time().isoformat()
            }
            
        except Exception as e:
            logger.error(f"批量計算快速訂單時間失敗: {str(e)}")
            return {'success': False, 'error': str(e), 'results': {}}
    
    @staticmethod
    def update_order_pickup_times(order_ids):
        """更新指定訂單的取貨時間信息"""
        try:
            from eshop.models import OrderModel
            
            updated_count = 0
            error_count = 0
            
            for order_id in order_ids:
                try:
                    order = OrderModel.objects.get(id=order_id)
                    if order.is_quick_order:
                        time_info = UnifiedTimeServiceCompat.calculate_quick_order_pickup_time(order)
                        if time_info and time_info['estimated_pickup_time']:
                            order.estimated_ready_time = time_info['estimated_pickup_time']
                            if time_info['latest_start_time']:
                                order.latest_start_time = time_info['latest_start_time']
                            order.save()
                            updated_count += 1
                            
                except OrderModel.DoesNotExist:
                    error_count += 1
                    logger.error(f"訂單 {order_id} 不存在")
                except Exception as e:
                    error_count += 1
                    logger.error(f"更新訂單 {order_id} 取貨時間失敗: {str(e)}")
            
            return {
                'success': True,
                'updated_count': updated_count,
                'error_count': error_count,
                'total': len(order_ids)
            }
            
        except Exception as e:
            logger.error(f"批量更新訂單取貨時間失敗: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def calculate_pickup_time_for_quick_order(order):
        """相容舊接口 - 內部呼叫新的方法"""
        return UnifiedTimeServiceCompat.calculate_quick_order_pickup_time(order)


# 全局單例實例（保持兼容性）
time_service = UnifiedTimeServiceCompat()