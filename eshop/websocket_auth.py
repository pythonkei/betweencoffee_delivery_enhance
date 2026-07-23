"""
eshop/websocket_auth.py - WebSocket 認證 Middleware（修復 Render PostgreSQL 連線問題）

問題：
在 Render 生產環境中，PostgreSQL 的 CONN_MAX_AGE=0（免費方案限制），
導致 AuthMiddleware 在 resolve_scope 中調用 get_user() 查詢資料庫時，
出現 "django.db.utils.InterfaceError: connection already closed"。

解決方案：
自定義 AuthMiddleware，在 get_user() 調用前先確保資料庫連線，
並在捕獲 InterfaceError 時自動重試。
"""

import logging

from channels.auth import AuthMiddleware, AuthMiddlewareStack
from channels.db import database_sync_to_async

logger = logging.getLogger(__name__)


@database_sync_to_async
def _ensure_db_connection():
    """
    確保資料庫連線可用。
    在 Render 生產環境中，PostgreSQL 連線在空閒後會被資料庫端關閉。
    此方法強制初始化資料庫連線池。
    """
    from django.db import connection

    try:
        connection.ensure_connection()
        return True
    except Exception as e:
        logger.warning(f"⚠️ 資料庫連線初始化失敗（將重試）: {e}")
        return False


class RobustAuthMiddleware(AuthMiddleware):
    """
    增強版 AuthMiddleware - 在 resolve_scope 前先確保資料庫連線

    解決 Render 生產環境中 WebSocket 連線時出現
    "django.db.utils.InterfaceError: connection already closed" 的問題。
    """

    async def resolve_scope(self, scope):
        """在解析使用者前先確保資料庫連線"""
        # 🔧 修復：先確保資料庫連線
        await _ensure_db_connection()

        # 調用原始的 resolve_scope
        try:
            await super().resolve_scope(scope)
        except Exception as e:
            error_msg = str(e)
            if (
                "connection already closed" in error_msg
                or "InterfaceError" in error_msg
            ):
                logger.warning(f"⚠️ resolve_scope 遇到連線問題，重試一次: {e}")
                # 重試：再次確保連線後重試
                await _ensure_db_connection()
                await super().resolve_scope(scope)
            else:
                raise


def RobustAuthMiddlewareStack(inner):
    """
    增強版 AuthMiddlewareStack - 使用 RobustAuthMiddleware 替代 AuthMiddleware

    用法：在 asgi.py 中替換 AuthMiddlewareStack 為 RobustAuthMiddlewareStack
    """
    from channels.sessions import CookieMiddleware, SessionMiddleware

    return CookieMiddleware(SessionMiddleware(RobustAuthMiddleware(inner)))
