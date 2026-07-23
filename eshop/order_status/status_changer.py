# eshop/order_status/status_changer.py
"""
狀態變更子模組

拆分自 order_status_manager.py
負責訂單狀態的變更操作：
- 訂單狀態變化處理（含 CoffeeQueue 同步）
- 批量狀態變化處理
- 手動標記：等待中/已取消/製作中/就緒/已完成
- WebSocket 通知發送
"""

import logging
import threading
from datetime import timedelta

from django.utils import timezone

from ..models import CoffeeQueue, OrderModel
from ..time_calculation import unified_time_service
from .order_type_analyzer import OrderTypeAnalyzer

logger = logging.getLogger(__name__)


class StatusChanger:
    """狀態變更器 - 處理訂單狀態的變更操作"""

    def __init__(self, order):
        self.order = order
        self.items = order.get_items()

    # ==================== 業務邏輯：處理訂單狀態變化的統一方法 ====================

    @classmethod
    def process_order_status_change(cls, order_id, new_status, staff_name=None):
        """處理訂單狀態變化的統一邏輯 - 包含統一時間計算"""
        try:
            logger.info(f"🔄 處理訂單 #{order_id} 狀態變化: {new_status}")

            order = OrderModel.objects.get(id=order_id)
            old_status = order.status

            # 更新訂單狀態
            order.status = new_status

            # 根據狀態設置時間戳
            now = timezone.now()
            if new_status == "preparing":
                order.preparation_started_at = now
            elif new_status == "ready":
                order.ready_at = now
            elif new_status == "completed":
                order.picked_up_at = now

            order.save()
            logger.info(f"✅ 訂單 #{order_id} 狀態已更新: {old_status} → {new_status}")

            # ✅ 重要：同步更新 CoffeeQueue.status（確保與 OrderModel.status 一致）
            queue_item = CoffeeQueue.objects.filter(order=order).first()
            if queue_item:
                old_queue_status = queue_item.status
                queue_item.status = new_status

                # 根據狀態設置時間戳
                if new_status == "preparing":
                    queue_item.actual_start_time = now
                elif new_status == "ready":
                    queue_item.actual_completion_time = now
                    queue_item.position = 0  # 清理隊列位置
                elif new_status == "completed":
                    queue_item.position = 0  # 清理隊列位置

                queue_item.save()
                logger.info(
                    f"✅ 訂單 #{order_id} CoffeeQueue 狀態已同步: "
                    f"{old_queue_status} → {new_status}"
                )
            else:
                logger.warning(f"⚠️ 訂單 #{order_id} 無對應 CoffeeQueue 記錄")

            # ✅ 重要：觸發統一時間計算
            from ..queue_manager_refactored import CoffeeQueueManager

            queue_manager = CoffeeQueueManager()

            logger.info(f"🔄 訂單狀態變化，開始統一時間計算...")
            time_result = queue_manager.recalculate_all_order_times()

            if time_result.get("success"):
                logger.info(f"✅ 訂單狀態變化後時間計算完成")
            else:
                logger.warning(
                    f"⚠️ 訂單狀態變化後時間計算有問題: {time_result.get('message')}"
                )

            # ============================================================
            # 🔧 修復：發送WebSocket通知（統一使用 'status' 類型）
            # ============================================================
            try:
                from ..websocket_utils import send_order_update

                send_order_update(
                    order_id=order_id,
                    update_type="status",
                    data={
                        "status": new_status,
                        "status_display": order.get_status_display(),
                        "message": f"訂單狀態已更新為 {new_status}",
                    },
                )
                logger.info(f"✅ 已發送訂單 #{order_id} 狀態更新 WebSocket 通知")
            except Exception as ws_error:
                logger.error(f"發送WebSocket通知失敗: {str(ws_error)}")

            return {
                "success": True,
                "order_id": order_id,
                "old_status": old_status,
                "new_status": new_status,
                "time_recalculated": True,
            }

        except OrderModel.DoesNotExist:
            logger.error(f"❌ 訂單 #{order_id} 不存在")
            return {"success": False, "error": "訂單不存在"}
        except Exception as e:
            logger.error(f"❌ 處理訂單狀態變化失敗: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e)}

    # ✅ 新增：批量處理多個訂單狀態變化
    @classmethod
    def process_batch_status_changes(cls, order_status_list):
        """批量處理多個訂單狀態變化 - 效率更高"""
        try:
            logger.info(f"🔄 批量處理 {len(order_status_list)} 個訂單狀態變化")

            results = []
            for order_id, new_status in order_status_list:
                result = cls.process_order_status_change(order_id, new_status)
                results.append(result)

            # 批量處理後統一計算時間（只計算一次）
            logger.info(f"🔄 批量處理完成，開始統一時間計算...")
            from ..queue_manager_refactored import CoffeeQueueManager

            queue_manager = CoffeeQueueManager()

            time_result = queue_manager.recalculate_all_order_times()

            logger.info(
                f"✅ 批量處理完成，統一時間計算結果: {time_result.get('success')}"
            )

            return {"success": True, "results": results, "time_recalculated": True}

        except Exception as e:
            logger.error(f"❌ 批量處理訂單狀態變化失敗: {str(e)}")
            return {"success": False, "error": str(e)}

    # ==================== 手動標記方法 ====================

    @classmethod
    def mark_as_waiting_manually(cls, order_id, staff_name=None):
        """手動將訂單標記為等待中"""
        try:
            order = OrderModel.objects.get(id=order_id)
            old_status = order.status

            # 驗證狀態轉換
            if old_status not in ["pending", "preparing", "ready"]:
                raise ValueError(f"無法從狀態 {old_status} 轉換為 waiting")

            order.status = "waiting"
            order.preparation_started_at = None
            order.estimated_ready_time = None
            order.save(
                update_fields=[
                    "status",
                    "preparation_started_at",
                    "estimated_ready_time",
                ]
            )

            # 更新隊列項
            queue_item = CoffeeQueue.objects.filter(order=order).first()
            if queue_item:
                queue_item.status = "waiting"
                queue_item.actual_start_time = None
                queue_item.save()

            logger.info(
                f"Order {order_id} marked as waiting by {staff_name or 'system'}"
            )
            return {"success": True, "order": order}

        except Exception as e:
            logger.error(f"標記訂單 {order_id} 為等待中失敗: {str(e)}")
            return {"success": False, "message": str(e)}

    @classmethod
    def mark_as_cancelled_manually(cls, order_id, staff_name=None, reason=None):
        """手動將訂單標記為已取消"""
        try:
            order = OrderModel.objects.get(id=order_id)
            old_status = order.status

            # 檢查是否可以取消
            if old_status in ["completed", "cancelled"]:
                return {"success": False, "message": f"訂單已{old_status}，無法取消"}

            order.status = "cancelled"
            order.payment_status = "cancelled"

            order.save(update_fields=["status", "payment_status"])

            # 更新隊列項
            queue_item = CoffeeQueue.objects.filter(order=order).first()
            if queue_item:
                queue_item.status = "cancelled"
                queue_item.save()

            logger.info(
                f"Order {order_id} cancelled by {staff_name or 'system'}. Reason: {reason}"
            )
            return {"success": True, "order": order}

        except Exception as e:
            logger.error(f"取消訂單 {order_id} 失敗: {str(e)}")
            return {"success": False, "message": str(e)}

    @classmethod
    def mark_as_preparing_manually(
        cls, order_id, barista_name=None, preparation_minutes=None
    ):
        """手動將訂單標記為製作中（員工操作）- 優化版本"""
        try:
            # 獲取訂單
            order = OrderModel.objects.get(id=order_id)

            # 檢查訂單狀態
            if order.status not in ["waiting", "pending", "confirmed"]:
                msg = f"訂單狀態 {order.status} 不允許開始製作"
                raise ValueError(msg)

            # 檢查支付狀態
            if order.payment_status != "paid":
                raise ValueError("訂單未支付，無法開始製作")

            # 計算製作時間（如果未提供）
            if preparation_minutes is None:
                items = order.get_items()
                coffee_count = sum(
                    item.get("quantity", 1)
                    for item in items
                    if item.get("type") == "coffee"
                )

                from ..queue_manager_refactored import CoffeeQueueManager

                queue_manager = CoffeeQueueManager()

                if coffee_count > 0:
                    preparation_minutes = queue_manager.calculate_preparation_time(
                        coffee_count
                    )
                else:
                    preparation_minutes = 5

            # ====== 階段1優化：立即更新數據庫並發送WebSocket通知 ======
            old_status = order.status

            # 1. 更新訂單狀態
            order.status = "preparing"
            order.preparation_started_at = timezone.now()

            # 計算預計完成時間（使用新的時間服務）
            hk_time = unified_time_service.get_hong_kong_time()
            order.estimated_ready_time = hk_time + timedelta(
                minutes=preparation_minutes
            )

            # 2. 立即保存訂單狀態
            order.save(
                update_fields=[
                    "status",
                    "preparation_started_at",
                    "estimated_ready_time",
                ]
            )
            logger.info(f"✅ 訂單 #{order_id} 狀態已更新: {old_status} → preparing")

            # 3. 立即發送WebSocket通知（不等待其他處理）
            try:
                from ..websocket_utils import send_order_update

                estimated_time = None
                if order.estimated_ready_time:
                    estimated_time = order.estimated_ready_time.isoformat()

                send_order_update(
                    order_id=order_id,
                    update_type="status",
                    data={
                        "status": "preparing",
                        "status_display": "製作中",
                        "message": "咖啡正在製作中！",
                        "timestamp": timezone.now().isoformat(),
                        "estimated_ready_time": estimated_time,
                    },
                )
                logger.info(f"✅ 已立即發送訂單 #{order_id} 狀態更新 WebSocket 通知")
            except Exception as ws_error:
                logger.error(f"❌ 發送WebSocket通知失敗: {str(ws_error)}")

            # 4. 更新隊列項（在WebSocket通知後處理）
            queue_item = CoffeeQueue.objects.filter(order=order).first()
            if queue_item:
                queue_item.status = "preparing"
                queue_item.actual_start_time = timezone.now()
                queue_item.estimated_completion_time = hk_time + timedelta(
                    minutes=preparation_minutes
                )
                if barista_name:
                    queue_item.barista = barista_name
                queue_item.save()
                logger.info(f"✅ 訂單 #{order_id} 隊列項已更新")

            # 5. 更新隊列時間（異步處理，不阻塞響應）
            try:
                from ..queue_manager_refactored import CoffeeQueueManager

                queue_manager = CoffeeQueueManager()

                def async_update_queue_times():
                    try:
                        queue_manager.update_estimated_times()
                        logger.info(f"✅ 訂單 #{order_id} 隊列時間已異步更新")
                    except Exception as e:
                        logger.error(f"❌ 異步更新隊列時間失敗: {str(e)}")

                thread = threading.Thread(target=async_update_queue_times)
                thread.daemon = True
                thread.start()

            except Exception as queue_error:
                logger.error(f"❌ 隊列時間更新失敗: {str(queue_error)}")

            # 6. 記錄日誌
            logger.info(
                f"✅ 訂單 #{order_id} 已開始製作，操作員: {barista_name or 'system'}"
            )

            return {
                "success": True,
                "order": order,
                "queue_item": queue_item,
                "preparation_minutes": preparation_minutes,
                "message": f"訂單 #{order_id} 已開始製作",
                "websocket_sent": True,
                "timestamp": timezone.now().isoformat(),
            }

        except OrderModel.DoesNotExist:
            logger.error(f"❌ 訂單 {order_id} 不存在")
            return {"success": False, "message": "訂單不存在"}
        except Exception as e:
            logger.error(
                f"❌ 標記訂單 {order_id} 為製作中失敗: {str(e)}", exc_info=True
            )
            return {"success": False, "message": str(e)}

    @classmethod
    def mark_as_ready_manually(cls, order_id, staff_name=None):
        """手動將訂單標記為就緒"""
        try:
            order = OrderModel.objects.get(id=order_id)

            # 檢查狀態轉換是否允許
            if order.status != "preparing":
                raise ValueError(f"訂單狀態 {order.status} 不能直接標記為就緒")

            # 更新訂單狀態
            order.status = "ready"
            order.ready_at = timezone.now()

            # 確保預計就緒時間已設置
            if not order.estimated_ready_time:
                order.estimated_ready_time = timezone.now()

            order.save(update_fields=["status", "ready_at", "estimated_ready_time"])

            # 更新隊列項 - 關鍵修復：清理隊列位置
            queue_item = CoffeeQueue.objects.filter(order=order).first()
            if queue_item:
                old_position = queue_item.position
                queue_item.status = "ready"
                queue_item.position = 0  # ✅ 重要：清理隊列位置
                queue_item.actual_completion_time = timezone.now()
                queue_item.save()

                logger.info(
                    f"✅ 訂單 #{order_id} 隊列項已更新: 狀態 → ready, 位置 {old_position} → 0"
                )

            # 發送 WebSocket 通知
            try:
                from ..websocket_utils import send_order_update, send_staff_action

                # 通知顧客訂單狀態更新
                send_order_update(
                    order_id=order_id,
                    update_type="status",
                    data={
                        "status": "ready",
                        "status_display": "已就緒",
                        "message": f"訂單 #{order_id} 已就緒，請取餐！",
                    },
                )

                # 通知員工端
                send_staff_action(
                    order_id=order_id,
                    action="marked_ready",
                    staff_name=staff_name,
                    message=f"訂單 #{order_id} 已就緒",
                )
                logger.info(f"✅ 已發送訂單 #{order_id} 就緒 WebSocket 通知")
            except Exception as ws_error:
                logger.error(f"❌ 發送 WebSocket 通知失敗: {str(ws_error)}")

            logger.info(f"Order {order_id} marked as ready by {staff_name or 'system'}")
            return {"success": True, "order": order, "queue_item": queue_item}

        except Exception as e:
            logger.error(f"標記訂單 {order_id} 為就緒失敗: {str(e)}")
            return {"success": False, "message": str(e)}

    @classmethod
    def mark_as_completed_manually(cls, order_id, staff_name=None):
        """手動將訂單標記為已提取 - 員工操作"""
        try:
            logger.info(f"👨‍🍳 員工 {staff_name} 手動標記訂單 #{order_id} 為已提取")

            result = cls.process_order_status_change(
                order_id=order_id, new_status="completed", staff_name=staff_name
            )

            if result.get("success"):
                logger.info(f"✅ 訂單 #{order_id} 已成功標記為已提取")
            else:
                logger.error(
                    f"❌ 標記訂單 #{order_id} 為已提取失敗: {result.get('error')}"
                )

            return result

        except Exception as e:
            logger.error(f"❌ 標記訂單 {order_id} 為已提取失敗: {str(e)}")
            return {"success": False, "message": str(e)}
