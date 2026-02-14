# eshop/management/commands/cleanup_queue.py
import os
import django
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
import logging
from eshop.models import CoffeeQueue, OrderModel
from eshop.order_status_manager import OrderStatusManager

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = '清理隊列，處理舊訂單'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--hours',
            type=int,
            default=1,
            help='處理多少小時前的訂單（默認1小時）'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='模擬運行，不實際修改數據'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='強制清理，即使訂單狀態不允許'
        )
    
    def handle(self, *args, **options):
        hours = options['hours']
        dry_run = options['dry_run']
        force = options.get('force', False)
        
        cutoff_time = timezone.now() - timedelta(hours=hours)
        
        # 找到超過指定時間的等待訂單
        old_queues = CoffeeQueue.objects.filter(
            status='waiting',
            created_at__lt=cutoff_time
        ).select_related('order')
        
        self.stdout.write(f"找到 {old_queues.count()} 個超過{hours}小時的等待訂單")
        
        if dry_run:
            self.stdout.write("模擬運行，不會修改數據")
            for queue in old_queues:
                self.stdout.write(f"訂單 #{queue.order.id} - {queue.order.name} - 創建於 {queue.created_at}")
            return
        
        processed = 0
        failed = 0
        
        for queue in old_queues:
            self.stdout.write(f"處理訂單 #{queue.order.id} - {queue.order.name} - 創建於 {queue.created_at}")
            
            try:
                order = queue.order
                
                # ✅ 修復：使用 OrderStatusManager 來更新狀態
                # 先檢查訂單是否允許標記為就緒
                if order.status not in ['pending', 'waiting', 'preparing'] and not force:
                    self.stdout.write(
                        self.style.WARNING(f"  跳過：訂單狀態為 {order.status}，不允許標記為就緒")
                    )
                    continue
                
                # 先更新隊列項
                queue.status = 'ready'
                queue.actual_completion_time = timezone.now()
                queue.position = 0
                
                # 如果沒有實際開始時間，設置一個
                if not queue.actual_start_time:
                    queue.actual_start_time = timezone.now() - timedelta(minutes=queue.preparation_time_minutes or 5)
                
                queue.save()
                
                # ✅ 使用 OrderStatusManager 標記訂單為就緒
                result = OrderStatusManager.mark_as_ready_manually(
                    order_id=order.id,
                    staff_name="cleanup_queue_command"
                )
                
                if result.get('success'):
                    processed += 1
                    self.stdout.write(
                        self.style.SUCCESS(f"  已標記為就緒")
                    )
                else:
                    failed += 1
                    self.stdout.write(
                        self.style.ERROR(f"  失敗：{result.get('message', '未知錯誤')}")
                    )
                    
            except Exception as e:
                failed += 1
                logger.error(f"處理訂單 #{queue.order.id} 失敗: {str(e)}")
                self.stdout.write(
                    self.style.ERROR(f"  處理失敗：{str(e)}")
                )
        
        if processed > 0:
            self.stdout.write(
                self.style.SUCCESS(f"處理完成！成功處理 {processed} 個訂單")
            )
        if failed > 0:
            self.stdout.write(
                self.style.WARNING(f"有 {failed} 個訂單處理失敗")
            )
        
        # 執行統一的隊列時間重新計算
        try:
            from eshop.queue_manager import CoffeeQueueManager
            queue_manager = CoffeeQueueManager()
            time_result = queue_manager.recalculate_all_order_times()
            
            if time_result.get('success'):
                self.stdout.write(
                    self.style.SUCCESS("✅ 隊列時間已重新計算")
                )
            else:
                self.stdout.write(
                    self.style.WARNING("⚠️ 隊列時間重新計算可能不完整")
                )
        except Exception as e:
            logger.error(f"重新計算隊列時間失敗: {str(e)}")