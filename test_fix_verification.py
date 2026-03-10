#!/usr/bin/env python
"""
測試修正效果驗證腳本
"""

import os
import sys
import django

# 設置Django環境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'betweencoffee_delivery.settings')
django.setup()

from eshop.models import OrderModel, CoffeeQueue
from eshop.utils.order_item_processor import OrderItemProcessor
import pytz
from django.utils import timezone

def test_fixes():
    """測試修正效果"""
    print("=== 測試修正效果 ===")
    
    hk_tz = pytz.timezone('Asia/Hong_Kong')
    now = timezone.now()
    
    # 查找一個純咖啡豆訂單
    beans_only_order = OrderModel.objects.filter(
        items__type='bean'
    ).exclude(
        items__type='coffee'
    ).first()
    
    if beans_only_order:
        print(f"1. 檢查純咖啡豆訂單 #{beans_only_order.id}:")
        
        # 使用處理器準備數據
        order_data = OrderItemProcessor.prepare_ready_order_data(beans_only_order, now, hk_tz)
        print(f"   是否為純咖啡豆訂單: {order_data.get('is_beans_only')}")
        print(f"   咖啡師: '{order_data.get('barista')}' (應該為空字符串)")
    else:
        print("1. 沒有找到純咖啡豆訂單")
    
    print()
    
    # 查找一個混合訂單（有咖啡的訂單）
    mixed_order = OrderModel.objects.filter(
        items__type='coffee'
    ).first()
    
    if mixed_order:
        print(f"2. 檢查混合訂單 #{mixed_order.id}:")
        
        # 使用處理器準備數據
        order_data = OrderItemProcessor.prepare_ready_order_data(mixed_order, now, hk_tz)
        print(f"   是否為純咖啡豆訂單: {order_data.get('is_beans_only')}")
        print(f"   咖啡師: '{order_data.get('barista')}'")
    else:
        print("2. 沒有找到混合訂單")
    
    print()
    print("=== CSS修正測試 ===")
    print("已修正 staff_order_management.css 中的 .badge-success 規則:")
    print("  修正前: background-color: #fff !important; color: black !important;")
    print("  修正後: background-color: #28a745 !important; color: white !important;")
    print()
    print("現在'已就緒: 下午xx:xx'徽章應該顯示綠色背景白色文字")
    
    # 檢查CSS文件
    css_file = "static/css/staff_order_management.css"
    if os.path.exists(css_file):
        with open(css_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if "background-color: #28a745 !important" in content:
                print(f"✅ CSS文件 {css_file} 已正確修正")
            else:
                print(f"❌ CSS文件 {css_file} 可能未正確修正")
    else:
        print(f"⚠️ CSS文件 {css_file} 不存在")

if __name__ == "__main__":
    test_fixes()