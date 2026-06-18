# eshop/views/websocket_views.py
"""
WebSocket 監控和管理 API
- 使用整合後的 WebSocketManager
- 所有端點都需要管理員權限
"""
import logging
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render 

# ✅ 補齊缺少的導入
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

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
        heartbeat_timeout = int(request.GET.get('heartbeat_timeout', 10))
        activity_timeout = int(request.GET.get('activity_timeout', 30))
        
        cleaned = websocket_manager.cleanup_inactive_connections(
            heartbeat_timeout_minutes=heartbeat_timeout,
            activity_timeout_minutes=activity_timeout
        )
        
        stats = websocket_manager.get_stats()
        
        return JsonResponse({
            'success': True,
            'stats': stats,
            'cleaned_count': cleaned,
            'timestamp': timezone.now().isoformat(),
        })
        
    except Exception as e:
        logger.error(f"❌ 獲取 WebSocket 統計失敗: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e),
        }, status=500)


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
        user_type = request.GET.get('user_type')
        connections = websocket_manager.get_active_connections(user_type)
        
        formatted_connections = []
        for conn in connections:
            formatted_connections.append({
                'id': conn['id'],
                'user_type': conn['user_info'].get('user_type', 'unknown'),
                'username': conn['user_info'].get('username', 'anonymous'),
                'user_id': conn['user_info'].get('user_id'),
                'connected_at': conn['connected_at'].isoformat(),
                'last_activity': conn['last_activity'].isoformat(),
                'message_count': conn['message_count'],
                'status': 'active',
                'channel_name': conn['channel_name'][:30] + '...' if len(conn['channel_name']) > 30 else conn['channel_name'],
            })
        
        return JsonResponse({
            'success': True,
            'connections': formatted_connections,
            'count': len(formatted_connections),
            'filters': {
                'user_type': user_type,
            },
            'timestamp': timezone.now().isoformat(),
        })
        
    except Exception as e:
        logger.error(f"❌ 獲取 WebSocket 連接列表失敗: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e),
        }, status=500)


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
        message = request.GET.get('message', '🧪 測試廣播訊息')
        message_type = request.GET.get('type', 'info')
        
        # ✅ 修正：使用 send_system_message，並判斷成功數 > 0
        success_count = send_system_message(message, message_type)
        success = success_count > 0
        
        return JsonResponse({
            'success': success,
            'message': '✅ 廣播訊息已發送' if success else '❌ 廣播失敗',
            'data': {
                'message': message,
                'type': message_type,
                'recipient_count': success_count,
            },
            'timestamp': timezone.now().isoformat(),
        })
        
    except Exception as e:
        logger.error(f"❌ 廣播測試失敗: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e),
        }, status=500)


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
        return JsonResponse({
            'success': True,
            'message': '📊 WebSocket 統計數據已重置',
            'timestamp': timezone.now().isoformat(),
        })
    except Exception as e:
        logger.error(f"❌ 重置統計失敗: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e),
        }, status=500)


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
        user_id = request.POST.get('user_id')
        connection_id = request.POST.get('connection_id')
        
        disconnected = []
        
        if connection_id:
            if websocket_manager.disconnect(connection_id, "管理員強制斷開"):
                disconnected.append(connection_id)
        elif user_id:
            for conn_id, conn_data in websocket_manager.connections.items():
                if conn_data['user_info'].get('user_id') == int(user_id) and conn_data['status'] == 'active':
                    websocket_manager.disconnect(conn_id, "管理員強制斷開")
                    disconnected.append(conn_id)
        
        return JsonResponse({
            'success': True,
            'disconnected_count': len(disconnected),
            'disconnected_connections': disconnected,
            'timestamp': timezone.now().isoformat(),
        })
    except Exception as e:
        logger.error(f"❌ 強制斷開連線失敗: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e),
        }, status=500)


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
        async_to_sync(channel_layer.send)('health_check', {
            'type': 'health_check',
            'timestamp': timezone.now().isoformat()
        })
        
        return JsonResponse({
            'success': True,
            'status': 'healthy',
            'active_connections': websocket_manager.stats['active_connections'],
            'timestamp': timezone.now().isoformat(),
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': timezone.now().isoformat(),
        }, status=503)



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
    return render(request, 'websocket_monitoring_dashboard.html')
