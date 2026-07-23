# eshop/models.py
"""
eshop.models - 模型重新導出模組

所有模型已拆分到 eshop/models/ 套件中：
- base.py: 工具函數 (get_image_url, get_product_image_url)
- shop_items.py: CoffeeItem, BeanItem
- cart_item.py: CartItem
- order.py: OrderModel
- queue_models.py: CoffeeQueue, Barista, CoffeePreparationTime

此文件僅作為重新導出入口，保持向後相容性。
"""

import warnings

from .models.base import get_image_url, get_product_image_url
from .models.shop_items import CoffeeItem, BeanItem
from .models.cart_item import CartItem
from .models.order import OrderModel
from .models.queue_models import CoffeeQueue, Barista, CoffeePreparationTime

warnings.warn(
    "直接從 eshop.models 導入已棄用，請從 eshop.models 套件導入。",
    DeprecationWarning,
    stacklevel=2
)
