# eshop/order_status_manager_refactored.py
"""
處理所有訂單狀態相關的顯示邏輯 - 使用統一的錯誤處理框架

這個版本使用新的錯誤處理框架，提供：
1. 統一的錯誤處理
2. 標準化的響應格式
3. 詳細的錯誤日誌
4. 錯誤ID追蹤
"""

import logging
from django.utils import timezone

from .models import OrderModel, CoffeeQueue
from .time_calculation import unified_time_service
from .error_handling import (
    handle_error,
    handle_success,
    error_handler_decorator,
    handle_database_error,
    ErrorHandler
)

logger = logging.getLogger(__name__)

# 創建訂單狀態管理器的錯誤處理器
order_error_handler = ErrorHandler(module_name='order_status_manager')


class OrderStatusManager:
    """統一的訂單狀態管理器 - 使用錯誤處理框架"""
    
    def __init__(self, order):
        self.order = order
        self.items = order.get_items()
        self.error_handler = ErrorHandler(module_name='OrderStatusManager')
    

    @classmethod
    def process_payment_success(cls, order_id, request=None):
        """處理支付成功後的統一邏輯（含購物車清空）- 使用錯誤處理框架"""
        try:
            logger.info(f"🔄 開始處理訂單 #{order_id} 支付成功")
            
            order = OrderModel.objects.get(id=order_id)
            manager = cls(order)
            
            # ✅ 修復：更新支付狀態為 'paid'
            if order.payment_status != 'paid':
                order.payment_status = 'paid'
                logger.info(f"✅ 訂單 #{order_id} 支付狀態更新為 paid")
            
            # ✅ 修復：確保訂單狀態正確
            if order.status == 'pending':
                # 分析訂單類型
                order_type = manager.analyze_order_type()
                if order_type['is_beans_only']:
                    order.status = 'ready'
                    logger.info(f"✅ 純咖啡豆訂單 #{order_id} 狀態更新為 ready")
                else:
                    order.status = 'waiting'
                    logger.info(f"✅ 訂單 #{order_id} 狀態更新為 waiting")
            
            # ✅ 修復：保存所有更新
            order.save()
            logger.info(f"✅ 訂單 #{order_id} 保存成功: status={order.status}, payment_status={order.payment_status}")
            
            # ✅ 修改：加入隊列邏輯
            queue_item = None
            if manager.should_add_to_queue():
                logger.info(f"✅ 訂單 #{order_id} 需要加入隊列")
                
                # 如果是快速訂單，計算相關時間
                if order.order_type == 'quick':
                    order.calculate_times_based_on_pickup_choice()
                    order.save()
                    logger.info(f"快速訂單 #{order.id} 已計算取貨時間")
                
                # 將訂單加入隊列
                from .queue_manager_refactored import CoffeeQueueManager
                queue_manager = CoffeeQueueManager()
                queue_item = queue_manager.add_order_to_queue(order)
                
                if queue_item:
                    logger.info(f"訂單 {order.id} 已加入製作隊列，位置: {queue_item.position}")
                else:
                    logger.error(f"訂單 {order.id} 加入隊列失敗")
            else:
                logger.info(f"ℹ️ 訂單 #{order_id} 不需要加入隊列")
            
            # ✅ 修改：重新計算所有訂單時間
            logger.info(f"🔄 訂單 #{order_id} 支付成功，開始統一時間計算...")
            from .queue_manager_refactored import CoffeeQueueManager
            queue_manager = CoffeeQueueManager()
            time_result = queue_manager.recalculate_all_order_times_compatible()
            
            # ✅ 修改：如果有request，清空購物車
            if request:
                cls.clear_user_cart_and_session(request)
            
            # ✅ 修改：發送WebSocket通知
            try:
                from .websocket_utils import send_payment_update
                send_payment_update(
                    order_id=order_id,
                    payment_status='paid',
                    data={
                        'payment_method': order.payment_method,
                        'message': '支付成功，訂單已加入隊列'
                    }
                )
            except Exception as ws_error:
                logger.error(f"發送WebSocket通知失敗: {str(ws_error)}")
            
            logger.info(f"✅ 訂單 {order_id} 支付成功處理完成")
            
            # 使用錯誤處理框架返回成功響應
            return handle_success(
                operation='process_payment_success',
                data={
                    'order_id': order_id,
                    'order': order,
                    'queue_item': queue_item,
                    'time_recalculated': time_result.get('success', False)
                },
                message='支付成功處理完成'
            )
            
        except OrderModel.DoesNotExist as e:
            return handle_database_error(
                error=e,
                operation='process_payment_success',
                query=f"SELECT * FROM eshop_ordermodel WHERE id = {order_id}",
                model='OrderModel'
            )
        except Exception as e:
            return handle_error(
                error=e,
                context='OrderStatusManager.process_payment_success',
                operation='process_payment_success',
                data={'order_id': order_id, 'request_provided': request is not None}
            )


    @staticmethod
    def clear_user_cart_and_session(request):
        """清空用戶的購物車和session - 使用錯誤處理框架"""
        try:
            from cart.cart import Cart
            
            # 1. 清空購物車對象
            cart = Cart(request)
            cart.clear()
            
            # 2. 清除相關session數據
            session_keys_to_clear = [
                'pending_order',
                'guest_cart',
                'quick_order_data',
                'cart'
            ]
            
            cleared_keys = []
            for key in session_keys_to_clear:
                if key in request.session:
                    del request.session[key]
                    cleared_keys.append(key)
            
            request.session.modified = True
            
            logger.info(f"✅ 購物車和session已清除: {cleared_keys}")
            
            return handle_success(
                operation='clear_user_cart_and_session',
                data={'cleared_keys': cleared_keys},
                message='購物車和session已清除'
            )
            
        except Exception as e:
            return handle_error(
                error=e,
                context='OrderStatusManager.clear_user_cart_and_session',
                operation='clear_user_cart_and_session',
                data={'session_keys': session_keys_to_clear}
            )


    # 業務邏輯 : 處理訂單狀態變化的統一方法
    @classmethod
    def process_order_status_change(cls, order_id, new_status, staff_name=None):
        """處理訂單狀態變化的統一邏輯 - 使用錯誤處理框架"""
        try:
            logger.info(f"🔄 處理訂單 #{order_id} 狀態變化: {new_status}")
            
            order = OrderModel.objects.get(id=order_id)
            old_status = order.status
            
            # 更新訂單狀態
            order.status = new_status
            
            # 根據狀態設置時間戳
            now = timezone.now()
            if new_status == 'preparing':
                order.preparation_started_at = now
            elif new_status == 'ready':
                order.ready_at = now
            elif new_status == 'completed':
                order.picked_up_at = now
            
            order.save()
            logger.info(f"✅ 訂單 #{order_id} 狀態已更新: {old_status} → {new_status}")
            
            # ✅ 重要：清理隊列位置（當訂單狀態變為 ready 或 completed 時）
            if new_status in ['ready', 'completed']:
                queue_item = CoffeeQueue.objects.filter(order=order).first()
                if queue_item and queue_item.position > 0:
                    old_position = queue_item.position
                    queue_item.position = 0
                    queue_item.save()
                    logger.info(
                        f"✅ 訂單 #{order_id} 隊列位置已清理: "
                        f"位置 {old_position} → 0 (狀態: {new_status})"
                    )
            
            # ✅ 重要：觸發統一時間計算
            from .queue_manager_refactored import CoffeeQueueManager
            queue_manager = CoffeeQueueManager()
            
            logger.info(f"🔄 訂單狀態變化，開始統一時間計算...")
            time_result = queue_manager.recalculate_all_order_times_compatible()
            
            if time_result.get('success'):
                logger.info(f"✅ 訂單狀態變化後時間計算完成")
            else:
                logger.warning(f"⚠️ 訂單狀態變化後時間計算有問題: {time_result.get('error')}")
            
            # 發送WebSocket通知
            try:
                from .websocket_utils import send_order_update
                send_order_update(
                    order_id=order_id,
                    update_type='status_change',
                    data={
                        'status': new_status,
                        'message': f"訂單狀態已更新為 {new_status}"
                    }
                )
            except Exception as ws_error:
                logger.error(f"發送WebSocket通知失敗: {str(ws_error)}")
            
            return handle_success(
                operation='process_order_status_change',
                data={
                    'order_id': order_id,
                    'old_status': old_status,
                    'new_status': new_status,
                    'time_recalculated': True,
                    'staff_name': staff_name
                },
                message=f'訂單狀態已更新為 {new_status}'
            )
            
        except OrderModel.DoesNotExist as e:
            return handle_database_error(
                error=e,
                operation='process_order_status_change',
                query=f"SELECT * FROM eshop_ordermodel WHERE id = {order_id}",
                model='OrderModel'
            )
        except Exception as e:
            return handle_error(
                error=e,
                context='OrderStatusManager.process_order_status_change',
                operation='process_order_status_change',
                data={'order_id': order_id, 'new_status': new_status, 'staff_name': staff_name}
            )


    # ✅ 新增：批量處理多個訂單狀態變化
    @classmethod
    def process_batch_status_changes(cls, order_status_list):
        """批量處理多個訂單狀態變化 - 使用錯誤處理框架"""
        try:
            logger.info(f"🔄 批量處理 {len(order_status_list)} 個訂單狀態變化")
            
            results = []
            for order_id, new_status in order_status_list:
                result = cls.process_order_status_change(order_id, new_status)
                results.append(result)
            
            # 批量處理後統一計算時間（只計算一次）
            logger.info(f"🔄 批量處理完成，開始統一時間計算...")
            from .queue_manager_refactored import CoffeeQueueManager
            queue_manager = CoffeeQueueManager()
            
            time_result = queue_manager.recalculate_all_order_times_compatible()
            
            logger.info(f"✅ 批量處理完成，統一時間計算結果: {time_result.get('success')}")
            
            return handle_success(
                operation='process_batch_status_changes',
                data={
                    'results': results,
                    'time_recalculated': True,
                    'total_orders': len(order_status_list)
                },
                message=f'批量處理 {len(order_status_list)} 個訂單完成'
            )
            
        except Exception as e:
            return handle_error(
                error=e,
                context='OrderStatusManager.process_batch_status_changes',
                operation='process_batch_status_changes',
                data={'order_status_list': order_status_list}
            )


    def get_display_status(self):
        """獲取訂單顯示狀態 - 使用錯誤處理框架"""
        try:
            order_type = self.analyze_order_type()
            
            # 基礎狀態 - 修復：使用 payment_status 而不是 is_paid
            status_info = {
                'order': self.order,
                'items': self.order.get_items_with_chinese_options(),
                'payment_status': 'paid' if self.order.payment_status == 'paid' else 'pending',
                **order_type
            }
            
            # 根據訂單類型添加特定信息
            if order_type['is_beans_only']:
                # 純咖啡豆訂單：直接完成
                status_info.update(self._get_beans_only_status())
            else:
                # 咖啡訂單或混合訂單：需要製作
                status_info.update(self._get_coffee_order_status())
            
            # ====== 添加取貨時間信息（如果適用） ======
            # 添加取貨時間選擇顯示
            if hasattr(self.order, 'pickup_time_choice') and self.order.pickup_time_choice:
                choice_map = {
                    '5': '5分鐘後',
                    '10': '10分鐘後', 
                    '15': '15分鐘後',
                    '20': '20分鐘後',
                    '30': '30分鐘後',
                }
                status_info['pickup_time_display'] = choice_map.get(
                    self.order.pickup_time_choice, '5分鐘後'
                )
                
                # 添加最晚開始時間（如果已計算）
                if hasattr(self.order, 'latest_start_time') and self.order.latest_start_time:
                    status_info['latest_start_time'] = unified_time_service.format_time_for_display(
                        self.order.latest_start_time, 'full'
                    )
                    status_info['is_urgent'] = self.order.should_be_in_queue_by_now() if hasattr(self.order, 'should_be_in_queue_by_now') else False
            
            return status_info
            
        except Exception as e:
            # 使用錯誤處理框架處理錯誤，但返回部分信息
            error_response = handle_error(
                error=e,
                context='OrderStatusManager.get_display_status',
                operation='get_display_status',
                data={'order_id': self.order.id},
                log_level='warning'
            )
            
            # 返回基本的狀態信息
            return {
                'order': self.order,
                'items': [],
                'payment_status': 'error',
                'has_coffee': False,
                'has_beans': False,
                'is_mixed_order': False,
                'is_beans_only': False,
                'is_coffee_only': False,
                'error': error_response
            }


    def _get_beans_only_status(self):
        """獲取純咖啡豆訂單狀態"""
        # 純咖啡豆訂單，支付後直接設置為就緒 - 修復：使用 payment_status
        if self.order.payment_status == 'paid' and self.order.status in ['pending', 'waiting', 'preparing']:
            self.order.status = 'ready'
            self.order.save()
            logger.info(f"純咖啡豆訂單 {self.order.id} 自動設置為就緒狀態")
        
        return {
            'progress_percentage': 100,
            'progress_display': '100% 完成',
            'show_progress_bar': False,
            'queue_info': None,
            'remaining_minutes': 0,
            'estimated_time': '隨時可取',
            'is_ready': True,
            'status_message': '您的咖啡豆已準備就緒，隨時可以提取！'
        }


    def _get_coffee_order_status(self):
        """獲取咖啡訂單狀態（包含混合訂單）"""
        # 獲取隊列信息
        queue_info = self._get_queue_info()
        
        # 計算進度
        progress_info = self._calculate_progress()
        
        # 確定是否就緒
        is_ready = self.order.status in ['ready', 'completed']
        
        # 獲取隊列顯示文本
        queue_display, queue_message, remaining_display = self._get_queue_display_text(queue_info)
        
        # 格式化預計時間（香港時區）
        estimated_time_display = unified_time_service.format_time_for_display(
            self.order.estimated_ready_time, 'full'
        ) if self.order.estimated_ready_time else '計算中...'
        
        # 獲取訂單狀態消息
        status_message = self._get_status_message(is_ready)
        
        # 構建狀態信息 - 修復：使用 payment_status
        status_info = {
            'queue_info': queue_info,
            'progress_percentage': progress_info['percentage'],
            'progress_display': progress_info['display'],
            'show_progress_bar': self.order.payment_status == 'paid' and not self.analyze_order_type()['is_beans_only'],
            'remaining_minutes': self._get_remaining_minutes(),
            'estimated_time': estimated_time_display,
            'is_ready': is_ready,
            
            # ✅ 確保模板需要的字段都存在
            'queue_display': queue_display,
            'queue_message': queue_message,
            'remaining_display': remaining_display,
            'status_message': status_message,
        }
        
        return status_info


    def _get_status_message(self, is_ready):
        """獲取狀態消息"""
        if is_ready:
            order_type = self.analyze_order_type()
            if order_type['is_mixed_order']:
                return '您訂購的商品已準備就緒，隨時可以提取！'
            else:
                return '您的咖啡已準備就緒，隨時可以提取！'
        else:
            return '您的訂單正在製作中，請耐心等候...'
    

    def _get_queue_display_text(self, queue_info):
        """生成隊列顯示文本"""
        if not queue_info:
            return '等待加入隊列...', '系統正在處理您的訂單', ''
        
        queue_position = queue_info['queue_position']
        wait_minutes = queue_info['queue_wait_minutes']
        total_minutes = queue_info['total_minutes']
        
        # 隊列狀態文本
        queue_display = f"隊列位置: #{queue_position} | 預計等待: {wait_minutes}分鐘"
        
        # 隊列消息
        if queue_position == 1:
            queue_message = '下一個就輪到您了！'
        elif queue_position <= 3:
            queue_message = f'前面還有 {queue_position - 1} 個訂單'
        else:
            queue_message = '目前訂單較多，請耐心等候'
        
        # 剩餘時間顯示
        remaining_display = f"(約{total_minutes}分鐘後)"
