# eshop/models/base.py
"""
基礎模型工具函數

從 models.py 提取的通用工具函數。
"""

import logging

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
