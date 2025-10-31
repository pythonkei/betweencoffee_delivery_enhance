from django.core.management.base import BaseCommand
from django.conf import settings
import requests
import base64
import json

class Command(BaseCommand):
    help = '测试PayPal集成'
    
    def handle(self, *args, **options):
        self.stdout.write('正在测试PayPal集成...')
        
        # 获取访问令牌
        try:
            auth_string = f"{settings.PAYPAL_CLIENT_ID}:{settings.PAYPAL_CLIENT_SECRET}"
            auth_bytes = auth_string.encode('ascii')
            base64_auth = base64.b64encode(auth_bytes).decode('ascii')
            
            headers = {
                'Authorization': f'Basic {base64_auth}',
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            data = {'grant_type': 'client_credentials'}
            
            base_url = 'https://api-m.sandbox.paypal.com' if settings.PAYPAL_ENVIRONMENT == 'sandbox' else 'https://api-m.paypal.com'
            
            # 发送请求获取令牌
            response = requests.post(f'{base_url}/v1/oauth2/token', headers=headers, data=data)
            
            if response.status_code == 200:
                self.stdout.write(self.style.SUCCESS('✅ PayPal访问令牌获取成功'))
                token_data = response.json()
                access_token = token_data['access_token']
                self.stdout.write(f'令牌前缀: {access_token[:20]}...')
                
                # 测试创建订单功能（而不是测试/v1/health）
                self.test_order_creation(access_token, base_url)
            else:
                self.stdout.write(self.style.ERROR(f'❌ 获取访问令牌失败: {response.status_code}'))
                self.stdout.write(f'响应内容: {response.text}')
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ 测试过程中发生异常: {str(e)}'))
    
    def test_order_creation(self, access_token, base_url):
        """测试创建PayPal订单"""
        try:
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {access_token}',
                'Prefer': 'return=representation'
            }
            
            # 创建测试订单
            order_data = {
                "intent": "CAPTURE",
                "purchase_units": [
                    {
                        "amount": {
                            "currency_code": "HKD",
                            "value": "10.00"
                        },
                        "description": "测试订单 - Between Coffee"
                    }
                ],
                "application_context": {
                    "brand_name": "Between Coffee",
                    "user_action": "PAY_NOW"
                }
            }
            
            response = requests.post(
                f'{base_url}/v2/checkout/orders',
                headers=headers,
                json=order_data
            )
            
            if response.status_code == 201:
                self.stdout.write(self.style.SUCCESS('✅ PayPal订单创建测试成功'))
                order_info = response.json()
                self.stdout.write(f"订单ID: {order_info['id']}")
                self.stdout.write(f"订单状态: {order_info['status']}")
                
                # 查找批准链接
                for link in order_info.get('links', []):
                    if link.get('rel') == 'approve':
                        self.stdout.write(f"批准链接: {link.get('href')}")
                        break
            else:
                self.stdout.write(self.style.WARNING(f'⚠️ 订单创建失败，状态码: {response.status_code}'))
                self.stdout.write(f"响应内容: {response.text}")
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ 订单创建测试失败: {str(e)}'))