"""
訂單項目處理器 - 統一處理訂單項目的共用模塊
從 queue_views.py 中提取的重複邏輯
"""

import logging
from typing import Dict, List, Tuple, Any, Optional

logger = logging.getLogger(__name__)


class OrderItemProcessor:
    """訂單項目處理器 - 統一處理訂單項目的共用邏輯"""
    
    @staticmethod
    def process_order_items(items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        統一處理訂單項目，提取重複邏輯
        
        參數:
            items: 訂單項目列表
            
        返回:
            包含處理結果的字典:
            {
                'all_items': List[Dict],  # 所有項目
                'coffee_items': List[Dict],  # 咖啡項目
                'bean_items': List[Dict],  # 咖啡豆項目
                'coffee_count': int,  # 咖啡總數量
                'bean_count': int,  # 咖啡豆總數量
                'has_coffee': bool,  # 是否有咖啡
                'has_beans': bool,  # 是否有咖啡豆
                'is_mixed_order': bool,  # 是否混合訂單
                'is_beans_only': bool,  # 是否僅咖啡豆
                'items_count': int,  # 項目種類數
                'items_detail': List[str],  # 項目詳細描述
                'items_display': str,  # 項目顯示文本
                'items_options': Dict[str, List[str]],  # 項目選項顯示
            }
        """
        coffee_items = []
        bean_items = []
        all_items = []
        coffee_count = 0
        bean_count = 0
        
        for item in items:
            item_type = item.get('type', 'unknown')
            item_copy = item.copy()
            
            # 處理圖片URL
            if not item_copy.get('image'):
                item_copy['image'] = OrderItemProcessor._get_default_image_url(item_type)
            
            # 分類項目
            if item_type == 'coffee':
                coffee_items.append(item_copy)
                coffee_count += item_copy.get('quantity', 1)
            elif item_type == 'bean':
                bean_items.append(item_copy)
                bean_count += item_copy.get('quantity', 1)
            
            all_items.append(item_copy)
        
        # 計算統計信息
        has_coffee = len(coffee_items) > 0
        has_beans = len(bean_items) > 0
        is_mixed_order = has_coffee and has_beans
        is_beans_only = has_beans and not has_coffee
        
        items_count = 0
        if has_coffee:
            items_count += 1
        if has_beans:
            items_count += 1
        
        # 生成詳細描述
        items_detail = []
        if coffee_count > 0:
            items_detail.append(f"咖啡{coffee_count}杯")
        if bean_count > 0:
            items_detail.append(f"咖啡豆{bean_count}包")
        
        # 生成顯示文本
        items_display = f"{items_count}項商品"
        if items_detail:
            items_display += f" - {', '.join(items_detail)}"
        
        # 生成項目選項顯示
        items_options = OrderItemProcessor._generate_items_options(all_items)
        
        return {
            'all_items': all_items,
            'coffee_items': coffee_items,
            'bean_items': bean_items,
            'coffee_count': coffee_count,
            'bean_count': bean_count,
            'has_coffee': has_coffee,
            'has_beans': has_beans,
            'is_mixed_order': is_mixed_order,
            'is_beans_only': is_beans_only,
            'items_count': items_count,
            'items_detail': items_detail,
            'items_display': items_display,
            'items_options': items_options,
        }
    
    @staticmethod
    def _get_default_image_url(item_type: str) -> str:
        """根據項目類型獲取默認圖片URL"""
        if item_type == 'coffee':
            return '/static/images/default-coffee.png'
        elif item_type == 'bean':
            return '/static/images/default-beans.png'
        else:
            return '/static/images/default-product.png'
    
    @staticmethod
    def _generate_items_options(items: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """
        生成項目選項顯示
        
        參數:
            items: 訂單項目列表
            
        返回:
            項目選項顯示字典:
            {
                'coffee_options': List[str],  # 咖啡選項顯示
                'bean_options': List[str],  # 咖啡豆選項顯示
                'all_options': List[str],  # 所有選項顯示
            }
        """
        coffee_options = []
        bean_options = []
        all_options = []
        
        for item in items:
            item_type = item.get('type', 'unknown')
            item_name = item.get('name', '未知商品')
            
            if item_type == 'coffee':
                # 咖啡選項：只顯示杯型和牛奶選項
                options = []
                if item.get('cup_level_cn'):
                    options.append(f"杯型: {item['cup_level_cn']}")
                if item.get('milk_level_cn'):
                    options.append(f"牛奶: {item['milk_level_cn']}")
                
                if options:
                    option_text = f"{item_name}: {', '.join(options)}"
                    coffee_options.append(option_text)
                    all_options.append(option_text)
                else:
                    coffee_options.append(item_name)
                    all_options.append(item_name)
                    
            elif item_type == 'bean':
                # 咖啡豆選項：顯示重量和研磨選項
                options = []
                if item.get('weight_cn'):
                    options.append(f"重量: {item['weight_cn']}")
                elif item.get('weight'):
                    options.append(f"重量: {item['weight']}")
                
                if item.get('grinding_level_cn'):
                    options.append(f"研磨: {item['grinding_level_cn']}")
                
                if options:
                    option_text = f"{item_name}: {', '.join(options)}"
                    bean_options.append(option_text)
                    all_options.append(option_text)
                else:
                    bean_options.append(item_name)
                    all_options.append(item_name)
            else:
                # 其他類型商品
                all_options.append(item_name)
        
        return {
            'coffee_options': coffee_options,
            'bean_options': bean_options,
            'all_options': all_options,
        }
    
    @staticmethod
    def calculate_total_price(order, items: List[Dict[str, Any]]) -> str:
        """
        計算訂單總價
        
        參數:
            order: 訂單對象
            items: 訂單項目列表
            
        返回:
            總價字符串
        """
        total_price = order.total_price
        if not total_price or total_price == '0.00':
            # 從項目計算總價
            total = sum(float(item.get('total_price', 0) or 0) for item in items)
            total_price = str(total)
        return total_price
    
    @staticmethod
    def prepare_order_data(
        order,
        queue_item=None,
        now=None,
        hk_tz=None,
        include_queue_info: bool = True
    ) -> Dict[str, Any]:
        """
        準備訂單數據用於顯示
        
        參數:
            order: 訂單對象
            queue_item: 隊列項對象（可選）
            now: 當前時間（可選）
            hk_tz: 香港時區（可選）
            include_queue_info: 是否包含隊列信息
            
        返回:
            訂單數據字典
        """
        from django.utils import timezone
        from eshop.time_calculation import unified_time_service
        
        # 獲取訂單項目
        items = order.get_items_with_chinese_options()
        
        # 處理項目
        item_result = OrderItemProcessor.process_order_items(items)
        
        # 獲取取貨時間信息
        pickup_time_info = unified_time_service.format_pickup_time_for_order(order)
        
        # 計算總價
        total_price = OrderItemProcessor.calculate_total_price(order, item_result['all_items'])
        
        # 基礎訂單數據
        order_data = {
            'id': order.id,
            'order_id': order.id,
            'pickup_code': order.pickup_code or '',
            'name': order.name or '顾客',
            'phone': order.phone or '',
            'total_price': total_price,
            'items': item_result['all_items'],
            'coffee_items': item_result['coffee_items'],
            'bean_items': item_result['bean_items'],
            'coffee_count': item_result['coffee_count'],
            'bean_count': item_result['bean_count'],
            'items_count': item_result['items_count'],
            'items_detail': item_result['items_detail'],
            'items_display': item_result['items_display'],
            'has_coffee': item_result['has_coffee'],
            'has_beans': item_result['has_beans'],
            'is_mixed_order': item_result['is_mixed_order'],
            'is_beans_only': item_result['is_beans_only'],
            'payment_method': order.payment_method or '',
            'is_quick_order': order.is_quick_order,
            'pickup_time_info': pickup_time_info,
            'pickup_time_display': pickup_time_info['text'] if pickup_time_info else '--',
            'pickup_time_choice': order.pickup_time_choice if hasattr(order, 'pickup_time_choice') else None,
        }
        
        # 處理時間信息
        if now and hk_tz:
            created_at_hk = order.created_at.astimezone(hk_tz) if order.created_at.tzinfo else timezone.make_aware(order.created_at, hk_tz)
            order_data['created_at'] = created_at_hk.isoformat()
            order_data['created_at_iso'] = created_at_hk.isoformat()
        
        # 處理隊列信息
        if include_queue_info and queue_item:
            order_data.update(OrderItemProcessor._prepare_queue_info(queue_item, now, hk_tz))
        
        return order_data
    
    @staticmethod
    def _prepare_queue_info(queue_item, now=None, hk_tz=None) -> Dict[str, Any]:
        """
        準備隊列信息
        
        參數:
            queue_item: 隊列項對象
            now: 當前時間（可選）
            hk_tz: 香港時區（可選）
            
        返回:
            隊列信息字典
        """
        from django.utils import timezone
        
        queue_info = {
            'queue_item_id': queue_item.id,
            'position': queue_item.position,
            'status': queue_item.status,
            'preparation_time_minutes': queue_item.preparation_time_minutes,
        }
        
        # 處理時間信息
        if now and hk_tz:
            # 估計完成時間
            if queue_item.estimated_completion_time:
                est_completion = queue_item.estimated_completion_time
                if est_completion.tzinfo is None:
                    est_completion = timezone.make_aware(est_completion)
                estimated_completion_time_hk = est_completion.astimezone(hk_tz)
                queue_info['estimated_completion_time'] = estimated_completion_time_hk.strftime('%H:%M')
                queue_info['estimated_completion_time_iso'] = estimated_completion_time_hk.isoformat()
                
                # 計算剩餘時間
                remaining_seconds = max(0, int((estimated_completion_time_hk - now).total_seconds()))
                queue_info['remaining_seconds'] = remaining_seconds
            
            # 估計開始時間
            if queue_item.estimated_start_time:
                est_start = queue_item.estimated_start_time
                if est_start.tzinfo is None:
                    est_start = timezone.make_aware(est_start)
                estimated_start_hk = est_start.astimezone(hk_tz)
                queue_info['estimated_start_time'] = estimated_start_hk.isoformat()
                queue_info['estimated_start_display'] = estimated_start_hk.strftime('%H:%M')
                
                # 計算等待時間
                wait_seconds = max(0, int((estimated_start_hk - now).total_seconds()))
                wait_minutes = max(0, int(wait_seconds / 60))
                queue_info['wait_seconds'] = wait_seconds
                queue_info['wait_display'] = f"{wait_minutes}分鐘"
        
        return queue_info
    
    @staticmethod
    def prepare_ready_order_data(order, now=None, hk_tz=None) -> Dict[str, Any]:
        """
        準備就緒訂單數據
        
        參數:
            order: 訂單對象
            now: 當前時間（可選）
            hk_tz: 香港時區（可選）
            
        返回:
            就緒訂單數據字典
        """
        from django.utils import timezone
        
        # 使用基礎處理器準備數據
        order_data = OrderItemProcessor.prepare_order_data(
            order, 
            now=now, 
            hk_tz=hk_tz,
            include_queue_info=False
        )
        
        # 添加就緒時間信息
        if order.ready_at and hk_tz:
            ready_time = order.ready_at
            if ready_time.tzinfo is None:
                ready_time = timezone.make_aware(ready_time)
            ready_at_hk = ready_time.astimezone(hk_tz)
            
            order_data['ready_at'] = ready_at_hk.isoformat()
            order_data['completed_time'] = ready_at_hk.strftime('%H:%M')
            
            # 計算等待時間
            if now and not order_data['is_beans_only']:
                wait_seconds = (now - ready_at_hk).total_seconds()
                wait_minutes = int(wait_seconds / 60)
                order_data['wait_minutes'] = wait_minutes
                order_data['wait_display'] = f"{wait_minutes}分鐘前" if wait_minutes > 0 else "刚刚"
        
        return order_data
    
    @staticmethod
    def prepare_completed_order_data(order, now=None, hk_tz=None) -> Dict[str, Any]:
        """
        準備已完成訂單數據
        
        參數:
            order: 訂單對象
            now: 當前時間（可選）
            hk_tz: 香港時區（可選）
            
        返回:
            已完成訂單數據字典
        """
        from django.utils import timezone
        
        # 使用基礎處理器準備數據
        order_data = OrderItemProcessor.prepare_order_data(
            order, 
            now=now, 
            hk_tz=hk_tz,
            include_queue_info=False
        )
        
        # 添加取餐時間信息
        if order.picked_up_at and hk_tz:
            pickup_time = order.picked_up_at
            if pickup_time.tzinfo is None:
                pickup_time = timezone.make_aware(pickup_time)
            picked_up_at_hk = pickup_time.astimezone(hk_tz)
            
            order_data['picked_up_at'] = picked_up_at_hk.isoformat()
            order_data['completed_time'] = picked_up_at_hk.strftime('%H:%M')
        
        return order_data


# 簡化函數接口
def process_order_items(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """簡化接口：處理訂單項目"""
    return OrderItemProcessor.process_order_items(items)


def prepare_order_data(order, **kwargs) -> Dict[str, Any]:
    """簡化接口：準備訂單數據"""
    return OrderItemProcessor.prepare_order_data(order, **kwargs)


def prepare_ready_order_data(order, **kwargs) -> Dict[str, Any]:
    """簡化接口：準備就緒訂單數據"""
    return OrderItemProcessor.prepare_ready_order_data(order, **kwargs)


def prepare_completed_order_data(order, **kwargs) -> Dict[str, Any]:
    """簡化接口：準備已完成訂單數據"""
    return OrderItemProcessor.prepare_completed_order_data(order, **kwargs)