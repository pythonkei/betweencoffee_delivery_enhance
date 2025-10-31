# eshop/sms_utils.py
import logging
import requests
from django.conf import settings
from twilio.base.exceptions import TwilioRestException

logger = logging.getLogger(__name__)

# TWILIO
def send_sms_notification(order):
    """
    发送短信通知给香港客户
    """
    try:
        # 检查是否配置了短信服务
        if not all([hasattr(settings, 'TWILIO_ACCOUNT_SID'), 
                   hasattr(settings, 'TWILIO_AUTH_TOKEN'), 
                   hasattr(settings, 'TWILIO_PHONE_NUMBER')]):
            logger.warning("短信服务未配置完整，跳过发送")
            return False
        
        # 打印配置信息用于调试
        logger.info(f"Twilio配置 - SID: {settings.TWILIO_ACCOUNT_SID[:10]}...")
        logger.info(f"Twilio号码: {settings.TWILIO_PHONE_NUMBER}")
        
        # 确保电话号码是香港号码
        if not order.phone.startswith('+852'):
            logger.warning(f"非香港电话号码 {order.phone}，跳过发送")
            return False
        
        # 构建短信内容
        message_body = f"""
        感謝您在Between Coffee下單！
        訂單號: #{order.id}
        取餐碼: {order.pickup_code}
        總金額: HK${order.total_price}
        """
        
        if order.estimated_ready_time:
            from django.utils import timezone
            from django.utils.formats import date_format
            local_time = timezone.localtime(order.estimated_ready_time)
            ready_time = date_format(local_time, "H:i")
            message_body += f"預計提取時間: {ready_time}"
        
        message_body += "\n請憑取餐碼到店取餐，謝謝！"
        
        # 使用Twilio发送短信
        from twilio.rest import Client
        
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        
        message = client.messages.create(
            body=message_body,
            from_=settings.TWILIO_PHONE_NUMBER,
            to=order.phone
        )
        
        logger.info(f"短信已发送到 {order.phone}, 消息ID: {message.sid}")
        return True
        
    except TwilioRestException as e:
        logger.error(f"Twilio API错误: {e.code} - {e.msg}")
        if e.code == 21603:
            logger.error("错误21603: 'From'电话号码无效。请检查:")
            logger.error("1. 电话号码是否存在于你的Twilio账户中")
            logger.error("2. 电话号码是否已启用短信功能")
            logger.error("3. 电话号码格式是否正确 (E.164格式)")
        return False
    except Exception as e:
        logger.error(f"发送短信失败: {str(e)}")
        return False