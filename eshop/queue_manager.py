# eshop/queue_manager.py
'''
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  等待区     │    │  制作区     │    │  取餐区     │
│ (waiting)   │───▶│ (preparing) │───▶│  (ready)    │
│ 尚未开始    │    │ 正在制作    │    │ 制作完成    │
└─────────────┘    └─────────────┘    └─────────────┘
等待区：排队等待制作（应计入队列位置）
制作区：正在使用资源制作（应计入当前等待时间）
取餐区：已制作完成，仅等待提取（不应计入任何队列计算）
graph TD
    A[订单支付成功] --> B{加入队列}
    B --> C[状态: waiting]
    C --> D[分配队列位置]
    D --> E[进入等待队列]
    E --> F[显示在等待列表]
    
    F --> G[咖啡师点击"开始制作"]
    G --> H[状态: preparing]
    H --> I[从等待队列移除]
    I --> J[显示在制作中列表]
    
    J --> K[咖啡师点击"标记就绪"]
    K --> L[状态: ready]
    L --> M[从制作队列移除]
    M --> N[显示在就绪列表]
    
    N --> O[顾客提取]
    O --> P[可选: 标记已提取/归档]
'''

import logging
import pytz
from django.utils import timezone
from datetime import timedelta
from .models import CoffeeQueue, OrderModel
from .time_calculation import unified_time_service  # 使用统一时间服务
from django.views.decorators.http import require_GET, require_POST
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.admin.views.decorators import staff_member_required
from .order_status_manager import OrderStatusManager

logger = logging.getLogger(__name__)



class CoffeeQueueManager:
    """咖啡制作队列管理器"""
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    

    def get_queue_summary(self):
        """获取队列摘要"""
        try:
            waiting = CoffeeQueue.objects.filter(status='waiting').count()
            preparing = CoffeeQueue.objects.filter(status='preparing').count()
            ready = CoffeeQueue.objects.filter(status='ready').count()
            
            return {
                'waiting': waiting,
                'preparing': preparing,
                'ready': ready,
                'total': waiting + preparing + ready
            }
        except Exception as e:
            self.logger.error(f"获取队列摘要失败: {str(e)}")
            return {'waiting': 0, 'preparing': 0, 'ready': 0, 'total': 0}
    

    def add_order_to_queue(self, order):
        """將訂單添加到隊列 - 修改為使用優先級"""
        try:
            logger.info(f"=== 開始將訂單 {order.id} 加入隊列 ===")
            
            # 檢查訂單是否已經在隊列中
            if CoffeeQueue.objects.filter(order=order).exists():
                logger.warning(f"訂單 {order.id} 已在隊列中")
                return CoffeeQueue.objects.get(order=order)
            
            # 計算咖啡杯數
            items = order.get_items()
            coffee_count = 0
            for item in items:
                if item.get('type') == 'coffee':
                    coffee_count += item.get('quantity', 1)
            
            logger.info(f"訂單 {order.id} 包含 {coffee_count} 杯咖啡")
            
            if coffee_count == 0:
                logger.info(f"訂單 {order.id} 不包含咖啡，跳過加入隊列")
                return None
            
            # ====== 計算優先級位置 ======
            position = self.calculate_priority_position(order, coffee_count)
            
            # 計算製作時間 - 使用统一时间服务
            preparation_time = unified_time_service.calculate_preparation_time(coffee_count)
            
            # 創建隊列項
            queue_item = CoffeeQueue.objects.create(
                order=order,
                position=position,
                coffee_count=coffee_count,
                preparation_time_minutes=preparation_time,
                status='waiting'
            )
            
            logger.info(f"創建隊列項成功: {queue_item.id}, 預計製作時間: {preparation_time}分鐘")
            
            # 檢查並重新排序隊列（確保優先級正確）
            self.check_and_reorder_queue_by_priority()
            
            # 更新隊列時間
            self.update_estimated_times()
            
            logger.info(f"訂單 {order.id} 已加入隊列，位置: {queue_item.position}")
            return queue_item
            
        except Exception as e:
            logger.error(f"添加訂單到隊列失敗: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return None


    def get_next_position(self):
        """获取下一个队列位置"""
        try:
            last_item = CoffeeQueue.objects.filter(status='waiting').order_by('-position').first()
            if last_item:
                return last_item.position + 1
            return 1
        except Exception as e:
            logger.error(f"获取下一个队列位置失败: {str(e)}")
            return 1
    

    def calculate_preparation_time(self, coffee_count):
        """统一制作时间计算 - 使用统一时间服务"""
        return unified_time_service.calculate_preparation_time(coffee_count)
    
    # 添加静态方法，可以在其他地方调用
    @staticmethod
    def get_preparation_time(coffee_count):
        """静态方法：获取制作时间 - 使用统一时间服务"""
        return unified_time_service.calculate_preparation_time(coffee_count)


    def update_estimated_times(self):
        """更新所有等待隊列項的預計時間（香港時區）- 使用统一时间服务"""
        try:
            # 先檢查並重新排序（確保順序正確）
            self.check_and_reorder_queue_by_priority()
            
            # 使用統一的香港時間函數
            current_time = unified_time_service.get_hong_kong_time()
            logger.info(f"=== 更新隊列預計時間（香港時區）===")
            logger.info(f"當前香港時間: {current_time}")
            
            # 獲取按正確順序排列的等待隊列
            waiting_queues = CoffeeQueue.objects.filter(status='waiting').order_by('position')
            
            # 計算累計時間
            cumulative_time = timedelta(minutes=0)
            processed_count = 0
            
            for queue in waiting_queues:
                try:
                    order = queue.order
                    
                    # 預計開始時間 = 當前時間 + 累計時間
                    estimated_start_time = current_time + cumulative_time
                    queue.estimated_start_time = estimated_start_time
                    
                    # 計算這個訂單的製作時間
                    prep_time = timedelta(minutes=queue.preparation_time_minutes)
                    
                    # 預計完成時間
                    queue.estimated_completion_time = estimated_start_time + prep_time
                    
                    # 保存更新
                    queue.save()
                    
                    # 更新累計時間
                    cumulative_time += prep_time
                    processed_count += 1
                    
                    # 獲取訂單類型顯示
                    order_type_display = "快速" if order.order_type == 'quick' else "普通"
                    pickup_display = f"（{order.pickup_time_choice}分鐘）" if hasattr(order, 'pickup_time_choice') and order.pickup_time_choice else ""
                    
                    logger.info(f"等待訂單 #{order.id} [{order_type_display}訂單{pickup_display}] - 位置: {queue.position}, " +
                            f"預計開始: {queue.estimated_start_time.strftime('%H:%M')}, " +
                            f"預計完成: {queue.estimated_completion_time.strftime('%H:%M')}, " +
                            f"製作時間: {queue.preparation_time_minutes}分鐘")
                    
                except Exception as e:
                    logger.error(f"處理等待訂單 #{queue.order.id if queue.order else '未知'} 失敗: {str(e)}")
                    continue
            
            logger.info(f"=== 隊列時間更新完成，處理了 {processed_count} 個等待訂單 ===")
            return True
            
        except Exception as e:
            logger.error(f"更新預計時間失敗: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return False


    def calculate_wait_time(self, queue_item):
        """计算等待时间（香港时区）- 使用统一时间服务"""
        try:
            # 如果已经是preparing状态，等待时间为0
            if queue_item.status == 'preparing':
                return 0
            
            # 获取当前香港时间 - 使用统一时间服务
            current_time = unified_time_service.get_hong_kong_time()
            
            # 如果有预计开始时间，直接计算
            if queue_item.estimated_start_time:
                # 确保 estimated_start_time 是香港时区
                if isinstance(queue_item.estimated_start_time, str):
                    from django.utils.dateparse import parse_datetime
                    estimated_start = parse_datetime(queue_item.estimated_start_time)
                    if estimated_start:
                        # 转换为香港时区
                        hk_tz = pytz.timezone('Asia/Hong_Kong')
                        if estimated_start.tzinfo is None:
                            estimated_start = pytz.UTC.localize(estimated_start)
                        estimated_start = estimated_start.astimezone(hk_tz)
                else:
                    estimated_start = queue_item.estimated_start_time
                
                if estimated_start:
                    # 计算分钟差
                    wait_delta = estimated_start - current_time
                    wait_minutes = max(0, int(wait_delta.total_seconds() / 60))
                    return wait_minutes
            
            # 否则手动计算
            # 获取当前订单之前的所有等待订单
            waiting_before = CoffeeQueue.objects.filter(
                status='waiting',
                position__lt=queue_item.position
            ).order_by('position')
            
            total_minutes = 0
            
            # 加上当前正在制作订单的剩余时间
            preparing_now = CoffeeQueue.objects.filter(status='preparing').first()
            if preparing_now and preparing_now.actual_start_time:
                elapsed = current_time - preparing_now.actual_start_time
                total_prep = timedelta(minutes=preparing_now.preparation_time_minutes)
                remaining = total_prep - elapsed
                if remaining > timedelta(0):
                    total_minutes += remaining.total_seconds() / 60
            
            # 加上前面等待订单的制作时间
            for waiting in waiting_before:
                total_minutes += waiting.preparation_time_minutes
            
            return int(total_minutes)
            
        except Exception as e:
            logger.error(f"计算等待时间失败: {str(e)}")
            return 0


    
    def add_order_to_queue_with_priority(self, order):
        """將訂單添加到隊列（考慮取貨時間優先級）"""
        try:
            logger.info(f"=== 開始將訂單 {order.id} 加入隊列（優先級版）===")
            
            # 檢查訂單是否已經在隊列中
            if CoffeeQueue.objects.filter(order=order).exists():
                logger.warning(f"訂單 {order.id} 已在隊列中")
                return CoffeeQueue.objects.get(order=order)
            
            # 計算咖啡杯數
            items = order.get_items()
            coffee_count = 0
            for item in items:
                if item.get('type') == 'coffee':
                    coffee_count += item.get('quantity', 1)
            
            logger.info(f"訂單 {order.id} 包含 {coffee_count} 杯咖啡")
            
            if coffee_count == 0:
                logger.info(f"訂單 {order.id} 不包含咖啡，跳過加入隊列")
                return None
            
            # ====== 計算優先級位置 ======
            position = self.calculate_priority_position(order, coffee_count)
            
            # 計算製作時間 - 使用统一时间服务
            preparation_time = unified_time_service.calculate_preparation_time(coffee_count)
            
            # 創建隊列項
            queue_item = CoffeeQueue.objects.create(
                order=order,
                position=position,
                coffee_count=coffee_count,
                preparation_time_minutes=preparation_time,
                status='waiting'
            )
            
            logger.info(f"創建隊列項成功: {queue_item.id}, 位置: {position}, 預計製作時間: {preparation_time}分鐘")
            
            # 更新隊列時間
            self.update_estimated_times()
            
            logger.info(f"訂單 {order.id} 已加入隊列，位置: {position}")
            return queue_item
            
        except Exception as e:
            logger.error(f"添加訂單到隊列失敗: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    


    def calculate_priority_position(self, order, coffee_count):
        """計算優先級位置（簡化版：所有快速訂單優先）"""
        try:
            # 獲取當前所有等待中的訂單
            waiting_queues = CoffeeQueue.objects.filter(status='waiting').order_by('position')
            
            # 如果沒有等待訂單，返回位置1
            if not waiting_queues.exists():
                return 1
            
            # ====== 簡化優先級邏輯 ======
            # 1. 所有快速訂單都排在普通訂單前面
            # 2. 快速訂單內部按創建時間排序（先來先做）
            # 3. 普通訂單按創建時間排序
            
            # 如果是快速訂單，插入到所有普通訂單之前，並在快速訂單中按創建時間排序
            if order.order_type == 'quick':
                for queue in waiting_queues:
                    other_order = queue.order
                    
                    # 如果遇到第一個普通訂單，快速訂單應該排在它前面
                    if other_order.order_type != 'quick':
                        return queue.position
                    
                    # 如果都是快速訂單，按創建時間排序（先來先做）
                    if order.created_at < other_order.created_at:
                        return queue.position
                
                # 如果所有訂單都是快速訂單且當前訂單創建時間最晚，添加到隊尾
                last_position = waiting_queues.last().position
                return last_position + 1
            
            else:
                # 普通訂單：添加到所有快速訂單後面
                # 找到最後一個快速訂單的位置
                last_quick_position = 0
                for queue in waiting_queues:
                    if queue.order.order_type == 'quick':
                        last_quick_position = max(last_quick_position, queue.position)
                
                # 如果沒有快速訂單，按創建時間插入到普通訂單中
                if last_quick_position == 0:
                    for queue in waiting_queues:
                        if order.created_at < queue.order.created_at:
                            return queue.position
                
                # 如果有快速訂單，插入到最後一個快速訂單之後
                return last_quick_position + 1 if last_quick_position > 0 else len(waiting_queues) + 1
                
        except Exception as e:
            logger.error(f"計算優先級位置失敗: {str(e)}")
            # 降級處理：添加到隊尾
            last_item = CoffeeQueue.objects.filter(status='waiting').order_by('-position').first()
            if last_item:
                return last_item.position + 1
            return 1
    

    def check_and_reorder_queue_by_priority(self):
        """檢查並重新排序隊列（基於優先級）- 簡化版本：所有快速訂單優先"""
        try:
            logger.info("=== 檢查隊列優先級排序（簡化版） ===")
            
            waiting_queues = CoffeeQueue.objects.filter(status='waiting')
            
            if not waiting_queues.exists():
                logger.info("等待隊列為空，無需排序")
                return False
            
            # 收集所有等待訂單的信息
            queues_with_info = []
            for queue in waiting_queues:
                order = queue.order
                info = {
                    'queue_id': queue.id,
                    'order_id': order.id,
                    'order_type': order.order_type,
                    'pickup_time_choice': getattr(order, 'pickup_time_choice', None),
                    'latest_start_time': getattr(order, 'latest_start_time', None),
                    'current_position': queue.position,
                    'coffee_count': queue.coffee_count,
                    'created_at': order.created_at,
                }
                queues_with_info.append(info)
            
            # ====== 新的優先級排序邏輯：所有快速訂單優先 ======
            # 優先級規則：
            # 1. 快速訂單（全部優先）按照創建時間排序（越早越前）
            # 2. 普通訂單按照創建時間排序（越早越前）
            def get_queue_priority(info):
                # 快速訂單優先級計算 - 所有快速訂單優先
                if info['order_type'] == 'quick':
                    # 所有快速訂單第一級都為0，按創建時間排序
                    return (0, info['created_at'].timestamp())
                
                # 普通訂單優先級計算
                # 使用創建時間的時間戳，越早的值越小
                return (1, info['created_at'].timestamp())
            
            # 排序：先按第一級（0:快速，1:普通），再按第二級（創建時間）
            queues_with_info.sort(key=get_queue_priority)
            
            # 檢查是否需要重新排序（以下代碼保持不變）
            needs_reorder = False
            for index, info in enumerate(queues_with_info, start=1):
                if info['current_position'] != index:
                    needs_reorder = True
                    break
            
            if needs_reorder:
                logger.info("檢測到隊列順序需要調整，重新排序...")
                
                # 暫時清除所有位置（避免唯一性約束衝突）
                for queue in waiting_queues:
                    queue.position = 0
                    queue.save()
                
                # 按新順序分配位置
                for index, info in enumerate(queues_with_info, start=1):
                    queue = CoffeeQueue.objects.get(id=info['queue_id'])
                    old_position = info['current_position']
                    queue.position = index
                    queue.save()
                    
                    # 獲取訂單類型顯示
                    order_type_display = "快速訂單" if info['order_type'] == 'quick' else "普通訂單"
                    pickup_display = f"（{info['pickup_time_choice']}分鐘）" if info['pickup_time_choice'] else ""
                    
                    logger.info(f"調整訂單 #{queue.order.id} 位置: {old_position} → {index} [{order_type_display}{pickup_display}]")
                
                # 更新時間估算
                self.update_estimated_times()
                logger.info("隊列優先級排序完成")
                return True
            else:
                logger.info("隊列順序正常，無需調整")
                return False
                
        except Exception as e:
            logger.error(f"檢查隊列優先級排序失敗: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return False


    def fix_queue_positions(self):
            """修复队列位置：确保ready订单不计入，waiting订单位置连续"""
            try:
                logger.info("=== 开始修复队列位置 ===")
                
                # 1. 将所有ready订单的位置设为0
                ready_updated = CoffeeQueue.objects.filter(status='ready').update(position=0)
                logger.info(f"已将 {ready_updated} 个ready订单位置设为0")
                
                # 2. 重新为waiting订单分配连续位置
                waiting_queues = CoffeeQueue.objects.filter(status='waiting').order_by('created_at')
                
                position = 1
                for queue in waiting_queues:
                    if queue.position != position:
                        logger.info(f"修复订单 #{queue.order.id} 位置: {queue.position} -> {position}")
                        queue.position = position
                        queue.save()
                    position += 1
                
                logger.info(f"重新分配了 {position-1} 个等待订单的位置")
                
                # 3. 更新预计时间
                self.update_estimated_times()
                
                logger.info("=== 队列位置修复完成 ===")
                return True
                
            except Exception as e:
                logger.error(f"修复队列位置失败: {str(e)}")
                return False


    def start_preparation(self, queue_item, barista_name=None):
        """开始制作"""
        try:
            if queue_item.status != 'waiting':
                logger.warning(f"订单 {queue_item.order.id} 状态为 {queue_item.status}，无法开始制作")
                return False
            
            queue_item.status = 'preparing'
            queue_item.actual_start_time = timezone.now()
            queue_item.barista = barista_name or '未分配'
            queue_item.save()
            
            # 重新计算后续队列项的预计时间
            self.update_estimated_times()
            
            logger.info(f"订单 {queue_item.order.id} 已开始制作")
            return True
            
        except Exception as e:
            logger.error(f"开始制作失败: {str(e)}")
            return False
    

    def verify_queue_integrity(self):
            """验证队列完整性"""
            try:
                issues = []
                
                # 检查ready订单是否有位置（不应该有）
                ready_with_position = CoffeeQueue.objects.filter(status='ready', position__gt=0)
                if ready_with_position.exists():
                    issues.append(f"发现 {ready_with_position.count()} 个ready订单有队列位置")
                
                # 检查waiting订单位置是否连续
                waiting_queues = CoffeeQueue.objects.filter(status='waiting').order_by('position')
                expected_pos = 1
                for queue in waiting_queues:
                    if queue.position != expected_pos:
                        issues.append(f"订单 #{queue.order.id} 位置不连续: {queue.position} (期望: {expected_pos})")
                    expected_pos += 1
                
                # 检查是否有重复位置
                from django.db.models import Count
                duplicate_positions = CoffeeQueue.objects.filter(status='waiting') \
                    .values('position') \
                    .annotate(count=Count('position')) \
                    .filter(count__gt=1)
                
                for dup in duplicate_positions:
                    issues.append(f"位置 {dup['position']} 有 {dup['count']} 个订单")
                
                return {
                    'has_issues': len(issues) > 0,
                    'issues': issues,
                    'waiting_count': waiting_queues.count(),
                    'preparing_count': CoffeeQueue.objects.filter(status='preparing').count(),
                    'ready_count': CoffeeQueue.objects.filter(status='ready').count()
                }
                
            except Exception as e:
                logger.error(f"验证队列完整性失败: {str(e)}")
                return {'has_issues': True, 'issues': [f"验证失败: {str(e)}"]}
    

    def mark_as_ready(self, queue_item, staff_name=None):
        """標記為已就緒 - 使用 OrderStatusManager"""
        try:
            order = queue_item.order
            
            # 檢查訂單是否已經就緒
            if order.status == 'ready':
                logger.warning(f"訂單 {order.id} 已經是就緒狀態")
                return True
            
            # 先更新隊列項的時間（為 OrderStatusManager 準備數據）
            queue_item.status = 'ready'
            queue_item.actual_completion_time = unified_time_service.get_hong_kong_time()
            
            # 如果沒有實際開始時間，設置一個
            if not queue_item.actual_start_time:
                queue_item.actual_start_time = unified_time_service.get_hong_kong_time() - timedelta(minutes=queue_item.preparation_time_minutes)
                logger.warning(f"訂單 {order.id} 沒有實際開始時間，已補設")
            
            queue_item.save()
            
            # ✅ 修復：使用 OrderStatusManager
            result = OrderStatusManager.mark_as_ready_manually(
                order_id=order.id,
                staff_name=staff_name or "queue_manager"
            )
            
            if not result.get('success'):
                logger.error(f"使用 OrderStatusManager 標記為就緒失敗: {result.get('message')}")
                return False
            
            # ✅ 確保訂單的時間與隊列項同步
            order.refresh_from_db()  # 重新加載訂單數據
            
            # 如果訂單沒有就緒時間，使用隊列項的時間
            if not order.ready_at and queue_item.actual_completion_time:
                order.ready_at = queue_item.actual_completion_time
                order.save(update_fields=['ready_at'])
            
            # 如果訂單沒有預計就緒時間，設置一個
            if not order.estimated_ready_time and queue_item.actual_completion_time:
                order.estimated_ready_time = queue_item.actual_completion_time
                order.save(update_fields=['estimated_ready_time'])
            
            logger.info(f"✅ 訂單 {order.id} 已使用 OrderStatusManager 標記為就緒，完成時間: {queue_item.actual_completion_time}")
            
            # 重新計算隊列時間
            self.update_estimated_times()
            
            return True
            
        except Exception as e:
            logger.error(f"標記為就緒失敗: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return False


    def get_preparing_orders_with_elapsed_time(self):
        """獲取製作中訂單的已用時間和剩餘時間 - 使用统一时间服务"""
        try:
            current_time = unified_time_service.get_hong_kong_time()
            preparing_queues = CoffeeQueue.objects.filter(status='preparing')
            
            result = []
            for queue in preparing_queues:
                order = queue.order
                
                elapsed_seconds = 0
                remaining_seconds = 0
                is_time_up = False
                
                if queue.actual_start_time:
                    # 確保時間有時區信息
                    if queue.actual_start_time.tzinfo is None:
                        queue.actual_start_time = pytz.UTC.localize(queue.actual_start_time)
                    
                    # 轉換為香港時間
                    hk_tz = pytz.timezone('Asia/Hong_Kong')
                    actual_start_time = queue.actual_start_time.astimezone(hk_tz)
                    
                    # 計算已用時間
                    elapsed = current_time - actual_start_time
                    elapsed_seconds = max(0, int(elapsed.total_seconds()))
                    
                    # 計算剩餘時間
                    total_prep_seconds = queue.preparation_time_minutes * 60
                    remaining_seconds = max(0, total_prep_seconds - elapsed_seconds)
                    
                    # 檢查時間是否已用完
                    is_time_up = (elapsed_seconds >= total_prep_seconds)
                
                result.append({
                    'order_id': order.id,
                    'queue_id': queue.id,
                    'elapsed_seconds': elapsed_seconds,
                    'remaining_seconds': remaining_seconds,
                    'is_time_up': is_time_up,
                    'preparation_minutes': queue.preparation_time_minutes,
                    'coffee_count': queue.coffee_count,
                    'estimated_completion_time': queue.estimated_completion_time.isoformat() if queue.estimated_completion_time else None,
                })
            
            return result
            
        except Exception as e:
            logger.error(f"獲取製作中訂單時間信息失敗: {str(e)}")
            return []


    def verify_queue_positions(self):
        """验证并修复队列位置"""
        waiting_queues = CoffeeQueue.objects.filter(status='waiting').order_by('created_at')
        
        for index, queue in enumerate(waiting_queues, start=1):
            if queue.position != index:
                print(f"修复队列位置: 订单#{queue.order.id} 从 {queue.position} 改为 {index}")
                queue.position = index
                queue.save()
        
        return True
    

    def sync_order_queue_status(self):
        """同步訂單狀態與隊列狀態 - 使用 OrderStatusManager"""
        try:
            logger.info("=== 開始同步訂單與隊列狀態 ===")
            
            from django.db import transaction
            
            with transaction.atomic():
                # 1. 查找所有已支付且狀態為 preparing 的訂單，但不在隊列中的
                preparing_orders = OrderModel.objects.filter(
                    payment_status="paid",
                    status='preparing'
                )
                
                for order in preparing_orders:
                    # 檢查訂單是否在隊列中
                    if not CoffeeQueue.objects.filter(order=order).exists():
                        logger.info(f"訂單 {order.id} 已支付且狀態為preparing，但不在隊列中，添加到隊列")
                        self.add_order_to_queue(order)
                
                # 2. 查找隊列中的訂單，更新訂單狀態
                waiting_queues = CoffeeQueue.objects.filter(status='waiting')
                for queue in waiting_queues:
                    order = queue.order
                    
                    # ✅ 修復：使用正確的條件
                    # 注意：OrderModel 已經移除了 is_paid 字段，改用 payment_status
                    if order.status != 'preparing' and order.payment_status == 'paid':
                        logger.info(f"更新隊列訂單 {order.id} 狀態為 preparing")
                        
                        # ✅ 獲取製作時間（從隊列項）
                        preparation_minutes = queue.preparation_time_minutes or 5
                        
                        # ✅ 修復：使用 OrderStatusManager
                        result = OrderStatusManager.mark_as_preparing_manually(
                            order_id=order.id,
                            barista_name="system_sync",  # 系統同步操作
                            preparation_minutes=preparation_minutes
                        )
                        
                        if not result.get('success'):
                            logger.warning(f"同步訂單 {order.id} 狀態為 preparing 失敗: {result.get('message')}")
                
                # 3. 檢查製作中的訂單，確保隊列項狀態正確
                preparing_queues = CoffeeQueue.objects.filter(status='preparing')
                for queue in preparing_queues:
                    order = queue.order
                    if order.status != 'preparing':
                        logger.info(f"訂單 {order.id} 隊列狀態為preparing但訂單狀態為{order.status}，修正訂單狀態")
                        
                        result = OrderStatusManager.mark_as_preparing_manually(
                            order_id=order.id,
                            barista_name="system_sync",
                            preparation_minutes=queue.preparation_time_minutes or 5
                        )
            
            # 4. 更新隊列時間
            self.update_estimated_times()
            
            logger.info("=== 狀態同步完成 ===")
            return True
            
        except Exception as e:
            logger.error(f"狀態同步失敗: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return False



    # ==================== 統一時間計算入口（新增） ====================

    def recalculate_all_order_times(self):
        """
        🔄 統一重新計算所有訂單時間 - 這是時間計算的統一入口
        
        為什麼需要這個方法？
        ----------
        1. 訂單時間計算分散在多個地方，容易不一致
        2. 隊列重新排序後，時間需要重新計算
        3. 快速訂單的取貨時間需要特殊處理
        
        執行順序很重要：
        ----------
        1. 先重新排序隊列（確保優先級正確）
        2. 更新快速訂單的取貨時間（基於取貨選擇）
        3. 更新隊列預計時間（基於新順序）
        4. 檢查緊急訂單（標記需要立即處理的訂單）
        
        新手注意：
        ----------
        - 這個方法確保所有時間計算的一致性
        - 每次隊列變化或優先級調整後都應該調用
        - 不會刪除或修改現有訂單，只更新時間
        """
        try:
            logger.info("🔄 === 開始統一重新計算所有訂單時間 ===")
            
            # 1️⃣ 第一步：檢查並重新排序隊列（確保優先級正確）
            logger.info("步驟1: 檢查隊列優先級排序...")
            needs_reorder = self.check_and_reorder_queue_by_priority()
            
            if needs_reorder:
                logger.info("✅ 隊列已重新排序，準備更新時間")
            else:
                logger.info("✅ 隊列順序正常，繼續時間計算")
            
            # 2️⃣ 第二步：更新快速訂單的取貨相關時間
            logger.info("步驟2: 更新快速訂單的取貨時間...")
            quick_orders_updated = 0
            
            # 獲取所有已支付的快速訂單
            from .models import OrderModel
            quick_orders = OrderModel.objects.filter(
                order_type='quick', 
                payment_status='paid'
            ).exclude(status__in=['completed', 'cancelled'])
            
            for order in quick_orders:
                try:
                    # 檢查是否有取貨時間選擇
                    if hasattr(order, 'pickup_time_choice') and order.pickup_time_choice:
                        # 重新計算取貨相關時間 - 使用统一时间服务
                        time_info = unified_time_service.calculate_quick_order_times(order)
                        if time_info:
                            order.estimated_ready_time = time_info['estimated_pickup_time']
                            order.latest_start_time = time_info['latest_start_time']
                            order.save()
                            quick_orders_updated += 1
                            
                            logger.debug(f"快速訂單 #{order.id} 時間已更新: 取貨{order.pickup_time_choice}分鐘")
                except Exception as e:
                    logger.error(f"❌ 更新快速訂單 #{order.id} 時間失敗: {str(e)}")
                    continue
            
            logger.info(f"✅ 已更新 {quick_orders_updated} 個快速訂單的取貨時間")
            
            # 3️⃣ 第三步：更新隊列預計時間（這是最重要的步驟）
            logger.info("步驟3: 更新隊列預計時間...")
            time_update_success = self.update_estimated_times()
            
            if time_update_success:
                logger.info("✅ 隊列預計時間更新成功")
            else:
                logger.warning("⚠️ 隊列預計時間更新可能不完整")
            
            # 4️⃣ 第四步：檢查緊急訂單（標記需要立即處理的訂單）
            logger.info("步驟4: 檢查緊急訂單...")
            urgent_orders_count = 0
            
            for order in quick_orders:
                try:
                    # 檢查是否應該已經在隊列中（基於最晚開始時間）
                    if hasattr(order, 'should_be_in_queue_by_now') and order.should_be_in_queue_by_now():
                        # 標記為緊急（如果模型有這個字段）
                        if hasattr(order, 'is_urgent'):
                            if not order.is_urgent:
                                order.is_urgent = True
                                order.save()
                                urgent_orders_count += 1
                                logger.info(f"⚠️ 訂單 #{order.id} 標記為緊急（超過最晚開始時間）")
                except Exception as e:
                    logger.error(f"❌ 檢查訂單 #{order.id} 緊急狀態失敗: {str(e)}")
                    continue
            
            logger.info(f"✅ 發現 {urgent_orders_count} 個緊急訂單需要立即處理")
            
            # 5️⃣ 第五步：驗證數據完整性（可選，但建議）
            logger.info("步驟5: 驗證隊列數據完整性...")
            integrity_check = self.verify_queue_integrity()
            
            if integrity_check['has_issues']:
                logger.warning(f"⚠️ 隊列完整性檢查發現問題: {len(integrity_check['issues'])} 個")
                for issue in integrity_check['issues']:
                    logger.warning(f"  - {issue}")
            else:
                logger.info("✅ 隊列數據完整性驗證通過")
            
            # 返回統計信息
            result = {
                'success': True,
                'message': '時間重新計算完成',
                'details': {
                    'queue_reordered': needs_reorder,
                    'quick_orders_updated': quick_orders_updated,
                    'urgent_orders_found': urgent_orders_count,
                    'total_quick_orders': quick_orders.count(),
                    'time_update_success': time_update_success,
                    'integrity_issues': len(integrity_check.get('issues', [])),
                    'timestamp': unified_time_service.get_hong_kong_time().isoformat()
                }
            }
            
            logger.info(f"✅ === 統一時間計算完成 ===")
            logger.info(f"📊 結果: {result}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ 統一重新計算訂單時間失敗: {str(e)}")
            logger.error(traceback.format_exc())
            
            return {
                'success': False,
                'error': str(e),
                'message': '時間重新計算失敗，請檢查系統日誌'
            }


# 在 queue_manager.py 中添加新的辅助函数
def get_hong_kong_time_now():
    """获取当前香港时间 - 使用统一时间服务"""
    return unified_time_service.get_hong_kong_time()


def sync_ready_orders_timing():
    """同步已就绪订单的时间"""
    try:
        logger.info("同步已就绪订单的时间...")
        
        # 獲取所有已就緒訂單
        ready_orders = OrderModel.objects.filter(
            status='ready',
            payment_status="paid"
        )
        
        for order in ready_orders:
            # 檢查對應的隊列項
            try:
                queue_item = CoffeeQueue.objects.get(order=order)
                # 如果隊列項有完成時間，同步到訂單
                if queue_item.actual_completion_time and not order.ready_at:
                    order.ready_at = queue_item.actual_completion_time
                    order.save()
            except CoffeeQueue.DoesNotExist:
                # 如果沒有隊列項，但訂單是就緒狀態，設置默認時間
                if not order.ready_at and order.updated_at:
                    order.ready_at = order.updated_at
                    order.save()
        
        logger.info("已就緒訂單時間同步完成")
        return True
    except Exception as e:
        logger.error(f"同步已就緒訂單時間失敗: {str(e)}")
        return False


def repair_queue_data():
    """修復隊列數據 - 用於API調用"""
    try:
        logger.info("開始修復隊列數據...")
        
        # 創建隊列管理器實例
        queue_manager = CoffeeQueueManager()
        
        # 1. 修復隊列位置
        queue_manager.fix_queue_positions()
        
        # 2. 同步訂單狀態
        queue_manager.sync_order_queue_status()
        
        # 3. 更新預計時間
        queue_manager.update_estimated_times()
        
        # 4. 同步已就緒訂單時間
        sync_ready_orders_timing()
        
        logger.info("隊列數據修復完成")
        return True
    except Exception as e:
        logger.error(f"修復隊列數據失敗: {str(e)}")
        return False

def get_queue_updates():
    """獲取隊列更新數據 - 修改為支持手動確認"""
    try:
        queue_manager = CoffeeQueueManager()
        
        # 獲取隊列摘要
        queue_summary = queue_manager.get_queue_summary()
        
        # 獲取等待訂單
        waiting_queues = CoffeeQueue.objects.filter(status='waiting').order_by('position')
        waiting_orders = []
        
        for queue in waiting_queues:
            wait_time = queue_manager.calculate_wait_time(queue)
            waiting_orders.append({
                'id': queue.order.id,
                'order_id': queue.order.id,
                'position': queue.position,
                'pickup_code': queue.order.pickup_code,
                'coffee_names': '咖啡',  # 可根據需要從訂單項目中提取具體咖啡名稱
                'coffee_count': queue.coffee_count,
                'queue_wait_minutes': wait_time,
                'estimated_start_time': queue.estimated_start_time.isoformat() if queue.estimated_start_time else None,
                'estimated_completion_time': queue.estimated_completion_time.isoformat() if queue.estimated_completion_time else None,
            })
        
        # 獲取製作中訂單 - 添加時間信息
        preparing_queues = CoffeeQueue.objects.filter(status='preparing').order_by('actual_start_time')
        preparing_orders = []
        
        for queue in preparing_queues:
            if queue.actual_start_time:
                # 計算已用時間和剩餘時間 - 使用统一时间服务
                current_time = unified_time_service.get_hong_kong_time()
                elapsed = current_time - queue.actual_start_time
                total_time = timedelta(minutes=queue.preparation_time_minutes)
                remaining = total_time - elapsed
                remaining_seconds = int(remaining.total_seconds())
                
                # 檢查是否時間已到
                is_time_up = remaining_seconds <= 0
                
                # 如果時間已到，設置剩餘時間為0，並添加標記
                if is_time_up:
                    remaining_seconds = 0
                    status_display = "已完成（等待確認）"
                else:
                    status_display = "製作中"
                    
            else:
                remaining_seconds = queue.preparation_time_minutes * 60
                is_time_up = False
                status_display = "製作中（未開始計時）"
                
            preparing_orders.append({
                'id': queue.order.id,
                'order_id': queue.order.id,
                'pickup_code': queue.order.pickup_code,
                'coffee_names': '咖啡',  # 可根據需要從訂單項目中提取具體咖啡名稱
                'coffee_count': queue.coffee_count,  # 確保這個字段存在
                'started_at': queue.actual_start_time.strftime('%H:%M') if queue.actual_start_time else '--:--',
                'estimated_completion_time': queue.estimated_completion_time.strftime('%H:%M') if queue.estimated_completion_time else '--:--',
                'remaining_seconds': remaining_seconds,
                'is_time_up': is_time_up,  # 新增：時間是否已用完
                'status_display': status_display,  # 新增：狀態顯示文本
                'requires_manual_confirmation': is_time_up,  # 新增：需要手動確認
            })
        
        # 獲取已就緒訂單（最近15分鐘內的）
        ready_queues = CoffeeQueue.objects.filter(
            status='ready',
            actual_completion_time__gte=unified_time_service.get_hong_kong_time() - timedelta(minutes=15)
        ).order_by('-actual_completion_time')
        
        ready_orders = []
        
        for queue in ready_queues:
            if queue.actual_completion_time:
                wait_minutes = int((unified_time_service.get_hong_kong_time() - queue.actual_completion_time).total_seconds() / 60)
            else:
                wait_minutes = 0
                
            ready_orders.append({
                'id': queue.order.id,
                'order_id': queue.order.id,
                'pickup_code': queue.order.pickup_code,
                'coffee_names': '咖啡',  # 可根據需要從訂單項目中提取具體咖啡名稱
                'completed_time': queue.actual_completion_time.strftime('%H:%M') if queue.actual_completion_time else '--:--',
                'wait_minutes': wait_minutes,
            })
        
        return {
            'success': True,
            'queue_summary': queue_summary,
            'waiting_orders': waiting_orders,
            'preparing_orders': preparing_orders,
            'ready_orders': ready_orders,
            'timestamp': unified_time_service.get_hong_kong_time().isoformat(),
            'requires_manual_confirmation': any(order.get('is_time_up', False) for order in preparing_orders),  # 新增：是否有需要手動確認的訂單
        }
        
    except Exception as e:
        logger.error(f"獲取隊列更新失敗: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'queue_summary': {'waiting': 0, 'preparing': 0, 'ready': 0, 'total': 0},
            'waiting_orders': [],
            'preparing_orders': [],
            'ready_orders': [],
        }
    

def force_sync_queue_and_orders():
    """强制同步队列状态和订单状态"""
    try:
        logger.info("=== 开始强制同步队列与订单状态 ===")
        
        paid_orders = OrderModel.objects.filter(
            payment_status="paid",
            status='preparing'
        )
        
        added_count = 0
        for order in paid_orders:
            items = order.get_items()
            has_coffee = any(item.get('type') == 'coffee' for item in items)
            
            if has_coffee and not CoffeeQueue.objects.filter(order=order).exists():
                logger.info(f"强制添加订单 {order.id} 到队列")
                
                coffee_count = sum(
                    item.get('quantity', 1) 
                    for item in items 
                    if item.get('type') == 'coffee'
                )
                
                if coffee_count > 0:
                    queue_status = 'waiting'
                    if order.status == 'preparing':
                        queue_status = 'preparing'
                        logger.info(f"订单 {order.id} 状态为 preparing，队列项状态设为 preparing")
                    elif order.status == 'ready':
                        queue_status = 'ready'
                        logger.info(f"订单 {order.id} 状态为 ready，队列项状态设为 ready")
                    
                    last_item = CoffeeQueue.objects.filter(status='waiting').order_by('-position').first()
                    position = last_item.position + 1 if last_item else 1
                    
                    # 使用统一时间服务计算制作时间
                    preparation_minutes = unified_time_service.calculate_preparation_time(coffee_count)
                    
                    queue_item = CoffeeQueue.objects.create(
                        order=order,
                        position=position if queue_status == 'waiting' else 0,
                        coffee_count=coffee_count,
                        preparation_time_minutes=preparation_minutes,
                        status=queue_status,
                        actual_start_time=order.preparation_started_at if queue_status == 'preparing' else None,
                        actual_completion_time=order.ready_at if queue_status == 'ready' else None
                    )
                    added_count += 1
                    logger.info(f"已创建队列项 {queue_item.id} 用于订单 {order.id}，状态: {queue_status}")
        
        # 同步队列项和订单状态
        queue_items = CoffeeQueue.objects.all()
        for queue_item in queue_items:
            order = queue_item.order
            
            if queue_item.status == 'waiting' and order.status == 'ready':
                logger.info(f"订单 {order.id} 队列状态与订单状态不一致，更新队列状态为ready")
                queue_item.status = 'ready'
                queue_item.save()
            
            elif queue_item.status == 'preparing' and order.status == 'ready':
                logger.info(f"订单 {order.id} 制作完成，更新队列状态为ready")
                queue_item.status = 'ready'
                if not queue_item.actual_completion_time:
                    queue_item.actual_completion_time = unified_time_service.get_hong_kong_time()
                queue_item.save()
        
        logger.info(f"=== 同步完成，添加了 {added_count} 个订单到队列 ===")
        return True
        
    except Exception as e:
        logger.error(f"同步失败: {str(e)}")
        return False


# 取消訂單API
def cancel_order_api(request, order_id):
    """取消訂單API - 使用 OrderStatusManager"""
    try:
        from django.http import JsonResponse
        
        order = OrderModel.objects.get(id=order_id, user=request.user)
        
        # ✅ 修復：使用正確的支付狀態檢查
        if order.payment_status == "paid":
            return JsonResponse({
                'success': False,
                'error': '訂單已支付，無法取消'
            }, status=400)
        
        # ✅ 修復：使用 OrderStatusManager
        result = OrderStatusManager.mark_as_cancelled_manually(
            order_id=order.id,
            staff_name=request.user.username,  # 使用用戶名作為操作者
            reason="用戶取消訂單"
        )
        
        if not result.get('success'):
            return JsonResponse({
                'success': False,
                'error': result.get('message', '取消訂單失敗')
            }, status=400)
        
        logger.info(f"用戶取消訂單: {order.id}, 操作者: {request.user.username}")
        
        return JsonResponse({
            'success': True,
            'message': '訂單已取消',
            'order_id': order.id
        })
        
    except OrderModel.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': '訂單不存在'
        }, status=404)
    except Exception as e:
        logger.error(f"取消訂單API錯誤: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return JsonResponse({
            'success': False,
            'error': '伺服器錯誤'
        }, status=500)


@require_GET
@login_required
def get_customer_queue_status(request, order_id):
    """获取顾客队列状态"""
    try:
        order = OrderModel.objects.get(id=order_id)
        
        # 验证权限
        if not request.user.is_staff and order.user != request.user:
            return JsonResponse({
                'success': False,
                'error': '无权查看此订单'
            }, status=403)
        
        # 检查是否有队列项
        try:
            queue_item = CoffeeQueue.objects.get(order=order)
            
            # 计算预计时间 - 使用统一时间服务
            now = unified_time_service.get_hong_kong_time()
            
            queue_info = {
                'queue_position': queue_item.position,
                'status': queue_item.status,
                'estimated_start_time': queue_item.estimated_start_time.isoformat() if queue_item.estimated_start_time else None,
                'estimated_completion_time': queue_item.estimated_completion_time.isoformat() if queue_item.estimated_completion_time else None,
                'actual_start_time': queue_item.actual_start_time.isoformat() if queue_item.actual_start_time else None,
                'actual_completion_time': queue_item.actual_completion_time.isoformat() if queue_item.actual_completion_time else None,
                'barista': queue_item.barista,
                'preparation_time_minutes': queue_item.preparation_time_minutes,
                'queue_wait_minutes': 0,
                'remaining_minutes': 0,
            }
            
            # 计算等待时间
            queue_manager = CoffeeQueueManager()
            if queue_item.status == 'waiting':
                queue_info['queue_wait_minutes'] = queue_manager.calculate_wait_time(queue_item)
            
            # 计算剩余时间
            if queue_item.status == 'preparing' and queue_item.estimated_completion_time:
                remaining_seconds = (queue_item.estimated_completion_time - now).total_seconds()
                queue_info['remaining_minutes'] = max(0, int(remaining_seconds / 60))
            
        except CoffeeQueue.DoesNotExist:
            queue_info = None
        
        response_data = {
            'success': True,
            'order_id': order.id,
            'queue_info': queue_info,
            'order_status': order.status,
            'estimated_ready_time': order.estimated_ready_time.isoformat() if order.estimated_ready_time else None,
        }
        
        return JsonResponse(response_data)
        
    except OrderModel.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': '订单不存在'
        }, status=404)
    

# 調試函數來檢查隊列狀態
def debug_queue_priority(self):
    """調試函數：顯示隊列優先級狀態"""
    try:
        logger.info("=== 隊列優先級調試信息 ===")
        
        waiting_queues = CoffeeQueue.objects.filter(status='waiting').order_by('position')
        
        logger.info(f"等待訂單總數: {waiting_queues.count()}")
        
        for queue in waiting_queues:
            order = queue.order
            
            # 獲取訂單信息
            order_type = order.order_type
            pickup_choice = getattr(order, 'pickup_time_choice', '無')
            latest_start = getattr(order, 'latest_start_time', None)
            latest_start_str = latest_start.strftime('%H:%M') if latest_start else '無'
            
            logger.info(
                f"位置 {queue.position:2d} | "
                f"訂單 #{order.id:4d} | "
                f"類型: {order_type:6s} | "
                f"取貨選擇: {pickup_choice:>3s}分鐘 | "
                f"最晚開始: {latest_start_str:5s} | "
                f"咖啡杯數: {queue.coffee_count:2d}杯 | "
                f"創建時間: {order.created_at.strftime('%H:%M')}"
            )
        
        return True
        
    except Exception as e:
        logger.error(f"調試隊列優先級失敗: {str(e)}")
        return False