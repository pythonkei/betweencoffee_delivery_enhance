"""
統一的API響應格式系統
確保所有API端點返回一致的數據結構
"""

from django.http import JsonResponse
from django.utils import timezone
from typing import Any, Dict, Optional, List, Union
import json


class ApiResponse:
    """
    統一的API響應類
    
    設計目標：
    1. 標準化成功和錯誤響應格式
    2. 支持分頁和元數據
    3. 提供鏈式調用接口
    4. 自動時間戳和版本信息
    """
    
    # 標準響應字段
    STANDARD_FIELDS = {
        'success': bool,
        'message': str,
        'data': Any,
        'timestamp': str,
        'code': Optional[int],
        'pagination': Optional[Dict],
        'metadata': Optional[Dict],
    }
    
    # 預定義錯誤代碼
    ERROR_CODES = {
        # 通用錯誤 (1000-1099)
        'VALIDATION_ERROR': 1001,
        'AUTHENTICATION_ERROR': 1002,
        'AUTHORIZATION_ERROR': 1003,
        'NOT_FOUND': 1004,
        'METHOD_NOT_ALLOWED': 1005,
        'RATE_LIMIT_EXCEEDED': 1006,
        
        # 業務邏輯錯誤 (2000-2099)
        'ORDER_VALIDATION_ERROR': 2001,
        'PAYMENT_ERROR': 2002,
        'QUEUE_FULL_ERROR': 2003,
        'INVALID_STATE_ERROR': 2004,
        
        # 系統錯誤 (5000-5099)
        'INTERNAL_SERVER_ERROR': 5001,
        'DATABASE_ERROR': 5002,
        'EXTERNAL_SERVICE_ERROR': 5003,
        'CACHE_ERROR': 5004,
    }
    
    def __init__(self):
        """初始化響應構建器"""
        self._response = {
            'success': True,
            'message': '',
            'data': None,
            'timestamp': timezone.now().isoformat(),
            'version': '1.0.0',
        }
    
    @classmethod
    def success(cls, data: Any = None, message: str = "操作成功", **kwargs) -> Dict:
        """
        創建成功響應
        
        Args:
            data: 響應數據
            message: 成功消息
            **kwargs: 額外字段
            
        Returns:
            標準化的成功響應字典
        """
        response = {
            'success': True,
            'message': message,
            'data': data,
            'timestamp': timezone.now().isoformat(),
            'version': '1.0.0',
        }
        
        # 添加額外字段
        response.update(kwargs)
        return response
    
    @classmethod
    def error(cls, 
              message: str = "操作失敗", 
              code: Optional[int] = None,
              details: Optional[Any] = None,
              status_code: int = 400,
              **kwargs) -> Dict:
        """
        創建錯誤響應
        
        Args:
            message: 錯誤消息
            code: 錯誤代碼
            details: 詳細錯誤信息
            status_code: HTTP狀態碼（用於JsonResponse）
            **kwargs: 額外字段
            
        Returns:
            標準化的錯誤響應字典
        """
        response = {
            'success': False,
            'message': message,
            'error_code': code,
            'timestamp': timezone.now().isoformat(),
            'version': '1.0.0',
        }
        
        if details:
            response['details'] = details
        
        # 添加額外字段
        response.update(kwargs)
        return response
    
    @classmethod
    def paginated(cls, 
                  data: List, 
                  total: int, 
                  page: int, 
                  page_size: int,
                  message: str = "操作成功",
                  **kwargs) -> Dict:
        """
        創建分頁響應
        
        Args:
            data: 當前頁數據
            total: 總記錄數
            page: 當前頁碼
            page_size: 每頁大小
            message: 成功消息
            **kwargs: 額外字段
            
        Returns:
            標準化的分頁響應字典
        """
        response = {
            'success': True,
            'message': message,
            'data': data,
            'pagination': {
                'total': total,
                'page': page,
                'page_size': page_size,
                'total_pages': (total + page_size - 1) // page_size if page_size > 0 else 0,
                'has_next': page * page_size < total,
                'has_prev': page > 1,
            },
            'timestamp': timezone.now().isoformat(),
            'version': '1.0.0',
        }
        
        # 添加額外字段
        response.update(kwargs)
        return response
    
    @classmethod
    def validation_error(cls, 
                         field_errors: Dict[str, List[str]], 
                         message: str = "數據驗證失敗") -> Dict:
        """
        創建驗證錯誤響應
        
        Args:
            field_errors: 字段錯誤字典 {字段名: [錯誤列表]}
            message: 錯誤消息
            
        Returns:
            驗證錯誤響應
        """
        return cls.error(
            message=message,
            code=cls.ERROR_CODES['VALIDATION_ERROR'],
            details={'field_errors': field_errors},
            status_code=400,
        )
    
    @classmethod
    def not_found(cls, resource_type: str, resource_id: Any, message: str = None) -> Dict:
        """
        創建資源未找到錯誤響應
        
        Args:
            resource_type: 資源類型
            resource_id: 資源ID
            message: 自定義錯誤消息
            
        Returns:
            未找到錯誤響應
        """
        if message is None:
            message = f"{resource_type} 未找到"
        
        return cls.error(
            message=message,
            code=cls.ERROR_CODES['NOT_FOUND'],
            details={
                'resource_type': resource_type,
                'resource_id': resource_id,
            },
            status_code=404,
        )
    
    @classmethod
    def permission_error(cls, 
                         resource: str, 
                         action: str, 
                         message: str = None) -> Dict:
        """
        創建權限錯誤響應
        
        Args:
            resource: 資源名稱
            action: 嘗試的操作
            message: 自定義錯誤消息
            
        Returns:
            權限錯誤響應
        """
        if message is None:
            message = f"無權執行 {action} 操作"
        
        return cls.error(
            message=message,
            code=cls.ERROR_CODES['AUTHORIZATION_ERROR'],
            details={
                'resource': resource,
                'action': action,
            },
            status_code=403,
        )
    
    @classmethod
    def internal_error(cls, 
                       error_message: str, 
                       traceback: Optional[str] = None,
                       request_id: Optional[str] = None) -> Dict:
        """
        創建內部服務器錯誤響應
        
        Args:
            error_message: 錯誤消息
            traceback: 追蹤信息（僅開發環境）
            request_id: 請求ID
            
        Returns:
            內部錯誤響應
        """
        from django.conf import settings
        
        details = {'request_id': request_id} if request_id else {}
        
        # 開發環境包含追蹤信息
        if settings.DEBUG and traceback:
            details['traceback'] = traceback
        
        return cls.error(
            message="伺服器內部錯誤" if not settings.DEBUG else error_message,
            code=cls.ERROR_CODES['INTERNAL_SERVER_ERROR'],
            details=details,
            status_code=500,
        )


class JsonResponseBuilder:
    """
    JsonResponse構建器，提供鏈式調用接口
    """
    
    def __init__(self, status_code: int = 200):
        self._response = ApiResponse.success()
        self._status_code = status_code
    
    def success(self, data: Any = None) -> 'JsonResponseBuilder':
        """設置成功響應"""
        self._response = ApiResponse.success(data=data)
        return self
    
    def error(self, message: str, code: Optional[int] = None) -> 'JsonResponseBuilder':
        """設置錯誤響應"""
        self._response = ApiResponse.error(message=message, code=code)
        return self
    
    def message(self, message: str) -> 'JsonResponseBuilder':
        """設置消息"""
        self._response['message'] = message
        return self
    
    def data(self, data: Any) -> 'JsonResponseBuilder':
        """設置數據"""
        self._response['data'] = data
        return self
    
    def code(self, code: int) -> 'JsonResponseBuilder':
        """設置錯誤代碼"""
        self._response['code'] = code
        return self
    
    def status(self, status_code: int) -> 'JsonResponseBuilder':
        """設置HTTP狀態碼"""
        self._status_code = status_code
        return self
    
    def add_metadata(self, key: str, value: Any) -> 'JsonResponseBuilder':
        """添加元數據"""
        if 'metadata' not in self._response:
            self._response['metadata'] = {}
        self._response['metadata'][key] = value
        return self
    
    def pagination(self, total: int, page: int, page_size: int) -> 'JsonResponseBuilder':
        """設置分頁信息"""
        self._response = ApiResponse.paginated(
            data=self._response.get('data'),
            total=total,
            page=page,
            page_size=page_size,
            message=self._response.get('message', '')
        )
        return self
    
    def build(self) -> JsonResponse:
        """構建JsonResponse"""
        return JsonResponse(self._response, status=self._status_code)
    
    def to_dict(self) -> Dict:
        """轉換為字典（用於測試或其他用途）"""
        return self._response


# Django視圖裝飾器
def api_response_format(view_func):
    """
    API響應格式化裝飾器
    
    自動捕獲異常並返回統一的錯誤格式
    將視圖返回值自動包裝為標準響應
    """
    from functools import wraps
    from django.http import JsonResponse
    import traceback
    
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        try:
            # 執行視圖函數
            result = view_func(request, *args, **kwargs)
            
            # 如果已經是JsonResponse，直接返回
            if isinstance(result, JsonResponse):
                return result
            
            # 如果視圖返回了字典，自動包裝
            if isinstance(result, dict):
                # 檢查是否已經是標準格式
                if 'success' in result:
                    return JsonResponse(result)
                else:
                    # 自動包裝為成功響應
                    return JsonResponse(ApiResponse.success(data=result))
            
            # 其他類型（如重定向、HttpResponse等）
            return result
            
        except Exception as e:
            # 捕獲異常並返回統一的錯誤格式
            error_traceback = traceback.format_exc()
            
            # 記錄錯誤
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"API視圖錯誤: {str(e)}")
            logger.debug(f"錯誤追蹤: {error_traceback}")
            
            # 根據異常類型返回適當的錯誤
            from django.core.exceptions import ValidationError, PermissionDenied
            from django.http import Http404
            
            if isinstance(e, ValidationError):
                field_errors = {}
                if hasattr(e, 'message_dict'):
                    field_errors = e.message_dict
                elif hasattr(e, 'messages'):
                    field_errors = {'non_field_errors': e.messages}
                
                return JsonResponse(
                    ApiResponse.validation_error(field_errors),
                    status=400
                )
            
            elif isinstance(e, PermissionDenied):
                return JsonResponse(
                    ApiResponse.permission_error('資源', '訪問'),
                    status=403
                )
            
            elif isinstance(e, Http404):
                resource_type = '資源'
                resource_id = str(e) if str(e) else '未知'
                if 'matching query' in str(e):
                    resource_type = '記錄'
                return JsonResponse(
                    ApiResponse.not_found(resource_type, resource_id),
                    status=404
                )
            
            else:
                # 內部服務器錯誤
                request_id = getattr(request, 'id', None)
                from django.conf import settings
                
                if settings.DEBUG:
                    # 開發環境顯示詳細錯誤
                    return JsonResponse(
                        ApiResponse.internal_error(
                            str(e), 
                            traceback=error_traceback,
                            request_id=request_id
                        ),
                        status=500
                    )
                else:
                    # 生產環境顯示通用錯誤
                    return JsonResponse(
                        ApiResponse.internal_error(
                            "伺服器內部錯誤",
                            request_id=request_id
                        ),
                        status=500
                    )
    
    return wrapper


# 快捷函數
def api_success(data=None, message="操作成功", status_code=200, **kwargs):
    """快速創建成功JsonResponse"""
    response_data = ApiResponse.success(data=data, message=message, **kwargs)
    return JsonResponse(response_data, status=status_code)


def api_error(message="操作失敗", code=None, status_code=400, **kwargs):
    """快速創建錯誤JsonResponse"""
    response_data = ApiResponse.error(message=message, code=code, **kwargs)
    return JsonResponse(response_data, status=status_code)


def api_paginated(data, total, page, page_size, message="操作成功", **kwargs):
    """快速創建分頁JsonResponse"""
    response_data = ApiResponse.paginated(
        data=data, 
        total=total, 
        page=page, 
        page_size=page_size, 
        message=message,
        **kwargs
    )
    return JsonResponse(response_data)


# 測試使用
if __name__ == "__main__":
    # 示例用法
    print("=== 成功響應示例 ===")
    print(json.dumps(ApiResponse.success(
        data={'user': {'id': 1, 'name': 'John'}},
        message="用戶信息獲取成功"
    ), indent=2))
    
    print("\n=== 錯誤響應示例 ===")
    print(json.dumps(ApiResponse.error(
        message="用戶不存在",
        code=1004,
        details={'user_id': 999}
    ), indent=2))
    
    print("\n=== 分頁響應示例 ===")
    print(json.dumps(ApiResponse.paginated(
        data=[{'id': i, 'name': f'Item {i}'} for i in range(1, 11)],
        total=100,
        page=1,
        page_size=10,
        message="數據獲取成功"
    ), indent=2))
    
    print("\n=== 鏈式調用示例 ===")
    response = JsonResponseBuilder()\
        .success({'test': 'data'})\
        .message("測試成功")\
        .add_metadata('processed_by', 'api_gateway')\
        .build()
    print(f"響應狀態碼: {response.status_code}")
    print(f"響應內容: {json.loads(response.content)}")