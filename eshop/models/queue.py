# eshop/models/queue.py
"""
隊列模型：CoffeeQueue, Barista, CoffeePreparationTime

從 models.py 提取的隊列相關模型。
"""

import logging
from django.db import models
from django.conf import settings

logger = logging.getLogger(__name__)


class CoffeePreparationTime(models.Model):
    """咖啡製作時間配置"""
    coffee = models.OneToOneField(
        'eshop.CoffeeItem', on_delete=models.CASCADE, related_name='preparation_time',
        verbose_name="咖啡"
    )
    minutes = models.PositiveIntegerField(default=5, verbose_name="製作時間(分鐘)")
    
    class Meta:
        app_label = 'eshop'
        verbose_name = "咖啡製作時間"
        verbose_name_plural = "咖啡製作時間"
    
    def __str__(self):
        return f"{self.coffee.name}: {self.minutes}分鐘"


class Barista(models.Model):
    """咖啡師模型"""
    name = models.CharField(max_length=100, verbose_name="咖啡師名稱")
    is_available = models.BooleanField(default=True, verbose_name="是否可用")
    current_workload = models.IntegerField(default=0, verbose_name="當前工作量")
    max_workload = models.IntegerField(default=2, verbose_name="最大工作量")
    
    class Meta:
        app_label = 'eshop'
        verbose_name = "咖啡師"
        verbose_name_plural = "咖啡師"
    
    def __str__(self):
        return self.name
    
    def is_available(self):
        """檢查咖啡師是否可用"""
        return self.current_workload < self.max_workload


class CoffeeQueue(models.Model):
    """咖啡製作隊列模型"""
    order = models.OneToOneField(
        'eshop.OrderModel', on_delete=models.CASCADE, related_name='coffee_queue',
        verbose_name="訂單"
    )
    barista = models.ForeignKey(
        Barista, on_delete=models.SET_NULL, blank=True, null=True,
        related_name='queue_items', verbose_name="咖啡師"
    )
    position = models.IntegerField(default=0, verbose_name="隊列位置")
    coffee_count = models.IntegerField(default=0, verbose_name="咖啡數量")
    preparation_time_minutes = models.IntegerField(default=5, verbose_name="預計製作時間(分鐘)")
    estimated_start_time = models.DateTimeField(blank=True, null=True, verbose_name="預計開始時間")
    estimated_completion_time = models.DateTimeField(blank=True, null=True, verbose_name="預計完成時間")
    started_at = models.DateTimeField(blank=True, null=True, verbose_name="實際開始時間")
    completed_at = models.DateTimeField(blank=True, null=True, verbose_name="實際完成時間")
    status = models.CharField(
        max_length=20,
        choices=[
            ('waiting', '等待中'),
            ('preparing', '製作中'),
            ('completed', '已完成'),
        ],
        default='waiting',
        verbose_name="狀態"
    )
    notes = models.TextField(blank=True, verbose_name="備註")
    added_at = models.DateTimeField(auto_now_add=True, verbose_name="加入時間")
    
    class Meta:
        app_label = 'eshop'
        verbose_name = "咖啡隊列"
        verbose_name_plural = "咖啡隊列"
        ordering = ['position', 'added_at']
    
    def __str__(self):
        return f"訂單 #{self.order_id} - 位置 {self.position}"
    
    def add_to_queue(self):
        """
        將訂單加入製作隊列
        返回: (success, message)
        """
        try:
            from eshop.queue_manager_refactored import CoffeeQueueManager
            manager = CoffeeQueueManager()
            result = manager.add_order_to_queue(self.order)
            return result.get('success', False), result.get('message', '')
        except Exception as e:
            logger.error(f"加入隊列失敗: {str(e)}")
            return False, str(e)
    
    def get_queue_position(self):
        """獲取當前隊列位置"""
        try:
            from eshop.queue_manager_refactored import CoffeeQueueManager
            manager = CoffeeQueueManager()
            return manager.get_queue_position(self.order)
        except Exception as e:
            logger.error(f"獲取隊列位置失敗: {str(e)}")
            return None
    
    def get_queue_wait_time(self):
        """獲取預計等待時間（分鐘）"""
        try:
            from eshop.queue_manager_refactored import CoffeeQueueManager
            manager = CoffeeQueueManager()
            return manager.get_queue_wait_time(self.order)
        except Exception as e:
            logger.error(f"獲取等待時間失敗: {str(e)}")
            return None
