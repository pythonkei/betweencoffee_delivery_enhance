# eshop/views/order_views.py
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.urls import reverse
from django.core.exceptions import PermissionDenied
from django.views.decorators.http import require_GET, require_POST
from datetime import timedelta

# ✅ 修復：使用絕對導入，避免相對導入問題
from eshop.models import OrderModel, CoffeeItem, BeanItem, CoffeeQueue
from eshop.order_status_manager import OrderStatusManager
from eshop.view_utils import (
    validate_and_format_phone,
    find_existing_pending_order,
    handle_order_error,
    handle_payment_error,
    handle_validation_error,
    OrderErrorHandler,  # 新增：統一錯誤處理器
)

from eshop.payment_utils import get_payment_tools
from cart.cart import Cart


# 设置日志
logger = logging.getLogger(__name__)


# ==================== 訂單確認視圖 ====================


@method_decorator(login_required, name='dispatch')
class OrderConfirm(View):
    """訂單確認與付款頁面 - 修改後版本使用統一支付工具"""
    template_name = 'eshop/order_confirm.html'
    
    def get(self, request, *args, **kwargs):
        try:
            # 优先检查购物车数据
            cart_data = request.session.get('pending_order')
            quick_order_data = request.session.get('quick_order_data')
            
            # ✅ 修正：普通訂單不需要取貨時間選擇，所以不從 session 獲取
            # 只有快速訂單才需要從 session 獲取之前選擇的取貨時間
            previous_pickup_time = '5'  # 普通訂單固定為5分鐘（隱藏）
            
            if cart_data and quick_order_data:
                logger.info("检测到购物车数据和快速订单数据同时存在，优先使用购物车数据")
                if 'quick_order_data' in request.session:
                    del request.session['quick_order_data']
                    request.session.modified = True
                    
            if cart_data:
                items = []
                total_price = 0  # 添加这行：初始化总价变量
                
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
                            
                        # 计算价格
                        if item_type == 'bean':
                            weight = item_data.get('weight', '200g')
                            price = float(item.get_price(weight))
                        else:
                            price = float(item.price)
                        
                        item_total = price * item_data.get('quantity', 1)
                        total_price += item_total  # 累加到总价
                        
                        items.append({
                            'name': item.name,
                            'quantity': item_data.get('quantity', 1),
                            'total_price': item_total,  # 单项总价
                            'type': item_type,
                            'image': item_data.get('image', ''),
                            'cup_level': item_data.get('cup_level'),
                            'milk_level': item_data.get('milk_level'),
                            'grinding_level': item_data.get('grinding_level'),
                            'weight': item_data.get('weight'),
                        })
                    except (CoffeeItem.DoesNotExist, BeanItem.DoesNotExist):
                        # 如果数据库中没有找到，使用session中的数据
                        price = float(item_data.get('price', 0))
                        quantity = item_data.get('quantity', 1)
                        item_total = price * quantity
                        total_price += item_total  # 累加到总价
                        
                        items.append({
                            'name': item_data.get('name', '商品'),
                            'quantity': quantity,
                            'total_price': item_total,
                            'type': item_type,
                            'image': item_data.get('image', ''),
                            'cup_level': item_data.get('cup_level'),
                            'milk_level': item_data.get('milk_level'),
                            'grinding_level': item_data.get('grinding_level'),
                            'weight': item_data.get('weight'),
                        })
                        continue

                # ✅ 修正：普通訂單 - 固定為5分鐘，不顯示選擇（隱藏）
                initial_data = {
                    'pickup_time': '5'  # 固定值，隱藏不顯示
                }
                is_quick_order = False
                
            elif quick_order_data:
                items = quick_order_data.get('items', [])
                total_price = quick_order_data.get('total_price', 0)
                
                # ✅ 修正：快速訂單 - 繼承首頁選擇的取貨時間，並允許修改
                pickup_time_from_session = quick_order_data.get('pickup_time', '5')
                
                # 轉換格式：如果格式是「5 分鐘後」，提取數字部分
                if isinstance(pickup_time_from_session, str) and '分鐘' in pickup_time_from_session:
                    # 提取數字部分，例如「5 分鐘後」 -> 「5」
                    import re
                    match = re.search(r'(\d+)', pickup_time_from_session)
                    if match:
                        pickup_time_from_session = match.group(1)
                
                initial_data = {
                    'name': quick_order_data.get('name', ''),
                    'phone': quick_order_data.get('phone', ''),
                    'email': quick_order_data.get('email', ''),
                    'pickup_time': pickup_time_from_session,  # ✅ 使用轉換後的取貨時間
                }
                is_quick_order = True
            else:
                messages.error(request, "没有待处理的订单")
                return redirect('cart:cart_detail')

            context = {
                'items': items,
                'total_price': total_price,
                'user': request.user,
                'initial_data': initial_data,
                'is_quick_order': is_quick_order
            }
            return render(request, self.template_name, context)
        
        except Exception as e:
            # ✅ 使用統一錯誤處理
            logger.error(f"OrderConfirm.get() 發生錯誤: {str(e)}")
            return handle_order_error(
                request, 
                e, 
                redirect_url='cart:cart_detail', 
                error_type='order'
            )


    def post(self, request, *args, **kwargs):
        logger.info("=== OrderConfirm POST 方法开始执行 ===")
        
        try:
            quick_order_data = request.session.get('quick_order_data')
            
            if quick_order_data:
                # ✅ 快速訂單：處理取貨時間選擇
                pickup_time_choice = request.POST.get('pickup_time', '5')
                
                # ✅ 新增：保存取货时间到 session，供下次快速訂單使用
                request.session['selected_pickup_time'] = pickup_time_choice
                request.session.modified = True
                
                items = quick_order_data.get('items', [])
                total_price = quick_order_data.get('total_price', 0)
                is_quick_order = True

                # 确保每个商品都有图片
                for item in items:
                    if item.get('type') == 'coffee' and item.get('id'):
                        try:
                            coffee_item = CoffeeItem.objects.get(id=item['id'])
                            item['image'] = coffee_item.image.url if coffee_item.image else '/static/images/default-coffee.png'
                        except CoffeeItem.DoesNotExist:
                            item['image'] = '/static/images/default-coffee.png'
            else:
                # ✅ 普通訂單：使用固定取貨時間（5分鐘）
                pickup_time_choice = '5'  # 固定值
                
                cart_data = request.session.get('pending_order', {})
                if not cart_data:
                    messages.error(request, "您的購物車是空的")
                    return redirect('cart:cart_detail')
                    
                items = []
                for item_key, item_data in cart_data.get('items', {}).items():
                    parts = item_key.split('_')
                    if len(parts) < 2:
                        continue
                        
                    item_type = parts[0]
                    item_id = parts[1]

                    try:
                        if item_type == 'coffee':
                            db_item = CoffeeItem.objects.get(id=item_id)
                        elif item_type == 'bean':
                            db_item = BeanItem.objects.get(id=item_id)
                        else:
                            continue
                        
                        image_url = db_item.image.url if db_item.image else '/static/images/default-product.png'
                        
                        # 计算价格
                        if item_type == 'bean':
                            weight = item_data.get('weight', '200g')
                            price = float(db_item.get_price(weight))
                        else:
                            price = float(db_item.price)

                        items.append({
                            'type': item_type,
                            'id': int(item_id),
                            'name': db_item.name,
                            'price': price,
                            'quantity': item_data.get('quantity', 1),
                            'cup_level': item_data.get('cup_level'),
                            'milk_level': item_data.get('milk_level'),
                            'grinding_level': item_data.get('grinding_level'),
                            'weight': item_data.get('weight'),
                            'image': image_url
                        })
                    except (CoffeeItem.DoesNotExist, BeanItem.DoesNotExist):
                        # 使用session中的旧数据
                        items.append({
                            'type': item_type,
                            'id': int(item_id),
                            'name': item_data.get('name', '商品'),
                            'price': float(item_data.get('price', 0)),
                            'quantity': item_data.get('quantity', 1),
                            'cup_level': item_data.get('cup_level'),
                            'milk_level': item_data.get('milk_level'),
                            'grinding_level': item_data.get('grinding_level'),
                            'weight': item_data.get('weight'),
                            'image': item_data.get('image', '/static/images/default-product.png')
                        })

                total_price = float(cart_data.get('total_price', 0))
                is_quick_order = False

            # ✅ 修正：驗證取貨時間選擇是否有效（快速訂單才需要驗證）
            if is_quick_order:
                valid_choices = ['5', '10', '15', '20', '30']
                if pickup_time_choice not in valid_choices:
                    pickup_time_choice = '5'
            else:
                # 普通訂單固定為5分鐘
                pickup_time_choice = '5'

            # 验证电话号码
            phone = request.POST.get('phone', '')
            formatted_phone = validate_and_format_phone(phone)
            if not formatted_phone:
                # ✅ 使用驗證錯誤處理
                field_errors = {'phone': '電話號碼格式不正確'}
                return handle_validation_error(request, field_errors)

            # 检查是否存在可重用的未支付订单
            existing_order = find_existing_pending_order(
                request.user, items, total_price
            )
            
            if existing_order:
                logger.info(f"找到可重用的未支付订单: {existing_order.id}")
                existing_order.name = request.POST.get('name', '')
                existing_order.email = request.POST.get('email', '')
                existing_order.phone = formatted_phone
                existing_order.pickup_time_choice = pickup_time_choice
                existing_order.payment_method = request.POST.get('payment_method', 'alipay')
                
                try:
                    # 重新計算時間
                    existing_order.calculate_times_based_on_pickup_choice()
                    existing_order.set_payment_timeout(minutes=5)
                    existing_order.save()
                except Exception as e:
                    logger.error(f"更新现有订单失败: {str(e)}")
                    existing_order = None
            
            if not existing_order:
                try:
                    # 創建訂單時計算時間
                    order = OrderModel.objects.create(
                        user=request.user if request.user.is_authenticated else None,
                        total_price=total_price,
                        name=request.POST.get('name', ''),
                        email=request.POST.get('email', ''),
                        phone=formatted_phone,
                        items=items,
                        order_type='quick' if is_quick_order else 'normal',
                        is_quick_order=is_quick_order,
                        pickup_time_choice=pickup_time_choice,
                        status='pending',
                        payment_method=request.POST.get('payment_method', 'alipay'),
                        payment_status='pending',
                    )
                    
                    logger.info(f"创建新订单，ID: {order.id}")
                    
                    # 計算取貨時間相關的時間
                    order.calculate_times_based_on_pickup_choice()
                    order.set_payment_timeout(minutes=5)
                    order.save()
                    order.refresh_from_db()
                    
                except Exception as e:
                    logger.error(f"订单创建失败: {str(e)}")
                    messages.error(request, "创建订单失败，请稍后重试")
                    return redirect('cart:cart_detail')
            else:
                order = existing_order

            # 清除session数据
            if 'pending_order' in request.session:
                del request.session['pending_order']
            if 'quick_order_data' in request.session:
                del request.session['quick_order_data']
            request.session.modified = True

            # 设置session中的订单ID
            request.session['last_order_id'] = order.id
            request.session.modified = True

            payment_method = request.POST.get('payment_method', 'alipay')
            return self.handle_payment(request, order, payment_method)

        except Exception as e:
            # ✅ 使用統一錯誤處理
            logger.error(f"订单创建失败: {str(e)}")
            return handle_order_error(
                request, 
                e, 
                redirect_url='cart:cart_detail', 
                error_type='order'
            )


    def handle_payment(self, request, order, payment_method):
        """统一处理付款 - 使用统一的支付工具"""
        try:
            logger.info(f"处理支付方式: {payment_method}, 订单: {order.id}")
            
            # 使用统一的支付工具获取器
            payment_tools = get_payment_tools(payment_method)
            
            if not payment_tools:
                logger.error(f"无效的支付方式: {payment_method}")
                messages.error(request, "请选择有效的付款方式")
                return redirect('eshop:order_confirm')
            
            if payment_method == 'alipay':
                # 检查是否有创建支付的功能
                if 'create' not in payment_tools:
                    logger.error(f"支付宝支付工具缺失创建函数")
                    messages.error(request, "支付宝支付暂时不可用，请选择其他支付方式")
                    return redirect(reverse('eshop:order_payment_confirmation') + f'?order_id={order.id}&payment_status=error')
                
                logger.info("重定向到支付宝支付")
                try:
                    payment_url = payment_tools['create'](order, request)
                    if payment_url:
                        order.increment_payment_attempts()
                        logger.info(f"支付宝支付URL生成成功，订单: {order.id}")
                        return redirect(payment_url)
                    else:
                        logger.error(f"支付宝支付URL生成失败，订单: {order.id}")
                        messages.error(request, "支付宝支付暂时不可用，请选择其他支付方式")
                        return redirect(reverse('eshop:order_payment_confirmation') + f'?order_id={order.id}&payment_status=error')
                except Exception as e:
                    logger.error(f"支付宝支付处理异常: {str(e)}")
                    messages.error(request, "支付宝支付暂时不可用，请选择其他支付方式")
                    return redirect(reverse('eshop:order_payment_confirmation') + f'?order_id={order.id}&payment_status=error')
                    
            elif payment_method == 'paypal':
                try:
                    if 'create' not in payment_tools:
                        logger.error(f"PayPal支付工具缺失创建函数")
                        messages.error(request, "PayPal支付暂时不可用，请选择其他支付方式")
                        return redirect(reverse('eshop:order_payment_confirmation') + f'?order_id={order.id}&payment_status=error')
                    
                    paypal_url = payment_tools['create'](order, request)
                    if paypal_url:
                        request.session['pending_paypal_order_id'] = order.id
                        request.session.modified = True
                        logger.info(f"PayPal支付创建成功，订单: {order.id}")
                        return redirect(paypal_url)
                    else:
                        logger.error(f"PayPal支付创建失败，订单: {order.id}")
                        messages.error(request, "PayPal支付暂时不可用，请选择其他支付方式")
                        return redirect(reverse('eshop:order_payment_confirmation') + f'?order_id={order.id}&payment_status=error')
                except Exception as e:
                    logger.error(f"PayPal支付处理异常: {str(e)}")
                    messages.error(request, "PayPal支付暂时不可用，请选择其他支付方式")
                    return redirect(reverse('eshop:order_payment_confirmation') + f'?order_id={order.id}&payment_status=error')
                    
            elif payment_method == 'fps':
                return self.handle_fps_payment(request, order)
                
            elif payment_method == 'cash':
                return self.handle_cash_payment(request, order)
                
            else:
                logger.error(f"无效的支付方式: {payment_method}")
                messages.error(request, "请选择有效的付款方式")
                return redirect('eshop:order_confirm')
                
        except Exception as e:
            # ✅ 使用支付特定錯誤處理
            return handle_payment_error(request, e, order.id)


    def handle_fps_payment(self, request, order):
        """處理FPS轉數快支付"""
        try:
            # 使用统一的支付工具
            payment_tools = get_payment_tools('fps')
            
            if not payment_tools or 'create_reference' not in payment_tools:
                messages.error(request, "FPS支付系统暂时不可用")
                return redirect('eshop:order_confirm')
            
            # 生成FPS参考号
            fps_reference = payment_tools['create_reference'](order.id)
            
            order.fps_reference = fps_reference
            order.save()
            
            request.session['pending_fps_order_id'] = order.id
            request.session.modified = True
            
            return redirect('eshop:fps_payment', order_id=order.id)
                
        except Exception as e:
            logger.error(f"FPS支付處理失敗: {str(e)}")
            messages.error(request, "FPS支付處理失敗，請稍後重試")
            return redirect('eshop:order_confirm')
        

    def handle_cash_payment(self, request, order):
        """處理現金支付"""
        try:
            # ✅ 已修復：使用 OrderStatusManager
            from eshop.order_status_manager import OrderStatusManager
            result = OrderStatusManager.process_order_status_change(
                order_id=order.id,
                new_status='pending',
                staff_name=request.user.username if hasattr(request, 'user') else 'system'
            )
            if not result.get('success'):
                logger.error(f"標記訂單 {order.id} 為 pending 失敗: {result.get('message')}")
            order.payment_status="pending"
            order.save()
            
            request.session['pending_cash_order_id'] = order.id
            request.session.modified = True
            
            return redirect('eshop:cash_payment', order_id=order.id)
            
        except Exception as e:
            logger.error(f"現金支付處理失敗: {str(e)}")
            messages.error(request, "現金支付處理失敗，請稍後重試")
            return redirect('eshop:order_confirm')


# ==================== 快速訂單相關函式 ====================

@require_POST
def quick_order(request):
    """快速订单 - 直接使用前端传回的数字取货时间"""
    name = request.POST.get('name', '')
    phone = request.POST.get('phone', '')
    email = request.POST.get('email', '')
    pickup_time_raw = request.POST.get('pickup_time', '5')
    
    logger.info(f"快速订单数据: name={name}, phone={phone}")
    
    # ----- 直接解析数字取货时间（前端 select value 为纯数字）-----
    try:
        minutes_to_add = int(pickup_time_raw)
        # 保证在有效范围内
        if minutes_to_add not in (5, 10, 15, 20, 30):
            minutes_to_add = 5
    except (ValueError, TypeError):
        minutes_to_add = 5
    
    pickup_time_choice = str(minutes_to_add)
    pickup_time_display = f"{minutes_to_add}分鐘後"
    # ---------------------------------------------------------
    
    try:
        # 尝试获取WakeMeup咖啡
        wake_meup_coffee = CoffeeItem.objects.get(id=1)
        quick_order_item = {
            'type': 'coffee',
            'id': 1,
            'name': wake_meup_coffee.name,
            'price': float(wake_meup_coffee.price),
            'quantity': 1,
            'cup_level': 'Medium',
            'cup_level_cn': '中',
            'milk_level': 'Medium',
            'milk_level_cn': '正常',
            'image': wake_meup_coffee.image.url if wake_meup_coffee.image else '/static/images/default-coffee.png',
            'total_price': float(wake_meup_coffee.price)
        }
    except CoffeeItem.DoesNotExist:
        logger.warning("CoffeeItem id=1 不存在，使用默认值")
        quick_order_item = {
            'type': 'coffee',
            'id': 1,
            'name': 'WakeMeup 醒神配方',
            'price': 38.0,
            'quantity': 1,
            'cup_level': 'Medium',
            'cup_level_cn': '中',
            'milk_level': 'Medium',
            'milk_level_cn': '正常',
            'image': '/static/images/default-coffee.png',
            'total_price': 38.0
        }
    
    # 儲存到 session，同時保存顯示文本和數字選擇
    request.session['quick_order_data'] = {
        'items': [quick_order_item],
        'total_price': quick_order_item['total_price'],
        'name': name,
        'phone': phone,
        'email': email,
        'pickup_time': pickup_time_display,       # 用於前台顯示（如 "5分鐘後"）
        'pickup_time_choice': pickup_time_choice, # 用於表單預選、訂單建立（純數字）
        'is_quick_order': True,
        'cup_level': 'Medium'
    }
    request.session.modified = True
    
    logger.info(f"快速订单数据已保存到session, pickup_time: {pickup_time_display}, choice: {pickup_time_choice}")
    
    return redirect('eshop:order_confirm')


@login_required
def clear_quick_order(request):
    """清除快速订单数据，返回购物车"""
    if 'quick_order_data' in request.session:
        del request.session['quick_order_data']
        request.session.modified = True
        messages.info(request, "已清除快速订单数据")
        logger.info("清除快速订单数据成功")
    
    # 如果有购物车数据，显示购物车
    if 'pending_order' in request.session and request.session['pending_order']:
        return redirect('cart:cart_detail')
    else:
        return redirect('/')


# ==================== 訂單詳情檢視 ====================


def order_detail(request, order_id):
    """订单详情页面"""
    try:
        order = get_object_or_404(OrderModel, id=order_id)
        
        # 验证权限
        if request.user.is_authenticated and order.user != request.user:
            raise PermissionDenied("您无权查看此订单")
        
        items = order.get_items_with_chinese_options()
        
        # 获取队列信息（如果存在）
        queue_info = None
        try:
            queue_info = CoffeeQueue.objects.get(order=order)
        except CoffeeQueue.DoesNotExist:
            pass
        
        context = {
            'order': order,
            'items': items,
            'queue_info': queue_info,
        }
        return render(request, 'eshop/order_detail.html', context)
        
    except Exception as e:
        logger.error(f"订单详情页面错误: {str(e)}")
        # ✅ 使用統一錯誤處理
        return handle_order_error(
            request, 
            e, 
            redirect_url='/', 
            error_type='general'
        )


@require_GET
def order_status_api(request, order_id):
    """
    訂單狀態API - 供前端UnifiedOrderUpdater使用
    返回統一的JSON格式數據
    """
    try:
        order = get_object_or_404(OrderModel, id=order_id)
        
        
        # 驗證權限
        if request.user.is_authenticated and order.user != request.user:
            return JsonResponse({
                'success': False,
                'error': '無權查看此訂單'
            }, status=403)
        
        # 使用 OrderStatusManager 獲取狀態
        status_manager = OrderStatusManager(order)
        status_info = status_manager.get_display_status()
        
        # 構建API響應
        response_data = {
            'success': True,
            'order_id': order.id,
            'status': order.status,
            'payment_status': order.payment_status,
            
            # 進度條數據
            'progress_percentage': status_info['progress_percentage'],
            'progress_display': status_info['progress_display'],
            'is_ready': status_info['is_ready'],
            
            # 隊列數據
            'queue_info': status_info.get('queue_info'),
            'queue_display': status_info.get('queue_display', ''),
            'queue_message': status_info.get('queue_message', ''),
            'remaining_display': status_info.get('remaining_display', ''),
            'estimated_time': status_info.get('estimated_time', ''),
            
            # 狀態消息
            'status_message': status_info.get('status_message', ''),
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        logger.error(f"訂單狀態API錯誤: {str(e)}")
        # ✅ 使用JSON錯誤處理
        from eshop.view_utils import OrderErrorHandler
        return OrderErrorHandler.handle_json_error(
            str(e), 
            status=500, 
            error_type='api'
        )


# 在 order_payment_confirmation 視圖中，確保 context 包含必要的數據
def order_payment_confirmation(request, order_id=None):
    """
    統一的訂單支付確認頁面 - 修復純咖啡豆訂單問題
    """
    # 獲取訂單ID
    if order_id is None:
        order_id = request.GET.get('order_id') or request.session.get('last_order_id')
    
    logger.info(f"訂單確認頁面 - 接收到的 order_id: {order_id}")
    
    if not order_id:
        context = {
            'payment_status': 'error',
            'error_message': '未找到訂單信息'
        }
        return render(request, 'eshop/order_payment_confirmation.html', context)
    
    try:
        order = get_object_or_404(OrderModel, id=order_id)
        
        # ✅ 修復：直接使用 order.payment_status 的值
        logger.info(f"訂單 {order.id} 當前狀態: status={order.status}, payment_status={order.payment_status}, payment_method={order.payment_method}")
        
        # 檢查支付狀態
        if order.payment_status == 'paid':
            payment_status_for_template = 'paid'
        elif order.payment_status == 'pending':
            payment_status_for_template = 'pending'
        else:
            payment_status_for_template = 'unknown'
            logger.warning(f"訂單 {order.id} 支付狀態異常: {order.payment_status}")
        
        # ✅ 使用 OrderStatusManager 統一處理
        status_manager = OrderStatusManager(order)
        status_info = status_manager.get_display_status()

        # ✅ 使用新的模型方法
        order_type = order.get_order_type_summary()
        
        # 確保訂單有取餐碼
        if not order.pickup_code:
            order.save()  # 這會觸發取餐碼生成
        
        context = {
            'order': order,
            'payment_status': payment_status_for_template,
            'order_type': order_type,
            'status_info': status_info,
        }

        logger.info(f"訂單確認頁面 - 訂單ID: {order.id}, 支付狀態: {payment_status_for_template}")
        
        return render(request, 'eshop/order_payment_confirmation.html', context)
        
    except OrderModel.DoesNotExist:
        return handle_order_error(
            request,
            f'訂單 #{order_id} 不存在',
            redirect_url='eshop:order_detail',  # 改為訂單詳情（但訂單不存在，可能需要跳轉到列表）
            error_type='order'
        )
    except Exception as e:
        logger.error(f"訂單確認頁面錯誤: {e}", exc_info=True)
        # 如果訂單存在，跳轉到訂單詳情頁；否則跳轉到首頁
        try:
            order = OrderModel.objects.get(id=order_id)
            redirect_url = reverse('eshop:order_detail', args=[order_id])
        except:
            redirect_url = '/'
        return handle_order_error(
            request,
            e,
            redirect_url=redirect_url,
            error_type='general'
        )

# ==================== 支付状态检查函数 ====================

def check_order_status(request, order_id):
    """检查订单状态（供前端轮询）"""
    try:
        order = get_object_or_404(OrderModel, id=order_id)
        
        # 验证权限
        if request.user.is_authenticated and order.user != request.user:
            return JsonResponse({
                'success': False,
                'error': '无权查看此订单'
            }, status=403)
        
        # 获取队列信息
        queue_info = None
        try:
            queue_info = CoffeeQueue.objects.get(order=order)
        except CoffeeQueue.DoesNotExist:
            pass
        
        # ✅ 修復：移除了錯誤的導入語句
        # 检查是否需要重试支付
        needs_retry = (
            order.payment_method == 'alipay' and 
            order.created_at < timezone.now() - timedelta(minutes=5)
        )
        
        return JsonResponse({
            'success': True,
            'order_id': order.id,
            'status': order.status,
            'payment_status': order.get_payment_status_display(),
            'queue_position': queue_info.position if queue_info else None,
            'estimated_time': queue_info.estimated_completion_time.isoformat() if queue_info else None,
            'needs_retry': needs_retry,
            'redirect_url': f'/eshop/continue_payment/{order.id}/' if needs_retry else None
        })
        
    except Exception as e:
        logger.error(f"检查订单状态错误: {str(e)}")
        # ✅ 使用JSON錯誤處理
        from eshop.view_utils import OrderErrorHandler
        return OrderErrorHandler.handle_json_error(
            str(e), 
            status=500, 
            error_type='api'
        )


def continue_payment(request, order_id):
    """继续支付（用于支付超时后的重试）"""
    try:
        order = get_object_or_404(OrderModel, id=order_id)
        
        if order.status != 'pending':
            messages.warning(request, f"订单状态为 {order.status}，无需重新支付")
            return redirect('eshop:order_detail', order_id=order.id)
        
        # 根据支付方式重定向
        if order.payment_method == 'alipay':
            return redirect('eshop:alipay_payment', order_id=order.id)
        elif order.payment_method == 'fps':
            return redirect('eshop:fps_payment', order_id=order.id)
        elif order.payment_method == 'cash':
            return redirect('eshop:cash_payment', order_id=order.id)
        else:
            messages.error(request, "未知的支付方式")
            return redirect('eshop:order_detail', order_id=order.id)
            
    except Exception as e:
        logger.error(f"继续支付错误: {str(e)}")
        # ✅ 使用統一錯誤處理
        return handle_order_error(
            request, 
            e, 
            redirect_url='/', 
            error_type='payment'
        )


# ==================== 支付确认视图 ====================

# ==================== 其他辅助函数（保留原有功能） ====================

def get_order_summary(request):
    """获取订单摘要（用于购物车预览）"""
    try:
        cart = Cart(request)
        total_amount = 0
        item_count = 0
        
        for item in cart:
            try:
                total_amount += float(item['price']) * item['quantity']
                item_count += item['quantity']
            except (KeyError, ValueError):
                continue
        
        return JsonResponse({
            'success': True,
            'item_count': item_count,
            'total_amount': total_amount,
            'formatted_total': f"${total_amount:.2f}"
        })
        
    except Exception as e:
        logger.error(f"获取订单摘要错误: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


@csrf_exempt
def add_to_cart(request):
    """添加商品到购物车"""
    if request.method == 'POST':
        try:
            product_id = request.POST.get('product_id')
            quantity = int(request.POST.get('quantity', 1))
            
            product = get_object_or_404(CoffeeItem, id=product_id)
            
            # 获取当前购物车
            cart = Cart(request)
            
            # 添加到购物车
            cart.add(
                product=product,
                product_type='coffee',
                quantity=quantity,
                cup_level=request.POST.get('cup_level', 'Medium'),
                milk_level=request.POST.get('milk_level', 'Medium')
            )
            
            # 保存购物车数据到session
            cart_data = {
                'items': cart.cart,
                'total_price': str(cart.get_total_price())
            }
            request.session['pending_order'] = cart_data
            request.session.modified = True
            
            messages.success(request, f"已添加 {product.name} 到购物车")
            
            return JsonResponse({
                'success': True,
                'cart_count': len(cart),
                'message': '商品已添加到购物车'
            })
            
        except Exception as e:
            logger.error(f"添加到购物车错误: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': f'添加失败: {str(e)}'
            }, status=500)
    
    return JsonResponse({
        'success': False,
        'message': '无效的请求方法'
    }, status=400)


def remove_from_cart(request):
    """从购物车移除商品"""
    if request.method == 'POST':
        try:
            product_id = request.POST.get('product_id')
            
            cart = Cart(request)
            
            # 从购物车移除商品
            cart.remove(product_id)
            
            # 更新session数据
            cart_data = {
                'items': cart.cart,
                'total_price': str(cart.get_total_price())
            }
            request.session['pending_order'] = cart_data
            request.session.modified = True
            
            messages.success(request, "已从购物车移除商品")
            
            return JsonResponse({
                'success': True,
                'cart_count': len(cart),
                'message': '商品已从购物车移除'
            })
            
        except Exception as e:
            logger.error(f"从购物车移除错误: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': f'移除失败: {str(e)}'
            }, status=500)
    
    return JsonResponse({
        'success': False,
        'message': '无效的请求方法'
    }, status=400)