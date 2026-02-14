# eshop/management/commands/check_queue_priority.py
from django.core.management.base import BaseCommand
from eshop.models import OrderModel, CoffeeQueue
from eshop.queue_manager import CoffeeQueueManager
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = '檢查隊列優先級排序狀態'
    
    def handle(self, *args, **options):
        queue_manager = CoffeeQueueManager()
        
        # 檢查等待隊列
        waiting_queues = CoffeeQueue.objects.filter(status='waiting').order_by('position')
        
        self.stdout.write("=== 隊列優先級狀態檢查 ===")
        self.stdout.write(f"等待訂單數量: {waiting_queues.count()}")
        
        for queue in waiting_queues:
            order = queue.order
            pickup_display = "無"
            
            if order.order_type == 'quick' and hasattr(order, 'pickup_time_choice'):
                pickup_display = f"{order.pickup_time_choice}分鐘後"
            
            self.stdout.write(
                f"位置 {queue.position:2d} | "
                f"訂單 #{order.id:4d} | "
                f"類型: {order.order_type:6s} | "
                f"取貨: {pickup_display:8s} | "
                f"創建: {order.created_at.strftime('%H:%M')}"
            )
        
        # 重新排序隊列
        self.stdout.write("\n=== 重新排序隊列 ===")
        needs_reorder = queue_manager.reorder_queue_by_priority()
        
        if needs_reorder:
            self.stdout.write(self.style.SUCCESS("隊列已重新排序"))
        else:
            self.stdout.write("隊列順序正常，無需重新排序")
        
        # 更新預計時間
        self.stdout.write("\n=== 更新預計時間 ===")
        queue_manager.update_estimated_times()
        self.stdout.write(self.style.SUCCESS("隊列預計時間已更新"))