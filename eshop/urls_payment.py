# eshop/urls_payment.py

from django.urls import path
from .views.payment_views import (
    alipay_payment,
    alipay_callback,
    alipay_notify,
    check_alipay_keys,
    check_key_match,
    check_alipay_config,
    paypal_callback,
    fps_payment,
    cash_payment,
    check_and_update_payment_status,
    check_payment_timeout,
    cancel_timeout_payment,
    query_payment_status,
    retry_payment,
    payment_failed,
    test_payment_cancel,
    simulate_alipay_cancel,
)

urlpatterns = [
    # 支付宝支付
    path('alipay/<int:order_id>/', alipay_payment, name='alipay_payment'),
    path('alipay/callback/', alipay_callback, name='alipay_callback'),  # 同步回调
    path('alipay/notify/', alipay_notify, name='alipay_notify'),        # 异步通知
    
    # 支付宝调试
    path('alipay/check-keys/', check_alipay_keys, name='check_alipay_keys'),
    path('alipay/check-key-match/', check_key_match, name='check_key_match'),
    path('alipay/check-config/', check_alipay_config, name='check_alipay_config'),
    
    # PayPal支付
    path('paypal/callback/', paypal_callback, name='paypal_callback'),
    
    # FPS和现金支付
    path('fps/<int:order_id>/', fps_payment, name='fps_payment'),
    path('cash/<int:order_id>/', cash_payment, name='cash_payment'),
    
    # 支付检查
    path('check-status/<int:order_id>/', check_and_update_payment_status, name='check_payment_status'),
    path('check-timeout/<int:order_id>/', check_payment_timeout, name='check_payment_timeout'),
    path('cancel-timeout/<int:order_id>/', cancel_timeout_payment, name='cancel_timeout_payment'),
    
    # 支付优化路由
    path('query-status/<int:order_id>/', query_payment_status, name='query_payment_status'),
    path('retry/<int:order_id>/', retry_payment, name='retry_payment'),
    path('failed/', payment_failed, name='payment_failed'),
    path('test-cancel/<int:order_id>/', test_payment_cancel, name='test_payment_cancel'),
    path('simulate-alipay-cancel/<int:order_id>/', simulate_alipay_cancel, name='simulate_alipay_cancel'),
]