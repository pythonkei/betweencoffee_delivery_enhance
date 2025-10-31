# eshop/alipay_utils.py:
from alipay import AliPay
from django.conf import settings
import os
import logging
from urllib.parse import quote, unquote

logger = logging.getLogger(__name__)


def get_alipay_client():
    """初始化支付宝客户端"""
    # Ensure the keys are properly formatted without extra whitespace
    private_key = settings.ALIPAY_APP_PRIVATE_KEY.strip()
    public_key = settings.ALIPAY_PUBLIC_KEY.strip()
    
    alipay = AliPay(
        appid=settings.ALIPAY_APP_ID,
        app_private_key_string=private_key,
        alipay_public_key_string=public_key,
        sign_type=settings.ALIPAY_SIGN_TYPE,
        debug=settings.ALIPAY_DEBUG
    )
    return alipay


def create_alipay_payment(order, request):
    """创建支付宝支付订单"""
    try:
        alipay = get_alipay_client()
        
        # 生成商品标题（使用新函数）
        subject = generate_order_subject(order)
        
        # 生成支付URL
        order_string = alipay.api_alipay_trade_page_pay(
            out_trade_no=str(order.id),
            total_amount=str(order.total_price),
            subject=subject,  # ← 使用新生成的标题
            return_url=settings.ALIPAY_RETURN_URL,
            notify_url=settings.ALIPAY_NOTIFY_URL
        )
        
        # 使用正确的沙箱URL
        if settings.ALIPAY_DEBUG:
            gateway = "https://openapi-sandbox.dl.alipaydev.com/gateway.do"
        else:
            gateway = "https://openapi.alipay.com/gateway.do"
            
        payment_url = f"{gateway}?{order_string}"
        return payment_url
        
    except Exception as e:
        logger.error(f"Alipay payment creation error: {str(e)}")
        raise


def generate_order_subject(order):
    """生成订单商品标题 - 显示最后一个商品和总数量"""
    try:
        # 从订单中获取商品信息
        items = order.get_items()
        
        if not items:
            return f"Between Coffee Order #{order.id}"
        
        # 获取最后一个商品（最新添加到购物车的商品）
        last_item = items[-1]
        item_name = last_item.get('name', '商品')
        
        # 计算所有商品的总数量
        total_quantity = 0
        for item in items:
            total_quantity += item.get('quantity', 1)
        
        # 如果有多个商品，显示"商品名 等X件物品"
        if len(items) > 1:
            return f"{item_name} 等{total_quantity}件物品"
        else:
            # 如果只有一件商品，显示数量和商品名
            quantity = last_item.get('quantity', 1)
            if quantity > 1:
                return f"{item_name} x{quantity}"
            else:
                return item_name
                
    except Exception as e:
        # 如果出错，使用默认标题
        logger.error(f"生成订单标题错误: {str(e)}")
        return f"Between Coffee Order #{order.id}"


def verify_alipay_notification(data):
    """验证支付宝通知"""
    try:
        # 确保正确处理编码 - 简化处理
        decoded_data = {}
        for key, value in data.items():
            if isinstance(value, str):
                # 只进行必要的URL解码
                try:
                    decoded_value = unquote(value)
                    decoded_data[key] = decoded_value
                except:
                    decoded_data[key] = value
            else:
                decoded_data[key] = value
        
        logger.debug(f"验证使用的数据: {decoded_data}")
        
        # 使用调试模式验证
        return debug_verification(decoded_data)
        
    except Exception as e:
        logger.error(f"Alipay verification error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def debug_verification(data):
    """详细的签名验证调试"""
    try:
        alipay = get_alipay_client()
        
        logger.debug("=== 支付宝签名验证调试 ===")
        
        # 1. 打印所有参数（除了签名）
        logger.debug("接收到的参数:")
        for key, value in data.items():
            if key != 'sign':
                logger.debug(f"  {key}: {repr(value)}")
        
        # 2. 检查签名是否存在
        sign = data.get('sign', '')
        if not sign:
            logger.error("缺少签名参数")
            return False
            
        logger.debug(f"签名: {sign}")
        
        # 3. 手动构建待签名字符串（模拟支付宝的验证过程）
        # 移除签名和空值参数
        verify_data = {k: v for k, v in data.items() 
                      if k not in ['sign', 'sign_type'] and v is not None and v != ''}
        
        # 按字母顺序排序
        sorted_items = sorted(verify_data.items(), key=lambda x: x[0])
        
        # 构建待签名字符串
        sign_string = '&'.join([f"{k}={v}" for k, v in sorted_items])
        logger.debug(f"待验证字符串: {repr(sign_string)}")
        
        # 4. 进行验证
        result = alipay.verify(verify_data, sign)
        
        logger.debug(f"验证结果: {result}")
        
        if not result:
            logger.error("签名验证失败的可能原因:")
            logger.error("1. 支付宝公钥不正确")
            logger.error("2. 应用公钥与私钥不匹配") 
            logger.error("3. 参数编码问题")
            logger.error("4. 签名算法不匹配")
        
        return result
        
    except Exception as e:
        logger.error(f"验证过程错误: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False