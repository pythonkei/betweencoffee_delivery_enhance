"""
WhatsApp 通知模組測試。
使用 mock 測試 WhatsApp Cloud API 發送邏輯，避免真實發送訊息。
"""
import json
from unittest.mock import MagicMock, patch

from django.conf import settings
from django.test import TestCase, override_settings

from eshop.whatsapp_notifier import send_whatsapp_message, send_order_ready_notification


class MockResponse:
    """模擬 requests.Response"""
    def __init__(self, status_code=200, json_data=None):
        self.status_code = status_code
        self._json_data = json_data or {"messages": [{"id": "test_msg_123"}]}

    def raise_for_status(self):
        if self.status_code >= 400:
            from requests.exceptions import HTTPError
            raise HTTPError(f"HTTP {self.status_code}")

    def json(self):
        return self._json_data


class WhatsAppNotifierTest(TestCase):
    """WhatsApp 通知模組測試"""

    def setUp(self):
        # 確保測試環境有 WhatsApp 設定
        self.original_token = getattr(settings, 'WHATSAPP_TOKEN', '')
        self.original_phone_id = getattr(settings, 'WHATSAPP_PHONE_NUMBER_ID', '')
        self.original_enabled = getattr(settings, 'WHATSAPP_ENABLED', False)

    def tearDown(self):
        # 還原設定
        settings.WHATSAPP_TOKEN = self.original_token
        settings.WHATSAPP_PHONE_NUMBER_ID = self.original_phone_id
        settings.WHATSAPP_ENABLED = self.original_enabled

    # ==================== send_whatsapp_message 測試 ====================

    def test_message_disabled_when_not_configured(self):
        """WHATSAPP_ENABLED=False 時不發送"""
        settings.WHATSAPP_TOKEN = ""
        settings.WHATSAPP_PHONE_NUMBER_ID = ""
        settings.WHATSAPP_ENABLED = False

        result = send_whatsapp_message("85298092384", "測試")
        self.assertFalse(result)

    def test_message_fails_without_phone(self):
        """無電話號碼時返回 False"""
        settings.WHATSAPP_ENABLED = True
        settings.WHATSAPP_TOKEN = "test_token_123"
        settings.WHATSAPP_PHONE_NUMBER_ID = "test_phone_id_456"

        result = send_whatsapp_message("", "測試")
        self.assertFalse(result)

    def test_hk_phone_adds_country_code(self):
        """香港 8 位號碼自動補 852 國碼"""
        settings.WHATSAPP_ENABLED = True
        settings.WHATSAPP_TOKEN = "test_token"
        settings.WHATSAPP_PHONE_NUMBER_ID = "test_phone_id"

        with patch('eshop.whatsapp_notifier.requests.post') as mock_post:
            mock_post.return_value = MockResponse()

            send_whatsapp_message("98092384", "測試")

            # 確認 API 呼叫的 to 參數包含 852
            call_args = mock_post.call_args
            call_data = call_args[1]['json']
            self.assertEqual(call_data['to'], "85298092384")

    def test_hk_phone_with_plus_sign(self):
        """含 + 號的號碼正確清理"""
        settings.WHATSAPP_ENABLED = True
        settings.WHATSAPP_TOKEN = "test_token"
        settings.WHATSAPP_PHONE_NUMBER_ID = "test_phone_id"

        with patch('eshop.whatsapp_notifier.requests.post') as mock_post:
            mock_post.return_value = MockResponse()

            send_whatsapp_message("+85298092384", "測試")

            call_args = mock_post.call_args
            call_data = call_args[1]['json']
            self.assertEqual(call_data['to'], "85298092384")

    def test_send_success(self):
        """成功發送返回 True"""
        settings.WHATSAPP_ENABLED = True
        settings.WHATSAPP_TOKEN = "test_token"
        settings.WHATSAPP_PHONE_NUMBER_ID = "test_phone_id"

        with patch('eshop.whatsapp_notifier.requests.post') as mock_post:
            mock_post.return_value = MockResponse()

            result = send_whatsapp_message("85298092384", "測試訊息")
            self.assertTrue(result)

    def test_send_api_error(self):
        """API 返回錯誤時返回 False"""
        settings.WHATSAPP_ENABLED = True
        settings.WHATSAPP_TOKEN = "test_token"
        settings.WHATSAPP_PHONE_NUMBER_ID = "test_phone_id"

        with patch('eshop.whatsapp_notifier.requests.post') as mock_post:
            mock_post.return_value = MockResponse(
                status_code=401,
                json_data={"error": {"message": "Invalid token"}}
            )

            result = send_whatsapp_message("85298092384", "測試")
            self.assertFalse(result)

    def test_send_timeout(self):
        """發送逾時返回 False"""
        settings.WHATSAPP_ENABLED = True
        settings.WHATSAPP_TOKEN = "test_token"
        settings.WHATSAPP_PHONE_NUMBER_ID = "test_phone_id"

        with patch('eshop.whatsapp_notifier.requests.post') as mock_post:
            from requests.exceptions import Timeout
            mock_post.side_effect = Timeout("Connection timed out")

            result = send_whatsapp_message("85298092384", "測試")
            self.assertFalse(result)

    def test_send_network_error(self):
        """網路錯誤返回 False"""
        settings.WHATSAPP_ENABLED = True
        settings.WHATSAPP_TOKEN = "test_token"
        settings.WHATSAPP_PHONE_NUMBER_ID = "test_phone_id"

        with patch('eshop.whatsapp_notifier.requests.post') as mock_post:
            from requests.exceptions import ConnectionError
            mock_post.side_effect = ConnectionError("Connection refused")

            result = send_whatsapp_message("85298092384", "測試")
            self.assertFalse(result)

    def test_api_response_without_messages(self):
        """API 回應無 messages 時返回 False"""
        settings.WHATSAPP_ENABLED = True
        settings.WHATSAPP_TOKEN = "test_token"
        settings.WHATSAPP_PHONE_NUMBER_ID = "test_phone_id"

        with patch('eshop.whatsapp_notifier.requests.post') as mock_post:
            mock_post.return_value = MockResponse(json_data={"error": "some_error"})

            result = send_whatsapp_message("85298092384", "測試")
            self.assertFalse(result)

    def test_message_format(self):
        """確認發送的訊息格式正確"""
        settings.WHATSAPP_ENABLED = True
        settings.WHATSAPP_TOKEN = "test_token"
        settings.WHATSAPP_PHONE_NUMBER_ID = "test_phone_id"

        with patch('eshop.whatsapp_notifier.requests.post') as mock_post:
            mock_post.return_value = MockResponse()

            test_message = "☕ 測試通知"
            send_whatsapp_message("85298092384", test_message)

            call_args = mock_post.call_args
            call_data = call_args[1]['json']

            # 確認 API 端點
            self.assertIn("test_phone_id/messages", call_args[0][0])

            # 確認訊息內容
            self.assertEqual(call_data['type'], "text")
            self.assertEqual(call_data['text']['body'], test_message)

            # 確認 Header 含 Token
            self.assertIn("Authorization", call_args[1]['headers'])
            self.assertIn("test_token", call_args[1]['headers']['Authorization'])

    # ==================== send_order_ready_notification 測試 ====================

    def test_ready_notification_without_phone(self):
        """訂單無電話時跳過通知"""
        order = MagicMock()
        order.id = 999
        order.phone = None

        result = send_order_ready_notification(order)
        self.assertFalse(result)

    def test_ready_notification_with_phone(self):
        """訂單有電話時發送通知"""
        order = MagicMock()
        order.id = 123
        order.phone = "98092384"
        order.contact_name = "測試用戶"
        order.order_number = "O-123"
        order.pickup_code = "A1B2"
        order.user = None

        settings.WHATSAPP_ENABLED = True
        settings.WHATSAPP_TOKEN = "test_token"
        settings.WHATSAPP_PHONE_NUMBER_ID = "test_phone_id"

        with patch('eshop.whatsapp_notifier.requests.post') as mock_post:
            mock_post.return_value = MockResponse()

            result = send_order_ready_notification(order)
            self.assertTrue(result)

            # 確認發送到正確號碼（含國碼）
            call_data = mock_post.call_args[1]['json']
            self.assertEqual(call_data['to'], "85298092384")

            # 確認訊息包含訂單資訊
            body = call_data['text']['body']
            self.assertIn("O-123", body)
            self.assertIn("A1B2", body)
            self.assertIn("測試用戶", body)
            self.assertIn("Between Coffee", body)

    def test_ready_notification_hk_8_digit_phone(self):
        """香港 8 位電話自動補國碼"""
        order = MagicMock()
        order.id = 456
        order.phone = "91234567"
        order.contact_name = "測試"
        order.order_number = None
        order.pickup_code = None
        order.user = None

        settings.WHATSAPP_ENABLED = True
        settings.WHATSAPP_TOKEN = "test_token"
        settings.WHATSAPP_PHONE_NUMBER_ID = "test_phone_id"

        with patch('eshop.whatsapp_notifier.requests.post') as mock_post:
            mock_post.return_value = MockResponse()

            send_order_ready_notification(order)

            call_data = mock_post.call_args[1]['json']
            self.assertEqual(call_data['to'], "85291234567")

    def test_ready_notification_already_has_country_code(self):
        """已有國碼的號碼不會重複添加"""
        order = MagicMock()
        order.id = 789
        order.phone = "85291234567"
        order.contact_name = "測試"
        order.order_number = None
        order.pickup_code = None
        order.user = None

        settings.WHATSAPP_ENABLED = True
        settings.WHATSAPP_TOKEN = "test_token"
        settings.WHATSAPP_PHONE_NUMBER_ID = "test_phone_id"

        with patch('eshop.whatsapp_notifier.requests.post') as mock_post:
            mock_post.return_value = MockResponse()

            send_order_ready_notification(order)

            call_data = mock_post.call_args[1]['json']
            self.assertEqual(call_data['to'], "85291234567")

    def test_ready_notification_uses_order_number(self):
        """訂單編號優先於 ID"""
        order = MagicMock()
        order.id = 111
        order.phone = "85298092384"
        order.contact_name = "測試"
        order.order_number = "BC-001"
        order.pickup_code = "XY99"
        order.user = None

        settings.WHATSAPP_ENABLED = True
        settings.WHATSAPP_TOKEN = "test_token"
        settings.WHATSAPP_PHONE_NUMBER_ID = "test_phone_id"

        with patch('eshop.whatsapp_notifier.requests.post') as mock_post:
            mock_post.return_value = MockResponse()

            send_order_ready_notification(order)

            body = mock_post.call_args[1]['json']['text']['body']
            self.assertIn("BC-001", body)
            self.assertNotIn("#111", body)