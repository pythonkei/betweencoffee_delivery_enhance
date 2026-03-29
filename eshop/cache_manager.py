"""
緩存管理器 - 階段2數據庫優化
管理查詢緩存，減少數據庫訪問
"""

import logging
from typing import Any, Callable, Optional
from datetime import timedelta

from django.core.cache import cache
from django.utils import timezone

logger = logging.getLogger(__name__)


class CacheManager:
    """緩存管理器 - 統一管理所有緩存操作"""
    
    # 緩存前綴
    CACHE_PREFIXES = {
        'queue_data': 'queue:data',
        'waiting_queues': 'queue:waiting',
        'preparing_queues': 'queue:preparing',
        'ready_orders': 'queue:ready',
        'completed_orders': 'queue:completed',
        'order_details': 'order:details',
        'performance_stats': 'perf:stats',
    }
    
    # 默認緩存時間（秒）
    DEFAULT_TIMEOUTS = {
        'queue_data': 15,  # 隊列數據變化頻繁，緩存時間較短
        'waiting_queues': 10,
        'preparing_queues': 10,
        'ready_orders': 10,
        'completed_orders': 30,  # 已完成訂單變化較少，緩存時間較長
        'order_details': 60,
        'performance_stats': 300,  # 性能統計變化較少
    }
    
    @staticmethod
    def get_cache_key(prefix: str, **kwargs) -> str:
        """
        生成緩存鍵
        
        參數:
            prefix: 緩存前綴
            **kwargs: 緩存參數
            
        返回:
            緩存鍵字符串
        """
        key_parts = [prefix]
        for key, value in sorted(kwargs.items()):
            if value is not None:
                key_parts.append(f"{key}:{value}")
        return ":".join(key_parts)
    
    @staticmethod
    def get_cached_data(
        cache_key: str,
        get_data_func: Callable[[], Any],
        timeout: Optional[int] = None,
        force_refresh: bool = False
    ) -> Any:
        """
        獲取緩存數據
        
        參數:
            cache_key: 緩存鍵
            get_data_func: 獲取數據的函數
            timeout: 緩存超時時間（秒），None則使用默認值
            force_refresh: 是否強制刷新緩存
            
        返回:
            緩存數據
        """
        # 如果強制刷新，直接獲取新數據
        if force_refresh:
            data = get_data_func()
            if data is not None:
                cache.set(cache_key, data, timeout or 30)
            return data
        
        # 嘗試從緩存獲取數據
        data = cache.get(cache_key)
        if data is not None:
            logger.debug(f"緩存命中: {cache_key}")
            return data
        
        # 緩存未命中，獲取新數據
        logger.debug(f"緩存未命中: {cache_key}")
        data = get_data_func()
        if data is not None:
            cache.set(cache_key, data, timeout or 30)
        
        return data
    
    @staticmethod
    def get_cached_queue_data(
        cache_type: str,
        get_data_func: Callable[[], Any],
        **kwargs
    ) -> Any:
        """
        獲取緩存的隊列數據
        
        參數:
            cache_type: 緩存類型（queue_data, waiting_queues等）
            get_data_func: 獲取數據的函數
            **kwargs: 緩存參數
            
        返回:
            緩存數據
        """
        if cache_type not in CacheManager.CACHE_PREFIXES:
            logger.warning(f"未知的緩存類型: {cache_type}")
            return get_data_func()
        
        prefix = CacheManager.CACHE_PREFIXES[cache_type]
        timeout = CacheManager.DEFAULT_TIMEOUTS.get(cache_type, 30)
        cache_key = CacheManager.get_cache_key(prefix, **kwargs)
        
        return CacheManager.get_cached_data(
            cache_key,
            get_data_func,
            timeout=timeout
        )
    
    @staticmethod
    def invalidate_cache(cache_type: str, **kwargs) -> bool:
        """
        使緩存失效
        
        參數:
            cache_type: 緩存類型
            **kwargs: 緩存參數
            
        返回:
            是否成功
        """
        try:
            if cache_type not in CacheManager.CACHE_PREFIXES:
                logger.warning(f"未知的緩存類型: {cache_type}")
                return False
            
            prefix = CacheManager.CACHE_PREFIXES[cache_type]
            cache_key = CacheManager.get_cache_key(prefix, **kwargs)
            
            # 刪除特定緩存鍵
            deleted = cache.delete(cache_key)
            
            # 如果刪除了緩存，同時刪除相關的隊列緩存
            if deleted and cache_type.startswith('queue'):
                CacheManager.invalidate_all_queue_caches()
            
            logger.info(f"緩存失效: {cache_key} (成功: {deleted})")
            return deleted
            
        except Exception as e:
            logger.error(f"使緩存失效失敗: {str(e)}")
            return False
    
    @staticmethod
    def invalidate_all_queue_caches() -> bool:
        """
        使所有隊列相關緩存失效
        
        返回:
            是否成功
        """
        try:
            deleted_count = 0
            
            # 刪除所有隊列相關緩存
            for cache_type in ['queue_data', 'waiting_queues', 'preparing_queues', 'ready_orders', 'completed_orders']:
                prefix = CacheManager.CACHE_PREFIXES[cache_type]
                
                # 簡單實現：刪除所有以該前綴開頭的緩存
                # 注意：這在生產環境中可能需要更高效的實現
                cache.delete_pattern(f"{prefix}:*")
                deleted_count += 1
            
            logger.info(f"所有隊列緩存已失效，共 {deleted_count} 種類型")
            return True
            
        except Exception as e:
            logger.error(f"使所有隊列緩存失效失敗: {str(e)}")
            return False
    
    @staticmethod
    def invalidate_order_caches(order_id: int) -> bool:
        """
        使訂單相關緩存失效
        
        參數:
            order_id: 訂單ID
            
        返回:
            是否成功
        """
        try:
            deleted_count = 0
            
            # 使訂單詳細信息緩存失效
            cache_key = CacheManager.get_cache_key(
                CacheManager.CACHE_PREFIXES['order_details'],
                order_id=order_id
            )
            if cache.delete(cache_key):
                deleted_count += 1
            
            # 使所有隊列緩存失效（因為訂單狀態變化會影響隊列）
            CacheManager.invalidate_all_queue_caches()
            deleted_count += 1
            
            logger.info(f"訂單 #{order_id} 相關緩存已失效，共 {deleted_count} 個緩存")
            return True
            
        except Exception as e:
            logger.error(f"使訂單 #{order_id} 緩存失效失敗: {str(e)}")
            return False
    
    @staticmethod
    def get_cache_stats() -> dict:
        """
        獲取緩存統計信息
        
        返回:
            緩存統計字典
        """
        try:
            # 簡單的緩存統計
            stats = {
                'total_cache_types': len(CacheManager.CACHE_PREFIXES),
                'default_timeouts': CacheManager.DEFAULT_TIMEOUTS.copy(),
                'timestamp': timezone.now().isoformat(),
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"獲取緩存統計失敗: {str(e)}")
            return {
                'error': str(e),
                'timestamp': timezone.now().isoformat(),
            }
    
    @staticmethod
    def clear_all_caches() -> dict:
        """
        清除所有緩存
        
        返回:
            清除結果
        """
        try:
            # 清除所有緩存
            cache.clear()
            
            result = {
                'success': True,
                'message': '所有緩存已清除',
                'timestamp': timezone.now().isoformat(),
            }
            
            logger.info("所有緩存已清除")
            return result
            
        except Exception as e:
            logger.error(f"清除所有緩存失敗: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': timezone.now().isoformat(),
            }


# 裝飾器函數
def cache_queue_data(timeout: Optional[int] = None):
    """
    隊列數據緩存裝飾器
    
    參數:
        timeout: 緩存超時時間（秒）
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            from eshop.cache_manager import CacheManager
            
            # 生成緩存鍵
            cache_key = CacheManager.get_cache_key(
                CacheManager.CACHE_PREFIXES['queue_data'],
                func_name=func.__name__,
                **kwargs
            )
            
            # 獲取緩存數據
            return CacheManager.get_cached_data(
                cache_key,
                lambda: func(*args, **kwargs),
                timeout=timeout or CacheManager.DEFAULT_TIMEOUTS['queue_data']
            )
        return wrapper
    return decorator


def cache_order_details(timeout: Optional[int] = None):
    """
    訂單詳細信息緩存裝飾器
    
    參數:
        timeout: 緩存超時時間（秒）
    """
    def decorator(func):
        def wrapper(order_id, *args, **kwargs):
            from eshop.cache_manager import CacheManager
            
            # 生成緩存鍵
            cache_key = CacheManager.get_cache_key(
                CacheManager.CACHE_PREFIXES['order_details'],
                order_id=order_id
            )
            
            # 獲取緩存數據
            return CacheManager.get_cached_data(
                cache_key,
                lambda: func(order_id, *args, **kwargs),
                timeout=timeout or CacheManager.DEFAULT_TIMEOUTS['order_details']
            )
        return wrapper
    return decorator


# 簡化函數接口
def get_cached_queue_data(cache_type, get_data_func, **kwargs):
    """簡化接口：獲取緩存的隊列數據"""
    return CacheManager.get_cached_queue_data(cache_type, get_data_func, **kwargs)


def invalidate_queue_caches():
    """簡化接口：使隊列緩存失效"""
    return CacheManager.invalidate_all_queue_caches()


def invalidate_order_cache(order_id):
    """簡化接口：使訂單緩存失效"""
    return CacheManager.invalidate_order_caches(order_id)


def get_cache_statistics():
    """簡化接口：獲取緩存統計"""
    return CacheManager.get_cache_stats()


def clear_caches():
    """簡化接口：清除所有緩存"""
    return CacheManager.clear_all_caches()