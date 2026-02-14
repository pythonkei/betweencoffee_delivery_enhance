# eshop/management/commands/reset_payment_attempts.py
from django.core.management.base import BaseCommand
from eshop.models import OrderModel

class Command(BaseCommand):
    help = '重置订单支付尝试次数'

    def add_arguments(self, parser):
        parser.add_argument('order_ids', nargs='+', type=int, help='订单ID列表')

    def handle(self, *args, **options):
        order_ids = options['order_ids']
        
        for order_id in order_ids:
            try:
                order = OrderModel.objects.get(id=order_id)
                old_attempts = order.payment_attempts
                order.payment_attempts = 0
                order.save()
                self.stdout.write(
                    self.style.SUCCESS(f'订单 {order_id} 支付尝试次数从 {old_attempts} 重置为 0')
                )
            except OrderModel.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'订单 {order_id} 不存在')
                )