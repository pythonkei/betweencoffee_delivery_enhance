# eshop/serializers.py
"""
統一的數據序列化工具
確保隊列API和訂單API返回一致的數據結構
"""

import json
import logging
from django.utils import timezone
from .models import OrderModel, CoffeeQueue, CoffeeItem, BeanItem
from .time_service import time_service

logger = logging.getLogger(__name__)


class OrderDataSerializer:
    """訂單數據序列化器 - 統一所有API返回的數據結構"""
    
    @staticmethod
    def serialize_order(order, include_queue_info=True, include_items=True):
        """
        統一序列化訂單數據
        
        Args:
            order: OrderModel 實例
            include_queue_info: 是否包含隊列信息
            include_items: 是否包含商品詳情
            
        Returns:
            統一的訂單數據字典
        """
        try:
            # 基本訂單信息
            order_data = {
                'id': order.id,
                'order_id': order.id,  # 兼容字段
                'status': order.status,
                'status_display': order.get_status_display(),
                'payment_status': order.payment_status,
                'payment_status_display': order.get_payment_status_display(),
                'payment_method': order.payment_method,
                'is_paid': order.payment_status == 'paid',
                'is_quick_order': order.is_quick_order,
                'pickup_code': order.pickup_code,
                'name': order.name or '顧客',
                'phone': order.phone or '',
                'total_price': str(order.total_price),
                'created_at': order.created_at.isoformat(),
                'updated_at': order.updated_at.isoformat(),
                'pickup_time': order.pickup_time or '儘快',
            }
            
            # 時間相關字段
            if order.estimated_ready_time:
                order_data['estimated_ready_time'] = order.estimated_ready_time.isoformat()
                order_data['estimated_ready_time_display'] = format_time_for_display(order.estimated_ready_time)
                
                # 計算剩餘時間
                now_hk = get_hong_kong_time()
                if order.estimated_ready_time > now_hk:
                    diff = order.estimated_ready_time - now_hk
                    order_data['remaining_minutes'] = max(0, int(diff.total_seconds() / 60))
                else:
                    order_data['remaining_minutes'] = 0
            else:
                order_data['estimated_ready_time'] = None
                order_data['estimated_ready_time_display'] = '等待中'
                order_data['remaining_minutes'] = 0
            
            # 商品信息
            if include_items:
                items_data = []
                try:
                    items = order.get_items_with_chinese_options()
                    for item in items:
                        item_data = {
                            'type': item.get('type', ''),
                            'name': item.get('name', ''),
                            'quantity': item.get('quantity', 1),
                            'price': str(item.get('price', 0)),
                            'total_price': str(item.get('total_price', 0)),
                            'image': item.get('image', ''),
                        }
                        
                        # 添加中文選項
                        if item.get('cup_level_cn'):
                            item_data['cup_level'] = item['cup_level_cn']
                        if item.get('milk_level_cn'):
                            item_data['milk_level'] = item['milk_level_cn']
                        if item.get('grinding_level_cn'):
                            item_data['grinding_level'] = item['grinding_level_cn']
                        if item.get('weight'):
                            item_data['weight'] = item['weight']
                        
                        items_data.append(item_data)
                except Exception as e:
                    logger.error(f"序列化商品信息失敗: {str(e)}")
                    items_data = []
                
                order_data['items'] = items_data
                order_data['item_count'] = len(items_data)
            
            # 隊列信息
            if include_queue_info:
                queue_info = OrderDataSerializer.get_queue_info_for_order(order)
                if queue_info:
                    order_data['queue_info'] = queue_info
            
            # 訂單類型標識
            try:
                items = order.get_items()
                has_coffee = any(item.get('type') == 'coffee' for item in items)
                has_beans = any(item.get('type') == 'bean' for item in items)
                
                order_data['has_coffee'] = has_coffee
                order_data['has_beans'] = has_beans
                order_data['is_beans_only'] = has_beans and not has_coffee
                order_data['is_coffee_only'] = has_coffee and not has_beans
                order_data['is_mixed_order'] = has_coffee and has_beans
            except:
                order_data['has_coffee'] = False
                order_data['has_beans'] = False
                order_data['is_beans_only'] = False
                order_data['is_coffee_only'] = False
                order_data['is_mixed_order'] = False
            
            return order_data
            
        except Exception as e:
            logger.error(f"序列化訂單 {order.id} 失敗: {str(e)}")
            # 返回最少的信息
            return {
                'id': order.id,
                'status': order.status,
                'is_paid': order.payment_status == 'paid',
                'error': '序列化失敗'
            }
    
    @staticmethod
    def get_queue_info_for_order(order):
        """獲取訂單的隊列信息"""
        try:
            queue_item = CoffeeQueue.objects.filter(order=order).first()
            if not queue_item:
                return None
            
            now_hk = get_hong_kong_time()
            
            queue_info = {
                'queue_id': queue_item.id,
                'position': queue_item.position,
                'queue_status': queue_item.status,
                'coffee_count': queue_item.coffee_count,
                'preparation_time_minutes': queue_item.preparation_time_minutes,
                'created_at': queue_item.created_at.isoformat(),
                'updated_at': queue_item.updated_at.isoformat(),
            }
            
            # 時間信息
            if queue_item.estimated_start_time:
                queue_info['estimated_start_time'] = queue_item.estimated_start_time.isoformat()
            
            if queue_item.estimated_completion_time:
                queue_info['estimated_completion_time'] = queue_item.estimated_completion_time.isoformat()
                
                # 計算隊列等待時間
                if queue_item.status == 'waiting' and queue_item.estimated_completion_time > now_hk:
                    diff = queue_item.estimated_completion_time - now_hk
                    queue_info['queue_wait_minutes'] = max(0, int(diff.total_seconds() / 60))
                else:
                    queue_info['queue_wait_minutes'] = 0
            
            # 實際時間
            if queue_item.actual_start_time:
                queue_info['actual_start_time'] = queue_item.actual_start_time.isoformat()
            if queue_item.actual_completion_time:
                queue_info['actual_completion_time'] = queue_item.actual_completion_time.isoformat()
            
            return queue_info
            
        except Exception as e:
            logger.error(f"獲取隊列信息失敗: {str(e)}")
            return None
    
    @staticmethod
    def serialize_queue_list(queue_items, include_order_info=True):
        """序列化隊列列表"""
        result = []
        for queue_item in queue_items:
            queue_data = {
                'queue_id': queue_item.id,
                'position': queue_item.position,
                'status': queue_item.status,
                'coffee_count': queue_item.coffee_count,
                'preparation_time_minutes': queue_item.preparation_time_minutes,
                'created_at': queue_item.created_at.isoformat(),
            }
            
            if include_order_info and queue_item.order:
                queue_data['order'] = OrderDataSerializer.serialize_order(
                    queue_item.order, 
                    include_queue_info=False,
                    include_items=True
                )
            
            result.append(queue_data)
        
        return result


class ApiResponseFormatter:
    """API響應格式化器 - 確保所有API返回統一的格式"""
    
    @staticmethod
    def success(data=None, message="操作成功", **kwargs):
        """成功響應格式"""
        response = {
            'success': True,
            'message': message,
            'timestamp': timezone.now().isoformat(),
        }
        
        if data is not None:
            response['data'] = data
        
        # 添加額外字段
        response.update(kwargs)
        return response
    
    @staticmethod
    def error(message="操作失敗", code=None, details=None, **kwargs):
        """錯誤響應格式"""
        response = {
            'success': False,
            'message': message,
            'timestamp': timezone.now().isoformat(),
        }
        
        if code:
            response['code'] = code
        
        if details:
            response['details'] = details
        
        # 添加額外字段
        response.update(kwargs)
        return response
    
    @staticmethod
    def paginated(data, total, page, page_size, **kwargs):
        """分頁響應格式"""
        response = {
            'success': True,
            'data': data,
            'pagination': {
                'total': total,
                'page': page,
                'page_size': page_size,
                'total_pages': (total + page_size - 1) // page_size if page_size > 0 else 0,
            },
            'timestamp': timezone.now().isoformat(),
        }
        
        # 添加額外字段
        response.update(kwargs)
        return response