# eshop/view_utils.py
"""
视图工具函数 - 从views.py中提取的通用函数
已移除重复的时间计算函数与WebSocket包装函数，统一使用专用模块
"""

import json
import traceback
import logging
import phonenumbers

from django.shortcuts import redirect
from django.contrib import messages
from django.utils import timezone
from django.urls import reverse
from django.http import JsonResponse
from decimal import Decimal
from datetime import timedelta

from eshop.order_status_manager import OrderStatusManager
from .models import CoffeeItem, BeanItem, OrderModel, CoffeeQueue
from .time_service import time_service  # 统一时间服务

logger = logging.getLogger(__name__)

# ==================== 通用工具函数 ====================

def validate_and_format_phone(phone):
    """验证并格式化电话号码为E.164格式"""
    try:
        if not phone:
            return None
        if not phone.startswith('+'):
            phone = f"+852{phone}"
        parsed_phone = phonenumbers.parse(phone, "HK")
        if phonenumbers.is_valid_number(parsed_phone):
            return phonenumbers.format_number(
                parsed_phone,
                phonenumbers.PhoneNumberFormat.E164
            )
        return None
    except Exception as e:
        logger.error(f"电话号码验证异常: {str(e)}")
        return None


def prepare_order_confirm_context(request, order=None, items=None, total_price=None):
    """准备订单确认页面的上下文"""
    context = {}
    if order:
        context = {
            'order': order,
            'items': order.get_items_with_chinese_options(),
            'total_price': order.total_price,
            'user': request.user,
            'initial_data': {
                'name': order.name,
                'phone': order.phone,
                'email': order.email,
                'pickup_time': order.pickup_time,
            },
            'is_quick_order': order.is_quick_order
        }
    elif items is not None and total_price is not None:
        context = {
            'items': items,
            'total_price': total_price,
            'user': request.user,
            'initial_data': {},
            'is_quick_order': False
        }
    return context


def prepare_payment_error_context(order, error=None):
    """准备支付错误页面的上下文"""
    items = []
    for item in order.get_items():
        try:
            items.append({
                'name': item['name'],
                'price': float(item['price']),
                'quantity': item['quantity'],
                'total_price': float(item['price']) * item['quantity'],
                'type': item['type'],
                'image': item.get('image', '/static/images/default-product.png'),
                'cup_level': item.get('cup_level'),
                'milk_level': item.get('milk_level'),
                'grinding_level': item.get('grinding_level'),
            })
        except (KeyError, ValueError):
            continue
    return {
        'order': order,
        'items': items,
        'total_price': order.total_price,
        'show_alipay_option': True,
        'alipay_error': str(error) if error else "未知错误"
    }


def redirect_to_confirmation(order_id):
    """重定向到支付确认页面"""
    return redirect(reverse('eshop:order_payment_confirmation') + f'?order_id={order_id}')


def redirect_to_payment_failed(error_message, order_id=None):
    """重定向到支付失败页面"""
    from urllib.parse import quote
    url = reverse('eshop:payment_failed')
    params = f"?error={quote(error_message)}"
    if order_id:
        params += f"&order_id={order_id}"
    return redirect(url + params)


def handle_payment_by_order_id(request, order_id):
    """根據訂單ID處理支付 - 使用 OrderStatusManager"""
    try:
        if not order_id:
            return redirect(reverse('eshop:order_payment_confirmation') + '?payment_status=error')
        order = OrderModel.objects.get(id=order_id)
        if order.payment_status == "paid":
            return redirect_to_confirmation(order_id)
        else:
            result = OrderStatusManager.process_payment_success(order_id, request)
            if not result['success']:
                logger.error(f"處理訂單 {order_id} 支付成功失敗: {result['message']}")
                return redirect(reverse('eshop:order_payment_confirmation') + f'?order_id={order_id}&payment_status=error')
            clear_payment_session(request, order_id)
            return redirect_to_confirmation(order_id)
    except OrderModel.DoesNotExist:
        logger.error(f"訂單不存在: {order_id}")
        return redirect(reverse('eshop:order_payment_confirmation') + '?payment_status=error')
    except Exception as e:
        logger.error(f"處理訂單 {order_id} 支付失敗: {str(e)}")
        return redirect(reverse('eshop:order_payment_confirmation') + '?payment_status=error')


def clear_payment_session(request, order_id):
    """清理支付相关的session数据"""
    try:
        if hasattr(request, 'session') and 'cart' in request.session:
            del request.session['cart']
        if hasattr(request, 'session'):
            request.session['last_order_id'] = order_id
            session_keys_to_remove = [
                'pending_paypal_order_id',
                'current_payment_order_id',
                'payment_start_time',
                'pending_fps_order_id',
                'pending_cash_order_id'
            ]
            for key in session_keys_to_remove:
                if key in request.session:
                    del request.session[key]
            request.session.modified = True
        logger.info(f"支付会话数据已清理，订单ID: {order_id}")
    except Exception as e:
        logger.error(f"清理支付会话失败: {str(e)}")


def send_payment_notifications(order):
    """发送支付成功通知"""
    try:
        if order.phone and hasattr(order, 'user') and order.user and order.user.is_authenticated:
            try:
                from .sms_utils import send_sms_notification
                send_sms_notification(order)
                logger.info(f"已发送短信通知到 {order.phone}")
            except Exception as e:
                logger.error(f"发送短信通知失败: {str(e)}")
    except Exception as e:
        logger.error(f"发送支付通知失败: {str(e)}")


def are_orders_similar(order1_items, order2_items, total_price1, total_price2, tolerance=0.01):
    """比較兩個訂單是否相似"""
    try:
        import decimal
        if total_price1 is None or total_price2 is None:
            logger.error("比較訂單失敗: 價格參數為None")
            return False
        if isinstance(total_price1, decimal.Decimal):
            total_price1 = float(total_price1)
        if isinstance(total_price2, decimal.Decimal):
            total_price2 = float(total_price2)
        if abs(total_price1 - total_price2) > tolerance:
            return False
        if len(order1_items) != len(order2_items):
            return False
        for item1, item2 in zip(order1_items, order2_items):
            if item1.get('type') != item2.get('type') or \
               item1.get('id') != item2.get('id') or \
               item1.get('quantity') != item2.get('quantity'):
                return False
        return True
    except Exception as e:
        logger.error(f"比較訂單失敗: {str(e)}")
        return False


def find_existing_pending_order(user, current_items, current_total_price):
    """查找可重用的未支付订单"""
    try:
        time_threshold = timezone.now() - timedelta(minutes=30)
        pending_orders = OrderModel.objects.filter(
            user=user,
            payment_status="pending",
            status='pending',
            created_at__gte=time_threshold
        ).order_by('-created_at')
        for order in pending_orders:
            if are_orders_similar(order, current_items, current_total_price):
                return order
        return None
    except Exception as e:
        logger.error(f"查找未支付订单失败: {str(e)}")
        return None


def calculate_dynamic_wait_time(ready_at):
    """计算动态等待时间（每秒更新）- 使用统一时间服务"""
    try:
        now = time_service.get_hong_kong_time()
        if isinstance(ready_at, str):
            from django.utils.dateparse import parse_datetime
            ready_time = parse_datetime(ready_at)
        else:
            ready_time = ready_at
        if ready_time:
            if ready_time.tzinfo is None:
                import pytz
                ready_time = pytz.UTC.localize(ready_time)
            hk_tz = pytz.timezone('Asia/Hong_Kong')
            ready_time_hk = ready_time.astimezone(hk_tz)
            time_diff = now - ready_time_hk
            total_seconds = int(time_diff.total_seconds())
            if total_seconds < 60:
                return f"{total_seconds}秒前"
            elif total_seconds < 3600:
                minutes = total_seconds // 60
                seconds = total_seconds % 60
                return f"{minutes}分{seconds}秒前"
            elif total_seconds < 86400:
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60
                return f"{hours}小时{minutes}分前"
            else:
                days = total_seconds // 86400
                return f"{days}天前"
        return "刚刚"
    except Exception as e:
        logger.error(f"计算动态等待时间失败: {str(e)}")
        return "刚刚"


# ==================== 权限检查装饰器 ====================

def staff_required(view_func):
    """员工权限装饰器"""
    from functools import wraps
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not request.user.is_staff:
            messages.error(request, "需要员工权限才能访问此页面")
            return redirect('index')
        return view_func(request, *args, **kwargs)
    return wrapper


def customer_only(view_func):
    """仅限顾客访问装饰器"""
    from functools import wraps
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if request.user.is_staff:
            messages.error(request, "员工账户无法访问顾客页面")
            return redirect('eshop:queue_dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


# ==================== 响应包装器 ====================

def json_response_success(data=None, message=None):
    """成功的JSON响应"""
    response = {'success': True}
    if data:
        response.update(data)
    if message:
        response['message'] = message
    return JsonResponse(response)


def json_response_error(message, status=400, data=None):
    """错误的JSON响应"""
    response = {'success': False, 'error': message}
    if data:
        response.update(data)
    return JsonResponse(response, status=status)


# ==================== 订单处理辅助函数 ====================

def process_cart_data(cart_data):
    """处理购物车数据"""
    items = []
    total_price = Decimal('0.00')
    if not cart_data or 'items' not in cart_data:
        return items, total_price
    for item_key, item_data in cart_data.get('items', {}).items():
        parts = item_key.split('_')
        if len(parts) < 2:
            continue
        item_type = parts[0]
        item_id = parts[1]
        try:
            if item_type == 'coffee':
                item = CoffeeItem.objects.get(id=item_id)
            elif item_type == 'bean':
                item = BeanItem.objects.get(id=item_id)
            else:
                continue
            quantity = item_data.get('quantity', 1)
            price = Decimal(str(item_data.get('price', item.price)))
            item_total = price * quantity
            items.append({
                'type': item_type,
                'id': int(item_id),
                'name': item.name,
                'price': float(price),
                'quantity': quantity,
                'total_price': float(item_total),
                'cup_level': item_data.get('cup_level'),
                'milk_level': item_data.get('milk_level'),
                'grinding_level': item_data.get('grinding_level'),
                'weight': item_data.get('weight'),
                'image': item.image.url if item.image else '/static/images/default-product.png',
            })
            total_price += item_total
        except (CoffeeItem.DoesNotExist, BeanItem.DoesNotExist, ValueError):
            continue
    return items, total_price


def process_quick_order_data(quick_order_data):
    """处理快速订单数据"""
    if not quick_order_data:
        return [], Decimal('0.00')
    items = quick_order_data.get('items', [])
    total_price = Decimal(str(quick_order_data.get('total_price', '0.00')))
    for item in items:
        if item.get('type') == 'coffee' and item.get('id'):
            try:
                coffee_item = CoffeeItem.objects.get(id=item['id'])
                item['image'] = coffee_item.image.url if coffee_item.image else '/static/images/default-coffee.png'
            except CoffeeItem.DoesNotExist:
                item['image'] = '/static/images/default-coffee.png'
    return items, total_price




# ==================== 权限验证 ====================

def verify_order_permission(request, order, allow_staff=True):
    """验证订单访问权限"""
    if not request.user.is_authenticated:
        return False, "需要登录"
    if allow_staff and request.user.is_staff:
        return True, None
    if order.user == request.user:
        return True, None
    return False, "无权查看此订单"


# ==================== 日志记录辅助函数 ====================

def log_order_event(order_id, event_type, message, user=None, extra_data=None):
    """记录订单事件日志"""
    log_message = f"订单 #{order_id}: {message}"
    if user:
        log_message = f"用户 {user.username} - {log_message}"
    if extra_data:
        log_message = f"{log_message} | 数据: {extra_data}"
    if event_type in ['error', 'failed', 'timeout']:
        logger.error(log_message)
    elif event_type in ['warning', 'retry']:
        logger.warning(log_message)
    elif event_type in ['success', 'paid', 'completed']:
        logger.info(log_message)
    else:
        logger.debug(log_message)


def log_payment_attempt(order_id, payment_method, status, details=None):
    """记录支付尝试"""
    message = f"支付尝试 - 方式: {payment_method}, 状态: {status}"
    if details:
        message = f"{message}, 详情: {details}"
    log_order_event(order_id, 'payment', message, extra_data={'payment_method': payment_method, 'status': status})


# ==================== 订单处理函数 ====================

def calculate_order_total(order_data):
    """计算订单总金额"""
    try:
        total = 0
        if isinstance(order_data, str):
            try:
                order_data = json.loads(order_data)
            except json.JSONDecodeError:
                logger.error(f"无法解析JSON字符串: {order_data}")
                return 0
        if isinstance(order_data, dict):
            if 'total_price' in order_data:
                try:
                    return float(order_data['total_price'])
                except (ValueError, TypeError):
                    pass
            if 'items' in order_data:
                items = order_data['items']
                if isinstance(items, dict):
                    for item_key, item_data in items.items():
                        try:
                            if isinstance(item_data, dict):
                                quantity = item_data.get('quantity', 1)
                                price = float(item_data.get('price', 0))
                                total += price * quantity
                        except (ValueError, KeyError, TypeError):
                            continue
                elif isinstance(items, list):
                    for item in items:
                        try:
                            if isinstance(item, dict):
                                quantity = item.get('quantity', 1)
                                price = float(item.get('price', 0))
                                total += price * quantity
                        except (ValueError, KeyError, TypeError):
                            continue
        elif isinstance(order_data, list):
            for item in order_data:
                try:
                    if isinstance(item, dict):
                        quantity = item.get('quantity', 1)
                        price = float(item.get('price', 0))
                        total += price * quantity
                except (ValueError, KeyError, TypeError):
                    continue
        logger.info(f"计算订单总金额: {total}")
        return total
    except Exception as e:
        logger.error(f"计算订单总金额失败: {str(e)}", exc_info=True)
        return 0


def create_order_items(order, items_data):
    """创建订单项"""
    try:
        from ..models import OrderItem, Product
        created_items = []
        for item_data in items_data:
            product_id = item_data.get('product_id')
            quantity = item_data.get('quantity', 1)
            unit_price = item_data.get('unit_price')
            notes = item_data.get('notes', '')
            try:
                product = Product.objects.get(id=product_id)
                if unit_price is None:
                    unit_price = product.price
                order_item = OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=quantity,
                    unit_price=Decimal(str(unit_price)),
                    notes=notes
                )
                created_items.append(order_item)
                if hasattr(product, 'stock_quantity') and product.stock_quantity is not None:
                    product.stock_quantity = max(0, product.stock_quantity - quantity)
                    product.save()
            except Product.DoesNotExist:
                logger.error(f"产品不存在，ID: {product_id}")
                continue
        return created_items
    except Exception as e:
        logger.error(f"创建订单项失败: {str(e)}")
        raise


def validate_order_data(order_data):
    """验证订单数据有效性"""
    try:
        if not isinstance(order_data, dict):
            return False
        items = order_data.get('items', [])
        if not items or len(items) == 0:
            return False
        for item in items:
            if 'product_id' not in item:
                return False
            quantity = item.get('quantity', 1)
            if not isinstance(quantity, (int, float)) or quantity <= 0:
                return False
            if item.get('unit_price', 0) < 0:
                return False
        if 'total_amount' in order_data:
            try:
                if Decimal(str(order_data['total_amount'])) < 0:
                    return False
            except:
                return False
        pickup_time = order_data.get('pickup_time')
        if pickup_time:
            try:
                from datetime import datetime
                datetime.strptime(pickup_time, '%H:%M')
            except:
                try:
                    from django.utils.dateparse import parse_datetime
                    if not parse_datetime(pickup_time):
                        return False
                except:
                    return False
        return True
    except Exception as e:
        logger.error(f"验证订单数据失败: {str(e)}")
        return False


def validate_payment_data(payment_data):
    """验证支付数据有效性"""
    try:
        if not isinstance(payment_data, dict):
            return False
        required_fields = ['order_id', 'amount', 'payment_method']
        for field in required_fields:
            if field not in payment_data:
                return False
        try:
            amount = Decimal(str(payment_data['amount']))
            if amount <= 0:
                return False
        except:
            return False
        valid_methods = ['alipay', 'wechat', 'fps', 'cash', 'paypal']
        if payment_data['payment_method'] not in valid_methods:
            return False
        return True
    except Exception as e:
        logger.error(f"验证支付数据失败: {str(e)}")
        return False


def format_queue_data(queue_items, include_times=True):
    """格式化队列数据用于显示"""
    try:
        formatted_data = []
        for item in queue_items:
            queue_info = {
                'order_id': item.order.id,
                'order_number': getattr(item.order, 'order_number', f'#{item.order.id}'),
                'position': item.position,
                'status': item.status,
                'status_display': item.get_status_display(),
                'coffee_count': getattr(item, 'coffee_count', 0),
                'preparation_time_minutes': getattr(item, 'preparation_time_minutes', 0),
                'estimated_wait_time': getattr(item, 'estimated_wait_time', ''),
                'customer_name': getattr(item.order.customer, 'name', '顾客'),
                'items_summary': get_order_items_summary(item.order)
            }
            if include_times:
                queue_info.update({
                    'added_to_queue': item.added_to_queue.isoformat() if item.added_to_queue else None,
                    'started_at': item.started_at.isoformat() if item.started_at else None,
                    'ready_time': item.ready_time.isoformat() if item.ready_time else None,
                    'estimated_prepare_time': item.estimated_prepare_time.isoformat() if item.estimated_prepare_time else None,
                })
            formatted_data.append(queue_info)
        return formatted_data
    except Exception as e:
        logger.error(f"格式化队列数据失败: {str(e)}")
        return []


def get_order_items_summary(order):
    """获取订单项目摘要"""
    try:
        items = order.orderitem_set.all()[:3]
        summary = []
        for item in items:
            product_name = getattr(item.product, 'name', '产品')
            summary.append(f"{product_name} x{item.quantity}")
        if order.orderitem_set.count() > 3:
            summary.append(f"...等{order.orderitem_set.count()}项")
        return "，".join(summary)
    except:
        return ""


def get_queue_statistics():
    """获取队列统计信息"""
    try:
        from ..models import CoffeeQueue, Order
        now = timezone.now()
        stats = {
            'waiting': CoffeeQueue.objects.filter(status='waiting').count(),
            'preparing': CoffeeQueue.objects.filter(status='preparing').count(),
            'ready': CoffeeQueue.objects.filter(status='ready').count(),
            'completed': CoffeeQueue.objects.filter(status='completed').count(),
        }
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_stats = {
            'total_orders': Order.objects.filter(created_at__gte=today_start).count(),
            'completed_orders': Order.objects.filter(
                created_at__gte=today_start,
                status__in=['completed', 'collected']
            ).count(),
            'pending_orders': Order.objects.filter(
                created_at__gte=today_start,
                status='pending'
            ).count(),
            'preparing_orders': Order.objects.filter(
                created_at__gte=today_start,
                status='preparing'
            ).count(),
        }
        completed_queues = CoffeeQueue.objects.filter(
            status='completed',
            ready_time__isnull=False,
            started_at__isnull=False
        ).order_by('-ready_time')[:10]
        avg_preparation_time = 0
        if completed_queues:
            total_seconds = 0
            for queue in completed_queues:
                if queue.ready_time and queue.started_at:
                    total_seconds += (queue.ready_time - queue.started_at).total_seconds()
            avg_preparation_time = total_seconds / len(completed_queues)
        return {
            'queue_stats': stats,
            'today_stats': today_stats,
            'avg_preparation_minutes': round(avg_preparation_time / 60, 1) if avg_preparation_time else 0,
            'total_active': stats['waiting'] + stats['preparing'] + stats['ready'],
            'last_updated': now.isoformat(),
        }
    except Exception as e:
        logger.error(f"获取队列统计失败: {str(e)}")
        return {
            'queue_stats': {'waiting': 0, 'preparing': 0, 'ready': 0, 'completed': 0},
            'today_stats': {'total_orders': 0, 'completed_orders': 0, 'pending_orders': 0, 'preparing_orders': 0},
            'avg_preparation_minutes': 0,
            'total_active': 0,
            'last_updated': timezone.now().isoformat(),
        }


def prepare_order_context(request, order_id=None):
    """准备订单上下文数据"""
    from ..models import Order
    context = {}
    try:
        if order_id:
            order = Order.objects.get(id=order_id)
            items = order.orderitem_set.all().select_related('product')
            context.update({
                'order': order,
                'items': items,
                'total_amount': order.total_amount,
                'customer': order.customer,
                'queue_info': getattr(order, 'coffeequeue', None),
            })
        context.update({
            'now': timezone.now(),
            'user': request.user,
            'is_staff': request.user.is_authenticated and request.user.is_staff,
        })
    except Order.DoesNotExist:
        logger.error(f"订单不存在: {order_id}")
    return context


# ==================== 支付状态处理函数 ====================

def update_payment_status(order, status, payment_method=None):
    """更新支付狀態 - 使用 OrderStatusManager"""
    try:
        old_status = order.payment_status
        if status == 'paid':
            result = OrderStatusManager.process_payment_success(order_id=order.id, request=None)
            if not result['success']:
                logger.error(f"支付成功處理失敗: {result['message']}")
                return False
        elif status == 'cancelled':
            result = OrderStatusManager.mark_as_cancelled_manually(
                order_id=order.id, staff_name='system', reason='支付取消'
            )
            if not result['success']:
                logger.error(f"取消訂單失敗: {result['message']}")
                return False
        elif status == 'pending':
            order.payment_status = status
            if payment_method:
                order.payment_method = payment_method
            order.save()
            logger.info(f"訂單 {order.id} 支付狀態變更為 {status}")
        else:
            order.payment_status = status
            if payment_method:
                order.payment_method = payment_method
            order.save()
            logger.info(f"訂單 {order.id} 支付狀態變更為 {status}")
        logger.info(f"訂單 {order.id} 支付狀態從 {old_status} 更新為 {status}")
        return True
    except Exception as e:
        logger.error(f"更新支付狀態失敗: {str(e)}")
        return False


def check_payment_conditions(order):
    """检查支付条件是否满足 - 使用 OrderStatusManager"""
    try:
        now = timezone.now()
        if order.created_at < now - timezone.timedelta(minutes=15):
            if order.status == 'pending':
                result = OrderStatusManager.mark_as_cancelled_manually(
                    order_id=order.id, staff_name='system', reason='支付超時自動取消'
                )
                if result['success']:
                    return {'can_pay': False, 'reason': '订单已超时，已自动取消', 'needs_redirect': True, 'redirect_url': f'/eshop/order/{order.id}/'}
                else:
                    return {'can_pay': False, 'reason': '订单已超时，但取消失败', 'needs_redirect': True, 'redirect_url': f'/eshop/order/{order.id}/'}
        if order.status in ['paid', 'preparing', 'ready', 'completed']:
            return {'can_pay': False, 'reason': '订单已支付', 'needs_redirect': True, 'redirect_url': f'/eshop/order/{order.id}/'}
        if order.status == 'cancelled':
            return {'can_pay': False, 'reason': '订单已取消', 'needs_redirect': True, 'redirect_url': '/eshop/'}
        return {'can_pay': True, 'reason': '可以支付', 'payment_method': order.payment_method}
    except Exception as e:
        logger.error(f"检查支付条件失败: {str(e)}")
        return {'can_pay': False, 'reason': f'系统错误: {str(e)}', 'needs_redirect': True, 'redirect_url': '/eshop/'}


# ==================== 統一錯誤處理系統 ====================

class OrderErrorHandler:
    """訂單錯誤處理器 - 統一處理所有訂單相關錯誤"""

    @staticmethod
    def handle_generic_error(request, error, redirect_url='cart:cart_detail', error_type='general'):
        """處理通用錯誤 - 改進備用重定向邏輯"""
        try:
            error_message = str(error) if error else "未知錯誤"
            if error_type in ['payment', 'validation']:
                logger.error(f"[{error_type.upper()} ERROR] {error_message}")
            else:
                logger.warning(f"[{error_type.upper()} ERROR] {error_message}")

            user_friendly_message = OrderErrorHandler.get_user_friendly_message(error_type, error_message)
            messages.error(request, user_friendly_message)

            from django.shortcuts import redirect
            from django.urls import reverse, NoReverseMatch

            # 嘗試多個備用重定向目標
            for url_candidate in [redirect_url, 'eshop:index', 'index', '/']:
                try:
                    if url_candidate == '/':
                        return redirect(url_candidate)
                    return redirect(reverse(url_candidate))
                except NoReverseMatch:
                    continue

            # 最終保底
            return redirect('/')
        except Exception as e:
            logger.critical(f"處理錯誤時發生異常: {str(e)}")
            return redirect('/')  # 無論如何不讓頁面崩潰

    @staticmethod
    def get_user_friendly_message(error_type, technical_message):
        """將技術性錯誤訊息轉換為用戶友好訊息"""
        error_map = {
            'payment': {
                'default': '支付處理失敗，請稍後重試',
                'timeout': '支付超時，請重新嘗試',
                'insufficient_funds': '餘額不足，請使用其他支付方式',
                'network_error': '網絡連接失敗，請檢查網絡後重試',
            },
            'order': {
                'default': '訂單處理失敗，請聯繫客服',
                'unavailable': '商品暫時無法購買',
                'sold_out': '商品已售罄',
                'invalid_quantity': '商品數量無效',
            },
            'validation': {
                'default': '輸入資料有誤，請檢查後重試',
                'phone': '電話號碼格式不正確',
                'email': '電子郵件格式不正確',
                'pickup_time': '取貨時間選擇無效',
            },
            'cart': {
                'default': '購物車操作失敗',
                'empty': '購物車為空',
                'item_not_found': '商品不存在',
            },
            'general': {
                'default': '系統繁忙，請稍後重試',
                'network': '網絡錯誤，請檢查連接',
                'server': '伺服器錯誤，請稍後再試',
            }
        }
        if error_type in error_map:
            for key in error_map[error_type]:
                if key.lower() in technical_message.lower():
                    return error_map[error_type][key]
            return error_map[error_type]['default']
        return error_map['general']['default']

    @staticmethod
    def handle_json_error(message, status=400, error_type='general'):
        """處理JSON響應錯誤"""
        from django.http import JsonResponse
        logger.error(f"[{error_type.upper()}] JSON錯誤: {message}")
        response_data = {
            'success': False,
            'error': message,
            'error_type': error_type,
            'user_friendly_message': OrderErrorHandler.get_user_friendly_message(error_type, message)
        }
        return JsonResponse(response_data, status=status)

    @staticmethod
    def handle_api_error(exception, request=None):
        """處理API錯誤（供API視圖使用）"""
        error_message = str(exception)
        if hasattr(exception, 'status_code'):
            status_code = exception.status_code
        elif 'permission' in error_message.lower() or '權限' in error_message:
            status_code = 403
        elif 'not found' in error_message.lower() or '不存在' in error_message:
            status_code = 404
        elif 'validation' in error_message.lower() or '驗證' in error_message:
            status_code = 400
            error_type = 'validation'
        else:
            status_code = 500
            error_type = 'server'
        logger.error(f"API錯誤 [{status_code}]: {error_message}")
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            from django.contrib import messages
            messages.error(request, OrderErrorHandler.get_user_friendly_message('general', error_message))
        return OrderErrorHandler.handle_json_error(error_message, status=status_code, error_type=error_type)


def handle_order_error(request, error_message, redirect_url='cart:cart_detail', error_type='general'):
    """統一處理訂單錯誤（兼容舊代碼）"""
    return OrderErrorHandler.handle_generic_error(request, error_message, redirect_url, error_type)


# ==================== 裝飾器 - 統一錯誤處理 ====================

def catch_order_errors(redirect_url='cart:cart_detail', error_type='general'):
    """裝飾器：捕獲訂單相關錯誤並統一處理"""
    from functools import wraps
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            try:
                return view_func(request, *args, **kwargs)
            except Exception as e:
                logger.error(f"視圖 {view_func.__name__} 執行錯誤: {str(e)}")
                logger.error(f"錯誤詳情: {traceback.format_exc()}")
                return OrderErrorHandler.handle_generic_error(request, e, redirect_url, error_type)
        return wrapper
    return decorator


def catch_api_errors():
    """裝飾器：捕獲API錯誤並返回JSON響應"""
    from functools import wraps
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            try:
                return view_func(request, *args, **kwargs)
            except Exception as e:
                return OrderErrorHandler.handle_api_error(e, request)
        return wrapper
    return decorator


# ==================== 特定錯誤處理函數 ====================

def handle_payment_error(request, error, order_id=None):
    """處理支付錯誤"""
    error_message = str(error)
    if 'timeout' in error_message.lower():
        error_type = 'payment'
        user_message = '支付超時，請重新嘗試'
    elif 'insufficient' in error_message.lower():
        error_type = 'payment'
        user_message = '餘額不足，請使用其他支付方式'
    elif 'network' in error_message.lower():
        error_type = 'payment'
        user_message = '網絡連接失敗，請檢查網絡後重試'
    else:
        error_type = 'payment'
        user_message = '支付處理失敗，請稍後重試'
    logger.error(f"支付錯誤 [訂單ID: {order_id}]: {error_message}")
    from django.contrib import messages
    messages.error(request, user_message)
    if order_id:
        try:
            from .models import OrderModel
            order = OrderModel.objects.get(id=order_id)
            return redirect('eshop:order_detail', order_id=order_id)
        except:
            pass
    return redirect('eshop:order_confirm')


def handle_validation_error(request, field_errors):
    """處理表單驗證錯誤"""
    for field, error in field_errors.items():
        if field == 'phone':
            messages.error(request, '電話號碼格式不正確，請使用香港電話號碼格式')
        elif field == 'email':
            messages.error(request, '電子郵件格式不正確')
        elif field == 'pickup_time':
            messages.error(request, '請選擇有效的取貨時間')
        else:
            messages.error(request, f'{field}: {error}')
    if hasattr(request, 'session'):
        request.session['form_data'] = request.POST.dict()
        request.session.modified = True
    from django.http import HttpResponseRedirect
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))


def handle_cart_error(request, error):
    """處理購物車錯誤"""
    error_message = str(error)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return OrderErrorHandler.handle_json_error(error_message, status=400, error_type='cart')
    else:
        messages.error(request, '購物車操作失敗，請重新嘗試')
        return redirect('cart:cart_detail')


# ==================== 上下文處理器 ====================

def error_context_processor(request):
    """錯誤上下文處理器 - 將錯誤訊息添加到模板上下文"""
    from django.contrib.messages import get_messages
    context = {}
    messages_list = list(get_messages(request))
    error_messages = [msg for msg in messages_list if msg.tags == 'error']
    warning_messages = [msg for msg in messages_list if msg.tags == 'warning']
    success_messages = [msg for msg in messages_list if msg.tags == 'success']
    info_messages = [msg for msg in messages_list if msg.tags == 'info']
    context.update({
        'error_messages': error_messages,
        'warning_messages': warning_messages,
        'success_messages': success_messages,
        'info_messages': info_messages,
        'has_errors': len(error_messages) > 0,
        'has_warnings': len(warning_messages) > 0,
        'has_success': len(success_messages) > 0,
        'has_info': len(info_messages) > 0,
    })
    return context


# ==================== 實用工具函數 ====================

def log_error_with_context(error, context=None, level='error'):
    """記錄帶有上下文的錯誤"""
    error_message = str(error)
    log_message = f"錯誤: {error_message}"
    if context:
        context_str = ', '.join([f"{k}={v}" for k, v in context.items()])
        log_message += f" | 上下文: {context_str}"
    log_message += f"\n堆棧跟踪: {traceback.format_exc()}"
    log_func = getattr(logger, level.lower(), logger.error)
    log_func(log_message)


def safe_execute(func, *args, **kwargs):
    """安全執行函數，捕獲並記錄異常"""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        logger.error(f"安全執行失敗 [{func.__name__}]: {str(e)}")
        logger.debug(f"詳細錯誤: {traceback.format_exc()}")
        return None


# ==================== 中間件（可選） ====================

class ErrorLoggingMiddleware:
    """錯誤日誌中間件 - 捕獲並記錄所有未處理的異常"""
    def __init__(self, get_response):
        self.get_response = get_response
    def __call__(self, request):
        return self.get_response(request)
    def process_exception(self, request, exception):
        logger.critical(f"未捕獲的異常 [{request.path}]: {str(exception)}")
        logger.critical(f"請求方法: {request.method}")
        logger.critical(f"用戶: {request.user}")
        logger.critical(f"堆棧跟踪: {traceback.format_exc()}")
        return None