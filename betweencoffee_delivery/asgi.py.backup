"""
ASGI config for betweencoffee_delivery project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

# asgi.py - 修正版本
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
    from channels.security.websocket import AllowedHostsOriginValidator
    
    # 延迟导入routing，避免循环导入
    def get_websocket_router():
        import eshop.routing
        return eshop.routing.websocket_urlpatterns
    
    application = ProtocolTypeRouter({
        "http": django_asgi_app,
        "websocket": AllowedHostsOriginValidator(
            AuthMiddlewareStack(
                URLRouter(
                    get_websocket_router()
                )
            )
        ),
    })
    print("使用Channels ASGI应用配置")
    
except ImportError as e:
    print(f"Channels导入错误: {e}")
    print("使用标准ASGI应用")
    application = django_asgi_app
except Exception as e:
    print(f"配置ASGI应用时出错: {e}")
    print("使用标准ASGI应用")
    application = django_asgi_app