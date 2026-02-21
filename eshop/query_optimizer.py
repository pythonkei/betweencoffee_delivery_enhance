# eshop/query_optimizer.py
"""
数据库查询优化器
缓存常用查询，减少数据库负载
"""
import logging
from functools import wraps
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)

class QueryOptimizer:
    """查询优化器"""
    
    # 缓存配置
    CACHE_TIMEOUTS = {
        'queue_summary': 30,  # 30秒
        'active_orders': 15,  # 15秒
        'order_status': 10,   # 10秒
        'quick_orders': 30,   # 30秒
    }
    
    @staticmethod
    def cached_query(cache_key, timeout=None, force_refresh=False):
        """查询缓存装饰器"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # 构建完整的缓存键
                full_cache_key = f"query_{cache_key}"
                if args:
                    full_cache_key += f"_{hash(str(args))}"
                if kwargs:
                    full_cache_key += f"_{hash(str(kwargs))}"
                
                # 强制刷新或缓存不存在
                if force_refresh or not cache.get(full_cache_key):
                    result = func(*args, **kwargs)
                    cache_timeout = timeout or QueryOptimizer.CACHE_TIMEOUTS.get(cache_key, 30)
                    cache.set(full_cache_key, result, cache_timeout)
                    logger.debug(f"缓存查询结果: {full_cache_key}")
                    return result
                
                # 返回缓存结果
                cached_result = cache.get(full_cache_key)
                logger.debug(f"使用缓存查询: {full_cache_key}")
                return cached_result
            return wrapper
        return decorator
    
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
        keys_to_delete = []
        for key in cache.keys(f"*{cache_key_prefix}*"):
            keys_to_delete.append(key)
        
        if keys_to_delete:
            cache.delete_many(keys_to_delete)
            logger.info(f"已使缓存失效: {len(keys_to_delete)} 个键")
    
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