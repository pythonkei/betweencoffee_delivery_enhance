# eshop/models/cart_item.py
"""
購物車項目模型：CartItem

從 models.py 提取的購物車相關模型。
"""

import json
import logging
from django.db import models
from django.core.exceptions import ValidationError

logger = logging.getLogger(__name__)


class CartItem(models.Model):
    """購物車項目模型"""
    ITEM_TYPE_CHOICES = [
        ('coffee', '咖啡'),
        ('bean', '咖啡豆'),
    ]
    
    session_key = models.CharField(max_length=255, blank=True, null=True, db_index=True, verbose_name="Session Key")
    user = models.ForeignKey(
        'auth.User', on_delete=models.CASCADE, blank=True, null=True, verbose_name="用戶"
    )
    item_type = models.CharField(max_length=20, choices=ITEM_TYPE_CHOICES, verbose_name="商品類型")
    coffee = models.ForeignKey(
        'eshop.CoffeeItem', on_delete=models.CASCADE, blank=True, null=True, verbose_name="咖啡"
    )
    bean = models.ForeignKey(
        'eshop.BeanItem', on_delete=models.CASCADE, blank=True, null=True, verbose_name="咖啡豆"
    )
    quantity = models.PositiveIntegerField(default=1, verbose_name="數量")
    options = models.TextField(blank=True, default='{}', verbose_name="選項(JSON)")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="創建時間")
    
    def get_items(self):
        """獲取購物車項目列表（兼容舊版）"""
        items = []
        item = {
            'type': self.item_type,
            'quantity': self.quantity,
            'options': self.get_options(),
        }
        
        if self.item_type == 'coffee' and self.coffee:
            item['id'] = self.coffee.id
            item['name'] = self.coffee.name
            item['price'] = float(self.coffee.price)
            item['image'] = self.coffee.get_index_image()
        elif self.item_type == 'bean' and self.bean:
            item['id'] = self.bean.id
            item['name'] = self.bean.name
            item['price'] = float(self.bean.get_price(self.get_options().get('weight', 500)))
            item['image'] = self.bean.get_index_image()
        
        items.append(item)
        return items
    
    def get_items_display(self):
        """獲取顯示用項目列表"""
        items = self.get_items()
        for item in items:
            options = item.get('options', {})
            if item['type'] == 'coffee':
                item['display'] = f"{item['name']} x{item['quantity']}"
                if options.get('cup_size'):
                    item['display'] += f" ({options['cup_size']})"
            elif item['type'] == 'bean':
                weight = options.get('weight', 500)
                item['display'] = f"{item['name']} ({weight}g) x{item['quantity']}"
        return items
    
    def get_options(self):
        """解析選項 JSON"""
        try:
            return json.loads(self.options) if self.options else {}
        except (json.JSONDecodeError, TypeError):
            return {}
    
    def clean(self):
        """驗證模型數據"""
        if self.item_type == 'coffee' and not self.coffee:
            raise ValidationError("咖啡類型必須選擇咖啡商品")
        if self.item_type == 'bean' and not self.bean:
            raise ValidationError("咖啡豆類型必須選擇咖啡豆商品")
    
    class Meta:
        app_label = 'eshop'
        verbose_name = "購物車項目"
        verbose_name_plural = "購物車項目"
