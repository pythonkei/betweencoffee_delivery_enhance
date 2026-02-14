# eshop/urls_staff.py - 员工管理URL配置

from django.urls import path
from .views.staff_views import (
    staff_order_management,
    mark_order_ready,
    mark_order_collected,
)
from .views.websocket_views import websocket_monitor_dashboard

urlpatterns = [
    path('order-management/', staff_order_management, name='staff_order_management'),
    path('order/<int:order_id>/mark-ready/', mark_order_ready, name='mark_order_ready'),
    path('order/<int:order_id>/mark-collected/', mark_order_collected, name='mark_order_collected'),
    path('websocket-monitor/', websocket_monitor_dashboard, name='websocket_monitor'),
]