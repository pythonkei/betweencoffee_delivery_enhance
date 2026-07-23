# eshop/views/websocket_views.py
"""
WebSocket 監控和管理 API
- 使用整合後的 WebSocketManager
- 所有端點都需要管理員權限
"""
import logging

from asgiref.sync import async_to_sync

# ✅ 補齊缺少的導入
from channels.layers import get_channel_layer
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

# ✅ 修正：使用正確的函式名稱 send_system_message
from eshop.websocket_manager import websocket_manager
from eshop.websocket_utils import send_system_message

logger = logging.getLogger(__name__)


@require_GET
@login_required
@staff_member_required
def websocket_stats_api(request):
    """
    🔥 WebSocket 統計數據 API
    URL: /eshop/api/websocket/stats/
    權限: 僅管理員
    """
    try:
        # 清理不活動連線（可選參數）
        heartbeat_timeout = int(request.GET.get("heartbeat_timeout", 10))
        activity_timeout = int(request.GET.get("activity_timeout", 30))

        cleaned = websocket_manager.cleanup_inactive_connections(
            heartbeat_timeout_minutes=heartbeat_timeout,
            activity_timeout_minutes=activity_timeout,
        )

        stats = websocket_manager.get_stats()

        return JsonResponse(
            {
                "success": True,
                "stats": stats,
                "cleaned_count": cleaned,
                "timestamp": timezone.now().isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"❌ 獲取 WebSocket 統計失敗: {str(e)}")
        return JsonResponse(
            {
                "success": False,
                "error": str(e),
            },
            status=500,
        )


@require_GET
@login_required
@staff_member_required
def websocket_connections_api(request):
    """
    🔥 WebSocket 連線列表 API
    URL: /eshop/api/websocket/connections/?user_type=staff
    權限: 僅管理員
    """
    try:
        user_type = request.GET.get("user_type")
        connections = websocket_manager.get_active_connections(user_type)

        formatted_connections = []
        for conn in connections:
            formatted_connections.append(
                {
                    "id": conn["id"],
                    "user_type": conn["user_info"].get("user_type", "unknown"),
                    "username": conn["user_info"].get("username", "anonymous"),
                    "user_id": conn["user_info"].get("user_id"),
                    "connected_at": conn["connected_at"].isoformat(),
                    "last_activity": conn["last_activity"].isoformat(),
                    "message_count": conn["message_count"],
                    "status": "active",
                    "channel_name": (
                        conn["channel_name"][:30] + "..."
                        if len(conn["channel_name"]) > 30
                        else conn["channel_name"]
                    ),
                }
            )

        return JsonResponse(
            {
                "success": True,
                "connections": formatted_connections,
                "count": len(formatted_connections),
                "filters": {
                    "user_type": user_type,
                },
                "timestamp": timezone.now().isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"❌ 獲取 WebSocket 連接列表失敗: {str(e)}")
        return JsonResponse(
            {
                "success": False,
                "error": str(e),
            },
            status=500,
        )


@require_GET
@login_required
@staff_member_required
def websocket_broadcast_test(request):
    """
    🔥 系統廣播測試 API
    URL: /eshop/api/websocket/broadcast-test/?message=Hello&type=info
    權限: 僅管理員
    """
    try:
        message = request.GET.get("message", "🧪 測試廣播訊息")
        message_type = request.GET.get("type", "info")

        # ✅ 修正：使用 send_system_message，並判斷成功數 > 0
        success_count = send_system_message(message, message_type)
        success = success_count > 0

        return JsonResponse(
            {
                "success": success,
                "message": "✅ 廣播訊息已發送" if success else "❌ 廣播失敗",
                "data": {
                    "message": message,
                    "type": message_type,
                    "recipient_count": success_count,
                },
                "timestamp": timezone.now().isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"❌ 廣播測試失敗: {str(e)}")
        return JsonResponse(
            {
                "success": False,
                "error": str(e),
            },
            status=500,
        )


@require_POST
@login_required
@staff_member_required
@csrf_exempt
def websocket_reset_stats(request):
    """
    🔥 重置統計數據 API
    URL: /eshop/api/websocket/reset-stats/
    權限: 僅管理員
    方法: POST
    """
    try:
        websocket_manager.reset_stats()
        return JsonResponse(
            {
                "success": True,
                "message": "📊 WebSocket 統計數據已重置",
                "timestamp": timezone.now().isoformat(),
            }
        )
    except Exception as e:
        logger.error(f"❌ 重置統計失敗: {str(e)}")
        return JsonResponse(
            {
                "success": False,
                "error": str(e),
            },
            status=500,
        )


@require_POST
@login_required
@staff_member_required
@csrf_exempt
def websocket_disconnect_user(request):
    """
    🔥 強制斷開指定用戶的 WebSocket 連線
    URL: /eshop/api/websocket/disconnect-user/
    權限: 僅管理員
    方法: POST
    參數: user_id 或 connection_id
    """
    try:
        user_id = request.POST.get("user_id")
        connection_id = request.POST.get("connection_id")

        disconnected = []

        if connection_id:
            if websocket_manager.disconnect(connection_id, "管理員強制斷開"):
                disconnected.append(connection_id)
        elif user_id:
            for conn_id, conn_data in websocket_manager.connections.items():
                if (
                    conn_data["user_info"].get("user_id") == int(user_id)
                    and conn_data["status"] == "active"
                ):
                    websocket_manager.disconnect(conn_id, "管理員強制斷開")
                    disconnected.append(conn_id)

        return JsonResponse(
            {
                "success": True,
                "disconnected_count": len(disconnected),
                "disconnected_connections": disconnected,
                "timestamp": timezone.now().isoformat(),
            }
        )
    except Exception as e:
        logger.error(f"❌ 強制斷開連線失敗: {str(e)}")
        return JsonResponse(
            {
                "success": False,
                "error": str(e),
            },
            status=500,
        )


# ==================== HTTP Fallback API（公開，供前端輪詢）====================


@require_GET
def ws_fallback_api(request):
    """
    HTTP Fallback API - 當 WebSocket 不可用時，前端透過此 API 輪詢獲取最新狀態

    URL: /eshop/api/ws-fallback/
    權限: 公開（僅返回訂單基本狀態，無敏感資訊）

    查詢參數:
        order_ids: 逗號分隔的訂單 ID 列表（可選）
        queue: 是否返回隊列狀態（1 或 0）
        since: ISO 格式時間戳，只返回此時間後的更新

    返回:
        {
            'orders': { order_id: { status, payment_status, ... } },
            'queue': { waiting_count, preparing_count, ... },
            'updates': [ { type, ... }, ... ],
            'timestamp': '...'
        }
    """
    try:
        from django.utils import timezone

        from eshop.models import CoffeeQueue, OrderModel

        response_data = {
            "orders": {},
            "queue": None,
            "updates": [],
            "timestamp": timezone.now().isoformat(),
        }

        # 1. 查詢訂單狀態
        order_ids_str = request.GET.get("order_ids", "")
        if order_ids_str:
            order_ids = [
                int(x.strip()) for x in order_ids_str.split(",") if x.strip().isdigit()
            ]
            if order_ids:
                orders = OrderModel.objects.filter(id__in=order_ids).select_related()
                for order in orders:
                    queue_info = None
                    try:
                        queue = CoffeeQueue.objects.get(order=order)
                        queue_info = {
                            "position": queue.position,
                            "estimated_completion_time": (
                                queue.estimated_completion_time.isoformat()
                                if queue.estimated_completion_time
                                else None
                            ),
                        }
                    except CoffeeQueue.DoesNotExist:
                        pass

                    response_data["orders"][str(order.id)] = {
                        "order_id": order.id,
                        "status": order.status,
                        "status_display": order.get_status_display(),
                        "payment_status": order.payment_status,
                        "payment_method": order.payment_method,
                        "pickup_code": order.pickup_code,
                        "queue_position": (
                            queue_info["position"] if queue_info else None
                        ),
                        "estimated_completion_time": (
                            queue_info["estimated_completion_time"]
                            if queue_info
                            else None
                        ),
                    }

        # 2. 查詢隊列狀態
        if request.GET.get("queue") == "1":
            waiting_count = CoffeeQueue.objects.filter(status="waiting").count()
            preparing_count = CoffeeQueue.objects.filter(status="preparing").count()
            ready_count = CoffeeQueue.objects.filter(status="ready").count()

            response_data["queue"] = {
                "waiting_count": waiting_count,
                "preparing_count": preparing_count,
                "ready_count": ready_count,
                "total_active": waiting_count + preparing_count,
            }

        return JsonResponse(response_data)

    except Exception as e:
        logger.error(f"❌ Fallback API 錯誤: {e}")
        return JsonResponse(
            {"error": str(e), "timestamp": timezone.now().isoformat()}, status=500
        )


# ==================== 健康檢查端點（公開）====================


@require_GET
def websocket_health_check(request):
    """
    WebSocket 服務健康檢查
    URL: /eshop/api/websocket/health/
    權限: 公開
    """
    try:
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.send)(
            "health_check",
            {"type": "health_check", "timestamp": timezone.now().isoformat()},
        )

        return JsonResponse(
            {
                "success": True,
                "status": "healthy",
                "active_connections": websocket_manager.stats["active_connections"],
                "timestamp": timezone.now().isoformat(),
            }
        )
    except Exception as e:
        return JsonResponse(
            {
                "success": False,
                "status": "unhealthy",
                "error": str(e),
                "timestamp": timezone.now().isoformat(),
            },
            status=503,
        )


# ==================== WebSocket 監控儀表板頁面 ====================


@require_GET
@login_required
@staff_member_required
def websocket_monitor_dashboard(request):
    """
    WebSocket 監控儀表板頁面
    URL: /eshop/staff/websocket-monitor/
    權限: 僅管理員
    """
    return render(request, "websocket_monitoring_dashboard.html")
