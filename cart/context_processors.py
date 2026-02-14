# cart/context_processors.py - 簡化版
from .cart import Cart

def cart_count(request):
    """購物車上下文處理器"""
    try:
        cart = Cart(request)
        return {
            'cart_count': len(cart),
        }
    except Exception:
        return {'cart_count': 0}