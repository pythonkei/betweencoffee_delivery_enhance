#!/usr/bin/env python
"""
驗證支付狀態遷移結果

檢查遷移後的數據一致性：
1. 檢查 is_paid 和 payment_status 的一致性
2. 報告不一致的訂單
3. 提供修復建議
"""

import logging
from django.core.management.base import BaseCommand
from eshop.models import OrderModel

logger = logging.getLogger(__name__)


class PaymentMigrationVerifier:
    """支付狀態遷移驗證器"""
    
    def __init__(self):
        self.inconsistencies = []
        self.stats = {
            'total_orders': 0,
            'orders_with_is_paid': 0,
            'consistent_orders': 0,
            'inconsistent_orders': 0,
            'by_status': {},
        }
    
    def verify_migration(self):
        """驗證遷移結果"""
        # 獲取所有訂單
        orders = OrderModel.objects.all()
        self.stats['total_orders'] = orders.count()
        
        for order in orders:
            self._check_order_consistency(order)
        
        return self.inconsistencies, self.stats
    
    def _check_order_consistency(self, order):
        """檢查單個訂單的一致性"""
        has_is_paid = order.is_paid is not None
        if has_is_paid:
            self.stats['orders_with_is_paid'] += 1
        
        # 統計支付狀態
        status = order.payment_status or 'unknown'
        self.stats['by_status'][status] = self.stats['by_status'].get(status, 0) + 1
        
        # 檢查一致性
        is_consistent = True
        issues = []
        
        if has_is_paid:
            # 檢查 is_paid 和 payment_status 的一致性
            if order.is_paid and order.payment_status != 'paid':
                is_consistent = False
                issues.append(f"is_paid=True 但 payment_status={order.payment_status}")
            
            if not order.is_paid and order.payment_status == 'paid':
                is_consistent = False
                issues.append(f"is_paid=False 但 payment_status={order.payment_status}")
        
        # 檢查 payment_status 的有效性
        valid_statuses = ['pending', 'paid', 'failed', 'refunded', 'cancelled']
        if order.payment_status and order.payment_status not in valid_statuses:
            is_consistent = False
            issues.append(f"無效的 payment_status: {order.payment_status}")
        
        if is_consistent:
            self.stats['consistent_orders'] += 1
        else:
            self.stats['inconsistent_orders'] += 1
            self.inconsistencies.append({
                'order_id': order.id,
                'is_paid': order.is_paid,
                'payment_status': order.payment_status,
                'issues': issues,
                'created_at': order.created_at,
            })
    
    def generate_report(self):
        """生成驗證報告"""
        report_lines = []
        report_lines.append("支付狀態遷移驗證報告")
        report_lines.append("=" * 80)
        
        # 統計信息
        report_lines.append("\n統計信息:")
        report_lines.append(f"  總訂單數: {self.stats['total_orders']}")
        report_lines.append(f"  包含 is_paid 的訂單: {self.stats['orders_with_is_paid']}")
        report_lines.append(f"  一致的訂單: {self.stats['consistent_orders']}")
        report_lines.append(f"  不一致的訂單: {self.stats['inconsistent_orders']}")
        
        # 支付狀態分佈
        report_lines.append("\n支付狀態分佈:")
        for status, count in sorted(self.stats['by_status'].items()):
            percentage = (count / self.stats['total_orders'] * 100) if self.stats['total_orders'] > 0 else 0
            report_lines.append(f"  {status}: {count} ({percentage:.1f}%)")
        
        # 不一致訂單詳情
        if self.inconsistencies:
            report_lines.append("\n不一致的訂單:")
            report_lines.append("-" * 40)
            
            for inc in self.inconsistencies[:20]:  # 只顯示前20個
                report_lines.append(f"\n訂單 #{inc['order_id']}:")
                report_lines.append(f"  is_paid: {inc['is_paid']}")
                report_lines.append(f"  payment_status: {inc['payment_status']}")
                report_lines.append(f"  創建時間: {inc['created_at']}")
                for issue in inc['issues']:
                    report_lines.append(f"  問題: {issue}")
            
            if len(self.inconsistencies) > 20:
                report_lines.append(f"\n... 還有 {len(self.inconsistencies) - 20} 個不一致的訂單")
        
        # 建議
        report_lines.append("\n" + "=" * 80)
        report_lines.append("建議:")
        
        if self.stats['inconsistent_orders'] == 0:
            report_lines.append("✅ 所有訂單的支付狀態一致")
            report_lines.append("建議下一步: 運行清理腳本移除 is_paid 引用")
        else:
            report_lines.append("⚠️  發現不一致的訂單")
            report_lines.append("建議修復步驟:")
            report_lines.append("1. 手動檢查不一致的訂單")
            report_lines.append("2. 根據業務邏輯修正 payment_status")
            report_lines.append("3. 重新運行遷移驗證")
        
        return "\n".join(report_lines)


class Command(BaseCommand):
    help = '驗證支付狀態遷移結果'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--fix',
            action='store_true',
            help='自動修復不一致的訂單（謹慎使用）'
        )
    
    def handle(self, *args, **options):
        fix_mode = options['fix']
        
        self.stdout.write("開始驗證支付狀態遷移結果...")
        
        verifier = PaymentMigrationVerifier()
        inconsistencies, stats = verifier.verify_migration()
        
        # 生成報告
        report = verifier.generate_report()
        self.stdout.write(report)
        
        # 自動修復（如果啟用）
        if fix_mode and inconsistencies:
            self.stdout.write("\n嘗試自動修復不一致的訂單...")
            fixed_count = self._fix_inconsistencies(inconsistencies)
            self.stdout.write(f"已修復 {fixed_count} 個訂單")
            
            # 重新驗證
            self.stdout.write("\n重新驗證修復結果...")
            verifier = PaymentMigrationVerifier()
            inconsistencies, stats = verifier.verify_migration()
            report = verifier.generate_report()
            self.stdout.write(report)
    
    def _fix_inconsistencies(self, inconsistencies):
        """自動修復不一致的訂單"""
        fixed_count = 0
        
        for inc in inconsistencies:
            try:
                order = OrderModel.objects.get(id=inc['order_id'])
                
                # 根據 is_paid 修正 payment_status
                if order.is_paid is not None:
                    if order.is_paid:
                        order.payment_status = 'paid'
                    else:
                        order.payment_status = 'pending'
                    
                    order.save(update_fields=['payment_status'])
                    fixed_count += 1
                    self.stdout.write(f"修復訂單 #{order.id}: payment_status -> {order.payment_status}")
                    
            except Exception as e:
                logger.error(f"修復訂單 {inc['order_id']} 失敗: {str(e)}")
        
        return fixed_count