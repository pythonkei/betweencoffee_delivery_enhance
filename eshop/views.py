# eshop/views.py:
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_GET, require_POST
from django.views import View
from django.utils import timezone
from django.db.models import Q
from .models import CoffeeItem, BeanItem, OrderModel
from cart.cart import Cart
from django.core.exceptions import PermissionDenied
from decimal import Decimal

from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.urls import reverse

from .alipay_utils import create_alipay_payment, verify_alipay_notification, debug_verification
from urllib.parse import unquote
from .paypal_utils import create_paypal_payment, capture_paypal_payment
from .fps_utils import create_fps_payment, verify_fps_payment
from .sms_utils import send_sms_notification

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from .time_utils import get_hong_kong_time, format_time_for_display
from phonenumbers.phonenumberutil import NumberParseException

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

import phonenumbers
import json
import time
import requests
import logging
logger = logging.getLogger(__name__)



# Parses the JSON data and renders it in a template for staff
def order_detail(request, order_id):
    order = get_object_or_404(OrderModel, id=order_id)
    
    # Verify order belongs to user (if authenticated)
    if request.user.is_authenticated and order.user != request.user:
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied("You don't have permission to view this order")
    
    items = order.get_items()  # Parse JSON data
    context = {
        'order': order,
        'items': items,
    }
    return render(request, 'eshop/order_detail.html', context)


"""
Validate and format phone number to E.164 format
Returns formatted phone if valid, None if invalid
"""
def validate_and_format_phone(phone):
    try:
        # Add Hong Kong country code if missing
        if not phone.startswith('+'):
            phone = f"+852{phone}"
        
        # Parse and validate
        parsed_phone = phonenumbers.parse(phone, "HK")
        if phonenumbers.is_valid_number(parsed_phone):
            return phonenumbers.format_number(
                parsed_phone, 
                phonenumbers.PhoneNumberFormat.E164
            )
        return None
    except NumberParseException:
        return None



@method_decorator(login_required, name='dispatch')
class OrderConfirm(View):
    """訂單確認與付款頁面"""
    template_name = 'eshop/order_confirm.html'
    
    def get(self, request, *args, **kwargs):
        # 檢查是否有快速訂單數據
        quick_order_data = request.session.get('quick_order_data')
        
        if quick_order_data:
            # 使用快速訂單數據
            items = quick_order_data['items']
            total_price = quick_order_data['total_price']
            initial_data = {
                'name': quick_order_data.get('name', ''),
                'phone': quick_order_data.get('phone', ''),
                'email': quick_order_data.get('email', ''),
                'pickup_time': quick_order_data.get('pickup_time', '5 分鐘後'),
            }
            is_quick_order = True
        else:
            # 原有邏輯：從購物車取得數據
            if not request.session.get('pending_order'):
                messages.error(request, "没有待处理的订单")
                return redirect('cart:cart_detail')
                
            cart_data = request.session['pending_order']
            items = []
            
            # 準備商品資訊
            for item_key, item_data in cart_data.get('items', {}).items():
                parts = item_key.split('_')
                item_type = parts[0]
                id = parts[1]

                try:
                    if item_type == 'coffee':
                        item = CoffeeItem.objects.get(id=id)
                    elif item_type == 'bean':
                        item = BeanItem.objects.get(id=id)
                    else:
                        continue
                        
                    items.append({
                        'name': item.name,
                        'quantity': item_data['quantity'],
                        'total_price': Decimal(item_data['price']) * item_data['quantity'],
                        'type': item_type,
                        'image': item_data['image'],
                        'cup_level': item_data.get('cup_level'),
                        'milk_level': item_data.get('milk_level'),
                        'grinding_level': item_data.get('grinding_level'),
                        'weight': item_data.get('weight'),
                    })
                except (CoffeeItem.DoesNotExist, BeanItem.DoesNotExist):
                    continue

            total_price = cart_data.get('total_price', '0.00')
            initial_data = {}
            is_quick_order = False

        context = {
            'items': items,
            'total_price': total_price,
            'user': request.user,
            'initial_data': initial_data,
            'is_quick_order': is_quick_order
        }
        return render(request, self.template_name, context)


    def post(self, request, *args, **kwargs):
        # 檢查是否有快速訂單數據
        quick_order_data = request.session.get('quick_order_data')
        
        if quick_order_data:
            # 處理快速訂單
            items = quick_order_data['items']
            total_price = quick_order_data['total_price']
            is_quick_order = True
            
            # 預先填充的數據
            initial_data = {
                'name': quick_order_data.get('name', ''),
                'phone': quick_order_data.get('phone', ''),
                'email': quick_order_data.get('email', ''),
                'pickup_time': quick_order_data.get('pickup_time', '5 分鐘後'),
            }
        else:
            # 原有逻辑：从购物车获取数据
            cart_data = request.session.get('pending_order', {})
            if not cart_data:
                messages.error(request, "您的購物車是空的")
                return redirect('cart:cart_detail')
                
            items = []
            # 准备订单项
            for item_key, item_data in cart_data.get('items', {}).items():
                parts = item_key.split('_')
                item_type = parts[0]
                id = parts[1]

                items.append({
                    'type': item_type,
                    'id': int(id),
                    'name': item_data['name'],
                    'price': item_data['price'],
                    'quantity': item_data['quantity'],
                    'cup_level': item_data.get('cup_level'),
                    'milk_level': item_data.get('milk_level'),
                    'grinding_level': item_data.get('grinding_level'),
                    'weight': item_data.get('weight'),
                })

            total_price = Decimal(cart_data.get('total_price', 0))
            is_quick_order = False
            
        # 驗證電話號碼
        phone = request.POST.get('phone', '')
        formatted_phone = validate_and_format_phone(phone)
        if not formatted_phone:
            messages.error(request, "請輸入有效的香港電話號碼")
            # 重新渲染頁面，保留已填寫的數據
            context = {
                'items': items,
                'total_price': total_price,
                'user': request.user,
                'initial_data': {
                    'name': request.POST.get('name', ''),
                    'phone': phone,
                    'email': request.POST.get('email', ''),
                    'pickup_time': request.POST.get('pickup_time', '5 分鐘後'),
                },
                'is_quick_order': is_quick_order
            }
            return render(request, self.template_name, context)
            
        try:
            # 建立訂單
            order = OrderModel.objects.create(
                user=request.user,
                total_price=total_price,
                name=request.POST.get('name', ''),
                email=request.POST.get('email', ''),
                phone=formatted_phone,
                items=items,
                order_type='quick' if is_quick_order else 'normal',
                is_quick_order=is_quick_order,
                pickup_time=request.POST.get('pickup_time', '5 分鐘後'),
                status='pending',
                payment_method=request.POST.get('payment_method', 'alipay')
            )
            # 注意：estimated_ready_time 現在在模型的 save() 方法中自動計算
            # 所以不需要在這裡手動設定
            # 產生二維碼
            order.qr_code = order.generate_qr_code_data()
            order.save()  # 再次儲存以更新二維碼
            
            # 清除session數據
            if 'pending_order' in request.session:
                del request.session['pending_order']
            if 'quick_order_data' in request.session:
                del request.session['quick_order_data']
            request.session.modified = True

            # 根據支付方式跳轉
            payment_method = request.POST.get('payment_method')
            return self.handle_payment(request, order, payment_method)

        except Exception as e:
            print("Order creation failed:", str(e))
            messages.error(request, f"建立訂單時發生錯誤: {str(e)}")
            return redirect('cart:cart_detail')



    def handle_payment(self, request, order, payment_method):
        """統一處理付款 - 修复版本"""
        if payment_method == 'alipay':
            return redirect('eshop:alipay_payment', order_id=order.id)
        elif payment_method == 'paypal':
            paypal_url = create_paypal_payment(order, request)
            if paypal_url:
                request.session['pending_paypal_order_id'] = order.id
                request.session.modified = True
                return redirect(paypal_url)
            else:
                messages.error(request, "建立PayPal付款失敗，請稍後重試或選擇其他付款方式")
                return redirect('eshop:order_confirm')
        elif payment_method == 'fps':
            # 直接处理FPS支付，而不是调用另一个方法
            return self.handle_fps_payment(request, order)
        elif payment_method == 'cash':
            # 直接处理现金支付，而不是调用另一个方法
            return self.handle_cash_payment(request, order)
        else:
            messages.error(request, "請選擇有效的付款方式")
            return redirect('eshop:order_confirm')

    def handle_fps_payment(self, request, order):
        """處理FPS轉數快支付 - 修复版本"""
        try:
            # 創建FPS支付
            fps_result = create_fps_payment(order, request)
            
            if fps_result['success']:
                # 保存FPS相關信息
                order.fps_qr_code = fps_result['qr_code']
                order.fps_reference = fps_result['reference']
                order.save()
                
                # 設置session以便在確認頁面使用
                request.session['pending_fps_order_id'] = order.id
                request.session.modified = True
                
                # 重定向到FPS支付頁面 - 确保这里返回重定向
                return redirect('eshop:fps_payment', order_id=order.id)
            else:
                messages.error(request, f"FPS支付創建失敗: {fps_result.get('error', '未知錯誤')}")
                return redirect('eshop:order_confirm')
                
        except Exception as e:
            logger.error(f"FPS支付處理失敗: {str(e)}")
            messages.error(request, "FPS支付處理失敗，請稍後重試")
            return redirect('eshop:order_confirm')

    def handle_cash_payment(self, request, order):
        """處理現金支付 - 修复版本"""
        try:
            # 現金支付直接標記為待確認
            order.status = 'pending'
            order.is_paid = False
            order.save()
            
            # 設置session
            request.session['pending_cash_order_id'] = order.id
            request.session.modified = True
            
            # 重定向到現金支付確認頁面 - 确保这里返回重定向
            return redirect('eshop:cash_payment', order_id=order.id)
            
        except Exception as e:
            logger.error(f"現金支付處理失敗: {str(e)}")
            messages.error(request, "現金支付處理失敗，請稍後重試")
            return redirect('eshop:order_confirm')


    # 發送通知
    def send_order_notification(self, order, status):
        """發送訂單狀態通知"""
        from django.core.mail import send_mail
        from django.conf import settings
        
        status_messages = {
            'created': '您的訂單已創建，正在等待處理',
            'preparing': '您的訂單已開始製作',
            'ready': '您的訂單已就緒，請前來取餐',
            'completed': '您的訂單已完成'
        }
        
        subject = f"Between Coffee訂單狀態更新 - 訂單 #{order.id}"
        message = f"""
        尊敬的{order.name}：

        您的訂單狀態已更新：{status_messages.get(status, '狀態更新')}
        
        訂單詳情：
        - 訂單號碼: #{order.id}
        - 取餐碼: {order.pickup_code}
        - 總金額: HK${order.total_price}
        - 預計就緒時間: {order.estimated_ready_time.strftime('%Y-%m-%d %H:%M')}
        
        感謝您選擇Between Coffee！
        """
        
        # 发送邮件通知
        if order.email:
            try:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [order.email],
                    fail_silently=False,
                )
            except Exception as e:
                print(f"郵件發送失敗: {str(e)}")
    
    # 这里可以添加短信通知逻辑（需要接入短信服务商API）
    # if order.phone:
    #     self.send_sms_notification(order.phone, message)



# Quick Order - index, 使用 session 存储快速订单数据逻辑
@require_POST
def quick_order(request):
    if request.method == 'POST':
        # 获取表单数据
        name = request.POST.get('name')
        phone = request.POST.get('phone')
        email = request.POST.get('email', '')
        pickup_time = request.POST.get('pickup_time')
        cup_size = request.POST.get('cup_size')
        
        # 创建快速订单项目（WakeMeup 咖啡）
        quick_order_item = {
            'type': 'coffee',
            'id': 1,  # 假设 WakeMeup 咖啡的 ID 是 1
            'name': 'WakeMeup 醒神配方',
            'price': 38.0,  # 假设价格
            'quantity': 1,
            'cup_level': cup_size,
            'milk_level': 'Medium',
            'image': '/static/images/menu-1.png',
            'total_price': 38.0
        }
        
        # 将订单数据存入 session，以便在 order_confirm 中使用
        request.session['quick_order_data'] = {
            'items': [quick_order_item],
            'total_price': 38.0,
            'name': name,
            'phone': phone,
            'email': email,
            'pickup_time': pickup_time,
            'is_quick_order': True
        }
        
        # 重定向到订单确认页面
        return redirect('eshop:order_confirm')
    
    # 如果是 GET 请求，重定向回首页
    return redirect('index')


# Auto gen qrcode for Alipay
import qrcode
import qrcode.image.svg
from io import BytesIO
import base64


'''
# 支付宝支付视图Checking, Use this temp test view for Direct key testing
http://localhost:8080/eshop/test_alipay_verification/ - 應該顯示驗證成功
http://localhost:8080/eshop/check_alipay_keys/ - 應該顯示金鑰格式正確
http://localhost:8080/eshop/check_key_match/- 兩個公鑰應該分別符合支付寶的配置
'''

# 支付寶支付視圖
@login_required
def alipay_payment(request, order_id):
    """支付宝支付视图"""
    try:
        order = get_object_or_404(OrderModel, id=order_id, user=request.user)
        
        # 创建支付宝支付URL
        payment_url = create_alipay_payment(order, request)
        
        # 重定向到支付宝支付页面
        return redirect(payment_url)
        
    except Exception as e:
        logger.error(f"Alipay payment error: {str(e)}")
        # 添加错误消息但停留在当前页面
        messages.error(request, f"支付系统错误: {str(e)}")
        
        # 准备订单项用于显示
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
            except KeyError:
                continue

        context = {
            'order': order,
            'items': items,
            'total_price': order.total_price,
            'show_alipay_option': True,
            'alipay_error': str(e)  # 传递错误信息到模板
        }
        return render(request, 'eshop/order_payment_confirmation.html', context)


def prepare_payment_error_context(order):
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
        except KeyError:
            continue

    return {
        'order': order,
        'items': items,
        'total_price': order.total_price,
        'show_alipay_option': True,
        'alipay_error': str(e)
    }



# 添加FPS支付视图
@login_required
def fps_payment(request, order_id):
    """FPS支付页面"""
    try:
        order = get_object_or_404(OrderModel, id=order_id, user=request.user)
        
        context = {
            'order': order,
            'fps_qr_code': order.fps_qr_code,
            'fps_reference': order.fps_reference,
            'total_price': order.total_price
        }
        
        return render(request, 'eshop/fps_payment.html', context)
        
    except Exception as e:
        logger.error(f"FPS支付頁面加載失敗: {str(e)}")
        messages.error(request, "加載支付頁面失敗")
        return redirect('eshop:order_confirm')



# cash view
@login_required
def cash_payment(request, order_id):
    """现金支付确认页面"""
    try:
        order = get_object_or_404(OrderModel, id=order_id, user=request.user)
        
        # 计算订单类型和制作时间
        items = order.get_items_with_chinese_options()
        has_coffee = any(item.get('type') == 'coffee' for item in order.get_items())
        has_beans = any(item.get('type') == 'bean' for item in order.get_items())
        
        context = {
            'order': order,
            'items': items,
            'total_price': order.total_price,
            'has_coffee': has_coffee,
            'has_beans': has_beans,
            'preparation_time_display': order.get_preparation_time_display(),
            'order_type_display': order.get_order_type_display(),
            'should_show_preparation_time': order.should_show_preparation_time(),
        }
        
        return render(request, 'eshop/cash_payment.html', context)
        
    except Exception as e:
        logger.error(f"現金支付頁面加載失敗: {str(e)}")
        messages.error(request, "加載支付頁面失敗")
        return redirect('eshop:order_confirm')




# 支付宝回调处理 - 简化版本
@csrf_exempt
def alipay_callback(request):
    """支付宝同步回调处理 - 简化版本"""
    logger.info("收到支付宝回调请求")
    
    try:
        # 解析数据
        data = {}
        for key, value in request.GET.items():
            data[key] = unquote(value)
        
        # 检查必要参数
        required_params = ['out_trade_no', 'total_amount', 'sign']
        for param in required_params:
            if param not in data:
                logger.error(f"缺少必要参数: {param}")
                return redirect(reverse('eshop:order_payment_confirmation') + '?payment_status=error')
        
        # 验证签名
        if not verify_alipay_notification(data):
            logger.error("支付宝签名验证失败")
            messages.error(request, "支付验证失败")
            return redirect(reverse('eshop:order_payment_confirmation') + '?payment_status=error')
        
        # 处理支付成功
        out_trade_no = data.get('out_trade_no')
        return handle_payment_success(request, out_trade_no)
            
    except Exception as e:
        logger.error(f"支付宝回调处理异常: {str(e)}")
        messages.error(request, "支付处理异常")
        return redirect(reverse('eshop:order_payment_confirmation') + '?payment_status=error')



# PayPal回调处理 - 简化版本
def paypal_callback(request):
    """PayPal支付回调处理 - 简化版本"""
    try:
        # 获取订单ID和支付ID
        order_id = request.session.get('pending_paypal_order_id')
        payment_id = request.GET.get('token')
        
        if not order_id:
            messages.error(request, "支付会话已过期")
            return redirect('cart:cart_detail')
        
        # 捕获支付
        if not capture_paypal_payment(payment_id):
            messages.error(request, "支付失败")
            return redirect('eshop:order_confirm')
        
        # 处理支付成功
        return handle_payment_success(request, order_id)
            
    except Exception as e:
        logger.error(f"PayPal回调处理异常: {str(e)}")
        messages.error(request, "支付处理异常")
        return redirect('eshop:order_confirm')


# 统一支付成功处理函数
def handle_payment_success(request, order_id):
    """统一处理支付成功逻辑"""
    try:
        order = OrderModel.objects.get(id=order_id)
        
        # 检查订单是否已经处理过
        if order.is_paid:
            logger.info(f"订单 {order_id} 已经支付过，跳过处理")
            return redirect_to_confirmation(order_id)
        
        # 更新订单状态
        order.is_paid = True
        order.status = 'preparing'
        order.estimated_ready_time = order.calculate_estimated_ready_time()
        order.save()
        
        logger.info(f"订单 {order_id} 支付成功，预计就绪时间: {order.estimated_ready_time}")
        
        # 支付成功后清理
        clear_payment_session(request, order_id)
        
        # 发送通知
        send_payment_notifications(order)
        
        return redirect_to_confirmation(order_id)
        
    except OrderModel.DoesNotExist:
        logger.error(f"订单不存在: {order_id}")
        return redirect(reverse('eshop:order_payment_confirmation') + '?payment_status=unknown')
    except Exception as e:
        logger.error(f"支付成功处理异常: {str(e)}")
        messages.error(request, "支付处理异常")
        return redirect(reverse('eshop:order_payment_confirmation') + '?payment_status=error')



# 重定向到确认页面
def redirect_to_confirmation(order_id):
    """重定向到支付确认页面"""
    return redirect(reverse('eshop:order_payment_confirmation') + f'?order_id={order_id}')



# 清理支付会话
def clear_payment_session(request, order_id):
    """清理支付相关的session数据"""
    # 清空购物车
    cart = Cart(request)
    cart.clear()
    
    # 保存订单ID到session
    request.session['last_order_id'] = order_id
    
    # 清除PayPal临时数据
    if 'pending_paypal_order_id' in request.session:
        del request.session['pending_paypal_order_id']
    
    request.session.modified = True
    logger.info("支付会话数据已清理")


# 发送支付通知
def send_payment_notifications(order):
    """发送支付成功通知"""
    # 发送短信通知
    if order.phone and order.user and order.user.is_authenticated:
        try:
            send_sms_notification(order)
            logger.info(f"已发送短信通知到 {order.phone}")
        except Exception as e:
            logger.error(f"发送短信通知失败: {str(e)}")
    
    # 这里可以添加邮件通知等其他通知方式
    # if order.email:
    # send_email_notification(order)


@csrf_exempt
def alipay_notify(request):
    """支付宝异步通知处理 - 简化版本"""
    if request.method == 'POST':
        # 解析数据
        data = {}
        for key, value in request.POST.items():
            data[key] = unquote(value)
        
        # 验证签名
        if not verify_alipay_notification(data):
            logger.error("支付宝异步通知签名验证失败")
            return HttpResponse("签名验证失败", status=400)
        
        # 处理支付成功
        out_trade_no = data.get('out_trade_no')
        trade_status = data.get('trade_status')
        
        if trade_status == 'TRADE_SUCCESS':
            try:
                order = OrderModel.objects.get(id=out_trade_no)
                if not order.is_paid:
                    order.is_paid = True
                    order.save()
                    logger.info(f"支付宝异步通知: 订单 {out_trade_no} 支付状态已更新")
                return HttpResponse("success")
            except OrderModel.DoesNotExist:
                return HttpResponse("订单不存在", status=400)
    
    return HttpResponse("仅支持POST请求", status=400)



# PayPal回调处理函数
@csrf_exempt
def paypal_callback(request):
    """PayPal支付回调处理"""
    try:
        # 取得訂單ID和支付ID
        order_id = request.session.get('pending_paypal_order_id')
        payment_id = request.GET.get('token')
        
        if not order_id:
            messages.error(request, "支付会话已过期，请重新下单")
            return redirect('cart:cart_detail')
        
        # 獲取訂單
        order = OrderModel.objects.get(id=order_id)
        
        # 如果訂單已經支付，直接跳到成功頁面
        if order.is_paid:
            return redirect(reverse('eshop:order_payment_confirmation') + f'?order_id={order.id}')
        
        # Capture 支付
        if capture_paypal_payment(payment_id):
            # 支付成功
            order.is_paid = True
            order.status = 'preparing'  # 设置状态为制作中
            
            # 付款成功後才計算預計就緒時間
            order.estimated_ready_time = order.calculate_estimated_ready_time()
            order.save()
            
            # 清空購物車
            cart = Cart(request)
            cart.clear()
            
            # 傳簡訊通知
            if order.phone and order.user and order.user.is_authenticated:
                try:
                    send_sms_notification(order)
                    logger.info(f"已发送短信通知到 {order.phone}")
                except Exception as e:
                    logger.error(f"发送短信通知失败: {str(e)}")
            
            # 清除session中的暫存數據
            if 'pending_paypal_order_id' in request.session:
                del request.session['pending_paypal_order_id']
            request.session.modified = True
            
            # 儲存訂單ID到session，用於確認頁面
            request.session['last_order_id'] = order.id
            request.session.modified = True
            
            # 重定向到付款成功頁面
            return redirect(reverse('eshop:order_payment_confirmation') + f'?order_id={order.id}')
        else:
            # 支付失敗
            messages.error(request, "支付失败，请稍后重试或选择其他支付方式")
            return redirect('eshop:order_confirm')
            
    except OrderModel.DoesNotExist:
        messages.error(request, "订单不存在")
        return redirect('cart:cart_detail')
    except Exception as e:
        logger.error(f"PayPal回调处理异常: {str(e)}")
        messages.error(request, "支付处理异常，请联系客服")
        return redirect('eshop:order_confirm')



# 訂單付款 -> 顯示基本傳遞商品資訊 -> 確認頁面
class OrderPaymentConfirmation(View):
    def get(self, request, *args, **kwargs):
        # 从session或URL参数中获取订单ID
        order_id = request.session.get('last_order_id') or request.GET.get('order_id')
        
        if order_id:
            try:
                order = OrderModel.objects.get(id=order_id)
                items = order.get_items_with_chinese_options()
                
                # 使用 OrderModel 的方法来判断订单类型
                order_items = order.get_items()
                has_coffee = any(item.get('type') == 'coffee' for item in order_items)
                has_beans = any(item.get('type') == 'bean' for item in order_items)
                
                # 设置订单类型标志
                is_beans_only = has_beans and not has_coffee
                is_coffee_only = has_coffee and not has_beans
                is_mixed_order = has_coffee and has_beans
                
                # 对于纯咖啡豆订单，不需要预计时间
                if is_beans_only:
                    # 确保状态直接设置为就绪
                    if order.status in ['pending', 'preparing']:
                        order.status = 'ready'
                        order.save()
                
                # 使用統一的時間處理方法
                context = {
                    'order': order,
                    'items': items,
                    'payment_status': 'paid' if order.is_paid else 'pending',
                    'remaining_minutes': order.get_remaining_minutes(),
                    'is_ready': order.is_ready(),
                    'estimated_time': order.get_display_time(),  # 使用统一方法
                    # 新增订单类型标志
                    'is_beans_only': is_beans_only,
                    'is_coffee_only': is_coffee_only,
                    'is_mixed_order': is_mixed_order,
                    'has_coffee': has_coffee,
                    'has_beans': has_beans,
                    # 新增制作时间显示
                    'preparation_time_display': order.get_preparation_time_display(),
                    'order_type_display': order.get_order_type_display(),
                }
                return render(request, 'eshop/order_payment_confirmation.html', context)
            except OrderModel.DoesNotExist:
                pass
        
        # 如果找不到訂單，顯示基本確認頁面
        context = {'payment_status': 'unknown'}
        return render(request, 'eshop/order_payment_confirmation.html', context)




# 確保倒數正確返回
class CountdownAPI(View):
    """倒數計時API"""
    def get(self, request, order_id):
        try:
            order = OrderModel.objects.get(id=order_id)
            
            # 验证订单属于当前用户
            if request.user.is_authenticated and order.user != request.user:
                return JsonResponse({'error': '無權存取此訂單'}, status=403)
            
            if not order.is_paid:
                return JsonResponse({'error': '訂單未支付'}, status=400)
            
            # 强制更新状态（确保状态最新）
            order.update_status_based_on_time()
            
            # 重新获取更新后的订单
            order.refresh_from_db()
            
            remaining_minutes = order.get_remaining_minutes()
            is_ready = order.is_ready()

            response_data = {
                'order_id': order.id,
                'remaining_minutes': remaining_minutes,
                'is_ready': is_ready,
                'status': order.status,
                'current_time': get_hong_kong_time().strftime('%H:%M:%S'),
                'estimated_time': order.get_display_time(),
                'debug': {
                    'estimated_ready_time': order.estimated_ready_time.isoformat() if order.estimated_ready_time else None,
                    'now': get_hong_kong_time().isoformat()
                }
            }
            
            logger.info(f"CountdownAPI 傳回數據: {response_data}")
            
            return JsonResponse(response_data)
            
        except OrderModel.DoesNotExist:
            return JsonResponse({'error': '訂單不存在'}, status=404)
        except Exception as e:
            logger.error(f"倒數API錯誤: {str(e)}")
            return JsonResponse({'error': '伺服器錯誤'}, status=500)


@login_required
@require_GET
def check_order_status(request, order_id):
    """检查订单支付状态API"""
    try:
        order = OrderModel.objects.get(id=order_id, user=request.user)
        return JsonResponse({
            'order_id': order.id,
            'is_paid': order.is_paid,
            'status': 'paid' if order.is_paid else 'pending',
            'total_price': str(order.total_price)
        })
    except OrderModel.DoesNotExist:
        return JsonResponse({'error': '订单不存在'}, status=404)



def send_order_status_update(order_id, status, message):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f'order_{order_id}',
        {
            'type': 'order_notification',
            'message': message,
            'status': status
        }
    )


# Then add this function in views.py
def check_alipay_keys(request):
    """Check if Alipay keys are properly configured and formatted"""
    try:
        # Load private key to check if it's valid
        private_key = serialization.load_pem_private_key(
            settings.ALIPAY_APP_PRIVATE_KEY.encode(),
            password=None,
            backend=default_backend()
        )
        
        # Load public key to check if it's valid
        public_key = serialization.load_pem_public_key(
            settings.ALIPAY_PUBLIC_KEY.encode(),
            backend=default_backend()
        )
        
        # If we get here, both keys are properly formatted
        return HttpResponse("✅ Keys are properly formatted and valid")
        
    except Exception as e:
        return HttpResponse(f"❌ Key error: {str(e)}")


@csrf_exempt
def check_key_match(request):
    """检查应用公钥是否与支付宝配置匹配"""
    try:
        from cryptography.hazmat.backends import default_backend
        from cryptography.hazmat.primitives import serialization
        
        # 从私钥生成公钥
        private_key = serialization.load_pem_private_key(
            settings.ALIPAY_APP_PRIVATE_KEY.encode(),
            password=None,
            backend=default_backend()
        )
        
        # 获取公钥数据
        public_key = private_key.public_key()
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode()
        
        response_text = "=== 密钥匹配检查 ===\n\n"
        response_text += "从私钥生成的公钥:\n"
        response_text += public_pem + "\n"
        
        response_text += "当前配置的支付宝公钥:\n"
        response_text += settings.ALIPAY_PUBLIC_KEY + "\n"
        
        response_text += "💡 提示: 上面第一个公钥应该与支付宝沙箱中'应用公钥'一致\n"
        response_text += "💡 提示: 上面第二个公钥应该与支付宝沙箱中'支付宝公钥'一致"
        
        return HttpResponse(response_text, content_type="text/plain")
        
    except Exception as e:
        return HttpResponse(f"检查失败: {str(e)}", content_type="text/plain")


# 视图for检查实际的回调数据
@csrf_exempt
def debug_real_callback(request):
    """调试实际回调数据的签名验证"""
    if request.method == 'GET':
        # 获取实际的回调数据
        data = {}
        for key, value in request.GET.items():
            data[key] = unquote(value)
        
        logger.debug("实际回调数据:")
        for key, value in data.items():
            logger.debug(f"  {key}: {repr(value)}")
        
        # 进行验证
        result = verify_alipay_notification(data)
        
        response_text = f"实际回调验证结果: {result}\n\n"
        response_text += f"回调参数: {data}\n\n"
        
        if not result:
            response_text += "❌ 实际回调签名验证失败\n"
            response_text += "请检查:\n"
            response_text += "1. 支付宝公钥是否正确配置\n"
            response_text += "2. 应用公钥是否与支付宝沙箱中配置的一致\n"
        else:
            response_text += "✅ 实际回调签名验证成功"
        
        return HttpResponse(response_text, content_type="text/plain")



# SMS inform
@login_required
def test_twilio_config(request):
    """测试Twilio配置的视图"""
    from twilio.rest import Client
    from twilio.base.exceptions import TwilioRestException
    
    context = {}

    # 详细打印配置信息
    print("=== Twilio 配置详情 ===")
    print(f"Account SID: {settings.TWILIO_ACCOUNT_SID}")
    print(f"Auth Token 长度: {len(settings.TWILIO_AUTH_TOKEN)}")
    print(f"Phone Number: {settings.TWILIO_PHONE_NUMBER}")
    
    # 检查配置是否存在
    if not all([hasattr(settings, 'TWILIO_ACCOUNT_SID'), 
               hasattr(settings, 'TWILIO_AUTH_TOKEN'), 
               hasattr(settings, 'TWILIO_PHONE_NUMBER')]):
        context['error'] = "Twilio配置不完整"
        return render(request, 'eshop/twilio_test.html', context)
    
    try:
        # 初始化客户端
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        
        # 尝试获取号码信息
        incoming_phone_numbers = client.incoming_phone_numbers.list()
        
        # 检查配置的号码是否存在
        configured_number = settings.TWILIO_PHONE_NUMBER
        number_exists = any(num.phone_number == configured_number for num in incoming_phone_numbers)
        
        context['configured_number'] = configured_number
        context['number_exists'] = number_exists
        context['account_numbers'] = [num.phone_number for num in incoming_phone_numbers]
        
        if number_exists:
            context['success'] = f"号码 {configured_number} 存在于你的Twilio账户中"
        else:
            context['error'] = f"号码 {configured_number} 不存在于你的Twilio账户中"
            
    except TwilioRestException as e:
        context['error'] = f"Twilio API错误: {e.code} - {e.msg}"
    except Exception as e:
        context['error'] = f"意外错误: {str(e)}"
    
    return render(request, 'eshop/twilio_test.html', context)



'''
@csrf_exempt
def test_alipay_verification(request):
    """测试支付宝签名验证 - 使用最新数据"""
    # 使用最新的回调数据
    test_data = {
        'charset': 'utf-8',
        'out_trade_no': '297',
        'method': 'alipay.trade.page.pay.return',
        'total_amount': '108.00',
        'sign': 'XsWn3gKFbahGLGeyd6yLSEjHnSFjMGuAxqhIb4qWog2pKEcrPRvcK5KNlXtJK2zzmd4w8Ntvw6LH0OuhF9fAo3vcXD4EFGVNJv35U7fD32h76oO4Vby9vxm0XMXe8svry1PksqD2AGp3ljVUHrIEkR+JLwU47YthzzmBJW0We3XfqlvZWMlnLKPMbc3R1gNQcm0+RaCgwvXPb+jKyFu8/GV37lu2rHzUyaecdO9Bcv7wBnVPGuQRSL/osxdva2BYiABIS7EcjISaF8eRqxWm1yzeNGqxKKD2hoPWfiIidMPZMVp2HLdoJnJ68UInVxjyc7DyaRgn/gPcT9uYOoEUww==',
        'trade_no': '2025082322001461350507844628',
        'auth_app_id': '9021000151625966',
        'version': '1.0',
        'app_id': '9021000151625966',
        'sign_type': 'RSA2',
        'seller_id': '2088721076137080',
        'timestamp': '2025-08-23+22:19:00'
    }
    
    logger.debug("开始测试签名验证...")
    result = debug_verification(test_data)
    
    response_text = f"验证结果: {result}\n\n"
    
    if not result:
        response_text += "❌ 签名验证失败\n"
        response_text += "可能的原因:\n"
        response_text += "1. 支付宝公钥不正确\n"
        response_text += "2. 应用公钥与私钥不匹配\n"
        response_text += "3. 请检查支付宝沙箱中的密钥配置\n"
    else:
        response_text += "✅ 签名验证成功"
    
    return HttpResponse(response_text, content_type="text/plain")
'''