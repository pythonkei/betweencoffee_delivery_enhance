# eshop/order_status_manager.py
"""
處理所有訂單狀態相關的顯示邏輯# - 統一的訂單狀態處理
# - 付款成功處理（含購物車清空）
# - 訂單類型分析
# - 狀態顯示邏輯
# - 隊列管理集成
"""

import logging
from django.utils import timezone

from .models import OrderModel, CoffeeQueue
from .time_calculation import unified_time_service

logger = logging.getLogger(__name__)


class OrderStatusManager:
    """统一的订单状态管理器"""
    
    def __init__(self, order):
        self.order = order
        self.items = order.get_items()
    

    @classmethod
    def process_payment_success(cls, order_id, request=None):
        """处理支付成功后的统一逻辑（含购物车清空）- 修复支付状态更新"""
        try:
            logger.info(f"🔄 开始处理订单 #{order_id} 支付成功")
            
            order = OrderModel.objects.get(id=order_id)
            manager = cls(order)
            
            # ✅ 修复：更新支付状态为 'paid'
            if order.payment_status != 'paid':
                order.payment_status = 'paid'
                order.paid_at = timezone.now()
                logger.info(f"✅ 订单 #{order_id} 支付状态更新为 paid，设置支付时间")
            
            # ✅ 修复：确保订单状态正确
            if order.status == 'pending':
                # 分析订单类型
                order_type = manager.analyze_order_type()
                if order_type['is_beans_only']:
                    order.status = 'ready'
                    logger.info(f"✅ 纯咖啡豆订单 #{order_id} 状态更新为 ready")
                else:
                    order.status = 'waiting'
                    logger.info(f"✅ 订单 #{order_id} 状态更新为 waiting")
            
            # ✅ 修复：保存所有更新
            order.save()
            logger.info(f"✅ 订单 #{order_id} 保存成功: status={order.status}, payment_status={order.payment_status}, paid_at={order.paid_at}")
            
            # ✅ 修改：加入队列逻辑
            queue_item = None
            if manager.should_add_to_queue():
                logger.info(f"✅ 订单 #{order_id} 需要加入队列")
                
                # 如果是快速订单，计算相关时间
                if order.order_type == 'quick':
                    order.calculate_times_based_on_pickup_choice()
                    order.save()
                    logger.info(f"快速订单 #{order.id} 已计算取货时间")
                
                # 将订单加入队列
                from .queue_manager_refactored import CoffeeQueueManager
                queue_manager = CoffeeQueueManager()
                queue_item = queue_manager.add_order_to_queue_compatible(order)
                
                if queue_item:
                    logger.info(f"订单 {order.id} 已加入制作队列，位置: {queue_item.position}")
                else:
                    logger.error(f"订单 {order.id} 加入队列失败")
            else:
                logger.info(f"ℹ️ 订单 #{order_id} 不需要加入队列")
            
            # ✅ 修改：重新计算所有订单时间
            logger.info(f"🔄 订单 #{order_id} 支付成功，开始统一时间计算...")
            from .queue_manager_refactored import CoffeeQueueManager
            queue_manager = CoffeeQueueManager()
            time_result = queue_manager.recalculate_all_order_times_compatible()
            
            # ✅ 修改：如果有request，清空购物车
            if request:
                cls.clear_user_cart_and_session(request)
            
            # ✅ 修改：发送WebSocket通知
            try:
                from .websocket_utils import send_payment_update
                send_payment_update(
                    order_id=order_id,
                    payment_status='paid',
                    data={
                        'payment_method': order.payment_method,
                        'message': '支付成功，订单已加入队列'
                    }
                )
            except Exception as ws_error:
                logger.error(f"发送WebSocket通知失败: {str(ws_error)}")
            
            logger.info(f"✅ 订单 {order_id} 支付成功处理完成")
            
            # ✅ 修改：返回字典格式，包含成功状态和订单信息
            return {
                'success': True,
                'order_id': order_id,
                'order': order,
                'queue_item': queue_item,
                'message': '支付成功处理完成',
                'time_recalculated': time_result.get('success', False)
            }
            
        except OrderModel.DoesNotExist:
            logger.error(f"❌ 订单 #{order_id} 不存在")
            return {'success': False, 'message': '订单不存在', 'error': 'Order not found'}
        except Exception as error:  # ✅ 修复：将变量名从 e 改为 error
            logger.error(f"❌ 处理支付成功失败: {str(error)}", exc_info=True)
            return {'success': False, 'message': f'处理失败: {str(error)}', 'error': str(error)}


    @staticmethod
    def clear_user_cart_and_session(request):
        """清空用户的购物车和session - 保持不變"""
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
            
        except Exception as e:
            logger.error(f"❌ 清空購物車失敗: {str(e)}")


    # 業務邏輯 : 處理訂單狀態變化的統一方法
    @classmethod
    def process_order_status_change(cls, order_id, new_status, staff_name=None):
        """處理訂單狀態變化的統一邏輯 - 包含統一時間計算"""
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
            
            # ============================================================
            # 🔧 修復：發送WebSocket通知（統一使用 'status' 類型）
            # 說明：前端 order-detail.js 中的 handleMessage 方法
            #       期望接收 update_type 為 'status' 的消息
            #       原本使用 'status_change' 導致前端無法正確處理
            # ============================================================
            try:
                from .websocket_utils import send_order_update
                send_order_update(
                    order_id=order_id,
                    update_type='status',  # ← 修復：改為 'status'，與前端一致
                    data={
                        'status': new_status,
                        'status_display': order.get_status_display(),  # ← 新增
                        'message': f"訂單狀態已更新為 {new_status}"
                    }
                )
                logger.info(f"✅ 已發送訂單 #{order_id} 狀態更新 WebSocket 通知")
            except Exception as ws_error:
                logger.error(f"發送WebSocket通知失敗: {str(ws_error)}")
            
            return {
                'success': True,
                'order_id': order_id,
                'old_status': old_status,
                'new_status': new_status,
                'time_recalculated': True
            }
            
        except OrderModel.DoesNotExist:
            logger.error(f"❌ 訂單 #{order_id} 不存在")
            return {'success': False, 'error': '訂單不存在'}
        except Exception as e:
            logger.error(f"❌ 處理訂單狀態變化失敗: {str(e)}", exc_info=True)
            return {'success': False, 'error': str(e)}


    # ✅ 新增：批量處理多個訂單狀態變化
    @classmethod
    def process_batch_status_changes(cls, order_status_list):
        """批量處理多個訂單狀態變化 - 效率更高"""
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
            
            return {
                'success': True,
                'results': results,
                'time_recalculated': True
            }
            
        except Exception as e:
            logger.error(f"❌ 批量處理訂單狀態變化失敗: {str(e)}")
            return {'success': False, 'error': str(e)}




    def get_display_status(self):
        """获取订单显示状态"""
        order_type = self.analyze_order_type()
        
        # 基础状态 - 修复：使用 payment_status 而不是 is_paid
        status_info = {
            'order': self.order,
            'items': self.order.get_items_with_chinese_options(),
            'payment_status': 'paid' if self.order.payment_status == 'paid' else 'pending',  # 修复这里
            **order_type
        }
        
        # 根据订单类型添加特定信息
        if order_type['is_beans_only']:
            # 纯咖啡豆订单：直接完成
            status_info.update(self._get_beans_only_status())
        else:
            # 咖啡订单或混合订单：需要制作
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
    

    def _get_beans_only_status(self):
        """获取纯咖啡豆订单状态"""
        # 纯咖啡豆订单，支付后直接设置为就绪 - 修复：使用 payment_status
        if self.order.payment_status == 'paid' and self.order.status in ['pending', 'waiting', 'preparing']:
            self.order.status = 'ready'
            self.order.save()
            logger.info(f"纯咖啡豆订单 {self.order.id} 自动设置为就绪状态")
        
        return {
            'progress_percentage': 100,
            'progress_display': '100% 完成',
            'show_progress_bar': False,
            'queue_info': None,
            'remaining_minutes': 0,
            'estimated_time': '随时可取',
            'is_ready': True,
            'status_message': '您的咖啡豆已準備就緒，隨時可以提取！'
        }


    def _get_coffee_order_status(self):
        """获取咖啡订单状态（包含混合订单）"""
        # 获取队列信息
        queue_info = self._get_queue_info()
        
        # 计算进度
        progress_info = self._calculate_progress()
        
        # 确定是否就绪
        is_ready = self.order.status in ['ready', 'completed']
        
        # 获取队列显示文本
        queue_display, queue_message, remaining_display = self._get_queue_display_text(queue_info)
        
        # 格式化预计时间（香港时区）
        estimated_time_display = unified_time_service.format_time_for_display(
            self.order.estimated_ready_time, 'full'
        ) if self.order.estimated_ready_time else '计算中...'
        
        # 获取订单状态消息
        status_message = self._get_status_message(is_ready)
        
        # 构建状态信息 - 修复：使用 payment_status
        status_info = {
            'queue_info': queue_info,
            'progress_percentage': progress_info['percentage'],
            'progress_display': progress_info['display'],
            'show_progress_bar': self.order.payment_status == 'paid' and not self.analyze_order_type()['is_beans_only'],
            'remaining_minutes': self._get_remaining_minutes(),
            'estimated_time': estimated_time_display,
            'is_ready': is_ready,
            
            # ✅ 确保模板需要的字段都存在
            'queue_display': queue_display,
            'queue_message': queue_message,
            'remaining_display': remaining_display,
            'status_message': status_message,
        }
        
        return status_info


    def _get_status_message(self, is_ready):
        """获取状态消息"""
        if is_ready:
            order_type = self.analyze_order_type()
            if order_type['is_mixed_order']:
                return '您訂購的商品已準備就緒，隨時可以提取！'
            else:
                return '您的咖啡已準備就緒，隨時可以提取！'
        else:
            return '您的訂單正在製作中，請耐心等候...'
    

    def _get_queue_display_text(self, queue_info):
        """生成队列显示文本"""
        if not queue_info:
            return '等待加入队列...', '系统正在处理您的订单', ''
        
        queue_position = queue_info['queue_position']
        wait_minutes = queue_info['queue_wait_minutes']
        total_minutes = queue_info['total_minutes']
        
        # 队列状态文本
        queue_display = f"队列位置: #{queue_position} | 预计等待: {wait_minutes}分钟"
        
        # 队列消息
        if queue_position == 1:
            queue_message = '下一个就轮到您了！'
        elif queue_position <= 3:
            queue_message = f'前面还有 {queue_position - 1} 个订单'
        else:
            queue_message = '目前订单较多，请耐心等候'
        
        # 剩余时间显示
        remaining_display = f"(约{total_minutes}分钟后)"
        
        return queue_display, queue_message, remaining_display
    



    @classmethod
    def mark_as_waiting_manually(cls, order_id, staff_name=None):
        """手動將訂單標記為等待中"""
        try:
            order = OrderModel.objects.get(id=order_id)
            old_status = order.status
            
            # 驗證狀態轉換
            if old_status not in ['pending', 'preparing', 'ready']:
                raise ValueError(f"無法從狀態 {old_status} 轉換為 waiting")
            
            order.status = 'waiting'
            order.preparation_started_at = None
            order.estimated_ready_time = None
            order.save(update_fields=['status', 'preparation_started_at', 'estimated_ready_time'])
            
            # 更新隊列項
            queue_item = CoffeeQueue.objects.filter(order=order).first()
            if queue_item:
                queue_item.status = 'waiting'
                queue_item.actual_start_time = None
                queue_item.save()
            
            logger.info(f"Order {order_id} marked as waiting by {staff_name or 'system'}")
            return {'success': True, 'order': order}
            
        except Exception as e:
            logger.error(f"標記訂單 {order_id} 為等待中失敗: {str(e)}")
            return {'success': False, 'message': str(e)}

    @classmethod  
    def mark_as_cancelled_manually(cls, order_id, staff_name=None, reason=None):
        """手動將訂單標記為已取消"""
        try:
            order = OrderModel.objects.get(id=order_id)
            old_status = order.status
            
            # 檢查是否可以取消
            if old_status in ['completed', 'cancelled']:
                return {'success': False, 'message': f'訂單已{old_status}，無法取消'}
            
            order.status = 'cancelled'
            order.cancelled_at = timezone.now()
            order.payment_status = 'cancelled'
            
            if reason:
                order.cancellation_reason = reason
                
            order.save(update_fields=['status', 'cancelled_at', 'payment_status', 'cancellation_reason'])
            
            # 更新隊列項
            queue_item = CoffeeQueue.objects.filter(order=order).first()
            if queue_item:
                queue_item.status = 'cancelled'
                queue_item.save()
            
            logger.info(f"Order {order_id} cancelled by {staff_name or 'system'}. Reason: {reason}")
            return {'success': True, 'order': order}
            
        except Exception as e:
            logger.error(f"取消訂單 {order_id} 失敗: {str(e)}")
            return {'success': False, 'message': str(e)}

    @classmethod
    def process_payment_and_update_status(cls, order_id, payment_method="unknown"):
        """處理支付成功並更新狀態（替換原有的支付成功邏輯）"""
        try:
            from datetime import timedelta
            
            order = OrderModel.objects.get(id=order_id)
            
            # 驗證當前狀態
            if order.payment_status == 'paid':
                return {'success': True, 'message': '訂單已支付', 'order': order}
            
            # 更新支付狀態
            order.payment_status = 'paid'
            order.payment_method = payment_method
            order.paid_at = timezone.now()
            
            # 根據訂單類型設置初始狀態
            order_type = cls.analyze_order_type(order)
            
            if order_type['is_beans_only']:
                # 純咖啡豆訂單直接標記為就緒
                order.status = 'ready'
            else:
                # 含咖啡飲品訂單標記為等待中
                order.status = 'waiting'
            
            order.save(update_fields=['payment_status', 'payment_method', 'paid_at', 'status'])
            
            # 創建或更新隊列項
            from eshop.queue_manager_refactored import CoffeeQueueManager
            queue_manager = CoffeeQueueManager()
            queue_item = queue_manager.add_order_to_queue_compatible(order)
            
            # 觸發相關事件
            cls._trigger_payment_success_events(order, payment_method)
            
            logger.info(f"Order {order_id} payment processed successfully via {payment_method}")
            return {
                'success': True, 
                'order': order, 
                'queue_item': queue_item,
                'is_beans_only': order_type['is_beans_only']
            }
            
        except Exception as e:
            logger.error(f"處理訂單 {order_id} 支付失敗: {str(e)}")
            return {'success': False, 'message': str(e)}


    def analyze_order_type(self, order=None):
        """分析訂單類型 - 確保返回完整字典"""
        if order is None:
            order = self.order
        
        try:
            items = order.get_items()
            has_coffee = False
            has_beans = False
            
            for item in items:
                item_type = item.get('type', '')
                if item_type == 'coffee':
                    has_coffee = True
                elif item_type == 'bean':
                    has_beans = True
            
            # ✅ 確保返回所有必要的鍵
            return {
                'has_coffee': has_coffee,
                'has_beans': has_beans,
                'is_mixed_order': has_coffee and has_beans,
                'is_beans_only': has_beans and not has_coffee,
                'is_coffee_only': has_coffee and not has_beans,
            }
        except Exception as e:
            logger.error(f"分析訂單類型時出錯: {str(e)}")
            # 返回默認值
            return {
                'has_coffee': False,
                'has_beans': False,
                'is_mixed_order': False,
                'is_beans_only': False,
                'is_coffee_only': False,
            }

    @staticmethod
    def _trigger_payment_success_events(order, payment_method):
        """觸發支付成功相關事件"""
        # 這裡可以添加 WebSocket 通知、郵件通知等
        pass


    @classmethod
    def mark_as_preparing_manually(cls, order_id, barista_name=None,
                                   preparation_minutes=None):
        """手動將訂單標記為製作中（員工操作）- 優化版本"""
        try:
            from django.utils import timezone
            from datetime import timedelta
            
            # 獲取訂單
            order = OrderModel.objects.get(id=order_id)
            
            # 檢查訂單狀態
            if order.status not in ['waiting', 'pending', 'confirmed']:
                msg = f"訂單狀態 {order.status} 不允許開始製作"
                raise ValueError(msg)
            
            # 檢查支付狀態
            if order.payment_status != "paid":
                raise ValueError("訂單未支付，無法開始製作")
            
            # 計算製作時間（如果未提供）
            if preparation_minutes is None:
                items = order.get_items()
                coffee_count = sum(
                    item.get('quantity', 1) 
                    for item in items 
                    if item.get('type') == 'coffee'
                )
                
                from eshop.queue_manager_refactored import CoffeeQueueManager
                queue_manager = CoffeeQueueManager()
                
                if coffee_count > 0:
                    preparation_minutes = queue_manager.calculate_preparation_time(
                        coffee_count
                    )
                else:
                    preparation_minutes = 5
            
            # ====== 階段1優化：立即更新數據庫並發送WebSocket通知 ======
            old_status = order.status
            
            # 1. 更新訂單狀態
            order.status = 'preparing'
            order.preparation_started_at = timezone.now()
            
            # 計算預計完成時間（使用新的時間服務）
            hk_time = unified_time_service.get_hong_kong_time()
            order.estimated_ready_time = hk_time + timedelta(
                minutes=preparation_minutes
            )
            
            # 2. 立即保存訂單狀態
            order.save(update_fields=[
                'status', 'preparation_started_at', 'estimated_ready_time'
            ])
            logger.info(f"✅ 訂單 #{order_id} 狀態已更新: {old_status} → preparing")
            
            # 3. 立即發送WebSocket通知（不等待其他處理）
            try:
                from .websocket_utils import send_order_update
                estimated_time = None
                if order.estimated_ready_time:
                    estimated_time = order.estimated_ready_time.isoformat()
                
                send_order_update(
                    order_id=order_id,
                    update_type='status',
                    data={
                        'status': 'preparing',
                        'status_display': '製作中',
                        'message': '咖啡正在製作中！',
                        'timestamp': timezone.now().isoformat(),
                        'estimated_ready_time': estimated_time
                    }
                )
                logger.info(
                    f"✅ 已立即發送訂單 #{order_id} 狀態更新 WebSocket 通知"
                )
            except Exception as ws_error:
                logger.error(f"❌ 發送WebSocket通知失敗: {str(ws_error)}")
            
            # 4. 更新隊列項（在WebSocket通知後處理）
            from eshop.models import CoffeeQueue
            queue_item = CoffeeQueue.objects.filter(order=order).first()
            if queue_item:
                queue_item.status = 'preparing'
                queue_item.actual_start_time = timezone.now()
                queue_item.estimated_completion_time = hk_time + timedelta(
                    minutes=preparation_minutes
                )
                if barista_name:
                    queue_item.barista = barista_name
                queue_item.save()
                logger.info(f"✅ 訂單 #{order_id} 隊列項已更新")
            
            # 5. 更新隊列時間（異步處理，不阻塞響應）
            try:
                from eshop.queue_manager_refactored import CoffeeQueueManager
                queue_manager = CoffeeQueueManager()
                
                # 使用線程異步處理隊列時間更新
                import threading
                
                def async_update_queue_times():
                    try:
                        queue_manager.update_estimated_times_compatible()
                        logger.info(
                            f"✅ 訂單 #{order_id} 隊列時間已異步更新"
                        )
                    except Exception as e:
                        logger.error(f"❌ 異步更新隊列時間失敗: {str(e)}")
                
                thread = threading.Thread(target=async_update_queue_times)
                thread.daemon = True
                thread.start()
                
            except Exception as queue_error:
                logger.error(f"❌ 隊列時間更新失敗: {str(queue_error)}")
            
            # 6. 記錄日誌
            logger.info(
                f"✅ 訂單 #{order_id} 已開始製作，操作員: {barista_name or 'system'}"
            )
            
            return {
                'success': True,
                'order': order,
                'queue_item': queue_item,
                'preparation_minutes': preparation_minutes,
                'message': f'訂單 #{order_id} 已開始製作',
                'websocket_sent': True,
                'timestamp': timezone.now().isoformat()
            }
            
        except OrderModel.DoesNotExist:
            logger.error(f"❌ 訂單 {order_id} 不存在")
            return {'success': False, 'message': '訂單不存在'}
        except Exception as e:
            logger.error(
                f"❌ 標記訂單 {order_id} 為製作中失敗: {str(e)}",
                exc_info=True
            )
            return {'success': False, 'message': str(e)}



    @classmethod
    def mark_as_ready_manually(cls, order_id, staff_name=None):
        """手動將訂單標記為就緒"""
        try:
            order = OrderModel.objects.get(id=order_id)

            # 檢查狀態轉換是否允許
            if order.status != 'preparing':
                raise ValueError(f"訂單狀態 {order.status} 不能直接標記為就緒")

            # 更新訂單狀態
            order.status = 'ready'
            order.ready_at = timezone.now()

            # 確保預計就緒時間已設置
            if not order.estimated_ready_time:
                order.estimated_ready_time = timezone.now()

            order.save(update_fields=['status', 'ready_at', 'estimated_ready_time'])

            # 更新隊列項 - 關鍵修復：清理隊列位置
            queue_item = CoffeeQueue.objects.filter(order=order).first()
            if queue_item:
                old_position = queue_item.position
                queue_item.status = 'ready'
                queue_item.position = 0  # ✅ 重要：清理隊列位置
                queue_item.actual_completion_time = timezone.now()
                queue_item.save()
                
                logger.info(
                    f"✅ 訂單 #{order_id} 隊列項已更新: "
                    f"狀態 → ready, 位置 {old_position} → 0"
                )

            logger.info(f"Order {order_id} marked as ready by {staff_name or 'system'}")
            return {'success': True, 'order': order, 'queue_item': queue_item}

        except Exception as e:
            logger.error(f"標記訂單 {order_id} 為就緒失敗: {str(e)}")
            return {'success': False, 'message': str(e)}


    # ✅ 新增：手動標記訂單為已提取（員工操作）
    @classmethod
    def mark_as_completed_manually(cls, order_id, staff_name=None):
        """手動將訂單標記為已提取 - 員工操作"""
        try:
            logger.info(f"👨‍🍳 員工 {staff_name} 手動標記訂單 #{order_id} 為已提取")
            
            result = cls.process_order_status_change(
                order_id=order_id,
                new_status='completed',
                staff_name=staff_name
            )
            
            if result.get('success'):
                logger.info(f"✅ 訂單 #{order_id} 已手動標記為已提取，操作員工: {staff_name}")
                
                # 發送特定的員工操作通知
                try:
                    from .websocket_utils import send_staff_action
                    send_staff_action(
                        order_id=order_id,
                        action='marked_completed',
                        staff_name=staff_name,
                        message=f"員工 {staff_name} 已將訂單標記為已提取"
                    )
                except Exception as ws_error:
                    logger.error(f"發送員工操作WebSocket通知失敗: {str(ws_error)}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ 手動標記訂單為已提取失敗: {str(e)}", exc_info=True)
            return {'success': False, 'error': str(e)}



    def _get_queue_info(self):
        """获取队列信息"""
        # 修复：使用 payment_status 而不是 is_paid
        if self.order.payment_status != 'paid':  # 修复这里
            return None
        
        try:
            queue_item = CoffeeQueue.objects.get(order=self.order)
            
            # 计算队列位置
            waiting_before = CoffeeQueue.objects.filter(
                status='waiting',
                position__lt=queue_item.position
            ).count()
            
            queue_position = waiting_before + 1
            
            # 计算等待时间
            queue_wait_minutes = 0
            waiting_items = CoffeeQueue.objects.filter(
                status='waiting',
                position__lt=queue_item.position
            ).order_by('position')
            
            for item in waiting_items:
                queue_wait_minutes += item.preparation_time_minutes or 5
            
            preparation_minutes = queue_item.preparation_time_minutes or 5
            total_minutes = queue_wait_minutes + preparation_minutes
            
            return {
                'queue_position': queue_position,
                'queue_wait_minutes': queue_wait_minutes,
                'preparation_minutes': preparation_minutes,
                'total_minutes': total_minutes,
            }
            
        except CoffeeQueue.DoesNotExist:
            return None
    

    def _calculate_progress(self):
        """计算制作进度"""
        # 如果订单已经完成
        if self.order.status in ['ready', 'completed']:
            return {
                'percentage': 100,
                'display': '100% 完成'
            }
        
        # 如果订单在制作中且有预计时间
        if self.order.status == 'preparing' and self.order.estimated_ready_time:
            # 使用新的时间服务计算进度
            from .time_calculation.time_calculators import TimeCalculators
            progress = TimeCalculators.calculate_progress_percentage(
                self.order.preparation_started_at,
                self.order.estimated_ready_time,
                unified_time_service.get_hong_kong_time()
            )
            return {
                'percentage': progress,
                'display': f'{progress}% 完成'
            }
        
        # 如果订单在等待中
        if self.order.status == 'waiting':
            return {
                'percentage': 10,  # 等待中的基础进度
                'display': '10% 等待中'
            }
        
        # 默认状态
        return {
            'percentage': 0,
            'display': '0% 等待支付'
        }
    

    def _get_remaining_minutes(self):
        """获取剩余分钟数"""
        if not self.order.estimated_ready_time:
            return 0
        
        now_hk = unified_time_service.get_hong_kong_time()
        if self.order.estimated_ready_time > now_hk:
            diff = self.order.estimated_ready_time - now_hk
            return max(0, int(diff.total_seconds() / 60))
        return 0
    
    
    def should_add_to_queue(self):
        """判斷訂單是否應該加入隊列"""
        try:
            # 檢查訂單支付狀態和狀態
            if self.order.payment_status != 'paid':
                logger.info(f"訂單 {self.order.id} 支付狀態不是 'paid'，而是 '{self.order.payment_status}'")
                return False
            
            if self.order.status != 'waiting':
                logger.info(f"訂單 {self.order.id} 狀態不是 'waiting'，而是 '{self.order.status}'")
                return False
            
            # 分析訂單類型
            order_type = self.analyze_order_type()
            should_add = order_type['has_coffee']
            
            logger.info(f"訂單 {self.order.id} 是否加入隊列: {should_add} (has_coffee: {order_type['has_coffee']})")
            return should_add
            
        except Exception as e:
            logger.error(f"判斷是否加入隊列時出錯: {str(e)}")
            return False
    
