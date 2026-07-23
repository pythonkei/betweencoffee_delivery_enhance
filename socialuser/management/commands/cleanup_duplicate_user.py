"""
管理命令：清理重複的用戶記錄 & 修復缺少 Profile 的用戶
"""

import logging

from allauth.account.models import EmailAddress
from allauth.socialaccount.models import SocialAccount, SocialToken
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from socialuser.models import Profile

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "清理重複的用戶記錄並修復缺少 Profile 的用戶"

    def handle(self, *args, **options):
        # ===== 第一部分：清理舊的重複用戶 (id=58) =====
        self._cleanup_old_user()

        # ===== 第二部分：檢查並修復缺少 Profile 的用戶 =====
        self._fix_missing_profiles()

    def _cleanup_old_user(self):
        """清理舊的重複用戶 fb_kei (id=58)"""
        user_id = 58
        username = "fb_kei"
        email = "manandapan@hotmail.com"

        try:
            user = User.objects.get(id=user_id)
            self.stdout.write(
                f"找到舊用戶: id={user.id}, username={user.username}, email={user.email}"
            )

            # 1. 刪除社交帳號 token
            social_accounts = SocialAccount.objects.filter(user=user)
            for acc in social_accounts:
                SocialToken.objects.filter(account=acc).delete()
                self.stdout.write(f"  刪除 SocialToken for account {acc.id}")

            # 2. 刪除社交帳號
            deleted_accounts = social_accounts.delete()
            self.stdout.write(f"  刪除 SocialAccount: {deleted_accounts}")

            # 3. 刪除 email 地址
            deleted_emails = EmailAddress.objects.filter(user=user).delete()
            self.stdout.write(f"  刪除 EmailAddress: {deleted_emails}")

            # 4. 刪除用戶
            deleted_user = user.delete()
            self.stdout.write(f"  刪除 User: {deleted_user}")

            self.stdout.write(
                self.style.SUCCESS(f"成功刪除舊用戶 {username} ({email})")
            )

        except User.DoesNotExist:
            self.stdout.write(f"舊用戶 {username} (id={user_id}) 不存在，可能已被刪除")

    def _fix_missing_profiles(self):
        """檢查所有用戶，為缺少 Profile 的用戶建立 Profile"""
        self.stdout.write("檢查缺少 Profile 的用戶...")

        users_without_profile = []
        for user in User.objects.all():
            if not hasattr(user, "profile"):
                try:
                    Profile.objects.create(user=user)
                    users_without_profile.append(f"{user.username} (id={user.id})")
                    self.stdout.write(
                        f"  已為 {user.username} (id={user.id}) 建立 Profile"
                    )
                except Exception as e:
                    self.stderr.write(
                        f"  為 {user.username} (id={user.id}) 建立 Profile 失敗: {e}"
                    )

        if users_without_profile:
            self.stdout.write(
                self.style.SUCCESS(
                    f"已修復 {len(users_without_profile)} 個缺少 Profile 的用戶"
                )
            )
        else:
            self.stdout.write("所有用戶都有 Profile，無需修復")
