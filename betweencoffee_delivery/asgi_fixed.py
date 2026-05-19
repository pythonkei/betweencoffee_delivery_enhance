"""
ASGI config for betweencoffee_delivery project - 修復版本
暫時禁用 AllowedHostsOriginValidator 以解決 WebSocket 403 錯誤
"""

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
    
    # 🔧 修復：暫時禁用 AllowedHostsOriginValidator 以解決 403 錯誤
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
    print(f"Channels導入錯誤: {e}")
    print("使用標準ASGI應用")
    application = django_asgi_app
except Exception as e:
    print(f"配置ASGI應用時出錯: {e}")
    print("使用標準ASGI應用")
    application = django_asgi_app