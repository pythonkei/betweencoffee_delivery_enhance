# eshop/notifications.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.cache import cache
from .models import OrderModel
import json
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=OrderModel)
def order_status_changed(sender, instance, **kwargs):
    """订单状态变化时发送推送通知"""
    if kwargs.get('created', False):
        return  # 新创建订单不发送通知
    
    # 检查状态是否变化
    if instance.tracker.has_changed('status'):
        send_order_notification(instance)

def send_order_notification(order):
    """发送订单通知到所有连接的客户端"""
    from channels.layers import get_channel_layer
    from asgiref.sync import async_to_sync
    
    try:
        channel_layer = get_channel_layer()
        
        notification_data = {
            'type': 'order_notification',
            'order_id': order.id,
            'status': order.status,
            'status_display': order.get_status_display(),
            'message': get_status_message(order.status),
            'timestamp': order.updated_at.isoformat()
        }
        
        # 发送到订单特定的频道组
        async_to_sync(channel_layer.group_send)(
            f'order_{order.id}',
            {
                'type': 'send_notification',
                'data': notification_data
            }
        )
        
        logger.info(f"推送通知已发送: 订单 {order.id} 状态变为 {order.status}")
        
    except Exception as e:
        logger.error(f"发送推送通知失败: {str(e)}")

def get_status_message(status):
    """根据状态获取消息内容"""
    messages = {
        'pending': '您的订单已提交，等待支付',
        'preparing': '您的订单已开始制作',
        'ready': '您的订单已就绪，请前来取餐',
        'completed': '您的订单已完成'
    }
    return messages.get(status, '订单状态已更新')