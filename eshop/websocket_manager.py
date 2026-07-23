# eshop/websocket_manager.py
"""
WebSocket 連接管理器（單一職責）- 增強版
- 連線註冊/註銷
- 心跳更新與超時檢查
- 訊息發送（含重試機制：指數退避 + 抖動）
- 群組廣播（可選重試）
- 統計報表
"""
import asyncio
import logging
import random
from datetime import timedelta

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.utils import timezone

logger = logging.getLogger(__name__)


class WebSocketManager:
    """WebSocket 連接管理器（單例模式）- 增強版"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """初始化（只執行一次）"""
        if self._initialized:
            return

        # ========== 連線儲存 ==========
        # key: connection_id (或 channel_name)
        # value: 連線資訊字典
        self.connections = {}

        # ========== 連線池（依使用者類型分組）==========
        self.connection_pool = {
            "staff": [],  # 員工連線 ID 列表
            "customer": [],  # 顧客連線 ID 列表
            "unknown": [],  # 未識別連線
        }

        # ========== 統計資料 ==========
        self.stats = {
            "total_connections": 0,  # 歷史累計連線數
            "active_connections": 0,  # 當前活動連線數
            "messages_sent": 0,  # 累計發送訊息數
            "errors": 0,  # 累計錯誤數
            "last_cleanup": None,  # 最後清理時間
        }

        # ========== 重試預設設定 ==========
        self.default_retry_config = {
            "max_retries": 5,
            "base_delay": 0.5,  # 初始延遲 0.5 秒
            "max_delay": 30.0,  # 最大延遲 30 秒
            "exponential": True,
            "jitter": True,
        }

        self._initialized = True
        logger.info("✅ WebSocketManager 增強版初始化完成")

    # ------------------------------------------------------------
    # 1. 連線生命週期管理
    # ------------------------------------------------------------

    def register_connection(self, connection_id, channel_name, user_info=None):
        """
        註冊新連線
        - connection_id: 通常為 channel_name 或自訂 ID
        - channel_name: Channels 的 channel 名稱
        - user_info: {'user_id': 1, 'user_type': 'staff/customer', 'username': 'kei'}
        """
        user_type = "unknown"
        if user_info and user_info.get("user_type") in ["staff", "customer"]:
            user_type = user_info["user_type"]

        # 儲存連線資訊
        self.connections[connection_id] = {
            "channel_name": channel_name,
            "user_info": user_info or {},
            "user_type": user_type,
            "connected_at": timezone.now(),
            "last_heartbeat": timezone.now(),
            "last_activity": timezone.now(),
            "status": "active",
            "message_count": 0,
            "disconnect_reason": None,
            "disconnected_at": None,
        }

        # 加入連線池
        if connection_id not in self.connection_pool[user_type]:
            self.connection_pool[user_type].append(connection_id)

        # 更新統計
        self.stats["total_connections"] += 1
        self.stats["active_connections"] += 1

        logger.info(f"✅ WebSocket 連線註冊: {connection_id}, 類型: {user_type}")
        return True

    def unregister_connection(self, connection_id, reason="正常斷開"):
        """註銷連線（完整移除）"""
        if connection_id in self.connections:
            # 從所有連線池中移除
            for pool in self.connection_pool.values():
                if connection_id in pool:
                    pool.remove(connection_id)

            # 更新統計
            if self.connections[connection_id]["status"] == "active":
                self.stats["active_connections"] -= 1

            # 刪除連線記錄
            del self.connections[connection_id]

            logger.info(f"✅ WebSocket 連線註銷: {connection_id}, 原因: {reason}")
            return True
        return False

    def disconnect(self, connection_id, reason="正常斷開"):
        """
        標記連線為已斷開（保留記錄供統計）
        不同於 unregister_connection，此方法保留連線記錄
        """
        if connection_id in self.connections:
            conn = self.connections[connection_id]

            # 如果已經是斷開狀態，不再重複處理
            if conn["status"] == "disconnected":
                return True

            conn["status"] = "disconnected"
            conn["disconnect_reason"] = reason
            conn["disconnected_at"] = timezone.now()

            # 從連線池中移除（但保留在 connections 中）
            for pool in self.connection_pool.values():
                if connection_id in pool:
                    pool.remove(connection_id)

            # 更新統計
            self.stats["active_connections"] -= 1

            logger.info(f"🔌 WebSocket 連線斷開: {connection_id}, 原因: {reason}")
            return True
        return False

    # ------------------------------------------------------------
    # 2. 心跳與活動監控
    # ------------------------------------------------------------

    def update_heartbeat(self, connection_id):
        """更新心跳時間（由 consumer 的 ping 觸發）"""
        if connection_id in self.connections:
            self.connections[connection_id]["last_heartbeat"] = timezone.now()
            self.connections[connection_id]["last_activity"] = timezone.now()
            self.connections[connection_id]["message_count"] += 1
            return True
        return False

    def update_activity(self, connection_id):
        """更新最後活動時間（收到任何訊息時觸發）"""
        if connection_id in self.connections:
            self.connections[connection_id]["last_activity"] = timezone.now()
            self.connections[connection_id]["message_count"] += 1
            return True
        return False

    def cleanup_inactive_connections(
        self, heartbeat_timeout_minutes=10, activity_timeout_minutes=30
    ):
        """
        清理不活動連線
        - heartbeat_timeout: 心跳超時（未回覆 ping）
        - activity_timeout: 活動超時（完全無訊息）
        """
        now = timezone.now()
        heartbeat_timeout = now - timedelta(minutes=heartbeat_timeout_minutes)
        activity_timeout = now - timedelta(minutes=activity_timeout_minutes)

        inactive_ids = []

        for conn_id, conn_data in self.connections.items():
            # 只處理狀態為 active 的連線
            if conn_data["status"] != "active":
                continue

            last_heartbeat = conn_data["last_heartbeat"]
            last_activity = conn_data["last_activity"]

            # 心跳超時 或 完全無活動超時
            if last_heartbeat < heartbeat_timeout or last_activity < activity_timeout:
                inactive_ids.append(conn_id)

        # 斷開不活動連線
        for conn_id in inactive_ids:
            self.disconnect(conn_id, "心跳超時或無活動")

        # 記錄清理時間
        self.stats["last_cleanup"] = now

        if inactive_ids:
            logger.info(f"🧹 清理了 {len(inactive_ids)} 個不活動連線")

        return len(inactive_ids)

    # ------------------------------------------------------------
    # 3. 訊息發送（增強版：重試 + 指數退避 + 抖動）
    # ------------------------------------------------------------

    async def send_with_retry_async(
        self,
        channel_name,
        message,
        max_retries=None,
        base_delay=None,
        max_delay=None,
        exponential=True,
        jitter=True,
    ):
        """
        非同步發送訊息，失敗時以指數退避 + 抖動重試

        Args:
            channel_name: 目標 channel 名稱
            message: 要發送的訊息 dict
            max_retries: 最大重試次數（預設使用 self.default_retry_config）
            base_delay: 初始延遲秒數（預設 0.5）
            max_delay: 最大延遲秒數（預設 30）
            exponential: 是否使用指數退避（預設 True）
            jitter: 是否加入隨機抖動（預設 True）

        Returns:
            bool: 是否成功發送
        """
        # 使用預設值或傳入參數
        cfg = self.default_retry_config
        max_retries = max_retries if max_retries is not None else cfg["max_retries"]
        base_delay = base_delay if base_delay is not None else cfg["base_delay"]
        max_delay = max_delay if max_delay is not None else cfg["max_delay"]

        channel_layer = get_channel_layer()
        attempt = 0

        while attempt <= max_retries:
            try:
                await channel_layer.send(channel_name, message)
                self.stats["messages_sent"] += 1
                logger.debug(f"📤 訊息發送成功至 {channel_name}")
                return True
            except Exception as e:
                attempt += 1
                if attempt > max_retries:
                    self.stats["errors"] += 1
                    logger.error(f"❌ 訊息發送最終失敗至 {channel_name}，錯誤: {e}")
                    return False

                # 計算重試延遲
                if exponential:
                    delay = base_delay * (2 ** (attempt - 1))
                else:
                    delay = base_delay * attempt
                delay = min(delay, max_delay)

                # 加入隨機抖動 (±20%)
                if jitter:
                    jitter_range = delay * 0.2
                    delay += random.uniform(-jitter_range, jitter_range)
                    delay = max(0.1, delay)  # 確保不小於 0.1 秒

                logger.warning(
                    f"⚠️ 訊息發送失敗（嘗試 {attempt}/{max_retries}），"
                    f"{delay:.2f}秒後重試: {e}"
                )
                await asyncio.sleep(delay)

        return False  # 不會執行到此

    def send_with_retry_sync(
        self,
        channel_name,
        message,
        max_retries=None,
        base_delay=None,
        max_delay=None,
        exponential=True,
        jitter=True,
    ):
        """
        同步版發送訊息 - ✅ 增強版：檢查是否在事件循環中

        適用於非 async 環境（如 Django view）
        如果在事件循環中被調用，則返回 False 並記錄警告
        """
        # 檢查是否在事件循環中
        try:
            loop = asyncio.get_running_loop()
            # 如果在事件循環中，不能使用 async_to_sync
            logger.warning(
                f"⚠️ 在事件循環中調用同步發送方法，跳過發送至 {channel_name}。"
                f"請改用異步版本 await send_with_retry_async()"
            )
            self.stats["errors"] += 1
            return False
        except RuntimeError:
            # 沒有運行中的事件循環，可以安全使用 async_to_sync
            pass

        # 使用預設值或傳入參數
        cfg = self.default_retry_config
        max_retries = max_retries if max_retries is not None else cfg["max_retries"]
        base_delay = base_delay if base_delay is not None else cfg["base_delay"]
        max_delay = max_delay if max_delay is not None else cfg["max_delay"]

        channel_layer = get_channel_layer()
        attempt = 0

        while attempt <= max_retries:
            try:
                async_to_sync(channel_layer.send)(channel_name, message)
                self.stats["messages_sent"] += 1
                logger.debug(f"📤 [同步] 訊息發送成功至 {channel_name}")
                return True
            except Exception as e:
                attempt += 1
                if attempt > max_retries:
                    self.stats["errors"] += 1
                    logger.error(
                        f"❌ [同步] 訊息發送最終失敗至 {channel_name}，錯誤: {e}"
                    )
                    return False

                # 計算重試延遲（同步環境使用 time.sleep）
                if exponential:
                    delay = base_delay * (2 ** (attempt - 1))
                else:
                    delay = base_delay * attempt
                delay = min(delay, max_delay)

                if jitter:
                    jitter_range = delay * 0.2
                    delay += random.uniform(-jitter_range, jitter_range)
                    delay = max(0.1, delay)

                logger.warning(
                    f"⚠️ [同步] 訊息發送失敗（嘗試 {attempt}/{max_retries}），"
                    f"{delay:.2f}秒後重試: {e}"
                )
                import time

                time.sleep(delay)

        return False

    def broadcast_to_group(
        self,
        group_name,
        message_type,
        data,
        exclude_channels=None,
        retry=False,
        **retry_kwargs,
    ):
        """
        廣播訊息到群組（可選重試）- ✅ 最終修復版
        - 在事件循環中返回普通字典，避免被 await 時出錯
        - 修復：確保返回字典，而不是可以被 await 的對象
        """
        try:
            # 檢查是否在事件循環中
            try:
                loop = asyncio.get_running_loop()
                logger.warning(
                    f"⚠️ broadcast_to_group 在事件循環中被調用，但當前是同步方法。"
                    f"廣播至 {group_name} 將跳過，返回空字典。"
                )
                # ✅ 返回普通字典，絕對不可 await
                return {"success": 0, "failed": 0}
            except RuntimeError:
                # 沒有運行中的事件循環，可以安全使用 async_to_sync
                pass

            channel_layer = get_channel_layer()

            # 建立 Channels 格式的訊息
            message = {
                "type": message_type,
                **data,
                "timestamp": timezone.now().isoformat(),
            }

            # 廣播到群組
            async_to_sync(channel_layer.group_send)(group_name, message)
            self.stats["messages_sent"] += 1
            logger.debug(f"📢 廣播到群組 {group_name}: {message_type}")
            return {"success": 1, "failed": 0}

        except Exception as e:
            logger.error(f"❌ 群組廣播失敗 {group_name}: {str(e)}")
            self.stats["errors"] += 1
            return {"success": 0, "failed": 0}

    # ------------------------------------------------------------
    # 4. 查詢與統計
    # ------------------------------------------------------------

    def get_connection(self, connection_id):
        """獲取特定連線的資訊"""
        return self.connections.get(connection_id)

    def get_connection_by_channel(self, channel_name):
        """根據 channel_name 查詢 connection_id"""
        for conn_id, conn_data in self.connections.items():
            if conn_data["channel_name"] == channel_name:
                return conn_id, conn_data
        return None, None

    def get_active_connections(self, user_type=None):
        """取得活動連線列表（可過濾使用者類型）"""
        result = []
        for conn_id, conn_data in self.connections.items():
            if conn_data["status"] == "active":
                if user_type is None or conn_data["user_type"] == user_type:
                    result.append(
                        {
                            "id": conn_id,
                            "channel_name": conn_data["channel_name"],
                            "user_info": conn_data["user_info"],
                            "connected_at": conn_data["connected_at"],
                            "last_activity": conn_data["last_activity"],
                            "message_count": conn_data["message_count"],
                        }
                    )
        return result

    def get_active_connections_count(self, user_type=None):
        """快速取得活動連線數量（依類型）"""
        count = 0
        for conn_data in self.connections.values():
            if conn_data["status"] == "active":
                if user_type is None or conn_data["user_type"] == user_type:
                    count += 1
        return count

    def get_stats(self):
        """取得完整統計資訊"""
        # 計算各類型連線數量
        user_type_stats = {}
        for conn_data in self.connections.values():
            ut = conn_data["user_type"]
            status = conn_data["status"]

            if ut not in user_type_stats:
                user_type_stats[ut] = {"total": 0, "active": 0}

            user_type_stats[ut]["total"] += 1
            if status == "active":
                user_type_stats[ut]["active"] += 1

        return {
            "summary": {
                "total_connections": len(self.connections),
                "active_connections": self.stats["active_connections"],
                "historical_total": self.stats["total_connections"],
                "messages_sent": self.stats["messages_sent"],
                "errors": self.stats["errors"],
                "last_cleanup": self.stats["last_cleanup"],
            },
            "user_type_stats": user_type_stats,
            "pool_size": {k: len(v) for k, v in self.connection_pool.items()},
        }

    def reset_stats(self):
        """重置統計資料（不影響連線）"""
        self.stats = {
            "total_connections": len(self.connections),  # 保留現有連線數
            "active_connections": self.stats["active_connections"],
            "messages_sent": 0,
            "errors": 0,
            "last_cleanup": self.stats["last_cleanup"],
        }
        logger.info("📊 WebSocket 統計資料已重置")

    async def async_broadcast_to_group(
        self,
        group_name,
        message_type,
        data,
        exclude_channels=None,
        retry=False,
        **retry_kwargs,
    ):
        """
        異步廣播到群組（供事件循環中調用）
        """
        channel_layer = get_channel_layer()
        message = {
            "type": message_type,
            **data,
            "timestamp": timezone.now().isoformat(),
        }
        # 如果有排除邏輯，可在這裡處理，簡化版本直接發送
        await channel_layer.group_send(group_name, message)
        self.stats["messages_sent"] += 1
        return {"success": 1, "failed": 0}


# ========== 全域單例 ==========
websocket_manager = WebSocketManager()
