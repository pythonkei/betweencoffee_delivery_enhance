"""
佇列視圖模組 - 統一資料流版本（重構後）
使用共用模塊消除重複代碼，提高代碼質量
"""

import logging
from datetime import timedelta
import pytz

from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_GET, require_POST
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone

from eshop.models import OrderModel, CoffeeQueue
from eshop.order_status_manager import OrderStatusManager
from eshop.queue_manager_refactored import CoffeeQueueManager, force_sync_queue_and_orders
from eshop.time_calculation import unified_time_service
from eshop.views.queue_processors import (
    process_waiting_queues,
    process_preparing_queues,
    process_ready_orders,
    process_completed_orders,
    process_payment_pending_orders,
)

logger = logging.getLogger(__name__)


# ==================== 队列管理页面 ====================

@login_required
@staff_member_required
def queue_management(request):
    """队列管理主页面"""
    return render(request, 'eshop/queue_dashboard.html')


@login_required
@staff_member_required
def queue_dashboard(request):
    """队列仪表板"""
    return render(request, 'eshop/queue_dashboard.html')


@login_required
@staff_member_required
def staff_order_management(request):
    """员工订单管理页面"""
    try:
        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        total_orders_today = OrderModel.objects.filter(
            created_at__gte=today_start
        ).count()
        
        context = {
            'total_orders_today': total_orders_today,
            'current_time': now,
        }
        
        return render(request, 'admin/staff_order_management.html', context)
        
    except Exception as e:
        logger.error(f"员工订单管理页面加载失败: {str(e)}")
        return render(request, 'admin/staff_order_management.html', {
            'error': '加载订单管理页面失败',
            'total_orders_today': 0,
            'current_time': timezone.now(),
        })


# ==================== 统一队列数据API（核心功能） ====================

def get_unified_queue_data(request):
    """返回統一的隊列數據，格式符合前端 UnifiedDataManager 要求"""
    try:
        # 獲取香港時區與當前時間
        hk_tz = pytz.timezone('Asia/Hong_Kong')
        now = timezone.now().astimezone(hk_tz)
        
        # 使用現有的處理函數取得各類訂單數據
        payment_pending_orders = process_payment_pending_orders(now, hk_tz)
        waiting_orders = process_waiting_queues(now, hk_tz)
        preparing_orders = process_preparing_queues(now, hk_tz)
        ready_orders = process_ready_orders(now, hk_tz)
        completed_orders = process_completed_orders(now, hk_tz)
        
        # 徽章摘要
        badge_summary = {
            'payment_pending': len(payment_pending_orders),
            'waiting': len(waiting_orders),
            'preparing': len(preparing_orders),
            'ready': len(ready_orders),
            'completed': len(completed_orders),
        }
        
        # ✅ 關鍵：將所有數據包裝在 data 欄位中
        response_data = {
            'success': True,
            'data': {
                'payment_pending_orders': payment_pending_orders,
                'waiting_orders': waiting_orders,
                'preparing_orders': preparing_orders,
                'ready_orders': ready_orders,
                'completed_orders': completed_orders,
                'badge_summary': badge_summary,
            },
            'timestamp': timezone.now().isoformat(),
            'message': '隊列數據加載成功'
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        logger.error(f"獲取統一隊列數據失敗: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': str(e),
            'data': {
                'waiting_orders': [],
                'preparing_orders': [],
                'ready_orders': [],
                'completed_orders': [],
                'badge_summary': {'waiting': 0, 'preparing': 0, 'ready': 0, 'completed': 0}
            }
        }, status=500)


# ==================== 队列操作API ====================

@require_POST
@login_required
@staff_member_required
def start_preparation_api(request, order_id):
    """API：開始制作訂單（統一使用 OrderStatusManager）"""
    try:
        barista_name = request.user.get_full_name() or request.user.username
        
        result = OrderStatusManager.mark_as_preparing_manually(
            order_id=order_id,
            barista_name=barista_name
        )
        
        if not result['success']:
            return JsonResponse({
                'success': False,
                'message': result['message']
            }, status=400)
        
        order = result['order']
        items = order.get_items()
        coffee_count = sum(item.get('quantity', 1) for item in items if item.get('type') == 'coffee')
        
        logger.info(f"訂單 {order_id} 已開始制作，操作員: {barista_name}")
        
        return JsonResponse({
            'success': True,
            'message': f'已開始制作訂單 #{order_id}',
            'order_id': order_id,
            'status': order.status,
            'preparation_minutes': result['preparation_minutes'],
            'coffee_count': coffee_count,
        })
        
    except Exception as e:
        logger.error(f"開始制作訂單 {order_id} 失敗: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'系統錯誤: {str(e)}'
        }, status=500)


@require_POST
@login_required
@staff_member_required
def recalculate_all_times_api(request):
    """API：手動觸發統一時間計算"""
    try:
        queue_manager = CoffeeQueueManager()
        logger.info("🔄 API: 手動觸發統一時間計算")
        
        result = queue_manager.recalculate_all_order_times()
        
        if result.get('success'):
            try:
                from eshop.websocket_utils import send_queue_time_update
                send_queue_time_update()
            except Exception as ws_error:
                logger.error(f"發送WebSocket通知失敗: {str(ws_error)}")
            
            return JsonResponse({
                'success': True,
                'message': '統一時間計算完成',
                'details': result.get('details', {}),
                'timestamp': timezone.now().isoformat()
            })
        else:
            return JsonResponse({
                'success': False,
                'error': result.get('error', '未知錯誤'),
                'message': '時間計算失敗'
            }, status=500)
        
    except Exception as e:
        logger.error(f"手動觸發統一時間計算失敗: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': str(e),
            'message': '系統錯誤'
        }, status=500)


@require_POST
@login_required
@staff_member_required
def mark_as_ready_api(request, order_id):
    """標記訂單為就緒（兼容舊前端，但改用OrderStatusManager）"""
    try:
        staff_name = request.user.username
        logger.info(f"👨‍🍳 員工 {staff_name} 通過舊API標記訂單 #{order_id} 為就緒")
        
        result = OrderStatusManager.mark_as_ready_manually(order_id, staff_name)
        
        if result.get('success'):
            logger.info(f"✅ 舊API: 訂單 #{order_id} 已通過OrderStatusManager標記為就緒")
            
            # 修復：移除無法序列化的對象，只返回可序列化的數據
            serializable_result = {
                'success': True,
                'order_id': order_id,
                'message': f'訂單 #{order_id} 已標記為就緒',
                'staff_name': staff_name,
                'timestamp': timezone.now().isoformat()
            }
            
            # 如果有隊列項信息，添加可序列化的部分
            if 'queue_item' in result and result['queue_item']:
                queue_item = result['queue_item']
                serializable_result['queue_item'] = {
                    'id': queue_item.id,
                    'status': queue_item.status,
                    'actual_completion_time': queue_item.actual_completion_time.isoformat() if queue_item.actual_completion_time else None
                }
            
            return JsonResponse(serializable_result)
        else:
            logger.error(f"❌ 舊API: 標記訂單 #{order_id} 為就緒失敗: {result.get('error')}")
            return JsonResponse({
                'success': False,
                'error': result.get('error', '未知錯誤'),
                'message': result.get('message', '標記失敗')
            }, status=400)
            
    except Exception as e:
        logger.error(f"❌ 舊API處理失敗: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': f'伺服器錯誤: {str(e)}'
        }, status=500)


@require_POST
@login_required
@staff_member_required
def mark_as_collected(request, order_id):
    """標記訂單為已提取（兼容舊前端，但改用OrderStatusManager）"""
    try:
        staff_name = request.user.username
        logger.info(f"👨‍🍳 員工 {staff_name} 通過舊API標記訂單 #{order_id} 為已提取")
        
        result = OrderStatusManager.mark_as_completed_manually(order_id, staff_name)
        
        if result.get('success'):
            logger.info(f"✅ 舊API: 訂單 #{order_id} 已通過OrderStatusManager標記為已提取")
            
            # 修復：移除無法序列化的對象，只返回可序列化的數據
            serializable_result = {
                'success': True,
                'order_id': order_id,
                'message': f'訂單 #{order_id} 已標記為已提取',
                'staff_name': staff_name,
                'timestamp': timezone.now().isoformat()
            }
            
            return JsonResponse(serializable_result)
        else:
            logger.error(f"❌ 舊API: 標記訂單 #{order_id} 為已提取失敗: {result.get('error')}")
            return JsonResponse({
                'success': False,
                'error': result.get('error', '未知錯誤'),
                'message': result.get('message', '標記失敗')
            }, status=400)
            
    except Exception as e:
        logger.error(f"❌ 舊API處理失敗: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': f'伺服器錯誤: {str(e)}'
        }, status=500)


# ==================== 数据修复API ====================

@require_POST
@login_required
@staff_member_required
def repair_queue_data(request):
    """修复队列数据：重新计算所有队列时间"""
    try:
        logger.info("=== 开始修复队列数据 ===")
        queue_manager = CoffeeQueueManager()
        
        queue_manager.fix_queue_positions()
        queue_manager.update_estimated_times()
        
        logger.info("=== 队列数据修复完成 ===")
        
        return JsonResponse({
            'success': True,
            'message': '队列数据已修复',
        })
        
    except Exception as e:
        logger.error(f"修复队列数据失败: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_POST
@login_required
@staff_member_required
def force_sync_api(request):
    """强制同步API"""
    try:
        queue_manager = CoffeeQueueManager()
        
        queue_manager.fix_queue_positions()
        force_sync_queue_and_orders()
        queue_manager.update_estimated_times()
        
        return JsonResponse({
            'success': True,
            'message': '强制同步完成'
        })
        
    except Exception as e:
        logger.error(f"强制同步失败: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


# ==================== 订单详细信息API ====================

@require_GET
@login_required
@staff_member_required
def order_details_for_waiting_api(request, order_id):
    """API：获取等待订单详细信息"""
    try:
        order = get_object_or_404(OrderModel, id=order_id)
        
        if not request.user.is_staff:
            return JsonResponse({
                'success': False,
                'error': '无权访问此订单详细信息'
            }, status=403)
        
        items = order.get_items_with_chinese_options()
        
        coffee_count = sum(
            item.get('quantity', 1) 
            for item in order.get_items() 
            if item.get('type') == 'coffee'
        )
        
        order_data = {
            'id': order.id,
            'pickup_code': order.pickup_code,
            'total_price': str(order.total_price),
            'name': order.name,
            'phone': order.phone,
            'is_quick_order': order.is_quick_order,
            'payment_method': order.payment_method,
            'status': order.status,
            'created_at': order.created_at.isoformat(),
            'coffee_count': coffee_count,
            'items_count': len(items),
            'items': items,
            'has_coffee': coffee_count > 0,
        }
        
        return JsonResponse({
            'success': True,
            'order': order_data,
            'timestamp': timezone.now().isoformat()
        })
        
    except OrderModel.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': '订单不存在'
        }, status=404)
    except Exception as e:
        logger.error(f"获取等待订单详情失败: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


# ==================== 清理函数 ====================

@require_POST
@login_required
@staff_member_required
def cleanup_queue_data(request):
    """安全清理：只删除队列项，不删除订单 - 使用 OrderStatusManager"""
    try:
        deleted_count = CoffeeQueue.objects.all().count()
        CoffeeQueue.objects.all().delete()
        
        orders = OrderModel.objects.filter(status__in=['preparing', 'ready'])
        reset_count = 0
        error_count = 0
        
        for order in orders:
            result = OrderStatusManager.mark_as_waiting_manually(
                order_id=order.id,
                staff_name=request.user.username if request.user else 'system'
            )
            
            if result['success']:
                reset_count += 1
            else:
                error_count += 1
                logger.error(f"重置訂單 {order.id} 狀態為等待中失敗: {result['message']}")
        
        return JsonResponse({
            'success': True,
            'message': f'清理完成！刪除了 {deleted_count} 個隊列項，並重置了 {reset_count} 個訂單狀態為等待中。',
            'queue_items_deleted': deleted_count,
            'orders_reset': reset_count,
            'errors': error_count
        })
        
    except Exception as e:
        logger.error(f"清理隊列數據失敗: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)