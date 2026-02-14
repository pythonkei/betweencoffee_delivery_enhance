# eshop/payment_utils.py - 完整整合版
"""
支付工具模块 - 整合所有支付功能，避免循环导入
"""

import logging
from django.conf import settings
from urllib.parse import unquote

logger = logging.getLogger(__name__)

# ==================== 支付工具获取器 ====================

def get_payment_tools(payment_method):
    """
    获取指定支付方式的工具函数（避免循环导入）
    Args:
        payment_method: 'alipay', 'paypal', 'fps', 'cash'
    Returns:
        dict: 包含该支付方式的所有工具函数
    """
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
    
    return tools.get(payment_method, {})


def get_payment_urls():
    """获取所有支付相关的URL配置"""
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
    return urls


def get_alipay_return_url():
    """获取支付宝同步回调URL"""
    return getattr(settings, 'ALIPAY_RETURN_URL', '')


def get_alipay_notify_url():
    """获取支付宝异步通知URL"""
    return getattr(settings, 'ALIPAY_NOTIFY_URL', '')


# ==================== 支付宝支付相关函数 ====================

def create_alipay_payment():
    """创建支付宝支付客户端"""
    try:
        from .alipay_utils import get_alipay_client
        return get_alipay_client()
    except ImportError as e:
        logger.error(f"导入支付宝工具失败: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"创建支付宝支付客户端失败: {str(e)}")
        return None


def verify_alipay_signature(data):
    """验证支付宝签名"""
    try:
        from .alipay_utils import verify_alipay_notification
        return verify_alipay_notification(data)
    except ImportError as e:
        logger.error(f"导入支付宝验证工具失败: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"验证支付宝签名失败: {str(e)}")
        return False


def create_alipay_payment_url(order, request):
    """创建支付宝支付URL"""
    try:
        from .alipay_utils import create_alipay_payment as create_alipay_payment_func
        return create_alipay_payment_func(order, request)
    except Exception as e:
        logger.error(f"创建支付宝支付URL失败: {str(e)}")
        return None


def check_alipay_keys():
    """检查支付宝密钥配置"""
    try:
        from alipay import AliPay
        
        if not hasattr(settings, 'ALIPAY_APP_PRIVATE_KEY'):
            return {
                'success': False,
                'error': 'ALIPAY_APP_PRIVATE_KEY 未配置'
            }
        
        if not hasattr(settings, 'ALIPAY_PUBLIC_KEY'):
            return {
                'success': False,
                'error': 'ALIPAY_PUBLIC_KEY 未配置'
            }
        
        try:
            alipay = AliPay(
                appid=settings.ALIPAY_APP_ID,
                app_notify_url=None,
                app_private_key_string=settings.ALIPAY_APP_PRIVATE_KEY,
                alipay_public_key_string=settings.ALIPAY_PUBLIC_KEY,
                sign_type="RSA2",
                debug=settings.ALIPAY_DEBUG
            )
            return {
                'success': True,
                'message': '支付宝密钥配置正常',
                'app_id': settings.ALIPAY_APP_ID,
                'debug': settings.ALIPAY_DEBUG,
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'支付宝客户端创建失败: {str(e)}'
            }
        
    except ImportError:
        return {
            'success': False,
            'error': '支付宝SDK未安装，请安装: pip install python-alipay-sdk'
        }


# ==================== PayPal支付相关函数 ====================

def get_paypal_access_token():
    """获取PayPal访问令牌"""
    try:
        from .paypal_utils import get_paypal_access_token as get_paypal_token
        return get_paypal_token()
    except ImportError as e:
        logger.error(f"导入PayPal工具失败: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"获取PayPal访问令牌失败: {str(e)}")
        return None


def create_paypal_payment(order, request):
    """创建PayPal支付"""
    try:
        from .paypal_utils import create_paypal_payment as create_paypal_payment_func
        return create_paypal_payment_func(order, request)
    except Exception as e:
        logger.error(f"创建PayPal支付失败: {str(e)}")
        return None


def capture_paypal_payment(payment_id):
    """捕获PayPal支付"""
    try:
        from .paypal_utils import capture_paypal_payment as capture_paypal_func
        return capture_paypal_func(payment_id)
    except Exception as e:
        logger.error(f"捕获PayPal支付失败: {str(e)}")
        return False


# ==================== FPS支付相关函数 ====================

def generate_fps_reference(order_id):
    """生成FPS参考编号"""
    return f"BC{order_id:06d}"


def validate_fps_payment(reference, amount):
    """验证FPS支付（模拟）"""
    return {
        'success': True,
        'reference': reference,
        'amount': amount,
        'verified': True
    }


# ==================== 通用支付函数 ====================

def validate_payment_amount(order, payment_amount):
    """验证支付金额"""
    try:
        order_amount = float(order.total_price)
        payment_amount = float(payment_amount)
        
        tolerance = order_amount * 0.01
        
        if abs(order_amount - payment_amount) <= tolerance:
            return True
        else:
            logger.warning(f"支付金额不匹配: 订单金额={order_amount}, 支付金额={payment_amount}")
            return False
            
    except Exception as e:
        logger.error(f"验证支付金额失败: {str(e)}")
        return False


def update_order_payment_status(order, payment_method, payment_data=None):
    """更新订单支付状态"""
    try:
        from django.utils import timezone
        
        if order.payment_status == "paid":
            logger.info(f"订单 {order.id} 已经是已支付状态")
            return True
        
        order.payment_status="paid"
        order.payment_status = 'paid'
        order.payment_method = payment_method
        order.paid_at = timezone.now()
        
        if payment_data:
            if payment_method == 'fps' and 'reference' in payment_data:
                order.fps_reference = payment_data['reference']
            elif payment_method == 'paypal' and 'payment_id' in payment_data:
                pass
        
        order.save()
        logger.info(f"订单 {order.id} 支付状态更新为已支付，支付方式: {payment_method}")
        
        return True
        
    except Exception as e:
        logger.error(f"更新订单支付状态失败: {str(e)}")
        return False


def handle_payment_callback(request, payment_type, data):
    """处理支付回调"""
    try:
        logger.info(f"处理 {payment_type} 支付回调")
        
        if payment_type == 'alipay':
            is_valid = verify_alipay_signature(data)
            if not is_valid:
                return {
                    'success': False,
                    'error': '签名验证失败'
                }
            
            out_trade_no = data.get('out_trade_no')
            if not out_trade_no:
                return {
                    'success': False,
                    'error': '缺少订单号'
                }
            
            return {
                'success': True,
                'order_id': int(out_trade_no),
                'payment_method': 'alipay',
                'payment_data': data
            }
            
        elif payment_type == 'paypal':
            payment_id = data.get('paymentId')
            payer_id = data.get('PayerID')
            
            if not payment_id or not payer_id:
                return {
                    'success': False,
                    'error': '缺少支付信息'
                }
            
            is_captured = capture_paypal_payment(payment_id)
            if not is_captured:
                return {
                    'success': False,
                    'error': '支付捕获失败'
                }
            
            order_id = data.get('custom')
            if not order_id:
                order_id = payment_id.split('_')[0] if '_' in payment_id else None
            
            return {
                'success': True,
                'order_id': order_id,
                'payment_method': 'paypal',
                'payment_data': {
                    'payment_id': payment_id,
                    'payer_id': payer_id
                }
            }
            
        else:
            return {
                'success': False,
                'error': f'不支持的支付类型: {payment_type}'
            }
            
    except Exception as e:
        logger.error(f"处理支付回调失败: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


def get_payment_method_display(method):
    """获取支付方式显示文本"""
    method_display = {
        'alipay': '支付宝',
        'paypal': 'PayPal',
        'fps': 'FPS转数快',
        'cash': '现金支付',
    }
    return method_display.get(method, method)


def is_payment_method_available(method):
    """检查支付方式是否可用"""
    if method == 'alipay':
        return all([
            hasattr(settings, 'ALIPAY_APP_ID'),
            hasattr(settings, 'ALIPAY_APP_PRIVATE_KEY'),
            hasattr(settings, 'ALIPAY_PUBLIC_KEY')
        ])
    
    elif method == 'paypal':
        return all([
            hasattr(settings, 'PAYPAL_CLIENT_ID'),
            hasattr(settings, 'PAYPAL_CLIENT_SECRET')
        ])
    
    elif method == 'fps':
        return True
    
    elif method == 'cash':
        return True
    
    return False


def get_available_payment_methods():
    """获取可用的支付方式"""
    methods = []
    
    if is_payment_method_available('alipay'):
        methods.append({
            'id': 'alipay',
            'name': '支付宝',
            'description': '使用支付宝扫码支付'
        })
    
    if is_payment_method_available('paypal'):
        methods.append({
            'id': 'paypal',
            'name': 'PayPal',
            'description': '使用PayPal国际支付'
        })
    
    if is_payment_method_available('fps'):
        methods.append({
            'id': 'fps',
            'name': 'FPS转数快',
            'description': '香港快速支付系统'
        })
    
    if is_payment_method_available('cash'):
        methods.append({
            'id': 'cash',
            'name': '现金支付',
            'description': '到店现金支付'
        })
    
    return methods