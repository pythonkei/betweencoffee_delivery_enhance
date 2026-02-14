# test_pages_display.py
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'betweencoffee_delivery.settings')
django.setup()

from django.test import TestCase, Client
from eshop.models import BeanItem, CoffeeItem
from decimal import Decimal

def test_actual_pages():
    """实际页面测试"""
    print("开始实际页面测试...")
    
    client = Client()
    
    # 获取一个存在的BeanItem
    bean = BeanItem.objects.first()
    if not bean:
        print("⚠️  没有找到咖啡豆数据，跳过页面测试")
        return
    
    # 尝试访问可能的URL模式
    test_patterns = [
        f'/bean/{bean.id}/',
        f'/beans/{bean.id}/',
        f'/shop/bean/{bean.id}/',
        f'/eshop/bean/{bean.id}/',
        f'/product/bean/{bean.id}/',
    ]
    
    for url in test_patterns:
        print(f"尝试访问: {url}")
        response = client.get(url)
        
        if response.status_code == 200:
            print(f"✅ 成功访问: {url}")
            
            # 检查内容
            content = response.content.decode('utf-8')
            
            # 检查重量选项
            if '200g' in content and '500g' in content:
                print("  ✅ 重量选项显示正确")
            else:
                print("  ❌ 重量选项显示不正确")
                
            # 检查价格显示
            if f'${bean.price_200g}' in content or str(bean.price_200g) in content:
                print(f"  ✅ 200g价格显示正确")
            else:
                print(f"  ❌ 200g价格显示不正确")
                
            if f'${bean.price_500g}' in content or str(bean.price_500g) in content:
                print(f"  ✅ 500g价格显示正确")
            else:
                print(f"  ❌ 500g价格显示不正确")
                
            break
        else:
            print(f"  ❌ 访问失败: {response.status_code}")
    
    print("\n页面测试完成！")

def main():
    """主测试函数"""
    print("="*60)
    print("开始实际页面测试...")
    print("="*60)
    
    try:
        test_actual_pages()
        
        print("\n" + "="*60)
        print("✅ 页面测试完成")
        print("="*60)
        return 0
        
    except Exception as e:
        print(f"\n❌ 测试过程中出现异常: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())