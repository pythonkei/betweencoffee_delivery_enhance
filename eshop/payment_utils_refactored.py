# eshop/payment_utils_refactored.py - 使用統一錯誤處理框架
"""
支付工具模块 - 整合所有支付功能，使用統一的錯誤處理框架

這個版本使用新的錯誤處理框架，提供：
1. 統一的錯誤處理
2. 標準化的響應格式
3. 詳細的錯誤日誌
4. 錯誤ID追蹤
"""

import logging
from django.conf import settings
from urllib.parse import unquote

from .error_handling import (
    handle_error,
    handle_success,
    error_handler_decorator,
    handle_external_api_error,
    ErrorHandler
)

logger = logging.getLogger(__name__)

# 創建支付模塊的錯誤處理器
payment_error_handler = ErrorHandler(module_name='payment_utils')


# ==================== 支付工具获取器 ====================

def get_payment_tools(payment_method):
    """
    获取指定支付方式的工具函数（避免循环导入）- 使用錯誤處理框架
    Args:
        payment_method: 'alipay', 'paypal', 'fps', 'cash'
    Returns:
        dict: 包含该支付方式的所有工具函数
    """
    try:
        tools = {
            'alipay': {
                'create': create_alipay_payment_url,
                'verify': verify_alipay_signature,
                'check_keys': check_alipay_keys,
                'client': create_alipay_payment,  # 返回客户端
            },
            'paypal': {
                'get_token': get_paypal_access_token,
                'create': create_paypal_payment,
                'capture': capture_paypal_payment,
            },
            'fps': {
                'create_reference': generate_fps_reference,
                'validate': validate_fps_payment,
            },
            'cash': {
                'process': lambda order, request: True
            }
        }
        
        if payment_method not in tools:
            return handle_error(
                error=ValueError(f"不支持的支付方式: {payment_method}"),
                context='get_payment_tools',
                operation='get_payment_tools',
                data={'payment_method': payment_method},
                log_level='warning'
            )
        
        return handle_success(
            operation='get_payment_tools',
            data={'tools': tools[payment_method], 'payment_method': payment_method},
            message=f'獲取 {payment_method} 支付工具成功'
        )
        
    except Exception as e:
        return handle_error(
            error=e,
            context='get_payment_tools',
            operation='get_payment_tools',
            data={'payment_method': payment_method}
        )


def get_payment_urls():
    """获取所有支付相关的URL配置 - 使用錯誤處理框架"""
    try:
        urls = {
            'alipay': {
                'return_url': getattr(settings, 'ALIPAY_RETURN_URL', ''),
                'notify_url': getattr(settings, 'ALIPAY_NOTIFY_URL', ''),
            },
            'paypal': {
                'return_url': getattr(settings, 'PAYPAL_RETURN_URL', ''),
                'cancel_url': getattr(settings, 'PAYPAL_CANCEL_URL', ''),
            }
        }
        
        return handle_success(
            operation='get_payment_urls',
            data={'urls': urls},
            message='獲取支付URL配置成功'
        )
        
    except Exception as e:
        return handle_error(
            error=e,
            context='get_payment_urls',
            operation='get_payment_urls'
        )


def get_alipay_return_url():
    """获取支付宝同步回调URL - 使用錯誤處理框架"""
    try:
        return_url = getattr(settings, 'ALIPAY_RETURN_URL', '')
        
        return handle_success(
            operation='get_alipay_return_url',
            data={'return_url': return_url},
            message='獲取支付寶返回URL成功'
        )
        
    except Exception as e:
        return handle_error(
            error=e,
            context='get_alipay_return_url',
            operation='get_alipay_return_url'
        )


def get_alipay_notify_url():
    """获取支付宝异步通知URL - 使用錯誤處理框架"""
    try:
        notify_url = getattr(settings, 'ALIPAY_NOTIFY_URL', '')
        
        return handle_success(
            operation='get_alipay_notify_url',
            data={'notify_url': notify_url},
            message='獲取支付寶通知URL成功'
        )
        
    except Exception as e:
        return handle_error(
            error=e,
            context='get_alipay_notify_url',
            operation='get_alipay_notify_url'
        )


# ==================== 支付宝支付相关函数 ====================

def create_alipay_payment():
    """创建支付宝支付客户端 - 使用錯誤處理框架"""
    try:
        from .alipay_utils import get_alipay_client
        client = get_alipay_client()
        
        if client is None:
            raise ValueError("創建支付寶客戶端失敗")
        
        return handle_success(
            operation='create_alipay_payment',
            data={'client': client},
            message='創建支付寶支付客戶端成功'
        )
        
    except ImportError as e:
        return handle_error(
            error=e,
            context='create_alipay_payment',
            operation='create_alipay_payment',
            data={'error_type': 'ImportError'},
            log_level='error'
        )
    except Exception as e:
        return handle_error(
            error=e,
            context='create_alipay_payment',
            operation='create_alipay_payment'
        )


def verify_alipay_signature(data):
    """验证支付宝签名 - 使用錯誤處理框架"""
    try:
        from .alipay_utils import verify_alipay_notification
        is_valid = verify_alipay_notification(data)
        
        return handle_success(
            operation='verify_alipay_signature',
            data={'is_valid': is_valid, 'data_keys': list(data.keys())},
            message='支付寶簽名驗證完成'
        )
        
    except ImportError as e:
        return handle_error(
            error=e,
            context='verify_alipay_signature',
            operation='verify_alipay_signature',
            data={'error_type': 'ImportError'},
            log_level='error'
        )
    except Exception as e:
        return handle_error(
            error=e,
            context='verify_alipay_signature',
            operation='verify_alipay_signature',
            data={'data_keys': list(data.keys()) if data else []}
        )


def create_alipay_payment_url(order, request):
    """创建支付宝支付URL - 使用錯誤處理框架"""
    try:
        from .alipay_utils import create_alipay_payment as create_alipay_payment_func
        payment_url = create_alipay_payment_func(order, request)
        
        if payment_url is None:
            raise ValueError("創建支付寶支付URL失敗")
        
        return handle_success(
            operation='create_alipay_payment_url',
            data={
                'payment_url': payment_url,
                'order_id': order.id,
                'payment_method': 'alipay'
            },
            message='創建支付寶支付URL成功'
        )
        
    except Exception as e:
        return handle_error(
            error=e,
            context='create_alipay_payment_url',
            operation='create_alipay_payment_url',
            data={'order_id': order.id if order else None}
        )


def check_alipay_keys():
    """检查支付宝密钥配置 - 使用錯誤處理框架"""
    try:
        from alipay import AliPay
        
        # 檢查必要配置
        required_keys = ['ALIPAY_APP_ID', 'ALIPAY_APP_PRIVATE_KEY', 'ALIPAY_PUBLIC_KEY']
        missing_keys = []
        
        for key in required_keys:
            if not hasattr(settings, key):
                missing_keys.append(key)
        
        if missing_keys:
            return handle_error(
                error=ValueError(f"支付寶配置缺失: {', '.join(missing_keys)}"),
                context='check_alipay_keys',
                operation='check_alipay_keys',
                data={'missing_keys': missing_keys},
                log_level='warning'
            )
        
        # 嘗試創建客戶端
        try:
            alipay = AliPay(
                appid=settings.ALIPAY_APP_ID,
                app_notify_url=None,
                app_private_key_string=settings.ALIPAY_APP_PRIVATE_KEY,
                alipay_public_key_string=settings.ALIPAY_PUBLIC_KEY,
                sign_type="RSA2",
                debug=getattr(settings, 'ALIPAY_DEBUG', False)
            )
            
            return handle_success(
                operation='check_alipay_keys',
                data={
                    'app_id': settings.ALIPAY_APP_ID,
                    'debug': getattr(settings, 'ALIPAY_DEBUG', False),
                    'client_created': True
                },
                message='支付寶密鑰配置正常'
            )
            
        except Exception as e:
            return handle_error(
                error=e,
                context='check_alipay_keys',
                operation='check_alipay_keys',
                data={'app_id': settings.ALIPAY_APP_ID},
                log_level='error'
            )
        
    except ImportError as e:
        return handle_error(
            error=e,
            context='check_alipay_keys',
            operation='check_alipay_keys',
            data={'error_type': 'ImportError'},
            log_level='error'
        )


# ==================== PayPal支付相关函数 ====================

def get_paypal_access_token():
    """获取PayPal访问令牌 - 使用錯誤處理框架"""
    try:
        from .paypal_utils import get_paypal_access_token as get_paypal_token
        token = get_paypal_token()
        
        if token is None:
            raise ValueError("獲取PayPal訪問令牌失敗")
        
        return handle_success(
            operation='get_paypal_access_token',
            data={'token': token[:20] + '...' if token else None},
            message='獲取PayPal訪問令牌成功'
        )
        
    except ImportError as e:
        return handle_error(
            error=e,
            context='get_paypal_access_token',
            operation='get_paypal_access_token',
            data={'error_type': 'ImportError'},
            log_level='error'
        )
    except Exception as e:
        return handle_error(
            error=e,
            context='get_paypal_access_token',
            operation='get_paypal_access_token'
        )


def create_paypal_payment(order, request):
    """创建PayPal支付 - 使用錯誤處理框架"""
    try:
        from .paypal_utils import create_paypal_payment as create_paypal_payment_func
        payment_result = create_paypal_payment_func(order, request)
        
        if payment_result is None:
            raise ValueError("創建PayPal支付失敗")
        
        return handle_success(
            operation='create_paypal_payment',
            data={
                'payment_result': payment_result,
                'order_id': order.id,
                'payment_method': 'paypal'
            },
            message='創建PayPal支付成功'
        )
        
    except Exception as e:
        return handle_error(
            error=e,
            context='create_paypal_payment',
            operation='create_paypal_payment',
            data={'order_id': order.id if order else None}
        )


def capture_paypal_payment(payment_id):
    """捕获PayPal支付 - 使用錯誤處理框架"""
    try:
        from .paypal_utils import capture_paypal_payment as capture_paypal_func
        capture_result = capture_paypal_func(payment_id)
        
        if not capture_result:
            raise ValueError("捕獲PayPal支付失敗")
        
        return handle_success(
            operation='capture_paypal_payment',
            data={
                'capture_result': capture_result,
                'payment_id': payment_id
            },
            message='捕獲PayPal支付成功'
        )
        
    except Exception as e:
        return handle_error(
            error=e,
            context='capture_paypal_payment',
            operation='capture_paypal_payment',
            data={'payment_id': payment_id}
        )


# ==================== FPS支付相关函数 ====================

def generate_fps_reference(order_id):
    """生成FPS参考编号 - 使用錯誤處理框架"""
    try:
        reference = f"BC{order_id:06d}"
        
        return handle_success(
            operation='generate_fps_reference',
            data={'reference': reference, 'order_id': order_id},
            message='生成FPS參考編號成功'
        )
        
    except Exception as e:
        return handle_error(
            error=e,
            context='generate_fps_reference',
            operation='generate_fps_reference',
            data={'order_id': order_id}
        )


def validate_fps_payment(reference, amount):
    """验证FPS支付（模拟） - 使用錯誤處理框架"""
    try:
        # 模擬驗證邏輯
        is_valid = True
        
        return handle_success(
            operation='validate_fps_payment',
            data={
                'success': True,
                'reference': reference,
                'amount': amount,
                'verified': is_valid
            },
            message='FPS支付驗證完成'
        )
        
    except Exception as e:
        return handle_error(
            error=e,
            context='validate_fps_payment',
            operation='validate_fps_payment',
            data={'reference': reference, 'amount': amount}
        )


# ==================== 通用支付函数 ====================

def validate_payment_amount(order, payment_amount):
    """验证支付金额 - 使用錯誤處理框架"""
    try:
        order_amount = float(order.total_price)
        payment_amount = float(payment_amount)
        
        tolerance = order_amount * 0.01
        
        if abs(order_amount - payment_amount) <= tolerance:
            return handle_success(
                operation='validate_payment_amount',
                data={
                    'order_amount': order_amount,
                    'payment_amount': payment_amount,
                    'difference': abs(order_amount - payment_amount),
                    'tolerance': tolerance,
                    'is_valid': True
                },
                message='支付金額驗證通過'
            )
        else:
            return handle_error(
                error=ValueError(f"支付金額不匹配: 訂單金額={order_amount}, 支付金額={payment_amount}"),
                context='validate_payment_amount',
                operation='validate_payment_amount',
                data={
                    'order_amount': order_amount,
                    'payment_amount': payment_amount,
                    'difference': abs(order_amount - payment_amount),
                    'tolerance': tolerance,
                    'is_valid': False
                },
                log_level='warning'
            )
            
    except Exception as e:
        return handle_error(
            error=e,
            context='validate_payment_amount',
            operation='validate_payment_amount',
            data={'order_id': order.id if order else None, 'payment_amount': payment_amount}
        )


def update_order_payment_status(order, payment_method, payment_data=None):
    """更新订单支付状态 - 使用錯誤處理框架"""
    try:
        from django.utils import timezone
        
        if order.payment_status == "paid":
            return handle_success(
                operation='update_order_payment_status',
                data={
                    'order_id': order.id,
                    'payment_status': 'paid',
                    'payment_method': payment_method,
                    'already_paid': True
                },
                message='訂單已經是已支付狀態'
            )
        
        order.payment_status = 'paid'
        order.payment_method = payment_method
        order.paid_at = timezone.now()
        
        if payment_data:
            if payment_method == 'fps' and 'reference' in payment_data:
                order.fps_reference = payment_data['reference']
            elif payment_method == 'paypal' and 'payment_id' in payment_data:
                pass
        
        order.save()
        
        return handle_success(
            operation='update_order_payment_status',
            data={
                'order_id': order.id,
                'payment_status': 'paid',
                'payment_method': payment_method,
                'paid_at': order.paid_at.isoformat()
            },
            message='訂單支付狀態更新成功'
        )
        
    except Exception as e:
        return handle_error(
            error=e,
            context='update_order_payment_status',
            operation='update_order_payment_status',
            data={
                'order_id': order.id if order else None,
                'payment_method': payment_method,
                'payment_data_keys': list(payment_data.keys()) if payment_data else []
            }
        )


def handle_payment_callback(request, payment_type, data):
    """处理支付回调 - 使用錯誤處理框架"""
    try:
        logger.info(f"處理 {payment_type} 支付回調")
        
        if payment_type == 'alipay':
            # 驗證支付寶簽名
            verification_result = verify_alipay_signature(data)
            if not verification_result.get('success') or not verification_result.get('data', {}).get('is_valid'):
                return handle_error(
                    error=ValueError("支付寶簽名驗證失敗"),
                    context='handle_payment_callback',
                    operation='handle_payment_callback',
                    data={'payment_type': payment_type, 'data_keys': list(data.keys())},
                    log_level='error'
                )
            
            out_trade_no = data.get('out_trade_no')
            if not out_trade_no:
                return handle_error(
                    error=ValueError("缺少訂單號"),
                    context='handle_payment_callback',
                    operation='handle_payment_callback',
                    data={'payment_type': payment_type, 'data': data},
                    log_level='error'
                )
            
            return handle_success(
                operation='handle_payment_callback',
                data={
                    'order_id': int(out_trade_no),
                    'payment_method': 'alipay',
                    'payment_data': data,
                    'payment_type': payment_type
                },
                message='支付寶支付回調處理成功'
            )
            
        elif payment_type == 'paypal':
            # 處理PayPal回調
            payment_id = data.get('paymentId')
            payer_id = data.get('PayerID')
            
            if not payment_id or not payer_id:
                return handle_error(
                    error=ValueError("缺少支付信息"),
                    context='handle_payment_callback',
                    operation='handle_payment_callback',
                    data={'payment_type': payment_type, 'data': data},
                    log_level='error'
                )
            
            # 捕獲PayPal支付
            capture_result = capture_paypal_payment(payment_id)
            if not capture_result.get('success'):
                return handle_error(
                    error=ValueError("支付捕獲失敗"),
                    context='handle_payment_callback',
                    operation='handle_payment_callback',
                    data={'payment_type': payment_type, 'payment_id': payment_id},
                    log_level='error'
                )
            
            order_id = data.get('custom')
            if not order_id:
                order_id = payment_id.split('_')[0] if '_' in payment_id else None
            
            return handle_success(
                operation='handle_payment_callback',
                data={
                    'order_id': order_id,
                    'payment_method': 'paypal',
                    'payment_data': {
                        'payment_id': payment_id,
                        'payer_id': payer_id
                    },
                    'payment_type': payment_type
                },
                message='PayPal支付回調處理成功'
            )
            
        else:
            return handle_error(
                error=ValueError(f"不支持的支付類型: {payment_type}"),
                context='handle_payment_callback',
                operation='handle_payment_callback',
                data={'payment_type': payment_type, 'data': data},
                log_level='error'
            )
            
    except Exception as e:
        return handle_error(
            error=e,
            context='handle_payment_callback',
            operation='handle_payment_callback',
            data={'payment_type': payment_type, 'data_keys': list(data.keys()) if data else []}
        )


def get_payment_method_display(method):
    """获取支付方式显示文本 - 使用錯誤處理框架"""
    try:
        method_display = {
            'alipay': '支付宝',
            'paypal': 'PayPal',
            'fps': 'FPS转数快',
            'cash': '现金支付',
        }
        
        display_text = method_display.get(method, method)
        
        return handle_success(
            operation='get_payment_method_display',
            data={'method': method, 'display_text': display_text},
            message='獲取支付方式顯示文本成功'
        )
        
    except Exception as e:
        return handle_error(
            error=e,
            context='get_payment_method_display',
            operation='get_payment_method_display',
            data={'method': method}
        )


def is_payment_method_available(method):
    """检查支付方式是否可用 - 使用錯誤處理框架"""
    try:
        if method == 'alipay':
            available = all([
                hasattr(settings, 'ALIPAY_APP_ID'),
                hasattr(settings, 'ALIPAY_APP_PRIVATE_KEY'),
                hasattr(settings, 'ALIPAY_PUBLIC_KEY')
            ])
        elif method == 'paypal':
            available = all([
                hasattr(settings, 'PAYPAL_CLIENT_ID'),
                hasattr(settings, 'PAYPAL_CLIENT_SECRET')
            ])
        elif method == 'fps':
            available = True
        elif method == 'cash':
            available = True
        else:
            available = False
        
        return handle_success(
            operation='is_payment_method_available',
            data={'method': method, 'available': available},
            message='支付方式可用性檢查完成'
        )
        
    except Exception as e:
        return handle_error(
            error=e,
            context='is_payment_method_available',
            operation='is_payment_method_available',
            data={'method': method}
        )


def get_available_payment_methods():
    """获取可用的支付方式 - 使用錯誤處理框架"""
    try:
        methods = []
        
        # 檢查支付寶
        alipay_available = is_payment_method_available('alipay')
        if alipay_available.get('success') and alipay_available.get('data', {}).get('available'):
            methods.append({
                'id': 'alipay',
                'name': '支付宝',
                'description': '使用支付宝扫码支付'
            })
        
        # 檢查PayPal
        paypal_available = is_payment_method_available('paypal')
        if paypal_available.get('success') and paypal_available.get('data', {}).get('available'):
            methods.append({
                'id': 'paypal',
                'name': 'PayPal',
                'description': '使用PayPal国际支付'
            })
        
        # 檢查FPS
        fps_available = is_payment_method_available('fps')
        if fps_available.get('success') and fps_available.get('data', {}).get('available'):
            methods.append({
                'id': 'fps',
                'name': 'FPS转数快',
                'description': '香港快速支付系统'
            })
        
        # 檢查現金
        cash_available = is_payment_method_available('cash')
        if cash_available.get('success') and cash_available.get('data', {}).get('available'):
            methods.append({
                'id': 'cash',
                'name': '现金支付',
                'description': '到店现金支付'
            })
        
        return handle_success(
            operation='get_available_payment_methods',
            data={'methods': methods, 'count': len(methods)},
            message='獲取可用支付方式成功'
        )
        
    except Exception as e:
        return handle_error(
            error=e,
            context='get_available_payment_methods',
            operation='get_available_payment_methods'
        )


# ==================== 裝飾器示例 ====================

@error_handler_decorator(context='payment_utils_example')
def example_payment_function(order_id, payment_method):
    """示例支付函數 - 使用錯誤處理裝飾器"""
    # 這裡可以實現具體的支付邏輯
    return {
        'order_id': order_id,
        'payment_method': payment_method,
        'status': 'success'
    }


# ==================== 兼容性包裝器 ====================

def get_payment_tools_compatible(payment_method):
    """兼容性包裝器 - 返回原始格式的工具字典"""
    result = get_payment_tools(payment_method)
    if result.get('success'):
        return result.get('data', {}).get('tools', {})
    else:
        # 返回空字典或拋出異常，根據原始行為
        return {}


def generate_fps_reference_compatible(order_id):
    """兼容性包裝器 - 返回原始格式的參考編號"""
    result = generate_fps_reference(order_id)
    if result.get('success'):
        return result.get('data', {}).get('reference', '')
    else:
        return f"BC{order_id:06d}"  # 默認格式


# ==================== 測試函數 ====================

if __name__ == "__main__":
    """測試支付工具模塊"""
    import sys
    
    print("🔍 測試支付工具模塊 - 使用統一錯誤處理框架")
    print("=" * 60)
    
    # 測試錯誤處理
    print("1. 測試錯誤處理...")
    error_result = get_payment_tools('invalid_method')
    print(f"   錯誤處理測試: {error_result.get('success', False)}")
    print(f"   錯誤ID: {error_result.get('error_id', 'N/A')}")
    
    # 測試成功處理
    print("\n2. 測試成功處理...")
    success_result = generate_fps_reference(123)
    print(f"   成功處理測試: {success_result.get('success', False)}")
    print(f"   參考編號: {success_result.get('data', {}).get('reference', 'N/A')}")
    
    # 測試裝飾器
    print("\n3. 測試裝飾器...")
    decorator_result = example_payment_function(456, 'alipay')
    print(f"   裝飾器測試: {decorator_result.get('success', False)}")
    
    print("\n" + "=" * 60)
    print("✅ 支付工具模塊測試完成")
    
    sys.exit(0)
