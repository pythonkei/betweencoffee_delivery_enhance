# betweencoffee_delivery/middleware.py
# This middleware to handle cart merging when users log in
from django.utils.deprecation import MiddlewareMixin
from cart.cart import Cart
from django.conf import settings


class CartMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # Initialize cart early in the request cycle
        request.cart = Cart(request)
        
    def process_response(self, request, response):
        # Handle cart merging after login
        if hasattr(request, 'user') and request.user.is_authenticated:
            cart = getattr(request, 'cart', None)
            if cart and hasattr(cart, 'merge_with_user_cart'):
                cart.merge_with_user_cart(request)
        return response



class AdminSessionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 检查是否访问管理员后台
        if request.path.startswith('/admin/'):
            # 为管理员后台使用不同的会话cookie名称
            request.session.cookie_name = 'admin_sessionid'
            request.session.cookie_path = '/admin/'
            
            # 同样处理CSRF cookie
            if hasattr(request, 'csrf_cookie_name'):
                request.csrf_cookie_name = 'admin_csrftoken'
                request.csrf_cookie_path = '/admin/'
        
        response = self.get_response(request)
        
        # 确保响应中也使用正确的cookie设置
        if request.path.startswith('/admin/'):
            for cookie in response.cookies:
                if cookie == 'sessionid':
                    response.cookies[cookie]['path'] = '/admin/'
                elif cookie == 'csrftoken':
                    response.cookies[cookie]['path'] = '/admin/'
        
        return response