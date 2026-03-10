"""
智能訂單分配系統 - 員工工作負載追蹤與智能分配

這個模塊實現了：
1. 員工工作負載實時追蹤
2. 智能訂單分配算法
3. 並行製作優化策略
4. 動態時間計算

設計原則：
- 保持員工手動操作（開始製作/標記就緒）
- 系統提供智能建議，員工做最終決定
- 最大化2名員工各2杯的並行容量
- 確保工作負載均衡
"""

import logging
import pytz
from django.utils import timezone
from datetime import timedelta
from django.db import models
from django.db.models import Q

logger = logging.getLogger(__name__)


class BaristaWorkloadManager:
    """
    員工工作負載管理器
    追蹤每個員工的當前工作狀態和容量
    """
    
    def __init__(self):
        self.logger = logging.getLogger('eshop.smart_allocation')
        self.logger.info("🔄 初始化員工工作負載管理器")
    
    def get_all_baristas(self):
        """獲取所有在崗員工"""
        from .models import Barista
        return Barista.objects.filter(is_active=True)
    
    def get_barista_workload(self, barista_id):
        """
        獲取指定員工的當前工作負載
        
        返回格式：
        {
            'barista_id': 1,
            'name': '員工A',
            'max_concurrent': 2,
            'current_load': 1,
            'available_slots': 1,
            'current_orders': [
                {'order_id': 101, 'coffee_count': 1, 'start_time': '...'}
            ],
            'efficiency_factor': 0.9
        }
        """
        from .models import Barista, CoffeeQueue
        
        try:
            barista = Barista.objects.get(id=barista_id)
            
            # 獲取該員工正在製作的訂單
            current_queues = CoffeeQueue.objects.filter(
                barista=barista.name,
                status='preparing'
            )
            
            current_orders = []
            total_coffee_count = 0
            
            for queue in current_queues:
                current_orders.append({
                    'order_id': queue.order.id,
                    'coffee_count': queue.coffee_count,
                    'start_time': queue.actual_start_time,
                    'queue_id': queue.id
                })
                total_coffee_count += queue.coffee_count
            
            available_slots = max(0, barista.max_concurrent_orders - total_coffee_count)
            
            return {
                'barista_id': barista.id,
                'name': barista.name,
                'max_concurrent': barista.max_concurrent_orders,
                'current_load': total_coffee_count,
                'available_slots': available_slots,
                'current_orders': current_orders,
                'efficiency_factor': barista.efficiency_factor,
                'is_available': barista.is_available()
            }
            
        except Barista.DoesNotExist:
            self.logger.error(f"員工 #{barista_id} 不存在")
            return None
    
    def get_all_baristas_workload(self):
        """獲取所有員工的工作負載"""
        baristas = self.get_all_baristas()
        workloads = []
        
        for barista in baristas:
            workload = self.get_barista_workload(barista.id)
            if workload:
                workloads.append(workload)
        
        # 按可用槽位排序（可用槽位多的排前面）
        workloads.sort(key=lambda x: x['available_slots'], reverse=True)
        
        return workloads
    
    def get_system_workload(self):
        """
        獲取系統整體工作負載
        
        返回格式：
        {
            'total_capacity': 總容量（杯）,
            'current_load': 當前負載（杯）,
            'available_capacity': 可用容量（杯）,
            'utilization_rate': 利用率（%）,
            'barista_count': 員工數量,
            'active_barista_count': 在崗員工數量
        }
        """
        workloads = self.get_all_baristas_workload()
        
        total_capacity = sum(w['max_concurrent'] for w in workloads)
        current_load = sum(w['current_load'] for w in workloads)
        available_capacity = sum(w['available_slots'] for w in workloads)
        
        utilization_rate = 0
        if total_capacity > 0:
            utilization_rate = round((current_load / total_capacity) * 100, 1)
        
        active_baristas = [w for w in workloads if w['is_available']]
        
        return {
            'total_capacity': total_capacity,
            'current_load': current_load,
            'available_capacity': available_capacity,
            'utilization_rate': utilization_rate,
            'barista_count': len(workloads),
            'active_barista_count': len(active_baristas)
        }
    
    def can_barista_take_order(self, barista_id, coffee_count):
        """檢查員工是否可以接單（有足夠容量）"""
        workload = self.get_barista_workload(barista_id)
        if not workload:
            return False
        
        return workload['available_slots'] >= coffee_count
    
    def assign_order_to_barista(self, order, barista_id, coffee_count):
        """
        分配訂單給員工
        
        注意：這只是記錄分配，實際開始製作需要員工手動點擊
        """
        from .models import Barista, CoffeeQueue
        
        try:
            barista = Barista.objects.get(id=barista_id)
            
            # 更新隊列項的咖啡師字段
            queue_item = CoffeeQueue.objects.filter(order=order).first()
            if queue_item:
                queue_item.barista = barista.name
                queue_item.save()
                
                self.logger.info(
                    f"✅ 訂單 #{order.id} ({coffee_count}杯) 分配給 {barista.name}"
                )
                
                return True
            else:
                self.logger.error(f"訂單 #{order.id} 沒有對應的隊列項")
                return False
                
        except Exception as e:
            self.logger.error(f"分配訂單失敗: {str(e)}")
            return False
    
    def complete_order_for_barista(self, order_id, barista_id):
        """員工完成訂單，釋放容量"""
        workload = self.get_barista_workload(barista_id)
        if workload:
            self.logger.info(
                f"✅ 員工 #{barista_id} 完成訂單 #{order_id}，釋放容量"
            )
            return True
        return False


class SmartOrderAllocator:
    """
    智能訂單分配器
    實現多種分配策略
    """
    
    def __init__(self):
        self.logger = logging.getLogger('eshop.smart_allocation')
        self.workload_manager = BaristaWorkloadManager()
        self.logger.info("🔄 初始化智能訂單分配器")
    
    def allocate_order(self, order, strategy='balanced'):
        """
        智能分配訂單
        
        參數：
        - order: OrderModel 實例
        - strategy: 分配策略 ('balanced', 'fastest', 'round_robin')
        
        返回：
        {
            'success': True/False,
            'recommended_barista_id': 推薦的員工ID,
            'recommended_barista_name': 推薦的員工名稱,
            'coffee_count': 咖啡杯數,
            'estimated_time': 預計製作時間,
            'allocation_strategy': 使用的策略,
            'message': 描述信息
        }
        """
        try:
            # 計算訂單中的咖啡杯數
            coffee_count = self._calculate_coffee_count(order)
            
            if coffee_count == 0:
                return {
                    'success': True,
                    'message': '訂單不包含咖啡，無需分配',
                    'coffee_count': 0,
                    'skip_allocation': True
                }
            
            # 獲取所有員工的工作負載
            workloads = self.workload_manager.get_all_baristas_workload()
            
            if not workloads:
                return {
                    'success': False,
                    'message': '沒有在崗員工',
                    'coffee_count': coffee_count
                }
            
            # 根據策略選擇員工
            if strategy == 'balanced':
                recommended = self._balanced_allocation(workloads, coffee_count, order)
            elif strategy == 'fastest':
                recommended = self._fastest_allocation(workloads, coffee_count, order)
            elif strategy == 'round_robin':
                recommended = self._round_robin_allocation(workloads, coffee_count, order)
            else:
                recommended = self._balanced_allocation(workloads, coffee_count, order)
            
            # 計算預計製作時間
            estimated_time = self._calculate_estimated_time(
                coffee_count, 
                recommended['efficiency_factor'] if recommended else 1.0
            )
            
            if recommended:
                return {
                    'success': True,
                    'recommended_barista_id': recommended['barista_id'],
                    'recommended_barista_name': recommended['name'],
                    'coffee_count': coffee_count,
                    'estimated_time': estimated_time,
                    'allocation_strategy': strategy,
                    'message': f"推薦分配給 {recommended['name']}，預計時間: {estimated_time}分鐘"
                }
            else:
                return {
                    'success': False,
                    'message': '沒有可用員工可以接此訂單',
                    'coffee_count': coffee_count,
                    'estimated_time': estimated_time
                }
                
        except Exception as e:
            self.logger.error(f"分配訂單失敗: {str(e)}")
            return {
                'success': False,
                'message': f'分配失敗: {str(e)}',
                'coffee_count': 0
            }
    
    def _calculate_coffee_count(self, order):
        """計算訂單中的咖啡杯數"""
        items = order.get_items()
        coffee_count = sum(
            item.get('quantity', 1) 
            for item in items 
            if item.get('type') == 'coffee'
        )
        return coffee_count
    
    def _balanced_allocation(self, workloads, coffee_count, order):
        """
        均衡分配策略
        優先選擇可用槽位足夠且當前負載較輕的員工
        """
        # 過濾可用員工（有足夠容量）
        available_baristas = [
            w for w in workloads 
            if w['available_slots'] >= coffee_count
        ]
        
        if not available_baristas:
            # 如果沒有單一員工可以接單，檢查是否可以拆分
            if coffee_count > 2:  # 超過單人最大容量
                return self._split_allocation(workloads, coffee_count, order)
            return None
        
        # 選擇負載最輕的員工
        return min(available_baristas, key=lambda x: x['current_load'])
    
    def _fastest_allocation(self, workloads, coffee_count, order):
        """
        最快完成策略
        優先選擇效率最高的員工（效率因子最小）
        """
        # 過濾可用員工
        available_baristas = [
            w for w in workloads 
            if w['available_slots'] >= coffee_count
        ]
        
        if not available_baristas:
            if coffee_count > 2:
                return self._split_allocation(workloads, coffee_count, order)
            return None
        
        # 選擇效率最高的員工（效率因子最小）
        return min(available_baristas, key=lambda x: x['efficiency_factor'])
    
    def _round_robin_allocation(self, workloads, coffee_count, order):
        """
        輪詢分配策略
        輪流分配給不同員工，確保公平
        """
        # 這裡簡單實現：選擇第一個可用員工
        # 實際實現可以記錄上次分配的員工
        available_baristas = [
            w for w in workloads 
            if w['available_slots'] >= coffee_count
        ]
        
        if not available_baristas:
            if coffee_count > 2:
                return self._split_allocation(workloads, coffee_count, order)
            return None
        
        # 簡單選擇第一個可用員工
        return available_baristas[0]
    
    def _split_allocation(self, workloads, coffee_count, order):
        """
        拆分分配策略
        當訂單超過單人容量時，拆分給多個員工
        
        返回主要負責的員工（分配較多杯數的）
        """
        # 簡單實現：選擇可用槽位最多的兩個員工
        sorted_workloads = sorted(workloads, key=lambda x: x['available_slots'], reverse=True)
        
        if len(sorted_workloads) < 2:
            return None
        
        # 嘗試分配給前兩個員工
        barista1 = sorted_workloads[0]
        barista2 = sorted_workloads[1]
        
        # 計算如何拆分
        if coffee_count == 3:
            # 3杯：2杯給員工1，1杯給員工2
            if barista1['available_slots'] >= 2 and barista2['available_slots'] >= 1:
                self.logger.info(
                    f"🔄 訂單 #{order.id} 拆分分配: "
                    f"{barista1['name']}(2杯) + {barista2['name']}(1杯)"
                )
                return barista1  # 返回主要負責的員工
            elif barista1['available_slots'] >= 1 and barista2['available_slots'] >= 2:
                self.logger.info(
                    f"🔄 訂單 #{order.id} 拆分分配: "
                    f"{barista1['name']}(1杯) + {barista2['name']}(2杯)"
                )
                return barista2  # 返回主要負責的員工
        
        elif coffee_count == 4:
            # 4杯：2杯給員工1，2杯給員工2
            if barista1['available_slots'] >= 2 and barista2['available_slots'] >= 2:
                self.logger.info(
                    f"🔄 訂單 #{order.id} 拆分分配: "
                    f"{barista1['name']}(2杯) + {barista2['name']}(2杯)"
                )
                return barista1  # 返回主要負責的員工
        
        # 無法拆分
        return None
    
    def _calculate_estimated_time(self, coffee_count, efficiency_factor=1.0):
        """
        計算預計製作時間
        
        基礎公式：第一杯5分鐘，每增加一杯+3分鐘
        考慮員工效率因子：0.8=快20%，1.2=慢20%
        """
        if coffee_count <= 0:
            return 0
        
        # 基礎時間計算
        if coffee_count == 1:
            base_minutes = 5
        else:
            base_minutes = 5 + (coffee_count - 1) * 3
        
        # 應用效率因子
        adjusted_minutes = base_minutes * efficiency_factor
        
        # 確保最小時間
        return max(2, round(adjusted_minutes, 1))
    
    def optimize_parallel_preparation(self, order):
        """
        優化並行製作策略
        分析訂單是否可以並行製作
        
        返回：
        {
            'can_parallel': True/False,
            'strategy': 'single'/'split_2_1'/'split_2_2'/'sequential',
            'estimated_time': 預計時間,
            'baristas_needed': 需要員工數,
            'split_suggestion': [2, 1] 等拆分建議
        }
        """
        coffee_count = self._calculate_coffee_count(order)
        
        if coffee_count <= 2:
            # 1-2杯：單一員工完成
            return {
                'can_parallel': False,
                'strategy': 'single',
                'estimated_time': self._calculate_estimated_time(coffee_count),
                'baristas_needed': 1,
                'split_suggestion': [coffee_count]
            }
        
        elif coffee_count == 3:
            # 3杯：可考慮拆分為2+1
            time_2_cups = self._calculate_estimated_time(2)
            time_1_cup = self._calculate_estimated_time(1)
            parallel_time = max(time_2_cups, time_1_cup)
            
            return {
                'can_parallel': True,
                'strategy': 'split_2_1',
                'estimated_time': parallel_time,
                'baristas_needed': 2,
                'split_suggestion': [2, 1],
                'time_saving': self._calculate_estimated_time(3) - parallel_time
            }
        
        elif coffee_count == 4:
            # 4杯：可拆分為2+2
            time_2_cups = self._calculate_estimated_time(2)
            
            return {
                'can_parallel': True,
                'strategy': 'split_2_2',
                'estimated_time': time_2_cups,
                'baristas_needed': 2,
                'split_suggestion': [2, 2],
                'time_saving': self._calculate_estimated_time(4) - time_2_cups
            }
        
        else:
            # 超過4杯：需要順序製作
            return {
                'can_parallel': False,
                'strategy': 'sequential',
                'estimated_time': self._calculate_estimated_time(coffee_count),
                'baristas_needed': 1,
                'split_suggestion': [coffee_count],
                'note': '超過並行容量，需要順序製作'
            }
    
    def get_system_status(self):
        """
        獲取系統整體狀態
        
        返回：
        {
            'total_baristas': 總員工數,
            'active_baristas': 在崗員工數,
            'total_capacity': 總容量（杯）,
            'current_load': 當前負載（杯）,
            'available_capacity': 可用容量（杯）,
            'utilization_rate': 利用率（%）,
            'barista_details': [...]
        }
        """
        workloads = self.workload_manager.get_all_baristas_workload()
        
        total_capacity = sum(w['max_concurrent'] for w in workloads)
        current_load = sum(w['current_load'] for w in workloads)
        available_capacity = sum(w['available_slots'] for w in workloads)
        
        utilization_rate = 0
        if total_capacity > 0:
            utilization_rate = round((current_load / total_capacity) * 100, 1)
        
        return {
            'total_baristas': len(workloads),
            'active_baristas': len([w for w in workloads if w['is_available']]),
            'total_capacity': total_capacity,
            'current_load': current_load,
            'available_capacity': available_capacity,
            'utilization_rate': utilization_rate,
            'barista_details': workloads
        }


class DynamicTimeCalculator:
    """
    動態時間計算器
    根據多種因素計算預計時間
    """
    
    def __init__(self):
        self.logger = logging.getLogger('eshop.smart_allocation')
    
    def calculate_order_preparation_time(self, order, barista_efficiency=1.0, is_quick_order=False):
        """
        計算訂單的預計製作時間
        
        參數：
        - order: OrderModel 實例
        - barista_efficiency: 員工效率因子
        - is_quick_order: 是否為快速訂單
        
        返回：預計時間（分鐘）
        """
        coffee_count = self._get_coffee_count_from_order(order)
        
        if coffee_count == 0:
            return 0
        
        # 基礎時間計算
        base_time = self._calculate_base_time(coffee_count)
        
        # 應用效率因子
        efficiency_adjusted = base_time * barista_efficiency
        
        # 快速訂單優先級調整（稍微加快）
        if is_quick_order:
            efficiency_adjusted *= 0.9  # 快速訂單加快10%
        
        # 確保最小時間
        return max(2, round(efficiency_adjusted, 1))
    
    def _get_coffee_count_from_order(self, order):
        """從訂單中獲取咖啡杯數"""
        items = order.get_items()
        return sum(
            item.get('quantity', 1) 
            for item in items 
            if item.get('type') == 'coffee'
        )
    
    def _calculate_base_time(self, coffee_count):
        """計算基礎製作時間"""
        if coffee_count <= 0:
            return 0
        elif coffee_count == 1:
            return 5
        else:
            return 5 + (coffee_count - 1) * 3
    
    def calculate_queue_wait_time(self, order, current_queue_length):
        """
        計算隊列等待時間
        
        參數：
        - order: 訂單
        - current_queue_length: 當前隊列長度
        
        返回：預計等待時間（分鐘）
        """
        coffee_count = self._get_coffee_count_from_order(order)
        
        if coffee_count == 0:
            return 0
        
        # 簡單估算：前面每個訂單平均製作時間
        avg_preparation_per_order = 8  # 分鐘
        wait_time = current_queue_length * avg_preparation_per_order
        
        return wait_time
    
    def calculate_total_estimated_time(self, order, barista_efficiency=1.0, queue_position=0):
        """
        計算總預計時間（等待時間 + 製作時間）
        
        返回：
        {
            'wait_time': 等待時間（分鐘）,
            'preparation_time': 製作時間（分鐘）,
            'total_time': 總時間（分鐘）,
            'estimated_completion': 預計完成時間
        }
        """
        from .time_calculation import unified_time_service
        
        coffee_count = self._get_coffee_count_from_order(order)
        
        if coffee_count == 0:
            return {
                'wait_time': 0,
                'preparation_time': 0,
                'total_time': 0,
                'estimated_completion': None
            }
        
        # 計算製作時間
        preparation_time = self.calculate_order_preparation_time(
            order, barista_efficiency, order.is_quick_order
        )
        
        # 計算等待時間（基於隊列位置）
        wait_time = queue_position * 5  # 簡單估算：每個位置5分鐘
        
        total_time = wait_time + preparation_time
        
        # 計算預計完成時間
        current_time = unified_time_service.get_hong_kong_time()
        estimated_completion = current_time + timedelta(minutes=total_time)
        
        return {
            'wait_time': round(wait_time, 1),
            'preparation_time': round(preparation_time, 1),
            'total_time': round(total_time, 1),
            'estimated_completion': estimated_completion
        }


# ==================== 全局輔助函數 ====================

def get_smart_allocator():
    """獲取智能分配器實例（單例模式）"""
    global _smart_allocator
    if '_smart_allocator' not in globals():
        _smart_allocator = SmartOrderAllocator()
    return _smart_allocator


def get_workload_manager():
    """獲取工作負載管理器實例（單例模式）"""
    global _workload_manager
    if '_workload_manager' not in globals():
        _workload_manager = BaristaWorkloadManager()
    return _workload_manager


def get_time_calculator():
    """獲取時間計算器實例（單例模式）"""
    global _time_calculator
    if '_time_calculator' not in globals():
        _time_calculator = DynamicTimeCalculator()
    return _time_calculator


def initialize_smart_system():
    """初始化智能系統"""
    logger.info("🔄 初始化智能訂單分配系統...")
    
    # 創建默認員工（如果不存在）
    from .models import Barista
    default_baristas = [
        {'name': '員工A', 'efficiency_factor': 0.9, 'max_concurrent_orders': 2},
        {'name': '員工B', 'efficiency_factor': 1.1, 'max_concurrent_orders': 2},
    ]
    
    for barista_data in default_baristas:
        if not Barista.objects.filter(name=barista_data['name']).exists():
            Barista.objects.create(
                name=barista_data['name'],
                efficiency_factor=barista_data['efficiency_factor'],
                max_concurrent_orders=barista_data['max_concurrent_orders'],
                is_active=True
            )
            logger.info(f"✅ 創建默認員工: {barista_data['name']}")
    
    # 初始化各個管理器
    get_smart_allocator()
    get_workload_manager()
    get_time_calculator()
    
    logger.info("✅ 智能訂單分配系統初始化完成")
    return True


def get_system_overview():
    """獲取系統概覽"""
    allocator = get_smart_allocator()
    return allocator.get_system_status()


def allocate_new_order(order_id):
    """
    為新訂單進行智能分配
    
    參數：
    - order_id: 訂單ID
    
    返回：分配結果
    """
    from .models import OrderModel
    
    try:
        order = OrderModel.objects.get(id=order_id)
        
        # 檢查訂單是否包含咖啡
        if not order.has_coffee():
            return {
                'success': True,
                'message': '訂單不包含咖啡，無需分配',
                'skip_allocation': True
            }
        
        # 使用智能分配器
        allocator = get_smart_allocator()
        result = allocator.allocate_order(order, strategy='balanced')
        
        if result['success'] and not result.get('skip_allocation'):
            # 記錄分配結果
            workload_manager = get_workload_manager()
            workload_manager.assign_order_to_barista(
                order, 
                result['recommended_barista_id'],
                result['coffee_count']
            )
        
        return result
        
    except OrderModel.DoesNotExist:
        return {
            'success': False,
            'message': f'訂單 #{order_id} 不存在'
        }
    except Exception as e:
        logger.error(f"分配新訂單失敗: {str(e)}")
        return {
            'success': False,
            'message': f'分配失敗: {str(e)}'
        }


def optimize_order_preparation(order_id):
    """
    優化訂單製作策略
    
    返回並行製作優化建議
    """
    from .models import OrderModel
    
    try:
        order = OrderModel.objects.get(id=order_id)
        
        if not order.has_coffee():
            return {
                'success': True,
                'message': '訂單不包含咖啡，無需優化',
                'optimization_applicable': False
            }
        
        allocator = get_smart_allocator()
        optimization = allocator.optimize_parallel_preparation(order)
        
        return {
            'success': True,
            'optimization': optimization,
            'order_id': order_id,
            'coffee_count': allocator._calculate_coffee_count(order)
        }
        
    except OrderModel.DoesNotExist:
        return {
            'success': False,
            'message': f'訂單 #{order_id} 不存在'
        }


def update_barista_workload(barista_id, order_id, action):
    """
    更新員工工作負載
    
    參數：
    - barista_id: 員工ID
    - order_id: 訂單ID
    - action: 'start'（開始製作）或 'complete'（完成製作）
    """
    workload_manager = get_workload_manager()
    
    if action == 'start':
        # 這裡只是記錄，實際容量檢查在分配時已經完成
        logger.info(f"員工 #{barista_id} 開始製作訂單 #{order_id}")
        return True
    elif action == 'complete':
        return workload_manager.complete_order_for_barista(order_id, barista_id)
    else:
        logger.error(f"未知的操作類型: {action}")
        return False


def get_recommendations_for_order(order_id):
    """
    獲取訂單的智能建議
    
    返回多種建議：
    1. 分配建議
    2. 製作策略建議
    3. 時間估算
    """
    from .models import OrderModel
    
    try:
        order = OrderModel.objects.get(id=order_id)
        
        if not order.has_coffee():
            return {
                'success': True,
                'message': '訂單不包含咖啡，無需建議',
                'recommendations': []
            }
        
        recommendations = []
        
        # 1. 分配建議
        allocator = get_smart_allocator()
        allocation_result = allocator.allocate_order(order)
        
        if allocation_result['success']:
            recommendations.append({
                'type': 'allocation',
                'priority': 'high',
                'title': '分配建議',
                'message': allocation_result['message'],
                'barista_name': allocation_result.get('recommended_barista_name'),
                'estimated_time': allocation_result.get('estimated_time')
            })
        
        # 2. 製作策略建議
        optimization_result = allocator.optimize_parallel_preparation(order)
        
        if optimization_result['can_parallel']:
            recommendations.append({
                'type': 'optimization',
                'priority': 'medium',
                'title': '並行製作建議',
                'message': f"建議使用{optimization_result['strategy']}策略，可節省{optimization_result.get('time_saving', 0):.1f}分鐘",
                'strategy': optimization_result['strategy'],
                'time_saving': optimization_result.get('time_saving', 0)
            })
        
        # 3. 時間估算
        time_calculator = get_time_calculator()
        
        # 獲取隊列位置
        from .models import CoffeeQueue
        queue_item = CoffeeQueue.objects.filter(order=order).first()
        queue_position = queue_item.position if queue_item else 0
        
        time_estimate = time_calculator.calculate_total_estimated_time(
            order, 
            barista_efficiency=1.0,
            queue_position=queue_position
        )
        
        recommendations.append({
            'type': 'time_estimate',
            'priority': 'low',
            'title': '時間估算',
            'message': f"預計總時間: {time_estimate['total_time']}分鐘 (等待: {time_estimate['wait_time']}分鐘, 製作: {time_estimate['preparation_time']}分鐘)",
            'wait_time': time_estimate['wait_time'],
            'preparation_time': time_estimate['preparation_time'],
            'total_time': time_estimate['total_time']
        })
        
        return {
            'success': True,
            'order_id': order_id,
            'recommendations': recommendations,
            'total_recommendations': len(recommendations)
        }
        
    except OrderModel.DoesNotExist:
        return {
            'success': False,
            'message': f'訂單 #{order_id} 不存在'
        }


# ==================== 測試函數 ====================

def test_smart_allocation():
    """測試智能分配系統"""
    logger.info("🧪 開始測試智能分配系統...")
    
    try:
        # 初始化系統
        initialize_smart_system()
        
        # 獲取系統狀態
        system_status = get_system_overview()
        logger.info(f"系統狀態: {system_status}")
        
        # 創建測試訂單
        from .models import OrderModel
        test_order = OrderModel.objects.filter(has_coffee=True).first()
        
        if test_order:
            # 測試分配
            allocation_result = allocate_new_order(test_order.id)
            logger.info(f"分配結果: {allocation_result}")
            
            # 測試優化
            optimization_result = optimize_order_preparation(test_order.id)
            logger.info(f"優化結果: {optimization_result}")
            
            # 測試建議
            recommendations_result = get_recommendations_for_order(test_order.id)
            logger.info(f"建議結果: {recommendations_result}")
            
            logger.info("✅ 智能分配系統測試完成")
            return True
        else:
            logger.warning("⚠️ 沒有找到包含咖啡的測試訂單")
            return False
            
    except Exception as e:
        logger.error(f"❌ 測試失敗: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False


# 如果直接運行此文件，執行測試
if __name__ == "__main__":
    test_smart_allocation()
