# eshop/models/queue_models.py
"""
佇列相關模型：CoffeeQueue, Barista, CoffeePreparationTime
"""

import logging

from django.db import models

from .order import OrderModel

logger = logging.getLogger(__name__)


class CoffeeQueue(models.Model):
    """咖啡制作队列"""

    STATUS_CHOICES = [
        (
            "waiting",
            "等待中",
        ),  # 等待开始制作 - 订单已支付，排队等待咖啡师开始制作, 需要被计入前面等待时间
        ("preparing", "制作中"),  # 正在制作咖啡 - 咖啡师已开始制作该订单的咖啡
        (
            "ready",
            "已就緒",
        ),  # 制作完成，等待提取 - 咖啡制作已完成，放在取餐区等待客户提取
        ("completed", "已完成"),
    ]
    """
    整个队列系统的完整逻辑流程图:
    订单支付成功
        ↓
    自动加入CoffeeQueue (status='waiting')
        ↓
    计算队列位置 (position)
        ↓
    计算预计时间 (estimated_start_time, estimated_completion_time)
        ↓
    ↓←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←
        ↓
    咖啡师点击"开始制作"
        ↓
    状态变为'preparing'，记录actual_start_time
        ↓
    ↓←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←
        ↓
    咖啡师点击"标记就绪"
        ↓
    状态变为'ready'，记录actual_completion_time
        ↓
    客户提取咖啡
        ↓
    可选：标记为已提取 (可移除或归档)
    """

    order = models.OneToOneField(
        OrderModel, on_delete=models.CASCADE, related_name="queue_item"
    )
    queue_position = models.PositiveIntegerField(default=0, verbose_name="队列位置")
    position = models.PositiveIntegerField(default=0, verbose_name="位置")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="waiting")
    estimated_start_time = models.DateTimeField(
        null=True, blank=True, verbose_name="预计开始时间"
    )
    estimated_completion_time = models.DateTimeField(
        null=True, blank=True, verbose_name="预计完成时间"
    )
    actual_start_time = models.DateTimeField(
        null=True, blank=True, verbose_name="实际开始时间"
    )
    actual_completion_time = models.DateTimeField(
        null=True, blank=True, verbose_name="实际完成时间"
    )
    barista = models.CharField(
        max_length=100, blank=True, null=True, verbose_name="制作人员"
    )
    notes = models.TextField(blank=True, null=True, verbose_name="备注")

    # 制作时间估算字段
    coffee_count = models.PositiveIntegerField(default=0, verbose_name="咖啡杯数")
    preparation_time_minutes = models.PositiveIntegerField(
        default=0, verbose_name="预计制作时间(分钟)"
    )

    # 是否為加速訂單（用於優先隊列）
    is_expedited = models.BooleanField(default=False, verbose_name="是否加速")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    added_at = models.DateTimeField(auto_now_add=True, verbose_name="加入隊列時間")

    class Meta:
        ordering = ["estimated_start_time"]
        verbose_name = "咖啡制作队列"
        verbose_name_plural = "咖啡制作队列"
        indexes = [
            models.Index(fields=["status", "estimated_start_time"]),
            models.Index(fields=["estimated_completion_time"]),
            models.Index(fields=["added_at"]),
        ]

    def __str__(self):
        return f"订单 #{self.order.id} - {self.get_status_display()}"


class Barista(models.Model):
    """咖啡师/制作人员"""

    name = models.CharField(max_length=100, verbose_name="姓名")
    is_active = models.BooleanField(default=True, verbose_name="是否在岗")
    efficiency_factor = models.FloatField(
        default=1.0,
        verbose_name="效率因子",
        help_text="1.0为正常，<1.0为较快，>1.0为较慢",
    )
    max_concurrent_orders = models.PositiveIntegerField(
        default=3, verbose_name="最大并发订单数"
    )
    current_load = models.PositiveIntegerField(default=0, verbose_name="当前负载")

    class Meta:
        verbose_name = "咖啡师"
        verbose_name_plural = "咖啡师"

    def __str__(self):
        return self.name

    def is_available(self):
        """检查咖啡师是否可用"""
        return self.is_active and self.current_load < self.max_concurrent_orders


class CoffeePreparationTime(models.Model):
    """咖啡制作时间配置"""

    coffee_type = models.CharField(max_length=100, verbose_name="咖啡类型")
    base_preparation_minutes = models.PositiveIntegerField(
        default=5, verbose_name="基础制作时间(分钟)"
    )
    additional_per_cup_minutes = models.PositiveIntegerField(
        default=3, verbose_name="每增加一杯额外时间(分钟)"
    )
    is_active = models.BooleanField(default=True, verbose_name="是否启用")

    class Meta:
        verbose_name = "咖啡制作时间配置"
        verbose_name_plural = "咖啡制作时间配置"

    def __str__(self):
        return f"{self.coffee_type}: {self.base_preparation_minutes}+{self.additional_per_cup_minutes}分钟"
