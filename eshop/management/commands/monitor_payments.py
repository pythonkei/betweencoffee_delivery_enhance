# eshop/management/commands/monitor_payments.py
# 手動監控 支付監控管理命令
from django.core.management.base import BaseCommand
from django.utils import timezone
import logging
from eshop.models import OrderModel
from eshop.order_status_manager import OrderStatusManager

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = '監控並清理超時支付訂單'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='模擬運行，不實際修改數據',
        )
        parser.add_argument(
            '--grace-minutes',
            type=int,
            default=15,
            help='支付寬限期（分鐘），默認15分鐘'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        grace_minutes = options['grace_minutes']
        
        # 計算超時時間點（當前時間 - 寬限期）
        timeout_threshold = timezone.now() - timedelta(minutes=grace_minutes)
        
        # 查找超時訂單
        # 注意：這裡假設訂單創建時間超過grace_minutes且仍未支付就是超時
        timeout_orders = OrderModel.objects.filter(
            payment_status="pending",
            status='pending',
            created_at__lt=timeout_threshold
        ).order_by('created_at')
        
        self.stdout.write(f"找到 {timeout_orders.count()} 個超時訂單（寬限期: {grace_minutes}分鐘）")
        
        if dry_run:
            self.stdout.write(self.style.WARNING('這是模擬運行，未實際修改數據'))
            for order in timeout_orders:
                self.stdout.write(
                    f"訂單 #{order.id} - "
                    f"創建於 {order.created_at.strftime('%Y-%m-%d %H:%M:%S')} - "
                    f"超時時間: {timeout_threshold.strftime('%H:%M:%S')}"
                )
            return
        
        cancelled = 0
        failed = 0
        
        for order in timeout_orders:
            self.stdout.write(
                f"處理訂單 #{order.id} - "
                f"創建於 {order.created_at.strftime('%Y-%m-%d %H:%M:%S')}"
            )
            
            try:
                # ✅ 修復：使用 OrderStatusManager 取消訂單
                result = OrderStatusManager.mark_as_cancelled_manually(
                    order_id=order.id,
                    staff_name="monitor_payments_command",
                    reason=f"支付超時自動取消（寬限期{grace_minutes}分鐘）"
                )
                
                if result.get('success'):
                    cancelled += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'  已取消超時訂單: #{order.id}')
                    )
                    
                    # 記錄詳細日誌
                    logger.info(
                        f"監控支付系統取消超時訂單 #{order.id}，"
                        f"創建時間: {order.created_at}，"
                        f"寬限期: {grace_minutes}分鐘"
                    )
                else:
                    failed += 1
                    self.stdout.write(
                        self.style.ERROR(f'  取消失敗: {result.get("message", "未知錯誤")}')
                    )
                    
            except Exception as e:
                failed += 1
                logger.error(f"取消訂單 #{order.id} 失敗: {str(e)}")
                self.stdout.write(
                    self.style.ERROR(f'  處理異常: {str(e)}')
                )
        
        if cancelled > 0:
            self.stdout.write(
                self.style.SUCCESS(f'成功取消 {cancelled} 個超時訂單')
            )
        if failed > 0:
            self.stdout.write(
                self.style.WARNING(f'有 {failed} 個訂單處理失敗')
            )
            
        # 清理相關的隊列項目（如果有的話）
        try:
            from eshop.models import CoffeeQueue
            cancelled_queue_items = CoffeeQueue.objects.filter(
                order__in=[o.id for o in timeout_orders]
            ).update(status='cancelled')
            
            if cancelled_queue_items > 0:
                self.stdout.write(
                    self.style.SUCCESS(f'已清理 {cancelled_queue_items} 個相關隊列項目')
                )
        except Exception as e:
            logger.error(f"清理隊列項目失敗: {str(e)}")
            self.stdout.write(
                self.style.WARNING(f'清理隊列項目時出現錯誤: {str(e)}')
            )