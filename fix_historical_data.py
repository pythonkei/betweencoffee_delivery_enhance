# fix_historical_data.py
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'betweencoffee_delivery.settings')
django.setup()

from eshop.models import OrderModel, BeanItem, CartItem
from decimal import Decimal
import json

def fix_historical_bean_weights():
    """修复历史订单中咖啡豆的重量字段"""
    print("开始修复历史订单数据...")
    orders = OrderModel.objects.all()
    fixed_count = 0
    
    for order in orders:
        items = order.items
        needs_update = False
        
        if isinstance(items, str):
            items = json.loads(items)
        elif items is None:
            continue
        
        for item in items:
            if item.get('type') == 'bean':
                # 检查weight字段
                weight = item.get('weight')
                if weight not in ['200g', '500g']:
                    # 尝试修复
                    if weight in ['1kg', '1000g']:
                        # 将1kg转换为500g（业务逻辑决定）
                        item['weight'] = '500g'
                        needs_update = True
                        print(f"订单 {order.id}: 将重量从 {weight} 修复为 500g")
                    elif weight is None or weight == '':
                        # 设置默认值
                        item['weight'] = '200g'
                        needs_update = True
                        print(f"订单 {order.id}: 设置默认重量 200g")
                    elif weight not in ['200g', '500g']:
                        # 其他无效值
                        item['weight'] = '200g'
                        needs_update = True
                        print(f"订单 {order.id}: 将无效重量 {weight} 修复为 200g")
        
        if needs_update:
            order.items = items
            order.save(update_fields=['items'])
            fixed_count += 1
    
    print(f"\n修复了 {fixed_count} 个订单的咖啡豆重量字段")
    return fixed_count

def fix_cart_items():
    """修复购物车中的咖啡豆项"""
    print("\n开始修复购物车数据...")
    cart_items = CartItem.objects.filter(product_type='bean')
    fixed_count = 0
    
    for item in cart_items:
        needs_update = False
        
        # 检查weight字段
        if item.weight not in ['200g', '500g']:
            # 尝试修复
            if item.weight in ['1kg', '1000g']:
                item.weight = '500g'
                needs_update = True
                print(f"购物车项 {item.id}: 将重量从 {item.weight} 修复为 500g")
            elif item.weight is None or item.weight == '':
                item.weight = '200g'
                needs_update = True
                print(f"购物车项 {item.id}: 设置默认重量 200g")
            elif item.weight not in ['200g', '500g']:
                item.weight = '200g'
                needs_update = True
                print(f"购物车项 {item.id}: 将无效重量 {item.weight} 修复为 200g")
        
        if needs_update:
            item.save()
            fixed_count += 1
    
    print(f"修复了 {fixed_count} 个购物车项的咖啡豆重量字段")
    return fixed_count

def verify_bean_prices():
    """验证并修复BeanItem价格"""
    print("\n开始验证BeanItem价格...")
    beans = BeanItem.objects.all()
    fixed_count = 0
    
    for bean in beans:
        needs_update = False
        
        # 确保价格是Decimal类型
        if not isinstance(bean.price_200g, Decimal):
            try:
                bean.price_200g = Decimal(str(bean.price_200g))
                needs_update = True
                print(f"Bean {bean.id}: 修复price_200g类型")
            except:
                bean.price_200g = Decimal('0')
                needs_update = True
                print(f"Bean {bean.id}: 设置price_200g默认值0")
        
        if not isinstance(bean.price_500g, Decimal):
            try:
                bean.price_500g = Decimal(str(bean.price_500g))
                needs_update = True
                print(f"Bean {bean.id}: 修复price_500g类型")
            except:
                bean.price_500g = Decimal('0')
                needs_update = True
                print(f"Bean {bean.id}: 设置price_500g默认值0")
        
        if needs_update:
            bean.save()
            fixed_count += 1
    
    print(f"验证了 {beans.count()} 个BeanItem，修复了 {fixed_count} 个")
    return fixed_count

def main():
    """主修复函数"""
    print("="*60)
    print("开始数据修复...")
    print("="*60)
    
    # 备份提醒
    print("⚠️  警告：在执行修复前，请确保已备份数据库！")
    print("是否继续？(输入 'yes' 继续)")
    
    confirmation = input().strip().lower()
    if confirmation != 'yes':
        print("已取消修复操作")
        return
    
    total_fixed = 0
    
    # 修复BeanItem价格类型
    bean_fixed = verify_bean_prices()
    total_fixed += bean_fixed
    
    # 修复订单数据
    order_fixed = fix_historical_bean_weights()
    total_fixed += order_fixed
    
    # 修复购物车数据
    cart_fixed = fix_cart_items()
    total_fixed += cart_fixed
    
    print("\n" + "="*60)
    print("修复完成汇总:")
    print("="*60)
    print(f"修复BeanItem价格类型: {bean_fixed} 个")
    print(f"修复订单重量字段: {order_fixed} 个")
    print(f"修复购物车重量字段: {cart_fixed} 个")
    print(f"总计修复: {total_fixed} 个数据项")
    print("\n✅ 数据修复完成！")
    print("建议运行 check_data_consistency.py 验证修复结果")
    print("="*60)

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"修复过程中出现异常: {e}")
        import traceback
        traceback.print_exc()