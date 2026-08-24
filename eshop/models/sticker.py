# eshop/models/sticker.py
"""
Sticker（貼紙）模型模組（2026-08-24 模組化）。

每個 Sticker 定義一組貼紙設計：背景款式 + 前圖（內建或上傳）+ 文字。
商品（CoffeeItem / BeanItem）透過 FK 選擇要顯示的貼紙；留空 = 不顯示。

需求背景：
- 並非所有咖啡都顯示貼紙（A 咖啡用 Sticker 1、B 咖啡用 Sticker 2，或留空不顯示）
- Django admin 可自由管理每種貼紙的顯示款式與文字
- 採「資料驅動模組化」，不需為每種咖啡複製 HTML
"""

import logging

from django.db import models

from .base import get_image_url

logger = logging.getLogger(__name__)


class Sticker(models.Model):
    """貼紙設計模型"""

    # 背景款式：內建 4 款 static 圖片（260×260，旋轉底圖）
    BG_CHOICES = [
        ("sticker_v1", "Sticker 1 背景（sticker_v1.png）"),
        ("sticker_v2", "Sticker 2 背景（sticker_v2.png）"),
        ("sticker_v3", "Sticker 3 背景（sticker_v3.png）"),
        ("sticker", "Sticker 4 背景（sticker.png）"),
    ]

    # 內建前圖款式：static 圖片（去背 PNG，顯示於 sticker 右上角）
    FRONT_PRESET_CHOICES = [
        ("", "不使用內建前圖（改用上方上傳的自訂圖）"),
        ("takeaway_cup", "咖啡杯（takeaway_cup.png）"),
        ("float_bean", "咖啡豆（float_bean.png）"),
        ("_takeaway_cup", "咖啡杯變體 A（_takeaway_cup.png）"),
        ("__takeaway_cup", "咖啡杯變體 B（__takeaway_cup.png）"),
    ]

    name = models.CharField(max_length=50, verbose_name="名稱", help_text="例：Sticker 1")
    bg_image = models.CharField(
        max_length=50,
        choices=BG_CHOICES,
        default="sticker_v1",
        verbose_name="背景款式",
    )
    front_image_preset = models.CharField(
        max_length=50,
        choices=FRONT_PRESET_CHOICES,
        blank=True,
        default="takeaway_cup",
        verbose_name="內建前圖款式",
        help_text="選擇內建前圖；若要使用下方上傳的自訂前圖，請選「不使用內建前圖」。",
    )
    front_image = models.ImageField(
        upload_to="stickers/",
        blank=True,
        null=True,
        verbose_name="自訂前圖（上傳）",
        help_text="上傳自訂去背 PNG 前圖；有值時優先於內建款式。注意：Render 免費方案重新部署後上傳檔案可能遺失（與現有商品圖相同限制）。",
    )
    text_en = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="英文副標題",
        help_text="貼紙上半部小字。用 \\n 換行，例：Follow \\nYour Rhythm",
    )
    text_zh = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="中文標語",
        help_text="貼紙下半部大字。用 \\n 換行，例：5分鐘內\\n準備就緒!!",
    )
    is_active = models.BooleanField(default=True, verbose_name="啟用")
    sort_order = models.PositiveIntegerField(default=0, verbose_name="排序")

    def __str__(self):
        return self.name or self.bg_image

    @property
    def bg_image_url(self):
        """背景圖 URL（內建 static 圖片）"""
        return f"/static/images/{self.bg_image}.png"

    @property
    def front_image_url(self):
        """前圖 URL：上傳的自訂圖優先，否則用內建 preset"""
        if self.front_image:
            return get_image_url(self.front_image, "")
        return f"/static/images/{self.front_image_preset or 'takeaway_cup'}.png"

    class Meta:
        verbose_name_plural = "Stickers"
        ordering = ["sort_order", "id"]
