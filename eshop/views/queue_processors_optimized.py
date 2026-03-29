"""
隊列處理器優化版 - 使用查詢優化器減少數據庫查詢
"""

import logging
from datetime import timedelta
from typing import List, Dict, Any, Optional

from django.utils import timezone
import pytz

from eshop.models import OrderModel, CoffeeQueue
from eshop.order_status_manager import OrderStatusManager
from eshop.utils.order_item_processor import OrderItemProcessor
from eshop.utils.time_formatter import TimeFormatter
from eshop.time_calculation import unified_time_service
from eshop.query_optimizer_enhanced import (
    QueryOptimizer,
    BatchOrderProcessor,
    batch_prepare_orders,
    batch_prepare_ready_orders
)

logger = logging.getLogger(__name__)


class OptimizedWaitingQueueProcessor:
    """優化的等待隊列處理器"""
    
    def __init__(self, now=None, hk_tz=None):
        self.now = now or timezone.now()
        self.hk_tz = hk_tz or pytz.timezone('Asia/Hong_Kong')
    
    def process(self) -> List[Dict[str, Any]]:
        """處理等待隊列數據（優化版）"""
        try:
            # 使用優化查詢獲取等待隊列
            waiting_queues = QueryOptimizer.get_waiting_queues()
            
            # 批量處理訂單數據
            orders = [queue_item.order for queue_item in waiting_queues]
            order_data_list = batch_prepare_orders(
                orders,
                include_queue_info=True,
                now=self.now,
                hk_tz=self.hk_tz
            )
            
            # 添加等待時間信息
            for i, queue_item in enumerate(waiting_queues):
                if i < len(order_data_list):
                    order_data = order_data_list[i]
                    
                    # 添加快速訂單時間信息
                    if queue_item.order.is_quick_order:
                        quick_order_time_info = unified_time_service.calculate_quick_order_times(
                            queue_item.order
                        )
                        order_data['quick_order_time_info'] = quick_order_time_info
                    
                    # 添加等待時間信息
                    if queue_item.estimated_start_time:
                        wait_info = TimeFormatter.calculate_wait_time(
                            self.now,
                            queue_item.estimated_start_time
                        )
                        order_data.update(wait_info)
                    elif queue_item.order.is_quick_order and queue_item.order.pickup_time_choice:
                        minutes_to_add = unified_time_service.get_minutes_from_pickup_choice(
                            queue_item.order.pickup_time_choice
                        )
                        order_data['wait_display'] = f"{minutes_to_add}分鐘後"
            
            return order_data_list
            
        except Exception as e:
            logger.error(f"處理等待隊列數據失敗: {str(e)}", exc_info=True)
            return []


class OptimizedPreparingQueueProcessor:
    """優化的製作中隊列處理器"""
    
    def __init__(self, now=None, hk_tz=None):
        self.now = now or timezone.now()
        self.hk_tz = hk_tz or pytz.timezone('Asia/Hong_Kong')
    
    def process(self) -> List[Dict[str, Any]]:
        """處理製作中隊列數據（優化版）"""
        try:
            # 使用優化查詢獲取製作中隊列
            preparing_queues = QueryOptimizer.get_preparing_queues()
            
            # 批量處理訂單數據
            orders = [queue_item.order for queue_item in preparing_queues]
            order_data_list = batch_prepare_orders(
                orders,
                include_queue_info=True,
                now=self.now,
                hk_tz=self.hk_tz
            )
            
            # 添加製作開始時間
            for i, queue_item in enumerate(preparing_queues):
                if i < len(order_data_list):
                    order_data = order_data_list[i]
                    
                    # 添加製作開始時間
                    if queue_item.order.preparation_started_at:
                        prep_start = queue_item.order.preparation_started_at
                        if prep_start.tzinfo is None:
                            prep_start = timezone.make_aware(prep_start)
                        preparation_started_at_hk = prep_start.astimezone(self.hk_tz)
                        order_data['preparation_started_at'] = preparation_started_at_hk.isoformat()
            
            return order_data_list
            
        except Exception as e:
            logger.error(f"處理製作中隊列數據失敗: {str(e)}", exc_info=True)
            return []


class OptimizedReadyOrderProcessor:
    """優化的就緒訂單處理器"""
    
    def __init__(self, now=None, hk_tz=None):
        self.now = now or timezone.now()
        self.hk_tz = hk_tz or pytz.timezone('Asia/Hong_Kong')
    
    def process(self) -> List[Dict[str, Any]]:
        """處理就緒訂單數據（優化版）"""
        try:
            # 使用優化查詢獲取就緒訂單
            ready_orders = QueryOptimizer.get_ready_orders()
            
            # 批量處理就緒訂單數據
            order_data_list = batch_prepare_ready_orders(
                list(ready_orders),
                now=self.now,
                hk_tz=self.hk_tz
            )
            
            return order_data_list
            
        except Exception as e:
            logger.error(f"處理就緒訂單數據失敗: {str(e)}", exc_info=True)
            return []


class OptimizedCompletedOrderProcessor:
    """優化的已完成訂單處理器"""
    
    def __init__(self, now=None, hk_tz=None):
        self.now = now or timezone.now()
        self.hk_tz = hk_tz or pytz.timezone('Asia/Hong_Kong')
    
    def process(self) -> List[Dict[str, Any]]:
        """處理已完成訂單數據（優化版）"""
        try:
            # 使用優化查詢獲取已完成訂單
            completed_orders = QueryOptimizer.get_completed_orders()
            
            # 批量處理訂單數據
            order_data_list = batch_prepare_orders(
                list(completed_orders),
                include_queue_info=False,
                now=self.now,
                hk_tz=self.hk_tz
            )
            
            # 添加取餐時間信息
            for i, order in enumerate(completed_orders):
                if i < len(order_data_list):
                    order_data = order_data_list[i]
                    
                    # 添加取餐時間信息
                    if order.picked_up_at and self.hk_tz:
                        pickup_time = order.picked_up_at
                        if pickup_time.tzinfo is None:
                            pickup_time = timezone.make_aware(pickup_time)
                        picked_up_at_hk = pickup_time.astimezone(self.hk_tz)
                        
                        order_data['picked_up_at'] = picked_up_at_hk.isoformat()
                        order_data['completed_time'] = picked_up_at_hk.strftime('%H:%M')
            
            # 按取餐時間排序
            order_data_list.sort(
                key=lambda x: x.get('picked_up_at') or '',
                reverse=True
            )
            
            return order_data_list
            
        except Exception as e:
            logger.error(f"處理已完成訂單數據失敗: {str(e)}", exc_info=True)
            return []


class OptimizedUnifiedQueueProcessor:
    """優化的統一隊列處理器"""
    
    def __init__(self):
        self.now = timezone.now()
        self.hk_tz = pytz.timezone('Asia/Hong_Kong')
        
        # 初始化優化處理器
        self.waiting_processor = OptimizedWaitingQueueProcessor(self.now, self.hk_tz)
        self.preparing_processor = OptimizedPreparingQueueProcessor(self.now, self.hk_tz)
        self.ready_processor = OptimizedReadyOrderProcessor(self.now, self.hk_tz)
        self.completed_processor = OptimizedCompletedOrderProcessor(self.now, self.hk_tz)
    
    def get_unified_queue_data(self) -> Dict[str, Any]:
        """
        獲取統一隊列數據（優化版）
        
        返回:
            統一隊列數據字典
        """
        try:
            # 並行處理所有隊列數據（實際上是順序執行，但結構支持並行）
            waiting_data = self.waiting_processor.process()
            preparing_data = self.preparing_processor.process()
            ready_data = self.ready_processor.process()
            completed_data = self.completed_processor.process()
            
            # 徽章摘要
            badge_summary = {
                'waiting': len(waiting_data),
                'preparing': len(preparing_data),
                'ready': len(ready_data),
                'completed': len(completed_data),
            }
            
            return {
                'waiting_orders': waiting_data,
                'preparing_orders': preparing_data,
                'ready_orders': ready_data,
                'completed_orders': completed_data,
                'badge_summary': badge_summary,
                'optimized': True,  # 標記為優化版本
                'timestamp': self.now.isoformat(),
            }
            
        except Exception as e:
            logger.error(f"獲取統一隊列數據（優化版）失敗: {str(e)}", exc_info=True)
            return {
                'waiting_orders': [],
                'preparing_orders': [],
                'ready_orders': [],
                'completed_orders': [],
                'badge_summary': {
                    'waiting': 0,
                    'preparing': 0,
                    'ready': 0,
                    'completed': 0
                },
                'optimized': True,
                'timestamp': self.now.isoformat(),
            }


# 簡化函數接口（優化版）
def get_optimized_unified_queue_data() -> Dict[str, Any]:
    """簡化接口：獲取優化的統一隊列數據"""
    processor = OptimizedUnifiedQueueProcessor()
    return processor.get_unified_queue_data()


def process_optimized_waiting_queues(now, hk_tz) -> List[Dict[str, Any]]:
    """簡化接口：處理優化的等待隊列"""
    processor = OptimizedWaitingQueueProcessor(now, hk_tz)
    return processor.process()


def process_optimized_preparing_queues(now, hk_tz) -> List[Dict[str, Any]]:
    """簡化接口：處理優化的製作中隊列"""
    processor = OptimizedPreparingQueueProcessor(now, hk_tz)
    return processor.process()


def process_optimized_ready_orders(now, hk_tz) -> List[Dict[str, Any]]:
    """簡化接口：處理優化的就緒訂單"""
    processor = OptimizedReadyOrderProcessor(now, hk_tz)
    return processor.process()


def process_optimized_completed_orders(now, hk_tz) -> List[Dict[str, Any]]:
    """簡化接口：處理優化的已完成訂單"""
    processor = OptimizedCompletedOrderProcessor(now, hk_tz)
    return processor.process()


# 兼容性函數（保持原有接口）
def get_unified_queue_data() -> Dict[str, Any]:
    """兼容接口：獲取統一隊列數據（使用優化版）"""
    return get_optimized_unified_queue_data()


def process_waiting_queues(now, hk_tz) -> List[Dict[str, Any]]:
    """兼容接口：處理等待隊列（使用優化版）"""
    return process_optimized_waiting_queues(now, hk_tz)


def process_preparing_queues(now, hk_tz) -> List[Dict[str, Any]]:
    """兼容接口：處理製作中隊列（使用優化版）"""
    return process_optimized_preparing_queues(now, hk_tz)


def process_ready_orders(now, hk_tz) -> List[Dict[str, Any]]:
    """兼容接口：處理就緒訂單（使用優化版）"""
    return process_optimized_ready_orders(now, hk_tz)


def process_completed_orders(now, hk_tz) -> List[Dict[str, Any]]:
    """兼容接口：處理已完成訂單（使用優化版）"""
    return process_optimized_completed_orders(now, hk_tz)