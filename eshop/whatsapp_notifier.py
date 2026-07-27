# eshop/whatsapp_notifier.py
"""
WhatsApp Cloud API 通知模組。
透過 Meta WhatsApp Cloud API 發送訂單狀態通知給客戶。
"""

import logging
from django.conf import settings

import requests

logger = logging.getLogger(__name__)

# API 基礎 URL
WHATSAPP_API_BASE = "https://graph.facebook.com/v18.0"


def send_whatsapp_message(to_phone: str, message: str) -> bool:
    """
    透過 WhatsApp Cloud API 發送文字訊息。

    Args:
        to_phone: 接收號碼，格式如 '8526xxxxxxx'（不含 + 號）
        message: 要發送的訊息內容

    Returns:
        bool: 是否發送成功
    """
    # 檢查是否已配置 WhatsApp
    if not settings.WHATSAPP_ENABLED:
        logger.debug("WhatsApp 通知未啟用（WHATSAPP_ENABLED=False），跳過")
        return False

    if not to_phone:
        logger.warning("WhatsApp 發送失敗：未提供電話號碼")
        return False

    # 清理電話號碼格式（移除 + 號和空格）
    to_phone = to_phone.strip().lstrip("+").replace(" ", "").replace("-", "")

    # 🔧 修復：香港本地號碼（8 位數字）自動加上 852 國碼
    if to_phone.isdigit() and len(to_phone) == 8:
        to_phone = "852" + to_phone
        logger.info(f"📞 自動補上香港國碼: 852...{to_phone[-4:]}")

    url = f"{WHATSAPP_API_BASE}/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"

    headers = {
        "Authorization": f"Bearer {settings.WHATSAPP_TOKEN}",
        "Content-Type": "application/json",
    }

    data = {
        "messaging_product": "whatsapp",
        "to": to_phone,
        "type": "text",
        "text": {"body": message},
    }

    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)
        response.raise_for_status()
        result = response.json()

        if result.get("messages"):
            logger.info(
                f"✅ WhatsApp 訊息已成功發送至 {to_phone} "
                f"(msg_id: {result['messages'][0]['id']})"
            )
            return True
        else:
            logger.warning(
                f"WhatsApp 發送回應異常: {result}"
            )
            return False

    except requests.exceptions.Timeout:
        logger.error(f"WhatsApp 發送逾時: {to_phone}")
        return False
    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code if e.response is not None else "N/A"
        error_detail = ""
        if e.response is not None:
            try:
                error_detail = e.response.json()
            except Exception:
                error_detail = e.response.text[:500]
        logger.error(
            f"WhatsApp API HTTP 錯誤 [{status_code}]: {error_detail}"
        )
        return False
    except requests.exceptions.RequestException as e:
        logger.error(f"WhatsApp 發送請求失敗: {e}")
        return False
    except Exception as e:
        logger.error(f"WhatsApp 發送未知錯誤: {e}")
        return False


def send_order_ready_notification(order) -> bool:
    """
    發送訂單已就緒（ready）通知。

    當訂單狀態變為 ready 時，通知客戶前來取餐。

    Args:
        order: OrderModel 實例

    Returns:
        bool: 是否發送成功
    """
    # 檢查客戶是否有電話號碼
    phone = getattr(order, "phone", None)
    if not phone:
        logger.info(
            f"訂單 #{order.id} 跳過 WhatsApp 通知：客戶未提供電話號碼"
        )
        return False

    # 取得客戶名稱
    customer_name = (
        getattr(order, "contact_name", None)
        or getattr(order.user, "username", None)
        or "顧客"
    )

    # 取得取餐資訊
    order_number = getattr(order, "order_number", None) or f"#{order.id}"
    pickup_code = getattr(order, "pickup_code", None)

    # 組成通知訊息
    message = (
        f"☕ Between Coffee 取餐通知\n\n"
        f"{customer_name} 您好！\n"
        f"您的訂單 {order_number} 已準備就緒 🎉\n\n"
        f"📋 訂單編號: {order_number}"
    )

    if pickup_code:
        message += f"\n🔑 取餐碼: {pickup_code}"

    message += (
        f"\n\n請到店鋪取餐，我們期待為您服務！\n"
        f"🕐 建議在 10 分鐘內取餐以保持最佳風味\n\n"
        f"— Between Coffee ☕"
    )

    return send_whatsapp_message(phone, message)