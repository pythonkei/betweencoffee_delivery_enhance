# check_remaining_issues.py
import os
import re

def analyze_file(filepath):
    """詳細分析文件中的 is_paid 引用"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        lines = content.split('\n')
    
    print(f"\n=== 分析: {filepath} ===")
    
    # 分類統計
    categories = {
        'property_def': 0,  # @property 定義
        'test_code': 0,     # 測試代碼
        'migration': 0,     # 遷移文件
        'query_filter': 0,  # 查詢過濾
        'attribute_access': 0,  # 屬性訪問
        'assignment': 0,    # 賦值操作
        'other': 0          # 其他
    }
    
    for i, line in enumerate(lines, 1):
        if 'is_paid' in line:
            # 分類
            if '@property' in line or 'def is_paid' in line:
                categories['property_def'] += 1
                print(f"  行 {i}: [屬性定義] {line.strip()}")
            elif 'test' in filepath.lower():
                categories['test_code'] += 1
                print(f"  行 {i}: [測試代碼] {line.strip()}")
            elif 'migration' in filepath:
                categories['migration'] += 1
                print(f"  行 {i}: [遷移文件] {line.strip()}")
            elif '.filter' in line or '.objects' in line:
                categories['query_filter'] += 1
                print(f"  行 {i}: [查詢過濾] {line.strip()}")
            elif '=' in line and 'is_paid' in line.split('=')[0]:
                categories['assignment'] += 1
                print(f"  行 {i}: [賦值操作] {line.strip()}")
            elif '.' in line and 'is_paid' in line:
                categories['attribute_access'] += 1
                print(f"  行 {i}: [屬性訪問] {line.strip()}")
            else:
                categories['other'] += 1
                print(f"  行 {i}: [其他] {line.strip()}")
    
    # 打印統計
    print(f"\n統計:")
    for category, count in categories.items():
        if count > 0:
            print(f"  {category}: {count}")
    
    return categories

# 檢查關鍵文件
files_to_check = [
    'eshop/order_status_manager.py',
    'eshop/queue_manager.py',
    'eshop/serializers.py',
    'eshop/views/payment_views.py',
    'eshop/views/api_views.py',
    'eshop/management/commands/debug_queue.py',
]

for file in files_to_check:
    if os.path.exists(file):
        analyze_file(file)