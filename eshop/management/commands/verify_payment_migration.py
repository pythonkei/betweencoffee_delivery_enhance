#!/usr/bin/env python
"""
驗證支付狀態遷移是否完成

檢查：
1. 數據庫中是否還有 is_paid 字段
2. 代碼中是否還有對 is_paid 的引用
3. 所有訂單的 payment_status 是否正確設置
4. 模板中是否使用正確的變量
"""

import logging
from django.core.management.base import BaseCommand
from django.db import connection
from eshop.models import OrderModel

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = '驗證支付狀態遷移是否完成'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--fix',
            action='store_true',
            help='嘗試自動修復發現的問題'
        )
    
    def handle(self, *args, **options):
        fix_mode = options['fix']
        
        self.stdout.write("開始驗證支付狀態遷移...")
        
        checks_passed = 0
        total_checks = 4
        
        # 檢查 1: 數據庫字段
        self.stdout.write("\n=== 檢查 1: 數據庫字段 ===")
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name='eshop_ordermodel' AND column_name='is_paid'
                """)
                has_is_paid_column = cursor.fetchone() is not None
                
                if has_is_paid_column:
                    self.stdout.write("❌ 數據庫中仍然存在 is_paid 字段")
                    if fix_mode:
                        self.stdout.write("⚠️  需要運行數據庫遷移來移除該字段")
                else:
                    self.stdout.write("✅ 數據庫中已無 is_paid 字段")
                    checks_passed += 1
        except Exception as e:
            self.stdout.write(f"⚠️  檢查數據庫字段時出錯: {str(e)}")
        
        # 檢查 2: 訂單數據
        self.stdout.write("\n=== 檢查 2: 訂單數據 ===")
        try:
            total_orders = OrderModel.objects.count()
            self.stdout.write(f"總訂單數: {total_orders}")
            
            # 檢查支付狀態分布
            from django.db.models import Count
            payment_status_counts = OrderModel.objects.values('payment_status').annotate(count=Count('id'))
            
            valid_statuses = ['pending', 'paid', 'cancelled', 'expired']
            has_invalid_status = False
            
            for stat in payment_status_counts:
                status = stat['payment_status']
                count = stat['count']
                
                if status in valid_statuses:
                    self.stdout.write(f"✅ {status}: {count} 個訂單")
                else:
                    self.stdout.write(f"❌ 無效支付狀態: {status} ({count} 個訂單)")
                    has_invalid_status = True
            
            if not has_invalid_status:
                self.stdout.write("✅ 所有訂單都有有效的支付狀態")
                checks_passed += 1
            else:
                self.stdout.write("⚠️  發現無效的支付狀態")
                
        except Exception as e:
            self.stdout.write(f"⚠️  檢查訂單數據時出錯: {str(e)}")
        
        # 檢查 3: 代碼引用
        self.stdout.write("\n=== 檢查 3: 代碼引用 ===")
        try:
            # 運行 cleanup_payment_references 來檢查
            from eshop.management.commands.cleanup_payment_references import PaymentReferenceCleaner
            from pathlib import Path
            
            project_root = Path.cwd()
            cleaner = PaymentReferenceCleaner(project_root)
            references = cleaner.find_is_paid_references()
            
            # 過濾掉註釋和棄用警告
            actual_references = []
            for ref in references:
                content = ref['content']
                # 跳過註釋和棄用警告
                if not (content.startswith('#') or '弃用字段' in content or '已弃用' in content):
                    actual_references.append(ref)
            
            if not actual_references:
                self.stdout.write("✅ 代碼中無實際的 is_paid 引用")
                checks_passed += 1
            else:
                self.stdout.write(f"❌ 發現 {len(actual_references)} 個實際的 is_paid 引用")
                for ref in actual_references[:5]:  # 只顯示前5個
                    self.stdout.write(f"    - {ref['file']}:{ref['line']} - {ref['content']}")
                if len(actual_references) > 5:
                    self.stdout.write(f"    ... 還有 {len(actual_references)-5} 個")
                
        except Exception as e:
            self.stdout.write(f"⚠️  檢查代碼引用時出錯: {str(e)}")
        
        # 檢查 4: 模板檢查
        self.stdout.write("\n=== 檢查 4: 模板檢查 ===")
        try:
            import os
            from pathlib import Path
            
            project_root = Path.cwd()
            templates_dir = project_root / 'templates'
            
            template_references = []
            if templates_dir.exists():
                for file_path in templates_dir.rglob('*.html'):
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # 檢查模板中的 is_paid 引用
                        if 'is_paid' in content.lower():
                            relative_path = file_path.relative_to(project_root)
                            template_references.append(str(relative_path))
                    except Exception:
                        pass
            
            if not template_references:
                self.stdout.write("✅ 模板中無 is_paid 引用")
                checks_passed += 1
            else:
                self.stdout.write(f"❌ 發現 {len(template_references)} 個模板引用 is_paid")
                for ref in template_references[:5]:
                    self.stdout.write(f"    - {ref}")
                if len(template_references) > 5:
                    self.stdout.write(f"    ... 還有 {len(template_references)-5} 個")
                
        except Exception as e:
            self.stdout.write(f"⚠️  檢查模板時出錯: {str(e)}")
        
        # 總結
        self.stdout.write("\n" + "=" * 80)
        self.stdout.write("驗證結果總結:")
        self.stdout.write(f"通過的檢查: {checks_passed}/{total_checks}")
        
        if checks_passed == total_checks:
            self.stdout.write("\n🎉 支付狀態遷移驗證通過！")
            self.stdout.write("所有檢查都已通過，系統已成功遷移到 payment_status 字段。")
        else:
            self.stdout.write(f"\n⚠️  遷移尚未完全完成 ({total_checks - checks_passed} 個檢查未通過)")
            self.stdout.write("請修復上述問題後重新運行驗證。")
        
        # 建議
        self.stdout.write("\n建議:")
        if checks_passed < total_checks:
            self.stdout.write("1. 運行數據庫遷移以移除 is_paid 字段（如果存在）")
            self.stdout.write("2. 更新代碼中的 is_paid 引用")
            self.stdout.write("3. 更新模板中的變量引用")
            self.stdout.write("4. 確保所有訂單都有有效的 payment_status")
        else:
            self.stdout.write("✅ 遷移已完成，可以安全地：")
            self.stdout.write("1. 移除 models.py 中的棄用 is_paid 屬性（如果需要）")
            self.stdout.write("2. 清理相關的遷移腳本")
            self.stdout.write("3. 更新文檔以反映新的支付狀態系統")