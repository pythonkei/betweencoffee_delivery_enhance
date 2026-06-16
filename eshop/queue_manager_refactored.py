# eshop/queue_manager_refactored.py
"""
隊列管理模塊 - 使用統一錯誤處理框架（遷移版本）

這個版本將隊列管理方法遷移到新的錯誤處理框架，提供：
1. 統一的錯誤處理
2. 標準化的響應格式
3. 詳細的錯誤日誌
4. 錯誤ID追蹤
5. 兼容性包裝器

注意：這個文件只包含遷移後的方法，其他部分保持不變
"""

import logging
import pytz
from django.utils import timezone
from datetime import timedelta
from .models import CoffeeQueue, OrderModel, Barista
from .time_calculation import unified_time_service
from .order_status_manager import OrderStatusManager
from .smart_allocation import (
    get_smart_allocator,
    get_workload_manager,
    get_time_calculator,
    initialize_smart_system,
    allocate_new_order,
    optimize_order_preparation,
    get_recommendations_for_order,
    update_barista_workload
)

from .error_handling import (
    handle_error,
    handle_success,
    handle_database_error,
    ErrorHandler
)

# 創建專門的隊列日誌器
queue_logger = logging.getLogger('eshop.queue_manager')

# 創建隊列錯誤處理器
queue_error_handler = ErrorHandler(module_name='queue_manager')


class CoffeeQueueManager:
    """咖啡制作隊列管理器 - 遷移版本"""
    
    def __init__(self):
        self.logger = queue_logger
    
    # ==================== 遷移的核心隊列操作方法 ====================
    
    def add_order_to_queue(self, order, use_priority=True):
        """
        將訂單添加到隊列 - 使用錯誤處理框架
        
        返回格式:
        {
            'success': True/False,
            'message': '操作消息',
            'data': {
                'queue_item_id': 0,
                'order_id': 0,
                'position': 0,
                'coffee_count': 0,
                'preparation_time_minutes': 0,
                'status': 'waiting',
                'queue_item': CoffeeQueue實例（通過兼容性包裝器訪問）
            },
            'details': {...},
            'timestamp': '...',
            'error_id': '...' (如果失敗)
        }
        """
        try:
            # 詳細的訂單進入隊列日誌
            self.logger.info(
                f"📝 訂單進入隊列檢查: 訂單 #{order.id}, "
                f"類型: {order.order_type}, "
                f"支付狀態: {order.payment_status}, "
                f"當前狀態: {order.status}"
            )
            
            # 檢查訂單是否已經在隊列中
            if CoffeeQueue.objects.filter(order=order).exists():
                existing_queue = CoffeeQueue.objects.get(order=order)
                self.logger.warning(
                    f"⚠️ 訂單 #{order.id} 已在隊列中: "
                    f"隊列項 #{existing_queue.id}, "
                    f"位置: {existing_queue.position}, "
                    f"狀態: {existing_queue.status}"
                )
                
                return handle_success(
                    operation='add_order_to_queue',
                    data={
                        'queue_item_id': existing_queue.id,
                        'order_id': order.id,
                        'position': existing_queue.position,
                        'coffee_count': existing_queue.coffee_count,
                        'preparation_time_minutes': existing_queue.preparation_time_minutes,
                        'status': existing_queue.status,
                        'queue_item': existing_queue,
                        'already_in_queue': True
                    },
                    message=f'訂單 #{order.id} 已在隊列中'
                )
            
            # 計算咖啡杯數
            coffee_count = self._calculate_coffee_count(order)
            self.logger.info(
                f"☕ 訂單 #{order.id} 咖啡杯數計算: {coffee_count} 杯"
            )
            
            if coffee_count == 0:
                self.logger.info(
                    f"⏭️ 訂單 #{order.id} 不包含咖啡，跳過加入隊列"
                )
                
                return handle_success(
                    operation='add_order_to_queue',
                    data={
                        'order_id': order.id,
                        'coffee_count': 0,
                        'skipped': True,
                        'reason': '訂單不包含咖啡'
                    },
                    message=f'訂單 #{order.id} 不包含咖啡，跳過加入隊列'
                )
            
            # 計算位置
            position = self._calculate_position(order, coffee_count, use_priority)
            self.logger.info(
                f"📍 訂單 #{order.id} 隊列位置計算: 位置 {position}, "
                f"優先級: {'啟用' if use_priority else '禁用'}"
            )
            
            # 計算製作時間
            preparation_time = unified_time_service.calculate_preparation_time(coffee_count)
            self.logger.info(
                f"⏱️ 訂單 #{order.id} 製作時間計算: {preparation_time} 分鐘"
            )
            
            # 創建隊列項
            queue_item = CoffeeQueue.objects.create(
                order=order,
                position=position,
                coffee_count=coffee_count,
                preparation_time_minutes=preparation_time,
                status='waiting'
            )
            
            self.logger.info(
                f"✅ 訂單 #{order.id} 成功進入隊列: "
                f"隊列項 #{queue_item.id}, "
                f"位置: {position}, "
                f"咖啡杯數: {coffee_count}, "
                f"製作時間: {preparation_time}分鐘, "
                f"狀態: waiting"
            )
            
            # 檢查並重新排序隊列
            if use_priority:
                reordered = self._check_and_reorder_queue()
                if reordered:
                    self.logger.info(
                        f"🔄 訂單 #{order.id} 隊列重新排序完成"
                    )
            
            # 更新隊列時間
            time_updated = self.update_estimated_times()
            if time_updated:
                self.logger.info(
                    f"⏰ 訂單 #{order.id} 隊列時間更新完成"
                )
            
            # 最終確認日誌
            self.logger.info(
                f"🎉 訂單 #{order.id} 隊列處理完成: "
                f"隊列項 #{queue_item.id}, "
                f"最終位置: {queue_item.position}, "
                f"狀態: {queue_item.status}"
            )
            
            return handle_success(
                operation='add_order_to_queue',
                data={
                    'queue_item_id': queue_item.id,
                    'order_id': order.id,
                    'position': queue_item.position,
                    'coffee_count': coffee_count,
                    'preparation_time_minutes': preparation_time,
                    'status': 'waiting',
                    'queue_item': queue_item,
                    'queue_reordered': reordered if use_priority else False,
                    'time_updated': time_updated
                },
                message=f'訂單 #{order.id} 成功加入隊列'
            )
            
        except Exception as e:
            return handle_database_error(
                error=e,
                operation='add_order_to_queue',
                query=f"添加訂單到隊列: 訂單 #{order.id if order else 'None'}",
                model='CoffeeQueue'
            )
    
    def add_order_to_queue_compatible(self, order, use_priority=True):
        """
        兼容性包裝器 - 返回原始格式的隊列項
        
        為了保持向後兼容性，這個方法返回原始的隊列項格式
        而不是錯誤處理框架的響應格式
        """
        result = self.add_order_to_queue(order, use_priority)
        
        if result.get('success'):
            return result['data']['queue_item']
        else:
            # 如果失敗，返回None
            self.logger.error(f"添加訂單到隊列失敗，返回None: {result.get('error_id', 'N/A')}")
            return None
    
    def start_preparation(self, queue_item, barista_name=None):
        """
        開始製作 - 使用錯誤處理框架
        
        返回格式:
        {
            'success': True/False,
            'message': '操作消息',
            'data': {
                'queue_item_id': 0,
                'order_id': 0,
                'old_status': 'waiting',
                'new_status': 'preparing',
                'old_position': 0,
                'new_position': 0,
                'barista': '名稱',
                'actual_start_time': datetime
            },
            'details': {...},
            'timestamp': '...',
            'error_id': '...' (如果失敗)
        }
        """
        try:
            # 狀態轉換日誌
            self.logger.info(
                f"🔄 訂單 #{queue_item.order.id} 狀態轉換檢查: "
                f"當前狀態: {queue_item.status}, "
                f"目標狀態: preparing"
            )
            
            if queue_item.status != 'waiting':
                self.logger.warning(
                    f"⚠️ 訂單 #{queue_item.order.id} 無法開始製作: "
                    f"當前狀態 {queue_item.status} 不是 waiting"
                )
                
                return handle_error(
                    error=Exception(f"訂單狀態不正確: {queue_item.status}"),
                    context='CoffeeQueueManager.start_preparation',
                    operation='start_preparation',
                    data={
                        'queue_item_id': queue_item.id,
                        'order_id': queue_item.order.id,
                        'current_status': queue_item.status,
                        'expected_status': 'waiting'
                    }
                )
            
            # 記錄狀態轉換前信息
            old_status = queue_item.status
            old_position = queue_item.position
            
            # 更新狀態
            queue_item.status = 'preparing'
            queue_item.actual_start_time = timezone.now()
            queue_item.barista = barista_name or '未分配'
            queue_item.save()
            
            # 狀態轉換成功日誌
            self.logger.info(
                f"👨‍🍳 訂單 #{queue_item.order.id} 開始製作: "
                f"狀態: {old_status} → preparing, "
                f"位置: {old_position} → 0, "
                f"咖啡師: {queue_item.barista}, "
                f"開始時間: {queue_item.actual_start_time}"
            )
            
            # 更新隊列時間
            time_updated = self.update_estimated_times()
            if time_updated:
                self.logger.info(
                    f"⏰ 訂單 #{queue_item.order.id} 隊列時間更新完成"
                )
            
            return handle_success(
                operation='start_preparation',
                data={
                    'queue_item_id': queue_item.id,
                    'order_id': queue_item.order.id,
                    'old_status': old_status,
                    'new_status': 'preparing',
                    'old_position': old_position,
                    'new_position': 0,
                    'barista': queue_item.barista,
                    'actual_start_time': queue_item.actual_start_time,
                    'time_updated': time_updated
                },
                message=f'訂單 #{queue_item.order.id} 開始製作'
            )
            
        except Exception as e:
            return handle_database_error(
                error=e,
                operation='start_preparation',
                query=f"開始製作隊列項: #{queue_item.id if queue_item else 'None'}",
                model='CoffeeQueue'
            )
    
    def start_preparation_compatible(self, queue_item, barista_name=None):
        """
        兼容性包裝器 - 返回原始格式的布爾值
        """
        result = self.start_preparation(queue_item, barista_name)
        
        if result.get('success'):
            return True
        else:
            # 如果失敗，返回False
            self.logger.error(f"開始製作失敗，返回False: {result.get('error_id', 'N/A')}")
            return False
    
    def mark_as_ready(self, queue_item, staff_name=None):
        """
        標記為已就緒 - 使用錯誤處理框架
        
        返回格式:
        {
            'success': True/False,
            'message': '操作消息',
            'data': {
                'queue_item_id': 0,
                'order_id': 0,
                'old_queue_status': 'preparing',
                'new_queue_status': 'ready',
                'old_order_status': 'preparing',
                'new_order_status': 'ready',
                'old_position': 0,
                'new_position': 0,
                'actual_completion_time': datetime,
                'ready_at': datetime
            },
            'details': {...},
            'timestamp': '...',
            'error_id': '...' (如果失敗)
        }
        """
        try:
            order = queue_item.order

            # 狀態轉換日誌
            self.logger.info(
                f"🔄 訂單 #{order.id} 狀態轉換檢查: "
                f"當前狀態: {order.status}, "
                f"隊列狀態: {queue_item.status}, "
                f"目標狀態: ready"
            )

            if order.status == 'ready':
                self.logger.info(
                    f"ℹ️ 訂單 #{order.id} 已經是就緒狀態，無需再次標記"
                )
                
                return handle_success(
                    operation='mark_as_ready',
                    data={
                        'queue_item_id': queue_item.id,
                        'order_id': order.id,
                        'already_ready': True,
                        'current_status': 'ready'
                    },
                    message=f'訂單 #{order.id} 已經是就緒狀態'
                )

            # 記錄狀態轉換前信息
            old_queue_status = queue_item.status
            old_order_status = order.status
            old_position = queue_item.position

            # 更新隊列項狀態 - 關鍵修復：清理隊列位置
            queue_item.status = 'ready'
            queue_item.position = 0  # ✅ 重要：清理隊列位置
            queue_item.actual_completion_time = unified_time_service.get_hong_kong_time()

            if not queue_item.actual_start_time:
                queue_item.actual_start_time = queue_item.actual_completion_time - timedelta(
                    minutes=queue_item.preparation_time_minutes
                )
                self.logger.info(
                    f"⏰ 訂單 #{order.id} 補設實際開始時間: {queue_item.actual_start_time}"
                )

            queue_item.save()

            self.logger.info(
                f"✅ 訂單 #{order.id} 隊列項標記為就緒: "
                f"隊列狀態: {old_queue_status} → ready, "
                f"位置: {old_position} → 0, "
                f"完成時間: {queue_item.actual_completion_time}"
            )
            
            # 使用OrderStatusManager更新訂單狀態
            result = OrderStatusManager.mark_as_ready_manually(
                order_id=order.id,
                staff_name=staff_name or "queue_manager"
            )
            
            if not result.get('success'):
                self.logger.error(
                    f"❌ 訂單 #{order.id} OrderStatusManager標記失敗: {result.get('message')}"
                )
                
                return handle_error(
                    error=Exception(f"OrderStatusManager標記失敗: {result.get('message')}"),
                    context='CoffeeQueueManager.mark_as_ready',
                    operation='mark_as_ready',
                    data={
                        'queue_item_id': queue_item.id,
                        'order_id': order.id,
                        'order_status_manager_result': result
                    }
                )
            
            self.logger.info(
                f"✅ 訂單 #{order.id} OrderStatusManager標記成功: "
                f"訂單狀態: {old_order_status} → ready"
            )
            
            # 同步時間
            order.refresh_from_db()
            if not order.ready_at:
                order.ready_at = queue_item.actual_completion_time
                order.save(update_fields=['ready_at'])
                self.logger.info(
                    f"⏰ 訂單 #{order.id} 同步就緒時間: {order.ready_at}"
                )
            
            # 更新隊列時間
            time_updated = self.update_estimated_times()
            if time_updated:
                self.logger.info(
                    f"⏰ 訂單 #{order.id} 隊列時間更新完成"
                )
            
            # 最終確認日誌
            self.logger.info(
                f"🎉 訂單 #{order.id} 標記為就緒完成: "
                f"隊列項 #{queue_item.id}, "
                f"訂單狀態: ready, "
                f"隊列狀態: ready, "
                f"完成時間: {queue_item.actual_completion_time}"
            )
            
            return handle_success(
                operation='mark_as_ready',
                data={
                    'queue_item_id': queue_item.id,
                    'order_id': order.id,
                    'old_queue_status': old_queue_status,
                    'new_queue_status': 'ready',
                    'old_order_status': old_order_status,
                    'new_order_status': 'ready',
                    'old_position': old_position,
                    'new_position': 0,
                    'actual_completion_time': queue_item.actual_completion_time,
                    'ready_at': order.ready_at,
                    'time_updated': time_updated,
                    'order_status_manager_success': True
                },
                message=f'訂單 #{order.id} 標記為就緒完成'
            )
            
        except Exception as e:
            return handle_database_error(
                error=e,
                operation='mark_as_ready',
                query=f"標記隊列項為就緒: #{queue_item.id if queue_item else 'None'}",
                model='CoffeeQueue'
            )
    
    def mark_as_ready_compatible(self, queue_item, staff_name=None):
        """
        兼容性包裝器 - 返回原始格式的布爾值
        """
        result = self.mark_as_ready(queue_item, staff_name)
        
        if result.get('success'):
            return True
        else:
            # 如果失敗，返回False
            self.logger.error(f"標記為就緒失敗，返回False: {result.get('error_id', 'N/A')}")
            return False
    
    # ==================== 私有輔助方法 ====================
    
    def _calculate_coffee_count(self, order):
        """計算訂單中的咖啡杯數"""
        try:
            items = order.get_items()
            coffee_count = sum(
                item.get('quantity', 1) 
                for item in items 
                if item.get('type') == 'coffee'
            )
            
            self.logger.debug(f"訂單 #{order.id} 咖啡杯數計算: {coffee_count} 杯")
            return coffee_count
            
        except Exception as e:
            self.logger.error(f"計算咖啡杯數失敗: {str(e)}")
            return 0
    
    def calculate_preparation_time(self, coffee_count):
        """
        計算製作時間 - 兼容性方法
        
        這個方法用於保持與原始代碼的兼容性
        實際調用 unified_time_service.calculate_preparation_time
        """
        try:
            preparation_minutes = unified_time_service.calculate_preparation_time(coffee_count)
            self.logger.debug(f"計算製作時間: {coffee_count} 杯 -> {preparation_minutes} 分鐘")
            return preparation_minutes
            
        except Exception as e:
            self.logger.error(f"計算製作時間失敗: {str(e)}")
            # 默認值：每杯咖啡5分鐘
            return max(5, coffee_count * 5)
    
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
        try:
            if use_priority:
                position = self._calculate_priority_position(order)
            else:
                position = self._get_next_simple_position()
            
            self.logger.debug(f"訂單 #{order.id} 位置計算: {position} (優先級: {use_priority})")
            return position
            
        except Exception as e:
            self.logger.error(f"計算位置失敗: {str(e)}")
            return 1
    
    def _get_next_simple_position(self):
        """獲取下一個簡單順序位置"""
        try:
            last_item = CoffeeQueue.objects.filter(status='waiting').order_by('-position').first()
            position = last_item.position + 1 if last_item else 1
            
            self.logger.debug(f"簡單順序位置計算: {position}")
            return position
            
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
                self.logger.debug(f"訂單 #{order.id} 優先級位置: 1 (隊列為空)")
                return 1
            
            # 快速訂單處理
            if order.order_type == 'quick':
                for queue in waiting_queues:
                    if queue.order.order_type != 'quick':
                        self.logger.debug(f"訂單 #{order.id} 優先級位置: {queue.position} (插入到普通訂單前)")
                        return queue.position
                    if order.created_at < queue.order.created_at:
                        self.logger.debug(f"訂單 #{order.id} 優先級位置: {queue.position} (插入到較晚的快速訂單前)")
                        return queue.position
                
                position = waiting_queues.last().position + 1
                self.logger.debug(f"訂單 #{order.id} 優先級位置: {position} (添加到隊列末尾)")
                return position
            
            # 普通訂單處理
            else:
                last_quick_position = 0
                for queue in waiting_queues:
                    if queue.order.order_type == 'quick':
                        last_quick_position = max(last_quick_position, queue.position)
                
                if last_quick_position == 0:
                    for queue in waiting_queues:
                        if order.created_at < queue.order.created_at:
                            self.logger.debug(f"訂單 #{order.id} 優先級位置: {queue.position} (插入到較晚的普通訂單前)")
                            return queue.position
                
                position = last_quick_position + 1 if last_quick_position > 0 else len(waiting_queues) + 1
                self.logger.debug(f"訂單 #{order.id} 優先級位置: {position} (添加到快速訂單後)")
                return position
                
        except Exception as e:
            self.logger.error(f"計算優先級位置失敗: {str(e)}")
            return self._get_next_simple_position()
    
    def _check_and_reorder_queue(self):
        """檢查並重新排序隊列"""
        try:
            waiting_queues = CoffeeQueue.objects.filter(status='waiting')
            
            if not waiting_queues.exists():
                self.logger.debug("隊列為空，無需重新排序")
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
                self.logger.debug("隊列順序正常，無需重新排序")
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
            
            self.logger.info(f"隊列重新排序完成，共 {len(queues_info)} 個訂單")
            return True
            
        except Exception as e:
            self.logger.error(f"檢查隊列排序失敗: {str(e)}")
            return False
    
    # ==================== 重要方法 ====================
    
    def recalculate_all_order_times(self):
        """
        統一重新計算所有訂單時間 - 使用錯誤處理框架
        
        返回格式:
        {
            'success': True/False,
            'message': '操作消息',
            'data': {
                'queue_reordered': True/False,
                'quick_orders_updated': 0,
                'urgent_orders_found': 0,
                'total_quick_orders': 0,
                'time_update_success': True/False,
                'integrity_issues': 0,
                'timestamp': '...'
            },
            'details': {...},
            'timestamp': '...',
            'error_id': '...' (如果失敗)
        }
        """
        try:
            self.logger.info("🔄 === 開始統一重新計算所有訂單時間 ===")
            
            # 1. 檢查並重新排序隊列
            needs_reorder = self._check_and_reorder_queue()
            
            if needs_reorder:
                self.logger.info("✅ 隊列已重新排序，準備更新時間")
            else:
                self.logger.info("✅ 隊列順序正常，繼續時間計算")
            
            # 2. 更新快速訂單的取貨時間
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
                except Exception as e:
                    self.logger.error(f"更新快速訂單 #{order.id} 時間失敗: {str(e)}")
                    continue
            
            self.logger.info(f"✅ 已更新 {quick_orders_updated} 個快速訂單的取貨時間")
            
            # 3. 更新隊列預計時間
            time_update_success = self.update_estimated_times()
            
            if time_update_success:
                self.logger.info("✅ 隊列預計時間更新成功")
            else:
                self.logger.warning("⚠️ 隊列預計時間更新可能不完整")
            
            # 4. 檢查緊急訂單
            urgent_orders_count = 0
            for order in quick_orders:
                try:
                    if hasattr(order, 'should_be_in_queue_by_now') and order.should_be_in_queue_by_now():
                        if hasattr(order, 'is_urgent'):
                            if not order.is_urgent:
                                order.is_urgent = True
                                order.save()
                                urgent_orders_count += 1
                except Exception as e:
                    self.logger.error(f"檢查訂單 #{order.id} 緊急狀態失敗: {str(e)}")
                    continue
            
            self.logger.info(f"✅ 發現 {urgent_orders_count} 個緊急訂單需要立即處理")
            
            # 5. 驗證數據完整性
            integrity_check_result = self.verify_queue_integrity()
            
            if integrity_check_result.get('success'):
                integrity_data = integrity_check_result['data']
                has_issues = integrity_data.get('has_issues', False)
                issues = integrity_data.get('issues', [])
                
                if has_issues:
                    self.logger.warning(f"⚠️ 隊列完整性檢查發現問題: {len(issues)} 個")
                else:
                    self.logger.info("✅ 隊列數據完整性驗證通過")
            else:
                self.logger.warning(f"⚠️ 隊列完整性檢查失敗: {integrity_check_result.get('message')}")
                has_issues = True
                issues = [f"完整性檢查失敗: {integrity_check_result.get('message')}"]
            
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
                    'integrity_issues': len(issues),
                    'timestamp': unified_time_service.get_hong_kong_time().isoformat()
                }
            }
            
            self.logger.info(f"✅ === 統一時間計算完成 ===")
            self.logger.info(f"📊 結果: {result}")
            
            return handle_success(
                operation='recalculate_all_order_times',
                data=result['details'],
                message='時間重新計算完成'
            )
            
        except Exception as e:
            self.logger.error(f"❌ 統一重新計算訂單時間失敗: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            
            return handle_database_error(
                error=e,
                operation='recalculate_all_order_times',
                query='重新計算所有訂單時間',
                model='OrderModel'
            )
    
    def recalculate_all_order_times_compatible(self):
        """
        兼容性包裝器 - 返回原始格式的字典
        """
        result = self.recalculate_all_order_times()
        
        if result.get('success'):
            return result['data']
        else:
            # 如果失敗，返回錯誤字典
            self.logger.error(f"重新計算時間失敗: {result.get('error_id', 'N/A')}")
            return {
                'success': False,
                'error': result.get('message', '未知錯誤'),
                'message': '時間重新計算失敗'
            }
    
    def update_estimated_times(self):
        """
        更新隊列預計時間 - 使用錯誤處理框架
        
        返回格式:
        {
            'success': True/False,
            'message': '操作消息',
            'data': {
                'waiting_orders_updated': 0,
                'current_time': '...',
                'total_preparation_minutes': 0,
                'timestamp': '...'
            },
            'details': {...},
            'timestamp': '...',
            'error_id': '...' (如果失敗)
        }
        """
        try:
            current_time = unified_time_service.get_hong_kong_time()
            waiting_queues = CoffeeQueue.objects.filter(status='waiting').order_by('position')
            
            cumulative_time = timedelta(minutes=0)
            waiting_orders_updated = 0
            total_preparation_minutes = 0
            
            for queue in waiting_queues:
                estimated_start = current_time + cumulative_time
                queue.estimated_start_time = estimated_start
                
                prep_time = timedelta(minutes=queue.preparation_time_minutes)
                queue.estimated_completion_time = estimated_start + prep_time
                
                queue.save()
                cumulative_time += prep_time
                waiting_orders_updated += 1
                total_preparation_minutes += queue.preparation_time_minutes
            
            self.logger.info(
                f"⏰ 更新隊列預計時間完成: "
                f"更新了 {waiting_orders_updated} 個等待訂單, "
                f"總製作時間: {total_preparation_minutes} 分鐘"
            )
            
            return handle_success(
                operation='update_estimated_times',
                data={
                    'waiting_orders_updated': waiting_orders_updated,
                    'current_time': current_time.isoformat(),
                    'total_preparation_minutes': total_preparation_minutes,
                    'timestamp': current_time.isoformat()
                },
                message=f'更新了 {waiting_orders_updated} 個訂單的預計時間'
            )
            
        except Exception as e:
            self.logger.error(f"❌ 更新預計時間失敗: {str(e)}")
            
            return handle_database_error(
                error=e,
                operation='update_estimated_times',
                query='更新隊列預計時間',
                model='CoffeeQueue'
            )
    
    def update_estimated_times_compatible(self):
        """
        兼容性包裝器 - 返回原始格式的布爾值
        """
        result = self.update_estimated_times()
        
        if result.get('success'):
            return True
        else:
            # 如果失敗，返回False
            self.logger.error(f"更新預計時間失敗: {result.get('error_id', 'N/A')}")
            return False
    
    def verify_queue_integrity(self):
        """
        驗證隊列完整性 - 使用錯誤處理框架
        
        返回格式:
        {
            'success': True/False,
            'message': '操作消息',
            'data': {
                'has_issues': True/False,
                'issues': [],
                'waiting_count': 0,
                'preparing_count': 0,
                'ready_count': 0,
                'total_count': 0,
                'timestamp': '...'
            },
            'details': {...},
            'timestamp': '...',
            'error_id': '...' (如果失敗)
        }
        """
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
            
            waiting_count = waiting_queues.count()
            preparing_count = CoffeeQueue.objects.filter(status='preparing').count()
            ready_count = CoffeeQueue.objects.filter(status='ready').count()
            total_count = waiting_count + preparing_count + ready_count
            
            has_issues = len(issues) > 0
            
            if has_issues:
                self.logger.warning(
                    f"⚠️ 隊列完整性檢查發現問題: {len(issues)} 個問題"
                )
                for issue in issues:
                    self.logger.warning(f"  - {issue}")
            else:
                self.logger.info(
                    f"✅ 隊列完整性檢查通過: "
                    f"等待中: {waiting_count}, "
                    f"製作中: {preparing_count}, "
                    f"已就緒: {ready_count}, "
                    f"總數: {total_count}"
                )
            
            return handle_success(
                operation='verify_queue_integrity',
                data={
                    'has_issues': has_issues,
                    'issues': issues,
                    'waiting_count': waiting_count,
                    'preparing_count': preparing_count,
                    'ready_count': ready_count,
                    'total_count': total_count,
                    'timestamp': unified_time_service.get_hong_kong_time().isoformat()
                },
                message=f'隊列完整性檢查完成，發現 {len(issues)} 個問題' if has_issues else '隊列完整性檢查通過'
            )
            
        except Exception as e:
            self.logger.error(f"❌ 驗證隊列完整性失敗: {str(e)}")
            
            return handle_database_error(
                error=e,
                operation='verify_queue_integrity',
                query='驗證隊列完整性',
                model='CoffeeQueue'
            )
    
    def verify_queue_integrity_compatible(self):
        """
        兼容性包裝器 - 返回原始格式的字典
        """
        result = self.verify_queue_integrity()
        
        if result.get('success'):
            return result['data']
        else:
            # 如果失敗，返回錯誤字典
            self.logger.error(f"驗證隊列完整性失敗: {result.get('error_id', 'N/A')}")
            return {
                'has_issues': True,
                'issues': [f"驗證失敗: {result.get('message', '未知錯誤')}"]
            }
    
    def sync_order_queue_status(self):
        """
        同步訂單與隊列狀態 - 使用錯誤處理框架
        
        返回格式:
        {
            'success': True/False,
            'message': '操作消息',
            'data': {
                'orders_checked': 0,
                'queue_items_added': 0,
                'status_synced': 0,
                'time_updated': True/False,
                'timestamp': '...'
            },
            'details': {...},
            'timestamp': '...',
            'error_id': '...' (如果失敗)
        }
        """
        try:
            from django.db import transaction
            
            orders_checked = 0
            queue_items_added = 0
            status_synced = 0
            
            with transaction.atomic():
                # 添加缺失的隊列項
                preparing_orders = OrderModel.objects.filter(
                    payment_status="paid",
                    status='preparing'
                )
                
                for order in preparing_orders:
                    orders_checked += 1
                    if not CoffeeQueue.objects.filter(order=order).exists():
                        result = self.add_order_to_queue(order)
                        if result.get('success'):
                            queue_items_added += 1
                
                # 同步狀態
                waiting_queues = CoffeeQueue.objects.filter(status='waiting')
                for queue in waiting_queues:
                    order = queue.order
                    if order.status != 'preparing' and order.payment_status == 'paid':
                        result = OrderStatusManager.mark_as_preparing_manually(
                            order_id=order.id,
                            barista_name="system_sync",
                            preparation_minutes=queue.preparation_time_minutes or 5
                        )
                        if result.get('success'):
                            status_synced += 1
            
            # 更新隊列時間
            time_update_result = self.update_estimated_times()
            time_updated = time_update_result.get('success', False)
            
            self.logger.info(
                f"🔄 同步訂單與隊列狀態完成: "
                f"檢查了 {orders_checked} 個訂單, "
                f"添加了 {queue_items_added} 個隊列項, "
                f"同步了 {status_synced} 個狀態, "
                f"時間更新: {'成功' if time_updated else '失敗'}"
            )
            
            return handle_success(
                operation='sync_order_queue_status',
                data={
                    'orders_checked': orders_checked,
                    'queue_items_added': queue_items_added,
                    'status_synced': status_synced,
                    'time_updated': time_updated,
                    'timestamp': unified_time_service.get_hong_kong_time().isoformat()
                },
                message=f'同步完成: 檢查 {orders_checked} 訂單, 添加 {queue_items_added} 隊列項, 同步 {status_synced} 狀態'
            )
            
        except Exception as e:
            self.logger.error(f"❌ 同步狀態失敗: {str(e)}")
            
            return handle_database_error(
                error=e,
                operation='sync_order_queue_status',
                query='同步訂單與隊列狀態',
                model='OrderModel'
            )
    
    def sync_order_queue_status_compatible(self):
        """
        兼容性包裝器 - 返回原始格式的布爾值
        """
        result = self.sync_order_queue_status()
        
        if result.get('success'):
            return True
        else:
            # 如果失敗，返回False
            self.logger.error(f"同步狀態失敗: {result.get('error_id', 'N/A')}")
            return False
    
    def fix_queue_positions(self):
        """
        修復隊列位置 - 使用錯誤處理框架
        
        返回格式:
        {
            'success': True/False,
            'message': '操作消息',
            'data': {
                'ready_positions_reset': 0,
                'waiting_positions_fixed': 0,
                'time_updated': True/False,
                'timestamp': '...'
            },
            'details': {...},
            'timestamp': '...',
            'error_id': '...' (如果失敗)
        }
        """
        try:
            # 重置ready訂單位置
            ready_positions_reset = CoffeeQueue.objects.filter(status='ready', position__gt=0).update(position=0)
            
            # 重新分配waiting訂單位置
            waiting_queues = CoffeeQueue.objects.filter(status='waiting').order_by('created_at')
            waiting_positions_fixed = 0
            
            for index, queue in enumerate(waiting_queues, start=1):
                if queue.position != index:
                    queue.position = index
                    queue.save()
                    waiting_positions_fixed += 1
            
            # 更新隊列時間
            time_update_result = self.update_estimated_times()
            time_updated = time_update_result.get('success', False)
            
            self.logger.info(
                f"🔧 修復隊列位置完成: "
                f"重置了 {ready_positions_reset} 個ready訂單位置, "
                f"修復了 {waiting_positions_fixed} 個waiting訂單位置, "
                f"時間更新: {'成功' if time_updated else '失敗'}"
            )
            
            return handle_success(
                operation='fix_queue_positions',
                data={
                    'ready_positions_reset': ready_positions_reset,
                    'waiting_positions_fixed': waiting_positions_fixed,
                    'time_updated': time_updated,
                    'timestamp': unified_time_service.get_hong_kong_time().isoformat()
                },
                message=f'修復完成: 重置 {ready_positions_reset} ready位置, 修復 {waiting_positions_fixed} waiting位置'
            )
            
        except Exception as e:
            self.logger.error(f"❌ 修復隊列位置失敗: {str(e)}")
            
            return handle_database_error(
                error=e,
                operation='fix_queue_positions',
                query='修復隊列位置',
                model='CoffeeQueue'
            )
    
    def fix_queue_positions_compatible(self):
        """
        兼容性包裝器 - 返回原始格式的布爾值
        """
        result = self.fix_queue_positions()
        
        if result.get('success'):
            return True
        else:
            # 如果失敗，返回False
            self.logger.error(f"修復隊列位置失敗: {result.get('error_id', 'N/A')}")
            return False
    
    # ==================== 智能分配方法 ====================
    
    def add_order_to_queue_with_smart_allocation(self, order, use_priority=True):
        """
        使用智能分配將訂單添加到隊列
        
        返回格式:
        {
            'success': True/False,
            'message': '操作消息',
            'data': {
                'queue_item_id': 0,
                'order_id': 0,
                'position': 0,
                'coffee_count': 0,
                'preparation_time_minutes': 0,
                'status': 'waiting',
                'queue_item': CoffeeQueue實例,
                'smart_allocation': {
                    'recommended_barista_id': 0,
                    'recommended_barista_name': '名稱',
                    'estimated_time': 0,
                    'allocation_strategy': '策略',
                    'optimization_suggestion': {...}
                }
            },
            'details': {...},
            'timestamp': '...',
            'error_id': '...' (如果失敗)
        }
        """
        try:
            self.logger.info(f"🤖 使用智能分配處理訂單 #{order.id}")
            
            # 1. 首先執行標準的隊列添加
            standard_result = self.add_order_to_queue(order, use_priority)
            
            if not standard_result.get('success'):
                return standard_result
            
            # 2. 執行智能分配
            allocation_result = allocate_new_order(order.id)
            
            # 3. 獲取優化建議
            optimization_result = optimize_order_preparation(order.id)
            
            # 4. 合併結果
            standard_data = standard_result['data']
            
            smart_data = {
                'queue_item_id': standard_data['queue_item_id'],
                'order_id': standard_data['order_id'],
                'position': standard_data['position'],
                'coffee_count': standard_data['coffee_count'],
                'preparation_time_minutes': standard_data['preparation_time_minutes'],
                'status': standard_data['status'],
                'queue_item': standard_data['queue_item'],
                'smart_allocation': {
                    'allocation_result': allocation_result,
                    'optimization_result': optimization_result
                }
            }
            
            # 如果有推薦的員工，更新隊列項
            if (allocation_result.get('success') and 
                allocation_result.get('recommended_barista_name')):
                
                queue_item = standard_data['queue_item']
                queue_item.barista = allocation_result['recommended_barista_name']
                queue_item.save()
                
                self.logger.info(
                    f"✅ 智能分配完成: 訂單 #{order.id} 分配給 {allocation_result['recommended_barista_name']}"
                )
            
            return handle_success(
                operation='add_order_to_queue_with_smart_allocation',
                data=smart_data,
                message=f'訂單 #{order.id} 已使用智能分配加入隊列'
            )
            
        except Exception as e:
            self.logger.error(f"智能分配失敗: {str(e)}")
            
            # 如果智能分配失敗，返回標準結果
            if 'standard_result' in locals():
                return standard_result
            else:
                return handle_database_error(
                    error=e,
                    operation='add_order_to_queue_with_smart_allocation',
                    query=f"智能分配訂單到隊列: 訂單 #{order.id if order else 'None'}",
                    model='CoffeeQueue'
                )
    
    def start_preparation_with_smart_assignment(self, queue_item, barista_name=None):
        """
        使用智能分配開始製作
        
        如果沒有指定咖啡師，使用智能分配推薦
        """
        try:
            self.logger.info(f"🤖 使用智能分配開始製作訂單 #{queue_item.order.id}")
            
            # 如果沒有指定咖啡師，嘗試智能分配
            if not barista_name:
                # 獲取智能建議
                recommendations = get_recommendations_for_order(queue_item.order.id)
                
                if recommendations.get('success') and recommendations.get('recommendations'):
                    # 查找分配建議
                    for rec in recommendations['recommendations']:
                        if rec['type'] == 'allocation' and rec.get('barista_name'):
                            barista_name = rec['barista_name']
                            self.logger.info(
                                f"✅ 智能分配建議: 使用 {barista_name}"
                            )
                            break
            
            # 執行標準的開始製作
            return self.start_preparation(queue_item, barista_name)
            
        except Exception as e:
            self.logger.error(f"智能分配開始製作失敗: {str(e)}")
            
            # 如果智能分配失敗，使用標準方法
            return self.start_preparation(queue_item, barista_name)
    
    def get_smart_recommendations(self, order_id):
        """
        獲取訂單的智能建議
        
        返回格式:
        {
            'success': True/False,
            'message': '操作消息',
            'data': {
                'order_id': 0,
                'recommendations': [...],
                'system_status': {...},
                'optimization_suggestions': {...}
            },
            'details': {...},
            'timestamp': '...',
            'error_id': '...' (如果失敗)
        }
        """
        try:
            from .models import OrderModel
            
            order = OrderModel.objects.get(id=order_id)
            
            # 獲取智能建議
            recommendations_result = get_recommendations_for_order(order_id)
            
            # 獲取系統狀態
            allocator = get_smart_allocator()
            system_status = allocator.get_system_status()
            
            # 獲取優化建議
            optimization_result = optimize_order_preparation(order_id)
            
            data = {
                'order_id': order_id,
                'recommendations': recommendations_result.get('recommendations', []),
                'system_status': system_status,
                'optimization_suggestions': optimization_result.get('optimization', {}),
                'total_recommendations': recommendations_result.get('total_recommendations', 0)
            }
            
            return handle_success(
                operation='get_smart_recommendations',
                data=data,
                message=f'訂單 #{order_id} 的智能建議已生成'
            )
            
        except OrderModel.DoesNotExist:
            return handle_error(
                error=Exception(f"訂單 #{order_id} 不存在"),
                context='CoffeeQueueManager.get_smart_recommendations',
                operation='get_smart_recommendations',
                data={'order_id': order_id}
            )
        except Exception as e:
            self.logger.error(f"獲取智能建議失敗: {str(e)}")
            
            return handle_database_error(
                error=e,
                operation='get_smart_recommendations',
                query=f"獲取訂單 #{order_id} 的智能建議",
                model='OrderModel'
            )
    
    def get_barista_workload_overview(self):
        """
        獲取員工工作負載概覽
        
        返回格式:
        {
            'success': True/False,
            'message': '操作消息',
            'data': {
                'total_baristas': 0,
                'active_baristas': 0,
                'total_capacity': 0,
                'current_load': 0,
                'available_capacity': 0,
                'utilization_rate': 0,
                'barista_details': [...]
            },
            'details': {...},
            'timestamp': '...',
            'error_id': '...' (如果失敗)
        }
        """
        try:
            # 初始化智能系統（如果尚未初始化）
            initialize_smart_system()
            
            # 獲取系統狀態
            allocator = get_smart_allocator()
            system_status = allocator.get_system_status()
            
            return handle_success(
                operation='get_barista_workload_overview',
                data=system_status,
                message='員工工作負載概覽已生成'
            )
            
        except Exception as e:
            self.logger.error(f"獲取工作負載概覽失敗: {str(e)}")
            
            return handle_database_error(
                error=e,
                operation='get_barista_workload_overview',
                query='獲取員工工作負載概覽',
                model='Barista'
            )
    
    def optimize_queue_with_smart_allocation(self):
        """
        使用智能分配優化整個隊列
        
        返回格式:
        {
            'success': True/False,
            'message': '操作消息',
            'data': {
                'orders_optimized': 0,
                'time_savings': 0,
                'load_balanced': True/False,
                'recommendations_generated': 0,
                'system_status_before': {...},
                'system_status_after': {...}
            },
            'details': {...},
            'timestamp': '...',
            'error_id': '...' (如果失敗)
        }
        """
        try:
            self.logger.info("🤖 開始智能隊列優化...")
            
            # 獲取優化前的系統狀態
            allocator = get_smart_allocator()
            system_status_before = allocator.get_system_status()
            
            # 獲取所有等待中的訂單
            waiting_queues = CoffeeQueue.objects.filter(status='waiting')
            orders_optimized = 0
            total_time_savings = 0
            
            # 為每個訂單生成優化建議
            recommendations_generated = 0
            
            for queue in waiting_queues:
                try:
                    # 獲取優化建議
                    optimization_result = optimize_order_preparation(queue.order.id)
                    
                    if optimization_result.get('success'):
                        recommendations_generated += 1
                        
                        # 計算時間節省
                        optimization = optimization_result.get('optimization', {})
                        time_saving = optimization.get('time_saving', 0)
                        total_time_savings += time_saving
                        
                        if time_saving > 0:
                            orders_optimized += 1
                            
                except Exception as e:
                    self.logger.error(f"優化訂單 #{queue.order.id} 失敗: {str(e)}")
                    continue
            
            # 獲取優化後的系統狀態
            system_status_after = allocator.get_system_status()
            
            # 檢查負載是否均衡
            load_balanced = True
            barista_details = system_status_after.get('barista_details', [])
            
            if len(barista_details) >= 2:
                # 檢查兩個員工的負載差異
                load_diff = abs(barista_details[0]['current_load'] - barista_details[1]['current_load'])
                load_balanced = load_diff <= 2  # 負載差異不超過2杯
            
            data = {
                'orders_optimized': orders_optimized,
                'time_savings': round(total_time_savings, 1),
                'load_balanced': load_balanced,
                'recommendations_generated': recommendations_generated,
                'system_status_before': system_status_before,
                'system_status_after': system_status_after,
                'total_waiting_orders': waiting_queues.count()
            }
            
            self.logger.info(
                f"✅ 智能隊列優化完成: "
                f"優化了 {orders_optimized} 個訂單, "
                f"節省 {total_time_savings:.1f} 分鐘, "
                f"負載均衡: {'是' if load_balanced else '否'}"
            )
            
            return handle_success(
                operation='optimize_queue_with_smart_allocation',
                data=data,
                message=f'隊列優化完成: 優化 {orders_optimized} 訂單, 節省 {total_time_savings:.1f} 分鐘'
            )
            
        except Exception as e:
            self.logger.error(f"智能隊列優化失敗: {str(e)}")
            
            return handle_database_error(
                error=e,
                operation='optimize_queue_with_smart_allocation',
                query='智能優化隊列',
                model='CoffeeQueue'
            )


# ==================== 輔助函數 ====================

def force_sync_queue_and_orders():
    """
    强制同步队列状态和订单状态 - 兼容性函數
    
    這個函數用於保持與原始 queue_manager.py 的兼容性
    它調用遷移後的隊列管理器來執行同步操作
    """
    try:
        queue_logger.info("=== 开始强制同步队列与订单状态 ===")
        
        # 創建隊列管理器實例
        manager = CoffeeQueueManager()
        
        # 執行同步操作
        sync_result = manager.sync_order_queue_status()
        
        if sync_result.get('success'):
            queue_logger.info("✅ 强制同步完成")
            return True
        else:
            queue_logger.error(f"❌ 强制同步失败: {sync_result.get('message')}")
            return False
            
    except Exception as e:
        queue_logger.error(f"❌ 强制同步失败: {str(e)}")
        return False


def repair_queue_data():
    """
    修復隊列數據 - 兼容性函數
    
    這個函數用於保持與原始 queue_manager.py 的兼容性
    它調用遷移後的隊列管理器來執行修復操作
    """
    try:
        # 創建隊列管理器實例
        manager = CoffeeQueueManager()
        
        # 執行修復操作
        fix_result = manager.fix_queue_positions()
        sync_result = manager.sync_order_queue_status()
        
        if fix_result.get('success') and sync_result.get('success'):
            return True
        else:
            return False
            
    except Exception as e:
        queue_logger.error(f"修復隊列數據失敗: {str(e)}")
        return False


def get_hong_kong_time_now():
    """
    獲取當前香港時間 - 兼容性函數
    
    這個函數用於保持與原始 queue_manager.py 的兼容性
    """
    from .time_calculation import unified_time_service
    return unified_time_service.get_hong_kong_time()


def sync_ready_orders_timing():
    """
    同步已就緒訂單的時間 - 兼容性函數
    
    這個函數用於保持與原始 queue_manager.py 的兼容性
    """
    try:
        queue_logger.info("同步已就緒訂單的時間...")
        
        # 獲取所有已就緒訂單
        ready_orders = OrderModel.objects.filter(
            status='ready',
            payment_status="paid"
        )
        
        for order in ready_orders:
            # 檢查對應的隊列項
            try:
                queue_item = CoffeeQueue.objects.get(order=order)
                # 如果隊列項有完成時間，同步到訂單
                if queue_item.actual_completion_time and not order.ready_at:
                    order.ready_at = queue_item.actual_completion_time
                    order.save()
            except CoffeeQueue.DoesNotExist:
                # 如果沒有隊列項，但訂單是就緒狀態，設置默認時間
                if not order.ready_at and order.updated_at:
                    order.ready_at = order.updated_at
                    order.save()
        
        queue_logger.info("已就緒訂單時間同步完成")
        return True
    except Exception as e:
        queue_logger.error(f"同步已就緒訂單時間失敗: {str(e)}")
        return False
