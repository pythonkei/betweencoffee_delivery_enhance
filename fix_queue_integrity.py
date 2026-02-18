#!/usr/bin/env python3
"""
隊列數據完整性修復腳本
修復 ready 狀態訂單仍有隊列位置的問題
"""

import os
import sys
import django

# 設置 Django 環境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'betweencoffee_delivery.settings')
django.setup()

from eshop.models import CoffeeQueue, OrderModel
from django.db import transaction
import logging

# 設置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class QueueIntegrityFixer:
    """隊列完整性修復器"""
    
    def __init__(self):
        self.fixed_count = 0
        self.errors = []
    
    def analyze_problems(self):
        """分析隊列問題"""
        logger.info("🔍 開始分析隊列數據問題...")
        
        # 1. 檢查 ready 狀態但有隊列位置的隊列項
        ready_with_position = CoffeeQueue.objects.filter(status='ready', position__gt=0)
        logger.info(f"📊 發現 {ready_with_position.count()} 個 ready 狀態但有隊列位置的隊列項")
        
        if ready_with_position.exists():
            # 分析位置分佈
            positions = list(ready_with_position.values_list('position', flat=True))
            from collections import Counter
            position_counts = Counter(positions)
            
            logger.info(f"📍 位置分佈: {dict(position_counts)}")
            
            # 檢查重複位置
            duplicate_positions = {pos: count for pos, count in position_counts.items() if count > 1}
            if duplicate_positions:
                logger.warning(f"⚠️ 發現重複位置: {duplicate_positions}")
        
        # 2. 檢查隊列狀態與訂單狀態不匹配
        mismatched = []
        for queue in CoffeeQueue.objects.filter(status='ready')[:50]:  # 檢查前50個
            order = queue.order
            if order.status == 'completed':
                mismatched.append({
                    'queue_id': queue.id,
                    'order_id': order.id,
                    'queue_status': queue.status,
                    'order_status': order.status,
                    'position': queue.position
                })
        
        logger.info(f"📊 發現 {len(mismatched)} 個隊列狀態與訂單狀態不匹配的項目")
        
        return {
            'ready_with_position_count': ready_with_position.count(),
            'mismatched_count': len(mismatched),
            'sample_mismatched': mismatched[:5] if mismatched else []
        }
    
    @transaction.atomic
    def fix_ready_positions(self):
        """修復 ready 狀態隊列項的位置"""
        logger.info("🛠️ 開始修復 ready 狀態隊列項的位置...")
        
        try:
            # 1. 將所有 ready 狀態的隊列項位置設為 0
            ready_queues = CoffeeQueue.objects.filter(status='ready', position__gt=0)
            count = ready_queues.count()
            
            if count == 0:
                logger.info("✅ 沒有需要修復的 ready 狀態隊列項")
                return 0
            
            # 記錄修復前的狀態
            for queue in ready_queues[:10]:  # 記錄前10個示例
                logger.info(f"  修復前: 隊列項 #{queue.id}, 訂單 #{queue.order.id}, 位置={queue.position}")
            
            # 執行修復
            updated = ready_queues.update(position=0)
            
            logger.info(f"✅ 已修復 {updated} 個 ready 狀態隊列項的位置")
            
            # 記錄修復後的狀態
            fixed_queues = CoffeeQueue.objects.filter(id__in=ready_queues.values_list('id', flat=True)[:10])
            for queue in fixed_queues:
                logger.info(f"  修復後: 隊列項 #{queue.id}, 訂單 #{queue.order.id}, 位置={queue.position}")
            
            self.fixed_count += updated
            return updated
            
        except Exception as e:
            logger.error(f"❌ 修復 ready 狀態隊列項位置失敗: {str(e)}")
            self.errors.append(f"修復 ready 位置失敗: {str(e)}")
            raise
    
    @transaction.atomic
    def fix_completed_orders_queue_status(self):
        """修復已完成訂單的隊列狀態"""
        logger.info("🛠️ 開始修復已完成訂單的隊列狀態...")
        
        try:
            # 查找訂單狀態為 completed 但隊列狀態不是 completed 的項目
            completed_orders = OrderModel.objects.filter(status='completed')
            
            fix_count = 0
            for order in completed_orders:
                try:
                    queue_item = CoffeeQueue.objects.get(order=order)
                    if queue_item.status != 'completed':
                        old_status = queue_item.status
                        queue_item.status = 'completed'
                        queue_item.position = 0  # 確保位置為0
                        queue_item.save()
                        
                        logger.info(f"  修復: 訂單 #{order.id}, 隊列狀態 {old_status} → completed")
                        fix_count += 1
                        
                except CoffeeQueue.DoesNotExist:
                    # 沒有隊列項是正常的，有些訂單可能沒有隊列項
                    pass
                except Exception as e:
                    logger.warning(f"  修復訂單 #{order.id} 失敗: {str(e)}")
            
            logger.info(f"✅ 已修復 {fix_count} 個已完成訂單的隊列狀態")
            self.fixed_count += fix_count
            return fix_count
            
        except Exception as e:
            logger.error(f"❌ 修復已完成訂單隊列狀態失敗: {str(e)}")
            self.errors.append(f"修復已完成訂單狀態失敗: {str(e)}")
            raise
    
    @transaction.atomic
    def reorder_waiting_queue(self):
        """重新排序等待隊列"""
        logger.info("🔄 開始重新排序等待隊列...")
        
        try:
            # 獲取所有 waiting 狀態的隊列項
            waiting_queues = CoffeeQueue.objects.filter(status='waiting').order_by('created_at')
            
            if not waiting_queues.exists():
                logger.info("✅ 沒有等待中的隊列項，無需重新排序")
                return 0
            
            logger.info(f"📊 發現 {waiting_queues.count()} 個等待中的隊列項")
            
            # 記錄排序前的狀態
            logger.info("排序前的位置:")
            for queue in waiting_queues[:10]:
                logger.info(f"  隊列項 #{queue.id}, 訂單 #{queue.order.id}, 位置={queue.position}")
            
            # 重新分配位置
            reorder_count = 0
            for index, queue in enumerate(waiting_queues, start=1):
                if queue.position != index:
                    old_position = queue.position
                    queue.position = index
                    queue.save()
                    reorder_count += 1
                    
                    if reorder_count <= 10:  # 只記錄前10個變更
                        logger.info(f"  重新排序: 隊列項 #{queue.id}, 位置 {old_position} → {index}")
            
            logger.info(f"✅ 已重新排序 {reorder_count} 個等待隊列項")
            
            # 記錄排序後的狀態
            logger.info("排序後的位置（前10個）:")
            for queue in waiting_queues[:10]:
                logger.info(f"  隊列項 #{queue.id}, 訂單 #{queue.order.id}, 位置={queue.position}")
            
            return reorder_count
            
        except Exception as e:
            logger.error(f"❌ 重新排序等待隊列失敗: {str(e)}")
            self.errors.append(f"重新排序失敗: {str(e)}")
            raise
    
    def verify_fix(self):
        """驗證修復結果"""
        logger.info("🔍 開始驗證修復結果...")
        
        issues = []
        
        # 1. 檢查是否還有 ready 狀態但有位置的隊列項
        ready_with_position = CoffeeQueue.objects.filter(status='ready', position__gt=0)
        if ready_with_position.exists():
            issues.append(f"仍有 {ready_with_position.count()} 個 ready 狀態隊列項有位置")
        
        # 2. 檢查 waiting 隊列的位置連續性
        waiting_queues = CoffeeQueue.objects.filter(status='waiting').order_by('position')
        expected_pos = 1
        for queue in waiting_queues:
            if queue.position != expected_pos:
                issues.append(f"等待隊列位置不連續: 隊列項 #{queue.id} 位置={queue.position} (期望:{expected_pos})")
                break
            expected_pos += 1
        
        # 3. 檢查重複位置
        from django.db.models import Count
        duplicate_positions = CoffeeQueue.objects.filter(status='waiting') \
            .values('position') \
            .annotate(count=Count('position')) \
            .filter(count__gt=1)
        
        if duplicate_positions.exists():
            for dup in duplicate_positions:
                issues.append(f"位置 {dup['position']} 有 {dup['count']} 個隊列項")
        
        if not issues:
            logger.info("✅ 所有驗證通過，隊列數據完整")
            return True
        else:
            logger.warning(f"⚠️ 驗證發現 {len(issues)} 個問題:")
            for issue in issues:
                logger.warning(f"  • {issue}")
            return False
    
    def run_full_fix(self):
        """運行完整修復流程"""
        logger.info("=" * 60)
        logger.info("🚀 開始隊列數據完整性修復")
        logger.info("=" * 60)
        
        try:
            # 1. 分析問題
            analysis = self.analyze_problems()
            
            if analysis['ready_with_position_count'] == 0 and analysis['mismatched_count'] == 0:
                logger.info("✅ 未發現隊列數據問題，無需修復")
                return True
            
            # 2. 執行修復
            logger.info("\n🛠️ 執行修復操作...")
            
            # 修復 ready 狀態隊列項的位置
            fix1 = self.fix_ready_positions()
            
            # 修復已完成訂單的隊列狀態
            fix2 = self.fix_completed_orders_queue_status()
            
            # 重新排序等待隊列
            fix3 = self.reorder_waiting_queue()
            
            total_fixed = fix1 + fix2 + fix3
            
            # 3. 驗證修復結果
            logger.info("\n🔍 驗證修復結果...")
            verification_passed = self.verify_fix()
            
            # 4. 生成報告
            logger.info("\n" + "=" * 60)
            logger.info("📋 修復完成報告")
            logger.info("=" * 60)
            logger.info(f"✅ 總共修復了 {total_fixed} 個問題")
            logger.info(f"  • 修復 ready 狀態位置: {fix1} 個")
            logger.info(f"  • 修復已完成訂單狀態: {fix2} 個")
            logger.info(f"  • 重新排序等待隊列: {fix3} 個")
            
            if self.errors:
                logger.warning(f"⚠️ 修復過程中發現 {len(self.errors)} 個錯誤:")
                for error in self.errors:
                    logger.warning(f"  • {error}")
            
            if verification_passed:
                logger.info("✅ 驗證通過，隊列數據完整性已恢復")
            else:
                logger.warning("⚠️ 驗證未完全通過，可能需要進一步修復")
            
            logger.info("=" * 60)
            
            return verification_passed
            
        except Exception as e:
            logger.error(f"❌ 修復過程失敗: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return False

def main():
    """主函數"""
    fixer = QueueIntegrityFixer()
    
    print("隊列數據完整性修復工具")
    print("=" * 40)
    
    # 詢問用戶確認
    response = input("確定要修復隊列數據嗎？(y/N): ").strip().lower()
    
    if response != 'y':
        print("操作已取消")
        return
    
    print("\n開始修復...")
    
    success = fixer.run_full_fix()
    
    if success:
        print("\n🎉 修復完成！")
    else:
        print("\n⚠️ 修復過程中遇到問題，請檢查日誌")

if __name__ == "__main__":
    main()