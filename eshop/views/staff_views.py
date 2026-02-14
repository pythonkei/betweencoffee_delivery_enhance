# eshop/views/staff_views.py

import json
import logging
import traceback
from datetime import timedelta

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.http import require_GET, require_POST
from django.utils import timezone
from django.contrib import messages
from django.db.models import Count
from django.core.exceptions import PermissionDenied

from eshop.models import OrderModel, CoffeeQueue
from eshop.time_service import time_service
from eshop.queue_manager import CoffeeQueueManager
from eshop.order_status_manager import OrderStatusManager


# 嘗試導入WebSocket工具（移除 send_payment_update）
try:
    from eshop.websocket_utils import send_order_update, send_queue_update
    WEBSOCKET_ENABLED = True
except ImportError:
    WEBSOCKET_ENABLED = False
    
    def send_order_update(order_id, update_type, data=None):
        logging.getLogger(__name__).info(f"WebSocket占位: 訂單更新 - {order_id}, {update_type}, data={data}")
        return True
    
    def send_queue_update(action, order_id, position=None, queue_type='waiting', data=None):
        logging.getLogger(__name__).info(f"WebSocket占位: 隊列更新 - {order_id}, {action}")
        return True

logger = logging.getLogger(__name__)


# ==================== 员工订单管理视图 ====================

@login_required
@staff_member_required
def staff_order_management(request):
    """员工订单管理页面"""
    try:
        # 获取当前时间
        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # 获取制作中订单
        preparing_orders = OrderModel.objects.filter(
            status='preparing',
            payment_status="paid"
        ).order_by('-created_at')
        
        # 获取已就绪订单
        ready_orders = OrderModel.objects.filter(
            status='ready',
            payment_status="paid",
            picked_up_at__isnull=True
        ).order_by('-ready_at', '-updated_at')
        
        # 获取最近4小时已提取的订单
        recent_completed_orders = OrderModel.objects.filter(
            status='completed',
            picked_up_at__isnull=False,
            picked_up_at__gte=now - timedelta(hours=4)
        ).order_by('-picked_up_at')
        
        # 获取今日订单总数
        total_orders_today = OrderModel.objects.filter(
            created_at__gte=today_start
        ).count()
        
        context = {
            'preparing_orders': preparing_orders,
            'ready_orders': ready_orders,
            'recent_completed_orders': recent_completed_orders,
            'total_orders_today': total_orders_today,
            'current_time': now,
        }
        
        return render(request, 'admin/staff_order_management.html', context)
        
    except Exception as e:
        logger.error(f"员工订单管理页面加载失败: {str(e)}")
        return render(request, 'admin/staff_order_management.html', {
            'error': '加载订单管理页面失败',
            'preparing_orders': [],
            'ready_orders': [],
            'recent_completed_orders': [],
            'total_orders_today': 0,
            'current_time': timezone.now(),
        })


# ==================== 订单状态管理API ====================

@require_POST
@login_required
@staff_member_required
def mark_order_ready(request, order_id):
    """員工手動標記訂單為就緒 - 使用 OrderStatusManager"""
    try:
        staff_name = request.user.get_full_name() or request.user.username
        
        result = OrderStatusManager.mark_as_ready_manually(
            order_id=order_id,
            staff_name=staff_name
        )
        
        if result['success']:
            messages.success(request, f'訂單 #{order_id} 已標記為就緒')
        else:
            messages.error(request, f'操作失敗: {result["message"]}')
        
        return redirect('eshop:staff_order_management')
        
    except Exception as e:
        messages.error(request, f'系統錯誤: {str(e)}')
        return redirect('eshop:staff_order_management')


@require_POST
@login_required
@staff_member_required
def mark_order_collected(request, order_id):
    """員工手動標記訂單為已提取 - 使用 OrderStatusManager"""
    try:
        staff_name = request.user.get_full_name() or request.user.username
        
        result = OrderStatusManager.mark_as_completed_manually(
            order_id=order_id,
            staff_name=staff_name
        )
        
        if result['success']:
            messages.success(request, f'訂單 #{order_id} 已標記為已提取')
        else:
            messages.error(request, f'操作失敗: {result["message"]}')
        
        return redirect('eshop:staff_order_management')
        
    except Exception as e:
        messages.error(request, f'系統錯誤: {str(e)}')
        return redirect('eshop:staff_order_management')
