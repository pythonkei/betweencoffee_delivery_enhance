# eshop/models/base.py
"""
基礎工具函數模組。
包含圖片 URL 獲取等共用工具函數。
"""

import logging

from django.conf import settings

logger = logging.getLogger(__name__)


def get_image_url(image_field, default=None):
    """
    統一的圖片 URL 獲取工具函數。

    MEDIA_URL 已根據環境動態設置（settings.py）：
    - 本地開發：MEDIA_URL = /media/ → image.url 返回 /media/xxx.jpg
    - 生產環境：MEDIA_URL = /static/media/ → image.url 返回 /static/media/xxx.jpg

    因此 image.url 在所有環境中都返回正確的路徑，無需額外轉換。

    Args:
        image_field: Django ImageField 實例（或任何有 .url 屬性的物件）
        default: 當 image_field 為空時的默認路徑

    Returns:
        str: 正確的圖片 URL 路徑
    """
    if not image_field:
        return default

    try:
        return image_field.url
    except (ValueError, AttributeError):
        return default


def get_product_image_url(item_data):
    """
    根據商品數據獲取正確的圖片 URL。

    MEDIA_URL 已根據環境動態設置（settings.py），image.url 在所有環境中都返回正確的路徑。
    本地開發：image.url 返回 /media/xxx.jpg，由 Django static() helper 提供服務。
    生產環境：image.url 返回 /static/media/xxx.jpg，由 Whitenoise 提供服務。
    """
    # 延遲導入以避免循環依賴
    from .shop_items import BeanItem, CoffeeItem

    # 如果已經有圖片 URL，直接返回
    if item_data.get("image"):
        return item_data["image"]

    # 如果沒有圖片 URL，嘗試從數據庫獲取
    try:
        if item_data.get("type") == "coffee":
            coffee = CoffeeItem.objects.get(id=item_data["id"])
            if coffee.image and hasattr(coffee.image, "name") and coffee.image.name:
                return get_image_url(coffee.image, "/static/images/default-coffee.png")
            return "/static/images/default-coffee.png"
        elif item_data.get("type") == "bean":
            bean = BeanItem.objects.get(id=item_data["id"])
            if bean.image and hasattr(bean.image, "name") and bean.image.name:
                return get_image_url(bean.image, "/static/images/default-bean.png")
            return "/static/images/default-bean.png"
    except (CoffeeItem.DoesNotExist, BeanItem.DoesNotExist):
        pass

    # 默認圖片
    return "/static/images/default-product.png"
