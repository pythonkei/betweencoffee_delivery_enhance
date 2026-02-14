# eshop/urls.py - 主URL配置
from django.urls import path, include

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
]