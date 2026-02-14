'''
*args, **kwargs 語法使用 :

可以在同一個函數定義中同時使用兩者，但*args必須在之前出現**kwargs。
您也可以在呼叫函數時使用*和語法。**例如：
>>> def print_three_things(a, b, c):
...     print( 'a = {0}, b = {1}, c = {2}'.format(a,b,c))
...
>>> mylist = ['aardvark', 'baboon', 'cat']
>>> print_three_things(*mylist)
a = aardvark, b = baboon, c = cat

正如您在這種情況下看到的，它會獲取項目清單（或元組）並將其解包。透過這種方式
它將它們與函數中的參數進行匹配。當然，您可以*在函數定義和函數呼叫中同時擁有它們。
'''

# betweencoffee_delivery/views.py
from django.shortcuts import render, get_object_or_404
from django.views import View
from django.db.models import Q
from eshop.models import CoffeeItem, BeanItem
from cart.cart import Cart  # Import the Cart class



# 處理index, about HTTP 請求所發生的情況
# 當使用者向伺服器發送 GET 請求時渲染 HTML template模板
class Index(View): 
    def get(self, request, *args, **kwargs):
        shop_hot_coffees = CoffeeItem.objects.filter(
            is_shop_hot_item=True, 
            is_published=True
        )[:4]
        
        # 简化：上下文处理器已经处理了cart，这里不需要重复
        context = {
            'shop_hot_coffees': shop_hot_coffees,
        }
        return render(request, 'betweencoffee_delivery/index.html', context)



# List out coffee item
class CoffeeMenu(View):
    def get(self, request, *args, **kwargs):
        coffee_menu = CoffeeItem.objects.all()
        cart = Cart(request)  # Initialize the cart

        context = {
            'coffee_menu': coffee_menu,
            'cart': cart,  # keep cart count fn
        }
        return render (request, 'betweencoffee_delivery/coffee_menu.html', context)


class Coffee(View):
    def get(self, request, product_id, *args, **kwargs):
        coffee = get_object_or_404(CoffeeItem, id=product_id)
        cart = Cart(request)  # Initialize the cart
        
        context = {
            'coffee' : coffee,
            'cart': cart,  # Add the cart to the context
        }
        return render(request, 'betweencoffee_delivery/coffee.html', context)
    

# List out bean item
class BeanMenu(View):
    def get(self, request, *args, **kwargs):
        bean_items = BeanItem.objects.all()
        cart = Cart(request)  # Initialize the cart

        context = {
            'bean_items': bean_items,
            'cart': cart,  # keep cart count fn
        }
        return render (request, 'betweencoffee_delivery/bean_menu.html', context)
    

class Bean(View):
    def get(self, request, product_id, *args, **kwargs):
        bean = get_object_or_404(BeanItem, id=product_id)
        cart = Cart(request)  # Initialize the cart

        context = {
            'bean' : bean,
            'cart': cart,  # keep cart count fn
        }
        return render(request, 'betweencoffee_delivery/bean.html', context)





# Keeping NOT use
class CoffeeMenuSearch(View):
    def get(self, request, *args, **kwargs):
        query = self.request.GET.get('q')
        # # 提供Search 搜尋特定的項目, 使用below過濾任何部分匹配結果
        search_items = CoffeeItem.objects.filter(
            Q(name__icontains = query) |
            Q(price__icontains = query) |
            Q(description__icontains = query)
        )

        context = {
            'search_items' : search_items
        }
        return render(request, 'betweencoffee_delivery/coffee_menu.html', context)


class BeanMenuSearch(View):
    def get(self, request, *args, **kwargs):
        query = self.request.GET.get('q')
        # 使用below過濾任何部分匹配結果
        search_items = CoffeeItem.objects.filter(
            Q(name__icontains = query) |
            Q(price__icontains = query) |
            Q(description__icontains = query)
        )

        context = {
            'search_items' : search_items
        }
        return render(request, 'betweencoffee_delivery/bean_menu.html', context)


class About(View):
    def get(self, request, *args, **kwargs):
        cart = Cart(request)  # Initialize the cart
        
        context = {
            'cart': cart,  # keep cart count fn
        }
        return render (request, 'betweencoffee_delivery/about.html', context)
    

class ItemInCart(View):
    def get(self, request, *args, **kwargs):
        cart = Cart(request)  # Initialize the cart
        
        context = {
            'cart': cart,  # keep cart count into page
        }
        return render (request, '/socialuser/login.html', context)