"""
性能優化模塊

這個模塊負責：
1. 監控系統性能指標
2. 優化智能分配算法
3. 緩存策略優化
4. 數據庫查詢優化
"""

import logging
import time
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Count, Avg, Sum
from collections import defaultdict

logger = logging.getLogger('eshop.performance_optimizer')


class PerformanceOptimizer:
    """性能優化器 - 用於監控和優化系統性能"""
    
    def __init__(self):
        self.logger = logger
        self.metrics = defaultdict(list)
        self.optimization_history = []
        
    def record_metric(self, metric_name, value, timestamp=None):
        """
        記錄性能指標
        
        Args:
            metric_name: 指標名稱
            value: 指標值
            timestamp: 時間戳（可選）
        """
        try:
            if timestamp is None:
                timestamp = timezone.now()
            
            self.metrics[metric_name].append({
                'value': value,
                'timestamp': timestamp,
                'timestamp_iso': timestamp.isoformat()
            })
            
            # 限制每個指標的記錄數量
            if len(self.metrics[metric_name]) > 1000:
                self.metrics[metric_name] = self.metrics[metric_name][-1000:]
            
            self.logger.debug(f"記錄指標: {metric_name} = {value}")
            
        except Exception as e:
            self.logger.error(f"記錄指標失敗: {str(e)}")
    
    def get_metric_stats(self, metric_name, hours=24):
        """
        獲取指標統計
        
        Args:
            metric_name: 指標名稱
            hours: 統計的小時數
        
        Returns:
            統計數據字典
        """
        try:
            if metric_name not in self.metrics:
                return {
                    'success': False,
                    'message': f'指標 {metric_name} 沒有數據',
                    'data': None
                }
            
            cutoff_time = timezone.now() - timedelta(hours=hours)
            recent_data = [
                m for m in self.metrics[metric_name]
                if m['timestamp'] >= cutoff_time
            ]
            
            if not recent_data:
                return {
                    'success': True,
                    'message': f'指標 {metric_name} 在過去 {hours} 小時內沒有數據',
                    'data': {
                        'count': 0,
                        'average': 0,
                        'min': 0,
                        'max': 0,
                        'latest': 0
                    }
                }
            
            values = [m['value'] for m in recent_data]
            
            return {
                'success': True,
                'message': f'獲取 {metric_name} 統計成功',
                'data': {
                    'count': len(values),
                    'average': round(sum(values) / len(values), 2),
                    'min': round(min(values), 2),
                    'max': round(max(values), 2),
                    'latest': round(values[-1], 2),
                    'time_range_hours': hours,
                    'data_points': len(values)
                }
            }
            
        except Exception as e:
            self.logger.error(f"獲取指標統計失敗: {str(e)}")
            return {
                'success': False,
                'message': f'獲取統計失敗: {str(e)}',
                'data': None
            }
    
    def monitor_allocation_performance(self):
        """
        監控分配性能
        
        Returns:
            分配性能報告
        """
        try:
            from .smart_allocation import get_smart_allocator
            
            allocator = get_smart_allocator()
            system_status = allocator.get_system_status()
            
            # 記錄系統狀態指標
            self.record_metric('system.total_baristas', system_status['total_baristas'])
            self.record_metric('system.active_baristas', system_status['active_baristas'])
            self.record_metric('system.total_capacity', system_status['total_capacity'])
            self.record_metric('system.current_load', system_status['current_load'])
            self.record_metric('system.available_capacity', system_status['available_capacity'])
            self.record_metric('system.utilization_rate', system_status['utilization_rate'])
            
            # 分析員工負載均衡
            barista_details = system_status['barista_details']
            if barista_details:
                loads = [b['current_load'] for b in barista_details]
                avg_load = sum(loads) / len(loads)
                max_load = max(loads)
                min_load = min(loads)
                
                # 計算負載均衡度（0-1，1表示完全均衡）
                if max_load > 0:
                    load_balance = 1 - ((max_load - min_load) / max_load)
                else:
                    load_balance = 1.0
                
                self.record_metric('system.load_balance', load_balance)
            
            # 獲取歷史分配數據
            from .models import CoffeeQueue
            recent_allocations = CoffeeQueue.objects.filter(
                created_at__gte=timezone.now() - timedelta(hours=24)
            ).count()
            
            self.record_metric('allocations.recent_24h', recent_allocations)
            
            return {
                'success': True,
                'message': '分配性能監控完成',
                'data': {
                    'system_status': system_status,
                    'metrics_recorded': len(self.metrics),
                    'recent_allocations': recent_allocations
                }
            }
            
        except Exception as e:
            self.logger.error(f"監控分配性能失敗: {str(e)}")
            return {
                'success': False,
                'message': f'監控失敗: {str(e)}',
                'data': None
            }
    
    def optimize_allocation_strategy(self):
        """
        優化分配策略
        
        基於歷史性能數據調整分配策略
        """
        try:
            # 獲取系統狀態
            from .smart_allocation import get_smart_allocator
            allocator = get_smart_allocator()
            system_status = allocator.get_system_status()
            
            utilization_rate = system_status['utilization_rate']
            available_capacity = system_status['available_capacity']
            
            optimization_suggestions = []
            
            # 根據利用率調整策略
            if utilization_rate > 80:
                # 高利用率：優先使用最快策略
                optimization_suggestions.append({
                    'priority': 'high',
                    'title': '高利用率優化',
                    'message': f'系統利用率高 ({utilization_rate}%)，建議使用最快分配策略',
                    'recommendation': '使用 fastest 分配策略',
                    'metric': 'utilization_rate',
                    'value': utilization_rate
                })
            elif utilization_rate < 30:
                # 低利用率：可以使用均衡策略
                optimization_suggestions.append({
                    'priority': 'low',
                    'title': '低利用率優化',
                    'message': f'系統利用率低 ({utilization_rate}%)，可以使用均衡分配策略',
                    'recommendation': '使用 balanced 分配策略',
                    'metric': 'utilization_rate',
                    'value': utilization_rate
                })
            
            # 檢查可用容量
            if available_capacity == 0:
                optimization_suggestions.append({
                    'priority': 'high',
                    'title': '容量不足',
                    'message': '系統可用容量為0，需要增加員工或優化製作流程',
                    'recommendation': '增加員工或優化製作流程',
                    'metric': 'available_capacity',
                    'value': available_capacity
                })
            
            # 檢查員工負載均衡
            barista_details = system_status['barista_details']
            if barista_details and len(barista_details) >= 2:
                loads = [b['current_load'] for b in barista_details]
                max_load = max(loads)
                min_load = min(loads)
                
                if max_load - min_load >= 2:  # 負載差異較大
                    optimization_suggestions.append({
                        'priority': 'medium',
                        'title': '負載不均衡',
                        'message': f'員工負載差異較大 ({min_load}-{max_load})，建議調整分配',
                        'recommendation': '使用 round_robin 分配策略',
                        'metric': 'load_difference',
                        'value': max_load - min_load
                    })
            
            # 記錄優化歷史
            optimization_record = {
                'timestamp': timezone.now().isoformat(),
                'system_status': system_status,
                'suggestions': optimization_suggestions,
                'total_suggestions': len(optimization_suggestions)
            }
            
            self.optimization_history.append(optimization_record)
            
            # 限制歷史記錄數量
            if len(self.optimization_history) > 100:
                self.optimization_history = self.optimization_history[-100:]
            
            return {
                'success': True,
                'message': f'生成 {len(optimization_suggestions)} 個優化建議',
                'data': {
                    'optimization_suggestions': optimization_suggestions,
                    'system_status': system_status,
                    'timestamp': timezone.now().isoformat()
                }
            }
            
        except Exception as e:
            self.logger.error(f"優化分配策略失敗: {str(e)}")
            return {
                'success': False,
                'message': f'優化失敗: {str(e)}',
                'data': None
            }
    
    def optimize_database_queries(self):
        """
        優化數據庫查詢
        
        分析並優化常見的數據庫查詢
        """
        try:
            from .models import CoffeeQueue, OrderModel, Barista
            
            optimization_suggestions = []
            
            # 檢查隊列查詢
            queue_count = CoffeeQueue.objects.count()
            self.record_metric('database.queue_count', queue_count)
            
            if queue_count > 1000:
                optimization_suggestions.append({
                    'priority': 'medium',
                    'title': '隊列數據量較大',
                    'message': f'隊列數據量較大 ({queue_count} 條記錄)，建議定期清理',
                    'recommendation': '定期清理完成的隊列記錄',
                    'metric': 'queue_count',
                    'value': queue_count
                })
            
            # 檢查索引使用
            # 這裡可以擴展為實際的索引分析
            
            # 檢查查詢性能
            start_time = time.time()
            
            # 測試常見查詢
            recent_orders = OrderModel.objects.filter(
                created_at__gte=timezone.now() - timedelta(days=1)
            ).count()
            
            query_time = time.time() - start_time
            self.record_metric('database.query_time_recent_orders', query_time)
            
            if query_time > 1.0:  # 查詢時間超過1秒
                optimization_suggestions.append({
                    'priority': 'high',
                    'title': '查詢性能問題',
                    'message': f'最近訂單查詢時間較長 ({query_time:.2f}秒)',
                    'recommendation': '為 created_at 字段添加索引',
                    'metric': 'query_time',
                    'value': query_time
                })
            
            return {
                'success': True,
                'message': f'生成 {len(optimization_suggestions)} 個數據庫優化建議',
                'data': {
                    'optimization_suggestions': optimization_suggestions,
                    'database_metrics': {
                        'queue_count': queue_count,
                        'recent_orders_24h': recent_orders,
                        'query_time_recent_orders': query_time
                    }
                }
            }
            
        except Exception as e:
            self.logger.error(f"優化數據庫查詢失敗: {str(e)}")
            return {
                'success': False,
                'message': f'優化失敗: {str(e)}',
                'data': None
            }
    
    def optimize_cache_strategy(self):
        """
        優化緩存策略
        
        分析緩存使用情況並提出優化建議
        """
        try:
            from django.core.cache import cache
            
            optimization_suggestions = []
            
            # 檢查緩存使用情況
            # 這裡可以擴展為實際的緩存分析
            
            # 建議緩存熱點數據
            optimization_suggestions.append({
                'priority': 'low',
                'title': '緩存優化建議',
                'message': '建議緩存員工工作負載和系統狀態數據',
                'recommendation': '為 get_system_status() 添加緩存',
                'metric': 'cache_hit_rate',
                'value': 0  # 這裡可以添加實際的緩存命中率
            })
            
            # 建議緩存時間設置
            optimization_suggestions.append({
                'priority': 'low',
                'title': '緩存時間優化',
                'message': '根據數據更新頻率設置合理的緩存時間',
                'recommendation': '系統狀態緩存設置為30秒，員工數據緩存設置為5分鐘',
                'metric': 'cache_ttl',
                'value': 0
            })
            
            return {
                'success': True,
                'message': f'生成 {len(optimization_suggestions)} 個緩存優化建議',
                'data': {
                    'optimization_suggestions': optimization_suggestions,
                    'cache_info': {
                        'default_timeout': cache.default_timeout,
                        'cache_backend': str(cache._cache)
                    }
                }
            }
            
        except Exception as e:
            self.logger.error(f"優化緩存策略失敗: {str(e)}")
            return {
                'success': False,
                'message': f'優化失敗: {str(e)}',
                'data': None
            }
    
    def get_performance_report(self, hours=24):
        """
        獲取性能報告
        
        Args:
            hours: 報告涵蓋的小時數
        
        Returns:
            完整的性能報告
        """
        try:
            # 監控分配性能
            allocation_result = self.monitor_allocation_performance()
            
            # 優化分配策略
            optimization_result = self.optimize_allocation_strategy()
            
            # 優化數據庫查詢
            database_result = self.optimize_database_queries()
            
            # 優化緩存策略
            cache_result = self.optimize_cache_strategy()
            
            # 收集所有指標統計
            metric_stats = {}
            important_metrics = [
                'system.utilization_rate',
                'system.available_capacity',
                'system.load_balance',
                'database.query_time_recent_orders'
            ]
            
            for metric in important_metrics:
                stats = self.get_metric_stats(metric, hours)
                if stats['success']:
                    metric_stats[metric] = stats['data']
            
            # 生成報告
            report = {
                'success': True,
                'message': f'性能報告生成完成（過去 {hours} 小時）',
                'data': {
                    'report_timestamp': timezone.now().isoformat(),
                    'report_period_hours': hours,
                    'allocation_performance': allocation_result.get('data', {}),
                    'optimization_suggestions': optimization_result.get('data', {}).get('optimization_suggestions', []),
                    'database_optimization': database_result.get('data', {}),
                    'cache_optimization': cache_result.get('data', {}),
                    'metric_statistics': metric_stats,
                    'total_optimization_suggestions': (
                        len(optimization_result.get('data', {}).get('optimization_suggestions', [])) +
                        len(database_result.get('data', {}).get('optimization_suggestions', [])) +
                        len(cache_result.get('data', {}).get('optimization_suggestions', []))
                    )
                }
            }
            
            # 記錄報告生成
            self.record_metric('performance.reports_generated', 1)
            
            self.logger.info(f"性能報告生成完成: {report['data']['total_optimization_suggestions']} 個建議")
            
            return report
            
        except Exception as e:
            self.logger.error(f"生成性能報告失敗: {str(e)}")
            return {
                'success': False,
                'message': f'生成報告失敗: {str(e)}',
                'data': None
            }
    
    def clear_old_metrics(self, days_old=7):
        """
        清理舊指標數據
        
        Args:
            days_old: 清理多少天前的數據
        """
        try:
            cutoff_time = timezone.now() - timedelta(days=days_old)
            cleared_count = 0
            
            for metric_name, records in list(self.metrics.items()):
                # 過濾掉舊數據
                new_records = [
                    r for r in records 
                    if r['timestamp'] >= cutoff_time
                ]
                
                cleared_count += len(records) - len(new_records)
                self.metrics[metric_name] = new_records
                
                # 如果沒有數據了，刪除該指標
                if not new_records:
                    del self.metrics[metric_name]
            
            # 清理優化歷史
            new_history = [
                h for h in self.optimization_history
                if datetime.fromisoformat(h['timestamp']) >= cutoff_time
            ]
            history_cleared = len(self.optimization_history) - len(new_history)
            self.optimization_history = new_history
            
            total_cleared = cleared_count + history_cleared
            
            self.logger.info(f"清理舊指標數據完成: 清理了 {total_cleared} 條記錄")
            
            return {
                'success': True,
                'message': f'清理了 {total_cleared} 條舊記錄',
                'data': {
                    'metrics_cleared': cleared_count,
                    'history_cleared': history_cleared,
                    'total_cleared': total_cleared,
                    'cutoff_days': days_old
                }
            }
            
        except Exception as e:
            self.logger.error(f"清理舊指標數據失敗: {str(e)}")
            return {
                'success': False,
                'message': f'清理失敗: {str(e)}',
                'data': None
            }


# 全局實例
_performance_optimizer = None

def get_performance_optimizer():
    """獲取性能優化器實例"""
    global _performance_optimizer
    if _performance_optimizer is None:
        _performance_optimizer = PerformanceOptimizer()
    return _performance_optimizer

def generate_performance_report(hours=24):
    """生成性能報告（便捷函數）"""
    optimizer = get_performance_optimizer()
    return optimizer.get_performance_report(hours)

def monitor_system_performance():
    """監控系統性能（便捷函數）"""
    optimizer = get_performance_optimizer()
    return optimizer.monitor_allocation_performance()

def optimize_system_performance():
    """優化系統性能（便捷函數）"""
    optimizer = get_performance_optimizer()
    
    # 執行所有優化
    allocation_result = optimizer.optimize_allocation_strategy()
    database_result = optimizer.optimize_database_queries()
    cache_result = optimizer.optimize_cache_strategy()
    
    return {
        'success': True,
        'message': '系統性能優化完成',
        'data': {
            'allocation_optimization': allocation_result,
            'database_optimization': database_result,
            'cache_optimization': cache_result,
            'timestamp': timezone.now().isoformat()
        }
    }
