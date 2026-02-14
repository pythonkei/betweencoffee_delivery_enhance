# eshop/urls_order.py

from django.urls import path
from .views.order_views import (
    OrderConfirm,
    order_detail,
    quick_order,
    clear_quick_order,
    check_order_status,
    continue_payment,
    order_payment_confirmation,
    order_status_api,
)


urlpatterns = [
    # 訂單確認頁面（處理表單提交）
    path('confirm/', OrderConfirm.as_view(), name='order_confirm'),
    
    # ========== 統一的訂單支付確認頁面 ==========
    # 1. 無參數版本 - 從session或GET參數獲取訂單
    path('payment-confirmation/', order_payment_confirmation, name='order_payment_confirmation'),
    
    # 2. 帶參數版本 - 直接訪問特定訂單
    path('payment-confirmation/<int:order_id>/', order_payment_confirmation, name='order_payment_confirmation_with_id'),
    # ========================================
    
    # 訂單詳情頁面（原名稱保持不變）
    path('detail/<int:order_id>/', order_detail, name='order_detail'),

    # 訂單狀態API
    path('api/order-status/<int:order_id>/', order_status_api, name='order_status_api'),
    
    # 快速訂單相關
    path('quick-order/', quick_order, name='quick_order'),
    path('clear-quick-order/', clear_quick_order, name='clear_quick_order'),
    
    # 支付狀態檢查
    path('check-status/<int:order_id>/', check_order_status, name='check_order_status'),
    path('continue-payment/<int:order_id>/', continue_payment, name='continue_payment'),
]