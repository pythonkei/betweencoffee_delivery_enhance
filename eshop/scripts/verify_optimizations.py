# eshop/scripts/verify_optimizations.py

import os
import sys
import django
from datetime import datetime

# 獲取項目根目錄的正確路徑
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../../'))
sys.path.insert(0, project_root)

# 設置 Django 環境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'betweencoffee_delivery.settings')
django.setup()

from django.db import connection
from eshop.models import OrderModel, CoffeeQueue
import time

def verify_optimizations():
    """驗證優化效果"""
    
    print("=== 優化效果驗證 ===")
    print(f"時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. 確認索引已存在
    print("\n1. 確認優化索引已存在:")
    
    required_indexes = [
        ('eshop_ordermodel', 'idx_order_quick_status'),
        ('eshop_ordermodel', 'idx_order_payment_created'),
        ('eshop_ordermodel', 'idx_order_pickup_choice'),
        ('eshop_coffeequeue', 'idx_queue_status_position'),
        ('eshop_coffeequeue', 'idx_queue_est_start'),
    ]
    
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT tablename, indexname 
            FROM pg_indexes 
            WHERE schemaname = 'public' 
            AND tablename IN ('eshop_ordermodel', 'eshop_coffeequeue')
            ORDER BY tablename, indexname;
        """)
        existing_indexes = cursor.fetchall()
        
        existing_index_dict = {f"{table}_{name}": True for table, name in existing_indexes}
        
        for table, index in required_indexes:
            key = f"{table}_{index}"
            if key in existing_index_dict:
                print(f"  ✓ {table}: {index}")
            else:
                print(f"  ✗ {table}: {index} (缺失)")
    
    # 2. 測試查詢性能
    print("\n2. 查詢性能測試:")
    
    performance_tests = [
        {
            'name': '快速訂單查詢',
            'query': lambda: OrderModel.objects.filter(is_quick_order=True, payment_status='paid'),
            'limit': 50
        },
        {
            'name': '等待隊列查詢', 
            'query': lambda: CoffeeQueue.objects.filter(status='waiting').order_by('position'),
            'limit': 50
        },
        {
            'name': '支付狀態+時間查詢',
            'query': lambda: OrderModel.objects.filter(payment_status='paid', created_at__date='2026-02-08'),
            'limit': 50
        },
        {
            'name': '混合查詢',
            'query': lambda: OrderModel.objects.filter(
                is_quick_order=True, 
                status='waiting',
                pickup_time_choice__in=['5', '10', '15']
            ),
            'limit': 50
        }
    ]
    
    for test in performance_tests:
        start_time = time.time()
        try:
            result = list(test['query']()[:test['limit']])
            elapsed = (time.time() - start_time) * 1000
            print(f"  {test['name']}: {len(result)} 條記錄，耗時 {elapsed:.2f}ms")
        except Exception as e:
            print(f"  {test['name']}: 查詢失敗 - {str(e)}")
    
    # 3. 分析查詢計劃
    print("\n3. 查詢計劃分析:")
    
    sample_queries = [
        ("快速訂單查詢計劃", 
         "EXPLAIN ANALYZE SELECT * FROM eshop_ordermodel WHERE is_quick_order = true AND status = 'waiting' LIMIT 10;"),
        ("隊列查詢計劃",
         "EXPLAIN ANALYZE SELECT * FROM eshop_coffeequeue WHERE status = 'waiting' ORDER BY position LIMIT 10;"),
    ]
    
    with connection.cursor() as cursor:
        for name, query in sample_queries:
            try:
                print(f"\n  {name}:")
                cursor.execute(query)
                rows = cursor.fetchall()
                for row in rows:
                    print(f"    {row[0]}")
            except Exception as e:
                print(f"   查詢計劃獲取失敗: {str(e)}")
    
    # 4. 系統狀態總結
    print("\n4. 系統狀態總結:")
    
    stats = {
        '總訂單數': OrderModel.objects.count(),
        '快速訂單數': OrderModel.objects.filter(is_quick_order=True).count(),
        '隊列等待數': CoffeeQueue.objects.filter(status='waiting').count(),
        '隊列製作中數': CoffeeQueue.objects.filter(status='preparing').count(),
    }
    
    for name, value in stats.items():
        print(f"  {name}: {value}")
    
    print("\n=== 驗證完成 ===")

if __name__ == '__main__':
    verify_optimizations()