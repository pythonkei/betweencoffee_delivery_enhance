# eshop/time_service.py
"""
统一的时间服务模块
整合所有分散的时间计算逻辑，确保一致性
功能来源：
  - time__utils.py (已移除，功能移入)
  - time_estimator.py (已移除，功能移入)
  - 部分原有 view_utils 时间函数
"""
import logging
import pytz
import re
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)


class UnifiedTimeService:
    """统一的时间服务类 - 替换所有分散的时间计算"""
    
    # ==================== 基础时间函数 ====================
    
    @staticmethod
    def get_hong_kong_time():
        """获取当前香港时间 - 统一入口"""
        return timezone.now().astimezone(pytz.timezone('Asia/Hong_Kong'))
    
    @staticmethod
    def format_time_for_display(dt, include_date=False):
        """统一的时间格式化"""
        if not dt:
            return "--:--"
        try:
            hk_time = dt
            if dt.tzinfo is None:
                hk_time = pytz.UTC.localize(dt)
            hk_tz = pytz.timezone('Asia/Hong_Kong')
            hk_time = hk_time.astimezone(hk_tz)
            if include_date:
                return hk_time.strftime('%Y-%m-%d %H:%M')
            else:
                return hk_time.strftime('%H:%M')
        except Exception as e:
            logger.error(f"格式化时间失败: {str(e)}")
            return "--:--"
    
    @staticmethod
    def is_time_ready(target_time):
        """检查目标时间是否已到达"""
        if not target_time:
            return True
        current_hk = UnifiedTimeService.get_hong_kong_time()
        target_hk = target_time.astimezone(pytz.timezone('Asia/Hong_Kong'))
        return current_hk >= target_hk
    
    # ==================== 剩余时间计算函数 ====================
    
    @staticmethod
    def get_remaining_minutes(target_time):
        """获取剩余分钟数（向上取整）"""
        if not target_time:
            return 0
        current_hk = UnifiedTimeService.get_hong_kong_time()
        target_hk = target_time.astimezone(pytz.timezone('Asia/Hong_Kong'))
        if current_hk >= target_hk:
            return 0
        diff = target_hk - current_hk
        return max(0, int(diff.total_seconds() / 60) + 1)  # 向上取整
    
    @staticmethod
    def calculate_remaining_time(target_time):
        """计算剩余时间（秒）"""
        if not target_time:
            return 0
        current_hk = UnifiedTimeService.get_hong_kong_time()
        if hasattr(target_time, 'tzinfo'):
            if target_time.tzinfo is None:
                target_hk = pytz.timezone('Asia/Hong_Kong').localize(target_time)
            else:
                target_hk = target_time.astimezone(pytz.timezone('Asia/Hong_Kong'))
        else:
            return 0
        if current_hk >= target_hk:
            return 0
        diff = target_hk - current_hk
        return max(0, int(diff.total_seconds()))
    
    @staticmethod
    def format_remaining_time(seconds):
        """格式化剩余时间显示"""
        if seconds < 60:
            return f"{seconds}秒"
        elif seconds < 3600:
            minutes = seconds // 60
            seconds_remaining = seconds % 60
            if seconds_remaining > 0:
                return f"{minutes}分{seconds_remaining}秒"
            return f"{minutes}分钟"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours}小时{minutes}分钟"
    
    # ==================== 进度计算函数 ====================
    
    @staticmethod
    def calculate_progress_percentage(order):
        """计算订单制作进度百分比"""
        if order.status in ['ready', 'completed']:
            return 100
        if not order.estimated_ready_time:
            return 0
        now = UnifiedTimeService.get_hong_kong_time()
        created_time = order.created_at.astimezone(pytz.timezone('Asia/Hong_Kong'))
        estimated_time = order.estimated_ready_time.astimezone(pytz.timezone('Asia/Hong_Kong'))
        if now >= estimated_time:
            return 100
        if now <= created_time:
            return 0
        total_seconds = (estimated_time - created_time).total_seconds()
        passed_seconds = (now - created_time).total_seconds()
        progress = (passed_seconds / total_seconds) * 100 if total_seconds > 0 else 0
        return max(0, min(100, int(progress)))
    
    # ==================== 统一制作时间计算 ====================
    
    @staticmethod
    def calculate_preparation_time(coffee_count):
        """统一制作时间计算"""
        if coffee_count <= 0:
            return 0
        base_time = 3      # 基础准备时间
        per_cup_time = 2   # 每杯制作时间
        return base_time + (coffee_count * per_cup_time)
    
    # ==================== 队列等待时间计算（核心）====================
    
    @staticmethod
    def _calculate_queue_wait_time():
        """计算当前队列总等待时间（分钟）"""
        from eshop.models import CoffeeQueue
        
        try:
            waiting_items = CoffeeQueue.objects.filter(status='waiting').order_by('position')
            preparing_items = CoffeeQueue.objects.filter(status='preparing')
            total_wait_time = 0.0
            
            # 1. 正在制作的订单：剩余时间
            for item in preparing_items:
                if item.estimated_completion_time:
                    remaining = max(0, (item.estimated_completion_time - timezone.now()).total_seconds() / 60)
                    total_wait_time += remaining
                else:
                    total_wait_time += item.preparation_time_minutes
            
            # 2. 等待队列的订单：完整的制作时间
            total_wait_time += sum(item.preparation_time_minutes for item in waiting_items)
            
            return round(total_wait_time, 1)
        except Exception as e:
            logger.error(f"计算队列等待时间失败: {str(e)}")
            return 0.0
    
    @staticmethod
    def _get_queue_size():
        """获取当前队列大小（等待+制作）"""
        from eshop.models import CoffeeQueue
        return CoffeeQueue.objects.filter(status__in=['waiting', 'preparing']).count()
    
    # ==================== 订单时间估算（整合自 time_estimator）====================
    
    @staticmethod
    def estimate_order_time(order, include_queue_wait=True):
        """
        估算订单的完成时间
        参数:
            order: OrderModel 实例
            include_queue_wait: 是否包含队列等待时间（默认 True）
        返回:
            dict: {
                'estimated_minutes': int,       # 总预计分钟数
                'queue_position': int/None,     # 队列位置（如果有）
                'is_immediate': bool,           # 是否立即可取
                'message': str,                 # 友好提示
                'queue_wait_minutes': int,      # 队列等待分钟
                'preparation_minutes': int,     # 制作分钟
            }
        """
        try:
            # 1. 分析订单类型
            items = order.get_items()
            has_coffee = any(item.get('type') == 'coffee' for item in items)
            has_beans = any(item.get('type') == 'bean' for item in items)
            
            # 纯咖啡豆订单：立即可取
            if has_beans and not has_coffee:
                return {
                    'estimated_minutes': 0,
                    'queue_position': None,
                    'is_immediate': True,
                    'message': '咖啡豆订单，立即可取',
                    'queue_wait_minutes': 0,
                    'preparation_minutes': 0
                }
            
            # 无咖啡的订单（纯咖啡豆已在上面处理，此处为其他商品）
            if not has_coffee:
                return {
                    'estimated_minutes': 0,
                    'queue_position': None,
                    'is_immediate': True,
                    'message': '无需制作',
                    'queue_wait_minutes': 0,
                    'preparation_minutes': 0
                }
            
            # 2. 计算咖啡杯数
            coffee_count = sum(item['quantity'] for item in items if item['type'] == 'coffee')
            preparation_minutes = UnifiedTimeService.calculate_preparation_time(coffee_count)
            
            if not include_queue_wait:
                return {
                    'estimated_minutes': preparation_minutes,
                    'queue_position': None,
                    'is_immediate': False,
                    'message': f'制作时间约 {preparation_minutes} 分钟',
                    'queue_wait_minutes': 0,
                    'preparation_minutes': preparation_minutes
                }
            
            # 3. 队列等待时间
            wait_minutes = UnifiedTimeService._calculate_queue_wait_time()
            total_minutes = preparation_minutes + wait_minutes
            
            # 4. 队列位置
            queue_position = None
            if hasattr(order, 'queue_item') and order.queue_item:
                queue_position = order.queue_item.position
            else:
                # 新订单尚未加入队列，预估位置
                queue_position = UnifiedTimeService._get_queue_size() + 1
            
            # 5. 生成友好消息
            message = UnifiedTimeService._generate_time_message(
                total_minutes, wait_minutes, preparation_minutes, queue_position
            )
            
            return {
                'estimated_minutes': int(total_minutes),
                'queue_position': queue_position,
                'is_immediate': False,
                'message': message,
                'queue_wait_minutes': int(wait_minutes),
                'preparation_minutes': preparation_minutes
            }
            
        except Exception as e:
            logger.error(f"估算订单 {order.id} 时间失败: {str(e)}")
            return {
                'estimated_minutes': 0,
                'queue_position': None,
                'is_immediate': False,
                'message': '无法估算时间',
                'queue_wait_minutes': 0,
                'preparation_minutes': 0
            }
    
    @staticmethod
    def estimate_new_order_time(coffee_count):
        """
        估算新订单（尚未创建）的完成时间
        用于订单确认页面的即时提示
        """
        wait_minutes = UnifiedTimeService._calculate_queue_wait_time()
        preparation_minutes = UnifiedTimeService.calculate_preparation_time(coffee_count)
        total_minutes = wait_minutes + preparation_minutes
        estimated_position = UnifiedTimeService._get_queue_size() + 1
        
        return {
            'total_minutes': int(total_minutes),
            'queue_wait_minutes': int(wait_minutes),
            'preparation_minutes': preparation_minutes,
            'estimated_position': estimated_position,
            'message': f"预计 {total_minutes:.0f} 分钟后可取（队列 #{estimated_position}）"
        }
    
    @staticmethod
    def _generate_time_message(total_time, wait_time, prep_time, queue_position):
        """生成时间友好消息"""
        if total_time <= 0:
            return "立即可取"
        messages = []
        if wait_time > 0:
            messages.append(f"队列等待约 {wait_time:.0f} 分钟")
        if prep_time > 0:
            messages.append(f"制作时间约 {prep_time:.0f} 分钟")
        if queue_position:
            messages.append(f"队列位置: #{queue_position}")
        base = f"预计 {total_time:.0f} 分钟后完成"
        if messages:
            base += " (" + "，".join(messages) + ")"
        return base
    
    # ==================== 订单综合时间信息（原有）====================
    
    @staticmethod
    def calculate_estimated_times(order):
        """
        统一计算订单的所有预估时间
        此方法为 `estimate_order_time` 的别名，保留向后兼容
        """
        return UnifiedTimeService.estimate_order_time(order, include_queue_wait=True)
    

    # ==================== 快速订单时间函数 ====================
    
    @staticmethod
    def calculate_quick_order_pickup_time(order):
        """计算快速订单取货时间"""
        try:
            if not order or not order.is_quick_order:
                return None
            now_hk = UnifiedTimeService.get_hong_kong_time()
            
            # ✅ 使用公開方法，不再呼叫私有方法
            minutes_to_add = UnifiedTimeService.get_minutes_from_pickup_choice(order.pickup_time_choice)
            estimated_pickup_time = now_hk + timedelta(minutes=minutes_to_add)
            pickup_time_display = UnifiedTimeService.get_pickup_time_display_from_choice(order.pickup_time_choice)
            
            # 手動計算咖啡杯數
            preparation_minutes = 0
            if order.has_coffee():
                items = order.get_items()
                coffee_count = sum(item['quantity'] for item in items if item.get('type') == 'coffee')
                preparation_minutes = UnifiedTimeService.calculate_preparation_time(coffee_count)
            
            buffer_minutes = 2
            latest_start_time = None
            if preparation_minutes > 0:
                latest_start_time = estimated_pickup_time - timedelta(minutes=(preparation_minutes + buffer_minutes))
            
            remaining_seconds = max(0, (estimated_pickup_time - now_hk).total_seconds())
            remaining_minutes = max(0, int(remaining_seconds / 60))
            
            return {
                'minutes_to_add': minutes_to_add,
                'pickup_time_display': pickup_time_display,
                'estimated_pickup_time': estimated_pickup_time,
                'estimated_pickup_display': UnifiedTimeService.format_time_for_display(estimated_pickup_time),
                'latest_start_time': latest_start_time,
                'latest_start_display': UnifiedTimeService.format_time_for_display(latest_start_time) if latest_start_time else None,
                'remaining_minutes': remaining_minutes,
                'remaining_seconds': int(remaining_seconds),
                'remaining_display': UnifiedTimeService.format_remaining_time(remaining_seconds),
                'is_past_due': now_hk >= estimated_pickup_time,
            }
        except Exception as e:
            logger.error(f"计算快速订单取货时间失败: {str(e)}")
            return None
    

    # ==================== 快速订单时间函数（公開版本）====================
    
    @staticmethod
    def get_minutes_from_pickup_choice(pickup_time_choice):
        """从取货时间选择中提取分钟数（公開方法）"""
        try:
            if isinstance(pickup_time_choice, str) and '分鐘' in pickup_time_choice:
                match = re.search(r'(\d+)', pickup_time_choice)
                if match:
                    return int(match.group(1))
            return int(pickup_time_choice) if pickup_time_choice else 5
        except (ValueError, TypeError):
            return 5
    
    @staticmethod
    def get_pickup_time_display_from_choice(pickup_time_choice):
        """统一处理取货时间选择的显示（公開方法）"""
        choice_map = {
            '5': '5分鐘後',
            '10': '10分鐘後',
            '15': '15分鐘後',
            '20': '20分鐘後',
            '30': '30分鐘後',
        }
        if not pickup_time_choice:
            return '5分鐘後'
        return choice_map.get(str(pickup_time_choice).strip(), '5分鐘後')
    
    
    # ==================== 订单取货时间格式化（防止循环依赖）====================
    
    @staticmethod
    def format_pickup_time_for_order(order):
        """为订单统一格式化取货时间信息"""
        if not order:
            return None
        
        # 纯咖啡豆订单
        if order.is_beans_only():
            return {
                'text': '隨時可取',
                'css_class': 'text-success',
                'icon': 'fa-clock',
                'is_immediate': True,
                'display_type': 'beans_only'
            }
        
        # 快速订单
        if order.is_quick_order:
            quick_order_info = UnifiedTimeService.calculate_quick_order_pickup_time(order)
            if quick_order_info:
                return {
                    'text': quick_order_info['pickup_time_display'],
                    'css_class': 'text-success',
                    'icon': 'fa-clock',
                    'estimated_time': quick_order_info['estimated_pickup_display'],
                    'remaining_minutes': quick_order_info['remaining_minutes'],
                    'remaining_display': quick_order_info['remaining_display'],
                    'is_immediate': False,
                    'display_type': 'quick_order',
                    'raw_info': quick_order_info
                }
        
        # 普通咖啡订单
        if order.has_coffee():
            return {
                'text': '製作中，請稍候',
                'css_class': 'text-info',
                'icon': 'fa-coffee',
                'is_immediate': False,
                'display_type': 'coffee_order'
            }
        
        # 默认情况
        return {
            'text': '處理中',
            'css_class': 'text-secondary',
            'icon': 'fa-hourglass-half',
            'is_immediate': False,
            'display_type': 'default'
        }
    
    # ==================== 批量处理函数 ====================
    
    @staticmethod
    def calculate_all_quick_order_times():
        """计算所有快速订单的时间信息"""
        try:
            from eshop.models import OrderModel
            quick_orders = OrderModel.objects.filter(
                is_quick_order=True,
                payment_status='paid',
                status__in=['waiting', 'preparing']
            )
            results = {}
            for order in quick_orders:
                try:
                    time_info = UnifiedTimeService.calculate_quick_order_pickup_time(order)
                    if time_info:
                        results[order.id] = time_info
                except Exception as e:
                    logger.error(f"計算訂單 {order.id} 時間失敗: {str(e)}")
                    continue
            return {
                'success': True,
                'count': len(results),
                'results': results,
                'timestamp': UnifiedTimeService.get_hong_kong_time().isoformat()
            }
        except Exception as e:
            logger.error(f"批量計算快速訂單時間失敗: {str(e)}")
            return {'success': False, 'error': str(e), 'results': {}}
    
    @staticmethod
    def update_order_pickup_times(order_ids):
        """更新指定訂單的取貨時間信息"""
        try:
            from eshop.models import OrderModel
            updated_count = 0
            error_count = 0
            for order_id in order_ids:
                try:
                    order = OrderModel.objects.get(id=order_id)
                    if order.is_quick_order:
                        time_info = UnifiedTimeService.calculate_quick_order_pickup_time(order)
                        if time_info and time_info['estimated_pickup_time']:
                            order.estimated_ready_time = time_info['estimated_pickup_time']
                            if time_info['latest_start_time']:
                                order.latest_start_time = time_info['latest_start_time']
                            order.save()
                            updated_count += 1
                except OrderModel.DoesNotExist:
                    error_count += 1
                    logger.error(f"訂單 {order_id} 不存在")
                except Exception as e:
                    error_count += 1
                    logger.error(f"更新訂單 {order_id} 取貨時間失敗: {str(e)}")
            return {
                'success': True,
                'updated_count': updated_count,
                'error_count': error_count,
                'total': len(order_ids)
            }
        except Exception as e:
            logger.error(f"批量更新訂單取貨時間失敗: {str(e)}")
            return {'success': False, 'error': str(e)}


    @staticmethod
    def calculate_pickup_time_for_quick_order(order):
        """相容舊接口 - 內部呼叫新的方法"""
        return UnifiedTimeService.calculate_quick_order_pickup_time(order)


# 全局单例实例（保持兼容性）
time_service = UnifiedTimeService()