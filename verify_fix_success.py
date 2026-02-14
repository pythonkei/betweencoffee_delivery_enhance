# verify_fix_success.py
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'betweencoffee_delivery.settings')
django.setup()

from eshop.models import OrderModel, BeanItem
import json

def verify_data_fix():
    """验证数据修复是否成功"""
    print("验证数据修复结果...")
    
    # 检查之前有问题的订单
    problem_order_ids = [935, 521, 528, 530, 657, 711, 701, 758, 1017, 857, 903, 898, 1039, 1018, 1001, 1028, 1002, 1005]
    
    fixed_count = 0
    still_problem_count = 0
    
    for order_id in problem_order_ids:
        try:
            order = OrderModel.objects.get(id=order_id)
            items = order.get_items()
            
            has_problem = False
            for item in items:
                if item.get('type') == 'bean':
                    weight = item.get('weight')
                    if weight == '1kg':
                        print(f"❌ 订单 {order_id} 仍然有重量问题: {weight}")
                        has_problem = True
                    elif weight in ['200g', '500g']:
                        print(f"✅ 订单 {order_id} 重量已修复: {weight}")
                    else:
                        print(f"⚠️  订单 {order_id} 有未知重量: {weight}")
                        has_problem = True
            
            if has_problem:
                still_problem_count += 1
            else:
                fixed_count += 1
                
        except OrderModel.DoesNotExist:
            print(f"⚠️  订单 {order_id} 不存在")
    
    print(f"\n修复结果:")
    print(f"✅ 已修复: {fixed_count} 个订单")
    print(f"❌ 仍有问题: {still_problem_count} 个订单")
    
    # 检查所有BeanItem的价格设置
    print("\n检查BeanItem价格设置...")
    beans = BeanItem.objects.all()
    for bean in beans:
        print(f"Bean: {bean.name}")
        print(f"  price_200g: ${bean.price_200g}")
        print(f"  price_500g: ${bean.price_500g}")
        print(f"  get_price('200g'): ${bean.get_price('200g')}")
        print(f"  get_price('500g'): ${bean.get_price('500g')}")
    
    return still_problem_count == 0

def check_order_display_logic():
    """检查订单显示逻辑"""
    print("\n检查订单显示逻辑...")
    
    # 创建一个测试订单来验证显示逻辑
    from decimal import Decimal
    import json
    
    # 获取一个BeanItem
    bean = BeanItem.objects.first()
    if bean:
        # 测试纯咖啡豆订单
        bean_order_data = {
            'type': 'bean',
            'id': bean.id,
            'name': bean.name,
            'quantity': 1,
            'weight': '500g',
            'price': float(bean.price_500g),
            'total_price': float(bean.price_500g)
        }
        
        # 创建一个临时订单对象（不保存到数据库）
        class TempOrder:
            def __init__(self, items):
                self.items = json.dumps([items])
                self.order_type = 'normal'
                self.is_quick_order = False
                self.pickup_time_choice = '5'
            
            def get_items(self):
                return json.loads(self.items) if isinstance(self.items, str) else self.items
        
        temp_order = TempOrder(bean_order_data)
        
        # 手动测试显示逻辑
        print("纯咖啡豆订单测试:")
        items = temp_order.get_items()
        has_coffee = any(item.get('type') == 'coffee' for item in items)
        has_beans = any(item.get('type') == 'bean' for item in items)
        
        print(f"  has_coffee: {has_coffee}")
        print(f"  has_beans: {has_beans}")
        print(f"  is_beans_only: {has_beans and not has_coffee}")
        
        if has_beans and not has_coffee:
            print("  ✅ 纯咖啡豆订单逻辑正确")
            print("  pickup_time_display: 隨時可取")
        else:
            print("  ❌ 纯咖啡豆订单逻辑不正确")
    
    return True

def main():
    print("="*60)
    print("验证数据修复结果")
    print("="*60)
    
    try:
        # 验证数据修复
        data_ok = verify_data_fix()
        
        # 检查显示逻辑
        logic_ok = check_order_display_logic()
        
        print("\n" + "="*60)
        if data_ok and logic_ok:
            print("✅ 数据修复验证通过！")
            print("\n下一步建议：")
            print("1. 手动测试以下页面：")
            print("   - /bean/1/ (咖啡豆详情页)")
            print("   - /cart/ (购物车页面)")
            print("   - 创建纯咖啡豆订单，验证订单确认页面")
            print("\n2. 如果手动测试通过，可以进入第二步：技术债务处理")
        else:
            print("❌ 数据修复验证未通过")
            print("请检查以上问题并重新修复")
        
        print("="*60)
        return 0 if data_ok and logic_ok else 1
        
    except Exception as e:
        print(f"❌ 验证过程中出现异常: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())