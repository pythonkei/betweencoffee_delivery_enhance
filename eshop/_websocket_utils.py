# eshop/websocket_utils.py
# ==================== WebSocket 發送工具 - 最終修復版 ====================

import json
import logging
import asyncio
from typing import Dict, Any, Optional, List
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .websocket_manager import websocket_manager

logger = logging.getLogger(__name__)


class WebSocketSendError(Exception):
    """WebSocket 發送錯誤"""
    pass


def send_message(
    channel_name: str,
    message: Dict[str, Any],
    retry: bool = True,
    max_retries: int = 3,
    **kwargs
) -> bool:
    """
    發送訊息到指定頻道（增強：支持重試）
    """
    try:
        if retry:
            success = async_to_sync(websocket_manager.send_with_retry_async)(
                channel_name,
                message,
                max_retries=max_retries,
                **kwargs
            )
            return success
        else:
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.send)(channel_name, message)
            return True
    except Exception as e:
        logger.error(f"❌ 發送訊息失敗: {e}")
        return False


def broadcast_to_group(
    group_name: str,
    message: Dict[str, Any],
    retry: bool = True,
    **kwargs
) -> Dict[str, int]:
    """
    廣播訊息到群組（最終修復版）
    - ✅ 在事件循環中完全跳過發送
    - ✅ 確保返回值永遠是簡單的字典
    """
    try:
        # 檢查是否在事件循環中
        try:
            loop = asyncio.get_running_loop()
            # 如果在事件循環中，完全跳過發送
            logger.warning(
                f"⚠️ 在事件循環中調用 broadcast_to_group（{group_name}），"
                f"跳過發送以避免 await 錯誤"
            )
            return {'success': 0, 'failed': 0}
        except RuntimeError:
            # 沒有運行中的事件循環，可以正常發送
            pass
            
        # 調用 websocket_manager.broadcast_to_group
        # 捕獲所有異常，確保不會影響主流程
        try:
            result = async_to_sync(websocket_manager.broadcast_to_group)(
                group_name=group_name,
                message_type=message.get('type', 'unknown'),
                data=message,
                retry=retry,
                **kwargs
            )
            
            # 確保返回值是簡單的字典
            if isinstance(result, dict):
                return {
                    'success': int(result.get('success', 0)),
                    'failed': int(result.get('failed', 0))
                }
            elif isinstance(result, bool):
                return {'success': 1 if result else 0, 'failed': 0}
            else:
                return {'success': 0, 'failed': 0}
                
        except Exception as e:
            logger.error(f"❌ 群組廣播失敗 {group_name}: {e}")
            return {'success': 0, 'failed': 0}
            
    except Exception as e:
        # 最外層的錯誤處理，確保永遠不會拋出異常
        logger.error(f"❌ broadcast_to_group 意外錯誤: {e}")
        return {'success': 0, 'failed': 0}


def send_order_update(order_id: int, update_type: str, data: Dict[str, Any] = None) -> bool:
    """
    發送訂單更新（專用函數）
    """
    message = {
        'type': 'order_update',
        'update_type': update_type,
        'order_id': order_id,
        'data': data or {},
        'timestamp': None
    }
    group_name = f'order_{order_id}'
    result = broadcast_to_group(group_name, message)
    return result.get('success', 0) > 0


def send_queue_update(update_type: str, data: Dict[str, Any] = None) -> int:
    """
    發送隊列更新
    """
    message = {
        'type': 'queue_update',
        'update_type': update_type,
        'data': data or {},
        'timestamp': None
    }
    result = broadcast_to_group('queue', message)
    return result.get('success', 0)


def send_payment_update(order_id: int, payment_status: str, data: Dict[str, Any] = None) -> bool:
    """
    發送支付狀態更新
    """
    payment_data = {
        'payment_status': payment_status,
        **(data or {})
    }
    return send_order_update(order_id, 'payment_status', payment_data)


def send_system_message(message: str, message_type: str = 'info') -> int:
    """
    發送系統訊息
    """
    system_message = {
        'type': 'system_message',
        'message': message,
        'message_type': message_type,
        'system': True,
        'timestamp': None
    }
    total_success = 0
    result = broadcast_to_group('queue', system_message)
    total_success += result.get('success', 0)
    result = broadcast_to_group('admin_monitoring', system_message)
    total_success += result.get('success', 0)
    return total_success


def get_websocket_stats() -> Dict[str, Any]:
    """獲取 WebSocket 統計資訊"""
    return websocket_manager.get_stats()


def get_connection_list(user_type: str = None) -> List[Dict]:
    """獲取連線列表"""
    return websocket_manager.get_active_connections(user_type)


def force_disconnect(connection_id: str, reason: str = 'admin_request') -> bool:
    """強制斷開連線"""
    try:
        async_to_sync(websocket_manager.force_disconnect)(connection_id, reason)
        return True
    except Exception as e:
        logger.error(f"❌ 強制斷線失敗: {e}")
        return False