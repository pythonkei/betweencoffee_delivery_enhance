"""
統一的錯誤處理和日誌記錄系統
用於標準化所有模塊的錯誤處理和日誌記錄
"""

import logging
import traceback
import inspect
import json
from datetime import datetime
from django.http import JsonResponse
from django.utils import timezone

logger = logging.getLogger(__name__)


class ErrorHandler:
    """
    統一的錯誤處理和日誌記錄類
    
    功能：
    1. 結構化日誌記錄
    2. 統一的API錯誤響應格式
    3. 錯誤分類和處理
    4. 異常上下文收集
    """
    
    # 錯誤代碼分類
    ERROR_CODES = {
        # 系統錯誤 (1000-1999)
        'SYSTEM_ERROR': 1000,
        'DATABASE_ERROR': 1001,
        'NETWORK_ERROR': 1002,
        'CONFIGURATION_ERROR': 1003,
        
        # 業務邏輯錯誤 (2000-2999)
        'VALIDATION_ERROR': 2000,
        'AUTHENTICATION_ERROR': 2001,
        'AUTHORIZATION_ERROR': 2002,
        'NOT_FOUND': 2003,
        'CONFLICT': 2004,
        'INVALID_STATE': 2005,
        
        # 支付相關錯誤 (3000-3999)
        'PAYMENT_FAILED': 3000,
        'PAYMENT_TIMEOUT': 3001,
        'PAYMENT_INVALID': 3002,
        
        # 隊列相關錯誤 (4000-4999)
        'QUEUE_FULL': 4000,
        'QUEUE_INVALID': 4001,
        'QUEUE_TIMEOUT': 4002,
        
        # WebSocket相關錯誤 (5000-5999)
        'WEBSOCKET_ERROR': 5000,
        'WEBSOCKET_TIMEOUT': 5001,
        'WEBSOCKET_DISCONNECTED': 5002,
    }
    
    @staticmethod
    def api_error_response(message, status=400, error_code=None,
                           details=None, request=None):
        """
        統一的API錯誤響應
        
        Args:
            message: 錯誤信息
            status: HTTP狀態碼
            error_code: 自定義錯誤代碼
            details: 詳細錯誤信息
            request: 請求對象（用於記錄上下文）
            
        Returns:
            JsonResponse: 統一格式的錯誤響應
        """
        if request:
            ErrorHandler.log_request_error(request, message, status)
        
        response_data = {
            'success': False,
            'error': message,
            'error_code': error_code,
            'timestamp': timezone.now().isoformat(),
        }
        
        if details:
            response_data['details'] = details
        
        # 生產環境隱藏敏感細節
        from django.conf import settings
        if (not settings.DEBUG and isinstance(details, dict) and
                'traceback' in details):
            del details['traceback']
        
        return JsonResponse(response_data, status=status)
    
    @staticmethod
    def log_error(context, exception, level='error', extra_data=None):
        """
        統一的結構化日誌記錄
        
        Args:
            context: 錯誤上下文描述
            exception: 異常對象或錯誤信息
            level: 日誌級別 ('debug', 'info', 'warning', 'error', 'critical')
            extra_data: 額外數據
        """
        log_data = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'context': context,
            'level': level.upper(),
            'module': inspect.currentframe().f_back.f_globals.get('__name__', 'unknown'),
        }
        
        if isinstance(exception, Exception):
            log_data.update({
                'exception_type': exception.__class__.__name__,
                'exception_message': str(exception),
                'traceback': traceback.format_exc(),
            })
        else:
            log_data['message'] = str(exception)
        
        if extra_data:
            log_data['extra'] = extra_data
        
        # 獲取調用棧信息
        frame = inspect.currentframe().f_back
        log_data['caller'] = {
            'file': frame.f_code.co_filename,
            'line': frame.f_lineno,
            'function': frame.f_code.co_name,
        }
        
        # 記錄結構化日誌
        log_message = json.dumps(log_data, ensure_ascii=False, default=str)
        
        log_method = getattr(logger, level.lower(), logger.error)
        log_method(log_message)
        
        return log_data
    
    @staticmethod
    def log_request_error(request, error_message, status_code):
        """
        記錄請求相關的錯誤
        
        Args:
            request: Django請求對象
            error_message: 錯誤信息
            status_code: HTTP狀態碼
        """
        request_info = {
            'method': request.method,
            'path': request.path,
            'user': str(request.user) if request.user.is_authenticated else 'anonymous',
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'ip_address': request.META.get('REMOTE_ADDR', ''),
        }
        
        if request.method in ['POST', 'PUT', 'PATCH']:
            try:
                body = json.loads(request.body.decode('utf-8'))
                # 隱藏敏感信息
                if isinstance(body, dict):
                    sanitized_body = body.copy()
                    sensitive_fields = ['password', 'token', 'credit_card', 'cvv']
                    for sensitive_field in sensitive_fields:
                        if sensitive_field in sanitized_body:
                            sanitized_body[sensitive_field] = '***REDACTED***'
                    request_info['request_body'] = sanitized_body
            except Exception:
                request_info['request_body'] = '無法解析'
        
        ErrorHandler.log_error(
            context=f"HTTP {status_code} 錯誤",
            exception=error_message,
            level='error' if status_code >= 500 else 'warning',
            extra_data={'request': request_info}
        )
    
    @staticmethod
    def handle_validation_error(exception, field_name=None):
        """
        處理驗證錯誤
        
        Args:
            exception: 驗證異常
            field_name: 字段名稱
            
        Returns:
            dict: 錯誤響應數據
        """
        error_message = str(exception)
        if field_name:
            error_message = f"{field_name}: {error_message}"
        
        return ErrorHandler.api_error_response(
            message="數據驗證失敗",
            status=400,
            error_code=ErrorHandler.ERROR_CODES['VALIDATION_ERROR'],
            details={
                'field': field_name,
                'message': str(exception),
                'error_type': exception.__class__.__name__,
            }
        )
    
    @staticmethod
    def handle_database_error(exception, operation):
        """
        處理數據庫錯誤
        
        Args:
            exception: 數據庫異常
            operation: 操作描述
            
        Returns:
            dict: 錯誤響應數據
        """
        return ErrorHandler.api_error_response(
            message=f"數據庫操作失敗: {operation}",
            status=500,
            error_code=ErrorHandler.ERROR_CODES['DATABASE_ERROR'],
            details={
                'operation': operation,
                'error_type': exception.__class__.__name__,
                'message': str(exception),
            }
        )
    
    @staticmethod
    def handle_not_found(resource_type, resource_id):
        """
        處理資源未找到錯誤
        
        Args:
            resource_type: 資源類型
            resource_id: 資源ID
            
        Returns:
            dict: 錯誤響應數據
        """
        return ErrorHandler.api_error_response(
            message=f"{resource_type} 未找到",
            status=404,
            error_code=ErrorHandler.ERROR_CODES['NOT_FOUND'],
            details={
                'resource_type': resource_type,
                'resource_id': resource_id,
            }
        )
    
    @staticmethod
    def handle_permission_error(resource, action):
        """
        處理權限錯誤
        
        Args:
            resource: 資源描述
            action: 嘗試的操作
            
        Returns:
            dict: 錯誤響應數據
        """
        return ErrorHandler.api_error_response(
            message=f"無權限執行 {action} 操作",
            status=403,
            error_code=ErrorHandler.ERROR_CODES['AUTHORIZATION_ERROR'],
            details={
                'resource': resource,
                'action': action,
            }
        )
    
    @staticmethod
    def wrap_exception(view_func):
        """
        裝飾器：包裝視圖函數，自動處理異常
        
        Args:
            view_func: 視圖函數
            
        Returns:
            包裝後的視圖函數
        """
        def wrapped_view(request, *args, **kwargs):
            try:
                return view_func(request, *args, **kwargs)
            except Exception as e:
                ErrorHandler.log_error(
                    context=f"視圖 {view_func.__name__} 執行錯誤",
                    exception=e,
                    extra_data={
                        'request_path': request.path,
                        'request_method': request.method,
                    }
                )
                
                # 根據異常類型返回適當的響應
                if hasattr(e, 'status_code'):
                    return ErrorHandler.api_error_response(
                        message=str(e),
                        status=e.status_code,
                        request=request
                    )
                elif "not found" in str(e).lower():
                    return ErrorHandler.api_error_response(
                        message="資源未找到",
                        status=404,
                        request=request
                    )
                elif "permission" in str(e).lower() or "權限" in str(e):
                    return ErrorHandler.api_error_response(
                        message="無權限訪問",
                        status=403,
                        request=request
                    )
                else:
                    return ErrorHandler.api_error_response(
                        message="伺服器內部錯誤",
                        status=500,
                        request=request
                    )
        
        return wrapped_view


class ErrorContext:
    """
    錯誤上下文管理器
    用於在代碼塊中收集錯誤上下文
    """
    
    def __init__(self, context_name):
        self.context_name = context_name
        self.start_time = datetime.utcnow()
        self.extra_data = {}
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_val:
            # 發生異常，記錄錯誤
            duration = (datetime.utcnow() - self.start_time).total_seconds()
            self.extra_data['duration_seconds'] = duration
            
            ErrorHandler.log_error(
                context=self.context_name,
                exception=exc_val,
                extra_data=self.extra_data
            )
        
        # 不捕獲異常，讓其繼續傳播
        return False
    
    def add_data(self, key, value):
        """添加上下文數據"""
        self.extra_data[key] = value


# 快捷函數
def log_system_error(context, exception, **kwargs):
    """記錄系統錯誤"""
    return ErrorHandler.log_error(context, exception, level='error', extra_data=kwargs)


def log_business_error(context, exception, **kwargs):
    """記錄業務錯誤"""
    return ErrorHandler.log_error(context, exception, level='warning', extra_data=kwargs)


def api_error(message, status=400, **kwargs):
    """快速API錯誤響應"""
    return ErrorHandler.api_error_response(message, status, **kwargs)


def validation_error(field, message):
    """驗證錯誤"""
    return ErrorHandler.handle_validation_error(Exception(message), field_name=field)


def not_found(resource_type, resource_id):
    """資源未找到錯誤"""
    return ErrorHandler.handle_not_found(resource_type, resource_id)


def permission_error(resource, action):
    """權限錯誤"""
    return ErrorHandler.handle_permission_error(resource, action)