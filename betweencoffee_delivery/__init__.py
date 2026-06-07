# betweencoffee_delivery/__init__.py
from __future__ import absolute_import, unicode_literals

# 導入 Celery app，確保 Django 啟動時自動加載
# 如果 celery 未安裝（如 Render 環境），優雅地跳過
try:
    from .celery_app import app as celery_app
    __all__ = ('celery_app',)
except ModuleNotFoundError:
    # Celery 未安裝（Render 等無 Redis 環境），跳過
    celery_app = None
    __all__ = ('celery_app',)
