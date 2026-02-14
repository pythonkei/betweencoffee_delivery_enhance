"""
支付相关测试
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from eshop.models import OrderModel
import json

User = get_user_model()

class PaymentTestCase(TestCase):
    """支付测试用例"""
    
    def setUp(self):
        """测试设置"""
        self.user = User.objects.create_user(
            username='paymentuser',
            email='payment@example.com',
            password='testpass123'
        )
        
        self.client.force_login(self.user)
        
        # 创建测试订单
        self.order = OrderModel.objects.create(
            user=self.user,
            name='支付测试用户',
            phone='87654321',
            items=json.dumps([{
                'type': 'coffee',
                'id': 1,
                'name': '拿铁咖啡',
                'price': 35.00,
                'quantity': 2,
                'cup_level': 'Large',
                'milk_level': 'Extra'
            }]),
            total_price=70.00,
            payment_status='pending',
            status='pending'
        )
    
    def test_payment_status_flow(self):
        """测试支付状态流程"""
        # 初始状态
        self.assertEqual(self.order.payment_status, 'pending')
        self.assertEqual(self.order.status, 'pending')
        
        # 模拟支付成功
        self.order.payment_status = 'paid'
        self.order.status = 'waiting'  # 支付后进入等待制作状态
        self.order.save()
        
        # 验证状态
        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_status, 'paid')
        self.assertEqual(self.order.status, 'waiting')
        print("✅ 支付状态流程测试通过")
    
    def test_payment_methods(self):
        """测试支付方式"""
        # 测试不同支付方式
        payment_methods = ['alipay', 'paypal', 'fps', 'cash']
        
        for method in payment_methods:
            order = OrderModel.objects.create(
                user=self.user,
                name=f'测试-{method}',
                phone='11111111',
                items=json.dumps([{'type': 'coffee', 'id': 1, 'name': '咖啡', 'price': 25.00, 'quantity': 1}]),
                total_price=25.00,
                payment_status='pending',
                status='pending',
                payment_method=method
            )
            
            self.assertEqual(order.payment_method, method)
            print(f"✅ {method} 支付方式测试通过")
    
    def test_payment_timeout(self):
        """测试支付超时"""
        from django.utils import timezone
        from datetime import timedelta
        
        # 设置支付超时时间
        self.order.set_payment_timeout(minutes=5)
        self.assertIsNotNone(self.order.payment_timeout)
        
        # 测试超时检查
        is_timeout = self.order.is_payment_timeout()
        self.assertFalse(is_timeout)  # 刚设置不应该超时
        
        print("✅ 支付超时测试通过")
    
    def test_payment_attempts(self):
        """测试支付尝试次数"""
        self.assertEqual(self.order.payment_attempts, 0)
        
        # 增加尝试次数
        self.order.increment_payment_attempts()
        self.assertEqual(self.order.payment_attempts, 1)
        
        # 测试是否可以重试支付
        can_retry = self.order.can_retry_payment()
        self.assertTrue(can_retry)
        
        print("✅ 支付尝试次数测试通过")
