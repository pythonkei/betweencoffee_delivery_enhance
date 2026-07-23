# eshop/views/__init__.py
"""
集中导入所有视图，保持向后兼容
已更新为统一数据流架构
"""

# ==================== 按正確順序導入，避免循環依賴 ====================

# 從 api_views 导入
from .api_views import (
    CountdownAPI,
    UnifiedOrderAPI,
    UnifiedQueueAPI,
    api_mark_order_as_completed,
    api_mark_order_as_ready,
    get_active_orders,
    get_dashboard_stats,
    get_quick_order_times,
    get_recent_orders,
    update_order_pickup_times_api,
)

# 然後導入類視圖
# 首先導入 order_views 中的函數視圖（沒有類依賴的）
from .order_views import (
    OrderConfirm,
    add_to_cart,
    check_order_status,
    clear_quick_order,
    continue_payment,
    get_order_summary,
    order_detail,
    order_payment_confirmation,
    order_status_api,
    quick_order,
    remove_from_cart,
)

# 從 payment_views 导入
from .payment_views import (
    alipay_callback,
    alipay_notify,
    alipay_payment,
    cancel_timeout_payment,
    cash_confirm_payment,
    cash_payment,
    check_alipay_config,
    check_alipay_keys,
    check_and_update_payment_status,
    check_key_match,
    check_payment_timeout,
    fps_confirm_payment,
    fps_payment,
    payment_failed,
    paypal_callback,
    query_payment_status,
    retry_payment,
    simulate_alipay_cancel,
    test_payment_cancel,
)

# 從 queue_views 导入
from .queue_views import recalculate_all_times_api  # ✅ 補上：__all__ 中有但導入缺失
from .queue_views import (
    cleanup_queue_data,
    force_sync_api,
    get_unified_queue_data,
    mark_as_collected,
    mark_as_ready_api,
    order_details_for_waiting_api,
    queue_dashboard,
    queue_management,
    repair_queue_data,
    staff_order_management,
    start_preparation_api,
)

# 從 staff_views 导入
from .staff_views import mark_order_collected, mark_order_ready

# ==================== 🔥 新增：導入 WebSocket 監控視圖 ====================
from .websocket_views import websocket_reset_stats  # 如果有的話
from .websocket_views import (
    websocket_broadcast_test,
    websocket_connections_api,
    websocket_stats_api,
)

# ==================== 導出列表（已更新）====================

__all__ = [
    # order_views - 函數
    "order_detail",
    "quick_order",
    "clear_quick_order",
    "check_order_status",
    "continue_payment",
    "order_payment_confirmation",
    "order_status_api",
    "get_order_summary",
    "add_to_cart",
    "remove_from_cart",
    # order_views - 類
    "OrderConfirm",
    # payment_views
    "alipay_payment",
    "alipay_callback",
    "alipay_notify",
    "check_alipay_keys",
    "check_key_match",
    "check_alipay_config",
    "paypal_callback",
    "fps_payment",
    "fps_confirm_payment",
    "cash_payment",
    "cash_confirm_payment",
    "check_and_update_payment_status",
    "check_payment_timeout",
    "cancel_timeout_payment",
    "query_payment_status",
    "retry_payment",
    "payment_failed",
    "test_payment_cancel",
    "simulate_alipay_cancel",
    # queue_views
    "queue_dashboard",
    "queue_management",
    "staff_order_management",
    "get_unified_queue_data",
    "start_preparation_api",
    "mark_as_ready_api",
    "mark_as_collected",
    "force_sync_api",
    "order_details_for_waiting_api",
    "cleanup_queue_data",
    "recalculate_all_times_api",
    "repair_queue_data",
    # staff_views
    "mark_order_ready",
    "mark_order_collected",
    # api_views
    "CountdownAPI",
    "UnifiedOrderAPI",
    "UnifiedQueueAPI",
    "get_dashboard_stats",
    "api_mark_order_as_ready",
    "api_mark_order_as_completed",
    "get_recent_orders",
    "get_active_orders",
    "get_quick_order_times",
    "update_order_pickup_times_api",
    # ==================== 🔥 新增：WebSocket 監控視圖 ====================
    "websocket_stats_api",
    "websocket_connections_api",
    "websocket_broadcast_test",
    "websocket_reset_stats",
]
