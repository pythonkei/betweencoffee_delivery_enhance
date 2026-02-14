# fix_image_display.py
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'betweencoffee_delivery.settings')
django.setup()

from eshop.models import CoffeeItem, BeanItem

def check_and_fix_image_problems():
    """检查和修复图片显示问题"""
    print("检查咖啡图片问题...")
    coffee_problems = []
    
    for coffee in CoffeeItem.objects.all():
        try:
            # 尝试访问图片URL
            if coffee.image:
                url = coffee.image.url
                print(f"✅ Coffee {coffee.id}: {coffee.name} - 图片正常")
            else:
                coffee_problems.append(coffee.id)
                print(f"❌ Coffee {coffee.id}: {coffee.name} - 没有图片")
        except Exception as e:
            coffee_problems.append(coffee.id)
            print(f"❌ Coffee {coffee.id}: {coffee.name} - 图片错误: {e}")
    
    print(f"\n检查咖啡豆图片问题...")
    bean_problems = []
    
    for bean in BeanItem.objects.all():
        try:
            if bean.image:
                url = bean.image.url
                print(f"✅ Bean {bean.id}: {bean.name} - 图片正常")
            else:
                bean_problems.append(bean.id)
                print(f"❌ Bean {bean.id}: {bean.name} - 没有图片")
        except Exception as e:
            bean_problems.append(bean.id)
            print(f"❌ Bean {bean.id}: {bean.name} - 图片错误: {e}")
    
    print(f"\n总结:")
    print(f"咖啡: {len(coffee_problems)} 个有问题，总共 {CoffeeItem.objects.count()} 个")
    print(f"咖啡豆: {len(bean_problems)} 个有问题，总共 {BeanItem.objects.count()} 个")
    
    return coffee_problems, bean_problems

def update_templates():
    """更新模板文件以使用正确的方法"""
    print("\n建议的模板更新:")
    print("="*60)
    print("在 coffee_menu.html 中:")
    print('  将: <img src="{{ coffee.image.url }}" alt="{{ coffee.name }}" class="img">')
    print('  改为: <img src="{{ coffee.get_detail_image }}" alt="{{ coffee.name }}" class="img">')
    print("\n在 bean_menu.html 中:")
    print('  将: <img src="{{ bean.image.url }}" alt="{{ bean.name }}" class="img">')
    print('  改为: <img src="{{ bean.get_detail_image }}" alt="{{ bean.name }}" class="img">')
    print("="*60)

def main():
    print("="*60)
    print("检查图片显示问题")
    print("="*60)
    
    coffee_problems, bean_problems = check_and_fix_image_problems()
    
    if coffee_problems or bean_problems:
        print(f"\n⚠️  发现 {len(coffee_problems) + len(bean_problems)} 个图片问题")
        print("\n建议解决方案:")
        print("1. 修复模型中的 get_detail_image() 方法（已提供代码）")
        print("2. 更新模板使用 get_detail_image 而不是 image.url")
        print("3. 为有问题的商品上传图片或设置默认图片")
        
        if coffee_problems:
            print(f"\n有问题的咖啡ID: {coffee_problems}")
        if bean_problems:
            print(f"有问题的咖啡豆ID: {bean_problems}")
    else:
        print("\n✅ 没有发现图片问题")
        print("但模板仍需要更新以使用正确的图片方法")
    
    update_templates()
    
    print("\n执行步骤:")
    print("1. 先修复 models.py 中的 get_detail_image() 方法")
    print("2. 然后更新 coffee_menu.html 和 bean_menu.html 模板")
    print("3. 最后测试页面显示")
    print("="*60)

if __name__ == '__main__':
    main()