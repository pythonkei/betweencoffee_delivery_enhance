# eshop/paypal_utils.py
import logging
import requests
import base64
from django.conf import settings
from django.urls import reverse

logger = logging.getLogger(__name__)

def get_paypal_environment_base_url():
    """获取PayPal环境基础URL"""
    environment = getattr(settings, 'PAYPAL_ENVIRONMENT', 'sandbox')
    logger.info(f"PayPal环境: {environment}")
    if environment == 'live':
        return 'https://api-m.paypal.com'
    else:
        return 'https://api-m.sandbox.paypal.com'

def get_paypal_access_token():
    """获取PayPal访问令牌"""
    try:
        # 验证配置
        if not hasattr(settings, 'PAYPAL_CLIENT_ID') or not settings.PAYPAL_CLIENT_ID:
            logger.error("PAYPAL_CLIENT_ID 未配置")
            return None
        if not hasattr(settings, 'PAYPAL_CLIENT_SECRET') or not settings.PAYPAL_CLIENT_SECRET:
            logger.error("PAYPAL_CLIENT_SECRET 未配置")
            return None
            
        logger.info(f"PayPal Client ID: {settings.PAYPAL_CLIENT_ID[:10]}...")
        
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
        
        # 使用修复的环境检测
        base_url = get_paypal_environment_base_url()
        
        logger.info(f"请求PayPal访问令牌，环境: {settings.PAYPAL_ENVIRONMENT}")
        
        # 发送请求
        response = requests.post(f'{base_url}/v1/oauth2/token', headers=headers, data=data, timeout=30)
        response.raise_for_status()
        
        # 解析响应
        token_data = response.json()
        logger.info("成功获取PayPal访问令牌")
        return token_data['access_token']
        
    except requests.exceptions.RequestException as e:
        logger.error(f"获取PayPal访问令牌网络错误: {str(e)}")
        return None
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
        base_url = get_paypal_environment_base_url()
        
        # 构建回调URL
        return_url = request.build_absolute_uri(reverse('eshop:paypal_callback'))
        cancel_url = request.build_absolute_uri(reverse('eshop:order_confirm'))
        
        logger.info(f"PayPal返回URL: {return_url}")
        logger.info(f"PayPal取消URL: {cancel_url}")
        
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
                        "value": f"{order.total_price:.2f}"
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
        
        logger.info(f"PayPal支付请求数据: {payment_data}")
        
        # 发送创建订单请求
        response = requests.post(
            f'{base_url}/v2/checkout/orders',
            headers=headers,
            json=payment_data,
            timeout=30
        )
        
        logger.info(f"PayPal响应状态: {response.status_code}")
        logger.info(f"PayPal响应内容: {response.text}")
        
        if response.status_code != 201:
            logger.error(f"创建PayPal订单失败: {response.status_code} - {response.text}")
            return None
        
        # 解析响应
        order_data = response.json()
        
        # 查找approval URL
        for link in order_data.get('links', []):
            if link.get('rel') == 'approve':
                approval_url = link.get('href')
                logger.info(f"PayPal批准URL: {approval_url}")
                return approval_url
        
        logger.error("未找到PayPal approval URL")
        return None
        
    except Exception as e:
        logger.error(f"创建PayPal支付失败: {str(e)}")
        return None

def capture_paypal_payment(payment_id):
    """捕获PayPal支付"""
    try:
        access_token = get_paypal_access_token()
        if not access_token:
            logger.error("无法获取PayPal访问令牌")
            return False
        
        base_url = get_paypal_environment_base_url()
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {access_token}',
        }
        
        response = requests.post(
            f'{base_url}/v2/checkout/orders/{payment_id}/capture',
            headers=headers
        )
        
        logger.info(f"PayPal捕获响应状态: {response.status_code}")
        
        if response.status_code != 201:
            logger.error(f"PayPal支付捕获失败: {response.status_code} - {response.text}")
            return False
        
        capture_data = response.json()
        return capture_data.get('status') == 'COMPLETED'
        
    except Exception as e:
        logger.error(f"捕获PayPal支付失败: {str(e)}")
        return False