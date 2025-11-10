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
from .views import Index, About, CoffeeMenu, Coffee, BeanMenu, Bean, CoffeeMenuSearch, BeanMenuSearch, ItemInCart # use own views render index and about
# from eshop.views import OrderConfirm
from socialuser.views import profile_view
from django.http import HttpResponse


# 健康检查视图
def health_check(request):
    return HttpResponse('OK')


urlpatterns = [
    path('health/', health_check, name='health_check'),
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('', Index.as_view(), name='index'), # find own app html file
    path('profile/', include('socialuser.urls')),
    path('@<username>/', profile_view, name="profile"),

    path('eshop/', include('eshop.urls', namespace="eshop")), # Include eshop URLs, this urls.py already set up app name
    path('cart/', include('cart.urls', namespace="cart")),

    path('coffee_menu/', CoffeeMenu.as_view(), name='coffee_menu'), # coffee list
    path('coffee/<int:product_id>/', Coffee.as_view(), name='coffee'), # coffee single with id
    path('bean_menu/', BeanMenu.as_view(), name='bean_menu'), # bean list
    path('bean/<int:product_id>/', Bean.as_view(), name='bean'), # bean single with id

    # Keeping NOT use
    path('coffee_menu/search/', CoffeeMenuSearch.as_view(), name='coffee_menu_search'),
    path('bean_menu/search/', BeanMenuSearch.as_view(), name='bean_menu_search'),

    # path('restaurant/', include('restaurant.urls')), # find restaurant app html file
    path('about/', About.as_view(), name='about'),
    path('socialuser/', ItemInCart.as_view(), name='socialuser'),
]

# static sources: css and image file root
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

