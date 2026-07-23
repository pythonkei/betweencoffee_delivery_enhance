# eshop/order_status_manager.py
"""
訂單狀態管理器（橋接層）

此文件已拆分為 eshop/order_status/ 子模組：
    - order_type_analyzer.py: 訂單類型分析
    - payment_handler.py: 支付成功處理
    - status_display.py: 狀態顯示邏輯
    - status_changer.py: 狀態變更操作

此橋接層保留向後兼容性，所有功能委託給子模組。
"""

import logging

from .order_status import (
    OrderTypeAnalyzer,
    PaymentHandler,
    StatusChanger,
    StatusDisplay,
)

logger = logging.getLogger(__name__)

# ==================== 向後兼容的別名 ====================

# 訂單類型分析
analyze_order_type = OrderTypeAnalyzer.analyze_order_type

# 支付處理
process_payment_success = PaymentHandler.process_payment_success
clear_user_cart_and_session = PaymentHandler.clear_user_cart_and_session
confirm_offline_payment = PaymentHandler.confirm_offline_payment
confirm_fps_payment = PaymentHandler.confirm_fps_payment
confirm_cash_payment = PaymentHandler.confirm_cash_payment
process_payment_and_update_status = PaymentHandler.process_payment_and_update_status

# 狀態顯示
get_display_status = StatusDisplay.get_display_status

# 狀態變更
process_order_status_change = StatusChanger.process_order_status_change
process_batch_status_changes = StatusChanger.process_batch_status_changes
mark_as_waiting_manually = StatusChanger.mark_as_waiting_manually
mark_as_cancelled_manually = StatusChanger.mark_as_cancelled_manually
mark_as_preparing_manually = StatusChanger.mark_as_preparing_manually
mark_as_ready_manually = StatusChanger.mark_as_ready_manually
mark_as_completed_manually = StatusChanger.mark_as_completed_manually

# ==================== 類別定義（向後兼容） ====================


class OrderStatusManager:
    """
    訂單狀態管理器（橋接層）

    保留向後兼容性，所有方法委託給子模組。
    新代碼應直接使用子模組中的類別。
    """

    def __init__(self, order=None):
        self.order = order
        self.items = order.get_items() if order else []

    # ---- 訂單類型分析 ----

    @staticmethod
    def analyze_order_type(order):
        """分析訂單類型 - 委託給 OrderTypeAnalyzer"""
        return OrderTypeAnalyzer.analyze_order_type(order)

    # ---- 支付處理 ----

    @classmethod
    def process_payment_success(cls, order_id, request=None):
        """處理支付成功 - 委託給 PaymentHandler"""
        return PaymentHandler.process_payment_success(order_id, request)

    @staticmethod
    def clear_user_cart_and_session(request):
        """清空購物車 - 委託給 PaymentHandler"""
        return PaymentHandler.clear_user_cart_and_session(request)

    @classmethod
    def confirm_offline_payment(cls, order_id, payment_method, staff_name="staff"):
        """線下付款確認 - 委託給 PaymentHandler"""
        return PaymentHandler.confirm_offline_payment(
            order_id, payment_method, staff_name
        )

    @classmethod
    def confirm_fps_payment(cls, order_id, staff_name="staff"):
        """FPS 付款確認 - 委託給 PaymentHandler"""
        return PaymentHandler.confirm_fps_payment(order_id, staff_name)

    @classmethod
    def confirm_cash_payment(cls, order_id, staff_name="staff"):
        """現金付款確認 - 委託給 PaymentHandler"""
        return PaymentHandler.confirm_cash_payment(order_id, staff_name)

    @classmethod
    def process_payment_and_update_status(cls, order_id, payment_method="unknown"):
        """處理支付並更新狀態 - 委託給 PaymentHandler"""
        return PaymentHandler.process_payment_and_update_status(
            order_id, payment_method
        )

    def should_add_to_queue(self):
        """判斷訂單是否應該加入隊列 - 委託給 PaymentHandler"""
        handler = PaymentHandler(self.order)
        return handler.should_add_to_queue()

    # ---- 狀態顯示 ----

    def get_display_status(self):
        """獲取顯示狀態 - 委託給 StatusDisplay"""
        display = StatusDisplay(self.order)
        return display.get_display_status()

    # ---- 狀態變更 ----

    @classmethod
    def process_order_status_change(cls, order_id, new_status, staff_name=None):
        """處理訂單狀態變化 - 委託給 StatusChanger"""
        return StatusChanger.process_order_status_change(
            order_id, new_status, staff_name
        )

    @classmethod
    def process_batch_status_changes(cls, order_status_list):
        """批量處理狀態變化 - 委託給 StatusChanger"""
        return StatusChanger.process_batch_status_changes(order_status_list)

    @classmethod
    def mark_as_waiting_manually(cls, order_id, staff_name=None):
        """標記為等待中 - 委託給 StatusChanger"""
        return StatusChanger.mark_as_waiting_manually(order_id, staff_name)

    @classmethod
    def mark_as_cancelled_manually(cls, order_id, staff_name=None, reason=None):
        """標記為已取消 - 委託給 StatusChanger"""
        return StatusChanger.mark_as_cancelled_manually(order_id, staff_name, reason)

    @classmethod
    def mark_as_preparing_manually(
        cls, order_id, barista_name=None, preparation_minutes=None
    ):
        """標記為製作中 - 委託給 StatusChanger"""
        return StatusChanger.mark_as_preparing_manually(
            order_id, barista_name, preparation_minutes
        )

    @classmethod
    def mark_as_ready_manually(cls, order_id, staff_name=None):
        """標記為就緒 - 委託給 StatusChanger"""
        return StatusChanger.mark_as_ready_manually(order_id, staff_name)

    @classmethod
    def mark_as_completed_manually(cls, order_id, staff_name=None):
        """標記為已完成 - 委託給 StatusChanger"""
        return StatusChanger.mark_as_completed_manually(order_id, staff_name)
