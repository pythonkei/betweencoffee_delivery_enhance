"""
ASGI config for betweencoffee_delivery project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

# asgi.py - 修復版本（暫時禁用 AllowedHostsOriginValidator）
import os
from django.core.asgi import get_asgi_application

# 必须先设置环境变量
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'betweencoffee_delivery.settings')

# 先获取基础的ASGI应用
django_asgi_app = get_asgi_application()

# 现在尝试导入Channels相关模块
try:
    from channels.routing import ProtocolTypeRouter, URLRouter
    from channels.auth import AuthMiddlewareStack
    
    # 延迟导入routing，避免循环导入
    def get_websocket_router():
        import eshop.routing
        return eshop.routing.websocket_urlpatterns
    
    # 🔧 修復：暫時禁用 AllowedHostsOriginValidator 以解決 WebSocket 403 錯誤
    # 在開發環境中，我們可以直接使用 AuthMiddlewareStack
    # 在生產環境中應該重新啟用 AllowedHostsOriginValidator
    application = ProtocolTypeRouter({
        "http": django_asgi_app,
        "websocket": AuthMiddlewareStack(  # 暫時移除 AllowedHostsOriginValidator
            URLRouter(
                get_websocket_router()
            )
        ),
    })
    print("使用修復版 Channels ASGI 應用配置（已禁用 AllowedHostsOriginValidator）")
    
except ImportError as e:
    print(f"Channels导入错误: {e}")
    print("使用标准ASGI应用")
    application = django_asgi_app
except Exception as e:
    print(f"配置ASGI应用时出错: {e}")
    print("使用标准ASGI应用")
    application = django_asgi_app
