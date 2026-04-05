#!/usr/bin/env python
"""
調試 INVALID_EXPRESSION 問題
"""

import os
import sys
import django

# 設置 Django 環境
sys.path.append('/home/kei/Desktop/betweencoffee_delivery_enhance')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'betweencoffee_delivery.settings')
django.setup()

from eshop.models import OrderModel
from django.contrib.auth import get_user_model
from django.template.loader import get_template
import re

def find_invalid_expression_in_template():
    """在模板中查找可能導致 INVALID_EXPRESSION 的問題"""
    print("=== 查找模板中的問題 ===")
    
    # 加載模板
    try:
        template = get_template('socialuser/order_history.html')
        print("✅ 模板加載成功")
    except Exception as e:
        print(f"❌ 模板加載失敗: {e}")
        return
    
    # 獲取模板源代碼
    template_source = template.template.source
    
    # 查找所有模板表達式
    print("\n查找模板表達式...")
    expressions = re.findall(r'\{\{[^}]*\}\}', template_source)
    
    print(f"找到 {len(expressions)} 個模板表達式")
    
    # 檢查每個表達式
    problematic_expressions = []
    for i, expr in enumerate(expressions[:20]):  # 只檢查前20個
        print(f"\n{i+1}. {expr}")
        
        # 檢查是否有明顯問題
        if 'get_status_display_with_timing' in expr:
            print("  ⚠️  包含已修復的 get_status_display_with_timing")
            problematic_expressions.append(expr)
        
        # 檢查是否有其他可能問題的方法
        if 'order.' in expr:
            method_name = expr.split('order.')[1].split('|')[0].split(' ')[0].split(')')[0]
            print(f"  調用方法: {method_name}")
    
    # 檢查模板中是否有其他問題
    print("\n=== 檢查模板其他部分 ===")
    
    # 檢查圖片路徑
    if 'item.image' in template_source:
        print("✅ 找到 item.image 表達式")
    
    # 檢查靜態文件路徑
    if 'static ' in template_source:
        print("✅ 找到 static 標籤")
    
    # 檢查 URL 反向解析
    if 'url ' in template_source:
        print("✅ 找到 url 標籤")
    
    return problematic_expressions

def test_specific_expressions():
    """測試特定表達式"""
    print("\n=== 測試特定表達式 ===")
    
    # 創建測試數據
    User = get_user_model()
    user = User.objects.filter(username='test_user_history').first()
    
    if not user:
        print("創建測試用戶...")
        user = User.objects.create_user(
            username='test_user_history',
            email='test_history@example.com',
            password='testpassword123'
        )
    
    # 創建測試訂單
    order = OrderModel.objects.create(
        user=user,
        name='Test User',
        email='test@example.com',
        phone='12345678',
        payment_status='paid',
        status='completed',
        total_price=50.00,
        items=[{
            'type': 'coffee',
            'id': 1,
            'name': 'Test Coffee',
            'quantity': 1,
            'price': 50.00,
            'total_price': 50.00,
            'cup_level': 'Medium',
            'milk_level': 'Medium'
        }]
    )
    
    # 測試可能導致問題的表達式
    test_cases = [
        ("order.get_status_display()", order.get_status_display),
        ("order.get_payment_status_display()", order.get_payment_status_display),
        ("order.get_remaining_minutes()", order.get_remaining_minutes),
        ("order.get_items()", order.get_items),
        ("order.get_items_with_chinese_options()", order.get_items_with_chinese_options),
        ("order.pickup_code", lambda: order.pickup_code),
        ("order.total_price|floatformat:2", lambda: f"{order.total_price:.2f}"),
    ]
    
    for expr, func in test_cases:
        try:
            result = func()
            print(f"✅ {expr}: {result}")
        except Exception as e:
            print(f"❌ {expr}: {e}")
    
    # 測試模板過濾器
    print("\n=== 測試模板過濾器 ===")
    
    from django.template import Template, Context
    
    test_filters = [
        ("{{ order.created_at|date:'Y-m-d H:i' }}", {'order': order}),
        ("{{ order.total_price|floatformat:2 }}", {'order': order}),
        ("{{ order.get_items|length }}", {'order': order}),
    ]
    
    for template_code, context_dict in test_filters:
        try:
            template = Template(template_code)
            context = Context(context_dict)
            result = template.render(context)
            print(f"✅ {template_code}: {result}")
        except Exception as e:
            print(f"❌ {template_code}: {e}")

def render_template_and_find_invalid():
    """渲染模板並查找 INVALID_EXPRESSION"""
    print("\n=== 渲染模板並查找問題 ===")
    
    # 創建測試數據
    User = get_user_model()
    user = User.objects.filter(username='test_user_history').first()
    
    # 創建訂單列表
    orders = []
    order = OrderModel.objects.create(
        user=user,
        name='Test User',
        email='test@example.com',
        phone='12345678',
        payment_status='paid',
        status='completed',
        total_price=50.00,
        items=[{
            'type': 'coffee',
            'id': 1,
            'name': 'Test Coffee',
            'quantity': 1,
            'price': 50.00,
            'total_price': 50.00,
            'cup_level': 'Medium',
            'milk_level': 'Medium'
        }]
    )
    orders.append(order)
    
    # 渲染模板
    template = get_template('socialuser/order_history.html')
    context = {
        'orders': orders,
        'STATIC_URL': '/static/'
    }
    
    try:
        rendered = template.render(context)
        print("✅ 模板渲染成功")
        
        # 查找 INVALID_EXPRESSION
        if 'INVALID_EXPRESSION' in rendered:
            print("❌ 渲染結果包含 INVALID_EXPRESSION")
            
            # 查找上下文
            lines = rendered.split('\n')
            for i, line in enumerate(lines):
                if 'INVALID_EXPRESSION' in line:
                    print(f"\n在第 {i+1} 行找到 INVALID_EXPRESSION:")
                    print(f"  行內容: {line}")
                    
                    # 顯示前後幾行
                    start = max(0, i-3)
                    end = min(len(lines), i+4)
                    print(f"\n  上下文:")
                    for j in range(start, end):
                        prefix = ">>> " if j == i else "    "
                        print(f"{prefix}{lines[j]}")
                    
                    # 嘗試找出問題表達式
                    if '{{' in line and '}}' in line:
                        expr_start = line.find('{{')
                        expr_end = line.find('}}', expr_start)
                        if expr_start != -1 and expr_end != -1:
                            expr = line[expr_start:expr_end+2]
                            print(f"\n  可能問題表達式: {expr}")
        
        else:
            print("✅ 渲染結果不包含 INVALID_EXPRESSION")
            
            # 檢查渲染結果的長度
            print(f"  渲染結果長度: {len(rendered)} 字符")
            
            # 檢查是否包含關鍵內容
            if '訂單編號' in rendered:
                print("✅ 包含訂單編號")
            if 'badge-info' in rendered:
                print("✅ 包含已完成訂單徽章")
            if '已完成' in rendered:
                print("✅ 包含'已完成'文字")
                
    except Exception as e:
        print(f"❌ 模板渲染失敗: {e}")
        import traceback
        print(traceback.format_exc())

if __name__ == '__main__':
    print("開始調試 INVALID_EXPRESSION 問題...")
    
    # 運行調試
    find_invalid_expression_in_template()
    test_specific_expressions()
    render_template_and_find_invalid()
    
    print("\n=== 調試完成 ===")