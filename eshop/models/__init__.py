# eshop/models/__init__.py
"""
eshop 模型包

將大型 models.py 拆分為模塊化結構：
- base.py: 基礎模型和工具函數
- shop_items.py: CoffeeItem, BeanItem
- cart_item.py: CartItem
- order.py: OrderModel（核心訂單模型）
- queue.py: CoffeeQueue, Barista, CoffeePreparationTime

向後兼容：所有模型仍可從 eshop.models 導入
"""

# 向後兼容導入 - 保持所有現有導入路徑有效
from .base import get_image_url
from .shop_items import CoffeeItem, BeanItem
from .cart_item import CartItem
from .order import OrderModel, get_product_image_url
from .queue import CoffeeQueue, Barista, CoffeePreparationTime

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
