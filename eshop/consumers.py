# eshop/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import OrderModel

class OrderConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.order_id = self.scope['url_route']['kwargs']['order_id']
        self.room_group_name = f'order_{self.order_id}'

        # 加入订单组
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # 离开订单组
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # 接收来自群组的消息
    async def order_notification(self, event):
        message = event['message']
        status = event['status']

        # 发送消息到WebSocket
        await self.send(text_data=json.dumps({
            'type': 'order_notification',
            'message': message,
            'status': status
        }))