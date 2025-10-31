'''
from django.shortcuts import render
from django.views import View
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.utils.timezone import datetime
from eshop.models import OrderModel



# restaurant views.py for :
# 員工群組內的帳戶才可以查看頁面。我們還將建立一個儀表板，其中顯示每日總收入、每日訂單總數以及當天所有訂單的清單
class Dashboard(LoginRequiredMixin, UserPassesTestMixin, View):

    def get(self, request, *args, **kwargs):
    # UserPassesTestMixin: 確保請求中的使用者已登錄
    # LoginRequiredMixin: 檢查請求
    # 獲取從當前日期開始的所有訂單
        today = datetime.today()
        orders = OrderModel.objects.filter(
            created_on__year=today.year, created_on__month=today.month, created_on__day=today.day)

        # loop through the orders and add the price value, check if order is not delivery
        undelivery_orders = []
        total_revenue = 0

        # 將每個訂單的價格加起來, 以獲得當天迄今為止的總收入
        for order in orders:
            total_revenue += order.price

            # 只有今天尚未發貨的訂單, 會顯示在dashboard表格中
            if not order.is_delivery:
                undelivery_orders.append(order)

        # pass total number of orders and total revenue into template
        # 將context内data with variable, 放入dashboard.html的模板
        context = {
            'orders': undelivery_orders,
            'total_revenue': total_revenue,
            'total_orders': len(orders)
        }
        return render(request, 'restaurant/dashboard.html', context)

    def test_func(self):
        return self.request.user.groups.filter(name='Staff').exists()
        # 如果確定是 Staff群組 傳回 true, 它將允許使用者查看儀表板, 傳回 false, 傳回 403 錯誤



# 確保只有使用員工帳戶登入的使用者才能存取該頁面
class OrderDetails(LoginRequiredMixin, UserPassesTestMixin, View):
    
    def get(self, request, pk, *args, **kwargs):
        order = OrderModel.objects.get(pk=pk)
        context = {
            'order': order
        }
        return render(request, 'restaurant/order_details.html', context)


    # 從url中取得pk，並將is_delivery設定為True, 然後我們保存物件並渲染order_details.html, then 單擊按鈕後訂單已發貨
    def post(self, request, pk, *args, **kwargs):
        order = OrderModel.objects.get(pk=pk)
        order.is_delivery = True
        order.save()

        context = {
            'order': order
        }
        return render(request, 'restaurant/order_details.html', context)

    def test_func(self):
        return self.request.user.groups.filter(name='Staff').exists()

'''