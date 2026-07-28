"""
Order StatusChanger 單元測試。
測試訂單狀態轉換邏輯、邊界條件和錯誤處理。
"""
from unittest.mock import MagicMock, patch

from django.test import TestCase

from eshop.order_status.status_changer import StatusChanger


class MockOrder:
    """Mock OrderModel that mimics save() behavior"""
    def __init__(self):
        self.id = 1
        self.status = "preparing"
        self.preparation_started_at = None
        self.ready_at = None
        self.estimated_ready_time = None
        self.picked_up_at = None
        self.payment_status = "paid"
        self._saved = False

    def save(self, update_fields=None):
        self._saved = True


class StatusChangerTest(TestCase):
    """StatusChanger 模組測試"""

    # ==================== mark_as_ready_manually 測試 ====================

    @patch('eshop.whatsapp_notifier.send_order_ready_notification')
    @patch('eshop.websocket_utils.send_staff_action')
    @patch('eshop.websocket_utils.send_order_update')
    @patch('eshop.order_status.status_changer.CoffeeQueue')
    @patch('eshop.order_status.status_changer.OrderModel.objects')
    def test_mark_as_ready_success(self, mock_objects, mock_queue, 
                                    mock_update, mock_staff, mock_whatsapp):
        """成功將 preparing 訂單標記為 ready"""
        order = MockOrder()
        mock_objects.get.return_value = order
        mock_queue.objects.filter.return_value.first.return_value = None

        result = StatusChanger.mark_as_ready_manually(1, staff_name="test_staff")

        self.assertTrue(result["success"])
        self.assertEqual(order.status, "ready")
        self.assertIsNotNone(order.ready_at)
        mock_whatsapp.assert_called_once()

    @patch('eshop.order_status.status_changer.OrderModel.objects')
    def test_mark_as_ready_wrong_status(self, mock_objects):
        """非 preparing 狀態的訂單無法標記為 ready"""
        order = MockOrder()
        order.status = "waiting"
        mock_objects.get.return_value = order

        result = StatusChanger.mark_as_ready_manually(1)

        self.assertFalse(result["success"])
        self.assertIn("不能直接標記為就緒", str(result.get("message", "")))

    @patch('eshop.order_status.status_changer.OrderModel.objects')
    def test_mark_as_ready_already_ready(self, mock_objects):
        """已經是 ready 的訂單無法再次標記"""
        order = MockOrder()
        order.status = "ready"
        mock_objects.get.return_value = order

        result = StatusChanger.mark_as_ready_manually(1)

        self.assertFalse(result["success"])

    @patch('eshop.whatsapp_notifier.send_order_ready_notification')
    @patch('eshop.websocket_utils.send_staff_action')
    @patch('eshop.websocket_utils.send_order_update')
    @patch('eshop.order_status.status_changer.CoffeeQueue')
    @patch('eshop.order_status.status_changer.OrderModel.objects')
    def test_mark_as_ready_sets_estimated_time(self, mock_objects, mock_queue,
                                                mock_update, mock_staff, mock_whatsapp):
        """沒有 estimated_ready_time 時會自動設置"""
        order = MockOrder()
        order.estimated_ready_time = None
        mock_objects.get.return_value = order
        mock_queue.objects.filter.return_value.first.return_value = None

        StatusChanger.mark_as_ready_manually(1)

        self.assertIsNotNone(order.estimated_ready_time)

    @patch('eshop.whatsapp_notifier.send_order_ready_notification')
    @patch('eshop.websocket_utils.send_staff_action')
    @patch('eshop.websocket_utils.send_order_update')
    @patch('eshop.order_status.status_changer.CoffeeQueue')
    @patch('eshop.order_status.status_changer.OrderModel.objects')
    def test_mark_as_ready_queue_cleanup(self, mock_objects, mock_queue,
                                          mock_update, mock_staff, mock_whatsapp):
        """標記 ready 後隊列位置歸零"""
        order = MockOrder()
        mock_objects.get.return_value = order
        queue_item = MagicMock()
        queue_item.position = 5
        queue_item.status = "preparing"
        mock_queue.objects.filter.return_value.first.return_value = queue_item

        StatusChanger.mark_as_ready_manually(1)

        self.assertEqual(queue_item.position, 0)
        self.assertEqual(queue_item.status, "ready")

    @patch('eshop.whatsapp_notifier.send_order_ready_notification')
    @patch('eshop.websocket_utils.send_staff_action')
    @patch('eshop.websocket_utils.send_order_update')
    @patch('eshop.order_status.status_changer.CoffeeQueue')
    @patch('eshop.order_status.status_changer.OrderModel.objects')
    def test_mark_as_ready_whatsapp_error(self, mock_objects, mock_queue,
                                           mock_update, mock_staff, mock_whatsapp):
        """WhatsApp 發送失敗不影響主流程"""
        order = MockOrder()
        mock_objects.get.return_value = order
        mock_queue.objects.filter.return_value.first.return_value = None
        mock_whatsapp.side_effect = Exception("WhatsApp API error")

        result = StatusChanger.mark_as_ready_manually(1)

        self.assertTrue(result["success"])
        self.assertEqual(order.status, "ready")

    # ==================== mark_as_preparing_manually 測試 ====================

    @patch('eshop.order_status.status_changer.CoffeeQueue')
    @patch('eshop.order_status.status_changer.OrderModel.objects')
    @patch('eshop.order_status.status_changer.unified_time_service')
    def test_mark_as_preparing_success(self, mock_time, mock_objects, mock_queue):
        """成功將等待中訂單標記為 preparing"""
        order = MockOrder()
        order.status = "waiting"
        order.payment_status = "paid"
        order.get_items = MagicMock(return_value=[])
        mock_objects.get.return_value = order
        mock_queue.objects.filter.return_value.first.return_value = None

        result = StatusChanger.mark_as_preparing_manually(
            1, barista_name="test_barista", preparation_minutes=5
        )

        self.assertTrue(result["success"])
        self.assertEqual(order.status, "preparing")

    @patch('eshop.order_status.status_changer.OrderModel.objects')
    def test_mark_as_preparing_not_paid(self, mock_objects):
        """未支付的訂單不能開始製作"""
        order = MockOrder()
        order.status = "waiting"
        order.payment_status = "pending"
        mock_objects.get.return_value = order

        result = StatusChanger.mark_as_preparing_manually(1)

        self.assertFalse(result["success"])

    @patch('eshop.order_status.status_changer.OrderModel.objects')
    def test_mark_as_preparing_invalid_status(self, mock_objects):
        """已完成訂單不能開始製作"""
        order = MockOrder()
        order.status = "completed"
        order.payment_status = "paid"
        mock_objects.get.return_value = order

        result = StatusChanger.mark_as_preparing_manually(1)

        self.assertFalse(result["success"])

    # ==================== process_order_status_change 測試 ====================

    @patch('eshop.order_status.status_changer.CoffeeQueue')
    @patch('eshop.order_status.status_changer.OrderModel.objects')
    @patch('eshop.websocket_utils.send_order_update')
    def test_process_status_change_to_completed(self, mock_update, mock_objects, mock_queue):
        """狀態變更到 completed 會記錄 picked_up_at"""
        order = MockOrder()
        order.status = "ready"
        mock_objects.get.return_value = order
        mock_queue.objects.filter.return_value.first.return_value = None

        result = StatusChanger.process_order_status_change(1, "completed")

        self.assertTrue(result["success"])
        self.assertEqual(order.status, "completed")
        self.assertIsNotNone(order.picked_up_at)

    # ==================== mark_as_cancelled_manually 測試 ====================

    @patch('eshop.order_status.status_changer.CoffeeQueue')
    @patch('eshop.order_status.status_changer.OrderModel.objects')
    def test_mark_as_cancelled_success(self, mock_objects, mock_queue):
        """成功取消訂單"""
        order = MockOrder()
        order.status = "waiting"
        mock_objects.get.return_value = order

        result = StatusChanger.mark_as_cancelled_manually(1, staff_name="staff", reason="客戶取消")

        self.assertTrue(result["success"])
        self.assertEqual(order.status, "cancelled")
        self.assertEqual(order.payment_status, "cancelled")

    @patch('eshop.order_status.status_changer.OrderModel.objects')
    def test_mark_as_cancelled_already_completed(self, mock_objects):
        """已完成的訂單不能取消"""
        order = MockOrder()
        order.status = "completed"
        mock_objects.get.return_value = order

        result = StatusChanger.mark_as_cancelled_manually(1)

        self.assertFalse(result["success"])

    # ==================== mark_as_waiting_manually 測試 ====================

    @patch('eshop.order_status.status_changer.CoffeeQueue')
    @patch('eshop.order_status.status_changer.OrderModel.objects')
    def test_mark_as_waiting_from_preparing(self, mock_objects, mock_queue):
        """從 preparing 回到 waiting"""
        order = MockOrder()
        order.status = "preparing"
        order.preparation_started_at = "some_time"
        order.estimated_ready_time = "some_time"
        mock_objects.get.return_value = order
        mock_queue.objects.filter.return_value.first.return_value = None

        result = StatusChanger.mark_as_waiting_manually(1, staff_name="staff")

        self.assertTrue(result["success"])
        self.assertEqual(order.status, "waiting")
        self.assertIsNone(order.preparation_started_at)
        self.assertIsNone(order.estimated_ready_time)

    @patch('eshop.order_status.status_changer.CoffeeQueue')
    @patch('eshop.order_status.status_changer.OrderModel.objects')
    def test_mark_as_waiting_from_ready(self, mock_objects, mock_queue):
        """從 ready 回到 waiting"""
        order = MockOrder()
        order.status = "ready"
        mock_objects.get.return_value = order
        mock_queue.objects.filter.return_value.first.return_value = None

        result = StatusChanger.mark_as_waiting_manually(1)

        self.assertTrue(result["success"])
        self.assertEqual(order.status, "waiting")

    @patch('eshop.order_status.status_changer.OrderModel.objects')
    def test_mark_as_waiting_invalid_source(self, mock_objects):
        """completed 不能回到 waiting"""
        order = MockOrder()
        order.status = "completed"
        mock_objects.get.return_value = order

        result = StatusChanger.mark_as_waiting_manually(1)

        self.assertFalse(result["success"])

    # ==================== mark_as_completed_manually 測試 ====================

    @patch('eshop.order_status.status_changer.CoffeeQueue')
    @patch('eshop.order_status.status_changer.OrderModel.objects')
    @patch('eshop.websocket_utils.send_order_update')
    def test_mark_as_completed(self, mock_update, mock_objects, mock_queue):
        """成功將 ready 標記為 completed"""
        order = MockOrder()
        order.status = "ready"
        mock_objects.get.return_value = order
        mock_queue.objects.filter.return_value.first.return_value = None

        result = StatusChanger.mark_as_completed_manually(1, staff_name="staff")

        self.assertTrue(result["success"])