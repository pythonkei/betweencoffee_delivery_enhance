#!/usr/bin/env python
"""
修復 queue_views.py 中的邏輯錯誤
問題：process_preparing_queues 函數會自動將隊列狀態為 preparing 的訂單狀態也改為 preparing
解決：檢查訂單狀態，如果是 completed 或 ready，則不應該出現在製作中隊列
"""

import os
import sys
import django

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

def analyze_problem():
    """分析問題"""
    print("=== 分析隊列視圖問題 ===")
    
    # 1. 檢查所有隊列狀態為 preparing 的訂單
    preparing_queues = CoffeeQueue.objects.filter(status='preparing')
    print(f"隊列狀態為 preparing 的隊列項: {preparing_queues.count()} 個")
    
    problematic_orders = []
    
    for queue_item in preparing_queues:
        order = queue_item.order
        if order.status != 'preparing':
            problematic_orders.append({
                'order_id': order.id,
                'order_status': order.status,
                'queue_status': queue_item.status,
                'queue_position': queue_item.position,
                'issue': f'訂單狀態={order.status}, 隊列狀態={queue_item.status}'
            })
    
    if problematic_orders:
        print(f"❌ 發現 {len(problematic_orders)} 個狀態不一致的訂單:")
        for item in problematic_orders:
            print(f"  訂單 #{item['order_id']}: {item['issue']}")
    else:
        print("✅ 所有隊列項與訂單狀態一致")
    
    return problematic_orders

def fix_problematic_orders(problematic_orders):
    """修復有問題的訂單"""
    print("\n=== 修復有問題的訂單 ===")
    
    fixed_count = 0
    deleted_count = 0
    
    for item in problematic_orders:
        order_id = item['order_id']
        order_status = item['order_status']
        queue_status = item['queue_status']
        
        try:
            order = OrderModel.objects.get(id=order_id)
            queue_item = CoffeeQueue.objects.get(order=order)
            
            print(f"\n處理訂單 #{order_id}: 訂單狀態={order_status}, 隊列狀態={queue_status}")
            
            if order_status == 'completed':
                # 訂單已完成，應該刪除隊列項
                queue_item.delete()
                deleted_count += 1
                print(f"  ✅ 已刪除訂單 #{order_id} 的隊列項（訂單已完成）")
                
            elif order_status == 'ready':
                # 訂單已就緒，更新隊列狀態為 ready
                queue_item.status = 'ready'
                queue_item.position = 0  # ready訂單不應該有隊列位置
                if not queue_item.actual_completion_time:
                    from django.utils import timezone
                    queue_item.actual_completion_time = timezone.now()
                queue_item.save()
                fixed_count += 1
                print(f"  ✅ 已更新訂單 #{order_id} 的隊列狀態為 ready")
                
            elif order_status == 'waiting':
                # 訂單在等待中，更新隊列狀態為 waiting
                queue_item.status = 'waiting'
                queue_item.save()
                fixed_count += 1
                print(f"  ✅ 已更新訂單 #{order_id} 的隊列狀態為 waiting")
                
            else:
                print(f"  ⚠️ 訂單 #{order_id} 狀態為 {order_status}，不需要特殊處理")
                
        except OrderModel.DoesNotExist:
            print(f"  ❌ 訂單 #{order_id} 不存在")
        except CoffeeQueue.DoesNotExist:
            print(f"  ⚠️ 訂單 #{order_id} 沒有隊列項")
        except Exception as e:
            print(f"  ❌ 修復訂單 #{order_id} 失敗: {e}")
    
    print(f"\n📊 修復統計:")
    print(f"  修復的隊列項: {fixed_count} 個")
    print(f"  刪除的隊列項: {deleted_count} 個")
    
    return fixed_count, deleted_count

def create_fixed_process_preparing_queues():
    """創建修復後的 process_preparing_queues 函數"""
    print("\n=== 創建修復後的 process_preparing_queues 函數 ===")
    
    fixed_code = '''
def process_preparing_queues(now, hk_tz):
    """處理製作中隊列數據 - 修復版本：檢查訂單狀態一致性"""
    preparing_queues = CoffeeQueue.objects.filter(status='preparing')
    preparing_data = []
    
    for queue_item in preparing_queues:
        try:
            order = queue_item.order
            
            # ====== 關鍵修復：檢查訂單狀態一致性 ======
            # 如果訂單狀態不是 preparing，根據實際狀態處理
            if order.status != 'preparing':
                if order.status == 'completed':
                    # 訂單已完成，刪除隊列項並跳過
                    logger.warning(f"訂單 {order.id} 狀態為 completed，刪除隊列項")
                    queue_item.delete()
                    continue
                elif order.status == 'ready':
                    # 訂單已就緒，更新隊列狀態為 ready
                    logger.warning(f"訂單 {order.id} 狀態為 ready，更新隊列狀態")
                    queue_item.status = 'ready'
                    queue_item.position = 0
                    if not queue_item.actual_completion_time:
                        queue_item.actual_completion_time = timezone.now()
                    queue_item.save()
                    continue
                elif order.status == 'waiting':
                    # 訂單在等待中，更新隊列狀態為 waiting
                    logger.warning(f"訂單 {order.id} 狀態為 waiting，更新隊列狀態")
                    queue_item.status = 'waiting'
                    queue_item.save()
                    continue
                else:
                    # 其他狀態，使用 OrderStatusManager 同步
                    result = OrderStatusManager.mark_as_preparing_manually(
                        order_id=order.id,
                        barista_name='system',
                        preparation_minutes=queue_item.preparation_time_minutes
                    )
                    
                    if not result['success']:
                        logger.error(f"同步訂單 {order.id} 狀態為製作中失敗: {result['message']}")
                        continue
                    else:
                        order = result['order']
            
            # 繼續處理正常的製作中訂單...
            pickup_time_info = unified_time_service.format_pickup_time_for_order(order)
            
            items = order.get_items_with_chinese_options()
            
            coffee_items = []
            bean_items = []
            all_items = []
            coffee_count = 0
            bean_count = 0
            
            for item in items:
                item_type = item.get('type', 'unknown')
                item_copy = item.copy()
                
                if not item_copy.get('image'):
                    if item_type == 'coffee':
                        item_copy['image'] = '/static/images/default-coffee.png'
                    elif item_type == 'bean':
                        item_copy['image'] = '/static/images/default-beans.png'
                    else:
                        item_copy['image'] = '/static/images/default-product.png'
                
                if item_type == 'coffee':
                    coffee_items.append(item_copy)
                    coffee_count += item_copy.get('quantity', 1)
                elif item_type == 'bean':
                    bean_items.append(item_copy)
                    bean_count += item_copy.get('quantity', 1)
                
                all_items.append(item_copy)
            
            has_coffee = len(coffee_items) > 0
            has_beans = len(bean_items) > 0
            items_count = 0
            if has_coffee:
                items_count += 1
            if has_beans:
                items_count += 1
            
            items_detail = []
            if coffee_count > 0:
                items_detail.append(f"咖啡{coffee_count}杯")
            if bean_count > 0:
                items_detail.append(f"咖啡豆{bean_count}包")
            
            items_display = f"{items_count}項商品"
            if items_detail:
                items_display += f" - {', '.join(items_detail)}"
            
            remaining_seconds = 0
            if queue_item.estimated_completion_time:
                est_completion = queue_item.estimated_completion_time
                if est_completion.tzinfo is None:
                    est_completion = timezone.make_aware(est_completion)
                est_completion_hk = est_completion.astimezone(hk_tz)
                remaining_seconds = max(0, int((est_completion_hk - now).total_seconds()))
            
            total_price = order.total_price
            if not total_price or total_price == '0.00':
                total_price = sum(float(item.get('total_price', 0) or 0) for item in all_items)
            
            created_at_hk = order.created_at.astimezone(hk_tz) if order.created_at.tzinfo else timezone.make_aware(order.created_at, hk_tz)
            
            preparation_started_at_hk = None
            if order.preparation_started_at:
                prep_start = order.preparation_started_at
                if prep_start.tzinfo is None:
                    prep_start = timezone.make_aware(prep_start)
                preparation_started_at_hk = prep_start.astimezone(hk_tz)
            
            estimated_completion_time_hk = None
            if queue_item.estimated_completion_time:
                est_comp = queue_item.estimated_completion_time
                if est_comp.tzinfo is None:
                    est_comp = timezone.make_aware(est_comp)
                estimated_completion_time_hk = est_comp.astimezone(hk_tz)
            
            preparing_data.append({
                'id': order.id,
                'order_id': order.id,
                'pickup_code': order.pickup_code or '',
                'name': order.name or '顾客',
                'phone': order.phone or '',
                'total_price': str(total_price),
                'items': all_items,
                'coffee_items': coffee_items,
                'bean_items': bean_items,
                'coffee_count': coffee_count,
                'bean_count': bean_count,
                'items_count': items_count,
                'items_detail': items_detail,
                'items_display': items_display,
                'has_coffee': has_coffee,
                'has_beans': has_beans,
                'is_mixed_order': has_coffee and has_beans,
                'is_beans_only': has_beans and not has_coffee,
                'remaining_seconds': remaining_seconds,
                'estimated_completion_time': estimated_completion_time_hk.strftime('%H:%M') if estimated_completion_time_hk else '--:--',
                'estimated_completion_time_iso': estimated_completion_time_hk.isoformat() if estimated_completion_time_hk else None,
                'payment_method': order.payment_method or '',
                'is_quick_order': order.is_quick_order,
                'preparation_started_at': preparation_started_at_hk.isoformat() if preparation_started_at_hk else None,
                'created_at': created_at_hk.isoformat(),
                'created_at_iso': created_at_hk.isoformat(),
                'queue_item_id': queue_item.id,
                'pickup_time_info': pickup_time_info,
                'pickup_time_display': pickup_time_info['text'] if pickup_time_info else '--',
                'pickup_time_choice': order.pickup_time_choice if hasattr(order, 'pickup_time_choice') else None,
            })
            
        except Exception as e:
            logger.error(f"處理製作中隊列項 {queue_item.id} 失敗: {str(e)}")
            continue
    
    return preparing_data
'''
    
    print("✅ 已創建修復後的函數代碼")
    print("\n📝 需要手動替換 eshop/views/queue_views.py 中的 process_preparing_queues 函數")
    
    return fixed_code

def main():
    """主函數"""
    print("=" * 60)
    print("隊列視圖邏輯修復工具")
    print("=" * 60)
    
    # 1. 分析問題
    problematic_orders = analyze_problem()
    
    if problematic_orders:
        # 2. 修復有問題的訂單
        fix_problematic_orders(problematic_orders)
        
        # 3. 創建修復後的函數代碼
        fixed_code = create_fixed_process_preparing_queues()
        
        print("\n" + "=" * 60)
        print("修復建議:")
        print("=" * 60)
        print("1. 手動修復 eshop/views/queue_views.py 中的 process_preparing_queues 函數")
        print("2. 替換第 200-210 行的邏輯為修復版本")
        print("3. 關鍵修復點:")
        print("   - 檢查訂單狀態是否為 'completed'，如果是則刪除隊列項")
        print("   - 檢查訂單狀態是否為 'ready'，如果是則更新隊列狀態為 ready")
        print("   - 檢查訂單狀態是否為 'waiting'，如果是則更新隊列狀態為 waiting")
        print("   - 只有當訂單狀態不是 preparing 且不是上述狀態時，才使用 OrderStatusManager 同步")
        
        print("\n📁 修復後的代碼已保存到 fix_queue_views.py")
    else:
        print("\n✅ 沒有發現狀態不一致的訂單，系統正常")
    
    print("\n" + "=" * 60)
    print("修復完成")
    print("=" * 60)

if __name__ == "__main__":
    main()