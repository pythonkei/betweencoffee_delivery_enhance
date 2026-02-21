"""
共用工具模塊 - 提取重複的業務邏輯和工具函數

這個模塊包含：
1. 時間相關工具函數
2. 錯誤處理快捷函數
3. 數據驗證和轉換函數
4. 其他共用業務邏輯
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional, List, Union
import pytz

from django.http import JsonResponse
from django.utils import timezone

# 導入統一的錯誤處理和API響應
from eshop.error_handling import handle_error, handle_success, ErrorHandler
from core.api_response import ApiResponse, api_success, api_error

logger = logging.getLogger(__name__)


class CommonUtils:
    """共用工具類"""
    
    # 香港時區
    HONG_KONG_TZ = pytz.timezone('Asia/Hong_Kong')
    
    @staticmethod
    def get_hong_kong_time() -> datetime:
        """
        獲取香港當前時間 - 統一入口
        
        返回:
            香港當前時間
        """
        try:
            # 優先使用統一的時間服務
            from eshop.time_calculation import unified_time_service
            return unified_time_service.get_hong_kong_time()
        except ImportError:
            # 備用方案
            return datetime.now(CommonUtils.HONG_KONG_TZ)
    
    @staticmethod
    def format_time_for_display(dt: datetime) -> str:
        """
        格式化時間為顯示格式 (HH:MM)
        
        參數:
            dt: 日期時間對象
            
        返回:
            格式化後的時間字符串
        """
        if not dt:
            return '--:--'
        
        try:
            if dt.tzinfo is None:
                dt = pytz.UTC.localize(dt)
            dt_local = dt.astimezone(CommonUtils.HONG_KONG_TZ)
            return dt_local.strftime('%H:%M')
        except Exception as e:
            logger.error(f"時間格式化失敗: {str(e)}")
            return '--:--'
    
    @staticmethod
    def format_datetime_for_display(dt: datetime) -> str:
        """
        格式化日期時間為顯示格式 (YYYY-MM-DD HH:MM)
        
        參數:
            dt: 日期時間對象
            
        返回:
            格式化後的日期時間字符串
        """
        if not dt:
            return '--'
        
        try:
            if dt.tzinfo is None:
                dt = pytz.UTC.localize(dt)
            dt_local = dt.astimezone(CommonUtils.HONG_KONG_TZ)
            return dt_local.strftime('%Y-%m-%d %H:%M')
        except Exception as e:
            logger.error(f"日期時間格式化失敗: {str(e)}")
            return '--'
    
    @staticmethod
    def calculate_time_diff_minutes(start_time: datetime, end_time: datetime) -> int:
        """
        計算兩個時間之間的分鐘差
        
        參數:
            start_time: 開始時間
            end_time: 結束時間
            
        返回:
            分鐘差（整數）
        """
        if not start_time or not end_time:
            return 0
        
        try:
            # 確保時區
            if start_time.tzinfo is None:
                start_time = pytz.UTC.localize(start_time)
            if end_time.tzinfo is None:
                end_time = pytz.UTC.localize(end_time)
            
            # 轉換到相同時區
            start_utc = start_time.astimezone(pytz.UTC)
            end_utc = end_time.astimezone(pytz.UTC)
            
            diff = end_utc - start_utc
            return int(diff.total_seconds() / 60)
        except Exception as e:
            logger.error(f"計算時間差失敗: {str(e)}")
            return 0
    
    @staticmethod
    def format_minutes_to_display(minutes: int) -> str:
        """
        格式化分鐘數為可讀格式
        
        參數:
            minutes: 分鐘數
            
        返回:
            可讀的時間字符串
        """
        if minutes <= 0:
            return "立即"
        
        if minutes < 60:
            return f"{minutes}分鐘"
        else:
            hours = minutes // 60
            remaining_minutes = minutes % 60
            if remaining_minutes > 0:
                return f"{hours}小時{remaining_minutes}分鐘"
            else:
                return f"{hours}小時"
    
    @staticmethod
    def safe_get(obj, attr_path: str, default: Any = None) -> Any:
        """
        安全獲取對象屬性，避免 AttributeError
        
        參數:
            obj: 對象
            attr_path: 屬性路徑，支持點號分隔 (如 'user.profile.name')
            default: 默認值
            
        返回:
            屬性值或默認值
        """
        try:
            attrs = attr_path.split('.')
            current = obj
            for attr in attrs:
                if hasattr(current, attr):
                    current = getattr(current, attr)
                else:
                    return default
            return current
        except (AttributeError, KeyError, TypeError):
            return default
    
    @staticmethod
    def validate_required_fields(data: Dict, required_fields: List[str]) -> Dict[str, List[str]]:
        """
        驗證必需字段
        
        參數:
            data: 數據字典
            required_fields: 必需字段列表
            
        返回:
            錯誤字典 {字段名: [錯誤消息]}
        """
        errors = {}
        for field in required_fields:
            if field not in data or data[field] in (None, '', []):
                errors[field] = ["此字段為必填項"]
        
        return errors
    
    @staticmethod
    def create_api_response(success: bool, 
                           message: str, 
                           data: Any = None, 
                           error_details: Any = None,
                           status_code: int = 200) -> JsonResponse:
        """
        創建統一的API響應
        
        參數:
            success: 是否成功
            message: 消息
            data: 數據
            error_details: 錯誤詳情
            status_code: HTTP狀態碼
            
        返回:
            JsonResponse
        """
        if success:
            return api_success(data=data, message=message, status_code=status_code)
        else:
            return api_error(message=message, status_code=status_code, details=error_details)
    
    @staticmethod
    def handle_exception_as_api_response(e: Exception, 
                                        context: str = 'unknown',
                                        operation: str = 'unknown') -> JsonResponse:
        """
        將異常處理為API響應
        
        參數:
            e: 異常對象
            context: 上下文
            operation: 操作名稱
            
        返回:
            JsonResponse
        """
        # 使用錯誤處理框架
        error_result = handle_error(
            error=e,
            context=context,
            operation=operation,
            log_level='error'
        )
        
        # 轉換為API響應
        return api_error(
            message=error_result.get('message', '操作失敗'),
            status_code=500,
            details={
                'error_id': error_result.get('error_id'),
                'error_type': error_result.get('error_type'),
                'context': context,
                'operation': operation
            }
        )
    
    @staticmethod
    def serialize_order_basic(order) -> Dict[str, Any]:
        """
        序列化訂單基本信息（共用邏輯）
        
        參數:
            order: 訂單對象
            
        返回:
            序列化的訂單字典
        """
        from eshop.utils.time_formatter import TimeFormatter
        
        if not order:
            return {}
        
        try:
            return {
                'id': order.id,
                'order_number': getattr(order, 'order_number', f'#{order.id}'),
                'status': order.status,
                'payment_status': order.payment_status,
                'order_type': getattr(order, 'order_type', 'normal'),
                'total_price': float(order.total_price) if order.total_price else 0.0,
                'created_at': TimeFormatter.format_iso(order.created_at, CommonUtils.HONG_KONG_TZ),
                'created_at_display': TimeFormatter.format_for_display(order.created_at, CommonUtils.HONG_KONG_TZ),
                'ready_at': TimeFormatter.format_iso(order.ready_at, CommonUtils.HONG_KONG_TZ) if order.ready_at else None,
                'ready_at_display': TimeFormatter.format_for_display(order.ready_at, CommonUtils.HONG_KONG_TZ) if order.ready_at else None,
                'customer_name': getattr(order, 'customer_name', ''),
                'phone': getattr(order, 'phone', ''),
                'email': getattr(order, 'email', ''),
                'pickup_code': getattr(order, 'pickup_code', ''),
            }
        except Exception as e:
            logger.error(f"序列化訂單失敗: {str(e)}")
            return {
                'id': order.id if order else 0,
                'error': '序列化失敗'
            }
    
    @staticmethod
    def get_queue_stats() -> Dict[str, Any]:
        """
        獲取隊列統計信息（共用邏輯）
        
        返回:
            隊列統計字典
        """
        try:
            from eshop.models import CoffeeQueue
            
            waiting_count = CoffeeQueue.objects.filter(status='waiting').count()
            preparing_count = CoffeeQueue.objects.filter(status='preparing').count()
            ready_count = CoffeeQueue.objects.filter(status='ready').count()
            total_count = waiting_count + preparing_count + ready_count
            
            return {
                'waiting_count': waiting_count,
                'preparing_count': preparing_count,
                'ready_count': ready_count,
                'total_count': total_count,
                'timestamp': CommonUtils.get_hong_kong_time().isoformat(),
            }
        except Exception as e:
            logger.error(f"獲取隊列統計失敗: {str(e)}")
            return {
                'waiting_count': 0,
                'preparing_count': 0,
                'ready_count': 0,
                'total_count': 0,
                'error': '獲取統計失敗',
                'timestamp': CommonUtils.get_hong_kong_time().isoformat(),
            }
    
    @staticmethod
    def log_operation(module: str, operation: str, message: str, level: str = 'info', **kwargs):
        """
        統一日誌記錄
        
        參數:
            module: 模塊名稱
            operation: 操作名稱
            message: 日誌消息
            level: 日誌級別 (info, warning, error, debug)
            **kwargs: 額外數據
        """
        log_message = f"[{module}] {operation}: {message}"
        
        if kwargs:
            log_message += f" | 數據: {kwargs}"
        
        if level == 'info':
            logger.info(log_message)
        elif level == 'warning':
            logger.warning(log_message)
        elif level == 'error':
            logger.error(log_message)
        elif level == 'debug':
            logger.debug(log_message)


# 全局實例
common_utils = CommonUtils()

# 快捷函數
def get_hong_kong_time() -> datetime:
    """快捷函數：獲取香港時間"""
    return common_utils.get_hong_kong_time()

def format_time_display(dt: datetime) -> str:
    """快捷函數：格式化時間顯示"""
    return common_utils.format_time_for_display(dt)

def format_datetime_display(dt: datetime) -> str:
    """快捷函數：格式化日期時間顯示"""
    return common_utils.format_datetime_for_display(dt)

def safe_get_attr(obj, attr_path: str, default: Any = None) -> Any:
    """快捷函數：安全獲取屬性"""
    return common_utils.safe_get(obj, attr_path, default)

def api_response(success: bool, message: str, data: Any = None, **kwargs) -> JsonResponse:
    """快捷函數：創建API響應"""
    return common_utils.create_api_response(success, message, data, **kwargs)

def log_info(module: str, operation: str, message: str, **kwargs):
    """快捷函數：記錄信息日誌"""
    common_utils.log_operation(module, operation, message, 'info', **kwargs)

def log_error(module: str, operation: str, message: str, **kwargs):
    """快捷函數：記錄錯誤日誌"""
    common_utils.log_operation(module, operation, message, 'error', **kwargs)


# 測試
if __name__ == "__main__":
    print("=== 測試共用工具模塊 ===")
    
    # 測試時間函數
    hk_time = get_hong_kong_time()
    print(f"香港時間: {hk_time}")
    print(f"格式化顯示: {format_time_display(hk_time)}")
    print(f"格式化日期時間顯示: {format_datetime_display(hk_time)}")
    
    # 測試時間差計算
    from datetime import timedelta
    start = hk_time
    end = hk_time + timedelta(minutes=90)
    minutes_diff = common_utils.calculate_time_diff_minutes(start, end)
    print(f"時間差: {minutes_diff} 分鐘")
    print(f"格式化分鐘: {common_utils.format_minutes_to_display(minutes_diff)}")
    
    # 測試安全獲取屬性
    class TestObj:
        def __init__(self):
            self.user = type('User', (), {'profile': type('Profile', (), {'name': 'John'})(), 'email': 'john@example.com'})()
    
    obj = TestObj()
    print(f"安全獲取屬性: {safe_get_attr(obj, 'user.profile.name')}")
    print(f"安全獲取不存在的屬性: {safe_get_attr(obj, 'user.profile.age', 'N/A')}")
    
    # 測試字段驗證
    data = {'name': 'John', 'email': '', 'age': None}
    errors = common_utils.validate_required_fields(data, ['name', 'email', 'age', 'address'])
    print(f"字段驗證錯誤: {errors}")
    
    print("=== 測試完成 ===")