# eshop/query_optimizer_refactored.py
"""
数据库查询优化器 - 使用统一错误处理框架

这个版本使用新的错误处理框架，提供：
1. 统一的错误处理
2. 标准化的响应格式
3. 详细的错误日志
4. 错误ID追踪
"""

import logging
from functools import wraps
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta

from .error_handling import (
    handle_error,
    handle_success,
    error_handler_decorator,
    handle_database_error,
    ErrorHandler
)

logger = logging.getLogger(__name__)

# 创建查询优化器的错误处理器
query_error_handler = ErrorHandler(module_name='query_optimizer')


class QueryOptimizer:
    """查询优化器 - 使用错误处理框架"""
    
    # 缓存配置
    CACHE_TIMEOUTS = {
        'queue_summary': 30,  # 30秒
        'active_orders': 15,  # 15秒
        'order_status': 10,   # 10秒
        'quick_orders': 30,   # 30秒
    }
    
    @staticmethod
    def cached_query(cache_key, timeout=None, force_refresh=False):
        """查询缓存装饰器 - 使用错误处理框架"""
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
        """缓存的队列摘要 - 使用错误处理框架"""
        try:
            from .models import CoffeeQueue
            from .queue_manager_refactored import CoffeeQueueManager
            
            queue_manager = CoffeeQueueManager()
            summary = queue_manager.get_queue_summary()
            
            return handle_success(
                operation='get_queue_summary_cached',
                data={'summary': summary},
                message='获取队列摘要成功'
            )
            
        except Exception as e:
            return handle_error(
                error=e,
                context='QueryOptimizer.get_queue_summary_cached',
                operation='get_queue_summary_cached'
            )
    
    @classmethod
    @cached_query('active_orders', timeout=15)
    def get_active_orders_cached(cls, user=None):
        """缓存的活动订单 - 使用错误处理框架"""
        try:
            from .models import OrderModel
            
            query = OrderModel.objects.filter(
                payment_status='paid',
                status__in=['waiting', 'preparing', 'ready']
            ).select_related('queue_item')
            
            if user:
                query = query.filter(user=user)
            
            orders = list(query.order_by('-created_at')[:50])
            
            return handle_success(
                operation='get_active_orders_cached',
                data={
                    'orders': orders,
                    'count': len(orders),
                    'user_provided': user is not None
                },
                message='获取活动订单成功'
            )
            
        except Exception as e:
            return handle_error(
                error=e,
                context='QueryOptimizer.get_active_orders_cached',
                operation='get_active_orders_cached',
                data={'user': str(user) if user else None}
            )
    
    @classmethod
    @cached_query('quick_order_times', timeout=30)
    def get_quick_order_times_cached(cls):
        """缓存的快速订单时间 - 使用错误处理框架"""
        try:
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
            
            return handle_success(
                operation='get_quick_order_times_cached',
                data={
                    'quick_orders': results,
                    'count': len(results)
                },
                message='获取快速订单时间成功'
            )
            
        except Exception as e:
            return handle_error(
                error=e,
                context='QueryOptimizer.get_quick_order_times_cached',
                operation='get_quick_order_times_cached'
            )
    
    @classmethod
    def invalidate_cache(cls, cache_key_prefix):
        """使缓存失效 - 使用错误处理框架"""
        try:
            keys_to_delete = []
            for key in cache.keys(f"*{cache_key_prefix}*"):
                keys_to_delete.append(key)
            
            if keys_to_delete:
                cache.delete_many(keys_to_delete)
                logger.info(f"已使缓存失效: {len(keys_to_delete)} 个键")
                
                return handle_success(
                    operation='invalidate_cache',
                    data={
                        'cache_key_prefix': cache_key_prefix,
                        'keys_deleted': keys_to_delete,
                        'count': len(keys_to_delete)
                    },
                    message=f'缓存失效成功，删除了 {len(keys_to_delete)} 个键'
                )
            else:
                return handle_success(
                    operation='invalidate_cache',
                    data={
                        'cache_key_prefix': cache_key_prefix,
                        'keys_deleted': [],
                        'count': 0
                    },
                    message='没有找到匹配的缓存键'
                )
                
        except Exception as e:
            return handle_error(
                error=e,
                context='QueryOptimizer.invalidate_cache',
                operation='invalidate_cache',
                data={'cache_key_prefix': cache_key_prefix}
            )
    
    @classmethod
    def prefetch_order_relations(cls, queryset):
        """预取订单关联关系 - 使用错误处理框架"""
        try:
            optimized_queryset = queryset.select_related(
                'user',
                'queue_item'
            ).prefetch_related(
                # 如果有其他关联关系，可以在这里添加
            )
            
            return handle_success(
                operation='prefetch_order_relations',
                data={
                    'queryset_optimized': True,
                    'select_related': ['user', 'queue_item'],
                    'prefetch_related': []
                },
                message='订单关联关系预取成功'
            )
            
        except Exception as e:
            return handle_error(
                error=e,
                context='QueryOptimizer.prefetch_order_relations',
                operation='prefetch_order_relations'
            )
    
    @classmethod
    def bulk_update_order_status(cls, order_ids, new_status):
        """批量更新订单状态（减少数据库查询）- 使用错误处理框架"""
        try:
            from .models import OrderModel
            from django.db import transaction
            
            with transaction.atomic():
                orders = OrderModel.objects.filter(id__in=order_ids)
                updated_count = orders.update(status=new_status)
                
                # 使相关缓存失效
                cls.invalidate_cache('active_orders')
                cls.invalidate_cache('queue_summary')
                
                logger.info(f"批量更新了 {updated_count} 个订单状态为 {new_status}")
                
                return handle_success(
                    operation='bulk_update_order_status',
                    data={
                        'order_ids': order_ids,
                        'new_status': new_status,
                        'updated_count': updated_count,
                        'cache_invalidated': ['active_orders', 'queue_summary']
                    },
                    message=f'批量更新了 {updated_count} 个订单状态'
                )
                
        except Exception as e:
            return handle_error(
                error=e,
                context='QueryOptimizer.bulk_update_order_status',
                operation='bulk_update_order_status',
                data={'order_ids': order_ids, 'new_status': new_status}
            )
    
    @classmethod
    def get_cache_stats(cls):
        """获取缓存统计信息 - 使用错误处理框架"""
        try:
            cache_stats = {
                'total_keys': 0,
                'query_keys': 0,
                'timeouts': cls.CACHE_TIMEOUTS.copy()
            }
            
            # 统计缓存键
            all_keys = cache.keys('*')
            if all_keys:
                cache_stats['total_keys'] = len(all_keys)
                cache_stats['query_keys'] = len([k for k in all_keys if k.startswith('query_')])
            
            return handle_success(
                operation='get_cache_stats',
                data=cache_stats,
                message='获取缓存统计信息成功'
            )
            
        except Exception as e:
            return handle_error(
                error=e,
                context='QueryOptimizer.get_cache_stats',
                operation='get_cache_stats'
            )
    
    @classmethod
    def clear_all_cache(cls):
        """清除所有缓存 - 使用错误处理框架"""
        try:
            cache.clear()
            logger.info("已清除所有缓存")
            
            return handle_success(
                operation='clear_all_cache',
                data={'cache_cleared': True},
                message='所有缓存已清除'
            )
            
        except Exception as e:
            return handle_error(
                error=e,
                context='QueryOptimizer.clear_all_cache',
                operation='clear_all_cache'
            )


# ==================== 装饰器示例 ====================

@error_handler_decorator(context='query_optimizer_example')
def example_query_function(order_ids):
    """示例查询函数 - 使用错误处理装饰器"""
    # 这里可以实现具体的查询逻辑
    return {
        'order_ids': order_ids,
        'result_count': len(order_ids),
        'status': 'success'
    }


# ==================== 兼容性包装器 ====================

def get_queue_summary_cached_compatible():
    """兼容性包装器 - 返回原始格式的队列摘要"""
    result = QueryOptimizer.get_queue_summary_cached()
    if result.get('success'):
        return result.get('data', {}).get('summary', {})
    else:
        # 返回空字典或抛出异常，根据原始行为
        return {}


def get_active_orders_cached_compatible(user=None):
    """兼容性包装器 - 返回原始格式的活动订单"""
    result = QueryOptimizer.get_active_orders_cached(user)
    if result.get('success'):
        return result.get('data', {}).get('orders', [])
    else:
        return []


# ==================== 测试函数 ====================

if __name__ == "__main__":
    """测试查询优化器模块"""
    import sys
    
    print("🔍 测试查询优化器模块 - 使用统一错误处理框架")
    print("=" * 60)
    
    # 测试错误处理
    print("1. 测试错误处理...")
    # 模拟一个错误情况
    try:
        # 这里可以模拟一个错误
        raise ValueError("测试错误")
    except Exception as e:
        error_result = handle_error(
            error=e,
            context='test_error_handling',
            operation='test_error_handling',
            data={'test': 'data'}
        )
        print(f"   错误处理测试: {error_result.get('success', False)}")
        print(f"   错误ID: {error_result.get('error_id', 'N/A')}")
    
    # 测试成功处理
    print("\n2. 测试成功处理...")
    success_result = handle_success(
        operation='test_success',
        data={'test': 'data'},
        message='测试成功'
    )
    print(f"   成功处理测试: {success_result.get('success', False)}")
    print(f"   消息: {success_result.get('message', 'N/A')}")
    
    # 测试装饰器
    print("\n3. 测试装饰器...")
    decorator_result = example_query_function([1, 2, 3])
    print(f"   装饰器测试: {decorator_result.get('success', False)}")
    
    print("\n" + "=" * 60)
    print("✅ 查询优化器模块测试完成")
    
    sys.exit(0)


# 全局优化器实例
query_optimizer = QueryOptimizer()