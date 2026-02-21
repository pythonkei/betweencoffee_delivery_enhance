#!/usr/bin/env python
"""
測試緩存優化效果
"""

import os
import sys
import time
import logging

# 設置 Django 環境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'betweencoffee_delivery.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import django
django.setup()

from eshop.query_optimizer import query_optimizer
from eshop.utils.cache_optimizer import cache_optimizer
from eshop.models import OrderModel

logger = logging.getLogger(__name__)


class CacheOptimizationTest:
    """緩存優化測試"""
    
    def __init__(self):
        self.results = {}
    
    def test_cache_performance(self):
        """測試緩存性能"""
        print("\n=== 緩存性能測試 ===")
        
        # 清除舊緩存
        cache_optimizer.clear_all_cache()
        
        tests = []
        
        # 測試1: 第一次查詢（應該緩存）
        start = time.time()
        result1 = query_optimizer.get_active_orders_cached(None)
        time1 = time.time() - start
        
        tests.append({
            'name': '第一次查詢（緩存寫入）',
            'time': time1,
            'count': len(result1),
            'type': 'cache_miss'
        })
        
        # 測試2: 第二次查詢（應該從緩存讀取）
        start = time.time()
        result2 = query_optimizer.get_active_orders_cached(None)
        time2 = time.time() - start
        
        tests.append({
            'name': '第二次查詢（緩存命中）',
            'time': time2,
            'count': len(result2),
            'type': 'cache_hit'
        })
        
        # 測試3: 直接資料庫查詢對比
        start = time.time()
        direct_result = OrderModel.objects.filter(
            payment_status='paid',
            status__in=['waiting', 'preparing', 'ready']
        ).order_by('-created_at')[:50]
        direct_count = direct_result.count()
        time3 = time.time() - start
        
        tests.append({
            'name': '直接資料庫查詢',
            'time': time3,
            'count': direct_count,
            'type': 'direct'
        })
        
        # 計算性能提升
        if time3 > 0 and time2 > 0:
            speedup = time3 / time2
            print(f"緩存性能提升: {speedup:.2f}倍")
        
        # 輸出結果
        for test in tests:
            print(f"{test['name']}: {test['time']:.6f}秒, 數量: {test['count']}")
        
        self.results['cache_performance'] = tests
        return tests
    
    def test_cache_invalidation(self):
        """測試緩存失效"""
        print("\n=== 緩存失效測試 ===")
        
        # 先獲取緩存結果
        result1 = query_optimizer.get_active_orders_cached(None)
        print(f"✅ 緩存結果數量: {len(result1)}")
        
        # 使緩存失效
        invalidated_count = cache_optimizer.invalidate_cache('active_orders')
        print(f"✅ 使緩存失效: {invalidated_count} 個鍵")
        
        # 再次查詢（應該重新緩存）
        result2 = query_optimizer.get_active_orders_cached(None)
        print(f"✅ 重新緩存結果數量: {len(result2)}")
        
        # 檢查緩存版本
        cache_stats = cache_optimizer.get_cache_stats()
        print(f"✅ 緩存統計: {cache_stats}")
        
        self.results['cache_invalidation'] = {
            'invalidated_count': invalidated_count,
            'cache_stats': cache_stats
        }
        
        return True
    
    def test_smart_caching(self):
        """測試智能緩存"""
        print("\n=== 智能緩存測試 ===")
        
        from eshop.utils.cache_optimizer import CacheOptimizer
        
        # 測試空結果不緩存
        @CacheOptimizer.smart_cached_query('empty_test', min_result_size=1)
        def get_empty_result():
            return []
        
        # 第一次調用
        start = time.time()
        result1 = get_empty_result()
        time1 = time.time() - start
        
        # 第二次調用（應該還是執行查詢，因為沒緩存）
        start = time.time()
        result2 = get_empty_result()
        time2 = time.time() - start
        
        print(f"空結果測試 - 第一次: {time1:.6f}秒, 第二次: {time2:.6f}秒")
        print(f"結果是否相同: {result1 == result2}")
        
        # 測試有意義結果緩存
        @CacheOptimizer.smart_cached_query('meaningful_test', min_result_size=1)
        def get_meaningful_result():
            return [{'id': 1, 'name': 'Test'}]
        
        # 第一次調用
        start = time.time()
        result3 = get_meaningful_result()
        time3 = time.time() - start
        
        # 第二次調用（應該從緩存讀取）
        start = time.time()
        result4 = get_meaningful_result()
        time4 = time.time() - start
        
        print(f"有意義結果測試 - 第一次: {time3:.6f}秒, 第二次: {time4:.6f}秒")
        print(f"緩存性能提升: {time3/time4:.2f}倍")
        
        self.results['smart_caching'] = {
            'empty_test': {'time1': time1, 'time2': time2},
            'meaningful_test': {'time1': time3, 'time2': time4}
        }
        
        return True
    
    def test_query_optimizer_methods(self):
        """測試查詢優化器方法"""
        print("\n=== 查詢優化器方法測試 ===")
        
        tests = []
        
        # 測試隊列摘要
        try:
            start = time.time()
            queue_summary = query_optimizer.get_queue_summary_cached()
            query_time = time.time() - start
            
            tests.append({
                'name': '隊列摘要查詢',
                'time': query_time,
                'success': queue_summary is not None
            })
            
            print(f"隊列摘要查詢: {query_time:.6f}秒")
            if queue_summary:
                print(f"摘要內容: {queue_summary}")
        except Exception as e:
            print(f"⚠️ 隊列摘要查詢失敗: {str(e)}")
        
        # 測試快速訂單時間
        try:
            start = time.time()
            quick_times = query_optimizer.get_quick_order_times_cached()
            query_time = time.time() - start
            
            tests.append({
                'name': '快速訂單時間查詢',
                'time': query_time,
                'success': quick_times is not None
            })
            
            print(f"快速訂單時間查詢: {query_time:.6f}秒")
            print(f"結果數量: {len(quick_times)}")
        except Exception as e:
            print(f"⚠️ 快速訂單時間查詢失敗: {str(e)}")
        
        self.results['query_optimizer'] = tests
        return tests
    
    def generate_report(self):
        """生成測試報告"""
        print("\n" + "="*60)
        print("📊 緩存優化測試報告")
        print("="*60)
        
        # 總結緩存性能
        if 'cache_performance' in self.results:
            cache_tests = self.results['cache_performance']
            if len(cache_tests) >= 3:
                cache_miss_time = cache_tests[0]['time']
                cache_hit_time = cache_tests[1]['time']
                direct_time = cache_tests[2]['time']
                
                print(f"\n📈 緩存性能總結:")
                print(f"  緩存未命中: {cache_miss_time:.6f}秒")
                print(f"  緩存命中: {cache_hit_time:.6f}秒")
                print(f"  直接查詢: {direct_time:.6f}秒")
                
                if cache_hit_time > 0:
                    cache_speedup = cache_miss_time / cache_hit_time
                    print(f"  緩存讀取速度提升: {cache_speedup:.2f}倍")
                
                if direct_time > 0 and cache_hit_time > 0:
                    overall_speedup = direct_time / cache_hit_time
                    print(f"  總體性能提升: {overall_speedup:.2f}倍")
        
        # 總結智能緩存
        if 'smart_caching' in self.results:
            smart_results = self.results['smart_caching']
            print(f"\n🧠 智能緩存總結:")
            
            if 'meaningful_test' in smart_results:
                test = smart_results['meaningful_test']
                if test['time2'] > 0:
                    speedup = test['time1'] / test['time2']
                    print(f"  有意義結果緩存提升: {speedup:.2f}倍")
        
        # 性能建議
        print("\n💡 優化建議:")
        
        suggestions = []
        
        # 檢查緩存效果
        if 'cache_performance' in self.results:
            cache_tests = self.results['cache_performance']
            if len(cache_tests) >= 3:
                cache_hit_time = cache_tests[1]['time']
                direct_time = cache_tests[2]['time']
                
                if direct_time / cache_hit_time < 1.5:
                    suggestions.append("緩存性能提升不明顯，考慮調整緩存策略")
                else:
                    suggestions.append("✅ 緩存性能提升明顯，效果良好")
        
        if suggestions:
            for i, suggestion in enumerate(suggestions, 1):
                print(f"  {i}. {suggestion}")
        else:
            print("  ✅ 所有測試通過，緩存優化效果良好")
        
        print("\n" + "="*60)
        
        return self.results


def main():
    """主測試函數"""
    print("🚀 開始緩存優化測試")
    print("="*60)
    
    tester = CacheOptimizationTest()
    
    try:
        # 執行測試
        tester.test_cache_performance()
        tester.test_cache_invalidation()
        tester.test_smart_caching()
        tester.test_query_optimizer_methods()
        
        # 生成報告
        report = tester.generate_report()
        
        print("✅ 緩存優化測試完成")
        return 0
        
    except Exception as e:
        print(f"❌ 測試失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)