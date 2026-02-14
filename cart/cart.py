# cart/cart.py - 修正版本
from django.conf import settings
from eshop.models import CoffeeItem, BeanItem, CartItem
from decimal import Decimal, InvalidOperation
import logging

logger = logging.getLogger(__name__)


class Cart:
    """購物車類 - 修正版"""
    
    def __init__(self, request):
        self.request = request
        self.session = request.session
        self.user = request.user
        
        # 從會話加載購物車
        cart_id = settings.CART_SESSION_ID
        self.cart = self.session.get(cart_id, {})
        
        # 如果是已認證用戶，從數據庫同步購物車
        if self.user.is_authenticated:
            self.sync_with_database()
    
    def sync_with_database(self):
        """同步會話購物車與數據庫購物車"""
        if not self.user.is_authenticated:
            return
        
        # 從數據庫加載購物車項目
        db_items = CartItem.objects.filter(user=self.user)
        
        # 如果有數據庫項目，使用數據庫項目
        if db_items.exists():
            self._load_from_db()
        # 如果會話中有購物車但數據庫沒有，保存到數據庫
        elif self.cart:
            self._save_to_db()
    
    def _load_from_db(self):
        """從數據庫加載購物車"""
        if not self.user.is_authenticated:
            return
        
        db_items = CartItem.objects.filter(user=self.user)
        self.cart = {}
        
        # 批量獲取產品
        coffee_ids = []
        bean_ids = []
        
        for item in db_items:
            if item.product_type == 'coffee':
                coffee_ids.append(item.product_id)
            elif item.product_type == 'bean':
                bean_ids.append(item.product_id)
        
        coffees = CoffeeItem.objects.in_bulk(coffee_ids) if coffee_ids else {}
        beans = BeanItem.objects.in_bulk(bean_ids) if bean_ids else {}
        
        for item in db_items:
            product = None
            if item.product_type == 'coffee':
                product = coffees.get(item.product_id)
            elif item.product_type == 'bean':
                product = beans.get(item.product_id)
            
            if not product:
                continue
            
            # 生成唯一鍵
            key = self._generate_item_key(
                item.product_type,
                item.product_id,
                item.cup_level,
                item.milk_level,
                item.grinding_level,
                item.weight
            )
            
            # 計算價格 - 使用修正的 _calculate_price 方法
            price = self._calculate_price(product, item.product_type, item.weight)
            
            self.cart[key] = {
                'quantity': item.quantity,
                'price': str(price),
                'name': product.name,
                'type': item.product_type,
                'image': product.image.url if product.image else '',
                'cup_level': item.cup_level,
                'milk_level': item.milk_level,
                'grinding_level': item.grinding_level,
                'weight': item.weight or '200g',
            }
    
    def _generate_item_key(self, product_type, product_id, cup_level=None, milk_level=None, grinding_level=None, weight=None):
        """生成唯一的購物車項目鍵"""
        key_parts = [product_type, str(product_id)]
        
        if product_type == 'coffee':
            if cup_level:
                key_parts.append(f'cup_{cup_level}')
            if milk_level:
                key_parts.append(f'milk_{milk_level}')
        elif product_type == 'bean':
            if grinding_level:
                key_parts.append(f'grinding_{grinding_level}')
            if weight:
                key_parts.append(f'weight_{weight}')
        
        return '_'.join(key_parts)
    
    def _calculate_price(self, product, product_type, weight=None):
        """計算商品價格 - 修正版本"""
        try:
            if product_type == 'bean' and weight:
                # 確保使用正確的 get_price 方法
                price = product.get_price(weight)
                # 確保返回 Decimal 類型
                if isinstance(price, Decimal):
                    return price
                else:
                    # 轉換為 Decimal
                    return Decimal(str(price))
            elif product_type == 'coffee':
                return product.price
            else:
                logger.warning(f"未知的商品類型: {product_type}")
                return Decimal('0')
        except Exception as e:
            logger.error(f"計算價格錯誤: {e}, product_id: {product.id}, type: {product_type}, weight: {weight}")
            # 返回安全的默認值
            return Decimal('0')
    
    def add(self, product, product_type, quantity=1, **options):
        """添加商品到購物車 - 修正版：不重複添加"""
        key = self._generate_item_key(
            product_type,
            product.id,
            options.get('cup_level'),
            options.get('milk_level'),
            options.get('grinding_level'),
            options.get('weight', '200g')
        )
        
        # 計算價格 - 使用修正的方法
        price = self._calculate_price(product, product_type, options.get('weight'))
        
        if key in self.cart:
            # 如果商品已存在，更新數量
            self.cart[key]['quantity'] += quantity
        else:
            # 否則添加新商品
            self.cart[key] = {
                'quantity': quantity,
                'price': str(price),
                'name': product.name,
                'type': product_type,
                'image': product.image.url if product.image else '',
                'cup_level': options.get('cup_level'),
                'milk_level': options.get('milk_level'),
                'grinding_level': options.get('grinding_level'),
                'weight': options.get('weight', '200g'),
            }
        
        self.save()
    
    def remove(self, item_key):
        """從購物車移除商品"""
        if item_key in self.cart:
            del self.cart[item_key]
            self.save()
    
    def update(self, item_key, quantity):
        """更新商品數量"""
        if item_key in self.cart and quantity > 0:
            self.cart[item_key]['quantity'] = quantity
            self.save()
    
    def save(self):
        """保存購物車"""
        # 保存到會話
        self.session[settings.CART_SESSION_ID] = self.cart
        self.session.modified = True
        
        # 如果是已認證用戶，同時保存到數據庫
        if self.user.is_authenticated:
            self._save_to_db()
    
    def _save_to_db(self):
        """保存購物車到數據庫"""
        if not self.user.is_authenticated:
            return
        
        # 獲取現有的數據庫項目
        existing_items = CartItem.objects.filter(user=self.user)
        existing_keys = {}
        
        for item in existing_items:
            key = self._generate_item_key(
                item.product_type,
                item.product_id,
                item.cup_level,
                item.milk_level,
                item.grinding_level,
                item.weight
            )
            existing_keys[key] = item
        
        # 更新或創建購物車項目
        for key, item_data in self.cart.items():
            parts = key.split('_')
            if len(parts) < 2:
                continue
            
            product_type = parts[0]
            product_id = int(parts[1])
            
            # 獲取選項
            cup_level = item_data.get('cup_level')
            milk_level = item_data.get('milk_level')
            grinding_level = item_data.get('grinding_level')
            weight = item_data.get('weight', '200g')
            
            # 檢查是否已存在
            if key in existing_keys:
                # 更新現有項目
                cart_item = existing_keys[key]
                cart_item.quantity = item_data['quantity']
                cart_item.save()
                del existing_keys[key]
            else:
                # 創建新項目
                CartItem.objects.create(
                    user=self.user,
                    product_type=product_type,
                    product_id=product_id,
                    quantity=item_data['quantity'],
                    cup_level=cup_level,
                    milk_level=milk_level,
                    grinding_level=grinding_level,
                    weight=weight
                )
        
        # 刪除不再存在的項目
        for key, cart_item in existing_keys.items():
            cart_item.delete()
    
    def clear(self):
        """清空購物車"""
        self.cart = {}
        self.session.pop(settings.CART_SESSION_ID, None)
        
        if self.user.is_authenticated:
            CartItem.objects.filter(user=self.user).delete()
        
        self.session.modified = True
    
    def get_total_price(self):
        """計算購物車總價格 - 修正版"""
        total = Decimal('0')
        
        for item in self.cart.values():
            try:
                price_str = item.get('price', '0')
                # 確保價格字符串格式正確
                if isinstance(price_str, str):
                    # 移除可能存在的貨幣符號
                    price_str = price_str.replace('$', '').strip()
                
                price = Decimal(str(price_str))
                quantity = int(item.get('quantity', 0))
                total += price * quantity
            except (ValueError, InvalidOperation, TypeError) as e:
                logger.error(f"價格計算錯誤: {e}, 項目: {item}")
                continue
        
        return total
    
    def __iter__(self):
        """迭代購物車項目 - 修正版：確保價格格式正確"""
        for key, item_data in self.cart.items():
            try:
                # 確保有正確的產品ID
                parts = key.split('_')
                product_id = int(parts[1]) if len(parts) > 1 else 0
                
                # 計算單項總價
                try:
                    price_str = item_data.get('price', '0')
                    # 移除可能存在的$符號
                    if isinstance(price_str, str):
                        price_str = price_str.replace('$', '').strip()
                    price = Decimal(str(price_str))
                    quantity = item_data.get('quantity', 0)
                    item_total = price * quantity
                    
                    # 格式化單價：如果是整數，返回整數格式
                    if price % 1 == 0:
                        price_str = str(int(price))
                    else:
                        price_str = str(price.quantize(Decimal('0.00')))
                    
                    # 格式化總價：如果是整數，返回整數格式
                    if item_total % 1 == 0:
                        item_total_str = str(int(item_total))
                    else:
                        item_total_str = str(item_total.quantize(Decimal('0.00')))
                except:
                    price_str = "0"
                    item_total_str = "0"
                
                yield {
                    'item_id': key,
                    'product_id': product_id,
                    'quantity': item_data['quantity'],
                    'price': price_str,  # 單價（不帶$符號）
                    'name': item_data['name'],
                    'type': item_data['type'],
                    'image': item_data['image'],
                    'cup_level': item_data.get('cup_level'),
                    'milk_level': item_data.get('milk_level'),
                    'grinding_level': item_data.get('grinding_level'),
                    'weight': item_data.get('weight'),
                    'total_price': item_total_str,  # 總價（不帶$符號）
                }
            except Exception as e:
                logger.error(f"購物車迭代錯誤: {e}")
                continue
    
    def __len__(self):
        """購物車商品總數"""
        return sum(item.get('quantity', 0) for item in self.cart.values())