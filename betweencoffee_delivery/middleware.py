# betweencoffee_delivery/middleware.py
# This middleware to handle cart merging when users log in
import logging

from django.utils.deprecation import MiddlewareMixin

from cart.cart import Cart

logger = logging.getLogger(__name__)


class CartMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # Initialize cart early in the request cycle
        try:
            request.cart = Cart(request)
        except Exception as e:
            logger.warning(f"Cart initialization failed (non-critical): {e}")
            # 創建一個空的購物車對象作為後備
            from cart.cart import Cart as CartClass

            # 使用最小初始化，避免數據庫查詢
            request.cart = CartClass.__new__(CartClass)
            request.cart.request = request
            request.cart.session = request.session
            request.cart.user = request.user
            request.cart.cart = {}

    def process_response(self, request, response):
        # Handle cart merging after login
        if hasattr(request, "user") and request.user.is_authenticated:
            cart = getattr(request, "cart", None)
            if cart and hasattr(cart, "merge_with_user_cart"):
                cart.merge_with_user_cart(request)
        return response


class AdminSessionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 检查是否访问管理员后台
        if request.path.startswith("/admin/"):
            # 为管理员后台使用不同的会话cookie名称
            request.session.cookie_name = "admin_sessionid"
            request.session.cookie_path = "/admin/"

            # 同样处理CSRF cookie
            if hasattr(request, "csrf_cookie_name"):
                request.csrf_cookie_name = "admin_csrftoken"
                request.csrf_cookie_path = "/admin/"

        response = self.get_response(request)

        # 确保响应中也使用正确的cookie设置
        if request.path.startswith("/admin/"):
            for cookie in response.cookies:
                if cookie == "sessionid":
                    response.cookies[cookie]["path"] = "/admin/"
                elif cookie == "csrftoken":
                    response.cookies[cookie]["path"] = "/admin/"

        return response


# DebugMiddleware 已移除（2026-08-01 安全審查）
# 原因：會記錄訂單 POST 資料（電話/地址/個資）與完整 Session 內容到日誌
# 如需除錯，請在本地開發環境自行加回，並確保生產環境不啟用
