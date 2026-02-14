from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.models import EmailAddress
from django.urls import reverse
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class NoNewUsersAccountAdapter(DefaultAccountAdapter):
    def is_open_for_signup(self, request):
        """
        只允许社交账户注册，禁止常规注册
        """
        # 检查是否是社交登录请求
        if request.path.startswith('/accounts/social/'):
            return True
        if 'sociallogin' in request.session:
            return True
        return False

    def save_user(self, request, user, form, commit=True):
        """
        防止常规表单注册保存用户
        """
        # 如果是社交登录，允许保存
        if request.path.startswith('/accounts/social/'):
            return super().save_user(request, user, form, commit)
        raise PermissionError("Regular account creation is disabled")

class SocialAccountAdapter(DefaultSocialAccountAdapter):
    def is_open_for_signup(self, request, sociallogin):
        """
        允许通过社交账户注册新用户
        """
        logger.info(f"Checking if open for signup for social login: {sociallogin.account.provider}")
        return True

    def pre_social_login(self, request, sociallogin):
        """
        处理社交登录，连接现有账户或创建新用户
        """
        try:
            email = sociallogin.account.extra_data.get("email")
            if not email:
                logger.warning("No email provided in social login")
                return

            # 记录社交登录尝试
            provider = sociallogin.account.provider
            logger.info(f"Social login attempt from {provider} with email: {email}")

            # 检查邮箱是否已存在
            try:
                existing_emails = EmailAddress.objects.filter(email=email, verified=True)
                if existing_emails.exists():
                    # 连接到现有用户
                    existing_email = existing_emails.first()
                    if existing_email.user != sociallogin.user:
                        sociallogin.connect(request, existing_email.user)
                        logger.info(f"Connected social account to existing user: {email}")
            except Exception as e:
                logger.error(f"Error checking existing emails: {e}")
                
        except Exception as e:
            logger.error(f"Error in pre_social_login: {e}")

    def save_user(self, request, sociallogin, form=None):
        """
        自动验证社交提供者的邮箱并确保创建用户档案
        """
        try:
            # 调用父类方法保存用户
            user = super().save_user(request, sociallogin, form)
            
            # 确保邮箱地址
            email = user.email
            if not email:
                email = sociallogin.account.extra_data.get('email')
                if email:
                    user.email = email
                    user.save()
            
            # 创建或更新邮箱地址记录
            if email:
                # 使用 update_or_create 处理可能的重复
                email_address, created = EmailAddress.objects.update_or_create(
                    user=user,
                    email=email,
                    defaults={'verified': True, 'primary': True}
                )
                logger.info(f"Email {'created' if created else 'updated'} for user: {user.username}")
            
            # 确保用户档案已创建
            if not hasattr(user, 'profile'):
                try:
                    from .models import UserProfile
                    UserProfile.objects.create(user=user)
                    logger.info(f"Created profile for user: {user.username}")
                except Exception as e:
                    logger.error(f"Error creating profile: {e}")
                    
        except Exception as e:
            logger.error(f"Error in save_user: {e}")
            raise
            
        return user

    def authentication_error(self, request, provider_id, error=None, exception=None, extra_context=None):
        """
        处理认证错误
        """
        logger.error(f"Social authentication error for {provider_id}: {error}")
        if exception:
            logger.error(f"Exception: {exception}")
        return super().authentication_error(request, provider_id, error, exception, extra_context)

    def get_app(self, request, provider, client_id=None, **kwargs):
        """
        处理多个 SocialApp 的情况，优先选择匹配 client_id 的 app
        """
        try:
            from allauth.socialaccount.models import SocialApp
            
            apps = SocialApp.objects.filter(provider=provider)
            
            # 如果没有配置任何 app
            if not apps.exists():
                logger.error(f"No SocialApp configured for provider: {provider}")
                raise Exception(f"No SocialApp configured for {provider}")
            
            # 如果只有一个 app，直接返回
            if apps.count() == 1:
                return apps.first()
            
            # 如果有多个 app，尝试匹配 client_id
            if client_id:
                matching_apps = apps.filter(client_id=client_id)
                if matching_apps.exists():
                    if matching_apps.count() > 1:
                        logger.warning(f"Multiple SocialApp found for {provider} with client_id {client_id}, using first")
                    return matching_apps.first()
            
            # 如果没有匹配的 client_id，使用第一个并记录警告
            logger.warning(f"Multiple SocialApp found for {provider}, using first one. Consider cleaning up duplicates.")
            return apps.first()
            
        except Exception as e:
            logger.error(f"Error getting app for provider {provider}: {e}")
            # 最后尝试：获取第一个可用的 app
            from allauth.socialaccount.models import SocialApp
            fallback_app = SocialApp.objects.filter(provider=provider).first()
            if fallback_app:
                logger.warning(f"Using fallback app for {provider}: {fallback_app.name}")
                return fallback_app
            raise

