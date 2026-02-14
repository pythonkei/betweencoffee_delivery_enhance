# eshop/time_estimator.py
from django.utils import timezone
from datetime import timedelta
from .models import CoffeeQueue, OrderModel
import logging

logger = logging.getLogger(__name__)

class TimeEstimator:
    def __init__(self):
        self.queue_manager = CoffeeQueueManager()
    
    def estimate_order_time(self, order_id, include_queue_wait=True):
        """估算订单完成时间"""
        try:
            order = OrderModel.objects.get(id=order_id)
            
            # 检查订单类型
            items = order.get_items()
            has_coffee = any(item.get('type') == 'coffee' for item in items)
            has_beans = any(item.get('type') == 'bean' for item in items)
            
            # 如果是纯咖啡豆订单，立即可用
            if has_beans and not has_coffee:
                return {
                    'estimated_minutes': 0,
                    'queue_position': None,
                    'is_immediate': True,
                    'message': '咖啡豆订单，立即可取'
                }
            
            # 如果没有咖啡，返回0
            if not has_coffee:
                return {
                    'estimated_minutes': 0,
                    'queue_position': None,
                    'is_immediate': True,
                    'message': '无需制作'
                }
            
            # 计算咖啡杯数
            coffee_count = sum(item['quantity'] for item in items if item['type'] == 'coffee')
            
            # 基本制作时间
            base_time = self.queue_manager.calculate_preparation_time(coffee_count)
            
            if not include_queue_wait:
                return {
                    'estimated_minutes': base_time,
                    'queue_position': None,
                    'is_immediate': False,
                    'message': f'制作时间约 {base_time} 分钟'
                }
            
            # 计算队列等待时间
            wait_time = self._calculate_queue_wait_time()
            
            total_time = base_time + wait_time
            
            # 获取队列位置
            queue_position = None
            if hasattr(order, 'queue_item'):
                queue_position = order.queue_item.position
            
            return {
                'estimated_minutes': total_time,
                'queue_position': queue_position,
                'queue_wait_minutes': wait_time,
                'preparation_minutes': base_time,
                'is_immediate': False,
                'message': self._generate_time_message(total_time, wait_time, base_time, queue_position)
            }
            
        except OrderModel.DoesNotExist:
            logger.error(f"订单不存在: {order_id}")
            return {
                'estimated_minutes': 0,
                'queue_position': None,
                'is_immediate': False,
                'message': '无法估算时间'
            }
    
    def _calculate_queue_wait_time(self):
        """计算队列等待时间"""
        # 获取所有正在等待和制作的订单
        waiting_items = CoffeeQueue.objects.filter(status='waiting').order_by('position')
        preparing_items = CoffeeQueue.objects.filter(status='preparing')
        
        total_wait_time = 0
        
        # 计算正在制作的订单剩余时间
        for item in preparing_items:
            if item.estimated_completion_time:
                remaining_time = max(0, (item.estimated_completion_time - timezone.now()).total_seconds() / 60)
                total_wait_time += remaining_time
            else:
                total_wait_time += item.preparation_time_minutes
        
        # 计算等待队列的时间
        total_wait_time += sum(item.preparation_time_minutes for item in waiting_items)
        
        return round(total_wait_time, 1)
    
    def _generate_time_message(self, total_time, wait_time, prep_time, queue_position):
        """生成时间消息"""
        if total_time <= 0:
            return "立即可取"
        
        messages = []
        
        if wait_time > 0:
            messages.append(f"队列等待约 {wait_time:.0f} 分钟")
        
        if prep_time > 0:
            messages.append(f"制作时间约 {prep_time:.0f} 分钟")
        
        if queue_position:
            messages.append(f"队列位置: #{queue_position}")
        
        message = "预计 " + str(total_time) + " 分钟后完成"
        if messages:
            message += " (" + "，".join(messages) + ")"
        
        return message
    
    def estimate_new_order_time(self, coffee_count):
        """估算新订单的完成时间（用于订单确认页面）"""
        # 当前队列等待时间
        queue_wait = self._calculate_queue_wait_time()
        
        # 新订单制作时间
        preparation_time = self.queue_manager.calculate_preparation_time(coffee_count)
        
        total_time = queue_wait + preparation_time
        
        # 估算队列位置
        current_queue_size = CoffeeQueue.objects.filter(status__in=['waiting', 'preparing']).count()
        estimated_position = current_queue_size + 1
        
        return {
            'total_minutes': total_time,
            'queue_wait_minutes': queue_wait,
            'preparation_minutes': preparation_time,
            'estimated_position': estimated_position,
            'message': f"预计 {total_time:.0f} 分钟后可取（队列 #{estimated_position}）"
        }