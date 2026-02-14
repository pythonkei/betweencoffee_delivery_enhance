# eshop/management/commands/check_payment_timeout.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from eshop.models import OrderModel
from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = '检查支付超时的订单并自动取消，发送支付提醒'

    def handle(self, *args, **options):
        self.check_expired_orders()
        self.send_payment_reminders()

    def check_expired_orders(self):
        """检查并取消超时订单"""
        now = timezone.now()
        expired_orders = OrderModel.objects.filter(
            payment_status='pending',
            payment_timeout__lt=now
        )
        
        count = expired_orders.count()
        for order in expired_orders:
            order.mark_as_cancelled()
            logger.info(f"订单 #{order.id} 因支付超时已自动取消")
            
            # 发送取消通知（可选）
            self.send_cancellation_notification(order)
        
        if count > 0:
            self.stdout.write(
                self.style.SUCCESS(f'成功取消 {count} 个超时订单')
            )
        else:
            self.stdout.write('没有找到超时订单')

    def send_payment_reminders(self):
        """发送支付提醒"""
        orders_needing_reminder = OrderModel.objects.filter(
            payment_status='pending'
        )
        
        reminder_count = 0
        for order in orders_needing_reminder:
            if order.should_send_payment_reminder():
                self.send_reminder_notification(order)
                order.mark_reminder_sent()
                reminder_count += 1
                logger.info(f"已发送支付提醒给订单 #{order.id}")
        
        if reminder_count > 0:
            self.stdout.write(
                self.style.SUCCESS(f'成功发送 {reminder_count} 个支付提醒')
            )

    def send_reminder_notification(self, order):
        """发送支付提醒通知"""
        try:
            subject = "【Between Coffee】您的订单即将超时，请及时支付"
            message = f"""
尊敬的{order.name}：

您的咖啡订单 (#{order.id}) 即将在5分钟后自动取消，请及时完成支付。

订单总金额：HK${order.total_price}
支付超时时间：{order.payment_timeout.strftime('%Y-%m-%d %H:%M')}

请尽快完成支付以避免订单被自动取消。

感谢您选择Between Coffee！
            """
            
            if order.email:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [order.email],
                    fail_silently=True,
                )
            
            # 这里可以添加短信通知（如果配置了短信服务）
            # if order.phone:
            #     self.send_sms_reminder(order)
                
        except Exception as e:
            logger.error(f"发送支付提醒失败: {str(e)}")



    def send_cancellation_notification(self, order):
        """发送订单取消通知"""
        try:
            subject = "【Between Coffee】您的订单已因超时取消"
            message = f"""
尊敬的{order.name}：

很抱歉，您的订单 (#{order.id}) 因支付超时已被自动取消。

如果您仍需要购买，请重新下单。

感谢您对Between Coffee的关注！
            """
            
            if order.email:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [order.email],
                    fail_silently=True,
                )
                
        except Exception as e:
            logger.error(f"发送取消通知失败: {str(e)}")