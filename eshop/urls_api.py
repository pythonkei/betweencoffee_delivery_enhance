# eshop/urls_api.py
"""
API URL 配置 - 包含 WebSocket 監控 API
已整合 WebSocketManager 監控端點
"""

from django.urls import path
from .views.api_views import (
    CountdownAPI,
    UnifiedOrderAPI,
    UnifiedQueueAPI,
    get_dashboard_stats,
    api_mark_order_as_ready,
    api_mark_order_as_completed,
    # 兼容性API
    get_recent_orders,
    get_active_orders,
    get_quick_order_times,
    update_order_pickup_times_api,
    health_check,
)

# ==================== 導入 WebSocket 監控視圖 ====================
from .views.websocket_views import (
    websocket_stats_api,        # WebSocket 統計數據
    websocket_connections_api,  # WebSocket 連線列表
    websocket_broadcast_test,   # 系統廣播測試
    websocket_reset_stats,      # 🔥 新增：重置統計數據（管理員用）
)

# ==================== 導入智能分配 API 視圖 ====================
from .views_smart_allocation import (
    barista_workload_api,
    optimize_queue_api,
    order_recommendations_api,
    system_status_api,
    assign_order_api,
    update_barista_status_api,
)

urlpatterns = [
    # ==================== 訂單相關 API ====================
    path('orders/', UnifiedOrderAPI.as_view(), name='unified_orders'),
    path('orders/<int:order_id>/', UnifiedOrderAPI.as_view(), name='unified_order_detail'),
    
    # ==================== 隊列相關 API ====================
    path('queue/', UnifiedQueueAPI.as_view(), name='unified_queue'),
    path('queue/<int:order_id>/', UnifiedQueueAPI.as_view(), name='queue_order_action'),
    path('queue/<str:action>/<int:order_id>/', UnifiedQueueAPI.as_view(), name='queue_specific_action'),
    
    # ==================== 訂單狀態操作 API ====================
    path('orders/<int:order_id>/mark-ready/', api_mark_order_as_ready, name='mark_order_ready'),
    path('orders/<int:order_id>/mark-completed/', api_mark_order_as_completed, name='mark_order_completed'),
    
    # ==================== 快速訂單時間 API ====================
    path('quick-order-times/', get_quick_order_times, name='quick_order_times'),
    path('update-pickup-times/', update_order_pickup_times_api, name='update_pickup_times'),

    # ==================== 統計與儀表板 API ====================
    path('stats/dashboard/', get_dashboard_stats, name='dashboard_stats'),
    
    # ==================== 倒計時 API ====================
    path('countdown/<int:order_id>/', CountdownAPI.as_view(), name='countdown_api'),
    
    # ==================== 兼容性 API（逐步遷移）====================
    path('recent-orders/', get_recent_orders, name='recent_orders'),
    path('active-orders/', get_active_orders, name='active_orders'),
    
    # ==================== 健康檢查 API ====================
    path('health/', health_check, name='health_check'),
    
    # ==================== 🔥 WebSocket 監控 API（管理員專用）====================
    # 這些端點需要 staff_member_required 權限，已在視圖中處理
    path('websocket/stats/', websocket_stats_api, name='websocket_stats'),
    path('websocket/connections/', websocket_connections_api, name='websocket_connections'),
    path('websocket/broadcast-test/', websocket_broadcast_test, name='websocket_broadcast_test'),
    path('websocket/reset-stats/', websocket_reset_stats, name='websocket_reset_stats'),  # 🔥 新增
    
    # ==================== 🤖 智能分配 API（管理員專用）====================
    # 員工工作負載查詢
    path('queue/barista-workload/', barista_workload_api, name='barista_workload'),
    
    # 隊列優化操作
    path('queue/optimize/', optimize_queue_api, name='optimize_queue'),
    
    # 訂單智能建議
    path('orders/<int:order_id>/recommendations/', order_recommendations_api, name='order_recommendations'),
    
    # 系統狀態查詢
    path('system/status/', system_status_api, name='system_status'),
    
    # 智能分配訂單
    path('orders/<int:order_id>/assign/', assign_order_api, name='assign_order'),
    
    # 更新員工狀態
    path('baristas/<int:barista_id>/update-status/', update_barista_status_api, name='update_barista_status'),
]

# ==================== API 版本前綴（可選）====================
"""
如果需要 API 版本控制，可以使用以下模式：

urlpatterns = [
    path('v1/', include(v1_patterns)),
]

但當前專案直接掛在 /eshop/api/ 下，已足夠
"""