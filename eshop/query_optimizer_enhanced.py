"""
查詢優化器 - 階段2數據庫優化
統一管理所有數據庫查詢，減少N+1問題
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import timedelta

from django.utils import timezone
from django.db.models import Prefetch

from eshop.models import OrderModel, CoffeeQueue

logger = logging.getLogger(__name__)


class QueryOptimizer:
    """查詢優化器 - 統一管理所有數據庫查詢"""
    
    @staticmethod
    def get_waiting_queues():
        """
        獲取等待隊列（優化版）
        使用 select_related 減少查詢次數
        """
        return CoffeeQueue.objects.filter(status='waiting') \
            .select_related('order') \
            .order_by('position')
    
    @staticmethod
    def get_preparing_queues():
        """
        獲取製作中隊列（優化版）
        使用 select_related 減少查詢次數
        """
        return CoffeeQueue.objects.filter(status='preparing') \
            .select_related('order') \
            .order_by('estimated_completion_time')
    
    @staticmethod
    def get_ready_orders():
        """
        獲取就緒訂單（優化版）
        使用 select_related 減少查詢次數
        """
        return OrderModel.objects.filter(
            status='ready',
            payment_status="paid",
            picked_up_at__isnull=True
        ).select_related('queue_item') \
         .order_by('-ready_at')[:20]
    
    @staticmethod
    def get_completed_orders(hours=4):
        """
        獲取已完成訂單（優化版）
        使用 select_related 減少查詢次數
        """
        time_threshold = timezone.now() - timedelta(hours=hours)
        return OrderModel.objects.filter(
            status='completed',
            picked_up_at__isnull=False,
            picked_up_at__gte=time_threshold
        ).select_related('queue_item') \
         .order_by('-picked_up_at')[:50]
    
    @staticmethod
    def get_coffee_queue_map(order_ids: List[int]) -> Dict[int, CoffeeQueue]:
        """
        批量獲取 CoffeeQueue 數據，減少N+1查詢
        
        參數:
            order_ids: 訂單ID列表
            
        返回:
            訂單ID到CoffeeQueue的映射字典
        """
        if not order_ids:
            return {}
        
        # 批量查詢所有相關的 CoffeeQueue 記錄
        coffee_queues = CoffeeQueue.objects.filter(order_id__in=order_ids) \
            .order_by('order_id', '-id')  # 按訂單ID和ID降序排序
        
        # 創建映射，每個訂單只保留最新的 CoffeeQueue 記錄
        queue_map = {}
        for cq in coffee_queues:
            if cq.order_id not in queue_map:
                queue_map[cq.order_id] = cq
        
        return queue_map
    
    @staticmethod
    def get_orders_with_queue_info(order_ids: List[int]):
        """
        批量獲取訂單及其隊列信息（優化版）
        使用 prefetch_related 減少查詢次數
        """
        if not order_ids:
            return OrderModel.objects.none()
        
        # 使用 prefetch_related 預加載 CoffeeQueue 數據
        return OrderModel.objects.filter(id__in=order_ids) \
            .prefetch_related(
                Prefetch(
                    'coffeequeue_set',
                    queryset=CoffeeQueue.objects.order_by('-id'),
                    to_attr='latest_coffee_queue'
                )
            )
    
    @staticmethod
    def get_unified_queue_data_optimized():
        """
        獲取統一隊列數據（優化版）
        批量處理所有查詢，減少數據庫往返
        """
        try:
            # 1. 批量獲取所有隊列數據
            waiting_queues = QueryOptimizer.get_waiting_queues()
            preparing_queues = QueryOptimizer.get_preparing_queues()
            ready_orders = QueryOptimizer.get_ready_orders()
            completed_orders = QueryOptimizer.get_completed_orders()
            
            # 2. 收集所有訂單ID用於批量查詢
            all_order_ids = set()
            
            # 等待隊列訂單ID
            for queue_item in waiting_queues:
                if queue_item.order_id:
                    all_order_ids.add(queue_item.order_id)
            
            # 製作中隊列訂單ID
            for queue_item in preparing_queues:
                if queue_item.order_id:
                    all_order_ids.add(queue_item.order_id)
            
            # 就緒訂單ID
            for order in ready_orders:
                all_order_ids.add(order.id)
            
            # 已完成訂單ID
            for order in completed_orders:
                all_order_ids.add(order.id)
            
            # 3. 批量獲取所有 CoffeeQueue 數據
            coffee_queue_map = QueryOptimizer.get_coffee_queue_map(list(all_order_ids))
            
            return {
                'waiting_queues': waiting_queues,
                'preparing_queues': preparing_queues,
                'ready_orders': ready_orders,
                'completed_orders': completed_orders,
                'coffee_queue_map': coffee_queue_map,
                'total_orders': len(all_order_ids),
            }
            
        except Exception as e:
            logger.error(f"獲取統一隊列數據（優化版）失敗: {str(e)}", exc_info=True)
            return {
                'waiting_queues': CoffeeQueue.objects.none(),
                'preparing_queues': CoffeeQueue.objects.none(),
                'ready_orders': OrderModel.objects.none(),
                'completed_orders': OrderModel.objects.none(),
                'coffee_queue_map': {},
                'total_orders': 0,
            }


class BatchOrderProcessor:
    """批量訂單處理器 - 減少數據庫查詢"""
    
    @staticmethod
    def prepare_orders_batch(orders, include_queue_info=True, now=None, hk_tz=None):
        """
        批量處理訂單數據
        
        參數:
            orders: 訂單對象列表
            include_queue_info: 是否包含隊列信息
            now: 當前時間
            hk_tz: 香港時區
            
        返回:
            訂單數據列表
        """
        from eshop.utils.order_item_processor import OrderItemProcessor
        
        if not orders:
            return []
        
        # 批量獲取所有相關數據
        order_ids = [order.id for order in orders]
        
        # 批量查詢 CoffeeQueue 數據
        coffee_queue_map = QueryOptimizer.get_coffee_queue_map(order_ids)
        
        # 批量處理訂單
        results = []
        for order in orders:
            queue_item = coffee_queue_map.get(order.id) if include_queue_info else None
            order_data = OrderItemProcessor.prepare_order_data(
                order, 
                queue_item=queue_item,
                now=now,
                hk_tz=hk_tz,
                include_queue_info=include_queue_info
            )
            if order_data:
                results.append(order_data)
        
        return results
    
    @staticmethod
    def prepare_ready_orders_batch(orders, now=None, hk_tz=None):
        """
        批量處理就緒訂單數據
        
        參數:
            orders: 就緒訂單對象列表
            now: 當前時間
            hk_tz: 香港時區
            
        返回:
            就緒訂單數據列表
        """
        from eshop.utils.order_item_processor import OrderItemProcessor
        
        if not orders:
            return []
        
        # 批量獲取所有相關數據
        order_ids = [order.id for order in orders]
        coffee_queue_map = QueryOptimizer.get_coffee_queue_map(order_ids)
        
        # 批量處理訂單
        results = []
        for order in orders:
            # 純咖啡豆訂單不顯示咖啡師（現貨商品）
            items = order.get_items()
            is_beans_only = all(item.get('type') == 'bean' for item in items) if items else False
            
            # 使用基礎處理器準備數據
            order_data = OrderItemProcessor.prepare_order_data(
                order, 
                now=now, 
                hk_tz=hk_tz,
                include_queue_info=False
            )
            
            if not order_data:
                continue
            
            # 添加咖啡師信息
            if is_beans_only:
                order_data['barista'] = ''
            else:
                queue_item = coffee_queue_map.get(order.id)
                order_data['barista'] = queue_item.barista if queue_item and queue_item.barista else '未分配'
            
            # 添加就緒時間信息
            if order.ready_at and hk_tz:
                from django.utils import timezone
                ready_time = order.ready_at
                if ready_time.tzinfo is None:
                    ready_time = timezone.make_aware(ready_time)
                ready_at_hk = ready_time.astimezone(hk_tz)
                
                order_data['ready_at'] = ready_at_hk.isoformat()
                order_data['completed_time'] = ready_at_hk.strftime('%H:%M')
                
                # 計算等待時間
                if now and not is_beans_only:
                    wait_seconds = (now - ready_at_hk).total_seconds()
                    wait_minutes = int(wait_seconds / 60)
                    order_data['wait_minutes'] = wait_minutes
                    order_data['wait_display'] = f"{wait_minutes}分鐘前" if wait_minutes > 0 else "刚刚"
            
            results.append(order_data)
        
        # 按就緒時間排序
        results.sort(key=lambda x: x.get('ready_at') or '', reverse=True)
        return results


class CacheManager:
    """緩存管理器 - 管理查詢緩存"""
    
    @staticmethod
    def get_cache_key(prefix, **kwargs):
        """生成緩存鍵"""
        key_parts = [prefix]
        for key, value in sorted(kwargs.items()):
            if value is not None:
                key_parts.append(f"{key}:{value}")
        return ":".join(key_parts)
    
    @staticmethod
    def get_cached_data(cache_key, get_data_func, timeout=30):
        """
        獲取緩存數據
        
        參數:
            cache_key: 緩存鍵
            get_data_func: 獲取數據的函數
            timeout: 緩存超時時間（秒）
            
        返回:
            緩存數據
        """
        from django.core.cache import cache
        
        data = cache.get(cache_key)
        if data is None:
            data = get_data_func()
            if data is not None:
                cache.set(cache_key, data, timeout)
        return data
    
    @staticmethod
    def invalidate_cache(prefix):
        """
        使緩存失效
        
        參數:
            prefix: 緩存鍵前綴
        """
        from django.core.cache import cache
        
        # 簡單實現：清除所有以該前綴開頭的緩存
        # 在生產環境中可能需要更複雜的緩存失效策略
        cache.delete_pattern(f"{prefix}:*")


# 簡化函數接口
def get_optimized_waiting_queues():
    """簡化接口：獲取優化的等待隊列"""
    return QueryOptimizer.get_waiting_queues()


def get_optimized_preparing_queues():
    """簡化接口：獲取優化的製作中隊列"""
    return QueryOptimizer.get_preparing_queues()


def get_optimized_ready_orders():
    """簡化接口：獲取優化的就緒訂單"""
    return QueryOptimizer.get_ready_orders()


def get_optimized_completed_orders(hours=4):
    """簡化接口：獲取優化的已完成訂單"""
    return QueryOptimizer.get_completed_orders(hours)


def batch_prepare_orders(orders, **kwargs):
    """簡化接口：批量處理訂單"""
    return BatchOrderProcessor.prepare_orders_batch(orders, **kwargs)


def batch_prepare_ready_orders(orders, **kwargs):
    """簡化接口：批量處理就緒訂單"""
    return BatchOrderProcessor.prepare_ready_orders_batch(orders, **kwargs)