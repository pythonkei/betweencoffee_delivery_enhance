# eshop/notifications.py
import logging

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import OrderModel

logger = logging.getLogger(__name__)


@receiver(post_save, sender=OrderModel)
def order_status_changed(sender, instance, **kwargs):
    """訂單狀態變化時發送推送通知 + WhatsApp 通知"""
    if kwargs.get("created", False):
        return  # 新創建訂單不發送通知

    # 檢查狀態是否變化
    if hasattr(instance, "tracker") and instance.tracker.has_changed("status"):
        send_order_notification(instance)

        # 當訂單變為 ready（已就緒）時，一併發送 WhatsApp 通知
        if instance.status == "ready":
            send_whatsapp_ready_notification(instance)


def send_whatsapp_ready_notification(order):
    """訂單就緒時發送 WhatsApp 通知"""
    try:
        from .whatsapp_notifier import send_order_ready_notification

        success = send_order_ready_notification(order)
        if success:
            logger.info(f"✅ WhatsApp 就緒通知已發送: 訂單 #{order.id}")
        else:
            logger.info(f"⚠️ WhatsApp 就緒通知跳過: 訂單 #{order.id}（無電話號碼或未配置）")
    except ImportError:
        logger.warning("WhatsApp 通知模組未安裝，跳過")
    except Exception as e:
        logger.error(f"發送 WhatsApp 通知失敗: {e}")


def send_order_notification(order):
    """發送訂單通知到所有連接的客戶端"""
    from asgiref.sync import async_to_sync
    from channels.layers import get_channel_layer

    try:
        channel_layer = get_channel_layer()

        notification_data = {
            "type": "order_notification",
            "order_id": order.id,
            "status": order.status,
            "status_display": order.get_status_display(),
            "message": get_status_message(order.status),
            "timestamp": order.updated_at.isoformat(),
        }

        # 发送到订单特定的频道组
        async_to_sync(channel_layer.group_send)(
            f"order_{order.id}",
            {"type": "send_notification", "data": notification_data},
        )

        logger.info(f"推送通知已发送: 订单 {order.id} 状态变为 {order.status}")

    except Exception as e:
        logger.error(f"发送推送通知失败: {str(e)}")


def get_status_message(status):
    """根据状态获取消息内容"""
    messages = {
        "pending": "您的订单已提交，等待支付",
        "preparing": "您的订单已开始制作",
        "ready": "您的订单已就绪，请前来取餐",
        "completed": "您的订单已完成",
    }
    return messages.get(status, "订单状态已更新")
