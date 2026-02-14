# eshop/websocket_utils.py
# ==================== WebSocket 發送工具 - 最終調試版 ====================

import logging
import asyncio
from typing import Dict, Any, List
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .websocket_manager import websocket_manager

logger = logging.getLogger(__name__)


class SafeDictResult:
    """
    安全字典結果，用於在事件循環中返回。
    模擬字典操作，但不可 await，如果被 await 會拋出異常並打印調用棧，
    從而幫助定位錯誤的 await 調用。
    """
    def __init__(self, success=0, failed=0):
        self._success = success
        self._failed = failed
        self._dict = {'success': success, 'failed': failed}

    def __getitem__(self, key):
        return self._dict[key]

    def get(self, key, default=None):
        return self._dict.get(key, default)

    def __contains__(self, key):
        return key in self._dict

    def __repr__(self):
        return f"SafeDictResult(success={self._success}, failed={self._failed})"


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
            success = async_to_sync(
                websocket_manager.send_with_retry_async
            )(
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
    修復版本：總是返回普通字典，避免在事件循環中返回 coroutine 導致 await 錯誤
    增強版：在事件循環中時，使用線程執行同步調用
    """
    try:
        # 檢查是否在事件循環中
        try:
            loop = asyncio.get_running_loop()
            # 在事件循環中，使用線程執行同步調用
            logger.warning(
                f"⚠️ 在事件循環中調用 broadcast_to_group（{group_name}），"
                "使用線程執行同步調用"
            )
            
            import threading
            import queue
            
            result_queue = queue.Queue()
            
            def sync_broadcast():
                try:
                    result = websocket_manager.broadcast_to_group(
                        group_name=group_name,
                        message_type=message.get('type', 'unknown'),
                        data=message,
                        retry=retry,
                        **kwargs
                    )
                    result_queue.put(result)
                except Exception as e:
                    logger.error(f"線程中廣播失敗: {e}")
                    result_queue.put({'success': 0, 'failed': 0})
            
            thread = threading.Thread(target=sync_broadcast)
            thread.start()
            thread.join(timeout=5)  # 5秒超時
            
            if thread.is_alive():
                logger.error(f"廣播線程超時: {group_name}")
                return {'success': 0, 'failed': 0}
            
            try:
                result = result_queue.get_nowait()
            except queue.Empty:
                return {'success': 0, 'failed': 0}
            
            # 確保返回普通字典
            if isinstance(result, dict):
                return {
                    'success': int(result.get('success', 0)),
                    'failed': int(result.get('failed', 0))
                }
            elif isinstance(result, bool):
                return {'success': 1 if result else 0, 'failed': 0}
            else:
                return {'success': 0, 'failed': 0}
                
        except RuntimeError:
            # 沒有運行中的事件循環，正常同步執行
            pass

        # 同步版本（無事件循環）- 直接調用同步函數
        result = websocket_manager.broadcast_to_group(
            group_name=group_name,
            message_type=message.get('type', 'unknown'),
            data=message,
            retry=retry,
            **kwargs
        )

        # 確保返回普通字典
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


async def _async_broadcast_wrapper(group_name, message, retry, **kwargs):
    """異步包裝器，供事件循環中 await 使用"""
    try:
        await websocket_manager.async_broadcast_to_group(
            group_name=group_name,
            message_type=message.get('type', 'unknown'),
            data=message,
            retry=retry,
            **kwargs
        )
        return {'success': 1, 'failed': 0}
    except Exception as e:
        logger.error(f"❌ 異步群組廣播失敗 {group_name}: {e}")
        return {'success': 0, 'failed': 0}


def send_order_update(
    order_id: int,
    update_type: str,
    data: Dict[str, Any] = None
) -> bool:
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
    # SafeDictResult 也實現了 get 方法，所以這裡可以正常工作
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


def send_payment_update(
    order_id: int,
    payment_status: str,
    data: Dict[str, Any] = None
) -> bool:
    """
    發送支付狀態更新
    """
    payment_data = {
        'payment_status': payment_status,
        **(data or {})
    }
    return send_order_update(order_id, 'payment_status', payment_data)


def send_staff_action(
    order_id: int,
    action: str,
    staff_name: str,
    message: str = None
) -> bool:
    """
    發送員工操作通知
    """
    default_message = f"員工 {staff_name} 執行了 {action} 操作"
    staff_data = {
        'action': action,
        'staff_name': staff_name,
        'message': message or default_message,
        'timestamp': None
    }
    # 發送到訂單群組
    order_result = send_order_update(order_id, 'staff_action', staff_data)
    # 發送到管理員監控群組
    admin_message = {
        'type': 'staff_action',
        'order_id': order_id,
        'action': action,
        'staff_name': staff_name,
        'message': message or default_message,
        'timestamp': None
    }
    admin_result = broadcast_to_group('admin_monitoring', admin_message)
    return order_result or (admin_result.get('success', 0) > 0)


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


def force_disconnect(connection_id: str) -> bool:
    """強制斷開連線"""
    try:
        return async_to_sync(websocket_manager.disconnect)(connection_id, "強制斷開")
    except Exception as e:
        logger.error(f"❌ 強制斷線失敗: {e}")
        return False
