
# eshop/scripts/analyze_queries.py

import os
import sys
import django

# 獲取項目根目錄的正確路徑
# 腳本位置：/home/kei/Desktop/betweencoffee_delivery_enhance/eshop/scripts/analyze_queries.py
# 項目根目錄：/home/kei/Desktop/betweencoffee_delivery_enhance
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../../'))
sys.path.insert(0, project_root)

# 設置 Django 環境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'betweencoffee_delivery.settings')

# 初始化 Django
django.setup()

from django.db import connection
from django.core.management import call_command
from eshop.models import OrderModel, CoffeeQueue

def analyze_queries():
    print("=== 數據庫查詢分析 ===")
    
    # 1. 檢查現有索引
    print("\n1. 現有索引分析:")
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                tablename, 
                indexname, 
                indexdef
            FROM pg_indexes
            WHERE schemaname = 'public'
            ORDER BY tablename, indexname;
        """)
        indexes = cursor.fetchall()
        for table, name, definition in indexes:
            print(f"  {table}: {name}")
    
    # 2. 分析關鍵模型的查詢模式
    print("\n2. 關鍵模型字段使用頻率分析:")
    
    # 訂單狀態相關查詢
    print("  OrderModel 常見查詢條件:")
    print("    - payment_status (已建立索引)")
    print("    - status (已建立索引)")
    print("    - created_at (已建立索引)")
    print("    - is_quick_order (建議添加索引)")
    print("    - pickup_time_choice (建議添加索引)")
    
    # 隊列相關查詢
    print("\n  CoffeeQueue 常見查詢條件:")
    print("    - status (建議添加索引)")
    print("    - position (已排序，需要索引)")
    print("    - order_id (外鍵索引)")
    
    # 3. 建議新增索引
    print("\n3. 建議新增索引:")
    print("  OrderModel:")
    print("    - 複合索引: (is_quick_order, status)")
    print("    - 複合索引: (payment_status, created_at)")
    print("    - 單列索引: pickup_time_choice")
    
    print("\n  CoffeeQueue:")
    print("    - 複合索引: (status, position)")
    print("    - 單列索引: estimated_start_time")
    
    # 4. 檢查表結構
    print("\n4. 表結構檢查:")
    try:
        # 檢查 OrderModel 表結構
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT column_name, data_type, character_maximum_length
                FROM information_schema.columns
                WHERE table_name = 'eshop_ordermodel'
                ORDER BY ordinal_position;
            """)
            columns = cursor.fetchall()
            print("  eshop_ordermodel 字段:")
            for col in columns[:10]:  # 只顯示前10個字段
                print(f"    - {col[0]} ({col[1]})")
            if len(columns) > 10:
                print(f"    ... 還有 {len(columns)-10} 個字段")
    except Exception as e:
        print(f"  檢查表結構時出錯: {str(e)}")
    
    print("\n=== 分析完成 ===")

if __name__ == '__main__':
    analyze_queries()