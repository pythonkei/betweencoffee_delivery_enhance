# eshop/management/commands/batch_cancel_pending_orders.py
"""
批次取消指定用戶的所有未完成訂單的管理命令。

用法:
    # 預覽模式（不實際執行）
    python manage.py batch_cancel_pending_orders --username kei --dry-run

    # 實際執行
    python manage.py batch_cancel_pending_orders --username kei

    # 指定其他用戶
    python manage.py batch_cancel_pending_orders --username other_user

    # 同時處理 CoffeeQueue 中的相關記錄
    python manage.py batch_cancel_pending_orders --username kei --clean-queue
"""

import logging

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from eshop.models import CoffeeQueue, OrderModel
from eshop.order_status_manager import OrderStatusManager

logger = logging.getLogger(__name__)
User = get_user_model()


class Command(BaseCommand):
    help = "批次取消指定用戶的所有未完成訂單"

    def add_arguments(self, parser):
        parser.add_argument(
            "--username",
            type=str,
            default="kei",
            help="要清除訂單的用戶名（預設: kei）",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="預覽模式：只顯示將被取消的訂單，不實際執行",
        )
        parser.add_argument(
            "--clean-queue",
            action="store_true",
            help="同時清理 CoffeeQueue 中的相關記錄",
        )

    def handle(self, *args, **options):
        username = options["username"]
        dry_run = options["dry_run"]
        clean_queue = options["clean_queue"]

        # 1. 查找用戶
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise CommandError(f"找不到用戶: {username}")

        self.stdout.write(f"🔍 正在處理用戶: {username} (ID: {user.id})")

        # 2. 查找未完成訂單
        pending_orders = OrderModel.objects.filter(
            user=user, payment_status="pending", status__in=["pending", "waiting"]
        ).order_by("created_at")

        total_count = pending_orders.count()
        self.stdout.write(f"📊 找到 {total_count} 筆未完成訂單")

        if total_count == 0:
            self.stdout.write(self.style.SUCCESS("✅ 沒有需要處理的訂單"))
            return

        # 3. 顯示訂單列表
        self.stdout.write("\n📋 訂單列表:")
        self.stdout.write("-" * 80)
        self.stdout.write(f'{"ID":>6} | {"狀態":<10} | {"建立時間":<25}')
        self.stdout.write("-" * 80)

        for order in pending_orders:
            created_str = order.created_at.strftime("%Y-%m-%d %H:%M:%S")
            self.stdout.write(f"{order.id:>6} | {order.status:<10} | {created_str:<25}")

        self.stdout.write("-" * 80)
        self.stdout.write(f"總計: {total_count} 筆訂單\n")

        # 4. 如果是預覽模式，到此為止
        if dry_run:
            self.stdout.write(self.style.WARNING("⚠️ 預覽模式 -- 未執行任何操作"))
            self.stdout.write(
                "執行 `python manage.py batch_cancel_pending_orders "
                "--username kei` 來實際取消這些訂單"
            )
            return

        # 5. 實際執行取消
        self.stdout.write("🔄 開始批次取消訂單...")

        success_count = 0
        fail_count = 0
        failed_ids = []

        for order in pending_orders:
            try:
                result = OrderStatusManager.mark_as_cancelled_manually(
                    order_id=order.id, staff_name="system", reason="批次清除未完成訂單"
                )

                if result.get("success"):
                    success_count += 1
                    self.stdout.write(f"  ✅ 訂單 #{order.id} 已取消", ending="\n")
                else:
                    fail_count += 1
                    failed_ids.append(order.id)
                    self.stdout.write(
                        self.style.ERROR(
                            f"  ❌ 訂單 #{order.id} 取消失敗: "
                            f'{result.get("message", "未知錯誤")}'
                        )
                    )

            except Exception as e:
                fail_count += 1
                failed_ids.append(order.id)
                self.stdout.write(
                    self.style.ERROR(f"  ❌ 訂單 #{order.id} 取消失敗: {str(e)}")
                )

        # 6. 清理 CoffeeQueue（可選）
        if clean_queue and success_count > 0:
            self.stdout.write("\n🔄 清理 CoffeeQueue 記錄...")
            queue_items = CoffeeQueue.objects.filter(
                order__in=pending_orders.values_list("id", flat=True)
            )
            queue_count = queue_items.count()
            queue_items.delete()
            self.stdout.write(f"  ✅ 已清理 {queue_count} 筆隊列記錄")

        # 7. 顯示結果
        self.stdout.write("\n" + "=" * 50)
        self.stdout.write("📊 處理結果")
        self.stdout.write("=" * 50)
        self.stdout.write(self.style.SUCCESS(f"✅ 成功: {success_count} 筆"))

        if fail_count > 0:
            self.stdout.write(self.style.ERROR(f"❌ 失敗: {fail_count} 筆"))
            self.stdout.write(f"失敗的訂單 ID: {failed_ids}")
        else:
            self.stdout.write("❌ 失敗: 0 筆")

        self.stdout.write("=" * 50)

        if success_count > 0:
            self.stdout.write(
                self.style.SUCCESS(f"\n🎉 已成功取消 {success_count} 筆未完成訂單")
            )
