# betweencoffee_delivery/celery_app.py
"""
Celery 配置 - 處理異步任務和定時任務

注意：在 Render free plan 上 Celery worker/beat 無法運行（無 Redis）。
Celery 任務會改為同步執行，不影響網站主要功能。
"""
import logging
import os

logger = logging.getLogger(__name__)

# 嘗試導入 Celery，如果失敗則使用模擬版本
try:
    from celery import Celery
    from celery.schedules import crontab

    CELERY_AVAILABLE = True
except ImportError:
    CELERY_AVAILABLE = False
    logger.warning("Celery 未安裝，任務將同步執行")

if CELERY_AVAILABLE:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "betweencoffee_delivery.settings")

    app = Celery("betweencoffee_delivery")
    app.config_from_object("django.conf:settings", namespace="CELERY")

    # 自動發現任務
    app.autodiscover_tasks()

    # 配置定時任務
    app.conf.beat_schedule = {
        "monitor-pending-payments-every-5-minutes": {
            "task": "eshop.tasks.monitor_pending_payments",
            "schedule": 300.0,  # 每5分鐘
        },
        "cleanup-old-queues-daily": {
            "task": "eshop.tasks.cleanup_old_queues",
            "schedule": crontab(hour=3, minute=0),  # 每天凌晨3點
        },
    }
else:
    # 提供一個模擬的 Celery 應用，讓導入不報錯
    class MockCelery:
        """當 Celery 不可用時的模擬對象"""

        def __init__(self):
            self.conf = type("conf", (), {})()

        def task(self, *args, **kwargs):
            def decorator(f):
                return f

            return decorator

        def autodiscover_tasks(self, *args, **kwargs):
            pass

    app = MockCelery()
    logger.info("使用模擬 Celery 應用（無需 Redis）")
