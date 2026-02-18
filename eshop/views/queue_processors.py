"""
隊列處理器 - 統一處理隊列數據的共用模塊
重構 queue_views.py 中的重複邏輯
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

logger = logging.getLogger(__name__)


class BaseQueueProcessor:
    """基礎隊列處理器"""
    
    def __init__(self, now=None, hk_tz=None):
        """
        初始化處理器
        
        參數:
            now: 當前時間（可選）
            hk_tz: 香港時區（可選）
        """
        self.now = now or timezone.now()
        self.hk_tz = hk_tz or pytz.timezone('Asia/Hong_Kong')
    
    def process_order(self, order, queue_item=None) -> Optional[Dict[str, Any]]:
        """
        處理單個訂單的基礎邏輯
        
        參數:
            order: 訂單對象
            queue_item: 隊列項對象（可選）
            
        返回:
            訂單數據字典或None（處理失敗時）
        """
        try:
            # 使用訂單項目處理器準備數據
            order_data = OrderItemProcessor.prepare_order_data(
                order=order,
                queue_item=queue_item,
                now=self.now,
                hk_tz=self.hk_tz,
                include_queue_info=(queue_item is not None)
            )
            
            return order_data
            
        except Exception as e:
            logger.error(f"處理訂單 {order.id} 失敗: {str(e)}")
            return None


class WaitingQueueProcessor(BaseQueueProcessor):
    """等待隊列處理器"""
    
    def process(self, queue_items: List[CoffeeQueue]) -> List[Dict[str, Any]]:
        """
        處理等待隊列數據
        
        參數:
            queue_items: 等待隊列項列表
            
        返回:
            等待訂單數據列表
        """
        waiting_data = []
        
        for queue_item in queue_items:
            try:
                order = queue_item.order
                
                # 檢查訂單狀態是否正確
                if order.status == 'ready':
                    logger.warning(f"訂單 {order.id} 狀態為 ready，更新隊列狀態")
                    queue_item.status = 'ready'
                    queue_item.actual_completion_time = timezone.now()
                    queue_item.save()
                    continue
                
                # 使用基礎處理器處理訂單
                order_data = self.process_order(order, queue_item)
                if not order_data:
                    continue
                
                # 添加快速訂單時間信息
                if order.is_quick_order:
                    quick_order_time_info = unified_time_service.calculate_quick_order_times(order)
                    order_data['quick_order_time_info'] = quick_order_time_info
                
                # 添加等待時間信息
                if queue_item.estimated_start_time:
                    wait_info = TimeFormatter.calculate_wait_time(self.now, queue_item.estimated_start_time)
                    order_data.update(wait_info)
                elif order.is_quick_order and order.pickup_time_choice:
                    minutes_to_add = unified_time_service.get_minutes_from_pickup_choice(order.pickup_time_choice)
                    order_data['wait_display'] = f"{minutes_to_add}分鐘後"
                
                waiting_data.append(order_data)
                
            except Exception as e:
                logger.error(f"處理等待隊列項 {queue_item.id} 失敗: {str(e)}")
                continue
        
        return waiting_data


class PreparingQueueProcessor(BaseQueueProcessor):
    """製作中隊列處理器"""
    
    def process(self, queue_items: List[CoffeeQueue]) -> List[Dict[str, Any]]:
        """
        處理製作中隊列數據
        
        參數:
            queue_items: 製作中隊列項列表
            
        返回:
            製作中訂單數據列表
        """
        preparing_data = []
        
        for queue_item in queue_items:
            try:
                order = queue_item.order
                
                # 確保訂單狀態與隊列狀態一致
                if order.status != 'preparing':
                    result = OrderStatusManager.mark_as_preparing_manually(
                        order_id=order.id,
                        barista_name='system',
                        preparation_minutes=queue_item.preparation_time_minutes
                    )
                    
                    if not result['success']:
                        logger.error(f"同步訂單 {order.id} 狀態為製作中失敗: {result['message']}")
                    else:
                        order = result['order']
                
                # 使用基礎處理器處理訂單
                order_data = self.process_order(order, queue_item)
                if not order_data:
                    continue
                
                # 添加製作開始時間
                if order.preparation_started_at:
                    prep_start = order.preparation_started_at
                    if prep_start.tzinfo is None:
                        prep_start = timezone.make_aware(prep_start)
                    preparation_started_at_hk = prep_start.astimezone(self.hk_tz)
                    order_data['preparation_started_at'] = preparation_started_at_hk.isoformat()
                
                preparing_data.append(order_data)
                
            except Exception as e:
                logger.error(f"處理製作中隊列項 {queue_item.id} 失敗: {str(e)}")
                continue
        
        return preparing_data


class ReadyOrderProcessor(BaseQueueProcessor):
    """就緒訂單處理器"""
    
    def process(self, orders: List[OrderModel]) -> List[Dict[str, Any]]:
        """
        處理就緒訂單數據
        
        參數:
            orders: 就緒訂單列表
            
        返回:
            就緒訂單數據列表
        """
        ready_data = []
        
        for order in orders:
            try:
                # 使用訂單項目處理器準備就緒訂單數據
                order_data = OrderItemProcessor.prepare_ready_order_data(
                    order=order,
                    now=self.now,
                    hk_tz=self.hk_tz
                )
                
                if order_data:
                    ready_data.append(order_data)
                    
            except Exception as e:
                logger.error(f"處理就緒訂單 {order.id} 失敗: {str(e)}")
                continue
        
        # 按就緒時間排序
        ready_data.sort(key=lambda x: x.get('ready_at') or '', reverse=True)
        return ready_data


class CompletedOrderProcessor(BaseQueueProcessor):
    """已完成訂單處理器"""
    
    def process(self, orders: List[OrderModel]) -> List[Dict[str, Any]]:
        """
        處理已完成訂單數據
        
        參數:
            orders: 已完成訂單列表
            
        返回:
            已完成訂單數據列表
        """
        completed_data = []
        
        for order in orders:
            try:
                # 使用訂單項目處理器準備已完成訂單數據
                order_data = OrderItemProcessor.prepare_completed_order_data(
                    order=order,
                    now=self.now,
                    hk_tz=self.hk_tz
                )
                
                if order_data:
                    completed_data.append(order_data)
                    
            except Exception as e:
                logger.error(f"處理已完成訂單 {order.id} 失敗: {str(e)}")
                continue
        
        # 按取餐時間排序
        completed_data.sort(key=lambda x: x.get('picked_up_at') or '', reverse=True)
        return completed_data


class UnifiedQueueProcessor:
    """統一隊列處理器 - 整合所有處理器"""
    
    def __init__(self):
        """初始化統一處理器"""
        self.now = timezone.now()
        self.hk_tz = pytz.timezone('Asia/Hong_Kong')
        
        # 初始化子處理器
        self.waiting_processor = WaitingQueueProcessor(self.now, self.hk_tz)
        self.preparing_processor = PreparingQueueProcessor(self.now, self.hk_tz)
        self.ready_processor = ReadyOrderProcessor(self.now, self.hk_tz)
        self.completed_processor = CompletedOrderProcessor(self.now, self.hk_tz)
    
    def get_unified_queue_data(self) -> Dict[str, Any]:
        """
        獲取統一隊列數據
        
        返回:
            統一隊列數據字典
        """
        try:
            # 獲取等待隊列數據
            waiting_queues = CoffeeQueue.objects.filter(status='waiting').order_by('position')
            waiting_data = self.waiting_processor.process(waiting_queues)
            
            # 獲取製作中隊列數據
            preparing_queues = CoffeeQueue.objects.filter(status='preparing')
            preparing_data = self.preparing_processor.process(preparing_queues)
            
            # 獲取就緒訂單數據
            ready_orders = OrderModel.objects.filter(
                status='ready',
                payment_status="paid",
                picked_up_at__isnull=True
            ).order_by('-ready_at')[:20]
            ready_data = self.ready_processor.process(ready_orders)
            
            # 獲取已完成訂單數據
            time_threshold = self.now - timedelta(hours=4)
            completed_orders = OrderModel.objects.filter(
                status='completed',
                picked_up_at__isnull=False,
                picked_up_at__gte=time_threshold
            ).order_by('-picked_up_at')[:50]
            completed_data = self.completed_processor.process(completed_orders)
            
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
            }
            
        except Exception as e:
            logger.error(f"獲取統一隊列數據失敗: {str(e)}", exc_info=True)
            return {
                'waiting_orders': [],
                'preparing_orders': [],
                'ready_orders': [],
                'completed_orders': [],
                'badge_summary': {'waiting': 0, 'preparing': 0, 'ready': 0, 'completed': 0},
            }


# 簡化函數接口
def get_unified_queue_data() -> Dict[str, Any]:
    """簡化接口：獲取統一隊列數據"""
    processor = UnifiedQueueProcessor()
    return processor.get_unified_queue_data()


def process_waiting_queues(now, hk_tz) -> List[Dict[str, Any]]:
    """簡化接口：處理等待隊列"""
    processor = WaitingQueueProcessor(now, hk_tz)
    queue_items = CoffeeQueue.objects.filter(status='waiting').order_by('position')
    return processor.process(queue_items)


def process_preparing_queues(now, hk_tz) -> List[Dict[str, Any]]:
    """簡化接口：處理製作中隊列"""
    processor = PreparingQueueProcessor(now, hk_tz)
    queue_items = CoffeeQueue.objects.filter(status='preparing')
    return processor.process(queue_items)


def process_ready_orders(now, hk_tz) -> List[Dict[str, Any]]:
    """簡化接口：處理就緒訂單"""
    processor = ReadyOrderProcessor(now, hk_tz)
    orders = OrderModel.objects.filter(
        status='ready',
        payment_status="paid",
        picked_up_at__isnull=True
    ).order_by('-ready_at')[:20]
    return processor.process(orders)


def process_completed_orders(now, hk_tz) -> List[Dict[str, Any]]:
    """簡化接口：處理已完成訂單"""
    processor = CompletedOrderProcessor(now, hk_tz)
    time_threshold = now - timedelta(hours=4)
    orders = OrderModel.objects.filter(
        status='completed',
        picked_up_at__isnull=False,
        picked_up_at__gte=time_threshold
    ).order_by('-picked_up_at')[:50]
    return processor.process(orders)