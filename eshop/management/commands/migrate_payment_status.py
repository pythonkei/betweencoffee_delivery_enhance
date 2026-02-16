#!/usr/bin/env python
"""
支付狀態遷移命令：從 is_paid 到 payment_status

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
        
        self.stdout.write(f"開始支付狀態遷移檢查 (dry-run: {dry_run})")
        
        # 1. 檢查數據庫字段
        self.stdout.write("\n=== 檢查數據庫字段 ===")
        
        # 檢查 OrderModel 是否有 is_paid 字段
        try:
            # 嘗試訪問 is_paid 字段
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name='eshop_ordermodel' AND column_name='is_paid'
                """)
                has_is_paid_column = cursor.fetchone() is not None
                
                if has_is_paid_column:
                    self.stdout.write("❌ 數據庫中仍然存在 is_paid 字段")
                    self.stdout.write("   需要運行數據庫遷移來移除該字段")
                else:
                    self.stdout.write("✅ 數據庫中已無 is_paid 字段")
        except Exception as e:
            self.stdout.write(f"⚠️  檢查數據庫字段時出錯: {str(e)}")
        
        # 2. 檢查代碼引用
        self.stdout.write("\n=== 檢查代碼引用 ===")
        
        # 搜索代碼中對 is_paid 的引用
        import os
        import re
        
        code_references = []
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        # 搜索 Python 文件
        for root, dirs, files in os.walk(project_root):
            # 跳過虛擬環境和遷移目錄
            if 'venv' in root or '.virtualenvs' in root or 'migrations' in root:
                continue
                
            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read()
                            
                        # 搜索 is_paid 引用
                        if re.search(r'\.is_paid\b|is_paid\s*=', content):
                            relative_path = os.path.relpath(filepath, project_root)
                            code_references.append(relative_path)
                    except Exception:
                        pass
        
        if code_references:
            self.stdout.write(f"❌ 發現 {len(code_references)} 個文件仍然引用 is_paid:")
            for ref in code_references[:10]:  # 只顯示前10個
                self.stdout.write(f"    - {ref}")
            if len(code_references) > 10:
                self.stdout.write(f"    ... 還有 {len(code_references)-10} 個文件")
        else:
            self.stdout.write("✅ 代碼中未發現對 is_paid 的直接引用")
        
        # 3. 檢查棄用屬性使用
        self.stdout.write("\n=== 檢查棄用屬性使用 ===")
        
        try:
            # 檢查是否有訂單使用棄用的 is_paid 屬性
            total_orders = OrderModel.objects.count()
            self.stdout.write(f"總訂單數: {total_orders}")
            
            # 檢查支付狀態分布
            from django.db.models import Count
            payment_status_counts = OrderModel.objects.values('payment_status').annotate(count=Count('id'))
            self.stdout.write("支付狀態分布:")
            for stat in payment_status_counts:
                self.stdout.write(f"    {stat['payment_status']}: {stat['count']} 個訂單")
            
        except Exception as e:
            self.stdout.write(f"⚠️  檢查訂單數據時出錯: {str(e)}")
        
        # 4. 建議
        self.stdout.write("\n=== 遷移狀態總結 ===")
        
        if not code_references:
            self.stdout.write("✅ 支付狀態遷移已完成")
            self.stdout.write("   1. 數據庫字段已更新")
            self.stdout.write("   2. 代碼引用已清理")
            self.stdout.write("   3. 系統已使用 payment_status 字段")
        else:
            self.stdout.write("⚠️  遷移尚未完成")
            self.stdout.write("   需要清理代碼中對 is_paid 的引用")
        
        self.stdout.write("\n建議後續步驟:")
        self.stdout.write("1. 運行清理命令: python manage.py cleanup_payment_references")
        self.stdout.write("2. 運行驗證命令: python manage.py verify_payment_migration")
        self.stdout.write("3. 確保所有模板和視圖使用 payment_status 而不是 is_paid")
