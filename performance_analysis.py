#!/usr/bin/env python
"""
性能分析腳本 - 分析系統性能瓶頸
"""

import os
import sys
import time
import logging
from datetime import datetime, timedelta

# 設置 Django 環境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'betweencoffee_delivery.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import django
django.setup()

from django.db import connection
from django.db.models import Count, Q, F
from django.utils import timezone

# 導入模型
from eshop.models import OrderModel, CoffeeQueue
from eshop.queue_manager_refactored import CoffeeQueueManager

logger = logging.getLogger(__name__)


class PerformanceAnalyzer:
    """性能分析器"""
    
    def __init__(self):
        self.results = {}
    
    def analyze_database_queries(self):
        """分析資料庫查詢性能"""
        print("\n=== 資料庫查詢性能分析 ===")
        
        queries = []
        
        # 1. 訂單查詢
        start = time.time()
        orders = OrderModel.objects.all()[:100]
        order_count = orders.count()
        query_time = time.time() - start
        queries.append({
            'name': '獲取100個訂單',
            'time': query_time,
            'count': order_count,
            'query_per_second': order_count / query_time if query_time > 0 else 0
        })
        
        # 2. 隊列查詢
        start = time.time()
        queue_items = CoffeeQueue.objects.select_related('order').filter(status='waiting').order_by('position')[:50]
        queue_count = queue_items.count()
        query_time = time.time() - start
        queries.append({
            'name': '獲取等待中隊列',
            'time': query_time,
            'count': queue_count,
            'query_per_second': queue_count / query_time if query_time > 0 else 0
        })
        
        # 3. 隊列統計查詢
        start = time.time()
        stats = CoffeeQueue.objects.aggregate(
            waiting=Count('id', filter=Q(status='waiting')),
            preparing=Count('id', filter=Q(status='preparing')),
            ready=Count('id', filter=Q(status='ready'))
        )
        query_time = time.time() - start
        queries.append({
            'name': '隊列統計查詢',
            'time': query_time,
            'count': sum(stats.values()),
            'query_per_second': 1 / query_time if query_time > 0 else 0
        })
        
        # 4. 複雜查詢：訂單與隊列關聯查詢
        start = time.time()
        complex_query = CoffeeQueue.objects.select_related('order').filter(
            order__payment_status='paid'
        ).order_by('-order__created_at')[:20]
        complex_count = complex_query.count()
        query_time = time.time() - start
        queries.append({
            'name': '複雜關聯查詢',
            'time': query_time,
            'count': complex_count,
            'query_per_second': complex_count / query_time if query_time > 0 else 0
        })
        
        # 輸出結果
        for query in queries:
            print(f"{query['name']}: {query['time']:.4f}秒, 數量: {query['count']}, QPS: {query['query_per_second']:.2f}")
        
        self.results['database_queries'] = queries
        return queries
    
    def analyze_cache_performance(self):
        """分析緩存性能"""
        print("\n=== 緩存性能分析 ===")
        
        cache_tests = []
        
        try:
            # 嘗試導入查詢優化器
            from eshop.query_optimizer import query_optimizer
            
            # 1. 測試緩存查詢
            start = time.time()
            cached_orders = query_optimizer.get_active_orders_cached(None)
            cache_time = time.time() - start
            cache_tests.append({
                'name': '緩存活動訂單查詢',
                'time': cache_time,
                'count': len(cached_orders),
                'type': 'cache'
            })
            
            # 2. 測試非緩存查詢對比
            start = time.time()
            direct_orders = OrderModel.objects.filter(
                status__in=['preparing', 'ready'],
                payment_status='paid'
            ).order_by('-created_at')[:50]
            direct_count = direct_orders.count()
            direct_time = time.time() - start
            cache_tests.append({
                'name': '直接資料庫查詢',
                'time': direct_time,
                'count': direct_count,
                'type': 'direct'
            })
            
            # 計算性能提升
            if direct_time > 0 and cache_time > 0:
                speedup = direct_time / cache_time
                print(f"緩存性能提升: {speedup:.2f}倍")
            
            # 輸出結果
            for test in cache_tests:
                print(f"{test['name']}: {test['time']:.4f}秒, 數量: {test['count']}")
                
        except Exception as e:
            print(f"⚠️ 緩存分析跳過: {str(e)}")
            # 只測試直接查詢
            start = time.time()
            direct_orders = OrderModel.objects.filter(
                status__in=['preparing', 'ready'],
                payment_status='paid'
            ).order_by('-created_at')[:50]
            direct_count = direct_orders.count()
            direct_time = time.time() - start
            
            cache_tests.append({
                'name': '直接資料庫查詢',
                'time': direct_time,
                'count': direct_count,
                'type': 'direct'
            })
            
            print(f"直接資料庫查詢: {direct_time:.4f}秒, 數量: {direct_count}")
        
        self.results['cache_performance'] = cache_tests
        return cache_tests
    
    def analyze_queue_manager_performance(self):
        """分析隊列管理器性能"""
        print("\n=== 隊列管理器性能分析 ===")
        
        queue_tests = []
        
        try:
            manager = CoffeeQueueManager()
            
            # 1. 測試獲取隊列摘要（如果可用）
            if hasattr(manager, 'get_queue_summary'):
                start = time.time()
                stats = manager.get_queue_summary()
                query_time = time.time() - start
                queue_tests.append({
                    'name': '獲取隊列摘要',
                    'time': query_time,
                    'stats': stats
                })
            
            # 2. 測試重新計算時間（如果可用）
            if hasattr(manager, 'recalculate_all_order_times'):
                start = time.time()
                result = manager.recalculate_all_order_times()
                query_time = time.time() - start
                queue_tests.append({
                    'name': '重新計算所有訂單時間',
                    'time': query_time,
                    'success': result.get('success', False) if isinstance(result, dict) else False
                })
            
            # 3. 測試基本操作
            start = time.time()
            waiting_count = CoffeeQueue.objects.filter(status='waiting').count()
            query_time = time.time() - start
            queue_tests.append({
                'name': '計算等待中訂單數量',
                'time': query_time,
                'count': waiting_count
            })
            
            # 輸出結果
            for test in queue_tests:
                print(f"{test['name']}: {test['time']:.4f}秒")
                if 'stats' in test:
                    print(f"  統計: {test['stats']}")
                elif 'count' in test:
                    print(f"  數量: {test['count']}")
                    
        except Exception as e:
            print(f"⚠️ 隊列管理器分析跳過: {str(e)}")
        
        self.results['queue_manager'] = queue_tests
        return queue_tests
    
    def analyze_memory_usage(self):
        """分析內存使用"""
        print("\n=== 內存使用分析 ===")
        
        import psutil
        import resource
        
        process = psutil.Process()
        
        memory_info = {
            'rss_mb': process.memory_info().rss / 1024 / 1024,
            'vms_mb': process.memory_info().vms / 1024 / 1024,
            'percent': process.memory_percent(),
            'threads': process.num_threads(),
        }
        
        # 獲取系統內存信息
        system_memory = psutil.virtual_memory()
        memory_info.update({
            'system_total_mb': system_memory.total / 1024 / 1024,
            'system_available_mb': system_memory.available / 1024 / 1024,
            'system_percent': system_memory.percent,
        })
        
        print(f"進程內存使用: {memory_info['rss_mb']:.2f} MB (RSS)")
        print(f"進程虛擬內存: {memory_info['vms_mb']:.2f} MB (VMS)")
        print(f"進程內存佔比: {memory_info['percent']:.2f}%")
        print(f"線程數量: {memory_info['threads']}")
        print(f"系統總內存: {memory_info['system_total_mb']:.2f} MB")
        print(f"系統可用內存: {memory_info['system_available_mb']:.2f} MB")
        print(f"系統內存使用率: {memory_info['system_percent']:.2f}%")
        
        self.results['memory_usage'] = memory_info
        return memory_info
    
    def analyze_connection_pool(self):
        """分析資料庫連接池"""
        print("\n=== 資料庫連接分析 ===")
        
        from django.db import connections
        
        connection_info = {}
        
        for conn_name in connections:
            conn = connections[conn_name]
            try:
                # 嘗試獲取連接信息
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    connection_info[conn_name] = {
                        'vendor': conn.vendor,
                        'settings': {
                            'engine': conn.settings_dict.get('ENGINE'),
                            'name': conn.settings_dict.get('NAME'),
                            'host': conn.settings_dict.get('HOST'),
                        },
                        'is_usable': True
                    }
            except Exception as e:
                connection_info[conn_name] = {
                    'vendor': conn.vendor,
                    'error': str(e),
                    'is_usable': False
                }
        
        for conn_name, info in connection_info.items():
            status = "✅ 可用" if info.get('is_usable') else "❌ 不可用"
            print(f"{conn_name}: {status}")
            if info.get('is_usable'):
                print(f"  引擎: {info['settings']['engine']}")
                print(f"  資料庫: {info['settings']['name']}")
        
        self.results['connections'] = connection_info
        return connection_info
    
    def generate_report(self):
        """生成性能報告"""
        print("\n" + "="*60)
        print("📊 性能分析報告")
        print("="*60)
        
        # 總結資料庫性能
        if 'database_queries' in self.results:
            total_time = sum(q['time'] for q in self.results['database_queries'])
            avg_qps = sum(q.get('query_per_second', 0) for q in self.results['database_queries']) / len(self.results['database_queries'])
            print(f"\n📈 資料庫性能總結:")
            print(f"  總查詢時間: {total_time:.4f}秒")
            print(f"  平均QPS: {avg_qps:.2f}")
        
        # 總結緩存性能
        if 'cache_performance' in self.results:
            cache_tests = self.results['cache_performance']
            if len(cache_tests) >= 2:
                cache_time = cache_tests[0]['time']
                direct_time = cache_tests[1]['time']
                if direct_time > 0:
                    speedup = direct_time / cache_time
                    print(f"\n💾 緩存性能總結:")
                    print(f"  緩存查詢: {cache_time:.4f}秒")
                    print(f"  直接查詢: {direct_time:.4f}秒")
                    print(f"  性能提升: {speedup:.2f}倍")
        
        # 總結內存使用
        if 'memory_usage' in self.results:
            mem = self.results['memory_usage']
            print(f"\n🧠 內存使用總結:")
            print(f"  進程內存: {mem['rss_mb']:.2f} MB")
            print(f"  系統使用率: {mem['system_percent']:.2f}%")
        
        # 性能建議
        print("\n💡 性能優化建議:")
        
        suggestions = []
        
        # 檢查慢查詢
        if 'database_queries' in self.results:
            slow_queries = [q for q in self.results['database_queries'] if q['time'] > 0.1]
            if slow_queries:
                suggestions.append(f"發現 {len(slow_queries)} 個慢查詢（>0.1秒），建議優化索引")
        
        # 檢查緩存效果
        if 'cache_performance' in self.results:
            cache_tests = self.results['cache_performance']
            if len(cache_tests) >= 2:
                cache_time = cache_tests[0]['time']
                direct_time = cache_tests[1]['time']
                if direct_time / cache_time < 1.5:
                    suggestions.append("緩存性能提升不明顯，建議檢查緩存策略")
        
        # 檢查內存使用
        if 'memory_usage' in self.results:
            if self.results['memory_usage']['rss_mb'] > 500:
                suggestions.append("進程內存使用較高（>500MB），建議檢查內存泄漏")
        
        if suggestions:
            for i, suggestion in enumerate(suggestions, 1):
                print(f"  {i}. {suggestion}")
        else:
            print("  ✅ 系統性能良好，無明顯問題")
        
        print("\n" + "="*60)
        
        return self.results


def main():
    """主函數"""
    print("🚀 開始性能分析")
    print("="*60)
    
    analyzer = PerformanceAnalyzer()
    
    try:
        # 執行各項分析
        analyzer.analyze_database_queries()
        analyzer.analyze_cache_performance()
        analyzer.analyze_queue_manager_performance()
        analyzer.analyze_memory_usage()
        analyzer.analyze_connection_pool()
        
        # 生成報告
        report = analyzer.generate_report()
        
        print("✅ 性能分析完成")
        return 0
        
    except Exception as e:
        print(f"❌ 性能分析失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)