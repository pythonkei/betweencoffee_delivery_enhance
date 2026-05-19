"""
Django 緩存配置模組
提供統一的緩存策略和性能優化工具
"""

import logging

from django.core.cache import cache

logger = logging.getLogger(__name__)


class CacheManager:
    """緩存管理器 - 提供統一的緩存策略"""
    
    # 緩存鍵前綴
    PREFIXES = {
        'queue': 'queue:',
        'order': 'order:',
        'badge': 'badge:',
        'unified_data': 'unified_data:',
        'menu': 'menu:',
        'user': 'user:',
    }
    
    # 默認緩存時間（秒）
    DEFAULT_TIMEOUTS = {
        'queue': 30,           # 隊列數據：30秒
        'order': 60,           # 訂單詳情：60秒
        'badge': 15,           # 徽章數據：15秒
        'unified_data': 10,    # 統一數據：10秒
        'menu': 300,           # 菜單數據：5分鐘
        'user': 1800,          # 用戶數據：30分鐘
    }
    
    @classmethod
    def get_key(cls, prefix, identifier):
        """生成緩存鍵"""
        if prefix not in cls.PREFIXES:
            raise ValueError(f"未知的緩存前綴: {prefix}")
        
        return f"{cls.PREFIXES[prefix]}{identifier}"
    
    @classmethod
    def get_timeout(cls, cache_type):
        """獲取緩存超時時間"""
        return cls.DEFAULT_TIMEOUTS.get(cache_type, 60)
    
    @classmethod
    def set(cls, prefix, identifier, value, timeout=None):
        """設置緩存值"""
        try:
            key = cls.get_key(prefix, identifier)
            actual_timeout = timeout or cls.get_timeout(prefix)
            
            cache.set(key, value, actual_timeout)
            logger.debug(f"緩存設置: {key} (超時: {actual_timeout}s)")
            
            # 記錄性能監控
            try:
                from eshop.performance_monitor import cache_monitor
                cache_monitor.increment_cache_set()
            except ImportError:
                pass
                
            return True
        except Exception as e:
            logger.error(f"設置緩存失敗: {e}")
            return False
    
    @classmethod
    def get(cls, prefix, identifier, default=None):
        """獲取緩存值"""
        try:
            key = cls.get_key(prefix, identifier)
            value = cache.get(key)
            
            if value is None:
                logger.debug(f"緩存未命中: {key}")
                # 記錄緩存未命中
                try:
                    from eshop.performance_monitor import cache_monitor
                    cache_monitor.increment_cache_miss()
                except ImportError:
                    pass
            else:
                logger.debug(f"緩存命中: {key}")
                # 記錄緩存命中
                try:
                    from eshop.performance_monitor import cache_monitor
                    cache_monitor.increment_cache_hit()
                except ImportError:
                    pass
            
            return value if value is not None else default
        except Exception as e:
            logger.error(f"獲取緩存失敗: {e}")
            return default
    
    @classmethod
    def delete(cls, prefix, identifier):
        """刪除緩存值"""
        try:
            key = cls.get_key(prefix, identifier)
            cache.delete(key)
            logger.debug(f"緩存刪除: {key}")
            
            # 記錄性能監控
            try:
                from eshop.performance_monitor import cache_monitor
                cache_monitor.increment_cache_delete()
            except ImportError:
                pass
                
            return True
        except Exception as e:
            logger.error(f"刪除緩存失敗: {e}")
            return False
    
    @classmethod
    def invalidate_queue_data(cls):
        """使隊列相關緩存失效"""
        try:
            # 刪除所有隊列相關緩存
            keys_to_delete = [
                cls.get_key('queue', '*'),
                cls.get_key('unified_data', '*'),
                cls.get_key('badge', '*'),
            ]
            
            for pattern in keys_to_delete:
                # 注意：Django緩存不支持通配符刪除，需要手動管理
                # 這裡我們使用一個特殊的鍵來標記緩存版本
                cache.delete('queue_cache_version')
            
            logger.info("隊列緩存已失效")
            return True
        except Exception as e:
            logger.error(f"失效隊列緩存失敗: {e}")
            return False
    
    @classmethod
    def get_or_set(cls, prefix, identifier, callback, timeout=None):
        """獲取或設置緩存值（如果不存在）"""
        try:
            value = cls.get(prefix, identifier)
            if value is None:
                value = callback()
                cls.set(prefix, identifier, value, timeout)
                logger.debug(f"緩存回調設置: {cls.get_key(prefix, identifier)}")
            return value
        except Exception as e:
            logger.error(f"獲取或設置緩存失敗: {e}")
            return callback() if callable(callback) else None


class QueryCacheMixin:
    """查詢緩存混合類 - 用於模型查詢緩存"""
    
    @classmethod
    def get_cached_queryset(cls, cache_key, queryset_func, timeout=60):
        """獲取緩存的查詢集"""
        try:
            # 嘗試從緩存獲取
            cached_data = cache.get(cache_key)
            if cached_data is not None:
                logger.debug(f"查詢集緩存命中: {cache_key}")
                return cached_data
            
            # 執行查詢函數
            result = queryset_func()
            
            # 緩存結果
            cache.set(cache_key, result, timeout)
            logger.debug(f"查詢集緩存設置: {cache_key} (超時: {timeout}s)")
            
            return result
        except Exception as e:
            logger.error(f"查詢集緩存失敗: {e}")
            return queryset_func()
    
    @classmethod
    def invalidate_cached_queryset(cls, cache_key):
        """使查詢集緩存失效"""
        try:
            cache.delete(cache_key)
            logger.debug(f"查詢集緩存失效: {cache_key}")
            return True
        except Exception as e:
            logger.error(f"失效查詢集緩存失敗: {e}")
            return False


class PerformanceMonitor:
    """性能監控器 - 用於跟踪緩存命中率和性能"""
    
    def __init__(self):
        self.stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0,
            'errors': 0,
        }
    
    def record_hit(self):
        """記錄緩存命中"""
        self.stats['hits'] += 1
    
    def record_miss(self):
        """記錄緩存未命中"""
        self.stats['misses'] += 1
    
    def record_set(self):
        """記錄緩存設置"""
        self.stats['sets'] += 1
    
    def record_delete(self):
        """記錄緩存刪除"""
        self.stats['deletes'] += 1
    
    def record_error(self):
        """記錄緩存錯誤"""
        self.stats['errors'] += 1
    
    def get_hit_rate(self):
        """獲取緩存命中率"""
        total = self.stats['hits'] + self.stats['misses']
        if total == 0:
            return 0.0
        return self.stats['hits'] / total * 100
    
    def get_stats(self):
        """獲取統計信息"""
        return {
            **self.stats,
            'hit_rate': self.get_hit_rate(),
            'total_operations': sum(self.stats.values()),
        }
    
    def reset_stats(self):
        """重置統計信息"""
        self.stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0,
            'errors': 0,
        }


# 全局性能監控器實例
performance_monitor = PerformanceMonitor()


def cache_decorator(prefix, timeout=None):
    """緩存裝飾器 - 用於函數結果緩存"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # 生成緩存鍵
            import hashlib
            import json

            # 基於函數名和參數生成唯一鍵
            key_parts = [
                func.__module__,
                func.__name__,
                str(args),
                str(sorted(kwargs.items()))
            ]
            key_string = json.dumps(key_parts, sort_keys=True)
            key_hash = hashlib.md5(key_string.encode()).hexdigest()
            
            cache_key = CacheManager.get_key(prefix, key_hash)
            
            # 嘗試從緩存獲取
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                performance_monitor.record_hit()
                logger.debug(f"裝飾器緩存命中: {cache_key}")
                return cached_result
            
            # 執行函數
            performance_monitor.record_miss()
            result = func(*args, **kwargs)
            
            # 緩存結果
            actual_timeout = timeout or CacheManager.get_timeout(prefix)
            cache.set(cache_key, result, actual_timeout)
            performance_monitor.record_set()
            logger.debug(f"裝飾器緩存設置: {cache_key} (超時: {actual_timeout}s)")
            
            return result
        return wrapper
    return decorator


# 緩存配置檢查
def check_cache_config():
    """檢查緩存配置"""
    try:
        # 測試緩存連接
        test_key = 'cache_config_test'
        test_value = 'test_value'
        
        cache.set(test_key, test_value, 10)
        retrieved_value = cache.get(test_key)
        
        if retrieved_value == test_value:
            logger.info("✅ 緩存配置正常")
            return True
        else:
            logger.warning("⚠️ 緩存配置測試失敗")
            return False
    except Exception as e:
        logger.error(f"❌ 緩存配置檢查失敗: {e}")
        return False