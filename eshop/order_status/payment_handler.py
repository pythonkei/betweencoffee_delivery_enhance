# eshop/order_status/payment_handler.py
"""
支付處理子模組

拆分自 order_status_manager.py
負責支付成功後的統一處理邏輯：
- 支付狀態更新
- 購物車清空
- 線下付款確認（FPS/現金）
- 會員積分添加
- WebSocket 通知發送
"""

import logging

from django.utils import timezone

from ..models import CoffeeQueue, OrderModel
from ..time_calculation import unified_time_service
from .order_type_analyzer import OrderTypeAnalyzer

logger = logging.getLogger(__name__)


class PaymentHandler:
    """支付處理器 - 處理支付成功後的統一邏輯"""

    def __init__(self, order):
        self.order = order
        self.items = order.get_items()

    @classmethod
    def process_payment_success(cls, order_id, request=None):
        """處理支付成功後的統一邏輯（含購物車清空）- 修復支付狀態更新"""
        try:
            logger.info(f"🔄 開始處理訂單 #{order_id} 支付成功")

            order = OrderModel.objects.get(id=order_id)
            manager = cls(order)

            # ✅ 修復：更新支付狀態為 'paid'
            # 支援從 payment_pending 和 pending 兩種狀態轉為 paid
            if order.payment_status not in ["paid", "payment_pending"]:
                order.payment_status = "paid"
                order.paid_at = timezone.now()
                logger.info(f"✅ 訂單 #{order_id} 支付狀態更新為 paid，設置支付時間")
            elif order.payment_status == "payment_pending":
                # 從 payment_pending 轉為 paid（員工確認 FPS 付款）
                order.payment_status = "paid"
                order.paid_at = timezone.now()
                logger.info(
                    f"✅ FPS 訂單 #{order_id} 員工確認付款，支付狀態更新為 paid"
                )
            else:
                logger.info(f"ℹ️ 訂單 #{order_id} 已經是 paid 狀態")

            # ✅ 修復：確保訂單狀態正確
            if order.status == "pending":
                # 分析訂單類型
                order_type = OrderTypeAnalyzer.analyze_order_type(order)
                if order_type["is_beans_only"]:
                    order.status = "ready"
                    logger.info(f"✅ 純咖啡豆訂單 #{order_id} 狀態更新為 ready")
                else:
                    order.status = "waiting"
                    logger.info(f"✅ 訂單 #{order_id} 狀態更新為 waiting")
            elif order.payment_status == "payment_pending":
                # 如果支付狀態還是 payment_pending（FPS/現金等待確認時）
                order_type = OrderTypeAnalyzer.analyze_order_type(order)
                if order_type["is_beans_only"]:
                    order.status = "ready"
                else:
                    order.status = "waiting"
                logger.info(
                    f"✅ FPS/現金訂單 #{order_id} 支付狀態從 payment_pending 更新為 paid，訂單狀態更新為 {order.status}"
                )

            # ✅ 修復：保存所有更新
            order.save()
            logger.info(
                f"✅ 訂單 #{order_id} 保存成功: status={order.status}, payment_status={order.payment_status}, paid_at={order.paid_at}"
            )

            # ✅ 修改：加入隊列邏輯
            queue_item = None
            if manager.should_add_to_queue():
                logger.info(f"✅ 訂單 #{order_id} 需要加入隊列")

                # 如果是快速訂單，計算相關時間
                if order.order_type == "quick":
                    order.calculate_times_based_on_pickup_choice()
                    order.save()
                    logger.info(f"快速訂單 #{order.id} 已計算取貨時間")

                # 將訂單加入隊列
                from ..queue_manager_refactored import CoffeeQueueManager

                queue_manager = CoffeeQueueManager()
                queue_result = queue_manager.add_order_to_queue(order)

                if queue_result.get("success"):
                    queue_item = queue_result["data"]["queue_item"]
                    logger.info(
                        f"訂單 {order.id} 已加入製作隊列，位置: {queue_item.position}"
                    )
                else:
                    logger.error(
                        f"訂單 {order.id} 加入隊列失敗: {queue_result.get('message')}"
                    )
            else:
                logger.info(f"ℹ️ 訂單 #{order_id} 不需要加入隊列")

            # ✅ 修改：重新計算所有訂單時間
            logger.info(f"🔄 訂單 #{order_id} 支付成功，開始統一時間計算...")
            from ..queue_manager_refactored import CoffeeQueueManager

            queue_manager = CoffeeQueueManager()
            time_result = queue_manager.recalculate_all_order_times()

            # ✅ 修改：如果有request，清空購物車
            if request:
                cls.clear_user_cart_and_session(request)

            # ✅ 修改：發送WebSocket通知（同時通知訂單群組和隊列群組）
            try:
                from ..websocket_utils import send_payment_update, send_queue_update

                # 1. 發送到特定訂單群組（顧客端）
                send_payment_update(
                    order_id=order_id,
                    payment_status="paid",
                    data={
                        "payment_method": order.payment_method,
                        "message": "支付成功，訂單已加入隊列",
                    },
                )
                # 2. 發送到隊列群組（員工端），觸發員工頁面刷新
                send_queue_update(
                    update_type="payment_confirmed",
                    data={
                        "order_id": order_id,
                        "payment_method": order.payment_method,
                        "message": f"訂單 #{order_id} 支付確認，已加入隊列",
                    },
                )
            except Exception as ws_error:
                logger.error(f"發送WebSocket通知失敗: {str(ws_error)}")

            # ✅ 新增：添加會員積分（支付成功後自動添加）
            if order.user:
                try:
                    from socialuser.models_enhanced import CustomerLoyalty

                    loyalty, created = CustomerLoyalty.objects.get_or_create(
                        user=order.user
                    )
                    points_earned = loyalty.add_points_from_order(order)
                    logger.info(
                        f"✅ 用戶 {order.user.username} 訂單 #{order.id} 獲得 {points_earned} 積分"
                    )
                except Exception as e:
                    logger.error(f"添加會員積分失敗: {str(e)}")

            logger.info(f"✅ 訂單 {order_id} 支付成功處理完成")

            return {
                "success": True,
                "order_id": order_id,
                "order": order,
                "queue_item": queue_item,
                "message": "支付成功處理完成",
                "time_recalculated": time_result.get("success", False),
            }

        except OrderModel.DoesNotExist:
            logger.error(f"❌ 訂單 #{order_id} 不存在")
            return {
                "success": False,
                "message": "訂單不存在",
                "error": "Order not found",
            }
        except Exception as error:
            logger.error(f"❌ 處理支付成功失敗: {str(error)}", exc_info=True)
            return {
                "success": False,
                "message": f"處理失敗: {str(error)}",
                "error": str(error),
            }

    @staticmethod
    def clear_user_cart_and_session(request):
        """清空用戶的購物車和session - 保持不變"""
        try:
            from cart.cart import Cart

            # 1. 清空購物車對象
            cart = Cart(request)
            cart.clear()

            # 2. 清除相關session數據
            session_keys_to_clear = [
                "pending_order",
                "guest_cart",
                "quick_order_data",
                "cart",
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

    @classmethod
    def confirm_offline_payment(cls, order_id, payment_method, staff_name="staff"):
        """
        統一處理線下付款確認（FPS / 現金）

        重構後：調用 process_payment_success() 作為核心支付成功處理，
        再加上線下付款特有的 WebSocket 通知。

        Args:
            order_id: 訂單 ID
            payment_method: 支付方式 ('fps' 或 'cash')
            staff_name: 確認付款的員工名稱

        Returns:
            dict: {'success': True/False, 'message': '...', 'order_id': ...}
        """
        method_label = "FPS" if payment_method == "fps" else "現金"
        try:
            logger.info(
                f"🔄 員工 {staff_name} 開始確認 {method_label} 付款，訂單 #{order_id}"
            )

            order = OrderModel.objects.get(id=order_id)

            # 檢查訂單狀態：必須是 payment_pending
            if order.payment_status != "payment_pending":
                return {
                    "success": False,
                    "message": f"訂單 #{order_id} 當前支付狀態為 {order.payment_status}，無法確認 {method_label} 付款",
                    "order_id": order_id,
                }

            # 設置支付方式（process_payment_success 不會覆蓋已設置的 payment_method）
            order.payment_method = payment_method
            order.save(update_fields=["payment_method"])

            # 調用核心方法處理支付成功邏輯
            result = cls.process_payment_success(order_id)

            if not result.get("success"):
                logger.error(
                    f"❌ {method_label} 訂單 #{order_id} 核心支付處理失敗: {result.get('message')}"
                )
                return {
                    "success": False,
                    "message": f'{method_label} 付款確認失敗: {result.get("message")}',
                    "order_id": order_id,
                }

            # 發送線下付款特有的 WebSocket 通知（包含員工確認資訊）
            try:
                from ..websocket_utils import send_order_update, send_queue_update

                send_order_update(
                    order_id=order_id,
                    update_type="payment_confirmed",
                    data={
                        "order_id": order_id,
                        "payment_method": payment_method,
                        "payment_status": "paid",
                        "status": (
                            order.status
                            if hasattr(order, "status")
                            else result.get("order", order).status
                        ),
                        "confirmed_by": staff_name,
                        "message": f"{method_label} 付款已由 {staff_name} 確認，訂單 #{order_id} 已進入製作流程",
                    },
                )

                # 通知員工端刷新隊列
                queue_item = result.get("queue_item")
                queue_update_data = {
                    "order_id": order_id,
                    "payment_method": payment_method,
                    "queue_type": "waiting",
                    "confirmed_by": staff_name,
                }
                if queue_item:
                    queue_update_data["position"] = queue_item.position
                    queue_update_data["update_type"] = "add"
                else:
                    queue_update_data["update_type"] = "payment_confirmed"
                    queue_update_data["queue_added"] = False
                    queue_update_data["message"] = (
                        f"訂單 #{order_id} 付款已確認，但加入隊列失敗，請手動處理"
                    )

                send_queue_update(
                    update_type=queue_update_data["update_type"], data=queue_update_data
                )
            except Exception as ws_error:
                logger.error(f"發送 WebSocket 通知失敗: {ws_error}")

            return {
                "success": True,
                "message": f"{method_label} 訂單 #{order_id} 付款確認成功",
                "order_id": order_id,
                "payment_status": "paid",
                "status": result.get("order", order).status,
                "queue_result": {
                    "added": queue_item is not None,
                    "position": queue_item.position if queue_item else None,
                },
            }

        except OrderModel.DoesNotExist:
            logger.error(f"❌ {method_label} 訂單 #{order_id} 不存在")
            return {
                "success": False,
                "message": f"訂單 #{order_id} 不存在",
                "order_id": order_id,
            }
        except Exception as e:
            logger.error(f"❌ {method_label} 付款確認異常: {str(e)}")
            return {
                "success": False,
                "message": f"{method_label} 付款確認失敗: {str(e)}",
                "order_id": order_id,
            }

    @classmethod
    def confirm_fps_payment(cls, order_id, staff_name="staff"):
        """保留向後兼容 - 調用統一的 confirm_offline_payment"""
        return cls.confirm_offline_payment(order_id, "fps", staff_name)

    @classmethod
    def confirm_cash_payment(cls, order_id, staff_name="staff"):
        """保留向後兼容 - 調用統一的 confirm_offline_payment"""
        return cls.confirm_offline_payment(order_id, "cash", staff_name)

    @classmethod
    def process_payment_and_update_status(cls, order_id, payment_method="unknown"):
        """處理支付成功並更新狀態（替換原有的支付成功邏輯）"""
        try:
            from datetime import timedelta

            order = OrderModel.objects.get(id=order_id)

            # 驗證當前狀態
            if order.payment_status == "paid":
                return {"success": True, "message": "訂單已支付", "order": order}

            # 更新支付狀態
            order.payment_status = "paid"
            order.payment_method = payment_method
            order.paid_at = timezone.now()

            # 根據訂單類型設置初始狀態
            order_type = OrderTypeAnalyzer.analyze_order_type(order)

            if order_type["is_beans_only"]:
                # 純咖啡豆訂單直接標記為就緒
                order.status = "ready"
            else:
                # 含咖啡飲品訂單標記為等待中
                order.status = "waiting"

            order.save(
                update_fields=["payment_status", "payment_method", "paid_at", "status"]
            )

            # 創建或更新隊列項
            from ..queue_manager_refactored import CoffeeQueueManager

            queue_manager = CoffeeQueueManager()
            queue_result = queue_manager.add_order_to_queue(order)
            queue_item = (
                queue_result["data"]["queue_item"]
                if queue_result.get("success")
                else None
            )

            # 觸發相關事件
            cls._trigger_payment_success_events(order, payment_method)

            logger.info(
                f"Order {order_id} payment processed successfully via {payment_method}"
            )
            return {
                "success": True,
                "order": order,
                "queue_item": queue_item,
                "is_beans_only": order_type["is_beans_only"],
            }

        except Exception as e:
            logger.error(f"處理訂單 {order_id} 支付失敗: {str(e)}")
            return {"success": False, "message": str(e)}

    @staticmethod
    def _trigger_payment_success_events(order, payment_method):
        """觸發支付成功相關事件"""
        pass

    def should_add_to_queue(self):
        """判斷訂單是否應該加入隊列"""
        try:
            if self.order.payment_status != "paid":
                logger.info(
                    f"訂單 {self.order.id} 支付狀態不是 'paid'，而是 '{self.order.payment_status}'"
                )
                return False

            if self.order.status != "waiting":
                logger.info(
                    f"訂單 {self.order.id} 狀態不是 'waiting'，而是 '{self.order.status}'"
                )
                return False

            order_type = OrderTypeAnalyzer.analyze_order_type(self.order)
            should_add = order_type["has_coffee"]

            logger.info(
                f"訂單 {self.order.id} 是否加入隊列: {should_add} (has_coffee: {order_type['has_coffee']})"
            )
            return should_add

        except Exception as e:
            logger.error(f"判斷是否加入隊列時出錯: {str(e)}")
            return False
