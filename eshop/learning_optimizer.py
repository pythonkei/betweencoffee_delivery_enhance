"""
學習優化器模塊

這個模塊負責：
1. 收集製作時間數據
2. 分析員工效率
3. 優化分配策略
4. 提供學習建議
"""

import logging
import json
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Avg, Count, Sum
from collections import defaultdict

logger = logging.getLogger('eshop.learning_optimizer')


class LearningOptimizer:
    """學習優化器 - 用於優化員工分配策略"""
    
    def __init__(self):
        self.logger = logger
        self.performance_data = defaultdict(list)
        self.strategy_weights = {
            'balanced': 1.0,
            'fastest': 0.8,
            'round_robin': 0.6
        }
        
    def record_performance(self, order_id, barista_id, actual_time, estimated_time):
        """
        記錄性能數據
        
        Args:
            order_id: 訂單ID
            barista_id: 員工ID
            actual_time: 實際製作時間（分鐘）
            estimated_time: 預計製作時間（分鐘）
        """
        try:
            performance_ratio = estimated_time / actual_time if actual_time > 0 else 1.0
            
            self.performance_data[barista_id].append({
                'order_id': order_id,
                'actual_time': actual_time,
                'estimated_time': estimated_time,
                'performance_ratio': performance_ratio,
                'timestamp': timezone.now().isoformat()
            })
            
            # 限制每個員工的記錄數量
            if len(self.performance_data[barista_id]) > 100:
                self.performance_data[barista_id] = self.performance_data[barista_id][-100:]
            
            self.logger.debug(
                f"記錄性能數據: 員工 #{barista_id}, "
                f"訂單 #{order_id}, "
                f"實際時間: {actual_time}分鐘, "
                f"預計時間: {estimated_time}分鐘, "
                f"性能比: {performance_ratio:.2f}"
            )
            
        except Exception as e:
            self.logger.error(f"記錄性能數據失敗: {str(e)}")
    
    def get_barista_efficiency(self, barista_id):
        """
        獲取員工效率
        
        Returns:
            效率因子 (0.5-2.0)
        """
        try:
            if barista_id not in self.performance_data:
                return 1.0  # 默認值
            
            performances = self.performance_data[barista_id]
            
            if not performances:
                return 1.0
            
            # 計算平均性能比
            total_ratio = sum(p['performance_ratio'] for p in performances)
            avg_ratio = total_ratio / len(performances)
            
            # 限制範圍
            efficiency = max(0.5, min(2.0, avg_ratio))
            
            self.logger.debug(
                f"員工 #{barista_id} 效率計算: "
                f"平均性能比: {avg_ratio:.2f}, "
                f"效率因子: {efficiency:.2f}"
            )
            
            return efficiency
            
        except Exception as e:
            self.logger.error(f"計算員工效率失敗: {str(e)}")
            return 1.0
    
    def analyze_historical_data(self, days=7):
        """
        分析歷史數據
        
        Args:
            days: 分析的天數
        
        Returns:
            分析結果字典
        """
        try:
            from .models import CoffeeQueue, Barista
            
            start_date = timezone.now() - timedelta(days=days)
            
            # 獲取完成的隊列項
            completed_queues = CoffeeQueue.objects.filter(
                status='ready',
                actual_start_time__gte=start_date,
                actual_start_time__isnull=False,
                actual_completion_time__isnull=False
            )
            
            total_orders = completed_queues.count()
            
            if total_orders == 0:
                return {
                    'success': True,
                    'message': '沒有足夠的歷史數據',
                    'data': {
                        'total_orders': 0,
                        'average_preparation_time': 0,
                        'efficiency_by_barista': {},
                        'busiest_hours': [],
                        'recommendations': []
                    }
                }
            
            # 計算平均製作時間
            avg_prep_time = completed_queues.aggregate(
                avg_time=Avg('preparation_time_minutes')
            )['avg_time'] or 0
            
            # 按員工分組統計
            efficiency_by_barista = {}
            barista_stats = {}
            
            for queue in completed_queues:
                if queue.barista and queue.barista not in barista_stats:
                    barista_stats[queue.barista] = {
                        'total_orders': 0,
                        'total_time': 0,
                        'avg_time': 0
                    }
                
                if queue.barista in barista_stats:
                    barista_stats[queue.barista]['total_orders'] += 1
                    barista_stats[queue.barista]['total_time'] += queue.preparation_time_minutes
            
            # 計算員工效率
            for barista_name, stats in barista_stats.items():
                if stats['total_orders'] > 0:
                    avg_time = stats['total_time'] / stats['total_orders']
                    efficiency = avg_prep_time / avg_time if avg_time > 0 else 1.0
                    efficiency = max(0.5, min(2.0, efficiency))
                    
                    efficiency_by_barista[barista_name] = {
                        'total_orders': stats['total_orders'],
                        'average_time': round(avg_time, 1),
                        'efficiency_factor': round(efficiency, 2)
                    }
            
            # 分析最繁忙時段
            from django.db.models.functions import ExtractHour
            hourly_stats = completed_queues.annotate(
                hour=ExtractHour('actual_start_time')
            ).values('hour').annotate(
                count=Count('id')
            ).order_by('-count')[:5]
            
            busiest_hours = [
                f"{stat['hour']}:00 ({stat['count']}訂單)"
                for stat in hourly_stats
            ]
            
            # 生成建議
            recommendations = self._generate_recommendations(
                total_orders, avg_prep_time, efficiency_by_barista
            )
            
            result = {
                'success': True,
                'message': f'分析完成，共 {total_orders} 個訂單',
                'data': {
                    'total_orders': total_orders,
                    'average_preparation_time': round(avg_prep_time, 1),
                    'efficiency_by_barista': efficiency_by_barista,
                    'busiest_hours': busiest_hours,
                    'recommendations': recommendations,
                    'analysis_period_days': days
                }
            }
            
            self.logger.info(
                f"歷史數據分析完成: "
                f"{total_orders} 訂單, "
                f"平均時間: {avg_prep_time:.1f}分鐘, "
                f"{len(efficiency_by_barista)} 個員工"
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"分析歷史數據失敗: {str(e)}")
            
            return {
                'success': False,
                'message': f'分析失敗: {str(e)}',
                'data': None
            }
    
    def _generate_recommendations(self, total_orders, avg_prep_time, efficiency_by_barista):
        """生成建議"""
        recommendations = []
        
        if total_orders < 10:
            recommendations.append({
                'priority': 'low',
                'title': '收集更多數據',
                'message': '訂單數據不足，建議收集更多數據後再進行分析'
            })
            return recommendations
        
        # 檢查效率差異
        if len(efficiency_by_barista) >= 2:
            efficiencies = [data['efficiency_factor'] for data in efficiency_by_barista.values()]
            max_eff = max(efficiencies)
            min_eff = min(efficiencies)
            
            if max_eff / min_eff > 1.5:
                recommendations.append({
                    'priority': 'medium',
                    'title': '效率差異較大',
                    'message': f'員工效率差異較大 ({min_eff:.2f}-{max_eff:.2f})，建議進行培訓或調整分配'
                })
        
        # 檢查平均時間
        if avg_prep_time > 10:
            recommendations.append({
                'priority': 'high',
                'title': '製作時間較長',
                'message': f'平均製作時間 {avg_prep_time:.1f} 分鐘較長，建議優化流程'
            })
        
        # 檢查員工負載均衡
        if len(efficiency_by_barista) >= 2:
            orders_by_barista = [data['total_orders'] for data in efficiency_by_barista.values()]
            max_orders = max(orders_by_barista)
            min_orders = min(orders_by_barista)
            
            if max_orders > min_orders * 2:
                recommendations.append({
                    'priority': 'medium',
                    'title': '工作負載不均衡',
                    'message': '員工工作負載差異較大，建議調整分配策略'
                })
        
        # 添加一般建議
        recommendations.append({
            'priority': 'low',
            'title': '持續優化',
            'message': '建議定期分析數據並調整分配策略'
        })
        
        return recommendations
    
    def optimize_strategy_weights(self):
        """
        優化策略權重
        
        基於歷史性能調整不同分配策略的權重
        """
        try:
            # 這裡可以實現更複雜的權重優化算法
            # 目前使用簡單的調整
            
            analysis_result = self.analyze_historical_data(days=3)
            
            if not analysis_result.get('success'):
                return self.strategy_weights
            
            data = analysis_result['data']
            
            # 根據平均時間調整權重
            avg_time = data.get('average_preparation_time', 8)
            
            if avg_time > 10:
                # 製作時間較長，傾向於使用最快策略
                self.strategy_weights['fastest'] = 1.2
                self.strategy_weights['balanced'] = 0.9
                self.strategy_weights['round_robin'] = 0.7
            elif avg_time < 6:
                # 製作時間較短，可以更均衡
                self.strategy_weights['balanced'] = 1.1
                self.strategy_weights['fastest'] = 0.9
                self.strategy_weights['round_robin'] = 0.8
            else:
                # 正常情況
                self.strategy_weights['balanced'] = 1.0
                self.strategy_weights['fastest'] = 0.8
                self.strategy_weights['round_robin'] = 0.6
            
            self.logger.info(
                f"策略權重優化完成: "
                f"balanced={self.strategy_weights['balanced']:.1f}, "
                f"fastest={self.strategy_weights['fastest']:.1f}, "
                f"round_robin={self.strategy_weights['round_robin']:.1f}"
            )
            
            return self.strategy_weights
            
        except Exception as e:
            self.logger.error(f"優化策略權重失敗: {str(e)}")
            return self.strategy_weights
    
    def get_optimization_suggestions(self, order_id=None):
        """
        獲取優化建議
        
        Args:
            order_id: 可選的訂單ID
        
        Returns:
            優化建議列表
        """
        try:
            suggestions = []
            
            # 分析歷史數據
            analysis_result = self.analyze_historical_data(days=3)
            
            if analysis_result.get('success'):
                data = analysis_result['data']
                
                # 添加歷史分析建議
                for rec in data.get('recommendations', []):
                    suggestions.append(rec)
            
            # 如果有訂單ID，添加特定建議
            if order_id:
                from .models import OrderModel
                try:
                    order = OrderModel.objects.get(id=order_id)
                    
                    # 檢查訂單類型
                    if order.order_type == 'quick':
                        suggestions.append({
                            'priority': 'medium',
                            'title': '快速訂單處理',
                            'message': '這是快速訂單，建議優先分配給效率最高的員工',
                            'order_id': order_id
                        })
                    
                    # 檢查咖啡杯數
                    coffee_count = sum(
                        item.get('quantity', 1) 
                        for item in order.get_items() 
                        if item.get('type') == 'coffee'
                    )
                    
                    if coffee_count > 3:
                        suggestions.append({
                            'priority': 'high',
                            'title': '大訂單處理',
                            'message': f'訂單包含 {coffee_count} 杯咖啡，建議分配給有容量的員工',
                            'order_id': order_id,
                            'coffee_count': coffee_count
                        })
                        
                except OrderModel.DoesNotExist:
                    pass
            
            # 添加系統建議
            suggestions.append({
                'priority': 'low',
                'title': '系統維護',
                'message': '建議定期清理歷史數據以保持系統性能'
            })
            
            return {
                'success': True,
                'message': f'生成 {len(suggestions)} 個建議',
                'suggestions': suggestions,
                'total_suggestions': len(suggestions)
            }
            
        except Exception as e:
            self.logger.error(f"獲取優化建議失敗: {str(e)}")
            
            return {
                'success': False,
                'message': f'獲取建議失敗: {str(e)}',
                'suggestions': [],
                'total_suggestions': 0
            }
    
    def clear_old_data(self, days_old=30):
        """
        清理舊數據
        
        Args:
            days_old: 清理多少天前的數據
        """
        try:
            cutoff_date = timezone.now() - timedelta(days=days_old)
            cutoff_iso = cutoff_date.isoformat()
            
            cleared_count = 0
            
            for barista_id, performances in list(self.performance_data.items()):
                # 過濾掉舊數據
                new_performances = [
                    p for p in performances 
                    if p['timestamp'] >= cutoff_iso
                ]
                
                cleared_count += len(performances) - len(new_performances)
                self.performance_data[barista_id] = new_performances
                
                # 如果沒有數據了，刪除該員工的記錄
                if not new_performances:
                    del self.performance_data[barista_id]
            
            self.logger.info(f"清理舊數據完成: 清理了 {cleared_count} 條記錄")
            
            return {
                'success': True,
                'message': f'清理了 {cleared_count} 條舊記錄',
                'cleared_count': cleared_count
            }
            
        except Exception as e:
            self.logger.error(f"清理舊數據失敗: {str(e)}")
            
            return {
                'success': False,
                'message': f'清理失敗: {str(e)}',
                'cleared_count': 0
            }


# 全局實例
_learning_optimizer = None

def get_learning_optimizer():
    """獲取學習優化器實例"""
    global _learning_optimizer
    if _learning_optimizer is None:
        _learning_optimizer = LearningOptimizer()
    return _learning_optimizer

def record_order_performance(order_id, barista_id, actual_time, estimated_time):
    """記錄訂單性能（便捷函數）"""
    optimizer = get_learning_optimizer()
    return optimizer.record_performance(order_id, barista_id, actual_time, estimated_time)

def get_optimization_suggestions(order_id=None):
    """獲取優化建議（便捷函數）"""
    optimizer = get_learning_optimizer()
    return optimizer.get_optimization_suggestions(order_id)

def analyze_system_performance(days=7):
    """分析系統性能（便捷函數）"""
    optimizer = get_learning_optimizer()
    return optimizer.analyze_historical_data(days)