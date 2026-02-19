"""
統一的錯誤處理框架

這個模塊提供統一的錯誤處理函數，用於標準化系統中的錯誤處理和日誌記錄。
"""

import logging
import traceback
from datetime import datetime
from typing import Any, Dict, Optional, Union

# 創建錯誤處理日誌器
error_logger = logging.getLogger('eshop.error_handling')


class ErrorHandler:
    """統一的錯誤處理器"""
    
    def __init__(self, module_name: str = None):
        """
        初始化錯誤處理器
        
        Args:
            module_name: 模塊名稱，用於日誌記錄
        """
        self.module_name = module_name or 'unknown'
        self.logger = error_logger
    
    def handle_error(
        self,
        error: Exception,
        context: str,
        operation: str,
        data: Optional[Dict[str, Any]] = None,
        raise_exception: bool = False,
        log_level: str = 'error'
    ) -> Dict[str, Any]:
        """
        統一的錯誤處理函數
        
        Args:
            error: 異常對象
            context: 錯誤發生的上下文（如函數名、操作描述）
            operation: 正在執行的操作
            data: 相關數據（可選）
            raise_exception: 是否重新拋出異常
            log_level: 日誌級別（error, warning, info, debug）
        
        Returns:
            標準化的錯誤響應字典
        """
        error_id = self._generate_error_id()
        error_message = str(error)
        error_type = type(error).__name__
        
        # 構建錯誤詳情
        error_details = {
            'error_id': error_id,
            'timestamp': datetime.now().isoformat(),
            'module': self.module_name,
            'context': context,
            'operation': operation,
            'error_type': error_type,
            'error_message': error_message,
            'data': data or {}
        }
        
        # 記錄日誌
        self._log_error(error_details, log_level, error)
        
        # 構建標準化響應
        response = {
            'success': False,
            'error_id': error_id,
            'error_type': error_type,
            'message': f"{operation} 失敗: {error_message}",
            'details': error_details,
            'timestamp': error_details['timestamp']
        }
        
        # 如果需要，重新拋出異常
        if raise_exception:
            raise error
        
        return response
    
    def handle_success(
        self,
        operation: str,
        data: Optional[Dict[str, Any]] = None,
        message: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        統一的成功處理函數
        
        Args:
            operation: 執行的操作
            data: 相關數據（可選）
            message: 自定義成功消息（可選）
        
        Returns:
            標準化的成功響應字典
        """
        success_details = {
            'timestamp': datetime.now().isoformat(),
            'module': self.module_name,
            'operation': operation,
            'data': data or {}
        }
        
        # 記錄成功日誌
        self.logger.info(
            f"✅ {self.module_name} - {operation} 成功: {message or '操作完成'}"
        )
        
        # 構建標準化響應
        response = {
            'success': True,
            'message': message or f"{operation} 成功",
            'details': success_details,
            'timestamp': success_details['timestamp']
        }
        
        if data:
            response['data'] = data
        
        return response
    
    def wrap_function(
        self,
        func,
        context: str = None,
        log_success: bool = True
    ):
        """
        裝飾器函數，用於包裝其他函數以提供統一的錯誤處理
        
        Args:
            func: 要包裝的函數
            context: 上下文名稱（默認為函數名）
            log_success: 是否記錄成功日誌
        
        Returns:
            包裝後的函數
        """
        def wrapper(*args, **kwargs):
            func_name = context or func.__name__
            handler = ErrorHandler(module_name=func.__module__)
            
            try:
                result = func(*args, **kwargs)
                
                if log_success:
                    handler.handle_success(
                        operation=func_name,
                        data={'result': result} if result is not None else None
                    )
                
                return result
                
            except Exception as e:
                return handler.handle_error(
                    error=e,
                    context=func_name,
                    operation=func_name,
                    data={'args': str(args), 'kwargs': str(kwargs)}
                )
        
        return wrapper
    
    def _generate_error_id(self) -> str:
        """生成唯一的錯誤ID"""
        import uuid
        return str(uuid.uuid4())[:8]
    
    def _log_error(
        self,
        error_details: Dict[str, Any],
        log_level: str,
        error: Exception
    ):
        """記錄錯誤日誌"""
        log_message = (
            f"❌ {self.module_name} - {error_details['context']} "
            f"({error_details['operation']}) 失敗: "
            f"{error_details['error_type']}: {error_details['error_message']} "
            f"[錯誤ID: {error_details['error_id']}]"
        )
        
        # 根據日誌級別記錄
        if log_level == 'error':
            self.logger.error(log_message)
            self.logger.error(f"錯誤詳情: {error_details}")
            self.logger.error(f"堆棧追蹤: {traceback.format_exc()}")
        elif log_level == 'warning':
            self.logger.warning(log_message)
            self.logger.warning(f"錯誤詳情: {error_details}")
        elif log_level == 'info':
            self.logger.info(log_message)
        elif log_level == 'debug':
            self.logger.debug(log_message)
            self.logger.debug(f"錯誤詳情: {error_details}")
            self.logger.debug(f"堆棧追蹤: {traceback.format_exc()}")


# 全局錯誤處理器實例
global_error_handler = ErrorHandler(module_name='eshop')


# 便捷函數
def handle_error(
    error: Exception,
    context: str,
    operation: str,
    data: Optional[Dict[str, Any]] = None,
    raise_exception: bool = False,
    log_level: str = 'error'
) -> Dict[str, Any]:
    """
    全局錯誤處理便捷函數
    
    參數和返回值與 ErrorHandler.handle_error 相同
    """
    return global_error_handler.handle_error(
        error=error,
        context=context,
        operation=operation,
        data=data,
        raise_exception=raise_exception,
        log_level=log_level
    )


def handle_success(
    operation: str,
    data: Optional[Dict[str, Any]] = None,
    message: Optional[str] = None
) -> Dict[str, Any]:
    """
    全局成功處理便捷函數
    
    參數和返回值與 ErrorHandler.handle_success 相同
    """
    return global_error_handler.handle_success(
        operation=operation,
        data=data,
        message=message
    )


def wrap_function(func, context: str = None, log_success: bool = True):
    """
    全局函數包裝便捷函數
    
    參數和返回值與 ErrorHandler.wrap_function 相同
    """
    return global_error_handler.wrap_function(
        func=func,
        context=context,
        log_success=log_success
    )


# 裝飾器
def error_handler_decorator(context: str = None, log_success: bool = True):
    """
    錯誤處理裝飾器
    
    Args:
        context: 上下文名稱
        log_success: 是否記錄成功日誌
    
    Returns:
        裝飾器函數
    """
    def decorator(func):
        return wrap_function(func, context=context, log_success=log_success)
    return decorator


# 特定錯誤類型的處理函數
def handle_database_error(
    error: Exception,
    operation: str,
    query: Optional[str] = None,
    model: Optional[str] = None
) -> Dict[str, Any]:
    """
    處理數據庫錯誤
    
    Args:
        error: 數據庫異常
        operation: 數據庫操作
        query: SQL查詢（可選）
        model: 模型名稱（可選）
    
    Returns:
        標準化的錯誤響應
    """
    data = {}
    if query:
        data['query'] = query
    if model:
        data['model'] = model
    
    return handle_error(
        error=error,
        context='database',
        operation=operation,
        data=data,
        log_level='error'
    )


def handle_validation_error(
    error: Exception,
    operation: str,
    field: Optional[str] = None,
    value: Optional[Any] = None
) -> Dict[str, Any]:
    """
    處理驗證錯誤
    
    Args:
        error: 驗證異常
        operation: 驗證操作
        field: 字段名稱（可選）
        value: 字段值（可選）
    
    Returns:
        標準化的錯誤響應
    """
    data = {}
    if field:
        data['field'] = field
    if value is not None:
        data['value'] = value
    
    return handle_error(
        error=error,
        context='validation',
        operation=operation,
        data=data,
        log_level='warning'
    )


def handle_external_api_error(
    error: Exception,
    operation: str,
    api_endpoint: Optional[str] = None,
    status_code: Optional[int] = None
) -> Dict[str, Any]:
    """
    處理外部API錯誤
    
    Args:
        error: API異常
        operation: API操作
        api_endpoint: API端點（可選）
        status_code: HTTP狀態碼（可選）
    
    Returns:
        標準化的錯誤響應
    """
    data = {}
    if api_endpoint:
        data['api_endpoint'] = api_endpoint
    if status_code:
        data['status_code'] = status_code
    
    return handle_error(
        error=error,
        context='external_api',
        operation=operation,
        data=data,
        log_level='error'
    )


# 示例使用
if __name__ == "__main__":
    # 示例1: 基本錯誤處理
    try:
        result = 1 / 0
    except Exception as e:
        error_response = handle_error(
            error=e,
            context='division',
            operation='divide_numbers',
            data={'numerator': 1, 'denominator': 0}
        )
        print(f"錯誤處理結果: {error_response}")
    
    # 示例2: 成功處理
    success_response = handle_success(
        operation='process_order',
        data={'order_id': 123, 'status': 'completed'},
        message='訂單處理成功'
    )
    print(f"成功處理結果: {success_response}")
    
    # 示例3: 使用裝飾器
    @error_handler_decorator(context='example_function')
    def example_function(x, y):
        """示例函數"""
        return x / y
    
    # 測試裝飾器
    result = example_function(10, 2)
    print(f"裝飾器測試結果: {result}")
    
    # 測試錯誤情況
    result = example_function(10, 0)
    print(f"裝飾器錯誤測試結果: {result}")