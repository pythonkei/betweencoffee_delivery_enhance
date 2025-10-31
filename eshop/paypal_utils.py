# eshop/paypal_utils.py
import logging
import requests
import base64
from django.conf import settings
from django.urls import reverse

logger = logging.getLogger(__name__)


def get_paypal_access_token():
    """获取PayPal访问令牌"""
    try:
        # 构建认证头
        auth_string = f"{settings.PAYPAL_CLIENT_ID}:{settings.PAYPAL_CLIENT_SECRET}"
        auth_bytes = auth_string.encode('ascii')
        base64_auth = base64.b64encode(auth_bytes).decode('ascii')
        
        # 请求头
        headers = {
            'Authorization': f'Basic {base64_auth}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        # 请求体
        data = {'grant_type': 'client_credentials'}
        
        # 确定API端点（沙箱或生产环境）
        base_url = 'https://api-m.sandbox.paypal.com' if settings.PAYPAL_ENVIRONMENT == 'sandbox' else 'https://api-m.paypal.com'
        
        # 发送请求
        response = requests.post(f'{base_url}/v1/oauth2/token', headers=headers, data=data)
        response.raise_for_status()
        
        # 解析响应
        token_data = response.json()
        return token_data['access_token']
        
    except Exception as e:
        logger.error(f"获取PayPal访问令牌失败: {str(e)}")
        return None


def create_paypal_payment(order, request):
    """创建PayPal支付订单"""
    try:
        access_token = get_paypal_access_token()
        if not access_token:
            logger.error("无法获取PayPal访问令牌")
            return None
        
        # 确定API端点
        base_url = 'https://api-m.sandbox.paypal.com' if settings.PAYPAL_ENVIRONMENT == 'sandbox' else 'https://api-m.paypal.com'
        
        # 构建回调URL
        return_url = request.build_absolute_uri(reverse('eshop:paypal_callback'))
        cancel_url = request.build_absolute_uri(reverse('eshop:order_confirm'))
        
        # 请求头
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {access_token}',
            'Prefer': 'return=representation'
        }
        
        # 请求数据
        payment_data = {
            "intent": "CAPTURE",
            "purchase_units": [
                {
                    "reference_id": str(order.id),
                    "amount": {
                        "currency_code": "HKD",
                        "value": str(order.total_price)
                    },
                    "description": f"Between Coffee Order #{order.id}"
                }
            ],
            "application_context": {
                "brand_name": "Between Coffee",
                "locale": "zh-HK",
                "landing_page": "BILLING",
                "user_action": "PAY_NOW",
                "return_url": return_url,
                "cancel_url": cancel_url
            }
        }
        
        # 发送创建订单请求
        response = requests.post(
            f'{base_url}/v2/checkout/orders',
            headers=headers,
            json=payment_data
        )
        
        if response.status_code != 201:
            logger.error(f"创建PayPal订单失败: {response.status_code} - {response.text}")
            return None
        
        # 解析响应
        order_data = response.json()
        
        # 查找approval URL
        for link in order_data.get('links', []):
            if link.get('rel') == 'approve':
                return link.get('href')
        
        logger.error("未找到PayPal approval URL")
        return None
        
    except Exception as e:
        logger.error(f"创建PayPal支付失败: {str(e)}")
        return None


def capture_paypal_payment(payment_id):
    """捕获PayPal支付 - 简化版本"""
    try:
        access_token = get_paypal_access_token()
        if not access_token:
            logger.error("无法获取PayPal访问令牌")
            return False
        
        base_url = 'https://api-m.sandbox.paypal.com' if settings.PAYPAL_ENVIRONMENT == 'sandbox' else 'https://api-m.paypal.com'
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {access_token}',
        }
        
        response = requests.post(
            f'{base_url}/v2/checkout/orders/{payment_id}/capture',
            headers=headers
        )
        
        if response.status_code != 201:
            logger.error(f"PayPal支付捕获失败: {response.status_code}")
            return False
        
        capture_data = response.json()
        return capture_data.get('status') == 'COMPLETED'
        
    except Exception as e:
        logger.error(f"捕获PayPal支付失败: {str(e)}")
        return False


# 删除重复的函数定义，只保留一个 capture_paypal_payment
# 注意：原文件中有两个同名的 capture_paypal_payment 函数，我已将其合并