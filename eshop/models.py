# eshop/models.py
"""
eshop 模型 - 向後兼容導入層

此文件保留為向後兼容的導入層。
所有模型已拆分到 eshop/models/ 包中：
- base.py: 基礎模型和工具函數
- shop_items.py: CoffeeItem, BeanItem
- cart_item.py: CartItem
- order.py: OrderModel（核心訂單模型）
- queue.py: CoffeeQueue, Barista, CoffeePreparationTime

所有現有導入路徑（from eshop.models import ...）仍然有效。
"""

# 從包導入所有模型和工具函數
from eshop.models import (
    get_image_url,
    CoffeeItem,
    BeanItem,
    CartItem,
    OrderModel,
    CoffeeQueue,
    Barista,
    CoffeePreparationTime,
    get_product_image_url,
)

__all__ = [
    'get_image_url',
    'CoffeeItem',
    'BeanItem',
    'CartItem',
    'OrderModel',
    'CoffeeQueue',
    'Barista',
    'CoffeePreparationTime',
    'get_product_image_url',
]
