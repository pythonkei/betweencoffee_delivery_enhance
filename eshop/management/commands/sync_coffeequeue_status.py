"""
管理命令：同步 CoffeeQueue.status 與 OrderModel.status

問題背景：
- CoffeeQueue.status 與 OrderModel.status 存在大量不同步（686 條髒資料）
- 根本原因：process_order_status_change 方法未同步更新 CoffeeQueue.status
- 本命令用於一次性清理現有髒資料

修復策略：
1. 找出所有 CoffeeQueue.status != OrderModel.status 的記錄
2. 根據 OrderModel.status 更新 CoffeeQueue.status
3. 特殊情況處理：
   - OrderModel.status='completed' → CoffeeQueue.status='completed', position=0
   - OrderModel.status='ready' → CoffeeQueue.status='ready', position=0
   - OrderModel.status='preparing' → CoffeeQueue.status='preparing'
   - OrderModel.status='waiting' → CoffeeQueue.status='waiting'
   - OrderModel.status='cancelled' → CoffeeQueue.status='cancelled'
   - OrderModel.status='pending' → CoffeeQueue.status='pending'
   - OrderModel.status='payment_pending' → CoffeeQueue.status='payment_pending'
4. 清理孤立的 CoffeeQueue 記錄（無對應 OrderModel）
"""

import logging

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from eshop.models import CoffeeQueue, OrderModel

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "同步 CoffeeQueue.status 與 OrderModel.status，清理髒資料"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="僅顯示將要進行的操作，不實際執行",
        )
        parser.add_argument(
            "--verbose",
            action="store_true",
            help="顯示詳細的每筆記錄資訊",
        )

    def handle(self, *args, **options):
        dry_run = options.get("dry_run", False)
        verbose = options.get("verbose", False)

        self.stdout.write(self.style.WARNING("=" * 70))
        self.stdout.write(self.style.WARNING("CoffeeQueue.status 同步工具"))
        self.stdout.write(
            self.style.WARNING(
                f'模式: {"🔍 預覽 (dry-run)" if dry_run else "🔧 實際執行"}'
            )
        )
        self.stdout.write(self.style.WARNING("=" * 70))

        # ===== 步驟 1：找出不同步的記錄 =====
        self.stdout.write("\n📊 步驟 1：分析不同步記錄...")

        # 使用 SQL JOIN 找出不同步的記錄
        from django.db import connection

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT 
                    cq.id,
                    cq.order_id,
                    cq.status AS queue_status,
                    om.status AS order_status,
                    cq.position,
                    cq.barista
                FROM eshop_coffeequeue cq
                INNER JOIN eshop_ordermodel om ON cq.order_id = om.id
                WHERE cq.status != om.status
                ORDER BY cq.order_id
            """
            )
            unsynced_rows = cursor.fetchall()

        total_unsynced = len(unsynced_rows)
        self.stdout.write(f"   找到 {total_unsynced} 條不同步記錄")

        if total_unsynced == 0:
            self.stdout.write(self.style.SUCCESS("\n✅ 沒有發現不同步記錄！"))
            return

        # ===== 統計不同步類型 =====
        stats = {}
        for row in unsynced_rows:
            key = f"{row[2]} → {row[3]}"
            stats[key] = stats.get(key, 0) + 1

        self.stdout.write("\n📈 不同步類型統計：")
        for key, count in sorted(stats.items()):
            self.stdout.write(f"   CoffeeQueue.{key}: {count} 條")

        if verbose:
            self.stdout.write("\n📝 詳細記錄：")
            for row in unsynced_rows:
                self.stdout.write(
                    f"   CoffeeQueue #{row[0]} (Order #{row[1]}): "
                    f"status={row[2]} → {row[3]}, "
                    f'position={row[4]}, barista={row[5] or "N/A"}'
                )

        if dry_run:
            self.stdout.write(self.style.WARNING("\n🔍 Dry-run 模式，未執行任何修改。"))
            self.stdout.write(
                self.style.SUCCESS(f"使用 --no-dry-run 參數執行實際同步。")
            )
            return

        # ===== 步驟 2：執行同步 =====
        self.stdout.write("\n🔧 步驟 2：執行同步...")

        updated_count = 0
        error_count = 0
        now = timezone.now()

        with transaction.atomic():
            for row in unsynced_rows:
                queue_id, order_id, queue_status, order_status, position, barista = row
                try:
                    queue_item = CoffeeQueue.objects.get(id=queue_id)

                    # 根據 OrderModel.status 更新 CoffeeQueue
                    queue_item.status = order_status

                    # 特殊處理：completed/ready 狀態清理 position
                    if order_status in ["ready", "completed"]:
                        queue_item.position = 0
                        if order_status == "completed":
                            queue_item.actual_completion_time = now

                    queue_item.save(
                        update_fields=["status", "position", "actual_completion_time"]
                    )
                    updated_count += 1

                    if verbose:
                        self.stdout.write(
                            f"   ✅ CoffeeQueue #{queue_id} (Order #{order_id}): "
                            f"{queue_status} → {order_status}"
                        )

                except CoffeeQueue.DoesNotExist:
                    self.stdout.write(
                        self.style.ERROR(f"   ❌ CoffeeQueue #{queue_id} 不存在")
                    )
                    error_count += 1
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(
                            f"   ❌ CoffeeQueue #{queue_id} 同步失敗: {str(e)}"
                        )
                    )
                    error_count += 1

        # ===== 步驟 3：清理孤立的 CoffeeQueue 記錄 =====
        self.stdout.write("\n🧹 步驟 3：清理孤立的 CoffeeQueue 記錄...")

        orphaned = CoffeeQueue.objects.filter(
            order__isnull=True
        ) | CoffeeQueue.objects.exclude(order_id__in=OrderModel.objects.values("id"))
        orphaned_count = orphaned.count()

        if orphaned_count > 0:
            self.stdout.write(f"   找到 {orphaned_count} 條孤立記錄")
            deleted_count = orphaned.delete()[0]
            self.stdout.write(f"   已刪除 {deleted_count} 條孤立記錄")
        else:
            self.stdout.write("   沒有發現孤立記錄")

        # ===== 結果總結 =====
        self.stdout.write("\n" + "=" * 70)
        self.stdout.write(self.style.SUCCESS("✅ 同步完成！"))
        self.stdout.write(f"   成功同步: {updated_count} 條")
        self.stdout.write(f"   失敗: {error_count} 條")
        self.stdout.write(
            f"   刪除孤立記錄: {orphaned_count if orphaned_count > 0 else 0} 條"
        )
        self.stdout.write("=" * 70)

        # 最終驗證
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM eshop_coffeequeue cq
                INNER JOIN eshop_ordermodel om ON cq.order_id = om.id
                WHERE cq.status != om.status
            """
            )
            remaining = cursor.fetchone()[0]

        if remaining == 0:
            self.stdout.write(self.style.SUCCESS("\n✅ 所有記錄已同步完成！"))
        else:
            self.stdout.write(
                self.style.WARNING(
                    f"\n⚠️ 仍有 {remaining} 條記錄未同步（可能是在執行期間新增的）"
                )
            )
