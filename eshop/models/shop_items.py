# eshop/models/shop_items.py
"""
商品模型：CoffeeItem, BeanItem

從 models.py 提取的商品相關模型。
"""

from django.db import models
from .base import get_image_url


class CoffeeItem(models.Model):
    """咖啡商品模型"""
    name = models.CharField(max_length=100, verbose_name="咖啡名稱")
    description = models.TextField(blank=True, verbose_name="描述")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="價格")
    image = models.ImageField(upload_to='coffee_images/', blank=True, null=True, verbose_name="圖片")
    hot_item = models.BooleanField(default=False, verbose_name="熱門商品")
    hot_item_order = models.IntegerField(default=0, verbose_name="熱門排序")
    is_available = models.BooleanField(default=True, verbose_name="上架")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="創建時間")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新時間")
    
    def __str__(self):
        return self.name
    
    def get_index_image(self):
        """獲取列表頁圖片"""
        return get_image_url(self.image, '/static/images/coffee_default_index.png')
    
    def get_detail_image(self):
        """獲取詳情頁圖片"""
        return get_image_url(self.image, '/static/images/coffee_default_detail.png')
    
    class Meta:
        app_label = 'eshop'
        verbose_name = "咖啡"
        verbose_name_plural = "咖啡"
        ordering = ['hot_item_order', 'name']


class BeanItem(models.Model):
    """咖啡豆商品模型"""
    name = models.CharField(max_length=100, verbose_name="咖啡豆名稱")
    description = models.TextField(blank=True, verbose_name="描述")
    price_500g = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="500g價格")
    image = models.ImageField(upload_to='bean_images/', blank=True, null=True, verbose_name="圖片")
    image_index = models.IntegerField(default=0, verbose_name="圖片索引")
    hot_item = models.BooleanField(default=False, verbose_name="熱門商品")
    hot_item_order = models.IntegerField(default=0, verbose_name="熱門排序")
    is_available = models.BooleanField(default=True, verbose_name="上架")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="創建時間")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新時間")
    
    def __str__(self):
        return self.name
    
    def get_index_image(self):
        """獲取列表頁圖片"""
        return get_image_url(self.image, '/static/images/bean_default_index.png')
    
    def get_detail_image(self):
        """獲取詳情頁圖片"""
        return get_image_url(self.image, '/static/images/bean_default_detail.png')
    
    def get_price(self, weight):
        """
        根據重量獲取價格
        weight: 500 (代表500g)
        """
        if weight == 500:
            return self.price_500g
        return self.price_500g
    
    class Meta:
        app_label = 'eshop'
        verbose_name = "咖啡豆"
        verbose_name_plural = "咖啡豆"
        ordering = ['hot_item_order', 'name']
