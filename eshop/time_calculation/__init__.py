"""
統一時間計算模組

提供統一的時間計算、格式化和驗證服務，
取代分散在各處的時間計算邏輯。
"""

from .unified_time_service import UnifiedTimeService
from .time_calculators import TimeCalculators
from .time_formatters import TimeFormatters
from .time_validators import TimeValidators
from .constants import TimeConstants

__all__ = [
    'UnifiedTimeService',
    'TimeCalculators',
    'TimeFormatters',
    'TimeValidators',
    'TimeConstants',
]

# 創建全局實例
unified_time_service = UnifiedTimeService()