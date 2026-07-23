"""betweencoffee_delivery URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

import os

from django.conf import settings
from django.conf.urls.static import static

# betweencoffee_delivery/urls.py:
from django.contrib import admin
from django.http import HttpResponse, JsonResponse
from django.urls import include, path

# from eshop.views import OrderConfirm
from socialuser.views import profile_view

from .views import Bean  # use own views render index and about
from .views import (
    About,
    BeanMenu,
    BeanMenuSearch,
    Coffee,
    CoffeeMenu,
    CoffeeMenuSearch,
    Index,
)


# 健康检查视图
def health_check(request):
    return JsonResponse({"status": "healthy", "service": "betweencoffee"})


urlpatterns = [
    path("health/", health_check, name="health_check"),
    path("admin/", admin.site.urls),
    path("accounts/", include("allauth.urls")),
    path("", Index.as_view(), name="index"),  # find own app html file
    path("__debug__/", include("debug_toolbar.urls")),
    path("profile/", include("socialuser.urls")),
    path("@<username>/", profile_view, name="user_profile"),
    path("eshop/", include("eshop.urls", namespace="eshop")),  # Include eshop URLs
    path("cart/", include("cart.urls", namespace="cart")),
    path("coffee_menu/", CoffeeMenu.as_view(), name="coffee_menu"),  # coffee list
    path(
        "coffee/<int:product_id>/", Coffee.as_view(), name="coffee"
    ),  # coffee single with id
    path("bean_menu/", BeanMenu.as_view(), name="bean_menu"),  # bean list
    path("bean/<int:product_id>/", Bean.as_view(), name="bean"),  # bean single with id
    # Keeping NOT use
    path("coffee_menu/search/", CoffeeMenuSearch.as_view(), name="coffee_menu_search"),
    path("bean_menu/search/", BeanMenuSearch.as_view(), name="bean_menu_search"),
    # restaurant app 已移除（功能已被 staff_order_management 取代）
    path("about/", About.as_view(), name="about"),
]

# static sources: css and image file root
# MEDIA_URL 已根據環境動態設置：
# - 本地開發：/media/ → Django static() helper 路由到 MEDIA_ROOT
# - 生產環境：/static/media/ → Whitenoise 從 staticfiles/media/ 提供服務
# 注意：在生產環境中（DEBUG=False），Django 的 static() helper 不會自動加入路由，
# 因此我們手動加入 media 檔案路由，確保產品圖片在 Render 上能正常顯示。
if settings.DEBUG:
    # 開發環境：直接從 media/ 目錄提供服務
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    # 生產環境：使用 staticfiles/media/（由 Dockerfile 的 build 命令複製）
    urlpatterns += static(
        settings.MEDIA_URL, document_root=os.path.join(settings.STATIC_ROOT, "media")
    )
