"""
時間計算常量定義
"""

import pytz

class TimeConstants:
    """時間相關常量"""
    
    # 時區
    HONG_KONG_TZ = pytz.timezone('Asia/Hong_Kong')
    UTC_TZ = pytz.UTC
    
    # 製作時間配置
    PREPARATION_BASE_MINUTES = 5      # 第一杯基礎時間
    PREPARATION_ADDITIONAL_PER_CUP = 3  # 每增加一杯額外時間
    MAX_CONCURRENT_CUPS = 3           # 最大並發製作杯數
    
    # 快速訂單時間映射
    QUICK_ORDER_TIME_MAP = {
        '5': 5,   # 5分鐘後
        '10': 10, # 10分鐘後
        '15': 15, # 15分鐘後
        '20': 20, # 20分鐘後
        '30': 30, # 30分鐘後
    }
    
    # 緩衝時間（分鐘）
    BUFFER_MINUTES = 2                # 製作緩衝時間
    URGENT_BUFFER_MINUTES = 5         # 緊急訂單緩衝時間
    
    # 時間格式化字符串
    TIME_FORMAT_FULL = '%Y-%m-%d %H:%M'
    TIME_FORMAT_TIME_ONLY = '%H:%M'
    TIME_FORMAT_DATE_ONLY = '%Y-%m-%d'
    TIME_FORMAT_ISO = '%Y-%m-%dT%H:%M:%S%z'
    
    # 相對時間閾值（秒）
    RELATIVE_JUST_NOW = 60            # 剛剛（1分鐘內）
    RELATIVE_MINUTES = 3600           # 分鐘（1小時內）
    RELATIVE_HOURS = 86400            # 小時（1天內）
    
    # 隊列相關
    DEFAULT_AVG_PREPARATION_TIME = 5  # 默認平均製作時間（分鐘）
    MAX_QUEUE_POSITION = 100          # 最大隊列位置
    
    @classmethod
    def get_preparation_time_config(cls):
        """獲取製作時間配置"""
        return {
            'base_minutes': cls.PREPARATION_BASE_MINUTES,
            'additional_per_cup': cls.PREPARATION_ADDITIONAL_PER_CUP,
            'max_concurrent': cls.MAX_CONCURRENT_CUPS,
        }
    
    @classmethod
    def get_quick_order_minutes(cls, choice):
        """獲取快速訂單分鐘數"""
        return cls.QUICK_ORDER_TIME_MAP.get(choice, 5)
    
    @classmethod
    def get_quick_order_display(cls, choice):
        """獲取快速訂單顯示文本"""
        display_map = {
            '5': '5分鐘後',
            '10': '10分鐘後',
            '15': '15分鐘後',
            '20': '20分鐘後',
            '30': '30分鐘後',
        }
        return display_map.get(choice, '5分鐘後')