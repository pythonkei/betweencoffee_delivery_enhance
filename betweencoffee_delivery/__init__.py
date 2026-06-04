# betweencoffee_delivery/__init__.py
from __future__ import absolute_import, unicode_literals

# 導入 Celery app，確保 Django 啟動時自動加載
from .celery_app import app as celery_app

__all__ = ('celery_app',)
