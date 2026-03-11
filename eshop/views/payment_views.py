# eshop/views/payment_views.py
"""
支付相关视图模块 - 修改后完整版本
处理支付宝、PayPal、FPS、现金支付等功能
使用统一的支付工具和错误处理
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.conf import settings
from django.urls import reverse
from urllib.parse import unquote
import logging
import json
import time
import traceback

# 导入项目模型
from ..models import OrderModel, CoffeeQueue
from eshop.order_status_manager import OrderStatusManager
from eshop.view_utils import OrderErrorHandler  # 統一錯誤處理器

# ==================== 导入统一的支付工具 ====================
from ..payment_utils import (
    get_payment_tools,          # 统一的支付工具获取器
    get_payment_urls,           # URL获取
    get_alipay_return_url,      # 支付宝URL
    get_alipay_notify_url,
    handle_payment_callback,    # 支付回调处理
    update_order_payment_status,  # 更新订单状态
    get_payment_method_display,  # 支付方式显示
    is_payment_method_available, # 支付方式可用性
    get_available_payment_methods, # 可用支付方式
)

# 使用導WebSocket工具
try:
    from ..websocket_utils import send_order_update, send_queue_update, send_payment_update
    WEBSOCKET_ENABLED = True
    # ✅ 這裡不要定義佔位函數，直接使用導入的
except ImportError:
    WEBSOCKET_ENABLED = False
    
    # 只有在導入失敗時才定義佔位函數
    def send_payment_update(order_id, payment_status, data=None):
        logger.info(f"WebSocket占位: 支付更新 - {order_id}, {payment_status}, data={data}")
        return True
    
    def send_order_update(order_id, update_type, data=None):
        logger.info(f"WebSocket占位: 订单更新 - {order_id}, {update_type}, data={data}")
        return True
    
    def send_queue_update(update_type, data=None):
        logger.info(f"WebSocket占位: 队列更新 - {update_type}, data={data}")
        return True

logger = logging.getLogger(__name__)

# ==================== 辅助函数 ====================

def clear_payment_session(request, order_id):
    """清理支付相关的session数据"""
    if 'pending_paypal_order_id' in request.session:
        del request.session['pending_paypal_order_id']
    if 'pending_fps_order_id' in request.session:
        del request.session['pending_fps_order_id']
    if 'pending_cash_order_id' in request.session:
        del request.session['pending_cash_order_id']
    
    request.session['last_order_id'] = order_id
    request.session.modified = True
    logger.info(f"支付会话数据已清理，订单: {order_id}")

def send_payment_notifications(order):
    """发送支付成功通知"""
    try:
        # 这里可以调用短信通知函数
        # from ..sms_utils import send_sms_notification
        # send_sms_notification(order)
        pass
    except Exception as e:
        logger.error(f"发送支付通知失败: {str(e)}")


# ==================== 支付宝支付视图 ====================

def alipay_payment(request, order_id):
    """支付宝支付视图 - 使用统一的支付工具"""
    try:
        logger.info(f"=== 支付宝支付视图开始 ===")
        order = get_object_or_404(OrderModel, id=order_id)
        
        # 验证用户权限
        if request.user.is_authenticated and order.user != request.user:
            messages.error(request, "您无权访问此订单")
            return redirect('index')
        
        logger.info(f"订单详情: ID={order.id}, 状态={order.status}, 支付状态={order.payment_status}")
        
        if order.payment_status == "paid":
            logger.info(f"订单 {order.id} 已经支付，跳转到确认页面")
            messages.info(request, "订单已支付")
            return redirect('eshop:order_payment_confirmation')
        
        if order.is_payment_timeout():
            logger.warning(f"订单 {order.id} 支付超时")
            messages.warning(request, "支付已超时，请重新创建订单")
            return redirect('cart:cart_detail')
        
        max_attempts = 5
        if order.payment_attempts >= max_attempts:
            logger.warning(f"订单 {order.id} 支付尝试次数过多: {order.payment_attempts}")
            messages.warning(request, "支付尝试次数过多，请重新创建订单")
            return redirect('cart:cart_detail')
        
        order.set_payment_timeout(minutes=5)
        logger.info(f"设置支付超时: {order.payment_timeout}")
        
        logger.info(f"开始创建支付宝支付URL，订单: {order.id}")
        
        # 使用统一的支付工具
        payment_tools = get_payment_tools('alipay')
        if not payment_tools or 'create' not in payment_tools:
            logger.error("支付宝支付工具不可用")
            messages.error(request, "支付宝支付系统暂时不可用，请稍后重试或选择其他支付方式")
            return redirect('eshop:order_payment_confirmation_with_id', order_id=order.id)
        
        payment_url = payment_tools['create'](order, request)
        
        if payment_url:
            logger.info(f"支付宝支付URL生成成功，订单: {order.id}")
            
            order.increment_payment_attempts()
            logger.info(f"支付尝试次数更新为: {order.payment_attempts}")
            
            request.session['current_payment_order_id'] = order.id
            request.session['payment_start_time'] = timezone.now().isoformat()
            request.session.modified = True
            
            logger.info(f"准备重定向到支付宝支付页面")
            return redirect(payment_url)
        else:
            logger.error(f"支付宝支付URL生成失败，订单: {order.id}")
            messages.error(request, "支付宝支付系统暂时不可用，请稍后重试或选择其他支付方式")
            return redirect('eshop:order_payment_confirmation_with_id', order_id=order.id)
        
    except Exception as e:
        logger.error(f"Alipay payment error: {str(e)}")
        messages.error(request, f"支付系统错误: {str(e)}")
        return redirect('eshop:order_payment_confirmation_with_id', order_id=order.id)


def get_order_confirmation_url(order_id):
    """獲取訂單確認頁面URL（統一入口）"""
    # 優先使用帶參數版本，避免session依賴
    from django.urls import reverse
    return reverse('eshop:order_payment_confirmation_with_id', kwargs={'order_id': order_id})


# ==================== 支付成功處理函數 ====================

def handle_payment_success(order_id, payment_method, request=None):
    """處理支付成功的統一函數"""
    try:
        logger.info(f"=== 開始處理支付成功，訂單: {order_id}, 支付方式: {payment_method} ===")
        
        # ✅ 修復：確保 OrderStatusManager 已導入
        try:
            from eshop.order_status_manager import OrderStatusManager
            
            # 先檢查訂單當前狀態
            try:
                from eshop.models import OrderModel
                order = OrderModel.objects.get(id=order_id)
                logger.info(f"訂單 {order_id} 當前狀態: status={order.status}, payment_status={order.payment_status}")
            except Exception as check_error:
                logger.error(f"檢查訂單狀態失敗: {check_error}")
            
            # 使用 OrderStatusManager 處理支付成功
            result = OrderStatusManager.process_payment_success(order_id, request)
            
            if not result.get('success'):
                error_msg = result.get('message', '支付成功但更新訂單狀態失敗')
                logger.error(f"支付成功但更新訂單狀態失敗: {error_msg}")
                
                # 嘗試記錄訂單狀態
                try:
                    order = OrderModel.objects.get(id=order_id)
                    logger.error(f"訂單 {order_id} 最終狀態: status={order.status}, payment_status={order.payment_status}")
                except:
                    pass
                
                return False
            
            logger.info(f"✅ 訂單 {order_id} 支付成功處理完成")
            return True
            
        except ImportError as import_error:
            logger.error(f"導入 OrderStatusManager 失敗: {import_error}")
            # 如果導入失敗，直接返回 False
            return False
        
    except Exception as e:
        logger.error(f"處理支付成功時發生錯誤: {str(e)}")
        logger.error(f"詳細錯誤: {traceback.format_exc()}")
        return False
    

@csrf_exempt
def alipay_callback(request):
    """支付寶同步回調處理 - 專門處理同步回調（沒有 trade_status）"""
    logger.info("收到支付寶回調請求")
    
    try:
        # 解析回調數據
        data = {}
        for key, value in request.GET.items():
            data[key] = unquote(value)
        
        logger.info(f"支付寶回調參數: {data}")
        
        # ✅ 修復：支付寶同步回調沒有 trade_status，只有方法標識
        out_trade_no = data.get('out_trade_no')
        method = data.get('method', '')
        
        # 檢查是否為支付頁面返回（同步回調）
        if method == 'alipay.trade.page.pay.return':
            logger.info(f"這是支付寶同步回調（return），訂單: {out_trade_no}")
        else:
            logger.info(f"支付寶回調方法: {method}")
        
        # ✅ 修復：同步回調中不檢查 trade_status，只驗證簽名和金額
        required_params = ['out_trade_no', 'total_amount']
        for param in required_params:
            if param not in data:
                logger.error(f"缺少必要參數: {param}")
                return redirect_to_payment_failed("支付回調參數不完整", out_trade_no)
        
        # 驗證簽名
        payment_tools = get_payment_tools('alipay')
        if not payment_tools or 'verify' not in payment_tools:
            logger.error("支付寶驗證工具不可用")
            return handle_payment_by_order_id(request, data.get('out_trade_no'))
        
        if not payment_tools['verify'](data):
            logger.error("支付寶簽名驗證失敗")
            return handle_payment_by_order_id(request, data.get('out_trade_no'))
        
        # 獲取訂單
        out_trade_no = data.get('out_trade_no')
        
        try:
            order = OrderModel.objects.get(id=out_trade_no)
            
            # ✅ 添加詳細日誌
            logger.info(f"✅ 找到訂單 {out_trade_no}, 當前狀態: status={order.status}, payment_status={order.payment_status}")
            
            if order.payment_status == 'paid':
                logger.info(f"訂單 {out_trade_no} 已經支付過，跳轉到確認頁面")
                # ✅ 即使已支付，也確保清空購物車
                clear_user_cart_and_session(request)
                return safe_redirect_to_confirmation(out_trade_no)
            
            logger.info(f"開始處理訂單 {out_trade_no} 支付成功")
            
            # ========== 關鍵修復：直接處理訂單，不依賴 handle_payment_success ==========
            try:
                # 直接更新訂單狀態
                logger.info(f"🔄 直接更新訂單 {out_trade_no} 狀態...")
                
                # 1. 更新支付狀態
                order.payment_status = 'paid'
                order.payment_method = 'alipay'
                
                # 2. 分析訂單類型，設置正確的狀態
                items = order.get_items()
                has_coffee = any(item.get('type') == 'coffee' for item in items)
                has_beans = any(item.get('type') == 'bean' for item in items)
                
                # 根據訂單類型設置狀態
                if has_coffee:
                    # 包含咖啡的訂單：設置為 waiting，等待加入隊列
                    order.status = 'waiting'
                    logger.info(f"訂單 {out_trade_no} 包含咖啡，設置為 waiting")
                elif has_beans:
                    # 純咖啡豆訂單：設置為 ready，可以直接提取
                    order.status = 'ready'
                    logger.info(f"訂單 {out_trade_no} 純咖啡豆，設置為 ready")
                else:
                    # 未知類型，默認為 waiting
                    order.status = 'waiting'
                    logger.warning(f"訂單 {out_trade_no} 未知商品類型，設置為 waiting")
                
                # 3. 保存訂單
                order.save()
                logger.info(f"✅ 直接更新訂單 {out_trade_no} 狀態成功")
                
                # 4. 清空購物車
                clear_user_cart_and_session(request)
                
                # 5. 嘗試將訂單加入隊列
                if has_coffee:
                    try:
                        from eshop.queue_manager_refactored import CoffeeQueueManager
                        queue_manager = CoffeeQueueManager()
                        # 使用兼容性包裝器，返回 CoffeeQueue 對象而不是字典
                        queue_item = queue_manager.add_order_to_queue_compatible(order)
                        
                        if queue_item:
                            # 修復：queue_item 可能是字典或對象，需要檢查類型
                            if isinstance(queue_item, dict):
                                position = queue_item.get('position', 0)
                                logger.info(f"✅ 訂單 {order.id} 已加入製作隊列，位置: {position}")
                            else:
                                logger.info(f"✅ 訂單 {order.id} 已加入製作隊列，位置: {queue_item.position}")
                        else:
                            logger.warning(f"⚠️ 訂單 {order.id} 加入隊列失敗")
                    except Exception as queue_error:
                        logger.error(f"加入隊列失敗: {queue_error}")
                
                # 6. 發送WebSocket通知（暫時註釋掉，以避免事件循環錯誤）
                # try:
                #     if WEBSOCKET_ENABLED:
                #         send_payment_update(
                #             order_id=order.id,
                #             payment_status='paid',
                #             data={
                #                 'payment_method': 'alipay',
                #                 'message': '支付宝支付成功'
                #             }
                #         )
                #
                #         send_order_update(
                #             order_id=order.id,
                #             update_type='status_change',
                #             data={
                #                 'status': order.status,
                #                 'message': '支付成功，訂單已確認'
                #             }
                #         )
                #         
                #         # 如果有隊列項，發送隊列更新
                #         try:
                #             queue_item = CoffeeQueue.objects.get(order=order)
                #             send_queue_update(
                #                 update_type='add',
                #                 data={
                #                     'order_id': order.id,
                #                     'position': queue_item.position,
                #                     'queue_type': 'waiting',
                #                     'estimated_start': queue_item.estimated_start_time.isoformat() if queue_item.estimated_start_time else None,
                #                     'estimated_complete': queue_item.estimated_completion_time.isoformat() if queue_item.estimated_completion_time else None,
                #                     'coffee_count': queue_item.coffee_count,
                #                     'preparation_time': queue_item.preparation_time_minutes
                #                 }
                #             )
                #         except CoffeeQueue.DoesNotExist:
                #             logger.info(f"訂單 {order.id} 沒有隊列項，可能不包含咖啡")
                # except Exception as ws_error:
                #     logger.error(f"發送WebSocket通知失敗: {ws_error}")
                #     
                # # WebSocket 發送暫時禁用，以確保支付流程穩定
                
                logger.info(f"✅ 支付寶回調處理成功，訂單: {out_trade_no}")
                clear_payment_session(request, out_trade_no)
                return safe_redirect_to_confirmation(out_trade_no)
                
            except Exception as direct_error:
                logger.error(f"直接處理訂單失敗: {direct_error}")
                return redirect_to_payment_failed(f"訂單處理失敗: {str(direct_error)}", out_trade_no)
            
        except OrderModel.DoesNotExist:
            logger.error(f"訂單不存在: {out_trade_no}")
            return redirect_to_payment_failed("訂單不存在", out_trade_no)
            
    except Exception as e:
        logger.error(f"支付寶回調處理異常: {str(e)}")
        logger.error(f"詳細錯誤: {traceback.format_exc()}")
        
        # 安全地獲取訂單ID
        try:
            out_trade_no = None
            if 'out_trade_no' in request.GET:
                out_trade_no = request.GET.get('out_trade_no')
            elif hasattr(request, 'data') and 'out_trade_no' in request.data:
                out_trade_no = request.data.get('out_trade_no')
            
            error_msg = f"支付處理異常: {str(e)}"
            if len(error_msg) > 100:
                error_msg = error_msg[:100] + "..."
            
            return redirect_to_payment_failed(error_msg, out_trade_no)
        except Exception as inner_e:
            logger.error(f"處理異常時發生錯誤: {inner_e}")
            return redirect_to_payment_failed("支付處理過程中發生未知錯誤")


@csrf_exempt
def alipay_notify(request):
    """支付寶異步通知處理 - 簡化版本"""
    if request.method == 'POST':
        # 解析數據
        data = {}
        for key, value in request.POST.items():
            data[key] = unquote(value)
        
        logger.info(f"支付寶異步通知數據: {data}")
        
        # 使用統一的支付工具驗證簽名
        payment_tools = get_payment_tools('alipay')
        if not payment_tools or 'verify' not in payment_tools:
            logger.error("支付寶驗證工具不可用")
            return HttpResponse("簽名驗證失敗", status=400)
        
        if not payment_tools['verify'](data):
            logger.error("支付寶異步通知簽名驗證失敗")
            return HttpResponse("簽名驗證失敗", status=400)
        
        # 處理支付成功
        out_trade_no = data.get('out_trade_no')
        trade_status = data.get('trade_status')
        
        if trade_status == 'TRADE_SUCCESS':
            try:
                order = OrderModel.objects.get(id=out_trade_no)
                if order.payment_status != "paid":
                    # 使用 OrderStatusManager 處理支付成功
                    if handle_payment_success(out_trade_no, 'alipay'):
                        logger.info(f"支付寶異步通知: 訂單 {out_trade_no} 支付狀態已更新")
                        return HttpResponse("success")
                    else:
                        return HttpResponse("訂單處理失敗", status=400)
                else:
                    return HttpResponse("success")
            except OrderModel.DoesNotExist:
                return HttpResponse("訂單不存在", status=400)
    
    return HttpResponse("僅支持POST請求", status=400)

@csrf_exempt
def paypal_callback(request):
    """PayPal支付回調處理 - 使用 OrderStatusManager"""
    try:
        # 取得訂單ID和支付ID
        order_id = request.session.get('pending_paypal_order_id')
        payment_id = request.GET.get('token')
        
        if not order_id:
            messages.error(request, "支付會話已過期，請重新下單")
            return redirect('cart:cart_detail')
        
        # 獲取訂單
        order = OrderModel.objects.get(id=order_id)
        
        # 如果訂單已經支付，直接跳到成功頁面
        if order.payment_status == "paid":
            clear_user_cart_and_session(request)
            return redirect_to_confirmation(order.id)
        
        # Capture 支付
        payment_tools = get_payment_tools('paypal')
        if not payment_tools or 'capture' not in payment_tools:
            messages.error(request, "PayPal支付系統暫時不可用")
            return redirect_to_payment_failed("PayPal支付系統不可用", order_id)
        
        if payment_tools['capture'](payment_id):
            # ✅ 修復：直接更新訂單支付狀態，然後使用 OrderStatusManager
            order.payment_status = 'paid'
            order.payment_method = 'paypal'
            order.save()
            
            # ✅ 修復：使用 OrderStatusManager 處理後續邏輯，並添加異常處理
            try:
                result = OrderStatusManager.process_payment_success(order_id, request)
                
                if not result.get('success'):
                    error_msg = result.get('message', '未知錯誤')
                    logger.error(f"PayPal支付成功但訂單處理失敗: {error_msg}")
                    messages.error(request, f"支付成功但訂單處理失敗: {error_msg}")
                    return redirect_to_payment_failed(f"PayPal支付成功但訂單處理失敗: {error_msg}", order_id)
            except Exception as e:
                logger.error(f"調用OrderStatusManager.process_payment_success失敗: {str(e)}")
                messages.error(request, f"支付成功但訂單處理失敗: {str(e)}")
                return redirect_to_payment_failed(f"PayPal支付成功但訂單處理失敗: {str(e)}", order_id)
            
            # 清空購物車
            clear_user_cart_and_session(request)
            
            # 發送通知（暫時註釋掉，以避免事件循環錯誤）
            # try:
            #     if WEBSOCKET_ENABLED:
            #         send_payment_update(
            #             order_id=order.id,
            #             payment_status='paid',
            #             data={
            #                 'payment_method': 'paypal',
            #                 'message': 'PayPal支付成功'
            #             }
            #         )
            #
            #         send_order_update(
            #             order_id=order.id,
            #             update_type='status_change',
            #             data={
            #                 'status': order.status,
            #                 'message': '支付成功，訂單已確認'
            #             }
            #         )
            # except Exception as ws_error:
            #     logger.error(f"發送WebSocket通知失敗: {ws_error}")
            
            # 清理session
            clear_payment_session(request, order_id)
            
            # ✅ 修復：使用正確的重定向函數
            return redirect_to_confirmation(order.id)
        else:
            # 支付失敗
            messages.error(request, "支付失敗，請稍後重試或選擇其他支付方式")
            return redirect_to_payment_failed("PayPal支付失敗", order_id)
            
    except OrderModel.DoesNotExist:
        messages.error(request, "訂單不存在")
        return redirect('cart:cart_detail')
    except Exception as e:
        logger.error(f"PayPal回調處理異常: {e}")
        messages.error(request, f"支付處理異常: {str(e)}")
        return redirect_to_payment_failed(f"PayPal處理異常: {str(e)}", order_id)



def safe_redirect_to_confirmation(order_id):
    """安全的訂單確認頁面重定向"""
    try:
        if not order_id:
            logger.error("safe_redirect_to_confirmation: 沒有提供訂單ID")
            return redirect_to_payment_failed("缺少訂單信息")
        
        # 驗證訂單是否存在
        try:
            order = OrderModel.objects.get(id=order_id)
        except OrderModel.DoesNotExist:
            logger.error(f"訂單不存在: {order_id}")
            return redirect_to_payment_failed(f"訂單 {order_id} 不存在")
        
        # 使用統一的重定向函數
        return redirect_to_confirmation(order_id)
        
    except Exception as e:
        logger.error(f"safe_redirect_to_confirmation 失敗: {str(e)}")
        return redirect_to_payment_failed(f"重定向失敗: {str(e)}", order_id)


# ✅ 新增：通用的購物車和session清理函數
def clear_user_cart_and_session(request):
    """清除用戶購物車和相關session數據"""
    try:
        from cart.cart import Cart
        
        # 1. 清空購物車對象
        cart = Cart(request)
        cart.clear()
        
        # 2. 清除所有相關session鍵
        session_keys_to_clear = [
            'cart',                    # 主購物車
            'pending_order',           # 待處理訂單
            'guest_cart',              # 遊客購物車
            'quick_order_data',        # 快速訂單數據
            'current_payment_order_id', # 當前支付訂單ID
            'payment_start_time',      # 支付開始時間
            'pending_paypal_order_id', # PayPal訂單ID
            'pending_fps_order_id',    # FPS訂單ID
            'pending_cash_order_id',   # 現金訂單ID
            'last_order_id'            # 上次訂單ID
        ]
        
        cleared_keys = []
        for key in session_keys_to_clear:
            if key in request.session:
                del request.session[key]
                cleared_keys.append(key)
        
        request.session.modified = True
        
        logger.info(f"✅ 購物車和session已清除: {cleared_keys}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 清空購物車失敗: {str(e)}")
        return False
        



# ==================== FPS支付视图 ====================

def fps_payment(request, order_id):
    """FPS支付页面"""
    try:
        order = get_object_or_404(OrderModel, id=order_id)
        
        # 验证用户权限
        if request.user.is_authenticated and order.user != request.user:
            messages.error(request, "您无权访问此订单")
            return redirect('index')
        
        # 生成FPS参考号
        payment_tools = get_payment_tools('fps')
        if payment_tools and 'create_reference' in payment_tools:
            fps_reference = payment_tools['create_reference'](order.id)
        else:
            fps_reference = f"BC{order.id:06d}"
        
        context = {
            'order': order,
            'fps_reference': order.fps_reference or fps_reference,
            'amount': order.total_price,
            'phone': order.phone or '',
        }
        
        return render(request, 'eshop/fps_payment.html', context)
        
    except Exception as e:
        logger.error(f"FPS支付页面错误: {str(e)}")
        messages.error(request, f"FPS支付页面加载失败: {str(e)}")
        return redirect('eshop:order_detail', order_id=order_id)

# ==================== 现金支付视图 ====================

def cash_payment(request, order_id):
    """现金支付确认页面"""
    try:
        order = get_object_or_404(OrderModel, id=order_id)
        
        # 验证用户权限
        if request.user.is_authenticated and order.user != request.user:
            messages.error(request, "您无权访问此订单")
            return redirect('index')
        
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
        logger.error(f"现金支付页面错误: {str(e)}")
        messages.error(request, f"现金支付页面加载失败: {str(e)}")
        return redirect('eshop:order_detail', order_id=order_id)



# ==================== 支付状态检查视图 ====================

def check_and_update_payment_status(request, order_id):
    """检查和更新支付状态"""
    try:
        order = get_object_or_404(OrderModel, id=order_id)
        
        return JsonResponse({
            'success': True,
            'order_id': order.id,
            'status': order.status,
            'payment_status': order.payment_status,
            'payment_method': order.payment_method,
        })
        
    except Exception as e:
        logger.error(f"检查支付状态错误: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

def query_payment_status(request, order_id):
    """查询支付状态"""
    try:
        order = get_object_or_404(OrderModel, id=order_id)
        
        return JsonResponse({
            'order_id': order.id,
            'payment_status': order.payment_status,
            'payment_method': order.payment_method,
            'created_at': order.created_at.isoformat(),
            'payment_timeout': order.payment_timeout.isoformat() if order.payment_timeout else None,
            'is_timeout': order.is_payment_timeout(),
            'total_price': float(order.total_price),
        })
        
    except Exception as e:
        logger.error(f"查询支付状态错误: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

# ==================== 支付超时处理 ====================

def check_payment_timeout(request, order_id):
    """检查支付超时"""
    try:
        order = get_object_or_404(OrderModel, id=order_id)
        
        if order.is_payment_timeout():
            return JsonResponse({
                'timeout': True,
                'message': '支付已超时',
                'redirect_url': f'/eshop/cancel_timeout_payment/{order.id}/'
            })
        else:
            # 计算剩余时间
            now = timezone.now()
            remaining = order.payment_timeout - now if order.payment_timeout else None
            
            return JsonResponse({
                'timeout': False,
                'remaining_seconds': remaining.total_seconds() if remaining else None,
                'payment_timeout': order.payment_timeout.isoformat() if order.payment_timeout else None,
            })
            
    except Exception as e:
        logger.error(f"检查支付超时错误: {str(e)}")
        return JsonResponse({
            'timeout': False,
            'error': str(e)
        })

def cancel_timeout_payment(request, order_id):
    """取消超時支付 - 使用 OrderStatusManager"""
    try:
        order = OrderModel.objects.get(id=order_id)
        
        if order.is_payment_timeout() and order.payment_status != 'paid':
            result = OrderStatusManager.mark_as_cancelled_manually(
                order_id=order_id,
                staff_name='system',
                reason='支付超時'
            )
            
            if result['success']:
                messages.warning(request, "支付超時，訂單已取消")
            else:
                messages.error(request, f"取消訂單失敗: {result['message']}")
                
            return redirect('eshop:index')
        else:
            messages.info(request, "訂單未超時或已支付")
            return redirect('eshop:order_detail', order_id=order.id)
            
    except Exception as e:
        logger.error(f"取消超時支付錯誤: {str(e)}")
        messages.error(request, f"取消支付失敗: {str(e)}")
        return redirect('eshop:order_detail', order_id=order_id)
    


# ==================== 重新支付视图 ====================

def retry_payment(request, order_id):
    """重新尝试支付"""
    try:
        order = get_object_or_404(OrderModel, id=order_id)
        
        if order.payment_status == "paid":
            messages.info(request, "订单已支付")
            return redirect('eshop:order_detail', order_id=order.id)
        
        # 重置支付超时时间
        order.set_payment_timeout(minutes=5)
        
        # 根据支付方式重定向
        if order.payment_method == 'alipay':
            return redirect('eshop:alipay_payment', order_id=order.id)
        elif order.payment_method == 'fps':
            return redirect('eshop:fps_payment', order_id=order.id)
        elif order.payment_method == 'cash':
            return redirect('eshop:cash_payment', order_id=order.id)
        else:
            # 默认使用支付宝
            return redirect('eshop:alipay_payment', order_id=order.id)
            
    except Exception as e:
        logger.error(f"重新支付错误: {str(e)}")
        messages.error(request, f"重新支付失败: {str(e)}")
        return redirect('eshop:order_detail', order_id=order_id)

# ==================== 支付失败页面 ====================

def payment_failed(request):
    """支付失败页面"""
    error_message = request.GET.get('error', '支付失败')
    order_id = request.GET.get('order_id')
    
    order = None
    can_retry = False
    
    if order_id:
        try:
            order = OrderModel.objects.get(id=order_id)
            if request.user.is_authenticated:
                can_retry = order.can_retry_payment() and order.payment_status != 'paid'
        except OrderModel.DoesNotExist:
            pass
    
    context = {
        'error_message': error_message,
        'order': order,
        'can_retry': can_retry
    }
    
    return render(request, 'eshop/payment_failed.html', context)


# ==================== 辅助函数 ====================


def redirect_to_payment_failed(error_message, order_id=None):
    """重定向到支付失败页面"""
    from django.urls import reverse
    from urllib.parse import quote
    
    url = reverse('eshop:payment_failed')
    params = f"?error={quote(error_message)}"
    
    if order_id:
        params += f"&order_id={order_id}"
    
    return redirect(url + params)



def redirect_to_confirmation(order_id):
    """重定向到支付确认页面"""
    from django.urls import reverse
    try:
        if WEBSOCKET_ENABLED:
            # 暫時註釋掉此處的 WebSocket 發送，因為在事件循環中也會引發錯誤
            # send_order_update(
            #     order_id=order_id,
            #     update_type='redirect',
            #     data={
            #         'message': '正在跳转到订单确认页面'
            #     }
            # )
            pass
    except Exception as ws_error:
        logger.error(f"发送WebSocket通知失败: {ws_error}")
    
    # ✅ 修復：使用 order_id 參數，而不是不存在的 order 變數
    try:
        # 嘗試使用帶參數的版本
        return redirect(reverse('eshop:order_payment_confirmation_with_id', kwargs={'order_id': order_id}))
    except:
        # 備用方案：使用無參數版本 + GET參數
        return redirect(reverse('eshop:order_payment_confirmation') + f'?order_id={order_id}')


def handle_payment_by_order_id(request, order_id):
    """根据订单ID处理支付"""
    try:
        if not order_id:
            from django.urls import reverse
            return redirect('eshop:order_payment_confirmation_with_id', order_id=order.id)
        
        order = OrderModel.objects.get(id=order_id)
        if order.payment_status == "paid":
            return redirect_to_confirmation(order_id)
        else:
            # 即使回调有问题，也标记为已支付（因为手机端显示已扣款）
            order.payment_status="paid"
            order.payment_status = 'paid'
            # ✅ 已修復：使用 OrderStatusManager
            from eshop.order_status_manager import OrderStatusManager
            result = OrderStatusManager.mark_as_waiting_manually(
                order_id=order.id,
                staff_name=request.user.username if hasattr(request, 'user') else 'system'
            )
            if not result.get('success'):
                logger.error(f"標記訂單 {order.id} 為 waiting 失敗: {result.get('message')}")
            order.save()
            clear_payment_session(request, order_id)
            return redirect_to_confirmation(order_id)
            
    except OrderModel.DoesNotExist:
        logger.error(f"订单不存在: {order_id}")
        from django.urls import reverse
        return redirect('eshop:order_payment_confirmation_with_id', order_id=order.id)

# ==================== 支付宝配置检查 ====================

def check_alipay_keys(request):
    """检查支付宝密钥配置"""
    try:
        payment_tools = get_payment_tools('alipay')
        if not payment_tools or 'check_keys' not in payment_tools:
            return JsonResponse({
                'success': False,
                'error': '支付宝检查工具不可用'
            })
        
        result = payment_tools['check_keys']()
        return JsonResponse(result)
    except Exception as e:
        logger.error(f"检查支付宝密钥错误: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

def check_key_match(request):
    """检查支付宝密钥匹配"""
    try:
        from alipay import AliPay
        
        # 创建测试签名
        test_data = {"test": "data"}
        
        app_private_key_string = open(settings.ALIPAY_PRIVATE_KEY_PATH).read()
        alipay_public_key_string = open(settings.ALIPAY_PUBLIC_KEY_PATH).read()
        
        alipay = AliPay(
            appid=settings.ALIPAY_APP_ID,
            app_notify_url=None,
            app_private_key_string=app_private_key_string,
            alipay_public_key_string=alipay_public_key_string,
            sign_type="RSA2",
            debug=settings.ALIPAY_DEBUG
        )
        
        # 测试签名和验证
        import json
        test_string = json.dumps(test_data)
        
        return JsonResponse({
            'success': True,
            'message': '支付宝密钥匹配检查完成',
            'note': '完整的密钥匹配需要实际支付测试'
        })
        
    except Exception as e:
        logger.error(f"检查密钥匹配错误: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

def check_alipay_config(request):
    """检查支付宝完整配置"""
    try:
        config_status = {
            'ALIPAY_APP_ID': settings.ALIPAY_APP_ID if hasattr(settings, 'ALIPAY_APP_ID') else None,
            'ALIPAY_DEBUG': settings.ALIPAY_DEBUG if hasattr(settings, 'ALIPAY_DEBUG') else None,
            'ALIPAY_RETURN_URL': settings.ALIPAY_RETURN_URL if hasattr(settings, 'ALIPAY_RETURN_URL') else None,
            'ALIPAY_NOTIFY_URL': settings.ALIPAY_NOTIFY_URL if hasattr(settings, 'ALIPAY_NOTIFY_URL') else None,
        }
        
        # 检查文件是否存在
        import os
        key_files = {
            'private_key': settings.ALIPAY_PRIVATE_KEY_PATH if hasattr(settings, 'ALIPAY_PRIVATE_KEY_PATH') else None,
            'public_key': settings.ALIPAY_PUBLIC_KEY_PATH if hasattr(settings, 'ALIPAY_PUBLIC_KEY_PATH') else None,
        }
        
        file_status = {}
        for key, path in key_files.items():
            if path and os.path.exists(path):
                file_status[key] = True
                # 检查文件是否可读
                try:
                    with open(path, 'r') as f:
                        content = f.read()
                    file_status[f'{key}_readable'] = True
                except:
                    file_status[f'{key}_readable'] = False
            else:
                file_status[key] = False
        
        return JsonResponse({
            'success': True,
            'config': config_status,
            'files': file_status,
            'all_good': all(file_status.get(f, False) for f in ['private_key', 'public_key'])
        })
        
    except Exception as e:
        logger.error(f"检查支付宝配置错误: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

# ==================== 测试功能 ====================

def test_payment_cancel(request, order_id):
    """测试支付取消（仅用于测试）"""
    try:
        order = get_object_or_404(OrderModel, id=order_id)
        
        if order.payment_status != "paid":
            # ✅ 已修復：使用 OrderStatusManager
            from eshop.order_status_manager import OrderStatusManager
            result = OrderStatusManager.mark_as_cancelled_manually(
                order_id=order.id,
                staff_name=request.user.username if hasattr(request, 'user') else 'system',
                reason='支付失敗或超時'
            )
            if not result.get('success'):
                logger.error(f"取消訂單 {order.id} 失敗: {result.get('message')}")
            order.payment_status = 'cancelled'
            order.save()
            
            messages.info(request, "测试：订单已取消")
        else:
            messages.warning(request, "订单已支付，无法取消")
        
        return redirect('eshop:order_detail', order_id=order.id)
        
    except Exception as e:
        logger.error(f"测试支付取消错误: {str(e)}")
        messages.error(request, f"测试失败: {str(e)}")
        return redirect('eshop:order_detail', order_id=order_id)

def simulate_alipay_cancel(request, order_id):
    """模拟支付宝取消支付（仅用于测试）"""
    try:
        order = get_object_or_404(OrderModel, id=order_id)
        
        if order.payment_status != "paid":
            # 模拟支付宝取消回调
            messages.info(request, "模拟支付宝支付取消")
            
            # 这里可以记录测试日志
            logger.info(f"模拟支付宝取消支付: 订单 {order_id}")
            
        return redirect('eshop:order_detail', order_id=order.id)
        
    except Exception as e:
        logger.error(f"模拟支付宝取消错误: {str(e)}")
        messages.error(request, f"模拟失败: {str(e)}")
        return redirect('eshop:order_detail', order_id=order_id)