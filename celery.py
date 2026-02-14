# your_project/celery.py
import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'your_project.settings')

app = Celery('your_project')
app.config_from_object('django.conf:settings', namespace='CELERY')

# 自動發現任務
app.autodiscover_tasks()

# 配置定時任務
app.conf.beat_schedule = {
    'monitor-pending-payments-every-5-minutes': {
        'task': 'eshop.tasks.monitor_pending_payments',
        'schedule': 300.0,  # 每5分鐘
    },
    'cleanup-old-queues-daily': {
        'task': 'eshop.tasks.cleanup_old_queues',
        'schedule': crontab(hour=3, minute=0),  # 每天凌晨3點
    },
}