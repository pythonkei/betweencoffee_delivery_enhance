# eshop/order_status/status_display.py
"""
狀態顯示子模組

拆分自 order_status_manager.py
負責訂單狀態的顯示邏輯：
- 獲取顯示狀態資訊
- 純咖啡豆/咖啡訂單狀態
- 佇列資訊與進度計算
- 狀態訊息生成
"""

import logging

from django.utils import timezone

from ..models import CoffeeQueue, OrderModel
from ..time_calculation import unified_time_service
from .order_type_analyzer import OrderTypeAnalyzer

logger = logging.getLogger(__name__)


class StatusDisplay:
    """狀態顯示器 - 處理訂單狀態的顯示邏輯"""

    def __init__(self, order):
        self.order = order
        self.items = order.get_items()

    def get_display_status(self):
        """獲取訂單顯示狀態"""
        order_type = OrderTypeAnalyzer.analyze_order_type(self.order)

        # 基礎狀態 - 修復：使用 payment_status 而不是 is_paid
        status_info = {
            "order": self.order,
            "items": self.order.get_items_with_chinese_options(),
            "payment_status": (
                "paid" if self.order.payment_status == "paid" else "pending"
            ),
            **order_type,
        }

        # 根據訂單類型添加特定資訊
        if order_type["is_beans_only"]:
            # 純咖啡豆訂單：直接完成
            status_info.update(self._get_beans_only_status())
        else:
            # 咖啡訂單或混合訂單：需要製作
            status_info.update(self._get_coffee_order_status())

        # ====== 添加取貨時間資訊（如果適用） ======
        if hasattr(self.order, "pickup_time_choice") and self.order.pickup_time_choice:
            choice_map = {
                "5": "5分鐘後",
                "10": "10分鐘後",
                "15": "15分鐘後",
                "20": "20分鐘後",
                "30": "30分鐘後",
            }
            status_info["pickup_time_display"] = choice_map.get(
                self.order.pickup_time_choice, "5分鐘後"
            )

            # 添加最晚開始時間（如果已計算）
            if (
                hasattr(self.order, "latest_start_time")
                and self.order.latest_start_time
            ):
                status_info["latest_start_time"] = (
                    unified_time_service.format_time_for_display(
                        self.order.latest_start_time, "full"
                    )
                )
                status_info["is_urgent"] = (
                    self.order.should_be_in_queue_by_now()
                    if hasattr(self.order, "should_be_in_queue_by_now")
                    else False
                )

        return status_info

    def _get_beans_only_status(self):
        """獲取純咖啡豆訂單狀態"""
        # 純咖啡豆訂單，支付後直接設置為就緒 - 修復：使用 payment_status
        if self.order.payment_status == "paid" and self.order.status in [
            "pending",
            "waiting",
            "preparing",
        ]:
            self.order.status = "ready"
            self.order.save()
            logger.info(f"純咖啡豆訂單 {self.order.id} 自動設置為就緒狀態")

        return {
            "progress_percentage": 100,
            "progress_display": "100% 完成",
            "show_progress_bar": False,
            "queue_info": None,
            "remaining_minutes": 0,
            "estimated_time": "隨時可取",
            "is_ready": True,
            "status_message": "您的咖啡豆已準備就緒，隨時可以提取！",
        }

    def _get_coffee_order_status(self):
        """獲取咖啡訂單狀態（包含混合訂單）"""
        # 獲取佇列資訊
        queue_info = self._get_queue_info()

        # 計算進度
        progress_info = self._calculate_progress()

        # 確定是否就緒
        is_ready = self.order.status in ["ready", "completed"]

        # 獲取佇列顯示文字
        queue_display, queue_message, remaining_display = self._get_queue_display_text(
            queue_info
        )

        # 格式化預計時間（香港時區）
        estimated_time_display = (
            unified_time_service.format_time_for_display(
                self.order.estimated_ready_time, "full"
            )
            if self.order.estimated_ready_time
            else "計算中..."
        )

        # 獲取訂單狀態訊息
        status_message = self._get_status_message(is_ready)

        # 構建狀態資訊 - 修復：使用 payment_status
        status_info = {
            "queue_info": queue_info,
            "progress_percentage": progress_info["percentage"],
            "progress_display": progress_info["display"],
            "show_progress_bar": self.order.payment_status == "paid"
            and not OrderTypeAnalyzer.analyze_order_type(self.order)["is_beans_only"],
            "remaining_minutes": self._get_remaining_minutes(),
            "estimated_time": estimated_time_display,
            "is_ready": is_ready,
            # ✅ 確保模板需要的欄位都存在
            "queue_display": queue_display,
            "queue_message": queue_message,
            "remaining_display": remaining_display,
            "status_message": status_message,
        }

        return status_info

    def _get_status_message(self, is_ready):
        """獲取狀態訊息"""
        if is_ready:
            order_type = OrderTypeAnalyzer.analyze_order_type(self.order)
            if order_type["is_mixed_order"]:
                return "您訂購的商品已準備就緒，隨時可以提取！"
            else:
                return "您的咖啡已準備就緒，隨時可以提取！"
        else:
            return "您的訂單正在製作中，請耐心等候..."

    def _get_queue_display_text(self, queue_info):
        """生成佇列顯示文字 - 增強版：利用新的佇列資訊"""
        if not queue_info:
            return "等待加入佇列...", "系統正在處理您的訂單", ""

        queue_position = queue_info["queue_position"]
        wait_minutes = queue_info["queue_wait_minutes"]
        total_minutes = queue_info["total_minutes"]
        has_preparing_items = queue_info.get("has_preparing_items", False)
        waiting_items_count = queue_info.get("waiting_items_count", 0)
        preparing_items_count = queue_info.get("preparing_items_count", 0)

        # 佇列狀態文字 - 更詳細的顯示
        if wait_minutes < 1:
            wait_display = "即將開始"
        else:
            wait_display = f"{wait_minutes}分鐘"

        queue_display = f"佇列位置: #{queue_position} | 預計等待: {wait_display}"

        # 佇列訊息 - 根據佇列狀態提供更準確的資訊
        if queue_position == 1:
            if has_preparing_items:
                queue_message = "當前訂單正在製作中，即將輪到您！"
            else:
                queue_message = "下一個就輪到您了！"
        elif queue_position <= 3:
            if preparing_items_count > 0:
                queue_message = f"前面有 {preparing_items_count} 個正在製作，{waiting_items_count} 個等待中"
            else:
                queue_message = f"前面還有 {queue_position - 1} 個訂單等待中"
        else:
            if preparing_items_count > 0:
                queue_message = f"目前有 {preparing_items_count} 個正在製作，{waiting_items_count} 個等待中"
            else:
                queue_message = "目前訂單較多，請耐心等候"

        # 剩餘時間顯示 - 更準確的描述
        if total_minutes < 1:
            remaining_display = "(即將完成)"
        elif total_minutes <= 5:
            remaining_display = f"(約{total_minutes}分鐘後完成)"
        else:
            remaining_display = f"(約{total_minutes}分鐘後)"

        return queue_display, queue_message, remaining_display

    def _get_queue_info(self):
        """獲取佇列資訊 - 從 CoffeeQueue 模型獲取"""
        try:
            queue_item = CoffeeQueue.objects.filter(order=self.order).first()
            if not queue_item:
                return None

            # 獲取佇列中所有項目的資訊
            all_queue_items = CoffeeQueue.objects.filter(
                status__in=["waiting", "preparing"]
            ).order_by("position")

            # 計算當前訂單在佇列中的位置
            current_position = None
            waiting_items_count = 0
            preparing_items_count = 0

            for idx, item in enumerate(all_queue_items, 1):
                if item.order_id == self.order.id:
                    current_position = idx
                if item.status == "waiting":
                    waiting_items_count += 1
                elif item.status == "preparing":
                    preparing_items_count += 1

            if current_position is None:
                return None

            # 計算預計等待時間
            from ..time_calculation import unified_time_service

            wait_time = unified_time_service.calculate_queue_wait_time(current_position)

            return {
                "queue_position": current_position,
                "queue_wait_minutes": wait_time,
                "total_minutes": wait_time,
                "has_preparing_items": preparing_items_count > 0,
                "waiting_items_count": waiting_items_count,
                "preparing_items_count": preparing_items_count,
            }

        except Exception as e:
            logger.error(f"獲取佇列資訊失敗: {str(e)}")
            return None

    def _calculate_progress(self):
        """計算訂單進度"""
        try:
            if self.order.status == "ready":
                return {"percentage": 100, "display": "100% 完成"}
            elif self.order.status == "preparing":
                # 根據已製作時間計算進度
                if (
                    self.order.preparation_started_at
                    and self.order.estimated_ready_time
                ):
                    now = timezone.now()
                    total_duration = (
                        self.order.estimated_ready_time
                        - self.order.preparation_started_at
                    ).total_seconds()
                    elapsed = (now - self.order.preparation_started_at).total_seconds()

                    if total_duration > 0:
                        percentage = min(int((elapsed / total_duration) * 100), 99)
                        return {
                            "percentage": percentage,
                            "display": f"{percentage}% 完成",
                        }
                return {"percentage": 50, "display": "50% 完成"}
            elif self.order.status == "waiting":
                return {"percentage": 25, "display": "等待中"}
            else:
                return {"percentage": 0, "display": "處理中"}
        except Exception as e:
            logger.error(f"計算進度失敗: {str(e)}")
            return {"percentage": 0, "display": "計算中..."}

    def _get_remaining_minutes(self):
        """獲取剩餘分鐘數"""
        try:
            if self.order.estimated_ready_time:
                now = timezone.now()
                remaining = (self.order.estimated_ready_time - now).total_seconds() / 60
                return max(0, int(remaining))
            return 0
        except Exception:
            return 0
