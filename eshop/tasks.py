# eshop/tasks.py
# 支付狀態監控
import logging
from datetime import timedelta

from django.utils import timezone

from .models import OrderModel
from .order_status_manager import OrderStatusManager

logger = logging.getLogger(__name__)

# 嘗試導入 Celery，如果不可用則使用同步裝飾器
try:
    from celery import shared_task
except ImportError:
    # Celery 不可用時，提供一個簡單的裝飾器讓任務同步執行
    def shared_task(*args, **kwargs):
        def decorator(f):
            return f

        return decorator if args and callable(args[0]) else decorator


@shared_task
def monitor_pending_payments():
    """監控待支付訂單，自動取消超時訂單"""
    try:
        logger.info("🔄 開始監控待支付訂單...")

        # 超時時間：創建後15分鐘
        timeout_threshold = timezone.now() - timedelta(minutes=15)

        # 查找超時訂單
        timeout_orders = OrderModel.objects.filter(
            payment_status="pending", status="pending", created_at__lt=timeout_threshold
        )

        logger.info(f"找到 {timeout_orders.count()} 個超時待支付訂單")

        cancelled_count = 0
        failed_count = 0

        for order in timeout_orders:
            try:
                # ✅ 修復：使用 OrderStatusManager
                result = OrderStatusManager.mark_as_cancelled_manually(
                    order_id=order.id,
                    staff_name="celery_task_monitor_pending_payments",
                    reason="支付超時自動取消（15分鐘）",
                )

                if result.get("success"):
                    cancelled_count += 1
                    logger.info(f"✅ 自動取消超時訂單: {order.id}")

                    # 發送系統通知（可選）
                    try:
                        from .websocket_utils import send_system_notification

                        send_system_notification(
                            type="order_cancelled",
                            message=f"訂單 #{order.id} 因支付超時已自動取消",
                            data={"order_id": order.id},
                        )
                    except Exception as ws_error:
                        logger.warning(f"發送WebSocket通知失敗: {str(ws_error)}")

                else:
                    failed_count += 1
                    logger.error(
                        f"❌ 取消訂單 {order.id} 失敗: {result.get('message')}"
                    )

            except Exception as e:
                failed_count += 1
                logger.error(f"❌ 處理訂單 {order.id} 時發生異常: {str(e)}")

        logger.info(
            f"監控完成：成功取消 {cancelled_count} 個訂單，失敗 {failed_count} 個"
        )

        return {
            "success": True,
            "cancelled": cancelled_count,
            "failed": failed_count,
            "total_found": timeout_orders.count(),
            "timestamp": timezone.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"❌ 監控待支付訂單任務失敗: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": timezone.now().isoformat(),
        }


@shared_task
def sync_payment_status(order_id):
    """同步支付狀態（對於支付渠道查詢）"""
    try:
        logger.info(f"🔄 開始同步訂單 #{order_id} 支付狀態")

        order = OrderModel.objects.get(id=order_id)

        # 如果已經支付，不需要同步
        if order.payment_status == "paid":
            logger.info(f"訂單 #{order_id} 已支付，跳過同步")
            return {"success": True, "status": "already_paid"}

        # 這裡模擬調用支付渠道API查詢狀態
        # 實際實現需要根據具體的支付渠道（如支付寶、微信）來調用相應的API

        # 示例：模擬查詢邏輯
        payment_method = order.payment_method

        if payment_method == "alipay":
            # 調用支付寶查詢接口
            # payment_result = query_alipay_payment(order.payment_trade_no)
            pass
        elif payment_method == "wechatpay":
            # 調用微信支付查詢接口
            # payment_result = query_wechat_payment(order.payment_trade_no)
            pass
        else:
            logger.warning(f"不支持的支付方式: {payment_method}")
            return {"success": False, "error": f"不支持的支付方式: {payment_method}"}

        # 模擬支付成功
        # 實際應該根據 payment_result 判斷
        payment_success = False  # 改為 True 如果支付成功

        if payment_success:
            # ✅ 使用 OrderStatusManager 處理支付成功
            result = OrderStatusManager.process_payment_success(
                order_id=order_id, request=None  # 在任務中沒有 request 對象
            )

            if result:
                logger.info(f"✅ 訂單 #{order_id} 支付同步成功")
                return {"success": True, "status": "payment_confirmed"}
            else:
                logger.error(f"❌ 訂單 #{order_id} 支付成功但處理失敗")
                return {"success": False, "status": "processing_failed"}
        else:
            # 支付未成功，檢查是否超時
            from datetime import datetime, timedelta

            order_age = timezone.now() - order.created_at

            if order_age > timedelta(minutes=15):
                # 超時，取消訂單
                logger.info(f"訂單 #{order_id} 支付超時，自動取消")

                cancel_result = OrderStatusManager.mark_as_cancelled_manually(
                    order_id=order_id,
                    staff_name="celery_task_sync_payment",
                    reason="支付狀態查詢超時",
                )

                return {
                    "success": cancel_result.get("success", False),
                    "status": "timeout_cancelled",
                    "message": cancel_result.get("message", ""),
                }
            else:
                # 未超時，稍後重試
                logger.info(f"訂單 #{order_id} 支付未完成，稍後重試")
                return {"success": True, "status": "pending_retry"}

    except OrderModel.DoesNotExist:
        logger.error(f"訂單 #{order_id} 不存在")
        return {"success": False, "error": "訂單不存在"}
    except Exception as e:
        logger.error(f"同步支付狀態失敗: {str(e)}")
        return {"success": False, "error": str(e)}


@shared_task
def cleanup_old_queues():
    """清理舊的隊列項目（每天執行）"""
    try:
        logger.info("🔄 開始清理舊隊列項目...")

        from datetime import timedelta

        from django.utils import timezone

        from .models import CoffeeQueue

        # 清理24小時前的已提取/已取消隊列項目
        cutoff_time = timezone.now() - timedelta(hours=24)

        old_ready_queues = CoffeeQueue.objects.filter(
            status="ready", actual_completion_time__lt=cutoff_time
        )

        old_cancelled_queues = CoffeeQueue.objects.filter(
            status="cancelled", updated_at__lt=cutoff_time
        )

        ready_count = old_ready_queues.count()
        cancelled_count = old_cancelled_queues.count()

        # 刪除舊記錄
        deleted_ready = old_ready_queues.delete()[0] if old_ready_queues.exists() else 0
        deleted_cancelled = (
            old_cancelled_queues.delete()[0] if old_cancelled_queues.exists() else 0
        )

        logger.info(
            f"✅ 清理完成：刪除 {deleted_ready} 個舊就緒隊列，{deleted_cancelled} 個舊取消隊列"
        )

        return {
            "success": True,
            "deleted_ready": deleted_ready,
            "deleted_cancelled": deleted_cancelled,
            "total_found": ready_count + cancelled_count,
            "timestamp": timezone.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"❌ 清理舊隊列任務失敗: {str(e)}")
        return {"success": False, "error": str(e)}
