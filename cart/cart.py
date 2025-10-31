# cart/cart.py:
from django.contrib.sessions.models import Session
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from eshop.models import CoffeeItem, BeanItem, CartItem
from django.http import JsonResponse
import json
from decimal import Decimal
import logging
logger = logging.getLogger(__name__)


# Inital cart in session processing and handle both guest and authenticated users
class Cart:
    def __init__(self, request):
        self.session = request.session
        self.request = request
        cart = self.session.get(settings.CART_SESSION_ID, {})
        
        # Initialize cart as empty dict if not present
        if not isinstance(cart, dict):
            cart = {}

        # Store user ID if authenticated
        if request.user.is_authenticated:
            self.user_id = request.user.id
            # Load cart from database
            self.load_from_db()
            # Migrate guest cart to user cart if exists
            if 'guest_cart' in self.session:
                self.migrate_guest_cart()
        else:
            self.user_id = None
            self.cart = cart


    def load_from_db(self):
        """Load cart items from database for authenticated users"""
        db_items = CartItem.objects.filter(user_id=self.user_id)
        self.cart = {}
        
        # Get all product IDs
        coffee_ids = [item.product_id for item in db_items if item.product_type == 'coffee']
        bean_ids = [item.product_id for item in db_items if item.product_type == 'bean']
        
        # Fetch all products in bulk
        coffees = CoffeeItem.objects.in_bulk(coffee_ids)
        beans = BeanItem.objects.in_bulk(bean_ids)
        
        for item in db_items:
            product = None
            if item.product_type == 'coffee':
                product = coffees.get(item.product_id)
            elif item.product_type == 'bean':
                product = beans.get(item.product_id)
            
            if not product:
                continue  # Skip if product not found
                
            # Recreate the same key format used in session
            if item.product_type == 'coffee':
                key = f"coffee_{item.product_id}_cup_{item.cup_level}_milk_{item.milk_level}"
            elif item.product_type == 'bean':
                # 包含重量信息
                key = f"bean_{item.product_id}_grinding_{item.grinding_level}_weight_{item.weight}"
            else:
                key = f"{item.product_type}_{item.product_id}"

            # 计算价格
            if item.product_type == 'bean':
                # 使用 CartItem 中的重量信息
                weight = item.weight if item.weight else '200g'
                price = str(product.get_price(weight))
            else:
                price = str(product.price)
                
            self.cart[key] = {
                'quantity': item.quantity,
                'price': price,
                'name': product.name,
                'type': item.product_type,
                'image': product.image.url if product.image else '',
                'cup_level': item.cup_level,
                'milk_level': item.milk_level,
                'grinding_level': item.grinding_level,
                'weight': item.weight  # 添加重量信息
            }


    def migrate_guest_cart(self):
        """Migrate guest cart items to authenticated user"""
        guest_cart = self.session.get('guest_cart', {})
        
        for key, item_data in guest_cart.items():
            # Add each item to database
            parts = key.split('_')
            product_type = parts[0]
            product_id = int(parts[1])
            
            # Extract options based on product type
            cup_level = item_data.get('cup_level')
            milk_level = item_data.get('milk_level')
            grinding_level = item_data.get('grinding_level')
            weight = item_data.get('weight')  # 获取重量信息
            
            # Create or update cart item in DB
            CartItem.objects.update_or_create(
                user_id=self.user_id,
                product_type=product_type,
                product_id=product_id,
                cup_level=cup_level,
                milk_level=milk_level,
                grinding_level=grinding_level,
                weight=weight,
                defaults={'quantity': item_data['quantity']}
            )
            
            # Add to current cart
            self.cart[key] = item_data
        
        # Clear guest cart from session
        del self.session['guest_cart']
        self.session.modified = True


    def save(self):
        self.session[settings.CART_SESSION_ID] = self.cart
        
        if self.user_id:
            # Save to database for authenticated users
            self.save_to_db()
            
            # Remove guest cart if exists
            if 'guest_cart' in self.session:
                del self.session['guest_cart']
        else:
            # Store guest cart separately
            self.session['guest_cart'] = self.cart
            
        self.session.modified = True


    def save_to_db(self):
        """Save cart items to database for authenticated users"""
        # First delete all existing cart items
        CartItem.objects.filter(user_id=self.user_id).delete()
        
        # Then save current cart items
        for key, item_data in self.cart.items():
            parts = key.split('_')
            product_type = parts[0]
            product_id = int(parts[1])
            
            CartItem.objects.create(
                user_id=self.user_id,
                product_type=product_type,
                product_id=product_id,
                quantity=item_data['quantity'],
                cup_level=item_data.get('cup_level'),
                milk_level=item_data.get('milk_level'),
                grinding_level=item_data.get('grinding_level'),
                weight=item_data.get('weight')
            )
    

    def clear(self):
        # Clear from database if authenticated
        if self.user_id:
            CartItem.objects.filter(user_id=self.user_id).delete()
            
        # Clear from session
        self.session[settings.CART_SESSION_ID] = {}
        if 'guest_cart' in self.session:
            del self.session['guest_cart']
        self.session.modified = True


    def __iter__(self):
        if not hasattr(self, 'cart') or not isinstance(self.cart, dict):
            self.cart = {}
        for item_id, item_data in self.cart.items():
            # Split the item_id to extract product ID
            parts = item_id.split('_')  # Split by underscores
            product_id = int(parts[1])  # Convert to integer

            yield {
                'item_id': item_id,
                'product_id': product_id,
                'quantity': item_data['quantity'],
                'price': item_data['price'],
                'name': item_data['name'],
                'type': item_data['type'],
                'image': item_data['image'],
                'cup_level': item_data.get('cup_level'),  # For coffee items ready select and keep track user action
                'milk_level': item_data.get('milk_level'),  # For coffee items ready select and keep track and keep track user action
                'grinding_level': item_data.get('grinding_level'),  # For bean items ready select and keep track user action
                'total_price': float(item_data['price']) * item_data['quantity'],
            }

    def __len__(self):
        return sum(item['quantity'] for item in self.cart.values())



    # 在add方法中修改bean项目的处理逻辑
    def add(self, product, product_type, quantity=1, cup_level=None, milk_level=None, grinding_level=None, weight=None):
        # 生成唯一的产品ID，基于产品类型、ID和所选选项
        if product_type == 'coffee':
            product_id = f"{product_type}_{product.id}_cup_{cup_level}_milk_{milk_level}"
        elif product_type == 'bean':
            # 添加重量选项到产品ID
            product_id = f"{product_type}_{product.id}_grinding_{grinding_level}_weight_{weight}"
        else:
            product_id = f"{product_type}_{product.id}"

        if product_id not in self.cart:
            # 根据重量获取价格（如果是咖啡豆）
            if product_type == 'bean' and weight:
                price = str(product.get_price(weight))
            else:
                # 对于咖啡或其他产品，使用默认价格
                price = str(product.price)
                
            self.cart[product_id] = {
                'quantity': 0,
                'price': price,
                'name': product.name,
                'type': product_type,
                'image': product.image.url if product.image else '',
                'cup_level': cup_level,
                'milk_level': milk_level,
                'grinding_level': grinding_level,
                'weight': weight,  # 存储重量信息
            }
        self.cart[product_id]['quantity'] += quantity
        self.save()

    def remove(self, product_id):
        if product_id in self.cart:
            del self.cart[product_id]
            self.save()


    def update(self, item_key, quantity):
        if item_key in self.cart:
            self.cart[item_key]['quantity'] = quantity
            self.cart[item_key]['total_price'] = float(self.cart[item_key]['price']) * quantity
            self.save()



    # Add method to merge carts when user logs in
    def merge_with_user_cart(self, request):
        if request.user.is_authenticated and 'guest_cart' in self.session:
            user_cart = self.session.get(settings.CART_SESSION_ID, {})
            guest_cart = self.session['guest_cart']
            
            # Merge strategy: keep guest cart items, update quantities if same item exists
            for item_id, item_data in guest_cart.items():
                if item_id in user_cart:
                    user_cart[item_id]['quantity'] += item_data['quantity']
                else:
                    user_cart[item_id] = item_data
            
            self.cart = user_cart
            del self.session['guest_cart']
            self.save()


    def get_total_price(self):
        return sum(float(item['price']) * item['quantity'] for item in self.cart.values())




# Cart fn between cart.py and Json response
@csrf_exempt
def add_to_cart(request):
    if request.method == 'POST':
        try:
            logger.debug(f"Raw request body: {request.body}")
            
            # Validate request body
            if not request.body:
                logger.debug("Empty request body")
                return JsonResponse({
                    'success': False,
                    'message': '請求內容為空'
                }, status=400)
            
            try:
                data = json.loads(request.body)
                logger.debug(f"Parsed JSON data: {data}")
            except json.JSONDecodeError as e:
                logger.debug(f"JSON decode error: {str(e)}")
                return JsonResponse({
                    'success': False,
                    'message': '無效的JSON格式'
                }, status=400)
            
            # Validate required fields
            if 'item_pk' not in data:
                return JsonResponse({
                    'success': False,
                    'message': 'miss item id'
                }, status=400)
            
            try:
                item_pk = int(data['item_pk'])
                quantity = int(data.get('quantity', 1))
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'message': 'invliate id'
                }, status=400)
            
            # Validate quantity
            if quantity < 1:
                return JsonResponse({
                    'success': False,
                    'message': 'Bigger than 0'
                }, status=400)
            
            # Get product
            try:
                item = get_object_or_404(CoffeeItem, id=item_pk)
            except:
                return JsonResponse({
                    'success': False,
                    'message': 'Item not find'
                }, status=404)
            
            # Update cart
            cart = request.session.get('cart', {})
            if str(item_pk) in cart:
                cart[str(item_pk)]['quantity'] += quantity
            else:
                cart[str(item_pk)] = {
                    'quantity': quantity,
                    'price': str(item.price),
                    'name': item.name,
                    'image': item.image.url if item.image else '/static/images/menu-01.png'
                }
            
            request.session['cart'] = cart
            request.session.modified = True
            
            return JsonResponse({
                'success': True, 
                'cart_total_items': sum(temp_item['quantity'] for temp_item in cart.values())
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Server Error: {str(e)}'
            }, status=500)
    
    return JsonResponse({
        'success': False,
        'message': 'POST Only'
    }, status=405)


# remove_from_cart
@csrf_exempt
def remove_from_cart(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        item_pk = str(data.get('item_pk'))
        
        cart = request.session.get('cart', {})
        if item_pk in cart:
            del cart[item_pk]
        
        request.session['cart'] = cart
        request.session.modified = True
        return JsonResponse({
            'success': True, 
            'cart_total_items': sum(temp_item['quantity'] for temp_item in cart.values())
        })
    
    return JsonResponse({'success': False}, status=400)

# end Cart fn between cart.py and Json response

