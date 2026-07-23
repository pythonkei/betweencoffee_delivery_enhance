# eshop/consumers.py
"""
WebSocket Consumer - 整合版本（增強訂單狀態推送）
- 處理訂單專屬連線 (ws/order/<order_id>/)
- 處理隊列廣播連線 (ws/queue/)
- 統一使用 WebSocketManager 管理連線
"""
import asyncio
import json
import logging

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.utils import timezone

# ✅ 導入 WebSocketManager
from .websocket_manager import websocket_manager

logger = logging.getLogger(__name__)


class BaseOrderConsumer(AsyncWebsocketConsumer):
    """訂單 WebSocket Consumer 基類 - 包含共用方法"""

    async def _get_user_info(self):
        """獲取使用者資訊（共用方法）"""
        user = self.scope["user"]
        user_id = user.id if user.is_authenticated else None
        user_type = (
            "staff"
            if user.is_staff
            else "customer" if user.is_authenticated else "guest"
        )

        return {
            "user_id": user_id,
            "username": user.username if user.is_authenticated else "anonymous",
            "user_type": user_type,
        }

    async def _send_json(self, data):
        """發送 JSON 訊息（共用方法）"""
        await self.send(text_data=json.dumps(data))

    async def receive(self, text_data=None, bytes_data=None):
        """接收客戶端訊息（共用方法）"""
        try:
            data = json.loads(text_data)
            msg_type = data.get("type")

            # ----- 處理 ping（心跳）-----
            if msg_type == "ping":
                # 更新 WebSocketManager 中的心跳時間
                if hasattr(self, "connection_id"):
                    websocket_manager.update_heartbeat(self.connection_id)

                # 回應 pong，包含服務端時間戳和延遲資訊
                await self._send_json(
                    {
                        "type": "pong",
                        "client_time": data.get("client_time"),
                        "server_time": timezone.now().timestamp(),
                        "timestamp": timezone.now().isoformat(),
                    }
                )
                logger.debug(f"❤️ 收到 ping，回應 pong: {self.channel_name}")

            # ----- 處理 sync_request（重連同步請求）-----
            elif msg_type == "sync_request":
                await self._handle_sync_request(data)

            # ----- 處理 subscribe_order（訂閱訂單）-----
            elif msg_type == "subscribe_order":
                order_id = data.get("order_id")
                if order_id:
                    room_group = f"order_{order_id}"
                    await self.channel_layer.group_add(room_group, self.channel_name)
                    logger.info(f"📋 客戶端訂閱訂單: {order_id}")
                    await self._send_json(
                        {
                            "type": "subscribed",
                            "order_id": order_id,
                            "timestamp": timezone.now().isoformat(),
                        }
                    )

            # ----- 處理 subscribe_queue（訂閱隊列）-----
            elif msg_type == "subscribe_queue":
                if (
                    hasattr(self, "room_group_name")
                    and self.room_group_name == "queue_updates"
                ):
                    # 已在隊列群組中
                    pass
                else:
                    await self.channel_layer.group_add(
                        "queue_updates", self.channel_name
                    )
                    logger.info(f"📋 客戶端訂閱隊列")
                    await self._send_json(
                        {
                            "type": "subscribed",
                            "queue": True,
                            "timestamp": timezone.now().isoformat(),
                        }
                    )

        except json.JSONDecodeError:
            logger.warning(f"⚠️ 無效的 JSON 格式: {text_data}")
        except Exception as e:
            logger.error(f"❌ 處理接收訊息時發生錯誤: {e}")

    async def _handle_sync_request(self, data):
        """
        處理客戶端重連後的同步請求
        客戶端在頁面恢復可見或重連成功後發送此請求，
        服務端回傳當前訂單/隊列的完整狀態
        """
        logger.info(f"🔄 收到同步請求: {getattr(self, 'connection_id', 'unknown')}")

        # 更新心跳時間
        if hasattr(self, "connection_id"):
            websocket_manager.update_heartbeat(self.connection_id)

        # 子類覆蓋此方法實現具體同步邏輯
        await self._send_json(
            {
                "type": "sync_ack",
                "timestamp": timezone.now().isoformat(),
                "message": "同步請求已接收",
            }
        )


class OrderConsumer(BaseOrderConsumer):
    """訂單專屬 WebSocket Consumer - 用於單個訂單的即時更新"""

    async def connect(self):
        """處理 WebSocket 連線"""
        # 從 URL 獲取訂單 ID
        self.order_id = self.scope["url_route"]["kwargs"]["order_id"]
        self.room_group_name = f"order_{self.order_id}"

        # 檢查訂單是否存在
        order_exists = await self._check_order_exists()
        if not order_exists:
            logger.warning(f"❌ 訂單 {self.order_id} 不存在，拒絕連線")
            await self.close()
            return

        # 獲取使用者資訊
        user_info = await self._get_user_info()
        self.user_info = user_info
        self.connection_id = f"order_{self.order_id}_{self.channel_name}"

        # 接受連線
        await self.accept()

        # ✅ 註冊連線到 WebSocketManager
        websocket_manager.register_connection(
            connection_id=self.connection_id,
            channel_name=self.channel_name,
            user_info=user_info,
        )

        # 加入訂單群組
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        # 啟動心跳監控任務
        self.heartbeat_task = asyncio.create_task(self._heartbeat_checker())

        # ✅ 連線成功後，立即發送當前訂單狀態
        await self.send_current_status()

        logger.info(
            f"✅ 訂單 Consumer 連線成功: {self.connection_id}, 用戶: {user_info['username']}"
        )

    async def _handle_sync_request(self, data):
        """
        訂單 Consumer 重連同步請求處理
        客戶端重連後，發送當前訂單的完整狀態
        """
        logger.info(f"🔄 訂單 Consumer 同步請求: 訂單 {self.order_id}")
        await self.send_current_status()
        await self._send_json(
            {
                "type": "sync_complete",
                "order_id": self.order_id,
                "timestamp": timezone.now().isoformat(),
            }
        )

    async def disconnect(self, close_code):
        """處理 WebSocket 斷線"""
        # 取消心跳任務
        if hasattr(self, "heartbeat_task"):
            self.heartbeat_task.cancel()

        # ✅ 從 WebSocketManager 斷開
        if hasattr(self, "connection_id"):
            websocket_manager.disconnect(
                self.connection_id, f"close_code: {close_code}"
            )

        # 離開訂單群組
        if hasattr(self, "room_group_name"):
            await self.channel_layer.group_discard(
                self.room_group_name, self.channel_name
            )

        logger.info(
            f"🔌 訂單 Consumer 斷線: 訂單 {getattr(self, 'order_id', 'unknown')}, code: {close_code}"
        )

    @database_sync_to_async
    def _check_order_exists(self):
        """檢查訂單是否存在"""
        from .models import OrderModel

        return OrderModel.objects.filter(id=self.order_id).exists()

    @database_sync_to_async
    def _get_order_status_data(self):
        """
        從資料庫獲取訂單當前狀態、隊列位置、預計完成時間等完整資訊
        供連線時立即推送，以及 event 資料不完整時備用
        """
        from django.utils import timezone

        from .models import CoffeeQueue, OrderModel
        from .order_status_manager import OrderStatusManager

        try:
            order = OrderModel.objects.get(id=self.order_id)
            status_manager = OrderStatusManager(order)
            status_info = status_manager.get_display_status()

            # 獲取隊列資訊（如果存在）
            queue_info = None
            try:
                queue = CoffeeQueue.objects.get(order=order)

                # 🔧 修復：計算剩餘秒數（如果預計完成時間存在）
                remaining_seconds = None
                if queue.estimated_completion_time:
                    now = timezone.now()
                    if queue.estimated_completion_time > now:
                        remaining_seconds = int(
                            (queue.estimated_completion_time - now).total_seconds()
                        )
                    else:
                        remaining_seconds = 0

                queue_info = {
                    "position": queue.position,
                    "estimated_time": (
                        queue.estimated_completion_time.isoformat()
                        if queue.estimated_completion_time
                        else None
                    ),
                    "remaining_seconds": remaining_seconds,
                }
            except CoffeeQueue.DoesNotExist:
                pass

            return {
                "order_id": order.id,
                "status": order.status,
                "status_display": order.get_status_display(),
                "payment_status": order.payment_status,
                "payment_method": order.payment_method,
                "pickup_code": order.pickup_code,
                "estimated_completion_time": status_info.get("estimated_time"),
                "queue_position": queue_info["position"] if queue_info else None,
                "remaining_seconds": (
                    queue_info["remaining_seconds"] if queue_info else None
                ),
                "progress_percentage": status_info.get("progress_percentage", 0),
                "progress_display": status_info.get("progress_display", ""),
            }
        except OrderModel.DoesNotExist:
            return None

    async def send_current_status(self):
        """主動發送當前訂單狀態給前端"""
        status_data = await self._get_order_status_data()
        if status_data:
            await self._send_json(
                {
                    "type": "order_status",
                    "data": status_data,
                    "timestamp": timezone.now().isoformat(),
                }
            )
            logger.debug(f"📤 發送當前訂單狀態: {self.order_id}")

    async def _heartbeat_checker(self):
        """心跳監控任務"""
        try:
            while True:
                await asyncio.sleep(30)

                conn_info = websocket_manager.get_connection(self.connection_id)
                if not conn_info:
                    break

                # ✅ 由 WebSocketManager 統一判斷超時，這裡只負責更新心跳
                websocket_manager.update_heartbeat(self.connection_id)

        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"❌ 心跳檢查任務錯誤: {e}")

    # ========== 訊息處理方法（由 channel_layer.group_send 觸發）==========

    # ============================================================
    # 🔧 修復：新增 order_update 方法
    # 說明：websocket_utils.py 中的 broadcast_to_group 使用
    #       message['type'] = 'order_update' 來路由消息
    #       channel layer 會自動將 type 中的 '.' 替換為 '_'
    #       所以需要定義 order_update 方法來接收這些消息
    # ============================================================
    async def order_update(self, event):
        """
        訂單更新路由器（來自 websocket_utils.send_order_update）

        此方法接收所有類型的訂單更新消息，並根據 update_type 分發處理

        event 格式：
            {
                'type': 'order_update',
                'update_type': 'status' | 'status_change' | 'payment_status' | ...,
                'order_id': 123,
                'data': {...}
            }
        """
        update_type = event.get("update_type", "")

        # 根據 update_type 分發到對應的處理方法
        if update_type in ("status", "status_change"):
            # 狀態變更 → 調用 order_status_update
            await self.order_status_update(event)
        elif update_type == "payment_status":
            # 支付狀態 → 調用 payment_status_update
            await self.payment_status_update(event)
        elif update_type == "queue_position":
            # 排隊位置 → 調用 queue_position_update
            await self.queue_position_update(event)
        elif update_type == "estimated_time":
            # 預計時間 → 調用 estimated_time_update
            await self.estimated_time_update(event)
        elif update_type == "staff_action":
            # 員工操作 → 直接發送給前端
            await self._send_json(
                {
                    "type": "staff_action",
                    "data": event.get("data", {}),
                    "timestamp": timezone.now().isoformat(),
                }
            )
        else:
            # 未知類型：記錄日誌並直接轉發給前端
            logger.warning(f"⚠️ 未知的 update_type: {update_type}")
            await self._send_json(
                {
                    "type": "order_update",
                    "update_type": update_type,
                    "data": event.get("data", {}),
                    "timestamp": timezone.now().isoformat(),
                }
            )

    async def order_status_update(self, event):
        """
        訂單狀態更新（來自 send_order_update 或 order_update 分發）
        event 應包含：
            - order_id
            - status
            - status_display (建議)
            - estimated_time (可選)
            - queue_position (可選)
            - remaining_seconds (可選)
            - progress_percentage (可選)
            - message (可選)
        """
        # 若 event 中缺少部分欄位，從資料庫補齊（非同步查詢）
        if (
            "status_display" not in event
            or "estimated_time" not in event
            or "queue_position" not in event
        ):
            status_data = await self._get_order_status_data()
            if status_data:
                event["status_display"] = status_data["status_display"]
                event["estimated_time"] = status_data["estimated_completion_time"]
                event["queue_position"] = status_data["queue_position"]
                event["remaining_seconds"] = status_data["remaining_seconds"]
                event["progress_percentage"] = status_data["progress_percentage"]

        # ✅ 修復：發送兩種格式的消息以確保兼容性
        # 格式1: 統一訂單更新器格式 {type: 'order_status', data: {...}}
        await self._send_json(
            {
                "type": "order_status",
                "data": {
                    "order_id": event.get("order_id", self.order_id),
                    "status": event.get("status"),
                    "status_display": event.get("status_display"),
                    "estimated_time": event.get("estimated_time"),
                    "queue_position": event.get("queue_position"),
                    "remaining_seconds": event.get("remaining_seconds"),
                    "progress_percentage": event.get("progress_percentage"),
                    "message": event.get("message", ""),
                },
                "timestamp": timezone.now().isoformat(),
            }
        )

        # 格式2: 直接狀態數據格式（兼容舊版客戶端）
        await self._send_json(
            {
                "type": "order_status_update",
                "order_id": event.get("order_id", self.order_id),
                "status": event.get("status"),
                "status_display": event.get("status_display"),
                "estimated_time": event.get("estimated_time"),
                "queue_position": event.get("queue_position"),
                "remaining_seconds": event.get("remaining_seconds"),
                "progress_percentage": event.get("progress_percentage"),
                "message": event.get("message", ""),
                "timestamp": timezone.now().isoformat(),
            }
        )

        order_id = event.get("order_id", self.order_id)
        status = event.get("status")
        logger.debug(f"📤 發送雙格式訂單狀態更新: 訂單 {order_id}, 狀態: {status}")

    async def queue_position_update(self, event):
        """隊列位置更新（專門針對排隊位置變化）"""
        await self._send_json(
            {
                "type": "queue_position",
                "order_id": event.get("order_id", self.order_id),
                "position": event.get("position"),
                "estimated_time": event.get("estimated_time"),
                "remaining_seconds": event.get("remaining_seconds"),
                "timestamp": timezone.now().isoformat(),
            }
        )

    async def estimated_time_update(self, event):
        """預計完成時間更新（專門針對時間變化）"""
        await self._send_json(
            {
                "type": "estimated_time",
                "order_id": event.get("order_id", self.order_id),
                "estimated_time": event.get("estimated_time"),
                "remaining_seconds": event.get("remaining_seconds"),
                "timestamp": timezone.now().isoformat(),
            }
        )

    async def payment_status_update(self, event):
        """支付狀態更新"""
        await self._send_json(
            {
                "type": "payment_status",
                "order_id": event.get("order_id", self.order_id),
                "payment_status": event.get("payment_status"),
                "payment_method": event.get("payment_method", ""),
                "message": event.get("message", ""),
                "timestamp": timezone.now().isoformat(),
            }
        )

    async def order_ready_notification(self, event):
        """訂單就緒通知"""
        await self._send_json(
            {
                "type": "order_ready",
                "order_id": event.get("order_id", self.order_id),
                "pickup_code": event.get("pickup_code"),
                "customer_name": event.get("customer_name"),
                "timestamp": timezone.now().isoformat(),
            }
        )


class TestConsumer(AsyncWebsocketConsumer):
    """測試 WebSocket Consumer - 用於診斷工具測試"""

    async def connect(self):
        """處理 WebSocket 連線"""
        # 接受連線
        await self.accept()

        logger.info(f"✅ 測試 Consumer 連線成功: {self.channel_name}")

        # 立即發送歡迎消息
        await self.send(
            text_data=json.dumps(
                {
                    "type": "welcome",
                    "message": "測試 WebSocket 連接成功！",
                    "timestamp": timezone.now().isoformat(),
                }
            )
        )

    async def disconnect(self, close_code):
        """處理 WebSocket 斷線"""
        logger.info(f"🔌 測試 Consumer 斷線: {self.channel_name}, code: {close_code}")

    async def receive(self, text_data):
        """接收客戶端訊息"""
        try:
            data = json.loads(text_data)
            msg_type = data.get("type")

            if msg_type == "ping":
                # 回應 ping
                await self.send(
                    text_data=json.dumps(
                        {
                            "type": "pong",
                            "message": "收到 ping",
                            "timestamp": timezone.now().isoformat(),
                        }
                    )
                )
                logger.debug(
                    f"❤️ 測試 Consumer 收到 ping，回應 pong: {self.channel_name}"
                )

            elif msg_type == "echo":
                # 回顯消息
                message = data.get("message", "")
                await self.send(
                    text_data=json.dumps(
                        {
                            "type": "echo_response",
                            "message": f"回顯: {message}",
                            "original_message": message,
                            "timestamp": timezone.now().isoformat(),
                        }
                    )
                )

            else:
                # 未知消息類型
                await self.send(
                    text_data=json.dumps(
                        {
                            "type": "unknown_message",
                            "received": data,
                            "timestamp": timezone.now().isoformat(),
                        }
                    )
                )

        except json.JSONDecodeError:
            logger.warning(f"⚠️ 測試 Consumer 無效的 JSON 格式: {text_data}")
            await self.send(
                text_data=json.dumps(
                    {
                        "type": "error",
                        "message": "無效的 JSON 格式",
                        "timestamp": timezone.now().isoformat(),
                    }
                )
            )


class QueueConsumer(BaseOrderConsumer):
    """隊列 WebSocket Consumer - 用於隊列頁面的即時廣播"""

    async def connect(self):
        """處理 WebSocket 連線"""
        self.room_group_name = "queue_updates"

        # 🔧 修復：在 accept() 之前先初始化資料庫連線
        # Render 生產環境中，PostgreSQL 連線在空閒後會被關閉，
        # 導致後續廣播時出現 "django.db.utils.InterfaceError: connection already closed"
        await self._ensure_db_connection()

        # 獲取使用者資訊
        user_info = await self._get_user_info()
        self.user_info = user_info
        self.connection_id = f"queue_{self.channel_name}"

        # 接受連線
        await self.accept()

        # ✅ 註冊連線到 WebSocketManager
        websocket_manager.register_connection(
            connection_id=self.connection_id,
            channel_name=self.channel_name,
            user_info=user_info,
        )

        # 加入隊列群組
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        # 啟動心跳監控任務
        self.heartbeat_task = asyncio.create_task(self._heartbeat_checker())

        logger.info(
            f"✅ 隊列 Consumer 連線成功: {self.connection_id}, 用戶: {user_info['username']}"
        )

    @database_sync_to_async
    def _ensure_db_connection(self):
        """
        初始化資料庫連線，避免 WebSocket 連線後出現 connection already closed

        在 Render 生產環境中，PostgreSQL 連線在空閒後會被資料庫端關閉。
        此方法在 accept() 之前強制初始化資料庫連線池，確保後續查詢正常。
        """
        from django.db import connection

        connection.ensure_connection()
        return True

    async def disconnect(self, close_code):
        """處理 WebSocket 斷線"""
        # 取消心跳任務
        if hasattr(self, "heartbeat_task"):
            self.heartbeat_task.cancel()

        # ✅ 從 WebSocketManager 斷開
        if hasattr(self, "connection_id"):
            websocket_manager.disconnect(
                self.connection_id, f"close_code: {close_code}"
            )

        # 離開隊列群組
        if hasattr(self, "room_group_name"):
            await self.channel_layer.group_discard(
                self.room_group_name, self.channel_name
            )

        logger.info(
            f"🔌 隊列 Consumer 斷線: {getattr(self, 'connection_id', 'unknown')}, code: {close_code}"
        )

    async def _heartbeat_checker(self):
        """心跳監控任務"""
        try:
            while True:
                await asyncio.sleep(30)

                conn_info = websocket_manager.get_connection(self.connection_id)
                if not conn_info:
                    break

                # ✅ 由 WebSocketManager 統一判斷超時，這裡只負責更新心跳
                websocket_manager.update_heartbeat(self.connection_id)

        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"❌ 心跳檢查任務錯誤: {e}")

    # ========== 訊息處理方法（由 channel_layer.group_send 觸發）==========

    async def queue_update(self, event):
        """隊列更新（通用）"""
        await self._send_json(
            {
                "type": "queue_update",
                "action": event.get("action", "update"),
                "order_id": event.get("order_id"),
                "position": event.get("position"),
                "queue_type": event.get("queue_type", "waiting"),
                "data": event.get("data", {}),
                "timestamp": timezone.now().isoformat(),
            }
        )

    async def new_order_notification(self, event):
        """新訂單通知"""
        await self._send_json(
            {
                "type": "new_order",
                "order_id": event.get("order_id"),
                "customer_name": event.get("customer_name"),
                "total_price": event.get("total_price"),
                "items_count": event.get("items_count"),
                "timestamp": timezone.now().isoformat(),
            }
        )

    async def order_ready(self, event):
        """訂單就緒通知"""
        await self._send_json(
            {
                "type": "order_ready",
                "order_id": event.get("order_id"),
                "pickup_code": event.get("pickup_code"),
                "customer_name": event.get("customer_name"),
                "timestamp": timezone.now().isoformat(),
            }
        )

    async def payment_update(self, event):
        """支付更新通知"""
        await self._send_json(
            {
                "type": "payment_update",
                "order_id": event.get("order_id"),
                "payment_status": event.get("payment_status"),
                "payment_method": event.get("payment_method", ""),
                "message": event.get("message", ""),
                "timestamp": timezone.now().isoformat(),
            }
        )

    async def order_update(self, event):
        """
        訂單更新轉發（來自 send_order_update 發送到 order_{order_id} 群組）

        當 QueueConsumer 的客戶端通過 subscribe_order 訂閱了特定訂單時，
        會收到 order_update 訊息。此方法將其轉發為 queue_update 格式，
        確保前端能正確處理。
        """
        await self._send_json(
            {
                "type": "queue_update",
                "action": "order_update",
                "order_id": event.get("order_id"),
                "update_type": event.get("update_type", "status"),
                "data": event.get("data", {}),
                "timestamp": timezone.now().isoformat(),
            }
        )

    async def system_message(self, event):
        """系統訊息廣播"""
        await self._send_json(
            {
                "type": "system",
                "message": event.get("message"),
                "message_type": event.get("message_type", "info"),
                "timestamp": timezone.now().isoformat(),
            }
        )
