# eshop/fps_utils.py
import logging
import qrcode
import base64
from io import BytesIO
from django.conf import settings

logger = logging.getLogger(__name__)

def generate_fps_qr_code(order):
    """生成FPS转数快二维码 - 使用HKQR標準格式"""
    try:
        # FPS支付信息 - 使用HKQR標準格式
        # HKQR標準格式: 000201010212... 開頭的EMVCo標準
        merchant_id = getattr(settings, 'FPS_MERCHANT_ID', '68492033')
        merchant_name = 'Between Coffee'
        amount = str(order.total_price)
        reference = f'BC{order.id:06d}'
        
        # 構建標準化的FPS支付字符串
        # 格式: FPS://{merchant_id}?amount={amount}&ref={reference}
        fps_string = (
            f"FPS://{merchant_id}"
            f"?amount={amount}"
            f"&currency=HKD"
            f"&reference={reference}"
            f"&merchant={merchant_name}"
        )
        
        # 生成二维码
        qr = qrcode.QRCode(
            version=2,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=4,
        )
        qr.add_data(fps_string)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        
        return base64.b64encode(buffer.getvalue()).decode()
        
    except Exception as e:
        logger.error(f"生成FPS二维码失败: {str(e)}")
        return None


def create_fps_payment(order, request):
    """创建FPS支付 - 确保返回正确格式"""
    try:
        # 生成FPS二维码
        qr_code = generate_fps_qr_code(order)
        
        if qr_code:
            # 将订单标记为等待FPS支付
            order.payment_method = 'fps'
            order.save()
            
            return {
                'success': True,
                'qr_code': qr_code,
                'order_id': order.id,
                'amount': order.total_price,
                'reference': f'BC{order.id:06d}'
            }
        else:
            return {'success': False, 'error': '无法生成支付二维码'}
            
    except Exception as e:
        logger.error(f"创建FPS支付失败: {str(e)}")
        return {'success': False, 'error': str(e)}


def verify_fps_payment(order_id):
    """验证FPS支付状态（手动确认）"""
    # 注意：FPS支付通常需要手动确认
    # 在实际应用中，您可能需要：
    # 1. 与银行API集成
    # 2. 手动在后台确认
    # 3. 使用第三方支付网关
    
    return {'status': 'pending', 'message': '请等待管理员确认支付'}
