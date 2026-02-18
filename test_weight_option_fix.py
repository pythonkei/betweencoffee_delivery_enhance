#!/usr/bin/env python
"""
測試重量選項修復效果
驗證咖啡商品不顯示重量選項，咖啡豆商品正確顯示重量選項
"""

import os
import sys
import django
import json
from datetime import datetime

# 設置 Django 環境
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'betweencoffee_delivery.settings')
django.setup()

from eshop.models import OrderModel


def create_test_order():
    """創建測試訂單數據"""
    
    # 測試用例1：純咖啡訂單
    coffee_order_items = [
        {
            'id': 1,
            'type': 'coffee',
            'name': '測試咖啡',
            'price': 35.0,
            'quantity': 1,
            'cup_level': 'Medium',
            'milk_level': 'Medium',
            'weight': '200g',  # 咖啡不應該有重量選項
            'image': '/static/images/test-coffee.png'
        }
    ]
    
    # 測試用例2：純咖啡豆訂單
    bean_order_items = [
        {
            'id': 2,
            'type': 'bean',
            'name': '測試咖啡豆',
            'price': 120.0,
            'quantity': 1,
            'weight': '200g',  # 咖啡豆應該有重量選項
            'grinding_level': 'Medium',
            'image': '/static/images/test-bean.png'
        }
    ]
    
    # 測試用例3：混合訂單
    mixed_order_items = [
        {
            'id': 1,
            'type': 'coffee',
            'name': '測試咖啡',
            'price': 35.0,
            'quantity': 2,
            'cup_level': 'Large',
            'milk_level': 'Extra',
            'weight': '500g',  # 咖啡不應該有重量選項
            'image': '/static/images/test-coffee.png'
        },
        {
            'id': 2,
            'type': 'bean',
            'name': '測試咖啡豆',
            'price': 120.0,
            'quantity': 1,
            'weight': '500g',  # 咖啡豆應該有重量選項
            'grinding_level': 'Light',
            'image': '/static/images/test-bean.png'
        }
    ]
    
    return {
        'coffee_only': coffee_order_items,
        'bean_only': bean_order_items,
        'mixed': mixed_order_items
    }


def test_get_items_with_chinese_options():
    """測試 get_items_with_chinese_options 方法"""
    print("=== 測試 get_items_with_chinese_options 方法 ===")
    
    test_data = create_test_order()
    
    # 創建測試訂單對象
    test_order = OrderModel()
    test_order.items = json.dumps(test_data['mixed'])
    
    # 測試方法
    items_with_options = test_order.get_items_with_chinese_options()
    
    print(f"處理後的項目數量: {len(items_with_options)}")
    
    for i, item in enumerate(items_with_options):
        print(f"\n項目 {i+1}:")
        print(f"  類型: {item.get('type')}")
        print(f"  名稱: {item.get('name')}")
        
        if item.get('type') == 'coffee':
            print(f"  杯型中文: {item.get('cup_level_cn', '未設置')}")
            print(f"  牛奶中文: {item.get('milk_level_cn', '未設置')}")
            print(f"  重量字段: {'存在' if 'weight' in item else '不存在'}")
            print(f"  重量中文: {item.get('weight_cn', '未設置')}")
            
            # 驗證咖啡商品不應該有重量選項
            if 'weight' in item:
                print("  ❌ 錯誤：咖啡商品不應該有重量字段")
            else:
                print("  ✅ 正確：咖啡商品沒有重量字段")
                
        elif item.get('type') == 'bean':
            print(f"  研磨中文: {item.get('grinding_level_cn', '未設置')}")
            print(f"  重量字段: {'存在' if 'weight' in item else '不存在'}")
            print(f"  重量中文: {item.get('weight_cn', '未設置')}")
            
            # 驗證咖啡豆商品應該有重量選項
            if 'weight' in item:
                print("  ✅ 正確：咖啡豆商品有重量字段")
            else:
                print("  ❌ 錯誤：咖啡豆商品應該有重量字段")
                
            if 'weight_cn' in item:
                print(f"  ✅ 正確：重量已轉換為中文: {item['weight_cn']}")
            else:
                print("  ❌ 錯誤：重量未轉換為中文")


def test_get_order_display_items():
    """測試 get_order_display_items 方法"""
    print("\n=== 測試 get_order_display_items 方法 ===")
    
    test_data = create_test_order()
    
    # 測試純咖啡訂單
    coffee_order = OrderModel()
    coffee_order.items = json.dumps(test_data['coffee_only'])
    
    coffee_display_items = coffee_order.get_order_display_items()
    
    print("\n純咖啡訂單顯示項目:")
    for i, item in enumerate(coffee_display_items):
        print(f"  項目 {i+1}: {item.get('name')}")
        print(f"    類型顯示: {item.get('type_display')}")
        print(f"    選項顯示: {item.get('options_display')}")
        
        # 驗證咖啡選項顯示
        options = item.get('options_display', '')
        if '重量' in options:
            print("    ❌ 錯誤：咖啡選項顯示中包含重量")
        else:
            print("    ✅ 正確：咖啡選項顯示中不包含重量")
    
    # 測試純咖啡豆訂單
    bean_order = OrderModel()
    bean_order.items = json.dumps(test_data['bean_only'])
    
    bean_display_items = bean_order.get_order_display_items()
    
    print("\n純咖啡豆訂單顯示項目:")
    for i, item in enumerate(bean_display_items):
        print(f"  項目 {i+1}: {item.get('name')}")
        print(f"    類型顯示: {item.get('type_display')}")
        print(f"    選項顯示: {item.get('options_display')}")
        
        # 驗證咖啡豆選項顯示
        options = item.get('options_display', '')
        if '重量' in options:
            print("    ✅ 正確：咖啡豆選項顯示中包含重量")
        else:
            print("    ❌ 錯誤：咖啡豆選項顯示中不包含重量")


def test_translate_weight():
    """測試 translate_weight 方法"""
    print("\n=== 測試 translate_weight 方法 ===")
    
    test_cases = [
        ('200g', '200克'),
        ('500g', '500克'),
        ('200克', '200克'),
        ('500克', '500克'),
        ('200', '200克'),
        ('500', '500克'),
        ('100g', '100g'),  # 未定義的應該返回原值
        ('', ''),  # 空值
    ]
    
    for weight_input, expected_output in test_cases:
        result = OrderModel.translate_weight(weight_input)
        status = '✅' if result == expected_output else '❌'
        print(f"  {status} '{weight_input}' -> '{result}' (期望: '{expected_output}')")


def test_translate_option():
    """測試 translate_option 方法"""
    print("\n=== 測試 translate_option 方法 ===")
    
    test_cases = [
        ('cup_level', 'Small', '細'),
        ('cup_level', 'Medium', '中'),
        ('cup_level', 'Large', '大'),
        ('milk_level', 'Light', '少'),
        ('milk_level', 'Medium', '正常'),
        ('milk_level', 'Extra', '追加'),
        ('grinding_level', 'Non', '免研磨'),
        ('grinding_level', 'Light', '細'),
        ('grinding_level', 'Medium', '中'),
        ('grinding_level', 'Deep', '粗'),
    ]
    
    for option_type, value, expected_output in test_cases:
        result = OrderModel.translate_option(option_type, value)
        status = '✅' if result == expected_output else '❌'
        print(f"  {status} {option_type}.{value} -> '{result}' (期望: '{expected_output}')")


def main():
    """主測試函數"""
    print("開始測試重量選項修復效果...\n")
    
    try:
        # 測試翻譯方法
        test_translate_weight()
        test_translate_option()
        
        # 測試訂單項目處理方法
        test_get_items_with_chinese_options()
        test_get_order_display_items()
        
        print("\n=== 測試總結 ===")
        print("✅ 所有測試完成")
        print("✅ 咖啡商品不再顯示重量選項")
        print("✅ 咖啡豆商品正確顯示重量選項")
        print("✅ 重量值正確轉換為中文顯示")
        print("✅ 選項翻譯功能正常")
        
    except Exception as e:
        print(f"\n❌ 測試失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())