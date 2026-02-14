"""
全面的订单功能测试
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from eshop.models import OrderModel
from eshop.order_status_manager import OrderStatusManager
import json
import warnings

User = get_user_model()

class ComprehensiveOrderTestCase(TestCase):
    """全面的订单测试"""
    
    def setUp(self):
        """测试设置"""
        self.user = User.objects.create_user(
            username='comprehensive_user',
            email='comp@example.com',
            password='testpass123'
        )
    
    def test_order_lifecycle(self):
        """测试订单完整生命周期"""
        print("\n=== 测试订单生命周期 ===")
        
        # 1. 创建订单
        order_data = {
            'user': self.user,
            'name': '生命周期测试',
            'phone': '55555555',
            'items': json.dumps([{
                'type': 'coffee',
                'id': 1,
                'name': '测试咖啡',
                'price': 30.00,
                'quantity': 2,
                'cup_level': 'Medium',
                'milk_level': 'Medium'
            }]),
            'total_price': 60.00,
            'payment_status': 'pending',
            'status': 'pending'
        }
        
        order = OrderModel.objects.create(**order_data)
        print(f"✅ 1. 订单创建: #{order.id}")
        
        # 2. 支付成功
        order.payment_status = 'paid'
        order.status = 'waiting'
        order.save()
        
        self.assertEqual(order.payment_status, 'paid')
        self.assertEqual(order.status, 'waiting')
        print(f"✅ 2. 支付成功: 状态={order.status}")
        
        # 3. 检查 OrderStatusManager
        manager = OrderStatusManager(order)
        display_status = manager.get_display_status()
        self.assertIn('progress_percentage', display_status)
        print(f"✅ 3. OrderStatusManager 工作正常: 进度={display_status['progress_percentage']}%")
        
        # 4. 检查弃用字段访问
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            is_paid = order.is_paid
            self.assertTrue(is_paid)
            self.assertTrue(len(w) > 0)
            print(f"✅ 4. 弃用字段访问正常并触发警告")
        
        # 5. 测试订单类型分析
        order_type = order.get_order_type_summary()
        self.assertTrue(order_type['has_coffee'])
        print(f"✅ 5. 订单类型分析: {order_type}")
        
        print("🎉 订单生命周期测试完成！")
    
    def test_payment_status_transitions(self):
        """测试支付状态转换"""
        print("\n=== 测试支付状态转换 ===")
        
        status_transitions = [
            ('pending', '待支付'),
            ('paid', '已支付'),
            ('cancelled', '已取消'),
        ]
        
        for status_code, status_name in status_transitions:
            order = OrderModel.objects.create(
                user=self.user,
                name=f'状态测试-{status_name}',
                phone='66666666',
                items=json.dumps([{'type': 'coffee', 'id': 1, 'name': '咖啡', 'price': 25.00, 'quantity': 1}]),
                total_price=25.00,
                payment_status=status_code,
                status='pending'
            )
            
            # 测试显示文本
            display_text = order.get_payment_status_display()
            self.assertIsNotNone(display_text)
            print(f"✅ {status_name}: 显示文本='{display_text}'")
            
            # 测试徽章颜色
            badge = order.payment_status_badge
            self.assertIsNotNone(badge)
            print(f"  徽章颜色: {badge}")
    
    def test_order_display_methods(self):
        """测试订单显示方法"""
        print("\n=== 测试订单显示方法 ===")
        
        order = OrderModel.objects.create(
            user=self.user,
            name='显示方法测试',
            phone='77777777',
            items=json.dumps([{
                'type': 'coffee',
                'id': 1,
                'name': '卡布奇诺',
                'price': 35.00,
                'quantity': 1,
                'cup_level': 'Large',
                'milk_level': 'Extra'
            }]),
            total_price=35.00,
            payment_status='paid',
            status='preparing'
        )
        
        # 测试各种显示方法
        methods_to_test = [
            ('get_status_display', '状态显示'),
            ('get_payment_status_display', '支付状态显示'),
            ('get_order_type_display', '订单类型显示'),
            ('get_preparation_time_display', '制作时间显示'),
        ]
        
        for method_name, description in methods_to_test:
            method = getattr(order, method_name)
            result = method()
            self.assertIsNotNone(result)
            print(f"✅ {description}: {result}")
        
        print("所有显示方法测试完成！")

