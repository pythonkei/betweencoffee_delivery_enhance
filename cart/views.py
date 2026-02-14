# cart/views.py - 修正版
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST, require_GET
from django.http import JsonResponse
from django.contrib import messages
from decimal import Decimal
import json
import logging

from .cart import Cart
from eshop.models import CoffeeItem, BeanItem
from eshop.view_utils import handle_cart_error

logger = logging.getLogger(__name__)


@require_GET
def cart_detail(request):
    """購物車詳情頁面"""
    try:
        cart = Cart(request)
        
        # 設置會話中的 pending_order（如果需要）
        if len(cart) > 0:
            request.session['pending_order'] = {
                'items': cart.cart,
                'total_price': str(cart.get_total_price())
            }
            request.session.modified = True
        
        context = {
            'cart': cart,
            'total_items': len(cart),
            'total_price': cart.get_total_price(),
        }
        
        return render(request, 'cart/cart_detail.html', context)
    
    except Exception as e:
        logger.error(f"購物車詳情錯誤: {str(e)}")
        return handle_cart_error(request, e)


@require_POST
def add_to_cart(request, product_id, product_type):
    """添加商品到購物車 - 修正版"""
    try:
        # 清除快速訂單數據（如果存在）
        if 'quick_order_data' in request.session:
            del request.session['quick_order_data']
            request.session.modified = True
        
        # 獲取商品
        if product_type == 'coffee':
            product = get_object_or_404(CoffeeItem, id=product_id)
            options = {
                'cup_level': request.POST.get('cup_level', 'Medium'),
                'milk_level': request.POST.get('milk_level', 'Medium'),
            }
        elif product_type == 'bean':
            product = get_object_or_404(BeanItem, id=product_id)
            options = {
                'grinding_level': request.POST.get('grinding_level', 'Non'),
                'weight': request.POST.get('weight', '200g'),
            }
        else:
            return JsonResponse({
                'success': False,
                'message': '無效的商品類型'
            })
        
        # 獲取數量
        try:
            quantity = int(request.POST.get('quantity', 1))
            if quantity < 1:
                quantity = 1
        except (ValueError, TypeError):
            quantity = 1
        
        cart = Cart(request)
        cart.add(product, product_type, quantity, **options)
        
        # 計算單價
        if product_type == 'bean' and 'weight' in options:
            unit_price = product.get_price(options['weight'])
        else:
            unit_price = product.price
        
        return JsonResponse({
            'success': True,
            'cart_count': len(cart),
            'product_name': product.name,
            'product_price': format_price(unit_price),
            'quantity': quantity,
            'image_url': product.image.url if product.image else '',
        })
    
    except Exception as e:
        logger.error(f"添加到購物車錯誤: {str(e)}")
        return handle_cart_error(request, e)


def remove_from_cart(request, item_key):
    """從購物車移除商品 - 允許GET請求"""
    try:
        # 清除快速訂單數據（如果存在）
        if 'quick_order_data' in request.session:
            del request.session['quick_order_data']
            request.session.modified = True
        
        cart = Cart(request)
        cart.remove(item_key)
        
        # 如果購物車為空，清除 pending_order
        if len(cart) == 0 and 'pending_order' in request.session:
            del request.session['pending_order']
            request.session.modified = True
        
        messages.success(request, "商品已從購物車移除")
        return redirect('cart:cart_detail')
    
    except Exception as e:
        logger.error(f"移除購物車商品錯誤: {str(e)}")
        messages.error(request, "移除商品時發生錯誤")
        return redirect('cart:cart_detail')


@require_POST
def update_cart(request):
    """更新購物車商品數量"""
    try:
        data = json.loads(request.body)
        item_key = data.get('item_key')
        quantity = int(data.get('quantity', 1))
        
        # 驗證數量
        if quantity < 1:
            quantity = 1
        
        cart = Cart(request)
        cart.update(item_key, quantity)
        
        # 計算該項目的總價
        item_total = Decimal('0')
        if item_key in cart.cart:
            item_data = cart.cart[item_key]
            try:
                price_str = item_data.get('price', '0')
                if isinstance(price_str, str):
                    price_str = price_str.replace('$', '').strip()
                price = Decimal(str(price_str))
                item_total = price * quantity
            except:
                item_total = Decimal('0')
        
        # 返回格式化的價格（不帶$符號）
        return JsonResponse({
            'success': True,
            'item_total_price': format_price(item_total),  # 不帶$符號
            'cart_total_price': format_price(cart.get_total_price()),  # 不帶$符號
            'cart_total_items': len(cart),
        })
    
    except Exception as e:
        logger.error(f"更新購物車錯誤: {str(e)}")
        from eshop.view_utils import OrderErrorHandler
        return OrderErrorHandler.handle_json_error(str(e), status=400, error_type='cart')


@require_POST
def create_order(request):
    """從購物車創建訂單"""
    try:
        cart = Cart(request)
        
        if len(cart) == 0:
            messages.error(request, "購物車為空")
            return redirect('cart:cart_detail')
        
        # 保存購物車數據到會話
        request.session['pending_order'] = {
            'items': cart.cart,
            'total_price': str(cart.get_total_price()),
            'cart_item_count': len(cart)
        }
        
        # 清除快速訂單數據
        if 'quick_order_data' in request.session:
            del request.session['quick_order_data']
        
        request.session.modified = True
        
        return redirect('eshop:order_confirm')
    
    except Exception as e:
        logger.error(f"創建訂單錯誤: {str(e)}")
        from eshop.view_utils import handle_order_error
        return handle_order_error(request, e, 'cart:cart_detail', 'cart')


@require_GET
def cart_count(request):
    """獲取購物車商品數量（API）"""
    try:
        cart = Cart(request)
        return JsonResponse({'count': len(cart)})
    except Exception as e:
        logger.error(f"獲取購物車數量錯誤: {str(e)}")
        return JsonResponse({'count': 0})


def format_price(value):
    """格式化價格 - 確保返回純數字字符串"""
    try:
        if isinstance(value, Decimal):
            decimal_value = value
        elif isinstance(value, (int, float)):
            decimal_value = Decimal(str(value))
        else:
            # 嘗試轉換字符串
            value_str = str(value).replace('$', '').strip()
            decimal_value = Decimal(value_str)
        
        # 格式化為整數（如果沒有小數部分）
        if decimal_value == decimal_value.to_integral():
            return str(int(decimal_value))
        else:
            # 保留兩位小數，移除尾隨的0
            formatted = str(decimal_value.quantize(Decimal('0.00')))
            return formatted.rstrip('0').rstrip('.')
    except:
        return "0"