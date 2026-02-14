# eshop/urls_queue.py
"""
队列管理系统的URL路由配置
已重构为统一数据流架构
"""

from django.urls import path
from .views.queue_views import (
    # 页面视图
    queue_dashboard,
    queue_management,
    staff_order_management,
    
    # ==================== 统一数据API（新增） ====================
    get_unified_queue_data,  # 核心：统一的队列数据API
    
    # ==================== 操作API（保持不变） ====================
    start_preparation_api,
    mark_as_ready_api,
    mark_as_collected,
    
    # ==================== 数据修复API（保持不变） ====================
    repair_queue_data,
    force_sync_api,
    cleanup_queue_data,
    
    # ==================== 订单详情API（保持不变） ====================
    order_details_for_waiting_api,
    
    # ==================== 已废弃的API（将被移除或注释掉） ====================
    # get_queue_updates,           # 已由 get_unified_queue_data 替代
    # get_badge_summary,          # 已由 get_unified_queue_data 替代
    # preparing_orders_count_api, # 已由 get_unified_queue_data 替代
    # ready_orders_count_api,     # 已由 get_unified_queue_data 替代
    # completed_orders_count_api, # 已由 get_unified_queue_data 替代
    # preparing_orders_json_api,  # 已由 get_unified_queue_data 替代
    # ready_orders_json_api,      # 已由 get_unified_queue_data 替代
    # completed_orders_json_api,  # 暂时保留（需要扩展统一API）
)

urlpatterns = [
    # ==================== 页面路由 ====================
    path('dashboard/', queue_dashboard, name='queue_dashboard'),
    path('management/', queue_management, name='queue_management'),
    path('staff-management/', staff_order_management, name='staff_order_management'),
    
    # ==================== 统一数据API路由（新增） ====================
    # 注意：这是核心API，所有前端组件都将使用这个单一端点
    path('unified-data/', get_unified_queue_data, name='unified_queue_data'),
    
    # ==================== 操作API路由（保持不变） ====================
    path('start/<int:order_id>/', start_preparation_api, name='start_preparation_api'),
    path('ready/<int:order_id>/', mark_as_ready_api, name='mark_as_ready_api'),
    path('collected/<int:order_id>/', mark_as_collected, name='mark_as_collected'),
    
    # ==================== 数据修复API路由（保持不变） ====================
    path('repair/', repair_queue_data, name='repair_queue_data'),
    path('force-sync/', force_sync_api, name='force_sync_api'),
    path('cleanup/', cleanup_queue_data, name='cleanup_queue_data'),
    
    # ==================== 订单详情API路由（保持不变） ====================
    path('order-details/<int:order_id>/', order_details_for_waiting_api, name='order_details_for_waiting_api'),
    

    
    # ==================== 需要扩展的API路由（已提取订单） ====================
    # 注意：第一步的get_unified_queue_data没有包含completed_orders，需要扩展
    # 暂时保持原路由，后续扩展统一API
    path('completed-orders/json/', get_unified_queue_data, name='completed_orders_json_api'),  # 暂时重定向
]


# 示例：重定向旧API到新API（可选）
from django.views.generic import RedirectView

# 如果希望旧API自动重定向到新API，可以取消注释以下代码：
"""
urlpatterns += [
    # 重定向旧API到统一API
    path('updates/', RedirectView.as_view(pattern_name='unified_queue_data', permanent=False), name='old_queue_updates'),
    path('badge-summary/', RedirectView.as_view(pattern_name='unified_queue_data', permanent=False), name='old_badge_summary'),
    path('preparing-count/', RedirectView.as_view(pattern_name='unified_queue_data', permanent=False), name='old_preparing_count'),
    path('ready-count/', RedirectView.as_view(pattern_name='unified_queue_data', permanent=False), name='old_ready_count'),
]
"""

# ==================== API文档说明 ====================
"""
统一数据API端点：/eshop/queue/unified-data/

返回数据结构示例：
{
    "success": true,
    "data": {
        "waiting_orders": [...],      // 等待队列数据
        "preparing_orders": [...],    // 制作中队列数据  
        "ready_orders": [...],        // 已就绪订单数据
        "badge_summary": {            // 徽章数据
            "waiting": 0,
            "preparing": 0,
            "ready": 0,
            "completed": 0
        }
    },
    "timestamp": "2024-01-19T10:30:00+08:00",
    "timezone": "Asia/Hong_Kong",
    "message": "数据加载成功"
}

前端调用示例：
fetch('/eshop/queue/unified-data/')
    .then(response => response.json())
    .then(data => {
        // 徽章数据：data.data.badge_summary
        // 等待队列：data.data.waiting_orders
        // 制作中队列：data.data.preparing_orders
        // 已就绪队列：data.data.ready_orders
    });
"""