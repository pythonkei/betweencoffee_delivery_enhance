# eshop/consumers.py
"""
WebSocket Consumer - 整合版本（增強訂單狀態推送）
- 處理訂單專屬連線 (ws/order/<order_id>/)
- 處理隊列廣播連線 (ws/queue/)
- 統一使用 WebSocketManager 管理連線
"""
import json
import logging
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone

# ✅ 導入 WebSocketManager
from .websocket_manager import websocket_manager

logger = logging.getLogger(__name__)


class BaseOrderConsumer(AsyncWebsocketConsumer):
    """訂單 WebSocket Consumer 基類 - 包含共用方法"""
    
    async def _get_user_info(self):
        """獲取使用者資訊（共用方法）"""
        user = self.scope['user']
        user_id = user.id if user.is_authenticated else None
        user_type = 'staff' if user.is_staff else 'customer' if user.is_authenticated else 'guest'
        
        return {
            'user_id': user_id,
            'username': user.username if user.is_authenticated else 'anonymous',
            'user_type': user_type,
        }
    
    async def _send_json(self, data):
        """發送 JSON 訊息（共用方法）"""
        await self.send(text_data=json.dumps(data))
    
    async def receive(self, text_data=None, bytes_data=None):
        """接收客戶端訊息（共用方法）"""
        try:
            data = json.loads(text_data)
            msg_type = data.get('type')
            
            # ----- 處理 ping（心跳）-----
            if msg_type == 'ping':
                # 更新 WebSocketManager 中的心跳時間
                if hasattr(self, 'connection_id'):
                    websocket_manager.update_heartbeat(self.connection_id)
                
                await self._send_json({
                    'type': 'pong',
                    'timestamp': timezone.now().isoformat()
                })
                logger.debug(f"❤️ 收到 ping，回應 pong: {self.channel_name}")
            
        except json.JSONDecodeError:
            logger.warning(f"⚠️ 無效的 JSON 格式: {text_data}")
        except Exception as e:
            logger.error(f"❌ 處理接收訊息時發生錯誤: {e}")


class OrderConsumer(BaseOrderConsumer):
    """訂單專屬 WebSocket Consumer - 用於單個訂單的即時更新"""
    
    async def connect(self):
        """處理 WebSocket 連線"""
        # 從 URL 獲取訂單 ID
        self.order_id = self.scope['url_route']['kwargs']['order_id']
        self.room_group_name = f'order_{self.order_id}'
        
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
            user_info=user_info
        )
        
        # 加入訂單群組
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        # 啟動心跳監控任務
        self.heartbeat_task = asyncio.create_task(self._heartbeat_checker())
        
        # ✅ 連線成功後，立即發送當前訂單狀態
        await self.send_current_status()
        
        logger.info(f"✅ 訂單 Consumer 連線成功: {self.connection_id}, 用戶: {user_info['username']}")
    
    async def disconnect(self, close_code):
        """處理 WebSocket 斷線"""
        # 取消心跳任務
        if hasattr(self, 'heartbeat_task'):
            self.heartbeat_task.cancel()
        
        # ✅ 從 WebSocketManager 斷開
        if hasattr(self, 'connection_id'):
            websocket_manager.disconnect(self.connection_id, f"close_code: {close_code}")
        
        # 離開訂單群組
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
        
        logger.info(f"🔌 訂單 Consumer 斷線: 訂單 {getattr(self, 'order_id', 'unknown')}, code: {close_code}")
    
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
        from .models import OrderModel, CoffeeQueue
        from .order_status_manager import OrderStatusManager
        
        try:
            order = OrderModel.objects.get(id=self.order_id)
            status_manager = OrderStatusManager(order)
            status_info = status_manager.get_display_status()
            
            # 獲取隊列資訊（如果存在）
            queue_info = None
            try:
                queue = CoffeeQueue.objects.get(order=order)
                queue_info = {
                    'position': queue.position,
                    'estimated_time': queue.estimated_completion_time.isoformat() if queue.estimated_completion_time else None,
                    'remaining_seconds': queue.remaining_seconds,
                }
            except CoffeeQueue.DoesNotExist:
                pass
            
            return {
                'order_id': order.id,
                'status': order.status,
                'status_display': order.get_status_display(),
                'payment_status': order.payment_status,
                'payment_method': order.payment_method,
                'pickup_code': order.pickup_code,
                'estimated_completion_time': status_info.get('estimated_time'),
                'queue_position': queue_info['position'] if queue_info else None,
                'remaining_seconds': queue_info['remaining_seconds'] if queue_info else None,
                'progress_percentage': status_info.get('progress_percentage', 0),
                'progress_display': status_info.get('progress_display', ''),
            }
        except OrderModel.DoesNotExist:
            return None
    
    async def send_current_status(self):
        """主動發送當前訂單狀態給前端"""
        status_data = await self._get_order_status_data()
        if status_data:
            await self._send_json({
                'type': 'order_status',
                'data': status_data,
                'timestamp': timezone.now().isoformat()
            })
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
    
    async def order_status_update(self, event):
        """
        訂單狀態更新（來自 send_order_update）
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
        if 'status_display' not in event or 'estimated_time' not in event or 'queue_position' not in event:
            status_data = await self._get_order_status_data()
            if status_data:
                event['status_display'] = status_data['status_display']
                event['estimated_time'] = status_data['estimated_completion_time']
                event['queue_position'] = status_data['queue_position']
                event['remaining_seconds'] = status_data['remaining_seconds']
                event['progress_percentage'] = status_data['progress_percentage']
        
        await self._send_json({
            'type': 'order_status',
            'data': {
                'order_id': event.get('order_id', self.order_id),
                'status': event.get('status'),
                'status_display': event.get('status_display'),
                'estimated_time': event.get('estimated_time'),
                'queue_position': event.get('queue_position'),
                'remaining_seconds': event.get('remaining_seconds'),
                'progress_percentage': event.get('progress_percentage'),
                'message': event.get('message', ''),
            },
            'timestamp': timezone.now().isoformat()
        })
    
    async def queue_position_update(self, event):
        """隊列位置更新（專門針對排隊位置變化）"""
        await self._send_json({
            'type': 'queue_position',
            'order_id': event.get('order_id', self.order_id),
            'position': event.get('position'),
            'estimated_time': event.get('estimated_time'),
            'remaining_seconds': event.get('remaining_seconds'),
            'timestamp': timezone.now().isoformat()
        })
    
    async def estimated_time_update(self, event):
        """預計完成時間更新（專門針對時間變化）"""
        await self._send_json({
            'type': 'estimated_time',
            'order_id': event.get('order_id', self.order_id),
            'estimated_time': event.get('estimated_time'),
            'remaining_seconds': event.get('remaining_seconds'),
            'timestamp': timezone.now().isoformat()
        })
    
    async def payment_status_update(self, event):
        """支付狀態更新"""
        await self._send_json({
            'type': 'payment_status',
            'order_id': event.get('order_id', self.order_id),
            'payment_status': event.get('payment_status'),
            'payment_method': event.get('payment_method', ''),
            'message': event.get('message', ''),
            'timestamp': timezone.now().isoformat()
        })
    
    async def order_ready_notification(self, event):
        """訂單就緒通知"""
        await self._send_json({
            'type': 'order_ready',
            'order_id': event.get('order_id', self.order_id),
            'pickup_code': event.get('pickup_code'),
            'customer_name': event.get('customer_name'),
            'timestamp': timezone.now().isoformat()
        })


class QueueConsumer(BaseOrderConsumer):
    """隊列 WebSocket Consumer - 用於隊列頁面的即時廣播"""
    
    async def connect(self):
        """處理 WebSocket 連線"""
        self.room_group_name = 'queue_updates'
        
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
            user_info=user_info
        )
        
        # 加入隊列群組
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        # 啟動心跳監控任務
        self.heartbeat_task = asyncio.create_task(self._heartbeat_checker())
        
        logger.info(f"✅ 隊列 Consumer 連線成功: {self.connection_id}, 用戶: {user_info['username']}")
    
    async def disconnect(self, close_code):
        """處理 WebSocket 斷線"""
        # 取消心跳任務
        if hasattr(self, 'heartbeat_task'):
            self.heartbeat_task.cancel()
        
        # ✅ 從 WebSocketManager 斷開
        if hasattr(self, 'connection_id'):
            websocket_manager.disconnect(self.connection_id, f"close_code: {close_code}")
        
        # 離開隊列群組
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
        
        logger.info(f"🔌 隊列 Consumer 斷線: {getattr(self, 'connection_id', 'unknown')}, code: {close_code}")
    
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
        await self._send_json({
            'type': 'queue_update',
            'action': event.get('action', 'update'),
            'order_id': event.get('order_id'),
            'position': event.get('position'),
            'queue_type': event.get('queue_type', 'waiting'),
            'data': event.get('data', {}),
            'timestamp': timezone.now().isoformat()
        })
    
    async def new_order_notification(self, event):
        """新訂單通知"""
        await self._send_json({
            'type': 'new_order',
            'order_id': event.get('order_id'),
            'customer_name': event.get('customer_name'),
            'total_price': event.get('total_price'),
            'items_count': event.get('items_count'),
            'timestamp': timezone.now().isoformat()
        })
    
    async def order_ready(self, event):
        """訂單就緒通知"""
        await self._send_json({
            'type': 'order_ready',
            'order_id': event.get('order_id'),
            'pickup_code': event.get('pickup_code'),
            'customer_name': event.get('customer_name'),
            'timestamp': timezone.now().isoformat()
        })
    
    async def payment_update(self, event):
        """支付更新通知"""
        await self._send_json({
            'type': 'payment_update',
            'order_id': event.get('order_id'),
            'payment_status': event.get('payment_status'),
            'payment_method': event.get('payment_method', ''),
            'message': event.get('message', ''),
            'timestamp': timezone.now().isoformat()
        })
    
    async def system_message(self, event):
        """系統訊息廣播"""
        await self._send_json({
            'type': 'system',
            'message': event.get('message'),
            'message_type': event.get('message_type', 'info'),
            'timestamp': timezone.now().isoformat()
        })