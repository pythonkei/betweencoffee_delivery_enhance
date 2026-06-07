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
            created_str = order.created_at.strftime('%Y-%m-%d %H:%M:%S')
            username = order.user.username if order.user else '訪客'
            self.stdout.write(
                f'{order.id:>6} | {username:<15} | '
                f'${order.total_price:>6.2f} | {created_str:<25}'
            )

        self.stdout.write('-' * 90)
        self.stdout.write(f'總計: {total_count} 筆訂單\n')

        # 預覽模式
        if dry_run:
            self.stdout.write(
                self.style.WARNING('⚠️ 預覽模式 -- 未執行任何操作')
            )
            return

        # 實際執行取消
        self.stdout.write('🔄 開始自動取消過期訂單...')

        success_count = 0
        fail_count = 0
        failed_ids = []

        for order in expired_orders:
            try:
                with transaction.atomic():
                    result = OrderStatusManager.mark_as_cancelled_manually(
                        order_id=order.id,
