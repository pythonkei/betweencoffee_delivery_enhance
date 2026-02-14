# eshop/views/queue_views.py
"""
佇列視圖模組 - 統一資料流版本
已移除所有冗餘和衝突的舊API函數
只保留統一資料API、操作API和必要的輔助函數
"""

import json
import logging
import traceback
from datetime import timedelta
import pytz

from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_GET, require_POST
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone
from django.core.exceptions import PermissionDenied
from django.db.models import Q

from eshop.models import OrderModel, CoffeeQueue
from eshop.order_status_manager import OrderStatusManager
from eshop.queue_manager import CoffeeQueueManager, force_sync_queue_and_orders
from eshop.time_service import time_service   # ✅ 唯一時間服務

logger = logging.getLogger(__name__)


# ==================== 队列管理页面 ====================

@login_required
@staff_member_required
def queue_management(request):
    """队列管理主页面"""
    return render(request, 'eshop/queue_dashboard.html')


@login_required
@staff_member_required
def queue_dashboard(request):
    """队列仪表板"""
    return render(request, 'eshop/queue_dashboard.html')


@login_required
@staff_member_required
def staff_order_management(request):
    """员工订单管理页面"""
    try:
        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        total_orders_today = OrderModel.objects.filter(
            created_at__gte=today_start
        ).count()
        
        context = {
            'total_orders_today': total_orders_today,
            'current_time': now,
        }
        
        return render(request, 'admin/staff_order_management.html', context)
        
    except Exception as e:
        logger.error(f"员工订单管理页面加载失败: {str(e)}")
        return render(request, 'admin/staff_order_management.html', {
            'error': '加载订单管理页面失败',
            'total_orders_today': 0,
            'current_time': timezone.now(),
        })


# ==================== 统一队列数据API（核心功能） ====================

def get_unified_queue_data(request):
    """返回統一的隊列數據，格式符合前端 UnifiedDataManager 要求"""
    try:
        # 獲取香港時區與當前時間
        hk_tz = pytz.timezone('Asia/Hong_Kong')
        now = timezone.now().astimezone(hk_tz)
        
        # 使用現有的處理函數取得各類訂單數據
        waiting_orders = process_waiting_queues(now, hk_tz)
        preparing_orders = process_preparing_queues(now, hk_tz)
        ready_orders = process_ready_orders(now, hk_tz)
        completed_orders = process_completed_orders(now, hk_tz)   # ✅ 確保有處理已提取訂單
        
        # 徽章摘要
        badge_summary = {
            'waiting': len(waiting_orders),
            'preparing': len(preparing_orders),
            'ready': len(ready_orders),
            'completed': len(completed_orders),
        }
        
        # ✅ 關鍵：將所有數據包裝在 data 欄位中
        response_data = {
            'success': True,
            'data': {
                'waiting_orders': waiting_orders,
                'preparing_orders': preparing_orders,
                'ready_orders': ready_orders,
                'completed_orders': completed_orders,
                'badge_summary': badge_summary,
            },
            'timestamp': timezone.now().isoformat(),
            'message': '隊列數據加載成功'
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        logger.error(f"獲取統一隊列數據失敗: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': str(e),
            'data': {   # ✅ 錯誤時也返回一致的 data 結構
                'waiting_orders': [],
                'preparing_orders': [],
                'ready_orders': [],
                'completed_orders': [],
                'badge_summary': {'waiting': 0, 'preparing': 0, 'ready': 0, 'completed': 0}
            }
        }, status=500)
    

# ==================== 核心处理函数 ====================

def process_waiting_queues(now, hk_tz):
    """處理等待隊列數據 - 修正商品項目顯示，使用統一時間格式化"""
    waiting_queues = CoffeeQueue.objects.filter(status='waiting').order_by('position')
    waiting_data = []
    
    for queue_item in waiting_queues:
        try:
            order = queue_item.order
            
            if order.status == 'ready':
                logger.warning(f"訂單 {order.id} 狀態為 ready，更新隊列狀態")
                queue_item.status = 'ready'
                queue_item.actual_completion_time = timezone.now()
                queue_item.save()
                continue
            
            items = order.get_items_with_chinese_options()
            
            coffee_items = []
            bean_items = []
            all_items = []
            coffee_count = 0
            bean_count = 0
            
            for item in items:
                item_type = item.get('type', 'unknown')
                item_copy = item.copy()
                
                if not item_copy.get('image'):
                    if item_type == 'coffee':
                        item_copy['image'] = '/static/images/default-coffee.png'
                    elif item_type == 'bean':
                        item_copy['image'] = '/static/images/default-beans.png'
                    else:
                        item_copy['image'] = '/static/images/default-product.png'
                
                if item_type == 'coffee':
                    coffee_items.append(item_copy)
                    coffee_count += item_copy.get('quantity', 1)
                elif item_type == 'bean':
                    bean_items.append(item_copy)
                    bean_count += item_copy.get('quantity', 1)
                
                all_items.append(item_copy)
            
            has_coffee = len(coffee_items) > 0
            has_beans = len(bean_items) > 0
            is_mixed_order = has_coffee and has_beans
            is_beans_only = has_beans and not has_coffee
            
            items_count = 0
            if has_coffee:
                items_count += 1
            if has_beans:
                items_count += 1
            
            items_detail = []
            if coffee_count > 0:
                items_detail.append(f"咖啡{coffee_count}杯")
            if bean_count > 0:
                items_detail.append(f"咖啡豆{bean_count}包")
            
            items_display = f"{items_count}項商品"
            if items_detail:
                items_display += f" - {', '.join(items_detail)}"
            
            # ✅ 統一使用 time_service 取得取貨時間資訊
            pickup_time_info = time_service.format_pickup_time_for_order(order)
            
            quick_order_time_info = None
            if order.is_quick_order:
                quick_order_time_info = time_service.calculate_quick_order_pickup_time(order)
            
            wait_seconds = 0
            wait_display = '--'
            
            if queue_item.estimated_start_time:
                est_start = queue_item.estimated_start_time
                if est_start.tzinfo is None:
                    est_start = timezone.make_aware(est_start)
                est_start_hk = est_start.astimezone(hk_tz)
                wait_seconds = max(0, int((est_start_hk - now).total_seconds()))
                wait_minutes = max(0, int(wait_seconds / 60))
                wait_display = f"{wait_minutes}分鐘"
            elif order.is_quick_order and order.pickup_time_choice:
                minutes_to_add = time_service.get_minutes_from_pickup_choice(order.pickup_time_choice)
                wait_display = f"{minutes_to_add}分鐘後"
            
            total_price = order.total_price
            if not total_price or total_price == '0.00':
                total_price = sum(float(item.get('total_price', 0) or 0) for item in all_items)
            
            created_at_hk = order.created_at.astimezone(hk_tz) if order.created_at.tzinfo else timezone.make_aware(order.created_at, hk_tz)
            
            estimated_completion_time = None
            estimated_completion_display = '--:--'
            if queue_item.estimated_completion_time:
                est_complete = queue_item.estimated_completion_time
                if est_complete.tzinfo is None:
                    est_complete = timezone.make_aware(est_complete)
                estimated_completion_time = est_complete.astimezone(hk_tz)
                estimated_completion_display = estimated_completion_time.strftime('%H:%M')
            
            estimated_start_display = '--:--'
            if queue_item.estimated_start_time:
                est_start = queue_item.estimated_start_time
                if est_start.tzinfo is None:
                    est_start = timezone.make_aware(est_start)
                estimated_start_hk = est_start.astimezone(hk_tz)
                estimated_start_display = estimated_start_hk.strftime('%H:%M')
            
            waiting_data.append({
                'id': order.id,
                'order_id': order.id,
                'position': queue_item.position,
                'name': order.name or '顾客',
                'phone': order.phone or '',
                'total_price': str(total_price),
                'items': all_items,
                'coffee_items': coffee_items,
                'bean_items': bean_items,
                'coffee_count': coffee_count,
                'bean_count': bean_count,
                'items_count': items_count,
                'items_detail': items_detail,
                'items_display': items_display,
                'has_coffee': has_coffee,
                'has_beans': has_beans,
                'is_mixed_order': is_mixed_order,
                'is_beans_only': is_beans_only,
                'preparation_time_minutes': queue_item.preparation_time_minutes,
                'wait_seconds': wait_seconds,
                'wait_display': wait_display,
                'pickup_time_info': pickup_time_info,
                'quick_order_time_info': quick_order_time_info,
                'pickup_time_display': pickup_time_info['text'] if pickup_time_info else '--',
                'is_quick_order': order.is_quick_order,
                'estimated_start_time': queue_item.estimated_start_time.isoformat() if queue_item.estimated_start_time else None,
                'estimated_start_display': estimated_start_display,
                'estimated_completion_time': estimated_completion_time.isoformat() if estimated_completion_time else None,
                'estimated_completion_display': estimated_completion_display,
                'pickup_code': order.pickup_code or '',
                'payment_method': order.payment_method or '',
                'payment_method_display': order.get_payment_method_display() if hasattr(order, 'get_payment_method_display') else order.payment_method,
                'created_at': created_at_hk.isoformat(),
                'created_at_display': created_at_hk.strftime('%H:%M'),
                'created_at_full': created_at_hk.strftime('%Y-%m-%d %H:%M'),
                'pickup_time_choice': order.pickup_time_choice if hasattr(order, 'pickup_time_choice') else None,
                'pickup_time_choice_display': pickup_time_info['text'] if pickup_time_info and order.is_quick_order else None,
            })
            
        except Exception as e:
            logger.error(f"處理等待隊列項 {queue_item.id} 失敗: {str(e)}")
            continue
    
    return waiting_data


def process_preparing_queues(now, hk_tz):
    """處理製作中隊列數據 - 使用 OrderStatusManager，添加統一時間格式化"""
    preparing_queues = CoffeeQueue.objects.filter(status='preparing')
    preparing_data = []
    
    for queue_item in preparing_queues:
        try:
            order = queue_item.order
            
            pickup_time_info = time_service.format_pickup_time_for_order(order)
            
            if order.status != 'preparing':
                result = OrderStatusManager.mark_as_preparing_manually(
                    order_id=order.id,
                    barista_name='system',
                    preparation_minutes=queue_item.preparation_time_minutes
                )
                
                if not result['success']:
                    logger.error(f"同步訂單 {order.id} 狀態為製作中失敗: {result['message']}")
                else:
                    order = result['order']
            
            items = order.get_items_with_chinese_options()
            
            coffee_items = []
            bean_items = []
            all_items = []
            coffee_count = 0
            bean_count = 0
            
            for item in items:
                item_type = item.get('type', 'unknown')
                item_copy = item.copy()
                
                if not item_copy.get('image'):
                    if item_type == 'coffee':
                        item_copy['image'] = '/static/images/default-coffee.png'
                    elif item_type == 'bean':
                        item_copy['image'] = '/static/images/default-beans.png'
                    else:
                        item_copy['image'] = '/static/images/default-product.png'
                
                if item_type == 'coffee':
                    coffee_items.append(item_copy)
                    coffee_count += item_copy.get('quantity', 1)
                elif item_type == 'bean':
                    bean_items.append(item_copy)
                    bean_count += item_copy.get('quantity', 1)
                
                all_items.append(item_copy)
            
            has_coffee = len(coffee_items) > 0
            has_beans = len(bean_items) > 0
            items_count = 0
            if has_coffee:
                items_count += 1
            if has_beans:
                items_count += 1
            
            items_detail = []
            if coffee_count > 0:
                items_detail.append(f"咖啡{coffee_count}杯")
            if bean_count > 0:
                items_detail.append(f"咖啡豆{bean_count}包")
            
            items_display = f"{items_count}項商品"
            if items_detail:
                items_display += f" - {', '.join(items_detail)}"
            
            remaining_seconds = 0
            if queue_item.estimated_completion_time:
                est_completion = queue_item.estimated_completion_time
                if est_completion.tzinfo is None:
                    est_completion = timezone.make_aware(est_completion)
                est_completion_hk = est_completion.astimezone(hk_tz)
                remaining_seconds = max(0, int((est_completion_hk - now).total_seconds()))
            
            total_price = order.total_price
            if not total_price or total_price == '0.00':
                total_price = sum(float(item.get('total_price', 0) or 0) for item in all_items)
            
            created_at_hk = order.created_at.astimezone(hk_tz) if order.created_at.tzinfo else timezone.make_aware(order.created_at, hk_tz)
            
            preparation_started_at_hk = None
            if order.preparation_started_at:
                prep_start = order.preparation_started_at
                if prep_start.tzinfo is None:
                    prep_start = timezone.make_aware(prep_start)
                preparation_started_at_hk = prep_start.astimezone(hk_tz)
            
            estimated_completion_time_hk = None
            if queue_item.estimated_completion_time:
                est_comp = queue_item.estimated_completion_time
                if est_comp.tzinfo is None:
                    est_comp = timezone.make_aware(est_comp)
                estimated_completion_time_hk = est_comp.astimezone(hk_tz)
            
            preparing_data.append({
                'id': order.id,
                'order_id': order.id,
                'pickup_code': order.pickup_code or '',
                'name': order.name or '顾客',
                'phone': order.phone or '',
                'total_price': str(total_price),
                'items': all_items,
                'coffee_items': coffee_items,
                'bean_items': bean_items,
                'coffee_count': coffee_count,
                'bean_count': bean_count,
                'items_count': items_count,
                'items_detail': items_detail,
                'items_display': items_display,
                'has_coffee': has_coffee,
                'has_beans': has_beans,
                'is_mixed_order': has_coffee and has_beans,
                'is_beans_only': has_beans and not has_coffee,
                'remaining_seconds': remaining_seconds,
                'estimated_completion_time': estimated_completion_time_hk.strftime('%H:%M') if estimated_completion_time_hk else '--:--',
                'estimated_completion_time_iso': estimated_completion_time_hk.isoformat() if estimated_completion_time_hk else None,
                'payment_method': order.payment_method or '',
                'is_quick_order': order.is_quick_order,
                'preparation_started_at': preparation_started_at_hk.isoformat() if preparation_started_at_hk else None,
                'created_at': created_at_hk.isoformat(),
                'created_at_iso': created_at_hk.isoformat(),
                'queue_item_id': queue_item.id,
                'pickup_time_info': pickup_time_info,
                'pickup_time_display': pickup_time_info['text'] if pickup_time_info else '--',
                'pickup_time_choice': order.pickup_time_choice if hasattr(order, 'pickup_time_choice') else None,
            })
            
        except Exception as e:
            logger.error(f"處理製作中隊列項 {queue_item.id} 失敗: {str(e)}")
            continue
    
    return preparing_data


def process_ready_orders(now, hk_tz):
    """處理已就緒訂單數據 - 添加統一時間格式化"""
    ready_orders = OrderModel.objects.filter(
        status='ready',
        payment_status="paid",
        picked_up_at__isnull=True
    ).order_by('-ready_at')[:20]
    
    ready_data = []
    for order in ready_orders:
        try:
            pickup_time_info = time_service.format_pickup_time_for_order(order)
            
            items = order.get_items_with_chinese_options()
            
            coffee_items = []
            bean_items = []
            all_items = []
            coffee_count = 0
            bean_count = 0
            
            for item in items:
                item_type = item.get('type', 'unknown')
                item_copy = item.copy()
                
                if not item_copy.get('image'):
                    if item_type == 'coffee':
                        item_copy['image'] = '/static/images/default-coffee.png'
                    elif item_type == 'bean':
                        item_copy['image'] = '/static/images/default-beans.png'
                    else:
                        item_copy['image'] = '/static/images/default-product.png'
                
                if item_type == 'coffee':
                    coffee_items.append(item_copy)
                    coffee_count += item_copy.get('quantity', 1)
                elif item_type == 'bean':
                    bean_items.append(item_copy)
                    bean_count += item_copy.get('quantity', 1)
                
                all_items.append(item_copy)
            
            has_coffee = len(coffee_items) > 0
            has_beans = len(bean_items) > 0
            items_count = 0
            if has_coffee:
                items_count += 1
            if has_beans:
                items_count += 1
            
            items_detail = []
            if coffee_count > 0:
                items_detail.append(f"咖啡{coffee_count}杯")
            if bean_count > 0:
                items_detail.append(f"咖啡豆{bean_count}包")
            
            items_display = f"{items_count}項商品"
            if items_detail:
                items_display += f" - {', '.join(items_detail)}"
            
            total_price = order.total_price
            if not total_price or total_price == '0.00':
                total_price = sum(float(item.get('total_price', 0) or 0) for item in all_items)
            
            created_at_hk = order.created_at.astimezone(hk_tz) if order.created_at.tzinfo else timezone.make_aware(order.created_at, hk_tz)
            
            ready_at_hk = None
            if order.ready_at:
                ready_time = order.ready_at
                if ready_time.tzinfo is None:
                    ready_time = timezone.make_aware(ready_time)
                ready_at_hk = ready_time.astimezone(hk_tz)
            
            wait_minutes = 0
            is_beans_only = has_beans and not has_coffee
            if ready_at_hk and not is_beans_only:
                wait_seconds = (now - ready_at_hk).total_seconds()
                wait_minutes = int(wait_seconds / 60)
            
            ready_data.append({
                'id': order.id,
                'order_id': order.id,
                'pickup_code': order.pickup_code or '',
                'name': order.name or '顾客',
                'phone': order.phone or '',
                'total_price': str(total_price),
                'items': all_items,
                'coffee_items': coffee_items,
                'bean_items': bean_items,
                'coffee_count': coffee_count,
                'bean_count': bean_count,
                'items_count': items_count,
                'items_detail': items_detail,
                'items_display': items_display,
                'has_coffee': has_coffee,
                'has_beans': has_beans,
                'is_mixed_order': has_coffee and has_beans,
                'is_beans_only': is_beans_only,
                'completed_time': ready_at_hk.strftime('%H:%M') if ready_at_hk else '--:--',
                'ready_at': ready_at_hk.isoformat() if ready_at_hk else None,
                'wait_minutes': wait_minutes,
                'wait_display': f"{wait_minutes}分鐘前" if wait_minutes > 0 else "刚刚",
                'payment_method': order.payment_method or '',
                'is_quick_order': order.is_quick_order,
                'created_at': created_at_hk.isoformat(),
                'pickup_time_info': pickup_time_info,
                'pickup_time_display': pickup_time_info['text'] if pickup_time_info else '--',
                'pickup_time_choice': order.pickup_time_choice if hasattr(order, 'pickup_time_choice') else None,
            })
            
        except Exception as e:
            logger.error(f"處理就緒訂單 {order.id} 失敗: {str(e)}")
            continue
    
    ready_data.sort(key=lambda x: x.get('ready_at') or '', reverse=True)
    return ready_data


def process_completed_orders(now, hk_tz):
    """處理已提取訂單數據（最近4小時） - 添加統一時間格式化"""
    try:
        time_threshold = now - timedelta(hours=4)
        completed_orders = OrderModel.objects.filter(
            status='completed',
            picked_up_at__isnull=False,
            picked_up_at__gte=time_threshold
        ).order_by('-picked_up_at')[:50]
        
        completed_data = []
        for order in completed_orders:
            try:
                pickup_time_info = time_service.format_pickup_time_for_order(order)
                
                items = order.get_items_with_chinese_options()
                
                coffee_items = []
                bean_items = []
                all_items = []
                coffee_count = 0
                bean_count = 0
                
                for item in items:
                    item_type = item.get('type', 'unknown')
                    item_copy = item.copy()
                    
                    if not item_copy.get('image'):
                        if item_type == 'coffee':
                            item_copy['image'] = '/static/images/default-coffee.png'
                        elif item_type == 'bean':
                            item_copy['image'] = '/static/images/default-beans.png'
                        else:
                            item_copy['image'] = '/static/images/default-product.png'
                    
                    if item_type == 'coffee':
                        coffee_items.append(item_copy)
                        coffee_count += item_copy.get('quantity', 1)
                    elif item_type == 'bean':
                        bean_items.append(item_copy)
                        bean_count += item_copy.get('quantity', 1)
                    
                    all_items.append(item_copy)
                
                has_coffee = len(coffee_items) > 0
                has_beans = len(bean_items) > 0
                items_count = 0
                if has_coffee:
                    items_count += 1
                if has_beans:
                    items_count += 1
                
                items_detail = []
                if coffee_count > 0:
                    items_detail.append(f"咖啡{coffee_count}杯")
                if bean_count > 0:
                    items_detail.append(f"咖啡豆{bean_count}包")
                
                items_display = f"{items_count}項商品"
                if items_detail:
                    items_display += f" - {', '.join(items_detail)}"
                
                total_price = order.total_price
                if not total_price or total_price == '0.00':
                    total_price = sum(float(item.get('total_price', 0) or 0) for item in all_items)
                
                created_at_hk = order.created_at.astimezone(hk_tz) if order.created_at.tzinfo else timezone.make_aware(order.created_at, hk_tz)
                
                picked_up_at_hk = None
                if order.picked_up_at:
                    pickup_time = order.picked_up_at
                    if pickup_time.tzinfo is None:
                        pickup_time = timezone.make_aware(pickup_time)
                    picked_up_at_hk = pickup_time.astimezone(hk_tz)
                
                completed_data.append({
                    'id': order.id,
                    'order_id': order.id,
                    'pickup_code': order.pickup_code or '',
                    'name': order.name or '顾客',
                    'phone': order.phone or '',
                    'total_price': str(total_price),
                    'items': all_items,
                    'coffee_items': coffee_items,
                    'bean_items': bean_items,
                    'coffee_count': coffee_count,
                    'bean_count': bean_count,
                    'items_count': items_count,
                    'items_detail': items_detail,
                    'items_display': items_display,
                    'has_coffee': has_coffee,
                    'has_beans': has_beans,
                    'is_mixed_order': has_coffee and has_beans,
                    'is_beans_only': has_beans and not has_coffee,
                    'completed_time': picked_up_at_hk.strftime('%H:%M') if picked_up_at_hk else '--:--',
                    'picked_up_at': picked_up_at_hk.isoformat() if picked_up_at_hk else None,
                    'payment_method': order.payment_method or '',
                    'is_quick_order': order.is_quick_order,
                    'created_at': created_at_hk.isoformat(),
                    'pickup_time_info': pickup_time_info,
                    'pickup_time_display': pickup_time_info['text'] if pickup_time_info else '--',
                    'pickup_time_choice': order.pickup_time_choice if hasattr(order, 'pickup_time_choice') else None,
                })
                
            except Exception as e:
                logger.error(f"處理已提取訂單 {order.id} 失敗: {str(e)}")
                continue
        
        completed_data.sort(key=lambda x: x.get('picked_up_at') or '', reverse=True)
        return completed_data
        
    except Exception as e:
        logger.error(f"處理已提取訂單數據失敗: {str(e)}")
        return []


# ==================== 队列操作API ====================

@require_POST
@login_required
@staff_member_required
def start_preparation_api(request, order_id):
    """API：開始制作訂單（統一使用 OrderStatusManager）"""
    try:
        barista_name = request.user.get_full_name() or request.user.username
        
        result = OrderStatusManager.mark_as_preparing_manually(
            order_id=order_id,
            barista_name=barista_name
        )
        
        if not result['success']:
            return JsonResponse({
                'success': False,
                'message': result['message']
            }, status=400)
        
        order = result['order']
        items = order.get_items()
        coffee_count = sum(item.get('quantity', 1) for item in items if item.get('type') == 'coffee')
        
        logger.info(f"訂單 {order_id} 已開始制作，操作員: {barista_name}")
        
        return JsonResponse({
            'success': True,
            'message': f'已開始制作訂單 #{order_id}',
            'order_id': order_id,
            'status': order.status,
            'preparation_minutes': result['preparation_minutes'],
            'coffee_count': coffee_count,
        })
        
    except Exception as e:
        logger.error(f"開始制作訂單 {order_id} 失敗: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'系統錯誤: {str(e)}'
        }, status=500)


@require_POST
@login_required
@staff_member_required
def recalculate_all_times_api(request):
    """API：手動觸發統一時間計算"""
    try:
        queue_manager = CoffeeQueueManager()
        logger.info("🔄 API: 手動觸發統一時間計算")
        
        result = queue_manager.recalculate_all_order_times()
        
        if result.get('success'):
            try:
                from eshop.websocket_utils import send_queue_time_update
                send_queue_time_update()
            except Exception as ws_error:
                logger.error(f"發送WebSocket通知失敗: {str(ws_error)}")
            
            return JsonResponse({
                'success': True,
                'message': '統一時間計算完成',
                'details': result.get('details', {}),
                'timestamp': timezone.now().isoformat()
            })
        else:
            return JsonResponse({
                'success': False,
                'error': result.get('error', '未知錯誤'),
                'message': '時間計算失敗'
            }, status=500)
        
    except Exception as e:
        logger.error(f"手動觸發統一時間計算失敗: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': str(e),
            'message': '系統錯誤'
        }, status=500)


@require_POST
@login_required
@staff_member_required
def mark_as_ready_api(request, order_id):
    """標記訂單為就緒（兼容舊前端，但改用OrderStatusManager）"""
    try:
        staff_name = request.user.username
        logger.info(f"👨‍🍳 員工 {staff_name} 通過舊API標記訂單 #{order_id} 為就緒")
        
        result = OrderStatusManager.mark_as_ready_manually(order_id, staff_name)
        
        if result.get('success'):
            logger.info(f"✅ 舊API: 訂單 #{order_id} 已通過OrderStatusManager標記為就緒")
            return JsonResponse(result)
        else:
            logger.error(f"❌ 舊API: 標記訂單 #{order_id} 為就緒失敗: {result.get('error')}")
            return JsonResponse(result, status=400)
            
    except Exception as e:
        logger.error(f"❌ 舊API處理失敗: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': f'伺服器錯誤: {str(e)}'
        }, status=500)


@require_POST
@login_required
@staff_member_required
def mark_as_collected(request, order_id):
    """標記訂單為已提取（兼容舊前端，但改用OrderStatusManager）"""
    try:
        staff_name = request.user.username
        logger.info(f"👨‍🍳 員工 {staff_name} 通過舊API標記訂單 #{order_id} 為已提取")
        
        result = OrderStatusManager.mark_as_completed_manually(order_id, staff_name)
        
        if result.get('success'):
            logger.info(f"✅ 舊API: 訂單 #{order_id} 已通過OrderStatusManager標記為已提取")
            return JsonResponse(result)
        else:
            logger.error(f"❌ 舊API: 標記訂單 #{order_id} 為已提取失敗: {result.get('error')}")
            return JsonResponse(result, status=400)
            
    except Exception as e:
        logger.error(f"❌ 舊API處理失敗: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': f'伺服器錯誤: {str(e)}'
        }, status=500)


# ==================== 数据修复API ====================

@require_POST
@login_required
@staff_member_required
def repair_queue_data(request):
    """修复队列数据：重新计算所有队列时间"""
    try:
        logger.info("=== 开始修复队列数据 ===")
        queue_manager = CoffeeQueueManager()
        
        queue_manager.fix_queue_positions()
        queue_manager.update_estimated_times()
        
        logger.info("=== 队列数据修复完成 ===")
        
        return JsonResponse({
            'success': True,
            'message': '队列数据已修复',
        })
        
    except Exception as e:
        logger.error(f"修复队列数据失败: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_POST
@login_required
@staff_member_required
def force_sync_api(request):
    """强制同步API"""
    try:
        queue_manager = CoffeeQueueManager()
        
        queue_manager.fix_queue_positions()
        force_sync_queue_and_orders()
        queue_manager.update_estimated_times()
        
        return JsonResponse({
            'success': True,
            'message': '强制同步完成'
        })
        
    except Exception as e:
        logger.error(f"强制同步失败: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


# ==================== 订单详细信息API ====================

@require_GET
@login_required
@staff_member_required
def order_details_for_waiting_api(request, order_id):
    """API：获取等待订单详细信息"""
    try:
        order = get_object_or_404(OrderModel, id=order_id)
        
        if not request.user.is_staff:
            return JsonResponse({
                'success': False,
                'error': '无权访问此订单详细信息'
            }, status=403)
        
        items = order.get_items_with_chinese_options()
        
        coffee_count = sum(
            item.get('quantity', 1) 
            for item in order.get_items() 
            if item.get('type') == 'coffee'
        )
        
        order_data = {
            'id': order.id,
            'pickup_code': order.pickup_code,
            'total_price': str(order.total_price),
            'name': order.name,
            'phone': order.phone,
            'is_quick_order': order.is_quick_order,
            'payment_method': order.payment_method,
            'status': order.status,
            'created_at': order.created_at.isoformat(),
            'coffee_count': coffee_count,
            'items_count': len(items),
            'items': items,
            'has_coffee': coffee_count > 0,
        }
        
        return JsonResponse({
            'success': True,
            'order': order_data,
            'timestamp': timezone.now().isoformat()
        })
        
    except OrderModel.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': '订单不存在'
        }, status=404)
    except Exception as e:
        logger.error(f"获取等待订单详情失败: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


# ==================== 清理函数 ====================

@require_POST
@login_required
@staff_member_required
def cleanup_queue_data(request):
    """安全清理：只删除队列项，不删除订单 - 使用 OrderStatusManager"""
    try:
        deleted_count = CoffeeQueue.objects.all().count()
        CoffeeQueue.objects.all().delete()
        
        orders = OrderModel.objects.filter(status__in=['preparing', 'ready'])
        reset_count = 0
        error_count = 0
        
        for order in orders:
            result = OrderStatusManager.mark_as_waiting_manually(
                order_id=order.id,
                staff_name=request.user.username if request.user else 'system'
            )
            
            if result['success']:
                reset_count += 1
            else:
                error_count += 1
                logger.error(f"重置訂單 {order.id} 狀態為等待中失敗: {result['message']}")
        
        return JsonResponse({
            'success': True,
            'message': f'清理完成！刪除了 {deleted_count} 個隊列項，並重置了 {reset_count} 個訂單狀態為等待中。',
            'queue_items_deleted': deleted_count,
            'orders_reset': reset_count,
            'errors': error_count
        })
        
    except Exception as e:
        logger.error(f"清理隊列數據失敗: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)