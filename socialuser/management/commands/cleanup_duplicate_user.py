"""
管理命令：清理重複的用戶記錄
用於刪除 fb_kei / manandapan@hotmail.com 的舊帳號
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from allauth.socialaccount.models import SocialAccount, SocialToken
from allauth.account.models import EmailAddress
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = '清理重複的用戶記錄'

    def handle(self, *args, **options):
        user_id = 58
        username = 'fb_kei'
        email = 'manandapan@hotmail.com'

        try:
            user = User.objects.get(id=user_id)
            self.stdout.write(f"找到用戶: id={user.id}, username={user.username}, email={user.email}")

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

            self.stdout.write(self.style.SUCCESS(f"成功刪除用戶 {username} ({email})"))

        except User.DoesNotExist:
            self.stdout.write(f"用戶 {username} (id={user_id}) 不存在，可能已被刪除")
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"錯誤: {e}"))
