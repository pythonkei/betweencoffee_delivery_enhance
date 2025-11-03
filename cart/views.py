# cart/views.py
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from .cart import Cart
from eshop.models import CoffeeItem, BeanItem
from eshop.views import OrderConfirm
from django.urls import reverse
from decimal import Decimal
import json



# Initial Rendeing From menu_item.html add to cart_detail.html
def cart_detail(request):
    cart = Cart(request)
    print(cart.cart)  # Debug: Print cart contents
    return render(request, 'cart/cart_detail.html', {'cart': cart})


def format_price(value):
    """Format price to remove trailing .00"""
    if isinstance(value, Decimal):
        return f"{value:.2f}".rstrip('0').rstrip('.')
    return f"{float(value):.2f}".rstrip('0').rstrip('.')


# Ensure that each option combination is treated as a unique or new item.
# cart/views.py
@require_POST
def add_to_cart(request, product_id, product_type):
    print(f"收到添加购物车请求: 产品ID={product_id}, 类型={product_type}")
    
    try:
        if product_type == 'coffee':
            product = get_object_or_404(CoffeeItem, id=product_id)
            cup_level = request.POST.get('cup_level', 'Medium')
            milk_level = request.POST.get('milk_level', 'Medium')
            grinding_level = None
            weight = None
            print(f"咖啡选项 - 杯量: {cup_level}, 奶量: {milk_level}")
        elif product_type == 'bean':
            product = get_object_or_404(BeanItem, id=product_id)
            grinding_level = request.POST.get('grinding_level', 'Non')
            weight = request.POST.get('weight', '200g')
            cup_level = None
            milk_level = None
            print(f"咖啡豆选项 - 研磨: {grinding_level}, 重量: {weight}")
        else:
            print(f"无效的产品类型: {product_type}")
            return JsonResponse({
                'success': False, 
                'message': '无效的产品类型'
            })

        quantity = int(request.POST.get('quantity', 1))
        print(f"数量: {quantity}")

        cart = Cart(request)
        cart.add(product, product_type, quantity=quantity, cup_level=cup_level, 
                milk_level=milk_level, grinding_level=grinding_level, weight=weight)

        # 计算单价
        if product_type == 'bean' and weight:
            unit_price = product.get_price(weight)
        else:
            unit_price = product.price

        print(f"添加到购物车成功: {product.name}")

        return JsonResponse({
            'success': True,
            'cart_count': len(cart),
            'product_name': product.name,
            'product_price': format_price(unit_price),
            'quantity': quantity,
            'image_url': product.image.url if product.image else ''
        })

    except Exception as e:
        print(f"添加到购物车错误: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'服务器错误: {str(e)}'
        })




def remove_from_cart(request, product_id):
    cart = Cart(request)
    cart.remove(product_id)
    return redirect('cart:cart_detail')



@require_POST
def cart_add_base(request):
    data = json.loads(request.body)
    item_id = data.get('item_id')
    item_type = data.get('item_type')
    quantity = int(data.get('quantity', 1))
    
    try:
        if item_type == 'coffee':
            item = CoffeeItem.objects.get(pk=item_id)
        elif item_type == 'bean':
            item = BeanItem.objects.get(pk=item_id)
        else:
            return JsonResponse({'success': False, 'message': '無效的商品類型'})
        
        cart = Cart(request)
        cart.add(item=item, quantity=quantity)
        return JsonResponse({
            'success': True,
            'cart_count': len(cart)
        })
        
    except (CoffeeItem.DoesNotExist, BeanItem.DoesNotExist):
        return JsonResponse({'success': False, 'message': '找不到商品'})



# Count by Json update and Response
def cart_count(request):
    cart = Cart(request)
    return JsonResponse({'count': len(cart)})



# Update by json cal quantity and total price
# 當使用者改變商品數量時，update_cart 視圖會更新會話資料並重新計算總數
# 會話資料在頁面重新載入和導航時仍然存在，從而確保購物車保持一致。
@require_POST 
def update_cart(request):
    data = json.loads(request.body)
    item_key = data.get('item_key')
    quantity = int(data.get('quantity'))

    cart = Cart(request)
    cart.update(item_key, quantity)

    return JsonResponse({
        'success': True,
        'item_total_price': format_price(Decimal(cart.cart[item_key]['total_price'])),
        'cart_total_price': format_price(cart.get_total_price()),
        'cart_total_items': cart.__len__(),
    })



@require_POST
def create_order(request):
    cart = Cart(request)
    if not cart:
        messages.error(request, "Your cart is empty")
        return redirect('cart:cart_detail')
    
    # Prepare cart data for session
    cart_data = {
        'items': cart.cart,
        'total_price': str(cart.get_total_price())
    }
    
    # Store cart data in session
    request.session['pending_order'] = cart_data
    return redirect('eshop:order_confirm')
