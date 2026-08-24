# eshop/models/__init__.py
"""
eshop.models 套件 - 模型模組拆分

模型分佈：
- base.py: 工具函數 (get_image_url, get_product_image_url)
- shop_items.py: CoffeeItem, BeanItem
- sticker.py: Sticker（貼紙設計，2026-08-24）
- cart_item.py: CartItem
- order.py: OrderModel
- queue_models.py: CoffeeQueue, Barista, CoffeePreparationTime
- audit_log.py: AuditLog
"""

# 從子模組匯入
from .audit_log import AuditLog
from .base import get_image_url, get_product_image_url
from .cart_item import CartItem
from .order import OrderModel
from .queue_models import Barista, CoffeePreparationTime, CoffeeQueue
from .shop_items import BeanItem, CoffeeItem
from .sticker import Sticker
