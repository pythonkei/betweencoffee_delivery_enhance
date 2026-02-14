# eshop/management/commands/cleanup_old_queues.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from eshop.models import CoffeeQueue

class Command(BaseCommand):
    help = '清理旧的队列记录'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='保留最近几天的数据（默认7天）'
        )
    
    def handle(self, *args, **options):
        days = options['days']
        cutoff_date = timezone.now() - timedelta(days=days)
        
        deleted_count, _ = CoffeeQueue.objects.filter(
            status='completed',
            updated_at__lt=cutoff_date
        ).delete()
        
        self.stdout.write(
            self.style.SUCCESS(f'成功清理 {deleted_count} 条旧的队列记录')
        )