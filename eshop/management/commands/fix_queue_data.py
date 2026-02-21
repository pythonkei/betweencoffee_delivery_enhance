# 在 eshop/management/commands/fix_queue_data.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from eshop.models import OrderModel, CoffeeQueue
from eshop.queue_manager_refactored import CoffeeQueueManager
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = '修复队列数据，确保所有等待订单正确显示'
    
    def handle(self, *args, **options):
        logger.info("=== 开始修复队列数据 ===")
        
        # 1. 同步状态
        queue_manager = CoffeeQueueManager()
        queue_manager.sync_order_queue_status()
        
        # 2. 修复队列位置
        queue_manager.fix_queue_positions()
        
        # 3. 更新预计时间
        queue_manager.update_estimated_times()
        
        # 4. 显示当前队列状态
        waiting_count = CoffeeQueue.objects.filter(status='waiting').count()
        preparing_count = CoffeeQueue.objects.filter(status='preparing').count()
        ready_orders = OrderModel.objects.filter(status='ready', payment_status="paid").count()
        
        self.stdout.write(f"修复完成:")
        self.stdout.write(f"  等待队列: {waiting_count} 个")
        self.stdout.write(f"  制作中队列: {preparing_count} 个")
        self.stdout.write(f"  已就绪订单: {ready_orders} 个")
        
        logger.info("=== 队列数据修复完成 ===")