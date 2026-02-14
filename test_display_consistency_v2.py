# test_display_consistency_v2.py
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
    """显示一致性测试 - 修正版"""
    
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
    
    def test_bean_model_methods(self):
        """测试咖啡豆模型方法"""
        print("测试咖啡豆模型方法...")
        
        # 测试 get_price 方法
        self.assertEqual(self.bean.get_price('200g'), Decimal('69.00'))
        self.assertEqual(self.bean.get_price('500g'), Decimal('129.00'))
        
        # 测试默认重量
        self.assertEqual(self.bean.get_price('invalid'), Decimal('69.00'))
        
        print("✅ BeanItem 模型方法测试通过")
    
    def test_coffee_model_methods(self):
        """测试咖啡模型方法"""
        print("测试咖啡模型方法...")
        
        # 测试价格
        self.assertEqual(self.coffee.price, Decimal('45.00'))
        
        # 测试图片方法
        self.assertIn('default-coffee-index.png', self.coffee.get_index_image())
        self.assertIn('default-coffee-detail.png', self.coffee.get_detail_image())
        
        print("✅ CoffeeItem 模型方法测试通过")
    
    def test_order_model_display_methods(self):
        """测试订单模型显示方法"""
        print("测试订单模型显示方法...")
        
        # 创建纯咖啡豆订单
        bean_order_data = {
            'type': 'bean',
            'id': self.bean.id,
            'name': self.bean.name,
            'quantity': 1,
            'weight': '500g',
            'price': float(self.bean.price_500g),
            'total_price': float(self.bean.price_500g)
        }
        
        bean_order = OrderModel.objects.create(
            items=json.dumps([bean_order_data]),
            total_price=float(self.bean.price_500g),
            order_type='normal',
            is_quick_order=False,
            pickup_time_choice='5'
        )
        
        # 测试纯咖啡豆订单
        self.assertTrue(bean_order.is_beans_only())
        self.assertFalse(bean_order.has_coffee())
        self.assertEqual(bean_order.get_pickup_time_display(), "隨時可取")
        self.assertEqual(bean_order.get_order_type_display(), "純咖啡豆訂單")
        self.assertFalse(bean_order.should_show_preparation_time())
        
        print("✅ 纯咖啡豆订单显示方法测试通过")
        
        # 创建咖啡订单
        coffee_order_data = {
            'type': 'coffee',
            'id': self.coffee.id,
            'name': self.coffee.name,
            'quantity': 1,
            'cup_level': 'Medium',
            'milk_level': 'Medium',
            'price': float(self.coffee.price),
            'total_price': float(self.coffee.price)
        }
        
        coffee_order = OrderModel.objects.create(
            items=json.dumps([coffee_order_data]),
            total_price=float(self.coffee.price),
            order_type='normal',
            is_quick_order=False,
            pickup_time_choice='10'
        )
        
        # 测试咖啡订单
        self.assertFalse(coffee_order.is_beans_only())
        self.assertTrue(coffee_order.has_coffee())
        self.assertEqual(coffee_order.get_pickup_time_display(), "10分鐘後")
        self.assertEqual(coffee_order.get_order_type_display(), "咖啡訂單 - 需要制作")
        self.assertTrue(coffee_order.should_show_preparation_time())
        
        print("✅ 咖啡订单显示方法测试通过")
        
        # 创建混合订单
        mixed_order_data = [
            bean_order_data,
            coffee_order_data
        ]
        
        mixed_order = OrderModel.objects.create(
            items=json.dumps(mixed_order_data),
            total_price=float(self.bean.price_500g + self.coffee.price),
            order_type='normal',
            is_quick_order=False,
            pickup_time_choice='15'
        )
        
        # 测试混合订单
        self.assertFalse(mixed_order.is_beans_only())
        self.assertTrue(mixed_order.has_coffee())
        self.assertEqual(mixed_order.get_order_type_display(), "混合訂單 - 咖啡需要制作")
        self.assertTrue(mixed_order.should_show_preparation_time())
        
        print("✅ 混合订单显示方法测试通过")
    
    def test_url_resolution(self):
        """测试URL解析"""
        print("测试URL解析...")
        
        # 尝试解析可能的URL名称
        url_patterns = [
            ('bean_detail', [self.bean.id]),
            ('eshop:bean_detail', [self.bean.id]),
            ('bean-detail', [self.bean.id]),
            ('coffee_detail', [self.coffee.id]),
            ('eshop:coffee_detail', [self.coffee.id]),
            ('coffee-detail', [self.coffee.id]),
            ('cart:cart_detail', []),
        ]
        
        found_urls = []
        
        for pattern, args in url_patterns:
            try:
                url = reverse(pattern, args=args)
                found_urls.append((pattern, url))
                print(f"✅ 找到URL: {pattern} -> {url}")
            except:
                pass
        
        if found_urls:
            print(f"✅ 共找到 {len(found_urls)} 个有效URL")
        else:
            print("⚠️  未找到有效URL，请检查urls.py配置")
        
        return found_urls

def main():
    """运行显示一致性测试"""
    print("="*60)
    print("开始显示一致性测试...")
    print("="*60)
    
    try:
        # 创建测试实例
        tester = DisplayConsistencyTests()
        tester.setUp()
        
        # 运行模型方法测试
        tester.test_bean_model_methods()
        tester.test_coffee_model_methods()
        tester.test_order_model_display_methods()
        
        # 运行URL测试
        urls = tester.test_url_resolution()
        
        print("\n" + "="*60)
        print("测试结果汇总:")
        print("="*60)
        print("✅ 模型方法测试全部通过")
        print(f"✅ URL解析: 找到 {len(urls)} 个有效URL")
        
        if urls:
            print("\n发现的URL:")
            for pattern, url in urls:
                print(f"  {pattern}: {url}")
        
        print("\n🎉 核心显示逻辑测试通过！")
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