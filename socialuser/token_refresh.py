"""
socialuser/token_refresh.py
OAuth Token 刷新機制

功能：
- Google OAuth Token 自動刷新（使用 refresh_token）
- Facebook Token 延長為長效 Token（60天）
- 統一的 Token 刷新介面
- 在登入時自動檢查並刷新即將過期的 Token

相容性：
- 支援本地開發（localhost:8081）與 Render 部署
- 使用 allauth 的 SocialToken 模型
"""

import logging
import time
from datetime import datetime, timedelta

from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


def refresh_google_token(social_token):
    """
    刷新 Google OAuth Token

    Google 的 refresh_token 是長期有效的，可以用來獲取新的 access_token。
    使用 Google OAuth2 API 直接刷新。

    Args:
        social_token: allauth 的 SocialToken 實例

    Returns:
        bool: 是否成功刷新
    """
    import requests

    try:
        provider = social_token.account.provider
        if provider != "google":
            logger.warning(
                f"refresh_google_token called for non-Google provider: {provider}"
            )
            return False

        # 從 SocialApp 獲取 client_id 和 client_secret
        app = social_token.app

        if not social_token.token:
            logger.warning("No access token to refresh")
            return False

        # Google 使用 refresh_token 來刷新 access_token
        refresh_data = {
            "client_id": app.client_id,
            "client_secret": app.secret,
            "refresh_token": social_token.token_secret,
            "grant_type": "refresh_token",
        }

        logger.info(
            f"Refreshing Google token for user {social_token.account.user.username}"
        )

        response = requests.post(
            "https://oauth2.googleapis.com/token",
            data=refresh_data,
            timeout=10,
        )

        if response.status_code == 200:
            data = response.json()
            new_token = data.get("access_token")
            expires_in = data.get("expires_in", 3600)  # 預設1小時

            if new_token:
                social_token.token = new_token
                social_token.expires_at = timezone.now() + timedelta(seconds=expires_in)
                social_token.save()
                logger.info(
                    f"Google token refreshed successfully, expires in {expires_in}s"
                )
                return True
            else:
                logger.warning("Google token refresh response missing access_token")
                return False
        else:
            logger.error(
                f"Google token refresh failed: {response.status_code} {response.text[:200]}"
            )
            return False

    except requests.exceptions.Timeout:
        logger.error("Google token refresh timed out")
        return False
    except requests.exceptions.ConnectionError:
        logger.error("Google token refresh connection error")
        return False
    except Exception as e:
        logger.error(f"Google token refresh error: {e}")
        return False


def refresh_facebook_token(social_token):
    """
    刷新/延長 Facebook Token

    Facebook 的短期 Token（2小時）可以通過 API 延長為長期 Token（60天）。
    注意：Facebook 不支援 refresh_token 模式，而是使用 Token 延長機制。

    Args:
        social_token: allauth 的 SocialToken 實例

    Returns:
        bool: 是否成功刷新
    """
    import requests

    try:
        provider = social_token.account.provider
        if provider != "facebook":
            logger.warning(
                f"refresh_facebook_token called for non-Facebook provider: {provider}"
            )
            return False

        app = social_token.app

        if not social_token.token:
            logger.warning("No Facebook token to refresh")
            return False

        logger.info(
            f"Refreshing Facebook token for user {social_token.account.user.username}"
        )

        # Facebook Token 延長 API
        response = requests.get(
            "https://graph.facebook.com/v18.0/oauth/access_token",
            params={
                "grant_type": "fb_exchange_token",
                "client_id": app.client_id,
                "client_secret": app.secret,
                "fb_exchange_token": social_token.token,
            },
            timeout=10,
        )

        if response.status_code == 200:
            data = response.json()
            new_token = data.get("access_token")
            expires_in = data.get("expires_in", 5184000)  # 預設60天

            if new_token:
                social_token.token = new_token
                social_token.expires_at = timezone.now() + timedelta(seconds=expires_in)
                social_token.save()
                logger.info(
                    f"Facebook token refreshed successfully, expires in {expires_in}s"
                )
                return True
            else:
                logger.warning("Facebook token refresh response missing access_token")
                return False
        else:
            logger.error(
                f"Facebook token refresh failed: {response.status_code} {response.text[:200]}"
            )
            return False

    except requests.exceptions.Timeout:
        logger.error("Facebook token refresh timed out")
        return False
    except requests.exceptions.ConnectionError:
        logger.error("Facebook token refresh connection error")
        return False
    except Exception as e:
        logger.error(f"Facebook token refresh error: {e}")
        return False


def refresh_social_token(social_token):
    """
    統一的 Token 刷新介面

    根據 provider 自動選擇對應的刷新方法。

    Args:
        social_token: allauth 的 SocialToken 實例

    Returns:
        bool: 是否成功刷新
    """
    if not social_token:
        logger.warning("refresh_social_token called with None")
        return False

    provider = social_token.account.provider

    if provider == "google":
        return refresh_google_token(social_token)
    elif provider == "facebook":
        return refresh_facebook_token(social_token)
    else:
        logger.warning(f"No refresh method for provider: {provider}")
        return False


def check_and_refresh_token(social_token, min_remaining_minutes=5):
    """
    檢查 Token 是否即將過期，如果是則自動刷新

    Args:
        social_token: allauth 的 SocialToken 實例
        min_remaining_minutes: 剩餘少於此分鐘數即觸發刷新

    Returns:
        bool: 是否成功刷新（或無需刷新）
    """
    if not social_token:
        return False

    # 如果沒有過期時間，無法判斷，假設有效
    if not social_token.expires_at:
        logger.info(
            f"Token for {social_token.account.provider} has no expiry, skipping refresh check"
        )
        return True

    now = timezone.now()
    remaining = social_token.expires_at - now
    remaining_minutes = remaining.total_seconds() / 60

    if remaining_minutes <= 0:
        logger.warning(
            f"Token for {social_token.account.provider} "
            f"expired {abs(remaining_minutes):.0f} minutes ago, refreshing..."
        )
        return refresh_social_token(social_token)

    if remaining_minutes <= min_remaining_minutes:
        logger.info(
            f"Token for {social_token.account.provider} "
            f"expires in {remaining_minutes:.0f} minutes, refreshing..."
        )
        return refresh_social_token(social_token)

    logger.debug(
        f"Token for {social_token.account.provider} "
        f"still valid for {remaining_minutes:.0f} minutes"
    )
    return True


def refresh_all_tokens_for_user(user):
    """
    刷新指定用戶的所有社交 Token

    在用戶登入時調用，確保所有社交 Token 都是有效的。

    Args:
        user: Django User 實例

    Returns:
        dict: 各 provider 的刷新結果
    """
    from allauth.socialaccount.models import SocialAccount, SocialToken

    results = {}

    try:
        social_accounts = SocialAccount.objects.filter(user=user)

        if not social_accounts.exists():
            logger.info(f"No social accounts for user {user.username}")
            return results

        for account in social_accounts:
            try:
                token = SocialToken.objects.get(account=account)
                success = check_and_refresh_token(token)
                results[account.provider] = {
                    "success": success,
                    "expires_at": (
                        token.expires_at.isoformat() if token.expires_at else None
                    ),
                }
            except SocialToken.DoesNotExist:
                logger.warning(
                    f"No token found for {account.provider} account of user {user.username}"
                )
                results[account.provider] = {"success": False, "error": "No token"}
            except Exception as e:
                logger.error(f"Error refreshing {account.provider} token: {e}")
                results[account.provider] = {"success": False, "error": str(e)}

    except Exception as e:
        logger.error(f"Error refreshing all tokens for user {user.username}: {e}")

    return results
