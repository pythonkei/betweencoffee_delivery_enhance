# eshop/management/commands/debug_queue.py
from django.core.management.base import BaseCommand
from eshop.models import OrderModel, CoffeeQueue
from eshop.queue_manager import CoffeeQueueManager

class Command(BaseCommand):
    help = '调试队列系统'
    
    def add_arguments(self, parser):
        parser.add_argument('--order-id', type=int, help='订单ID')
        parser.add_argument('--list', action='store_true', help='列出所有队列项')
        parser.add_argument('--force-add', action='store_true', help='强制将订单加入队列')
    
    def handle(self, *args, **options):
        if options['list']:
            self.list_queue_items()
        elif options['order_id']:
            if options['force_add']:
                self.force_add_to_queue(options['order_id'])
            else:
                self.debug_order(options['order_id'])
        else:
            self.stdout.write(self.style.WARNING('请提供参数'))
    
    def list_queue_items(self):
        """列出所有队列项"""
        queue_items = CoffeeQueue.objects.all().order_by('status', 'position')
        self.stdout.write(f"队列项总数: {queue_items.count()}")
        
        for item in queue_items:
            self.stdout.write(
                f"ID: {item.id}, "
                f"订单: {item.order.id}, "
                f"状态: {item.get_status_display()}, "
                f"位置: {item.position}, "
                f"咖啡杯数: {item.coffee_count}"
            )
    
    def debug_order(self, order_id):
        """调试订单"""
        try:
            order = OrderModel.objects.get(id=order_id)
            self.stdout.write(f"订单信息:")
            self.stdout.write(f"  ID: {order.id}")
            self.stdout.write(f"  状态: {order.status}")
            self.stdout.write(f"  是否支付: {order.is_paid}")
            self.stdout.write(f"  预计时间: {order.estimated_ready_time}")
            
            items = order.get_items()
            has_coffee = any(item.get('type') == 'coffee' for item in items)
            self.stdout.write(f"  包含咖啡: {has_coffee}")
            
            coffee_count = 0
            for item in items:
                if item.get('type') == 'coffee':
                    coffee_count += item.get('quantity', 1)
            self.stdout.write(f"  咖啡杯数: {coffee_count}")
            
            # 检查是否在队列中
            try:
                queue_item = CoffeeQueue.objects.get(order=order)
                self.stdout.write(f"  在队列中: 是")
                self.stdout.write(f"    队列状态: {queue_item.status}")
                self.stdout.write(f"    队列位置: {queue_item.position}")
            except CoffeeQueue.DoesNotExist:
                self.stdout.write(f"  在队列中: 否")
            
        except OrderModel.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"订单 {order_id} 不存在"))
    
    def force_add_to_queue(self, order_id):
        """强制将订单加入队列"""
        try:
            order = OrderModel.objects.get(id=order_id)
            
            # 检查是否已经在队列中
            if CoffeeQueue.objects.filter(order=order).exists():
                self.stdout.write(self.style.WARNING(f"订单 {order_id} 已在队列中"))
                return
            
            # 检查订单是否包含咖啡
            items = order.get_items()
            has_coffee = any(item.get('type') == 'coffee' for item in items)
            
            if not has_coffee:
                self.stdout.write(self.style.WARNING(f"订单 {order_id} 不包含咖啡"))
                return
            
            # 加入队列
            queue_manager = CoffeeQueueManager()
            queue_item = queue_manager.add_order_to_queue(order)
            
            if queue_item:
                self.stdout.write(self.style.SUCCESS(f"订单 {order_id} 已加入队列，位置: {queue_item.position}"))
            else:
                self.stdout.write(self.style.ERROR(f"订单 {order_id} 加入队列失败"))
            
        except OrderModel.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"订单 {order_id} 不存在"))