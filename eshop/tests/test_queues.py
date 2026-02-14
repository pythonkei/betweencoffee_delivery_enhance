"""
队列系统测试
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from eshop.models import OrderModel, CoffeeQueue
import json

User = get_user_model()

class QueueTestCase(TestCase):
    """队列测试用例"""
    
    def setUp(self):
        """测试设置"""
        self.user = User.objects.create_user(
            username='queueuser',
            email='queue@example.com',
            password='testpass123'
        )
        
        # 创建包含咖啡的订单
        self.coffee_order = OrderModel.objects.create(
            user=self.user,
            name='队列测试用户',
            phone='33333333',
            items=json.dumps([{
                'type': 'coffee',
                'id': 1,
                'name': '美式咖啡',
                'price': 25.00,
                'quantity': 1,
                'cup_level': 'Medium',
                'milk_level': 'Medium'
            }]),
            total_price=25.00,
            payment_status='paid',
            status='waiting'
        )
        
        # 创建纯咖啡豆订单
        self.beans_order = OrderModel.objects.create(
            user=self.user,
            name='咖啡豆订单',
            phone='44444444',
            items=json.dumps([{
                'type': 'bean',
                'id': 1,
                'name': '哥伦比亚咖啡豆',
                'price': 100.00,
                'quantity': 1,
                'weight': '200g',
                'grinding_level': 'Medium'
            }]),
            total_price=100.00,
            payment_status='paid',
            status='waiting'
        )
    
    def test_order_type_detection(self):
        """测试订单类型检测"""
        # 咖啡订单应该包含咖啡
        self.assertTrue(self.coffee_order.has_coffee())
        self.assertFalse(self.coffee_order.is_beans_only())
        
        # 咖啡豆订单不应该包含咖啡
        self.assertFalse(self.beans_order.has_coffee())
        self.assertTrue(self.beans_order.is_beans_only())
        
        print("✅ 订单类型检测测试通过")
    
    def test_queue_eligibility(self):
        """测试队列资格"""
        from eshop.order_status_manager import OrderStatusManager
        
        # 咖啡订单应该可以加入队列
        coffee_manager = OrderStatusManager(self.coffee_order)
        self.assertTrue(coffee_manager.should_add_to_queue())
        
        # 纯咖啡豆订单不应该加入队列
        beans_manager = OrderStatusManager(self.beans_order)
        self.assertFalse(beans_manager.should_add_to_queue())
        
        print("✅ 队列资格测试通过")
    
    def test_estimated_time_calculation(self):
        """测试预计时间计算"""
        # 咖啡订单应该有预计时间
        estimated_time = self.coffee_order.calculate_estimated_ready_time()
        self.assertIsNotNone(estimated_time)
        
        # 纯咖啡豆订单不应该有预计时间
        beans_estimated_time = self.beans_order.calculate_estimated_ready_time()
        self.assertIsNone(beans_estimated_time)
        
        print("✅ 预计时间计算测试通过")
