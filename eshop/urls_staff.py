# eshop/urls_staff.py - 员工管理URL配置

from django.urls import path

from .views.staff_views import (
    audit_log_page,
    mark_order_collected,
    mark_order_ready,
    staff_order_management,
)
from .views.websocket_views import websocket_monitor_dashboard

urlpatterns = [
    path("order-management/", staff_order_management, name="staff_order_management"),
    path("order/<int:order_id>/mark-ready/", mark_order_ready, name="mark_order_ready"),
    path(
        "order/<int:order_id>/mark-collected/",
        mark_order_collected,
        name="mark_order_collected",
    ),
    path("audit-log/", audit_log_page, name="audit_log_page"),
    path("websocket-monitor/", websocket_monitor_dashboard, name="websocket_monitor"),
]
