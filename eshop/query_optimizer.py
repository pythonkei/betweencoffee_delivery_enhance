# eshop/query_optimizer.py
"""
数据库查询优化器
缓存常用查询，减少数据库负载
"""
import logging
from eshop.utils.cache_optimizer import cache_optimizer

logger = logging.getLogger(__name__)


# 使用新的缓存优化器
cached_query = cache_optimizer.optimized_cached_query


class QueryOptimizer:
    """查询优化器"""
    
    # 缓存配置
    CACHE_TIMEOUTS = {
        'queue_summary': 30,  # 30秒
        'active_orders': 15,  # 15秒
        'order_status': 10,   # 10秒
        'quick_orders': 30,   # 30秒
    }
    
    @classmethod
    @cached_query('queue_summary', timeout=30)
    def get_queue_summary_cached(cls):
        """缓存的队列摘要"""
        from .models import CoffeeQueue
        from .queue_manager_refactored import CoffeeQueueManager
        
        queue_manager = CoffeeQueueManager()
        return queue_manager.get_queue_summary()
    
    @classmethod
    @cached_query('active_orders', timeout=15)
    def get_active_orders_cached(cls, user=None):
        """缓存的活动订单"""
        from .models import OrderModel
        
        query = OrderModel.objects.filter(
            payment_status='paid',
            status__in=['waiting', 'preparing', 'ready']
        ).select_related('queue_item')
        
        if user:
            query = query.filter(user=user)
        
        return list(query.order_by('-created_at')[:50])
    
    @classmethod
    @cached_query('quick_order_times', timeout=30)
    def get_quick_order_times_cached(cls):
        """缓存的快速订单时间"""
        from .time_calculation import unified_time_service
        from .models import OrderModel
        
        quick_orders = OrderModel.objects.filter(
            is_quick_order=True,
            payment_status='paid',
            status__in=['waiting', 'preparing']
        )
        
        results = {}
        for order in quick_orders:
            time_info = unified_time_service.calculate_quick_order_times(order)
            if time_info:
                results[order.id] = time_info
        
        return results
    
    @classmethod
    def invalidate_cache(cls, cache_key_prefix):
        """使缓存失效"""
        # 使用缓存优化器的方法
        return cache_optimizer.invalidate_cache(cache_key_prefix)
    
    @classmethod
    def prefetch_order_relations(cls, queryset):
        """预取订单关联关系"""
        return queryset.select_related(
            'user',
            'queue_item'
        ).prefetch_related(
            # 如果有其他关联关系，可以在这里添加
        )
    
    @classmethod
    def bulk_update_order_status(cls, order_ids, new_status):
        """批量更新订单状态（减少数据库查询）"""
        from .models import OrderModel
        from django.db import transaction
        
        with transaction.atomic():
            orders = OrderModel.objects.filter(id__in=order_ids)
            updated_count = orders.update(status=new_status)
            
            # 使相关缓存失效
            cls.invalidate_cache('active_orders')
            cls.invalidate_cache('queue_summary')
            
            logger.info(f"批量更新了 {updated_count} 个订单状态为 {new_status}")
            return updated_count

# 全局优化器实例
query_optimizer = QueryOptimizer()