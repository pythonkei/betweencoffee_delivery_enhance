'''betweencoffee_delivery URL Configuration

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
'''

# betweencoffee_delivery/urls.py:
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from .views import Index, About, CoffeeMenu, Coffee, BeanMenu, Bean, CoffeeMenuSearch, BeanMenuSearch # use own views render index and about
# from eshop.views import OrderConfirm
from socialuser.views import profile_view
from django.http import HttpResponse, JsonResponse

# 導入測試視圖
from eshop.views_test import test_smart_allocation_view, test_websocket_monitoring_view


# 健康检查视图
def health_check(request):
    return JsonResponse({"status": "healthy", "service": "betweencoffee"})


urlpatterns = [
    path('health/', health_check, name='health_check'),
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('', Index.as_view(), name='index'),  # find own app html file
    path('__debug__/', include('debug_toolbar.urls')),
    path('profile/', include('socialuser.urls')),
    path('profile/', include('socialuser.urls_enhanced')),  # 添加增強會員系統URL
    path('@<username>/', profile_view, name="user_profile"),

    path('eshop/', include('eshop.urls', namespace="eshop")),  # Include eshop URLs
    path('cart/', include('cart.urls', namespace="cart")),

    path('coffee_menu/', CoffeeMenu.as_view(), name='coffee_menu'),  # coffee list
    path('coffee/<int:product_id>/', Coffee.as_view(), name='coffee'),  # coffee single with id
    path('bean_menu/', BeanMenu.as_view(), name='bean_menu'),  # bean list
    path('bean/<int:product_id>/', Bean.as_view(), name='bean'),  # bean single with id

    # Keeping NOT use
    path('coffee_menu/search/', CoffeeMenuSearch.as_view(), name='coffee_menu_search'),
    path('bean_menu/search/', BeanMenuSearch.as_view(), name='bean_menu_search'),

    # path('restaurant/', include('restaurant.urls')),  # find restaurant app html file
    path('about/', About.as_view(), name='about'),
    
    # 智能分配系統測試頁面
    path('test_smart_allocation.html', test_smart_allocation_view, name='test_smart_allocation'),
    
    # WebSocket監控系統測試頁面
    path('test_websocket_monitoring.html', test_websocket_monitoring_view, name='test_websocket_monitoring'),
]

# static sources: css and image file root
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

