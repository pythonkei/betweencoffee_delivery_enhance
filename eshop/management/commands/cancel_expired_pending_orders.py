"""
自動取消過期未支付訂單的管理命令。

用於 Render Cron Job 替代 Celery Beat 定時任務。
每 5 分鐘執行一次，取消超過 30 分鐘未支付的訂單。

用法:
    # 直接執行
    python manage.py cancel_expired_pending_orders

    # 指定過期時間（分鐘）
    python manage.py cancel_expired_pending_orders --expire-minutes=60

    # 預覽模式
    python manage.py cancel_expired_pending_orders --dry-run
"""

import logging
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction

from eshop.models import OrderModel, CoffeeQueue
from eshop.order_status_manager import OrderStatusManager

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = '自動取消超過指定時間未支付的訂單'

    def add_arguments(self, parser):
        parser.add_argument(
            '--expire-minutes',
            type=int,
            default=30,
            help='訂單超過多少分鐘未支付視為過期（預設: 30）'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='預覽模式：只顯示將被取消的訂單，不實際執行'
        )

    def handle(self, *args, **options):
        expire_minutes = options['expire_minutes']
        dry_run = options['dry_run']

        # 計算過期時間點
        cutoff_time = timezone.now() - timedelta(minutes=expire_minutes)

        self.stdout.write(f'🔍 檢查超過 {expire_minutes} 分鐘未支付的訂單...')
        self.stdout.write(f'⏰ 截止時間: {cutoff_time.strftime("%Y-%m-%d %H:%M:%S")}')

        # 查找過期未支付訂單
        expired_orders = OrderModel.objects.filter(
            payment_status='pending',
            status__in=['pending', 'waiting'],
            created_at__lt=cutoff_time
        ).order_by('created_at')

        total_count = expired_orders.count()
        self.stdout.write(f'📊 找到 {total_count} 筆過期未支付訂單')

        if total_count == 0:
            self.stdout.write(self.style.SUCCESS('✅ 沒有需要處理的過期訂單'))
            return

        # 顯示訂單列表
        self.stdout.write('\n📋 過期訂單列表:')
        self.stdout.write('-' * 90)
        self.stdout.write(f'{"ID":>6} | {"用戶":<15} | {"金額":>8} | {"建立時間":<25}')
        self.stdout.write('-' * 90)

        for order in expired_orders:
            self.stdout.write(f'{order.id:>6} | {str(order.user or "訪客"):<15} | ${order.total_price:>7.2f} | {order.created_at.strftime("%Y-%m-%d %H:%M"):<25}')

        self.stdout.write('-' * 90)

        if dry_run:
            self.stdout.write(self.style.WARNING(f'\n🔍 預覽模式：將取消 {total_count} 筆訂單（未實際執行）'))
            return

        # 實際執行取消
        self.stdout.write(f'\n🔄 開始取消 {total_count} 筆過期訂單...')
        cancelled_count = 0
        failed_count = 0

        for order in expired_orders:
            try:
                with transaction.atomic():
                    status_manager = OrderStatusManager()
                    status_manager.cancel_order(order)
                    cancelled_count += 1
                    self.stdout.write(f'  ✅ 訂單 #{order.id} 已取消')
            except Exception as e:
                failed_count += 1
                self.stdout.write(self.style.ERROR(f'  ❌ 訂單 #{order.id} 取消失敗: {e}'))
                logger.error(f'取消訂單 #{order.id} 失敗: {e}')

        # 最終報告
        self.stdout.write('\n' + '=' * 50)
        self.stdout.write(self.style.SUCCESS(f'✅ 完成！成功取消 {cancelled_count} 筆訂單'))
        if failed_count > 0:
            self.stdout.write(self.style.ERROR(f'❌ 失敗 {failed_count} 筆訂單'))
        self.stdout.write('=' * 50)

