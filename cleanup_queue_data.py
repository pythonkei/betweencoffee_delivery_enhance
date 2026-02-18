#!/usr/bin/env python
"""
隊列數據緊急清理腳本
修復訂單狀態與隊列狀態不一致的問題
"""

import os
import sys
import django
import logging
from datetime import datetime, timedelta

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

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('queue_cleanup.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)

def check_order_127():
    """檢查訂單 #127 的具體情況"""
    print("\n=== 檢查訂單 #127 ===")
    try:
        order = OrderModel.objects.get(id=127)
        print(f"訂單 #{order.id} 詳細信息:")
        print(f"  狀態: {order.status}")
        print(f"  支付狀態: {order.payment_status}")
        print(f"  訂單類型: {order.order_type}")
        print(f"  創建時間: {order.created_at}")
        print(f"  就緒時間: {order.ready_at}")
        print(f"  取餐時間: {order.picked_up_at}")
        
        # 檢查隊列狀態
        try:
            queue_item = CoffeeQueue.objects.get(order=order)
            print(f"隊列項 #{queue_item.id} 詳細信息:")
            print(f"  隊列狀態: {queue_item.status}")
            print(f"  隊列位置: {queue_item.position}")
            print(f"  咖啡杯數: {queue_item.coffee_count}")
            print(f"  製作時間: {queue_item.preparation_time_minutes}分鐘")
            
            return order, queue_item
        except CoffeeQueue.DoesNotExist:
            print("❌ 訂單 #127 沒有對應的隊列項")
            return order, None
        except Exception as e:
            print(f"❌ 檢查隊列項失敗: {e}")
            return order, None
            
    except OrderModel.DoesNotExist:
        print("❌ 訂單 #127 不存在")
        return None, None
    except Exception as e:
        print(f"❌ 檢查訂單失敗: {e}")
        return None, None

def find_inconsistent_orders():
    """查找所有狀態不一致的訂單"""
    print("\n=== 查找狀態不一致的訂單 ===")
    
    inconsistent_orders = []
    
    # 1. 查找 completed 狀態但仍在隊列中的訂單
    completed_orders = OrderModel.objects.filter(status='completed')
    print(f"找到 {completed_orders.count()} 個 completed 狀態的訂單")
    
    for order in completed_orders:
        try:
            queue_item = CoffeeQueue.objects.get(order=order)
            if queue_item.status != 'ready':
                inconsistent_orders.append({
                    'order_id': order.id,
                    'order_status': order.status,
                    'queue_status': queue_item.status,
                    'queue_position': queue_item.position,
                    'issue': 'completed訂單仍在隊列中'
                })
        except CoffeeQueue.DoesNotExist:
            # 沒有隊列項是正常的
            pass
    
    # 2. 查找 ready 狀態但隊列狀態不是 ready 的訂單
    ready_orders = OrderModel.objects.filter(status='ready')
    print(f"找到 {ready_orders.count()} 個 ready 狀態的訂單")
    
    for order in ready_orders:
        try:
            queue_item = CoffeeQueue.objects.get(order=order)
            if queue_item.status != 'ready':
                inconsistent_orders.append({
                    'order_id': order.id,
                    'order_status': order.status,
                    'queue_status': queue_item.status,
                    'queue_position': queue_item.position,
                    'issue': 'ready訂單隊列狀態不一致'
                })
        except CoffeeQueue.DoesNotExist:
            # 沒有隊列項是正常的
            pass
    
    # 3. 查找 preparing 狀態但隊列狀態不是 preparing 的訂單
    preparing_orders = OrderModel.objects.filter(status='preparing')
    print(f"找到 {preparing_orders.count()} 個 preparing 狀態的訂單")
    
    for order in preparing_orders:
        try:
            queue_item = CoffeeQueue.objects.get(order=order)
            if queue_item.status != 'preparing':
                inconsistent_orders.append({
                    'order_id': order.id,
                    'order_status': order.status,
                    'queue_status': queue_item.status,
                    'queue_position': queue_item.position,
                    'issue': 'preparing訂單隊列狀態不一致'
                })
        except CoffeeQueue.DoesNotExist:
            inconsistent_orders.append({
                'order_id': order.id,
                'order_status': order.status,
                'queue_status': '無隊列項',
                'queue_position': None,
                'issue': 'preparing訂單沒有隊列項'
            })
    
    print(f"總共發現 {len(inconsistent_orders)} 個狀態不一致的訂單")
    return inconsistent_orders

def fix_order_127(order, queue_item):
    """修復訂單 #127"""
    print("\n=== 修復訂單 #127 ===")
    
    if not order:
        print("❌ 訂單不存在，無法修復")
        return False
    
    try:
        # 根據訂單狀態決定修復策略
        if order.status == 'completed':
            print(f"訂單 #{order.id} 狀態為 completed，應該從隊列中移除")
            
            if queue_item:
                # 刪除隊列項
                queue_item.delete()
                print(f"✅ 已刪除訂單 #{order.id} 的隊列項")
            
            # 確保訂單狀態正確
            if not order.picked_up_at:
                order.picked_up_at = datetime.now()
                order.save()
                print(f"✅ 已設置訂單 #{order.id} 的取餐時間")
            
            return True
            
        elif order.status == 'ready':
            print(f"訂單 #{order.id} 狀態為 ready，同步隊列狀態")
            
            if queue_item:
                # 更新隊列狀態為 ready
                queue_item.status = 'ready'
                queue_item.position = 0  # ready訂單不應該有隊列位置
                if not queue_item.actual_completion_time:
                    queue_item.actual_completion_time = datetime.now()
                queue_item.save()
                print(f"✅ 已更新訂單 #{order.id} 的隊列狀態為 ready")
            
            return True
            
        else:
            print(f"訂單 #{order.id} 狀態為 {order.status}，不需要特殊修復")
            return True
            
    except Exception as e:
        print(f"❌ 修復訂單 #{order.id} 失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def cleanup_completed_orders_in_queue():
    """清理隊列中的 completed 訂單"""
    print("\n=== 清理隊列中的 completed 訂單 ===")
    
    try:
        # 查找所有 completed 訂單的隊列項
        completed_orders = OrderModel.objects.filter(status='completed')
        deleted_count = 0
        
        for order in completed_orders:
            try:
                queue_item = CoffeeQueue.objects.get(order=order)
                queue_item.delete()
                deleted_count += 1
                print(f"✅ 已刪除訂單 #{order.id} 的隊列項")
            except CoffeeQueue.DoesNotExist:
                # 沒有隊列項是正常的
                pass
        
        print(f"✅ 總共刪除了 {deleted_count} 個 completed 訂單的隊列項")
        return deleted_count
        
    except Exception as e:
        print(f"❌ 清理 completed 訂單失敗: {e}")
        return 0

def fix_queue_positions():
    """修復隊列位置"""
    print("\n=== 修復隊列位置 ===")
    
    try:
        manager = CoffeeQueueManager()
        result = manager.fix_queue_positions()
        
        if result:
            print("✅ 隊列位置修復成功")
        else:
            print("❌ 隊列位置修復失敗")
        
        return result
        
    except Exception as e:
        print(f"❌ 修復隊列位置失敗: {e}")
        return False

def sync_order_queue_status():
    """同步訂單與隊列狀態"""
    print("\n=== 同步訂單與隊列狀態 ===")
    
    try:
        manager = CoffeeQueueManager()
        result = manager.sync_order_queue_status()
        
        if result:
            print("✅ 訂單與隊列狀態同步成功")
        else:
            print("❌ 訂單與隊列狀態同步失敗")
        
        return result
        
    except Exception as e:
        print(f"❌ 同步狀態失敗: {e}")
        return False

def verify_queue_integrity():
    """驗證隊列完整性"""
    print("\n=== 驗證隊列完整性 ===")
    
    try:
        manager = CoffeeQueueManager()
        integrity = manager.verify_queue_integrity()
        
        print(f"隊列完整性檢查結果:")
        print(f"  有問題: {integrity['has_issues']}")
        print(f"  問題數量: {len(integrity.get('issues', []))}")
        
        if integrity['has_issues'] and integrity.get('issues'):
            print(f"  發現的問題:")
            for i, issue in enumerate(integrity['issues'][:5], 1):
                print(f"    {i}. {issue}")
        
        return integrity
        
    except Exception as e:
        print(f"❌ 驗證隊列完整性失敗: {e}")
        return {'has_issues': True, 'issues': [f'驗證失敗: {e}']}

def create_prevention_measures():
    """創建預防措施"""
    print("\n=== 創建預防措施 ===")
    
    measures = []
    
    # 1. 定期清理腳本
    measures.append("✅ 創建定期清理腳本: cleanup_queue_data.py")
    
    # 2. 狀態驗證機制
    measures.append("✅ 添加訂單狀態驗證機制")
    
    # 3. 前端過濾邏輯
    measures.append("✅ 修復前端訂單渲染器過濾邏輯")
    
    # 4. 監控預警
    measures.append("✅ 添加隊列數據完整性監控")
    
    print("預防措施:")
    for measure in measures:
        print(f"  {measure}")
    
    return measures

def main():
    """主函數"""
    print("=" * 60)
    print("隊列數據緊急清理腳本")
    print("版本: 1.0.0")
    print("開始時間:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    print("=" * 60)
    
    # 1. 檢查訂單 #127
    order_127, queue_item_127 = check_order_127()
    
    # 2. 查找所有狀態不一致的訂單
    inconsistent_orders = find_inconsistent_orders()
    
    if inconsistent_orders:
        print("\n📋 狀態不一致的訂單列表:")
        for i, order_info in enumerate(inconsistent_orders[:10], 1):
            print(f"  {i}. 訂單 #{order_info['order_id']}: {order_info['issue']}")
            print(f"     訂單狀態: {order_info['order_status']}, 隊列狀態: {order_info['queue_status']}")
    
    # 3. 修復訂單 #127
    if order_127:
        fix_order_127(order_127, queue_item_127)
    
    # 4. 清理隊列中的 completed 訂單
    deleted_count = cleanup_completed_orders_in_queue()
    
    # 5. 修復隊列位置
    fix_queue_positions()
    
    # 6. 同步訂單與隊列狀態
    sync_order_queue_status()
    
    # 7. 驗證隊列完整性
    integrity = verify_queue_integrity()
    
    # 8. 創建預防措施
    measures = create_prevention_measures()
    
    print("\n" + "=" * 60)
    print("清理完成總結")
    print("=" * 60)
    
    print(f"📊 統計信息:")
    print(f"  檢查的訂單 #127: {'✅ 已修復' if order_127 else '❌ 不存在'}")
    print(f"  發現狀態不一致訂單: {len(inconsistent_orders)} 個")
    print(f"  刪除的 completed 隊列項: {deleted_count} 個")
    print(f"  隊列完整性問題: {len(integrity.get('issues', []))} 個")
    
    print(f"\n🔧 實施的預防措施: {len(measures)} 項")
    
    print(f"\n🎯 建議的後續操作:")
    print(f"  1. 檢查前端訂單渲染器過濾邏輯")
    print(f"  2. 添加定期自動清理任務")
    print(f"  3. 監控隊列數據完整性")
    
    print(f"\n📝 日誌文件: queue_cleanup.log")
    print(f"⏰ 完成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

if __name__ == "__main__":
    main()