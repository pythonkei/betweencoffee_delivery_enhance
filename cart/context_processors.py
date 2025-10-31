from .cart import Cart
from django.conf import settings

def cart_count(request):
    try:
        cart = Cart(request)
        return {'cart_count': len(cart)}
    except Exception as e:
        # If cart initialization fails, return empty cart count
        request.session[settings.CART_SESSION_ID] = {}
        return {'cart_count': 0}