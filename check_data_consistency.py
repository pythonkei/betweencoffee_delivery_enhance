# check_data_consistency.py
import os
import sys
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'betweencoffee_delivery.settings')
django.setup()

from eshop.models import BeanItem, OrderModel, CartItem
from cart.cart import Cart
from django.contrib.auth.models import User
from decimal import Decimal

def check_bean_items():
    """检查所有BeanItem的价格字段"""
    print("=== 检查BeanItem数据 ===")
    beans = BeanItem.objects.all()
    
    issues_found = False
    
    for bean in beans:
        print(f"\n检查: {bean.name} (ID: {bean.id})")
        
        # 检查price_200g
        if bean.price_200g is None or bean.price_200g == 0:
            print(f"  ❌ price_200g 为空或为0")
            issues_found = True
        else:
            print(f"  ✅ price_200g: ${bean.price_200g}")
        
        # 检查price_500g
        if bean.price_500g is None or bean.price_500g == 0:
            print(f"  ❌ price_500g 为空或为0")
            issues_found = True
        else:
            print(f"  ✅ price_500g: ${bean.price_500g}")
        
        # 验证get_price方法
        try:
            price_200g = bean.get_price('200g')
            price_500g = bean.get_price('500g')
            print(f"  ✅ get_price('200g'): ${price_200g}")
            print(f"  ✅ get_price('500g'): ${price_500g}")
            
            # 验证价格合理性
            if price_500g <= price_200g:
                print(f"  ⚠️  500g价格({price_500g})应大于200g价格({price_200g})")
                issues_found = True
        except Exception as e:
            print(f"  ❌ get_price方法错误: {e}")
            issues_found = True
    
    print(f"\n总计检查了 {beans.count()} 个BeanItem")
    return not issues_found

def check_orders_consistency():
    """检查订单中咖啡豆价格的一致性"""
    print("\n" + "="*50)
    print("=== 检查订单数据 ===")
    orders = OrderModel.objects.all()
    
    issues_found = False
    checked_count = 0
    bean_orders_count = 0
    
    for order in orders:
        items = order.get_items()
        has_bean_items = False
        
        for item in items:
            if item.get('type') == 'bean':
                has_bean_items = True
                bean_orders_count += 1
                
                # 检查weight字段
                weight = item.get('weight')
                if weight not in ['200g', '500g']:
                    print(f"订单 {order.id} 中的咖啡豆重量字段异常: {weight}")
                    issues_found = True
                
                # 检查price字段是否合理
                price = item.get('price', 0)
                if price == 0:
                    print(f"订单 {order.id} 中的咖啡豆价格为0")
                    issues_found = True
                
                # 检查商品是否存在
                try:
                    bean = BeanItem.objects.get(id=item['id'])
                    # 验证价格是否与当前商品价格一致
                    if weight == '200g' and float(price) != float(bean.price_200g):
                        print(f"订单 {order.id} 中200g价格不匹配: 订单${price} vs 当前${bean.price_200g}")
                    elif weight == '500g' and float(price) != float(bean.price_500g):
                        print(f"订单 {order.id} 中500g价格不匹配: 订单${price} vs 当前${bean.price_500g}")
                except BeanItem.DoesNotExist:
                    print(f"订单 {order.id} 中的咖啡豆(ID:{item['id']})不存在")
        
        if has_bean_items:
            checked_count += 1
    
    print(f"\n检查了 {checked_count} 个包含咖啡豆的订单")
    print(f"发现 {bean_orders_count} 个咖啡豆商品项")
    return not issues_found

def check_cart_items():
    """检查购物车中的咖啡豆项"""
    print("\n" + "="*50)
    print("=== 检查购物车数据 ===")
    
    cart_items = CartItem.objects.filter(product_type='bean')
    print(f"发现 {cart_items.count()} 个购物车中的咖啡豆项")
    
    issues_found = False
    
    for item in cart_items:
        # 检查weight字段
        if item.weight not in ['200g', '500g']:
            print(f"购物车项 {item.id} 重量字段异常: {item.weight}")
            issues_found = True
        
        # 检查对应的商品是否存在
        try:
            bean = BeanItem.objects.get(id=item.product_id)
            # 验证重量选择是否有效
            if item.weight not in ['200g', '500g']:
                print(f"购物车项 {item.id} 有无效的重量: {item.weight}")
                issues_found = True
        except BeanItem.DoesNotExist:
            print(f"购物车项 {item.id} 对应的咖啡豆(ID:{item.product_id})不存在")
            issues_found = True
    
    return not issues_found

def check_price_calculation():
    """验证价格计算逻辑"""
    print("\n" + "="*50)
    print("=== 验证价格计算逻辑 ===")
    
    issues_found = False
    
    # 测试几个BeanItem的价格计算
    beans = BeanItem.objects.all()[:3]  # 测试前3个
    
    for bean in beans:
        print(f"\n测试 Bean: {bean.name}")
        
        # 测试get_price方法
        try:
            price_200g = bean.get_price('200g')
            price_500g = bean.get_price('500g')
            
            print(f"  get_price('200g'): ${price_200g}")
            print(f"  get_price('500g'): ${price_500g}")
            
            # 验证类型
            if not isinstance(price_200g, Decimal):
                print(f"  ❌ get_price('200g') 返回类型错误: {type(price_200g)}")
                issues_found = True
            
            if not isinstance(price_500g, Decimal):
                print(f"  ❌ get_price('500g') 返回类型错误: {type(price_500g)}")
                issues_found = True
                
        except Exception as e:
            print(f"  ❌ get_price 方法失败: {e}")
            issues_found = True
    
    return not issues_found

def main():
    """主检查函数"""
    print("="*60)
    print("开始数据一致性检查...")
    print("="*60)
    
    all_passed = True
    
    # 检查BeanItem
    bean_ok = check_bean_items()
    if not bean_ok:
        all_passed = False
    
    # 检查订单
    orders_ok = check_orders_consistency()
    if not orders_ok:
        all_passed = False
    
    # 检查购物车
    cart_ok = check_cart_items()
    if not cart_ok:
        all_passed = False
    
    # 检查价格计算
    price_ok = check_price_calculation()
    if not price_ok:
        all_passed = False
    
    print("\n" + "="*60)
    print("检查结果汇总:")
    print("="*60)
    print(f"BeanItem数据: {'✅ 通过' if bean_ok else '❌ 发现问题'}")
    print(f"订单数据: {'✅ 通过' if orders_ok else '❌ 发现问题'}")
    print(f"购物车数据: {'✅ 通过' if cart_ok else '❌ 发现问题'}")
    print(f"价格计算逻辑: {'✅ 通过' if price_ok else '❌ 发现问题'}")
    print("-"*60)
    
    if all_passed:
        print("🎉 所有数据一致性检查通过！")
        print("="*60)
        return 0
    else:
        print("⚠️  发现数据一致性问题，请查看上方详情进行修复")
        print("="*60)
        return 1

if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as e:
        print(f"检查过程中出现异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)