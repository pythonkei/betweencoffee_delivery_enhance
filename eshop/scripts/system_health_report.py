# eshop/scripts/system_health_report.py

import os
import sys
import django
from datetime import datetime, timedelta

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../../'))
sys.path.insert(0, project_root)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'betweencoffee_delivery.settings')
django.setup()

from django.db import connection
from eshop.models import OrderModel, CoffeeQueue
from django.db.models import Count, Q, Sum
import time
from django.utils import timezone as django_timezone

def generate_health_report():
    """生成系統健康報告"""
    
    print("=" * 60)
    print("咖啡店訂單管理系統 - 健康檢查報告")
    print(f"生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 1. 數據庫健康狀態
    print("\n1. 數據庫健康狀態:")
    
    with connection.cursor() as cursor:
        # 檢查數據庫大小
        cursor.execute("""
            SELECT pg_size_pretty(pg_database_size(current_database())) as db_size;
        """)
        db_size = cursor.fetchone()[0]
        print(f"   數據庫大小: {db_size}")
        
        # 檢查表大小
        cursor.execute("""
            SELECT 
                tablename,
                pg_size_pretty(pg_total_relation_size(quote_ident(tablename))) as total_size
            FROM pg_tables
            WHERE schemaname = 'public'
            ORDER BY pg_total_relation_size(quote_ident(tablename)) DESC
            LIMIT 5;
        """)
        print(f"   主要表大小:")
        for table, size in cursor.fetchall():
            print(f"     - {table}: {size}")
    
    # 2. 業務指標
    print("\n2. 業務指標:")
    
    # 使用 Django 的時區感知時間
    today = django_timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    # 今日訂單統計
    today_stats = OrderModel.objects.filter(
        created_at__gte=today
    ).aggregate(
        total=Count('id'),
        paid=Count('id', filter=Q(payment_status='paid')),
        quick=Count('id', filter=Q(is_quick_order=True)),
        revenue=Sum('total_price', filter=Q(payment_status='paid'))
    )
    
    print(f"   今日訂單:")
    print(f"     - 總數: {today_stats['total'] or 0}")
    print(f"     - 已支付: {today_stats['paid'] or 0}")
    print(f"     - 快速訂單: {today_stats['quick'] or 0}")
    if today_stats['revenue']:
        print(f"     - 營業額: HK$ {float(today_stats['revenue']):.2f}")
    else:
        print(f"     - 營業額: HK$ 0.00")
    
    # 3. 隊列狀態
    print("\n3. 隊列狀態:")
    
    queue_stats = CoffeeQueue.objects.aggregate(
        waiting=Count('id', filter=Q(status='waiting')),
        preparing=Count('id', filter=Q(status='preparing')),
        ready=Count('id', filter=Q(status='ready'))
    )
    
    print(f"   等待製作: {queue_stats['waiting'] or 0}")
    print(f"   製作中: {queue_stats['preparing'] or 0}")
    print(f"   已就緒: {queue_stats['ready'] or 0}")
    
    # 4. 性能指標
    print("\n4. 性能指標:")
    
    # 測試關鍵查詢性能
    queries = [
        ("等待隊列查詢", lambda: list(CoffeeQueue.objects.filter(status='waiting').order_by('position')[:20])),
        ("今日快速訂單", lambda: list(OrderModel.objects.filter(
            is_quick_order=True, 
            created_at__gte=today,
            payment_status='paid'
        )[:20])),
        ("支付狀態查詢", lambda: list(OrderModel.objects.filter(
            payment_status='paid',
            status='waiting'
        )[:20])),
    ]
    
    for name, query in queries:
        start = time.time()
        result = query()
        elapsed = (time.time() - start) * 1000
        print(f"   {name}: {len(result)} 條記錄，{elapsed:.2f}ms")
    
    # 5. 索引使用情況（修正後的查詢）
    print("\n5. 索引使用情況:")
    
    with connection.cursor() as cursor:
        try:
            # 修正的查詢，使用正確的列名
            cursor.execute("""
                SELECT 
                    schemaname,
                    relname as tablename,
                    indexrelname as indexname,
                    idx_scan as scans,
                    idx_tup_read as tuples_read,
                    idx_tup_fetch as tuples_fetched
                FROM pg_stat_user_indexes
                WHERE schemaname = 'public'
                ORDER BY idx_scan DESC
                LIMIT 10;
            """)
            
            indexes = cursor.fetchall()
            if indexes:
                for schema, table, index, scans, read, fetched in indexes[:5]:
                    print(f"   {schema}.{table}.{index}: {scans} 次掃描")
            else:
                print("   未找到索引統計信息")
        except Exception as e:
            print(f"   獲取索引統計失敗: {str(e)[:100]}")
    
    # 6. 建議與警告
    print("\n6. 系統建議:")
    
    # 檢查是否有長時間等待的訂單
    two_hours_ago = django_timezone.now() - timedelta(hours=2)
    old_orders = OrderModel.objects.filter(
        status='waiting',
        payment_status='paid',
        created_at__lt=two_hours_ago
    ).count()
    
    if old_orders > 0:
        print(f"   ⚠️  發現 {old_orders} 個超過2小時的等待訂單，建議檢查隊列處理")
    else:
        print("   ✓ 沒有長時間等待的訂單")
    
    # 檢查隊列積壓
    waiting_count = queue_stats['waiting'] or 0
    if waiting_count > 20:
        print(f"   ⚠️  隊列積壓較多: {waiting_count} 個等待訂單")
    else:
        print(f"   ✓ 隊列狀態正常: {waiting_count} 個等待訂單")
    
    # 檢查快速訂單處理
    quick_waiting = OrderModel.objects.filter(
        is_quick_order=True,
        status='waiting',
        payment_status='paid'
    ).count()
    
    if quick_waiting > 5:
        print(f"   ⚠️  快速訂單等待較多: {quick_waiting} 個")
    else:
        print(f"   ✓ 快速訂單處理正常")
    
    # 7. 系統統計總覽
    print("\n7. 系統統計總覽:")
    
    total_stats = {
        '總訂單數': OrderModel.objects.count(),
        '快速訂單數': OrderModel.objects.filter(is_quick_order=True).count(),
        '普通訂單數': OrderModel.objects.filter(is_quick_order=False).count(),
        '已支付訂單數': OrderModel.objects.filter(payment_status='paid').count(),
        '待支付訂單數': OrderModel.objects.filter(payment_status='pending').count(),
        '咖啡訂單數': OrderModel.objects.filter(items__contains='coffee').count(),
        '咖啡豆訂單數': OrderModel.objects.filter(items__contains='bean').count(),
    }
    
    for name, value in total_stats.items():
        print(f"   {name}: {value}")
    
    print("\n" + "=" * 60)
    print("健康檢查報告生成完成")
    print("=" * 60)

if __name__ == '__main__':
    generate_health_report()