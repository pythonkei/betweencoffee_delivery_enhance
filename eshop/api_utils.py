# eshop/api_utils.py
"""
API視圖工具 - 提供統一的API處理函數
"""

import json
import logging
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.decorators import method_decorator
from django.views import View

from .serializers import OrderDataSerializer, ApiResponseFormatter

logger = logging.getLogger(__name__)


def staff_api_required(view_func=None, require_staff=True):
    """
    裝飾器：要求員工權限的API
    
    Args:
        require_staff: 是否需要員工權限
    """
    def decorator(view_func):
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            if require_staff and not request.user.is_staff:
                return JsonResponse(
                    ApiResponseFormatter.error("需要員工權限"),
                    status=403
                )
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    
    if view_func:
        return decorator(view_func)
    return decorator


class BaseApiView(View):
    """基礎API視圖類"""
    
    # 權限裝飾器
    decorators = []
    
    @classmethod
    def as_view(cls, **initkwargs):
        """應用裝飾器"""
        view = super().as_view(**initkwargs)
        for decorator in cls.decorators:
            view = decorator(view)
        return view
    
    def dispatch(self, request, *args, **kwargs):
        """統一的分發方法"""
        try:
            return super().dispatch(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"API處理異常: {str(e)}")
            return self.handle_exception(e)
    
    def handle_exception(self, exception):
        """統一異常處理"""
        error_message = str(exception)
        status_code = 500
        
        if hasattr(exception, 'status_code'):
            status_code = exception.status_code
        elif "not found" in str(exception).lower():
            status_code = 404
        elif "permission" in str(exception).lower():
            status_code = 403
        
        return JsonResponse(
            ApiResponseFormatter.error(
                message=error_message,
                code=status_code
            ),
            status=status_code
        )
    
    def get_json_data(self, request):
        """獲取JSON數據"""
        try:
            if request.body:
                return json.loads(request.body)
            return {}
        except json.JSONDecodeError:
            return {}
    
    def success_response(self, data=None, message="操作成功", **kwargs):
        """成功響應"""
        return JsonResponse(
            ApiResponseFormatter.success(data, message, **kwargs)
        )
    
    def error_response(self, message="操作失敗", code=None, details=None, status=400, **kwargs):
        """錯誤響應"""
        return JsonResponse(
            ApiResponseFormatter.error(message, code, details, **kwargs),
            status=status
        )


class OrderApiMixin:
    """訂單API混入類"""
    
    def get_order(self, order_id, check_permission=True):
        """獲取訂單並檢查權限"""
        order = get_object_or_404(self.order_model, id=order_id)
        
        if check_permission:
            self.check_order_permission(order)
        
        return order
    
    def check_order_permission(self, order):
        """檢查訂單權限"""
        # 員工可以查看所有訂單
        if hasattr(self.request, 'user') and self.request.user.is_staff:
            return True
        
        # 用戶只能查看自己的訂單
        if hasattr(self.request, 'user') and self.request.user.is_authenticated:
            if order.user != self.request.user:
                raise PermissionError("無權訪問此訂單")
            return True
        
        # 匿名用戶需要特殊處理
        raise PermissionError("需要登入")
    
    def serialize_order(self, order, include_queue_info=True, include_items=True):
        """序列化訂單"""
        return OrderDataSerializer.serialize_order(
            order, 
            include_queue_info=include_queue_info,
            include_items=include_items
        )