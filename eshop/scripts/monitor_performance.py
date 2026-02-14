# eshop/scripts/monitor_performance.py

import os
import django
import sys
import time
from datetime import datetime, timedelta

# 獲取項目根目錄的正確路徑
# 腳本位置：/home/kei/Desktop/betweencoffee_delivery_enhance/eshop/scripts/analyze_queries.py
# 項目根目錄：/home/kei/Desktop/betweencoffee_delivery_enhance
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../../'))
sys.path.insert(0, project_root)

# 設置 Django 環境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'betweencoffee_delivery.settings')



django.setup()

from eshop.models import OrderModel, CoffeeQueue
from django.db import connection
from django.db.models import Count, Q

def monitor_performance():
    """監控系統性能關鍵指標"""
    
    print(f"=== 系統性能監控 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===")
    
    # 1. 訂單統計
    print("\n1. 訂單統計:")
    total_orders = OrderModel.objects.count()
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    orders_today = OrderModel.objects.filter(created_at__gte=today).count()
    orders_pending = OrderModel.objects.filter(payment_status='pending').count()
    orders_paid = OrderModel.objects.filter(payment_status='paid').count()
    
    print(f"  總訂單數: {total_orders}")
    print(f"  今日訂單: {orders_today}")
    print(f"  待支付訂單: {orders_pending}")
    print(f"  已支付訂單: {orders_paid}")
    
    # 2. 隊列統計
    print("\n2. 隊列統計:")
    waiting_count = CoffeeQueue.objects.filter(status='waiting').count()
    preparing_count = CoffeeQueue.objects.filter(status='preparing').count()
    
    print(f"  等待中訂單: {waiting_count}")
    print(f"  製作中訂單: {preparing_count}")
    
    # 3. 快速訂單分析
    print("\n3. 快速訂單分析:")
    quick_orders = OrderModel.objects.filter(is_quick_order=True).count()
    quick_today = OrderModel.objects.filter(
        is_quick_order=True,
        created_at__gte=today
    ).count()
    
    print(f"  總快速訂單: {quick_orders}")
    print(f"  今日快速訂單: {quick_today}")
    
    # 4. 查詢性能分析
    print("\n4. 查詢性能分析:")
    
    # 測試常見查詢
    test_queries = [
        ("等待隊列查詢", lambda: list(CoffeeQueue.objects.filter(status='waiting').order_by('position')[:50])),
        ("今日訂單查詢", lambda: list(OrderModel.objects.filter(created_at__gte=today)[:50])),
        ("快速訂單查詢", lambda: list(OrderModel.objects.filter(is_quick_order=True, payment_status='paid')[:50])),
    ]
    
    for query_name, query_func in test_queries:
        start_time = time.time()
        result = query_func()
        elapsed = (time.time() - start_time) * 1000  # 轉為毫秒
        print(f"  {query_name}: {len(result)} 條記錄，耗時 {elapsed:.2f}ms")
    
    # 5. 數據庫連接狀態
    print("\n5. 數據庫連接狀態:")
    with connection.cursor() as cursor:
        cursor.execute("SELECT count(*) FROM pg_stat_activity WHERE state = 'active';")
        active_connections = cursor.fetchone()[0]
        print(f"  活躍連接數: {active_connections}")
    
    print("\n=== 監控完成 ===")

if __name__ == '__main__':
    monitor_performance()