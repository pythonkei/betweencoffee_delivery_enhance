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
    # 亮點標語（2026-08-14）：菜單卡片名稱下方顯示的 12-15 字中文亮點
    highlight = models.CharField(max_length=100, blank=True, verbose_name="亮點標語")
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
    # Strength level choices
    STRENGTH_CHOICES = [
        ("Normal", "預設"),
        ("Extra", "特濃"),
    ]
    strength_level = models.CharField(
        max_length=10, choices=STRENGTH_CHOICES, default="Normal"
    )
    is_published = models.BooleanField(default=True)
    is_shop_hot_item = models.BooleanField(default=False)
    # 排序字段
    hot_item_order = models.PositiveIntegerField(
        default=0, verbose_name="热门商品排序", help_text="数字越小显示越靠前"
    )
    # 菜單卡片排序（2026-08-13）：coffee_menu 頁面顯示順序，數字越小越靠前
    sort_order = models.PositiveIntegerField(
        default=0, verbose_name="菜單排序", help_text="數字越小顯示越靠前"
    )
    # ===== 自訂選項組開關（2026-08-15）：每種咖啡勾選要顯示的選項組，
    #       選項值定義見 eshop/models/option_definitions.py =====
    # 杯量 / 濃度：所有咖啡的基本選項 → default=True（Admin 可個別關閉，如 A 有 B 沒有）
    option_cup_level = models.BooleanField(default=True, verbose_name="杯量")
    option_strength_level = models.BooleanField(default=True, verbose_name="濃度")
    # 奶量（少/正常/追加）：非所有咖啡皆有 → 每種咖啡指定是否顯示（2026-08-15）
    option_milk_level = models.BooleanField(default=False, verbose_name="奶量（少/正常/追加）")
    option_milk = models.BooleanField(default=False, verbose_name="奶類")
    option_caramel = models.BooleanField(default=False, verbose_name="焦糖")
    option_butter = models.BooleanField(default=False, verbose_name="黃油")
    option_coconut = models.BooleanField(default=False, verbose_name="椰奶")
    option_vanilla = models.BooleanField(default=False, verbose_name="香草")
    option_special = models.BooleanField(default=False, verbose_name="特調")
    option_oolong = models.BooleanField(default=False, verbose_name="烏龍茶")
    option_jasmine = models.BooleanField(default=False, verbose_name="茉莉花茶")
    option_matcha = models.BooleanField(default=False, verbose_name="抹茶")
    option_green = models.BooleanField(default=False, verbose_name="綠茶")
    option_hojicha = models.BooleanField(default=False, verbose_name="焙茶")
    option_topping = models.BooleanField(default=False, verbose_name="面層配料")
    option_bean_blend = models.BooleanField(default=False, verbose_name="配豆")
    # 自訂選項組排序（2026-08-15）：每組一個數字欄位，數字越小越靠前，0=預設（依選項定義順序）
    option_order_cup_level = models.PositiveIntegerField(default=0, blank=True, verbose_name="杯量順序", help_text="數字越小越靠前，0=預設")
    option_order_strength_level = models.PositiveIntegerField(default=0, blank=True, verbose_name="濃度順序", help_text="數字越小越靠前，0=預設")
    option_order_milk_level = models.PositiveIntegerField(default=0, blank=True, verbose_name="奶量順序", help_text="數字越小越靠前，0=預設")
    option_order_milk = models.PositiveIntegerField(default=0, blank=True, verbose_name="奶類順序", help_text="數字越小越靠前，0=預設")
    option_order_caramel = models.PositiveIntegerField(default=0, blank=True, verbose_name="焦糖順序", help_text="數字越小越靠前，0=預設")
    option_order_butter = models.PositiveIntegerField(default=0, blank=True, verbose_name="黃油順序", help_text="數字越小越靠前，0=預設")
    option_order_coconut = models.PositiveIntegerField(default=0, blank=True, verbose_name="椰奶順序", help_text="數字越小越靠前，0=預設")
    option_order_vanilla = models.PositiveIntegerField(default=0, blank=True, verbose_name="香草順序", help_text="數字越小越靠前，0=預設")
    option_order_special = models.PositiveIntegerField(default=0, blank=True, verbose_name="特調順序", help_text="數字越小越靠前，0=預設")
    option_order_oolong = models.PositiveIntegerField(default=0, blank=True, verbose_name="烏龍順序", help_text="數字越小越靠前，0=預設")
    option_order_jasmine = models.PositiveIntegerField(default=0, blank=True, verbose_name="茉莉順序", help_text="數字越小越靠前，0=預設")
    option_order_matcha = models.PositiveIntegerField(default=0, blank=True, verbose_name="抹茶順序", help_text="數字越小越靠前，0=預設")
    option_order_green = models.PositiveIntegerField(default=0, blank=True, verbose_name="綠茶順序", help_text="數字越小越靠前，0=預設")
    option_order_hojicha = models.PositiveIntegerField(default=0, blank=True, verbose_name="焙茶順序", help_text="數字越小越靠前，0=預設")
    option_order_topping = models.PositiveIntegerField(default=0, blank=True, verbose_name="配料順序", help_text="數字越小越靠前，0=預設")
    option_order_bean_blend = models.PositiveIntegerField(default=0, blank=True, verbose_name="配豆順序", help_text="數字越小越靠前，0=預設")

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

    # ===== Sticker 貼紙（2026-08-24 模組化）：詳情頁右上角貼紙 =====
    # 留空 = 不顯示貼紙；選擇 = 顯示該貼紙設計（背景款式 + 前圖 + 文字）
    sticker = models.ForeignKey(
        "Sticker",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Sticker 貼紙",
        help_text="選擇詳情頁顯示的貼紙；留空 = 不顯示。",
    )

    class Meta:
        verbose_name_plural = "Coffee"
        ordering = []


class BeanItem(models.Model):
    """咖啡豆商品模型"""

    name = models.CharField(max_length=100)
    introduction = models.TextField(max_length=200, blank=True)
    description = models.TextField(max_length=400, blank=True)
    # 亮點標語（2026-08-14）：菜單卡片名稱下方顯示的 12-15 字中文亮點
    highlight = models.CharField(max_length=100, blank=True, verbose_name="亮點標語")
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
    # 菜單卡片排序（2026-08-13）：bean_menu 頁面顯示順序，數字越小越靠前
    sort_order = models.PositiveIntegerField(
        default=0, verbose_name="菜單排序", help_text="數字越小顯示越靠前"
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

    # ===== Sticker 貼紙（2026-08-24 模組化）：詳情頁右上角貼紙 =====
    # 留空 = 不顯示貼紙；選擇 = 顯示該貼紙設計（背景款式 + 前圖 + 文字）
    sticker = models.ForeignKey(
        "Sticker",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Sticker 貼紙",
        help_text="選擇詳情頁顯示的貼紙；留空 = 不顯示。",
    )

    class Meta:
        verbose_name_plural = "Bean"
        ordering = []
