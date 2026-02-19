# eshop/queue_manager_refactored.py
"""
重構版的咖啡制作隊列管理器
主要改進：
1. 消除重複代碼：合併 add_order_to_queue 和 add_order_to_queue_with_priority
2. 統一錯誤處理：使用一致的錯誤處理模式
3. 提取共用邏輯：將重複邏輯提取為私有方法
4. 改進代碼結構：更好的方法組織和文檔
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
    """咖啡制作隊列管理器 - 重構版"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    # ==================== 核心隊列操作方法 ====================
    
    def add_order_to_queue(self, order, use_priority=True):
        """
        將訂單添加到隊列 - 統一方法，替代原有的兩個重複方法
        
        Args:
            order: OrderModel實例
            use_priority: 是否使用優先級排序（默認True）
        
        Returns:
            CoffeeQueue實例或None（如果失敗）
        """
        try:
            self.logger.info(f"開始將訂單 {order.id} 加入隊列")
            
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
            
            # 計算位置
            position = self._calculate_position(order, coffee_count, use_priority)
            
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
            
            self.logger.info(f"創建隊列項成功: {queue_item.id}, 位置: {position}")
            
            # 檢查並重新排序隊列
            if use_priority:
                self._check_and_reorder_queue()
            
            # 更新隊列時間
            self.update_estimated_times()
            
            return queue_item
            
        except Exception as e:
            self.logger.error(f"添加訂單到隊列失敗: {str(e)}")
            return None
    
    # ==================== 私有輔助方法 ====================
    
    def _calculate_coffee_count(self, order):
        """計算訂單中的咖啡杯數"""
        items = order.get_items()
        return sum(
            item.get('quantity', 1) 
            for item in items 
            if item.get('type') == 'coffee'
        )
    
    def _calculate_position(self, order, coffee_count, use_priority):
        """
        計算隊列位置
        
        Args:
            order: 訂單實例
            coffee_count: 咖啡杯數
            use_priority: 是否使用優先級
        
        Returns:
            隊列位置
        """
        if use_priority:
            return self._calculate_priority_position(order)
        else:
            return self._get_next_simple_position()
    
    def _get_next_simple_position(self):
        """獲取下一個簡單順序位置"""
        try:
            last_item = CoffeeQueue.objects.filter(status='waiting').order_by('-position').first()
            return last_item.position + 1 if last_item else 1
        except Exception as e:
            self.logger.error(f"獲取簡單位置失敗: {str(e)}")
            return 1
    
    def _calculate_priority_position(self, order):
        """
        計算優先級位置
        
        優先級規則：
        1. 所有快速訂單優先
        2. 快速訂單內部按創建時間排序
        3. 普通訂單按創建時間排序
        """
        try:
            waiting_queues = CoffeeQueue.objects.filter(status='waiting').order_by('position')
            
            if not waiting_queues.exists():
                return 1
            
            # 快速訂單處理
            if order.order_type == 'quick':
                for queue in waiting_queues:
                    if queue.order.order_type != 'quick':
                        return queue.position
                    if order.created_at < queue.order.created_at:
                        return queue.position
                return waiting_queues.last().position + 1
            
            # 普通訂單處理
            else:
                last_quick_position = 0
                for queue in waiting_queues:
                    if queue.order.order_type == 'quick':
                        last_quick_position = max(last_quick_position, queue.position)
                
                if last_quick_position == 0:
                    for queue in waiting_queues:
                        if order.created_at < queue.order.created_at:
                            return queue.position
                
                return last_quick_position + 1 if last_quick_position > 0 else len(waiting_queues) + 1
                
        except Exception as e:
            self.logger.error(f"計算優先級位置失敗: {str(e)}")
            return self._get_next_simple_position()
    
    def _check_and_reorder_queue(self):
        """檢查並重新排序隊列"""
        try:
            waiting_queues = CoffeeQueue.objects.filter(status='waiting')
            
            if not waiting_queues.exists():
                return False
            
            # 收集信息並排序
            queues_info = []
            for queue in waiting_queues:
                queues_info.append({
                    'queue_id': queue.id,
                    'order_id': queue.order.id,
                    'order_type': queue.order.order_type,
                    'current_position': queue.position,
                    'created_at': queue.order.created_at.timestamp(),
                })
            
            # 排序：快速訂單優先，然後按創建時間
            queues_info.sort(key=lambda x: (0 if x['order_type'] == 'quick' else 1, x['created_at']))
            
            # 檢查是否需要重新排序
            needs_reorder = any(
                info['current_position'] != index + 1
                for index, info in enumerate(queues_info)
            )
            
            if not needs_reorder:
                return False
            
            # 重新排序
            self.logger.info("重新排序隊列...")
            
            # 暫時清除位置
            for queue in waiting_queues:
                queue.position = 0
                queue.save()
            
            # 分配新位置
            for index, info in enumerate(queues_info, start=1):
                queue = CoffeeQueue.objects.get(id=info['queue_id'])
                queue.position = index
                queue.save()
            
            return True
            
        except Exception as e:
            self.logger.error(f"檢查隊列排序失敗: {str(e)}")
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
        """更新隊列預計時間"""
        try:
            current_time = unified_time_service.get_hong_kong_time()
            waiting_queues = CoffeeQueue.objects.filter(status='waiting').order_by('position')
            
            cumulative_time = timedelta(minutes=0)
            
            for queue in waiting_queues:
                estimated_start = current_time + cumulative_time
                queue.estimated_start_time = estimated_start
                
                prep_time = timedelta(minutes=queue.preparation_time_minutes)
                queue.estimated_completion_time = estimated_start + prep_time
                
                queue.save()
                cumulative_time += prep_time
            
            return True
            
        except Exception as e:
            self.logger.error(f"更新預計時間失敗: {str(e)}")
            return False
    
    def calculate_wait_time(self, queue_item):
        """計算等待時間"""
        try:
            if queue_item.status == 'preparing':
                return 0
            
            current_time = unified_time_service.get_hong_kong_time()
            
            if queue_item.estimated_start_time:
                wait_delta = queue_item.estimated_start_time - current_time
                return max(0, int(wait_delta.total_seconds() / 60))
            
            # 手動計算
            total_minutes = 0
            
            # 當前製作訂單的剩餘時間
            preparing_now = CoffeeQueue.objects.filter(status='preparing').first()
            if preparing_now and preparing_now.actual_start_time:
                elapsed = current_time - preparing_now.actual_start_time
                total_prep = timedelta(minutes=preparing_now.preparation_time_minutes)
                remaining = total_prep - elapsed
                if remaining > timedelta(0):
                    total_minutes += remaining.total_seconds() / 60
            
            # 前面等待訂單的時間
            waiting_before = CoffeeQueue.objects.filter(
                status='waiting',
                position__lt=queue_item.position
            )
            for waiting in waiting_before:
                total_minutes += waiting.preparation_time_minutes
            
            return int(total_minutes)
            
        except Exception as e:
            self.logger.error(f"計算等待時間失敗: {str(e)}")
            return 0
    
    def fix_queue_positions(self):
        """修復隊列位置"""
        try:
            # 重置ready訂單位置
            CoffeeQueue.objects.filter(status='ready').update(position=0)
            
            # 重新分配waiting訂單位置
            waiting_queues = CoffeeQueue.objects.filter(status='waiting').order_by('created_at')
            for index, queue in enumerate(waiting_queues, start=1):
                if queue.position != index:
                    queue.position = index
                    queue.save()
            
            self.update_estimated_times()
            return True
            
        except Exception as e:
            self.logger.error(f"修復隊列位置失敗: {str(e)}")
            return False
    
    def verify_queue_integrity(self):
        """驗證隊列完整性"""
        try:
            issues = []
            
            # 檢查ready訂單位置
            ready_with_position = CoffeeQueue.objects.filter(status='ready', position__gt=0)
            if ready_with_position.exists():
                issues.append(f"發現 {ready_with_position.count()} 個ready訂單有隊列位置")
            
            # 檢查waiting訂單連續性
            waiting_queues = CoffeeQueue.objects.filter(status='waiting').order_by('position')
            expected_pos = 1
            for queue in waiting_queues:
                if queue.position != expected_pos:
                    issues.append(f"訂單 #{queue.order.id} 位置不連續: {queue.position} (期望: {expected_pos})")
                expected_pos += 1
            
            # 檢查重複位置
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
                return False
            
            queue_item.status = 'preparing'
            queue_item.actual_start_time = timezone.now()
            queue_item.barista = barista_name or '未分配'
            queue_item.save()
            
            self.update_estimated_times()
            return True
            
        except Exception as e:
            self.logger.error(f"開始製作失敗: {str(e)}")
            return False
    
    def mark_as_ready(self, queue_item, staff_name=None):
        """標記為已就緒"""
        try:
            order = queue_item.order
            
            if order.status == 'ready':
                return True
            
            queue_item.status = 'ready'
            queue_item.actual_completion_time = unified_time_service.get_hong_kong_time()
            
            if not queue_item.actual_start_time:
                queue_item.actual_start_time = queue_item.actual_completion_time - timedelta(
                    minutes=queue_item.preparation_time_minutes
                )
            
            queue_item.save()
            
            # 使用OrderStatusManager
            result = OrderStatusManager.mark_as_ready_manually(
                order_id=order.id,
                staff_name=staff_name or "queue_manager"
            )
            
            if not result.get('success'):
                return False
            
            # 同步時間
            order.refresh_from_db()
            if not order.ready_at:
                order.ready_at = queue_item.actual_completion_time
                order.save(update_fields=['ready_at'])
            
            self.update_estimated_times()
            return True
            
        except Exception as e:
            self.logger.error(f"標記為就緒失敗: {str(e)}")
            return False
    
    def sync_order_queue_status(self):
        """同步訂單與隊列狀態"""
        try:
            from django.db import transaction
            
            with transaction.atomic():
                # 添加缺失的隊列項
                preparing_orders = OrderModel.objects.filter(
                    payment_status="paid",
                    status='preparing'
                )
                
                for order in preparing_orders:
                    if not CoffeeQueue.objects.filter(order=order).exists():
                        self.add_order_to_queue(order)
                
                # 同步狀態
                waiting_queues = CoffeeQueue.objects.filter(status='waiting')
                for queue in waiting_queues:
                    order = queue.order
                    if order.status != 'preparing' and order.payment_status == 'paid':
                        OrderStatusManager.mark_as_preparing_manually(
                            order_id=order.id,
                            barista_name="system_sync",
                            preparation_minutes=queue.preparation_time_minutes or 5
                        )
            
            self.update_estimated_times()
            return True
            
        except Exception as e:
            self.logger.error(f"同步狀態失敗: {str(e)}")
            return False
    
    # ==================== 靜態方法 ====================
    
    @staticmethod
    def get_preparation_time(coffee_count):
        """獲取製作時間"""
        return unified_time_service.calculate_preparation_time(coffee_count)
    
    @staticmethod
    def get_hong_kong_time_now():
        """獲取當前香港時間"""
        return unified_time_service.get_hong_kong_time()


# 簡化的輔助函數
def get_queue_updates():
    """獲取隊列更新數據"""
    try:
        manager = CoffeeQueueManager()
        
        return {
            'success': True,
            'queue_summary': manager.get_queue_summary(),
            'timestamp': unified_time_service.get_hong_kong_time().isoformat()
        }
        
    except Exception as e:
        logger.error(f"獲取隊列更新失敗: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'queue_summary': {'waiting': 0, 'preparing': 0, 'ready': 0, 'total': 0}
        }


def repair_queue_data():
    """修復隊列數據"""
    try:
        manager = CoffeeQueueManager()
        manager.fix_queue_positions()
        manager.sync_order_queue_status()
        return True
    except Exception as e:
        logger.error(f"修復隊列數據失敗: {str(e)}")
        return False