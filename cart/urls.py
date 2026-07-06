# cart/urls.py
from django.urls import path
from . import views

app_name = 'cart'

urlpatterns = [
    path('', views.cart_detail, name='cart_detail'),
    path('add/<int:product_id>/<str:product_type>/', views.add_to_cart, name='add_to_cart'),
    path('remove/<str:item_key>/', views.remove_from_cart, name='remove_from_cart'),
    path('count/', views.cart_count, name='cart_count'),
    path('update_cart/', views.update_cart, name='update_cart'),
    path('clear/', views.clear_cart, name='clear_cart'),
    path('create_order/', views.create_order, name='create_order'),
    path('checkout/', views.checkout_page, name='checkout_page'),
    path('create_order_ajax/', views.create_order_ajax, name='create_order_ajax'),
]
