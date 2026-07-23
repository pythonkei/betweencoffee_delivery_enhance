# eshop/models/shop_items.py
"""
商品模型模組。
包含 CoffeeItem（咖啡商品）和 BeanItem（咖啡豆商品）模型。
"""

import logging

from django.db import models
from django.utils import timezone

from .base import get_image_url

logger = logging.getLogger(__name__)


class CoffeeItem(models.Model):
    """咖啡商品模型"""

    name = models.CharField(max_length=100)
    introduction = models.TextField(max_length=200, blank=True)
    description = models.TextField(max_length=400, blank=True)
    image = models.ImageField(upload_to="coffee_images/")
    image_index = models.ImageField(
        upload_to="coffee_images/index/", blank=True, null=True, verbose_name="首页图片"
    )
    price = models.DecimalField(max_digits=5, decimal_places=2)
    origin = models.CharField(max_length=30, blank=True)
    flavor = models.TextField(max_length=200, blank=True)
    list_date = models.DateTimeField(default=timezone.now, blank=True)
    # Cup level choices
    CUP_LEVEL_CHOICES = [
        ("Small", "Small"),
        ("Medium", "Medium"),
        ("Large", "Large"),
    ]
    cup_level = models.CharField(
        max_length=10, choices=CUP_LEVEL_CHOICES, default="Medium"
    )
    # Milk level choices
    MILK_LEVEL_CHOICES = [
        ("Light", "Light"),
        ("Medium", "Medium"),
        ("Extra", "Extra"),
    ]
    milk_level = models.CharField(
        max_length=10, choices=MILK_LEVEL_CHOICES, default="Medium"
    )
    is_published = models.BooleanField(default=True)
    is_shop_hot_item = models.BooleanField(default=False)
    # 排序字段
    hot_item_order = models.PositiveIntegerField(
        default=0, verbose_name="热门商品排序", help_text="数字越小显示越靠前"
    )

    def __str__(self):
        return self.name

    def get_index_image(self):
        """獲取首頁專用圖片，如果沒有則返回默認圖片"""
        if (
            self.image_index
            and hasattr(self.image_index, "name")
            and self.image_index.name
        ):
            return get_image_url(
                self.image_index, "/static/images/default-coffee-index.png"
            )
        elif self.image and hasattr(self.image, "name") and self.image.name:
            return get_image_url(self.image, "/static/images/default-coffee-index.png")
        else:
            return "/static/images/default-coffee-index.png"

    def get_detail_image(self):
        """獲取詳情頁圖片"""
        if self.image and hasattr(self.image, "name") and self.image.name:
            try:
                return get_image_url(
                    self.image, "/static/images/default-coffee-detail.png"
                )
            except (ValueError, AttributeError):
                return "/static/images/default-coffee-detail.png"
        else:
            return "/static/images/default-coffee-detail.png"

    class Meta:
        verbose_name_plural = "Coffee"
        ordering = []


class BeanItem(models.Model):
    """咖啡豆商品模型"""

    name = models.CharField(max_length=100)
    introduction = models.TextField(max_length=200, blank=True)
    description = models.TextField(max_length=400, blank=True)
    image = models.ImageField(upload_to="bean_images/")
    image_index = models.ImageField(
        upload_to="bean_images/index/", blank=True, null=True, verbose_name="首页图片"
    )
    price_200g = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    price_500g = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    origin = models.CharField(max_length=50, blank=True)

    ROAST_LEVEL_CHOICES = [
        ("light", "浅"),
        ("medium_light", "中浅"),
        ("medium", "中"),
        ("medium_dark", "中深"),
        ("dark", "深"),
    ]
    roast_level = models.CharField(
        max_length=20, choices=ROAST_LEVEL_CHOICES, default="medium"
    )

    GRINDING_LEVEL_CHOICES = [
        ("Non", "免研磨"),
        ("Light", "細研磨"),
        ("Medium", "中研磨"),
        ("Deep", "粗研磨"),
    ]
    grinding_level = models.CharField(
        max_length=10, choices=GRINDING_LEVEL_CHOICES, default="Non"
    )

    flavor = models.TextField(max_length=200, blank=True)
    list_date = models.DateTimeField(default=timezone.now, blank=True)
    is_published = models.BooleanField(default=True)
    is_shop_hot_item = models.BooleanField(default=False)
    # 排序字段
    hot_item_order = models.PositiveIntegerField(
        default=0, verbose_name="热门商品排序", help_text="数字越小显示越靠前"
    )

    def __str__(self):
        return self.name

    def get_index_image(self):
        """獲取首頁專用圖片，如果沒有則返回默認圖片"""
        if (
            self.image_index
            and hasattr(self.image_index, "name")
            and self.image_index.name
        ):
            return get_image_url(
                self.image_index, "/static/images/default-bean-index.png"
            )
        elif self.image and hasattr(self.image, "name") and self.image.name:
            return get_image_url(self.image, "/static/images/default-bean-index.png")
        else:
            return "/static/images/default-bean-index.png"

    def get_detail_image(self):
        """獲取詳情頁圖片"""
        if self.image and hasattr(self.image, "name") and self.image.name:
            try:
                return get_image_url(
                    self.image, "/static/images/default-bean-detail.png"
                )
            except (ValueError, AttributeError):
                return "/static/images/default-bean-detail.png"
        else:
            return "/static/images/default-bean-detail.png"

    def get_price(self, weight):
        """根據重量獲取價格"""
        if weight == "200g":
            return self.price_200g
        elif weight == "500g":
            return self.price_500g
        return self.price_200g  # 默認返回200克價格

    class Meta:
        verbose_name_plural = "Bean"
        ordering = []
