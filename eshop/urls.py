# eshop/urls.py:
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from .views import OrderConfirm, OrderPaymentConfirmation, check_order_status, check_alipay_keys
from . import views
from .views import CountdownAPI
from .views import test_twilio_config

app_name = 'eshop'

urlpatterns = [
    path('order_confirm/', OrderConfirm.as_view(), name='order_confirm'),
    path('order_payment_confirmation/', OrderPaymentConfirmation.as_view(), name='order_payment_confirmation'),
    path('order/<int:order_id>/', views.order_detail, name='order_detail'),
    path('quick-order/', views.quick_order, name='quick_order'),
    # Alipay core
    path('alipay_payment/<int:order_id>/', views.alipay_payment, name='alipay_payment'),
    path('alipay_callback/', views.alipay_callback, name='alipay_callback'),
    path('alipay_notify/', views.alipay_notify, name='alipay_notify'),
    path('check_order_status/<int:order_id>/', views.check_order_status, name='check_order_status'),
    path('debug_real_callback/', views.debug_real_callback, name='debug_real_callback'),
    # Alipay payment testing / debug
    path('check_alipay_keys/', views.check_alipay_keys, name='check_alipay_keys'),
    path('check_key_match/', views.check_key_match, name='check_key_match'),
    # PayPal core
    path('paypal_callback/', views.paypal_callback, name='paypal_callback'),
    path('countdown/<int:order_id>/', CountdownAPI.as_view(), name='countdown_api'),
    path('test-twilio-config/', test_twilio_config, name='test_twilio_config'),
    # path('test_alipay_verification/', views.test_alipay_verification, name='test_alipay_verification'),
    path('fps_payment/<int:order_id>/', views.fps_payment, name='fps_payment'),
    path('cash_payment/<int:order_id>/', views.cash_payment, name='cash_payment'),
]

# sources css, image file root
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
