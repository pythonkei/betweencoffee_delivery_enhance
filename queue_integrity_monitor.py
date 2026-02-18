#!/usr/bin/env python
"""
隊列數據完整性監控系統
實現統一的狀態轉換驗證和監控
"""

import os
import sys
import django
import logging
from datetime import datetime, timedelta
import json

# 設置Django環境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'betweencoffee_delivery.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    django.setup()
except Exception as e:
    print(f'❌ Django設置失敗: {e}')
    sys.exit(1)

from eshop.models import OrderModel, CoffeeQueue
from eshop.order_status_manager import OrderStatusManager
from eshop.queue_manager import CoffeeQueueManager
from django.utils import timezone

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('queue_integrity.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)

class QueueIntegrityMonitor:
    """隊列數據完整性監控器"""
    
    def __init__(self):
        self.issues = []
        self.fixed_count = 0
        self.deleted_count = 0
        
    def check_order_queue_consistency(self):
        """檢查訂單與隊列狀態一致性"""
        print("\n=== 檢查訂單與隊列狀態一致性 ===")
        
        # 1. 檢查所有隊列項
        all_queue_items = CoffeeQueue.objects.all()
        print(f"總隊列項數量: {all_queue_items.count()} 個")
        
        # 按狀態分組
        status_groups = {}
        for queue_item in all_queue_items:
            status = queue_item.status
            status_groups.setdefault(status, []).append(queue_item)
        
        print(f"隊列狀態分組:")
        for status, items in status_groups.items():
            print(f"  {status}: {len(items)} 個")
        
        # 2. 檢查每個隊列項的訂單狀態
        inconsistencies = []
        
        for queue_item in all_queue_items:
            order = queue_item.order
            
            # 檢查狀態一致性
            if queue_item.status == 'preparing' and order.status != 'preparing':
                inconsistencies.append({
                    'type': '狀態不一致',
                    'order_id': order.id,
                    'order_status': order.status,
                    'queue_status': queue_item.status,
                    'queue_position': queue_item.position,
                    'issue': f'隊列狀態=preparing, 訂單狀態={order.status}'
                })
            
            elif queue_item.status == 'ready' and order.status != 'ready':
                inconsistencies.append({
                    'type': '狀態不一致',
                    'order_id': order.id,
                    'order_status': order.status,
                    'queue_status': queue_item.status,
                    'queue_position': queue_item.position,
                    'issue': f'隊列狀態=ready, 訂單狀態={order.status}'
                })
            
            elif queue_item.status == 'waiting' and order.status == 'completed':
                inconsistencies.append({
                    'type': '已完成訂單在隊列中',
                    'order_id': order.id,
                    'order_status': order.status,
                    'queue_status': queue_item.status,
                    'queue_position': queue_item.position,
                    'issue': '訂單已完成但仍在隊列中'
                })
        
        if inconsistencies:
            print(f"❌ 發現 {len(inconsistencies)} 個狀態不一致問題:")
            for i, issue in enumerate(inconsistencies[:10], 1):
                print(f"  {i}. 訂單 #{issue['order_id']}: {issue['issue']}")
            
            self.issues.extend(inconsistencies)
        else:
            print("✅ 所有隊列項與訂單狀態一致")
        
        return inconsistencies
    
    def check_completed_orders_in_queue(self):
        """檢查隊列中的已完成訂單"""
        print("\n=== 檢查隊列中的已完成訂單 ===")
        
        completed_orders = OrderModel.objects.filter(status='completed')
        completed_in_queue = []
        
        for order in completed_orders:
            try:
                queue_item = CoffeeQueue.objects.get(order=order)
                completed_in_queue.append({
                    'order_id': order.id,
                    'queue_status': queue_item.status,
                    'queue_position': queue_item.position,
                    'picked_up_at': order.picked_up_at
                })
            except CoffeeQueue.DoesNotExist:
                # 沒有隊列項是正常的
                pass
        
        if completed_in_queue:
            print(f"❌ 發現 {len(completed_in_queue)} 個已完成訂單仍在隊列中:")
            for item in completed_in_queue:
                print(f"  訂單 #{item['order_id']}: 隊列狀態={item['queue_status']}, 位置={item['queue_position']}")
            
            self.issues.extend([
                {
                    'type': '已完成訂單在隊列中',
                    'order_id': item['order_id'],
                    'order_status': 'completed',
                    'queue_status': item['queue_status'],
                    'issue': '已完成訂單不應該在隊列中'
                }
                for item in completed_in_queue
            ])
        else:
            print("✅ 隊列中沒有已完成訂單")
        
        return completed_in_queue
    
    def check_ready_orders_without_queue(self):
        """檢查沒有隊列項的就緒訂單"""
        print("\n=== 檢查沒有隊列項的就緒訂單 ===")
        
        ready_orders = OrderModel.objects.filter(status='ready')
        ready_without_queue = []
        
        for order in ready_orders:
            try:
                CoffeeQueue.objects.get(order=order)
            except CoffeeQueue.DoesNotExist:
                ready_without_queue.append({
                    'order_id': order.id,
                    'ready_at': order.ready_at,
                    'issue': '就緒訂單沒有隊列項'
                })
        
        if ready_without_queue:
            print(f"⚠️ 發現 {len(ready_without_queue)} 個就緒訂單沒有隊列項:")
            for item in ready_without_queue:
                print(f"  訂單 #{item['order_id']}: 就緒時間={item['ready_at']}")
        else:
            print("✅ 所有就緒訂單都有隊列項")
        
        return ready_without_queue
    
    def check_preparing_orders_without_queue(self):
        """檢查沒有隊列項的製作中訂單"""
        print("\n=== 檢查沒有隊列項的製作中訂單 ===")
        
        preparing_orders = OrderModel.objects.filter(status='preparing')
        preparing_without_queue = []
        
        for order in preparing_orders:
            try:
                CoffeeQueue.objects.get(order=order)
            except CoffeeQueue.DoesNotExist:
                preparing_without_queue.append({
                    'order_id': order.id,
                    'preparation_started_at': order.preparation_started_at,
                    'issue': '製作中訂單沒有隊列項'
                })
        
        if preparing_without_queue:
            print(f"❌ 發現 {len(preparing_without_queue)} 個製作中訂單沒有隊列項:")
            for item in preparing_without_queue:
                print(f"  訂單 #{item['order_id']}: 開始製作時間={item['preparation_started_at']}")
            
            self.issues.extend([
                {
                    'type': '製作中訂單沒有隊列項',
                    'order_id': item['order_id'],
                    'order_status': 'preparing',
                    'issue': '製作中訂單應該有隊列項'
                }
                for item in preparing_without_queue
            ])
        else:
            print("✅ 所有製作中訂單都有隊列項")
        
        return preparing_without_queue
    
    def fix_inconsistencies(self, inconsistencies):
        """修復狀態不一致問題"""
        print("\n=== 修復狀態不一致問題 ===")
        
        if not inconsistencies:
            print("✅ 沒有需要修復的問題")
            return
        
        fixed_count = 0
        deleted_count = 0
        
        for issue in inconsistencies:
            order_id = issue['order_id']
            order_status = issue['order_status']
            queue_status = issue.get('queue_status')
            
            try:
                order = OrderModel.objects.get(id=order_id)
                
                if queue_status:
                    # 有隊列項的情況
                    try:
                        queue_item = CoffeeQueue.objects.get(order=order)
                        
                        if order_status == 'completed':
                            # 訂單已完成，刪除隊列項
                            queue_item.delete()
                            deleted_count += 1
                            print(f"  ✅ 已刪除訂單 #{order_id} 的隊列項（訂單已完成）")
                            
                        elif order_status == 'ready' and queue_status != 'ready':
                            # 訂單已就緒，更新隊列狀態
                            queue_item.status = 'ready'
                            queue_item.position = 0
                            if not queue_item.actual_completion_time:
                                queue_item.actual_completion_time = timezone.now()
                            queue_item.save()
                            fixed_count += 1
                            print(f"  ✅ 已更新訂單 #{order_id} 的隊列狀態為 ready")
                            
                        elif order_status == 'preparing' and queue_status != 'preparing':
                            # 訂單在製作中，更新隊列狀態
                            queue_item.status = 'preparing'
                            queue_item.save()
                            fixed_count += 1
                            print(f"  ✅ 已更新訂單 #{order_id} 的隊列狀態為 preparing")
                            
                        elif order_status == 'waiting' and queue_status != 'waiting':
                            # 訂單在等待中，更新隊列狀態
                            queue_item.status = 'waiting'
                            queue_item.save()
                            fixed_count += 1
                            print(f"  ✅ 已更新訂單 #{order_id} 的隊列狀態為 waiting")
                            
                    except CoffeeQueue.DoesNotExist:
                        # 沒有隊列項
                        if order_status == 'preparing':
                            # 製作中訂單應該有隊列項，創建一個
                            CoffeeQueue.objects.create(
                                order=order,
                                status='preparing',
                                coffee_count=order.get_coffee_count(),
                                preparation_time_minutes=5  # 默認值
                            )
                            fixed_count += 1
                            print(f"  ✅ 已為訂單 #{order_id} 創建隊列項（製作中）")
                
            except OrderModel.DoesNotExist:
                print(f"  ❌ 訂單 #{order_id} 不存在")
            except Exception as e:
                print(f"  ❌ 修復訂單 #{order_id} 失敗: {e}")
        
        self.fixed_count += fixed_count
        self.deleted_count += deleted_count
        
        print(f"\n📊 修復統計:")
        print(f"  修復的隊列項: {fixed_count} 個")
        print(f"  刪除的隊列項: {deleted_count} 個")
        
        return fixed_count, deleted_count
    
    def create_prevention_rules(self):
        """創建預防規則"""
        print("\n=== 創建預防規則 ===")
        
        rules = [
            {
                'name': '狀態一致性規則',
                'description': '隊列狀態必須與訂單狀態一致',
                'conditions': [
                    'queue.status == "preparing" => order.status == "preparing"',
                    'queue.status == "ready" => order.status == "ready"',
                    'queue.status == "waiting" => order.status == "waiting"',
                    'order.status == "completed" => queue should not exist'
                ]
            },
            {
                'name': '隊列項存在規則',
                'description': '特定狀態的訂單必須有隊列項',
                'conditions': [
                    'order.status == "preparing" => queue must exist',
                    'order.status == "waiting" => queue must exist'
                ]
            },
            {
                'name': '隊列位置規則',
                'description': '就緒訂單不應該有隊列位置',
                'conditions': [
                    'queue.status == "ready" => queue.position == 0'
                ]
            }
        ]
        
        print("預防規則:")
        for rule in rules:
            print(f"\n📋 {rule['name']}:")
            print(f"  描述: {rule['description']}")
            print(f"  條件:")
            for condition in rule['conditions']:
                print(f"    • {condition}")
        
        return rules
    
    def generate_monitoring_dashboard(self):
        """生成監控儀表板數據"""
        print("\n=== 生成監控儀表板數據 ===")
        
        # 統計數據
        total_orders = OrderModel.objects.count()
        total_queue_items = CoffeeQueue.objects.count()
        
        # 狀態分佈
        order_status_dist = {}
        for status in ['waiting', 'preparing', 'ready', 'completed']:
            count = OrderModel.objects.filter(status=status).count()
            order_status_dist[status] = count
        
        queue_status_dist = {}
        for status in ['waiting', 'preparing', 'ready']:
            count = CoffeeQueue.objects.filter(status=status).count()
            queue_status_dist[status] = count
        
        dashboard_data = {
            'timestamp': timezone.now().isoformat(),
            'summary': {
                'total_orders': total_orders,
                'total_queue_items': total_queue_items,
                'order_status_distribution': order_status_dist,
                'queue_status_distribution': queue_status_dist
            },
            'issues': {
                'total': len(self.issues),
                'fixed': self.fixed_count,
                'deleted': self.deleted_count,
                'details': self.issues[:20]  # 只顯示前20個問題
            },
            'health_score': self.calculate_health_score()
        }
        
        # 保存到文件
        with open('queue_monitoring_dashboard.json', 'w', encoding='utf-8') as f:
            json.dump(dashboard_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 監控儀表板數據已保存到 queue_monitoring_dashboard.json")
        
        return dashboard_data
    
    def calculate_health_score(self):
        """計算系統健康分數"""
        total_issues = len(self.issues)
        
        if total_issues == 0:
            return 100
        elif total_issues <= 5:
            return 90
        elif total_issues <= 10:
            return 80
        elif total_issues <= 20:
            return 70
        elif total_issues <= 50:
            return 60
        else:
            return 50
    
    def run_full_check(self):
        """運行完整檢查"""
        print("=" * 60)
        print("隊列數據完整性監控系統")
        print("開始時間:", timezone.now().strftime('%Y-%m-%d %H:%M:%S'))
        print("=" * 60)
        
        # 1. 檢查各種不一致問題
        inconsistencies = self.check_order_queue_consistency()
        completed_in_queue = self.check_completed_orders_in_queue()
        ready_without_queue = self.check_ready_orders_without_queue()
        preparing_without_queue = self.check_preparing_orders_without_queue()
        
        # 2. 修復問題
        all_issues = inconsistencies + [
            {
                'type': '已完成訂單在隊列中',
                'order_id': item['order_id'],
                'order_status': 'completed',
                'queue_status': item['queue_status']
            }
            for item in completed_in_queue
        ] + [
            {
                'type': '製作中訂單沒有隊列項',
                'order_id': item['order_id'],
                'order_status': 'preparing'
            }
            for item in preparing_without_queue
        ]
        
        self.fix_inconsistencies(all_issues)
        
        # 3. 創建預防規則
        rules = self.create_prevention_rules()
        
        # 4. 生成監控儀表板
        dashboard = self.generate_monitoring_dashboard()
        
        # 5. 輸出總結
        print("\n" + "=" * 60)
        print("監控完成總結")
        print("=" * 60)
        
        print(f"📊 系統狀態:")
        print(f"  總訂單數: {dashboard['summary']['total_orders']}")
        print(f"  總隊列項數: {dashboard['summary']['total_queue_items']}")
        print(f"  訂單狀態分佈: {dashboard['summary']['order_status_distribution']}")
        print(f"  隊列狀態分佈: {dashboard['summary']['queue_status_distribution']}")
        
        print(f"\n🔧 問題處理:")
        print(f"  發現問題: {len(self.issues)} 個")
        print(f"  修復隊列項: {self.fixed_count} 個")
        print(f"  刪除隊列項: {self.deleted_count} 個")
        
        print(f"\n🏥 系統健康分數: {dashboard['health_score']}/100")
        
        print(f"\n📝 日誌文件: queue_integrity.log")
        print(f"📊 儀表板文件: queue_monitoring_dashboard.json")
        print(f"⏰ 完成時間: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        return {
            'success': True,
            'issues_found': len(self.issues),
            'issues_fixed': self.fixed_count,
            'issues_deleted': self.deleted_count,
            'health_score': dashboard['health_score']
        }

def main():
    """主函數"""
    monitor = QueueIntegrityMonitor()
    result = monitor.run_full_check()
    
    # 根據結果提供建議
    if result['health_score'] >= 90:
        print("\n🎉 系統狀態優秀！")
        print("建議：定期運行監控腳本（每天1-2次）")
    elif result['health_score'] >= 70:
        print("\n👍 系統狀態良好")
        print("建議：檢查並修復發現的問題")
    elif result['health_score'] >= 50:
        print("\n⚠️ 系統狀態一般")
        print("建議：立即修復問題，並考慮優化隊列管理邏輯")
    else:
        print("\n❌ 系統狀態不佳")
        print("建議：全面檢查隊列數據，可能需要手動干預")
    
    print("\n🔧 維護建議:")
    print("1. 將此腳本添加到定時任務（cron）中")
    print("2. 每天至少運行一次完整性檢查")
    print("3. 監控 queue_integrity.log 文件")
    print("4. 定期查看 queue_monitoring_dashboard.json")
    
    return result

if __name__ == "__main__":
    main()
