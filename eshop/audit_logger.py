# eshop/audit_logger.py
"""
審計日誌記錄器 - 記錄員工操作日誌

提供 log_audit() 工具函數，供 status_changer.py 和其他
業務邏輯模組在操作成功後調用。

使用 try/except 保護，不影響主要業務流程。
"""

import logging

from django.http import HttpRequest

logger = logging.getLogger(__name__)


def _get_ip(request):
    """從 request 提取 IP 地址"""
    if request is None:
        return None
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", None)


def _get_staff_name(request):
    """從 request 提取員工名稱"""
    if request is None:
        return ""
    # 嘗試從 session 或 user 中獲取員工名稱
    staff_name = getattr(request, "session", {}).get("staff_name", "")
    if not staff_name and hasattr(request, "user") and request.user.is_authenticated:
        staff_name = request.user.get_full_name() or request.user.username
    return staff_name or ""


def log_audit(action, order=None, staff_name=None, request=None, **extra):
    """
    記錄審計日誌

    參數:
        action (str): 動作類型（如 'order_ready', 'order_preparing' 等）
        order (OrderModel, optional): 相關訂單
        staff_name (str, optional): 員工名稱（優先級高於 request）
        request (HttpRequest, optional): HTTP 請求（用於提取 IP 和員工名稱）
        **extra: 額外資訊（如 old_status, new_status 等）

    返回:
        AuditLog or None: 成功返回 AuditLog 實例，失敗返回 None
    """
    try:
        from .models.audit_log import AuditLog
        from .models.order import OrderModel

        # 驗證 order 是有效的 OrderModel 實例
        if order is not None and not isinstance(order, OrderModel):
            logger.warning(
                f"⚠️ 審計日誌跳過: order 不是 OrderModel 實例 (type={type(order).__name__})"
            )
            order = None

        # 如果未提供 staff_name，嘗試從 request 提取
        if not staff_name and request:
            staff_name = _get_staff_name(request)

        # 如果未提供 staff_name，使用預設
        if not staff_name:
            staff_name = ""

        ip_address = _get_ip(request) if request else None

        audit = AuditLog.objects.create(
            action=action,
            order=order,
            staff_name=staff_name,
            ip_address=ip_address,
            detail=extra,
        )
        logger.debug(f"📝 審計日誌已記錄: {audit}")
        return audit

    except Exception as e:
        logger.error(f"❌ 審計日誌記錄失敗 (action={action}): {str(e)}", exc_info=True)
        return None
