# eshop/models/audit_log.py
"""
AuditLog 模型 - 記錄員工操作日誌

用於追蹤所有員工在訂單管理系統中的操作，
包含：製作、就緒、完成、取消、支付確認等。
"""

from django.db import models

from .order import OrderModel


class AuditLog(models.Model):
    """審計日誌 - 記錄員工對訂單的操作"""

    # 動作類型
    ACTION_CHOICES = [
        ("order_waiting", "標記為等待中"),
        ("order_preparing", "開始製作"),
        ("order_ready", "標記為就緒"),
        ("order_completed", "標記為已完成"),
        ("order_cancelled", "取消訂單"),
        ("payment_fps_confirmed", "FPS 付款確認"),
        ("payment_cash_confirmed", "現金付款確認"),
        ("payment_auto_paid", "自動支付成功"),
        ("order_created", "訂單建立"),
        ("order_updated", "訂單更新"),
        ("whatsapp_notified", "WhatsApp 通知已發送"),
    ]

    action = models.CharField(
        max_length=30,
        choices=ACTION_CHOICES,
        db_index=True,
        verbose_name="操作類型",
    )
    order = models.ForeignKey(
        OrderModel,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="audit_logs",
        verbose_name="相關訂單",
    )
    staff_name = models.CharField(
        max_length=100,
        blank=True,
        db_index=True,
        verbose_name="員工名稱",
    )
    detail = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="詳細資訊",
        help_text="包含舊狀態、新狀態等JSON格式的詳細資訊",
    )
    ip_address = models.GenericIPAddressField(
        blank=True,
        null=True,
        verbose_name="IP 地址",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name="建立時間",
    )

    class Meta:
        app_label = "eshop"
        ordering = ["-created_at"]
        verbose_name = "審計日誌"
        verbose_name_plural = "審計日誌"
        indexes = [
            models.Index(fields=["action", "created_at"], name="audit_action_date_idx"),
            models.Index(fields=["staff_name", "created_at"], name="audit_staff_date_idx"),
        ]

    def __str__(self):
        return f"[{self.created_at:%Y-%m-%d %H:%M}] {self.get_action_display()} - {self.staff_name or '系統'} (訂單 #{self.order_id or 'N/A'})"