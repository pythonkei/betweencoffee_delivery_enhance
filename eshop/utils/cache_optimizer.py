# eshop/utils/cache_optimizer.py
"""
緩存優化器 - 修復緩存性能問題
"""
import logging
from functools import wraps
from django.core.cache import cache
from django.utils import timezone

logger = logging.getLogger(__name__)


class CacheOptimizer:
    """緩存優化器"""
    
    # 緩存配置
    CACHE_CONFIG = {
        'queue_summary': {'timeout': 30, 'version': 1},
        'active_orders': {'timeout': 15, 'version': 1},
        'order_status': {'timeout': 10, 'version': 1},
        'quick_orders': {'timeout': 30, 'version': 1},
        'user_orders': {'timeout': 60, 'version': 1},
    }
    
    @staticmethod
    def optimized_cached_query(cache_key, timeout=None, version=None):
        """優化的緩存裝飾器"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # 獲取緩存配置
                config = CacheOptimizer.CACHE_CONFIG.get(cache_key, {})
                cache_timeout = timeout or config.get('timeout', 30)
                cache_version = version or config.get('version', 1)
                
                # 構建簡單的緩存鍵
                cache_key_simple = f"opt_cache_{cache_key}_v{cache_version}"
                
                # 檢查緩存
                cached_result = cache.get(cache_key_simple)
                if cached_result is not None:
                    logger.debug(f"✅ 使用優化緩存: {cache_key_simple}")
                    return cached_result
                
                # 執行查詢
                logger.debug(f"🔄 執行查詢並緩存: {cache_key_simple}")
                result = func(*args, **kwargs)
                
                # 緩存結果
                cache.set(cache_key_simple, result, cache_timeout)
                return result
            return wrapper
        return decorator
    
    @staticmethod
    def smart_cached_query(cache_key, timeout=30, min_result_size=1):
        """智能緩存裝飾器 - 只緩存有意義的結果"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                cache_key_full = f"smart_{cache_key}"
                
                # 檢查緩存
                cached_result = cache.get(cache_key_full)
                if cached_result is not None:
                    return cached_result
                
                # 執行查詢
                result = func(*args, **kwargs)
                
                # 只緩存有意義的結果
                should_cache = True
                
                # 檢查結果大小
                if isinstance(result, (list, tuple, dict, set)):
                    if len(result) < min_result_size:
                        should_cache = False
                        logger.debug(f"⚠️ 結果太小({len(result)})，不緩存: {cache_key_full}")
                
                # 檢查結果是否為空
                if result is None or result == [] or result == {}:
                    should_cache = False
                    logger.debug(f"⚠️ 結果為空，不緩存: {cache_key_full}")
                
                # 緩存結果
                if should_cache:
                    cache.set(cache_key_full, result, timeout)
                    logger.debug(f"✅ 緩存結果: {cache_key_full} (大小: {len(result) if hasattr(result, '__len__') else 'N/A'})")
                
                return result
            return wrapper
        return decorator
    
    @classmethod
    def invalidate_cache(cls, cache_key_prefix):
        """使緩存失效"""
        from django.core.cache import caches
        
        try:
            # 嘗試使用keys方法（Redis支持）
            cache_backend = caches['default']
            if hasattr(cache_backend, 'keys'):
                keys = cache_backend.keys(f"*{cache_key_prefix}*")
                if keys:
                    cache_backend.delete_many(keys)
                    logger.info(f"✅ 已使緩存失效: {len(keys)} 個鍵")
                    return len(keys)
        except Exception as e:
            logger.warning(f"⚠️ 無法使用keys方法清理緩存: {str(e)}")
        
        # 回退方案：使用版本控制
        for cache_name, config in cls.CACHE_CONFIG.items():
            if cache_key_prefix in cache_name:
                config['version'] = config.get('version', 1) + 1
                logger.info(f"✅ 更新緩存版本: {cache_name} -> v{config['version']}")
        
        return 0
    
    @classmethod
    def get_cache_stats(cls):
        """獲取緩存統計"""
        stats = {
            'configs': len(cls.CACHE_CONFIG),
            'total_hits': 0,
            'total_misses': 0,
            'timestamp': timezone.now().isoformat(),
        }
        
        # 這裡可以添加緩存命中率統計
        # 實際項目中可以集成django-debug-toolbar或自定義中間件
        
        return stats
    
    @classmethod
    def clear_all_cache(cls):
        """清除所有緩存"""
        cache.clear()
        logger.info("✅ 已清除所有緩存")
        return True


# 全局緩存優化器實例
cache_optimizer = CacheOptimizer()


# 兼容性裝飾器
def cached_query(cache_key, timeout=None, force_refresh=False):
    """兼容舊版本的緩存裝飾器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 使用優化版本
            return CacheOptimizer.optimized_cached_query(cache_key, timeout)(func)(*args, **kwargs)
        return wrapper
    return decorator