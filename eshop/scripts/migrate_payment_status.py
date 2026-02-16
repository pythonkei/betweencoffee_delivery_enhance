#!/usr/bin/env python
"""
支付狀態遷移腳本：從 is_paid 到 payment_status

遷移邏輯：
1. 將 is_paid=True 的訂單設置為 payment_status='paid'
2. 將 is_paid=False 的訂單設置為 payment_status='pending'
3. 清理對 is_paid 字段的引用

使用方式：
python manage.py migrate_payment_status [--dry-run] [--batch-size=100]
"""

import logging
from django.core.management.base import BaseCommand
from django.utils import timezone
from eshop.models import OrderModel

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = '遷移支付狀態：從 is_paid 到 payment_status'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='模擬運行，不實際修改數據'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='每批處理的訂單數量'
        )
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        batch_size = options['batch_size']
        
        self.stdout.write(f"開始支付狀態遷移 (dry-run: {dry_run})")
        
        # 1. 統計需要遷移的訂單
        total_orders = OrderModel.objects.count()
        orders_with_is_paid = OrderModel.objects.filter(is_paid__isnull=False).count()
        
        self.stdout.write(f"總訂單數: {total_orders}")
        self.stdout.write(f"需要遷移的訂單數: {orders_with_is_paid}")
        
        # 2. 分批處理
        migrated_count = 0
        errors = []
        
        for i in range(0, orders_with_is_paid, batch_size):
            batch = OrderModel.objects.filter(is_paid__isnull=False)[i:i+batch_size]
            
            for order in batch:
                try:
                    old_is_paid = order.is_paid
                    old_payment_status = order.payment_status
                    
                    # 遷移邏輯
                    if old_is_paid and order.payment_status != 'paid':
                        if not dry_run:
                            order.payment_status = 'paid'
                            order.save(update_fields=['payment_status'])
                        
                        migrated_count += 1
                        
                        self.stdout.write(
                            f"訂單 #{order.id}: "
                            f"is_paid={old_is_paid} -> payment_status='paid' "
                            f"(原狀態: {old_payment_status})"
                        )
                    
                    elif not old_is_paid and order.payment_status == 'paid':
                        if not dry_run:
                            order.payment_status = 'pending'
                            order.save(update_fields=['payment_status'])
                        
                        migrated_count += 1
                        
                        self.stdout.write(
                            f"訂單 #{order.id}: "
                            f"is_paid={old_is_paid} -> payment_status='pending' "
                            f"(原狀態: {old_payment_status})"
                        )
                        
                except Exception as e:
                    errors.append(f"訂單 #{order.id}: {str(e)}")
                    logger.error(f"遷移訂單 {order.id} 失敗: {str(e)}")
            
            self.stdout.write(f"已處理: {min(i+batch_size, orders_with_is_paid)}/{orders_with_is_paid}")
        
        # 3. 輸出結果
        self.stdout.write(f"\n遷移完成!")
        self.stdout.write(f"成功遷移: {migrated_count} 個訂單")
        
        if errors:
            self.stdout.write(f"錯誤數量: {len(errors)}")
            for error in errors[:10]:  # 只顯示前10個錯誤
                self.stdout.write(f"  - {error}")
            
            if len(errors) > 10:
                self.stdout.write(f"  ... 還有 {len(errors)-10} 個錯誤")
        
        if dry_run:
            self.stdout.write("\n⚠️  這是模擬運行，未實際修改數據")
            self.stdout.write("使用 --dry-run=false 來實際執行遷移")
        
        # 4. 建議後續步驟
        self.stdout.write("\n建議後續步驟:")
        self.stdout.write("1. 運行清理腳本: python manage.py cleanup_payment_references")
        self.stdout.write("2. 驗證遷移結果: python manage.py verify_payment_migration")
        self.stdout.write("3. 更新代碼引用: 移除所有對 is_paid 字段的引用")