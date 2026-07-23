# eshop/models/cart_item.py
"""
購物車項目模型模組。
包含 CartItem 模型，用於存儲用戶的購物車商品。
"""

import json
import logging
from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError

from .base import get_image_url

logger = logging.getLogger(__name__)


class CartItem(models.Model):
    """購物車項目模型"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cart_items'
    )
    product_type = models.CharField(max_length=10)  # 'coffee' or 'bean'
    product_id = models.PositiveIntegerField()
    quantity = models.PositiveIntegerField(default=1)
    cup_level = models.CharField(max_length=10, blank=True, null=True)
    milk_level = models.CharField(max_length=10, blank=True, null=True)
    grinding_level = models.CharField(max_length=10, blank=True, null=True)
    weight = models.CharField(max_length=10, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'product_type', 'product_id', 'cup_level', 'milk_level', 'grinding_level', 'weight')
        
    def __str__(self):
        return f"{self.user.username}'s {self.product_type} item"

    def get_items(self):
        """Parse the JSON string and return the list of items with numeric values."""
        # 延遲導入以避免循環依賴
        from .shop_items import CoffeeItem, BeanItem

        if isinstance(self.items, str):
            items = json.loads(self.items)
        else:
            items = self.items  # If it's already a list
            
        # Convert prices to floats and ensure image URLs are present
        for item in items:
            try:
                # 修復：確保 price 鍵存在
                if 'price' not in item:
                    # 嘗試從產品獲取價格
                    try:
                        if item['type'] == 'coffee':
                            product = CoffeeItem.objects.get(id=item['id'])
                            item['price'] = float(product.price)
                        elif item['type'] == 'bean':
                            product = BeanItem.objects.get(id=item['id'])
                            # 根據重量獲取價格
                            weight = item.get('weight', '200g')
                            item['price'] = float(product.get_price(weight))
                        else:
                            item['price'] = 0.0
                    except (CoffeeItem.DoesNotExist, BeanItem.DoesNotExist, KeyError):
                        item['price'] = 0.0
                else:
                    # Convert price to float
                    item['price'] = float(item['price'])
                
                # 確保 quantity 存在
                if 'quantity' not in item:
                    item['quantity'] = 1
                
                # Calculate total price if not present
                if 'total_price' not in item:
                    item['total_price'] = item['price'] * item['quantity']
                else:
                    item['total_price'] = float(item['total_price'])
                
                # Ensure image URL exists
                if 'image' not in item:
                    # Try to get image from product
                    try:
                        if item['type'] == 'coffee':
                            product = CoffeeItem.objects.get(id=item['id'])
                            if product.image and hasattr(product.image, 'name') and product.image.name:
                                item['image'] = get_image_url(product.image, '/static/images/default-coffee.png')
                            else:
                                item['image'] = '/static/images/default-coffee.png'
                        elif item['type'] == 'bean':
                            product = BeanItem.objects.get(id=item['id'])
                            if product.image and hasattr(product.image, 'name') and product.image.name:
                                item['image'] = get_image_url(product.image, '/static/images/default-bean.png')
                            else:
                                item['image'] = '/static/images/default-bean.png'
                        else:
                            product = None
                            item['image'] = '/static/images/default-product.png'
                    except:
                        item['image'] = '/static/images/default-product.png'
            except (TypeError, ValueError, KeyError) as e:
                print(f"Error processing cart item: {item}, error: {e}")
                item['price'] = 0.0
                item['total_price'] = 0.0
                item['image'] = '/static/images/default-product.png'
                if 'quantity' not in item:
                    item['quantity'] = 1
        return items

    def get_items_display(self):
        """Format the items for display."""
        items = self.get_items()
        display_text = []
        for item in items:
            raw_price = item['price']
            if isinstance(raw_price, float):
                price_str = f"{raw_price:.2f}"
            else:
                price_str = str(raw_price)
                
            if '.00' in price_str:
                price_str = price_str.replace('.00', '')
                
            item_text = f"{item['name']} (Qty: {item['quantity']}, Price: ${price_str})"
            if item['type'] == 'coffee':
                item_text += f", Cup: {item['cup_level']}, Milk: {item['milk_level']}"
            elif item['type'] == 'bean':
                item_text += f", Grinding: {item['grinding_level']}"
            display_text.append(item_text)
        return "\n".join(display_text)
    
    def clean(self):
        """Validate the items field before saving."""
        if not isinstance(self.items, (str, list)):
            raise ValidationError("Items must be a JSON string or a list.")
        if isinstance(self.items, list):
            self.items = json.dumps(self.items)  # Convert list to JSON string

    class Meta:
        verbose_name_plural = "Order"
