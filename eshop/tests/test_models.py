"""
OrderModel 模型测试
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from eshop.models import OrderModel
import json
import warnings

User = get_user_model()

class OrderModelTestCase(TestCase):
    """OrderModel 测试用例"""
    
    def setUp(self):
        """测试设置"""
        # 创建测试用户
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # 创建测试订单数据
        self.order_data = {
            'name': '测试用户',
            'phone': '12345678',
            'items': json.dumps([{
                'type': 'coffee',
                'id': 1,
                'name': '测试咖啡',
                'price': 30.00,
                'quantity': 1,
                'cup_level': 'Medium',
                'milk_level': 'Medium'
            }]),
            'total_price': 30.00,
            'payment_status': 'pending',
            'status': 'pending'
        }
    
    def test_order_creation(self):
        """测试订单创建"""
        order = OrderModel.objects.create(
            user=self.user,
            **self.order_data
        )
        
        self.assertIsNotNone(order.id)
        self.assertEqual(order.name, '测试用户')
        self.assertEqual(order.payment_status, 'pending')
        self.assertEqual(order.status, 'pending')
        print("✅ 订单创建测试通过")
    
    def test_payment_status(self):
        """测试支付状态字段"""
        order = OrderModel.objects.create(
            user=self.user,
            **self.order_data
        )
        
        # 测试 payment_status 字段
        self.assertEqual(order.payment_status, 'pending')
        
        # 测试 is_paid 属性（应该触发弃用警告）
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            is_paid = order.is_paid
            self.assertFalse(is_paid)
            self.assertTrue(len(w) > 0)  # 应该触发警告
            print("✅ is_paid 弃用警告测试通过")
        
        # 更新支付状态
        order.payment_status = 'paid'
        order.save()
        
        self.assertEqual(order.payment_status, 'paid')
        
        # 再次测试 is_paid 属性
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            self.assertTrue(order.is_paid)
        
        print("✅ 支付状态测试通过")
    
    def test_removed_fields(self):
        """测试已移除字段"""
        order = OrderModel.objects.create(
            user=self.user,
            **self.order_data
        )
        
        # 检查已移除字段不应存在于数据库模型中
        field_names = [f.name for f in order._meta.get_fields()]
        
        # 这些字段应该不存在
        removed_fields = ['is_paid', 'created_on', 'cup_size', 'pickup_time']
        for field in removed_fields:
            self.assertNotIn(field, field_names)
            print(f"✅ {field} 字段已移除")
    
    def test_backward_compatibility(self):
        """测试向后兼容性"""
        order = OrderModel.objects.create(
            user=self.user,
            **self.order_data
        )
        
        # 测试弃用属性的访问
        deprecated_properties = ['is_paid', 'created_on', 'cup_size', 'pickup_time']
        
        for prop in deprecated_properties:
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                value = getattr(order, prop)
                self.assertTrue(len(w) > 0, f"{prop} 应该触发弃用警告")
                print(f"✅ {prop} 向后兼容性测试通过")
