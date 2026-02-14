# test_display_consistency.py
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'betweencoffee_delivery.settings')
django.setup()

from django.test import TestCase, Client
from django.urls import reverse
from eshop.models import BeanItem, CoffeeItem, OrderModel
import json
from decimal import Decimal

class DisplayConsistencyTests(TestCase):
    """显示一致性测试"""
    
    def setUp(self):
        self.client = Client()
        
        # 创建测试数据
        self.bean = BeanItem.objects.create(
            name="测试咖啡豆",
            price_200g=Decimal('69.00'),
            price_500g=Decimal('129.00'),
            origin="测试产地",
            description="测试描述",
            is_published=True
        )
        
        self.coffee = CoffeeItem.objects.create(
            name="测试咖啡",
            price=Decimal('45.00'),
            origin="测试产地",
            description="测试描述",
            is_published=True
        )
    
    def test_bean_page_display(self):
        """测试咖啡豆详情页显示"""
        response = self.client.get(reverse('bean_detail', args=[self.bean.id]))
        
        self.assertEqual(response.status_code, 200)
        
        # 检查重量选项
        content = response.content.decode('utf-8')
        
        # 应该包含200g选项
        self.assertIn('200g', content)
        self.assertIn('$69', content)
        
        # 应该包含500g选项
        self.assertIn('500g', content)
        self.assertIn('$129', content)
        
        # 不应该包含1kg
        self.assertNotIn('1kg', content)
        
        print("✅ bean.html 显示测试通过")
    
    def test_coffee_page_display(self):
        """测试咖啡详情页显示"""
        response = self.client.get(reverse('coffee_detail', args=[self.coffee.id]))
        
        self.assertEqual(response.status_code, 200)
        
        content = response.content.decode('utf-8')
        
        # 应该包含杯量选项
        self.assertIn('杯量', content)
        self.assertIn('奶量', content)
        
        print("✅ coffee.html 显示测试通过")
    
    def test_order_confirmation_display_logic(self):
        """测试订单确认页面显示逻辑"""
        # 创建测试订单
        order_data = {
            'items': json.dumps([
                {
                    'type': 'bean',
                    'id': self.bean.id,
                    'name': self.bean.name,
                    'quantity': 1,
                    'weight': '500g',
                    'price': float(self.bean.price_500g),
                    'total_price': float(self.bean.price_500g)
                }
            ]),
            'total_price': float(self.bean.price_500g),
            'order_type': 'normal',
            'is_quick_order': False,
            'pickup_time_choice': '5'
        }
        
        # 模拟订单确认页面逻辑
        order = OrderModel.objects.create(
            items=order_data['items'],
            total_price=order_data['total_price'],
            order_type=order_data['order_type'],
            is_quick_order=order_data['is_quick_order'],
            pickup_time_choice=order_data['pickup_time_choice']
        )
        
        # 测试纯咖啡豆订单
        self.assertTrue(order.is_beans_only())
        self.assertEqual(order.get_pickup_time_display(), "隨時可取")
        
        # 测试订单类型显示
        self.assertEqual(order.get_order_type_display(), "純咖啡豆訂單")
        
        print("✅ 订单确认页面显示逻辑测试通过")

def main():
    """运行显示一致性测试"""
    print("="*60)
    print("开始显示一致性测试...")
    print("="*60)
    
    try:
        # 创建测试实例
        tester = DisplayConsistencyTests()
        tester.setUp()
        
        # 运行测试
        tester.test_bean_page_display()
        tester.test_coffee_page_display()
        tester.test_order_confirmation_display_logic()
        
        print("\n" + "="*60)
        print("🎉 所有显示一致性测试通过！")
        print("="*60)
        return 0
        
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    except Exception as e:
        print(f"\n❌ 测试过程中出现异常: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())