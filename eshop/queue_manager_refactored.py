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
from .models import CoffeeQueue, OrderModel
from .time_calculation import unified_time_service
from .order_status_manager import OrderStatusManager

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
