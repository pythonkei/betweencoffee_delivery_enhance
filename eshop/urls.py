# eshop/urls.py - 主URL配置
from django.urls import path, include
from eshop.views.test_views import (
    websocket_test_view,
    websocket_diagnostic_view,
    beans_only_status_test_view
)

app_name = 'eshop'

urlpatterns = [
    # 订单相关路由
    path('order/', include('eshop.urls_order')),
    
    # 支付相关路由
    path('payment/', include('eshop.urls_payment')),
    
    # 队列相关路由 ⬅ 這裡包含了我們的隊列URL
    path('queue/', include('eshop.urls_queue')),
    
    # 员工管理路由
    path('staff/', include('eshop.urls_staff')),
    
    # API路由（用于实时更新等）
    path('api/', include('eshop.urls_api')),
    
    # WebSocket测试路由（仅开发环境）
    path('test/websocket/', websocket_test_view,
         name='websocket_test'),
    path('test/websocket-diagnostic/', websocket_diagnostic_view,
         name='websocket_diagnostic'),
    
    # 纯咖啡豆订单状态测试路由
    path('test/beans-only-status/', beans_only_status_test_view,
         name='beans_only_status_test'),
]
