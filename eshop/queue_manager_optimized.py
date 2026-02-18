# eshop/queue_manager_optimized.py
"""
優化版的咖啡制作隊列管理器
主要改進：
1. 消除重複代碼
2. 統一錯誤處理
3. 提取共用邏輯
4. 改進代碼結構
"""

import logging
import pytz
from django.utils import timezone
from datetime import timedelta
from .models import CoffeeQueue, OrderModel
from .time_calculation import unified_time_service
from .order_status_manager import OrderStatusManager

logger = logging.getLogger(__name__)


class CoffeeQueueManager:
    """咖啡制作隊列管理器 - 優化版"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    # ==================== 核心隊列操作方法 ====================
    
    def add_order_to_queue(self, order, use_priority=True):
        """
        將訂單添加到隊列 - 統一方法
        
        Args:
            order: OrderModel實例
            use_priority: 是否使用優先級排序（默認True）
        
        Returns:
            CoffeeQueue實例或None
        """
        try:
            self.logger.info(f"=== 開始將訂單 {order.id} 加入隊列 ===")
            
            # 檢查訂單是否已經在隊列中
            if CoffeeQueue.objects.filter(order=order).exists():
                self.logger.warning(f"訂單 {order.id} 已在隊列中")
                return CoffeeQueue.objects.get(order=order)
            
            # 計算咖啡杯數
            coffee_count = self._calculate_coffee_count(order)
            self.logger.info(f"訂單 {order.id} 包含 {coffee_count} 杯咖啡")
            
            if coffee_count == 0:
                self.logger.info(f"訂單 {order.id} 不包含咖啡，跳過加入隊列")
                return None
            
            # 計算位置（根據是否使用優先級）
            if use_priority:
                position = self._calculate_priority_position(order, coffee_count)
            else:
                position = self._get_next_position()
            
            # 計算製作時間
            preparation_time = unified_time_service.calculate_preparation_time(coffee_count)
            
            # 創建隊列項
            queue_item = CoffeeQueue.objects.create(
                order=order,
                position=position,
                coffee_count=coffee_count,
                preparation_time_minutes=preparation_time,
                status='waiting'
            )
            
            self.logger.info(f"創建隊列項成功: {queue_item.id}, 位置: {position}, 預計製作時間: {preparation_time}分鐘")
            
            # 檢查並重新排序隊列（確保優先級正確）
            if use_priority:
                self._check_and_reorder_queue_by_priority()
            
            # 更新隊列時間
            self.update_estimated_times()
            
            self.logger.info(f"訂單 {order.id} 已加入隊列，位置: {position}")
            return queue_item
            
        except Exception as e:
            self.logger.error(f"添加訂單到隊列失敗: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            return None
    
    # ==================== 輔助方法（私有） ====================
    
    def _calculate_coffee_count(self, order):
        """計算訂單中的咖啡杯數"""
        items = order.get_items()
        coffee_count = 0
        for item in items:
            if item.get('type') == 'coffee':
                coffee_count += item.get('quantity', 1)
        return coffee_count
    
    def _get_next_position(self):
        """獲取下一個隊列位置（簡單順序）"""
        try:
            last_item = CoffeeQueue.objects.filter(status='waiting').order_by('-position').first()
            if last_item:
                return last_item.position + 1
            return 1
        except Exception as e:
            self.logger.error(f"獲取下一個隊列位置失敗: {str(e)}")
            return 1
    
    def _calculate_priority_position(self, order, coffee_count):
        """
        計算優先級位置
        
        優先級規則：
        1. 所有快速訂單優先
        2. 快速訂單內部按創建時間排序
        3. 普通訂單按創建時間排序
        """
        try:
            # 獲取當前所有等待中的訂單
            waiting_queues = CoffeeQueue.objects.filter(status='waiting').order_by('position')
            
            # 如果沒有等待訂單，返回位置1
            if not waiting_queues.exists():
                return 1
            
            # 如果是快速訂單
            if order.order_type == 'quick':
                for queue in waiting_queues:
                    other_order = queue.order
                    
                    # 如果遇到第一個普通訂單，快速訂單應該排在它前面
                    if other_order.order_type != 'quick':
                        return queue.position
                    
                    # 如果都是快速訂單，按創建時間排序（先來先做）
                    if order.created_at < other_order.created_at:
                        return queue.position
                
                # 如果所有訂單都是快速訂單且當前訂單創建時間最晚，添加到隊尾
                last_position = waiting_queues.last().position
                return last_position + 1
            
            else:
                # 普通訂單：添加到所有快速訂單後面
                # 找到最後一個快速訂單的位置
                last_quick_position = 0
                for queue in waiting_queues:
                    if queue.order.order_type == 'quick':
                        last_quick_position = max(last_quick_position, queue.position)
                
                # 如果沒有快速訂單，按創建時間插入到普通訂單中
                if last_quick_position == 0:
                    for queue in waiting_queues:
                        if order.created_at < queue.order.created_at:
                            return queue.position
                
                # 如果有快速訂單，插入到最後一個快速訂單之後
                return last_quick_position + 1 if last_quick_position > 0 else len(waiting_queues) + 1
                
        except Exception as e:
            self.logger.error(f"計算優先級位置失敗: {str(e)}")
            # 降級處理：添加到隊尾
            last_item = CoffeeQueue.objects.filter(status='waiting').order_by('-position').first()
            if last_item:
                return last_item.position + 1
            return 1
    
    def _check_and_reorder_queue_by_priority(self):
        """檢查並重新排序隊列（基於優先級）"""
        try:
            self.logger.info("=== 檢查隊列優先級排序 ===")
            
            waiting_queues = CoffeeQueue.objects.filter(status='waiting')
            
            if not waiting_queues.exists():
                self.logger.info("等待隊列為空，無需排序")
                return False
            
            # 收集所有等待訂單的信息
            queues_with_info = []
            for queue in waiting_queues:
                order = queue.order
                info = {
                    'queue_id': queue.id,
                    'order_id': order.id,
                    'order_type': order.order_type,
                    'pickup_time_choice': getattr(order, 'pickup_time_choice', None),
                    'latest_start_time': getattr(order, 'latest_start_time', None),
                    'current_position': queue.position,
                    'coffee_count': queue.coffee_count,
                    'created_at': order.created_at,
                }
                queues_with_info.append(info)
            
            # 優先級排序邏輯
            def get_queue_priority(info):
                # 快速訂單優先級計算
                if info['order_type'] == 'quick':
                    return (0, info['created_at'].timestamp())
                
                # 普通訂單優先級計算
                return (1, info['created_at'].timestamp())
            
            # 排序
            queues_with_info.sort(key=get_queue_priority)
            
            # 檢查是否需要重新排序
            needs_reorder = False
            for index, info in enumerate(queues_with_info, start=1):
                if info['current_position'] != index:
                    needs_reorder = True
                    break
            
            if needs_reorder:
                self.logger.info("檢測到隊列順序需要調整，重新排序...")
                
                # 暫時清除所有位置（避免唯一性約束衝突）
                for queue in waiting_queues:
                    queue.position = 0
                    queue.save()
                
                # 按新順序分配位置
                for index, info in enumerate(queues_with_info, start=1):
                    queue = CoffeeQueue.objects.get(id=info['queue_id'])
                    old_position = info['current_position']
                    queue.position = index
                    queue.save()
                    
                    order_type_display = "快速訂單" if info['order_type'] == 'quick' else "普通訂單"
                    pickup_display = f"（{info['pickup_time_choice']}分鐘）" if info['pickup_time_choice'] else ""
                    
                    self.logger.info(f"調整訂單 #{queue.order.id} 位置: {old_position} → {index} [{order_type_display}{pickup_display}]")
                
                # 更新時間估算
                self.update_estimated_times()
                self.logger.info("隊列優先級排序完成")
                return True
            else:
                self.logger.info("隊列順序正常，無需調整")
                return False
                
        except Exception as e:
            self.logger.error(f"檢查隊列優先級排序失敗: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            return False
    
    # ==================== 公開方法 ====================
    
    def get_queue_summary(self):
        """獲取隊列摘要"""
        try:
            waiting = CoffeeQueue.objects.filter(status='waiting').count()
            preparing = CoffeeQueue.objects.filter(status='preparing').count()
            ready = CoffeeQueue.objects.filter(status='ready').count()
            
            return {
                'waiting': waiting,
                'preparing': preparing,
                'ready': ready,
                'total': waiting + preparing + ready
            }
        except Exception as e:
            self.logger.error(f"獲取隊列摘要失敗: {str(e)}")
            return {'waiting': 0, 'preparing': 0, 'ready': 0, 'total': 0}
    
    def update_estimated_times(self):
        """更新所有等待隊列項的預計時間（香港時區）"""
        try:
            # 先檢查並重新排序（確保順序正確）
            self._check_and_reorder_queue_by_priority()
            
            # 使用統一的香港時間函數
            current_time = unified_time_service.get_hong_kong_time()
            self.logger.info(f"=== 更新隊列預計時間（香港時區）===")
            self.logger.info(f"當前香港時間: {current_time}")
            
            # 獲取按正確順序排列的等待隊列
            waiting_queues = CoffeeQueue.objects.filter(status='waiting').order_by('position')
            
            # 計算累計時間
            cumulative_time = timedelta(minutes=0)
            processed_count = 0
            
            for queue in waiting_queues:
                try:
                    order = queue.order
                    
                    # 預計開始時間 = 當前時間 + 累計時間
                    estimated_start_time = current_time + cumulative_time
                    queue.estimated_start_time = estimated_start_time
                    
                    # 計算這個訂單的製作時間
                    prep_time = timedelta(minutes=queue.preparation_time_minutes)
                    
                    # 預計完成時間
                    queue.estimated_completion_time = estimated_start_time + prep_time
                    
                    # 保存更新
                    queue.save()
                    
                    # 更新累計時間
                    cumulative_time += prep_time
                    processed_count += 1
                    
                    # 獲取訂單類型顯示
                    order_type_display = "快速" if order.order_type == 'quick' else "普通"
                    pickup_display = f"（{order.pickup_time_choice}分鐘）" if hasattr(order, 'pickup_time_choice') and order.pickup_time_choice else ""
                    
                    self.logger.info(f"等待訂單 #{order.id} [{order_type_display}訂單{pickup_display}] - 位置: {queue.position}, " +
                            f"預計開始: {queue.estimated_start_time.strftime('%H:%M')}, " +
                            f"預計完成: {queue.estimated_completion_time.strftime('%H:%M')}, " +
                            f"製作時間: {queue.preparation_time_minutes}分鐘")
                    
                except Exception as e:
                    self.logger.error(f"處理等待訂單 #{queue.order.id if queue.order else '未知'} 失敗: {str(e)}")
                    continue
            
            self.logger.info(f"=== 隊列時間更新完成，處理了 {processed_count} 個等待訂單 ===")
            return True
            
        except Exception as e:
            self.logger.error(f"更新預計時間失敗: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            return False
    
    def calculate_wait_time(self, queue_item):
        """計算等待時間（香港時區）"""
        try:
            # 如果已經是preparing狀態，等待時間為0
            if queue_item.status == 'preparing':
                return 0
            
            # 獲取當前香港時間
            current_time = unified_time_service.get_hong_kong_time()
            
            # 如果有預計開始時間，直接計算
            if queue_item.estimated_start_time:
                # 確保 estimated_start_time 是香港時區
                if isinstance(queue_item.estimated_start_time, str):
                    from django.utils.dateparse import parse_datetime
                    estimated_start = parse_datetime(queue_item.estimated_start_time)
                    if estimated_start:
                        # 轉換為香港時區
                        hk_tz = pytz.timezone('Asia/Hong_Kong')
                        if estimated_start.tzinfo is None:
                            estimated_start = pytz.UTC.localize(estimated_start)
                        estimated_start = estimated_start.astimezone(hk_tz)
                else:
                    estimated_start = queue_item.estimated_start_time
                
                if estimated_start:
                    # 計算分鐘差
                    wait_delta = estimated_start - current_time
                    wait_minutes = max(0, int(wait_delta.total_seconds() / 60))
                    return wait_minutes
            
            # 否則手動計算
            # 獲取當前訂單之前的所有等待訂單
            waiting_before = CoffeeQueue.objects.filter(
                status='waiting',
                position__lt=queue_item.position
            ).order_by('position')
            
            total_minutes = 0
            
            # 加上當前正在製作訂單的剩餘時間
            preparing_now = CoffeeQueue.objects.filter(status='preparing').first()
            if preparing_now and preparing_now.actual_start_time:
                elapsed = current_time - preparing_now.actual_start_time
                total_prep = timedelta(minutes=preparing_now.preparation_time_minutes)
                remaining = total_prep - elapsed
                if remaining > timedelta(0):
                    total_minutes += remaining.total_seconds() / 60
            
            # 加上前面等待訂單的製作時間
            for waiting in waiting_before:
                total_minutes += waiting.preparation_time_minutes
            
            return int(total_minutes)
            
        except Exception as e:
            self.logger.error(f"計算等待時間失敗: {str(e)}")
            return 0
    
    def fix_queue_positions(self):
        """修復隊列位置：確保ready訂單不計入，waiting訂單位置連續"""
        try:
            self.logger.info("=== 開始修復隊列位置 ===")
            
            # 1. 將所有ready訂單的位置設為0
            ready_updated = CoffeeQueue.objects.filter(status='ready').update(position=0)
            self.logger.info(f"已將 {ready_updated} 個ready訂單位置設為0")
            
            # 2. 重新為waiting訂單分配連續位置
            waiting_queues = CoffeeQueue.objects.filter(status='waiting').order_by('created_at')
            
            position = 1
            for queue in waiting_queues:
                if queue.position != position:
                    self.logger.info(f"修復訂單 #{queue.order.id} 位置: {queue.position} -> {position}")
                    queue.position = position
                    queue.save()
                position += 1
            
            self.logger.info(f"重新分配了 {position-1} 個等待訂單的位置")
            
            # 3. 更新預計時間
            self.update_estimated_times()
            
            self.logger.info("=== 隊列位置修復完成 ===")
            return True
            
        except Exception as e:
            self.logger.error(f"修復隊列位置失敗: {str(e)}")
            return False
    
    def verify_queue_integrity(self):
        """驗證隊列完整性"""
        try:
            issues = []
            
            # 檢查ready訂單是否有位置（不應該有）
            ready_with_position = CoffeeQueue.objects.filter(status='ready', position__gt=0)
            if ready_with_position.exists():
                issues.append(f"發現 {ready_with_position.count()} 個ready訂單有隊列位置")
            
            # 檢查waiting訂單位置是否連續
            waiting_queues = CoffeeQueue.objects.filter(status='waiting').order_by('position')
            expected_pos = 1
            for queue in waiting_queues:
                if queue.position != expected_pos:
                    issues.append(f"訂單 #{queue.order.id} 位置不連續: {queue.position} (期望: {expected_pos})")
                expected_pos += 1
            
            # 檢查是否有重複位置
            from django.db.models import Count
            duplicate_positions = CoffeeQueue.objects.filter(status='waiting') \
                .values('position') \
                .annotate(count=Count('position')) \
                .filter(count__gt=1)
            
            for dup in duplicate_positions:
                issues.append(f"位置 {dup['position']} 有 {dup['count']} 個訂單")
            
            return {
                'has_issues': len(issues) > 0,
                'issues': issues,
                'waiting_count': waiting_queues.count(),
                'preparing_count': CoffeeQueue.objects.filter(status='preparing').count(),
                'ready_count': CoffeeQueue.objects.filter(status='ready').count()
            }
            
        except Exception as e:
            self.logger.error(f"驗證隊列完整性失敗: {str(e)}")
            return {'has_issues': True, 'issues': [f"驗證失敗: {str(e)}"]}
    
    def start_preparation(self, queue_item, barista_name=None):
        """開始製作"""
        try:
            if queue_item.status != 'waiting':
                self.logger.warning(f"訂單 {queue_item.order.id} 狀態為 {queue_item.status}，無法開始製作")
                return False
            
            queue_item.status = 'preparing'
            queue_item.actual_start_time = timezone.now()
            queue_item.barista = barista_name or '未分配'
            queue_item.save()
            
            # 重新計算後續隊列項的預計時間
            self.update_estimated_times()
            
            self.logger.info(f"訂單 {queue_item.order.id} 已開始製作")
            return True
            
        except Exception as e:
            self.logger.error(f"開始製作失敗: {str(e)}")
            return False
    
    def mark_as_ready(self, queue_item, staff_name=None):
        """標記為已就緒"""
        try:
            order = queue_item.order
            
            # 檢查訂單是否已經就緒
            if order.status == 'ready':
                self.logger.warning(f"訂單 {order.id} 已經是就緒狀態")
                return True
            
            # 先更新隊列項的時間
            queue_item.status = 'ready'
            queue_item.actual_completion_time = unified_time_service.get_hong_kong_time()
            
            # 如果沒有實際開始時間，設置一個
            if not queue_item.actual_start_time:
                queue_item.actual_start_time = unified_time_service.get_hong_kong_time() - timedelta(minutes=queue_item.preparation_time_minutes)
                self.logger.warning(f"訂單 {order.id} 沒有實際開始時間，已補設")
            
            queue_item.save()
            
            # 使用 OrderStatusManager
            result = OrderStatusManager.mark_as_ready_manually(
                order_id=order.id,
                staff_name=staff_name or "queue_manager"
            )
            
            if not result.get('success'):
                self.logger.error(f"使用 OrderStatusManager 標記為就緒失敗: {result.get('message')}")
                return False
            
            # 確保訂單的時間與隊列項同步
            order.refresh_from_db()
            
            # 如果訂單沒有就緒時間，使用隊列項的時間
            if not order.ready_at and queue_item.actual_completion_time:
                order.ready_at = queue_item.actual_completion_time
                order.save(update_fields=['ready_at'])
            
            # 如果訂單沒有預計就緒時間，設置一個
            if not order.estimated_ready_time and queue_item.actual_completion_time:
                order.estimated_ready_time = queue_item.actual_completion_time
                order.save(update_fields=['estimated_ready_time'])
            
            self.logger.info(f"✅ 訂單 {order.id} 已使用 OrderStatusManager 標記為就緒，完成時間: {queue_item.actual_completion_time}")
            
            # 重新計算隊列時間
            self.update_estimated_times()
            
            return True
            
        except Exception as e:
            self.logger.error(f"標記為就緒失敗: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            return False
    
    def sync_order_queue_status(self):
        """同步訂單狀態與隊列狀態"""
        try:
            self.logger.info("=== 開始同步訂單與隊列狀態 ===")
            
            from django.db import transaction
            
            with transaction.atomic():
                # 1. 查找所有已支付且狀態為 preparing 的訂單，但不在隊列中的
                preparing_orders = OrderModel.objects.filter(
                    payment_status="paid",
                    status='preparing'
                )
                
                for order in preparing_orders:
                    # 檢查訂單是否在隊列中
                    if not CoffeeQueue.objects.filter(order=order).exists():
                        self.logger.info(f"訂單 {order.id} 已支付且狀態為preparing，但不在隊列中，添加到隊列")
                        self.add_order_to_queue(order)
                
                # 2. 查找隊列中的訂單，更新訂單狀態
                waiting_queues = CoffeeQueue.objects.filter(status='waiting')
                for queue in waiting_queues:
                    order = queue.order
                    
                    if order.status != 'preparing' and order.payment_status == 'paid':
                        self.logger.info(f"更新隊列訂單 {order.id} 狀態為 preparing")
                        
                        preparation_minutes = queue.preparation_time_minutes or 5
                        
                        result = OrderStatusManager.mark_as_preparing_manually(
                            order_id=order.id,
                            barista_name="system_sync",
                            preparation_minutes=preparation_minutes
                        )
                        
                        if not result.get('success'):
                            self.logger.warning(f"同步訂單 {order.id} 狀態為 preparing 失敗: {result.get('message')}")
                
                # 3. 檢查製作中的訂單，確保隊列項狀態正確
                preparing_queues = CoffeeQueue.objects.filter(status='preparing')
                for queue in preparing_queues:
                    order = queue.order
                    if order.status != 'preparing':
                        self.logger.info(f"訂單 {order.id} 隊列狀態為preparing但訂單狀態為{order.status}，修正訂單狀態")
                        
                        result = OrderStatusManager.mark_as_preparing_manually(
                            order_id=order.id,
                            barista_name="system_sync",
                            preparation_minutes=queue.preparation_time_minutes or 5
                        )
            
            # 4. 更新隊列時間
            self.update_estimated_times()
            
            self.logger.info("=== 狀態同步完成 ===")
            return True
            
        except Exception as e:
            self.logger.error(f"狀態同步失敗: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            return False
    
    def recalculate_all_order_times(self):
        """
        🔄 統一重新計算所有訂單時間
        
        執行順序：
        1. 先重新排序隊列（確保優先級正確）
        2. 更新快速訂單的取貨時間（基於取貨選擇）
        3. 更新隊列預計時間（基於新順序）
        4. 檢查緊急訂單（標記需要立即處理的訂單）
        """
        try:
            self.logger.info("🔄 === 開始統一重新計算所有訂單時間 ===")
            
            # 1️⃣ 第一步：檢查並重新排序隊列
            self.logger.info("步驟1: 檢查隊列優先級排序...")
            needs_reorder = self._check_and_reorder_queue_by_priority()
            
            if needs_reorder:
                self.logger.info("✅ 隊列已重新排序，準備更新時間")
            else:
                self.logger.info("✅ 隊列順序正常，繼續時間計算")
            
            # 2️⃣ 第二步：更新快速訂單的取貨相關時間
            self.logger.info("步驟2: 更新快速訂單的取貨時間...")
            quick_orders_updated = 0
            
            quick_orders = OrderModel.objects.filter(
                order_type='quick', 
                payment_status='paid'
            ).exclude(status__in=['completed', 'cancelled'])
            
            for order in quick_orders:
                try:
                    if hasattr(order, 'pickup_time_choice') and order.pickup_time_choice:
                        time_info = unified_time_service.calculate_quick_order_times(order)
                        if time_info:
                            order.estimated_ready_time = time_info['estimated_pickup_time']
                            order.latest_start_time = time_info['latest_start_time']
                            order.save()
                            quick_orders_updated += 1
                            
                            self.logger.debug(f"快速訂單 #{order.id} 時間已更新: 取貨{order.pickup_time_choice}分鐘")
                except Exception as e:
                    self.logger.error(f"❌ 更新快速訂單 #{order.id} 時間失敗: {str(e)}")
                    continue
            
            self.logger.info(f"✅ 已更新 {quick_orders_updated} 個快速訂單的取貨時間")
            
            # 3️⃣ 第三步：更新隊列預計時間
            self.logger.info("步驟3: 更新隊列預計時間...")
            time_update_success = self.update_estimated_times()
            
            if time_update_success:
                self.logger.info("✅ 隊列預計時間更新成功")
            else:
                self.logger.warning("⚠️ 隊列預計時間更新可能不完整")
            
            # 4️⃣ 第四步：檢查緊急訂單
            self.logger.info("步驟4: 檢查緊急訂單...")
            urgent_orders_count = 0
            
            for order in quick_orders:
                try:
                    if hasattr(order, 'should_be_in_queue_by_now') and order.should_be_in_queue_by_now():
                        if hasattr(order, 'is_urgent'):
                            if not order.is_urgent:
                                order.is_urgent = True
                                order.save()
                                urgent_orders_count += 1
                                self.logger.info(f"⚠️ 訂單 #{order.id} 標記為緊急（超過最晚開始時間）")
                except Exception as e:
                    self.logger.error(f"❌ 檢查訂單 #{order.id} 緊急狀態失敗: {str(e)}")
                    continue
            
            self.logger.info(f"✅ 發現 {urgent_orders_count} 個緊急訂單需要立即處理")
            
            # 5️⃣ 第五步：驗證數據完整性
            self.logger.info("步驟5: 驗證隊列數據完整性...")
            integrity_check = self.verify_queue_integrity()
            
            if integrity_check['has_issues']:
                self.logger.warning(f"⚠️ 隊列完整性檢查發現問題: {len(integrity_check['issues'])} 個")
                for issue in integrity_check['issues']:
                    self.logger.warning(f"  - {issue}")
            else:
                self.logger.info("✅ 隊列數據完整性驗證通過")
            
            # 返回統計信息
            result = {
                'success': True,
                'message': '時間重新計算完成',
                'details': {
                    'queue_reordered': needs_reorder,
                    'quick_orders_updated': quick_orders_updated,
                    'urgent_orders_found': urgent_orders_count,
                    'total_quick_orders': quick_orders.count(),
                    'time_update_success': time_update_success,
                    'integrity_issues': len(integrity_check.get('issues', [])),
                    'timestamp': unified_time_service.get_hong_kong_time().isoformat()
                }
            }
            
            self.logger.info(f"✅ === 統一時間計算完成 ===")
            self.logger.info(f"📊 結果: {result}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ 統一重新計算訂單時間失敗: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            
            return {
                'success': False,
                'error': str(e),
                'message': '時間重新計算失敗，請檢查系統日誌'
            }
    
    # ==================== 靜態方法 ====================
    
    @staticmethod
    def get_preparation_time(coffee_count):
        """靜態方法：獲取製作時間"""
        return unified_time_service.calculate_preparation_time(coffee_count)
    
    @staticmethod
    def get_hong_kong_time_now():
        """靜態方法：獲取當前香港時間"""
        return unified_time_service.get_hong_kong_time()


# 輔助函數
def get_queue_updates():
    """獲取隊列更新數據"""
    try:
        queue_manager = CoffeeQueueManager()
        
        # 獲取隊列摘要
        queue_summary = queue_manager.get_queue_summary()
        
        # 獲取等待訂單
        waiting_queues = CoffeeQueue.objects.filter(status='waiting').order_by('position')
        waiting_orders = []
        
        for queue in waiting_queues:
            wait_time = queue_manager.calculate_wait_time(queue)
            waiting_orders.append({
                'id': queue.order.id,
                'order_id': queue.order.id,
                'position': queue.position,
                'pickup_code': queue.order.pickup_code,
                'coffee_names': '咖啡',
                'coffee_count': queue.coffee_count,
                'queue_wait_minutes': wait_time,
                'estimated_start_time': queue.estimated_start_time.isoformat() if queue.estimated_start_time else None,
                'estimated_completion_time': queue.estimated_completion_time.isoformat() if queue.estimated_completion_time else None,
            })
        
        # 獲取製作中訂單
        preparing_queues = CoffeeQueue.objects.filter(status='preparing').order_by('actual_start_time')
        preparing_orders = []
        
        for queue in preparing_queues:
            if queue.actual_start_time:
                current_time = unified_time_service.get_hong_kong_time()
                elapsed = current_time - queue.actual_start_time
                total_time = timedelta(minutes=queue.preparation_time_minutes)
                remaining = total_time - elapsed
                remaining_seconds = int(remaining.total_seconds())
                
                is_time_up = remaining_seconds <= 0
                
                if is_time_up:
                    remaining_seconds = 0
                    status_display = "已完成（等待確認）"
                else:
                    status_display = "製作中"
                    
            else:
                remaining_seconds = queue.preparation_time_minutes * 60
                is_time_up = False
                status_display = "製作中（未開始計時）"
                
            preparing_orders.append({
                'id': queue.order.id,
                'order_id': queue.order.id,
                'pickup_code': queue.order.pickup_code,
                'coffee_names': '咖啡',
                'coffee_count': queue.coffee_count,
                'started_at': queue.actual_start_time.strftime('%H:%M') if queue.actual_start_time else '--:--',
                'estimated_completion_time': queue.estimated_completion_time.strftime('%H:%M') if queue.estimated_completion_time else '--:--',
                'remaining_seconds': remaining_seconds,
                'is_time_up': is_time_up,
                'status_display': status_display,
                'requires_manual_confirmation': is_time_up,
            })
        
        # 獲取已就緒訂單
        ready_queues = CoffeeQueue.objects.filter(
            status='ready',
            actual_completion_time__gte=unified_time_service.get_hong_kong_time() - timedelta(minutes=15)
        ).order_by('-actual_completion_time')
        
        ready_orders = []
        
        for queue in ready_queues:
            if queue.actual_completion_time:
                wait_minutes = int((unified_time_service.get_hong_kong_time() - queue.actual_completion_time).total_seconds() / 60)
            else:
                wait_minutes = 0
                
            ready_orders.append({
                'id': queue.order.id,
                'order_id': queue.order.id,
                'pickup_code
