'''
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from .views import Dashboard, OrderDetails

urlpatterns = [
    path('dashboard/', Dashboard.as_view(), name='dashboard'),
    path('order/<int:pk>/', OrderDetails.as_view(), name='order_details'),
    # 將 pk(id) 傳遞到 url 中, 取得 OrderModel object
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
'''