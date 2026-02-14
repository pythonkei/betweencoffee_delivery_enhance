# eshop/routing.py
from django.urls import re_path, path

# ✅ 直接導入 consumers（不需要延遲導入）
from . import consumers

websocket_urlpatterns = [
    # 訂單詳情頁 WebSocket - 用於單個訂單的即時更新
    re_path(r'ws/order/(?P<order_id>\d+)/$', consumers.OrderConsumer.as_asgi()),
    
    # 隊列管理頁 WebSocket - 用於隊列的即時更新
    path('ws/queue/', consumers.QueueConsumer.as_asgi()),
]