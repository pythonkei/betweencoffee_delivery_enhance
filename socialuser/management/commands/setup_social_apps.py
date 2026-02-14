from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp
from django.conf import settings
import os

class Command(BaseCommand):
    help = 'Setup social applications for OAuth'

    def handle(self, *args, **options):
        # 首先更新站点信息
        try:
            current_site = Site.objects.get(id=settings.SITE_ID)
            
            # 根据环境设置站点域名
            is_railway = os.environ.get('RAILWAY_ENVIRONMENT') is not None
            if is_railway:
                domain = os.environ.get('RAILWAY_PUBLIC_DOMAIN', 'web-production-6a798.up.railway.app')
                name = 'Between Coffee - Railway'
            else:
                domain = 'localhost:8081'
                name = 'Between Coffee - Local'
            
            if current_site.domain != domain or current_site.name != name:
                current_site.domain = domain
                current_site.name = name
                current_site.save()
                self.stdout.write(
                    self.style.SUCCESS(f'Site updated to: {domain}')
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(f'Site already configured: {domain}')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error updating site: {e}')
            )
        
        # Google Social App - 使用 update_or_create 避免重复
        google_client_id = os.environ.get('OAUTH_GOOGLE_CLIENT_ID')
        google_secret = os.environ.get('OAUTH_GOOGLE_SECRET')
        
        if google_client_id and google_secret:
            # 清理可能存在的重复记录
            google_apps = SocialApp.objects.filter(provider='google')
            if google_apps.count() > 1:
                self.stdout.write(
                    self.style.WARNING(f'Found {google_apps.count()} Google apps, cleaning duplicates...')
                )
                # 保留第一个，删除其他
                for app in google_apps[1:]:
                    app.delete()
            
            google_app, created = SocialApp.objects.update_or_create(
                provider='google',
                defaults={
                    'name': 'Google OAuth',
                    'client_id': google_client_id,
                    'secret': google_secret,
                }
            )
            
            # 确保只关联到当前站点
            google_app.sites.clear()
            google_app.sites.add(current_site)
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS('Google SocialApp created successfully')
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS('Google SocialApp updated successfully')
                )
        else:
            self.stdout.write(
                self.style.WARNING('Google OAuth credentials not set')
            )
        
        # Facebook Social App - 使用 update_or_create 避免重复
        facebook_client_id = os.environ.get('OAUTH_FACEBOOK_CLIENT_ID')
        facebook_secret = os.environ.get('OAUTH_FACEBOOK_SECRET')
        
        if facebook_client_id and facebook_secret:
            # 清理可能存在的重复记录
            facebook_apps = SocialApp.objects.filter(provider='facebook')
            if facebook_apps.count() > 1:
                self.stdout.write(
                    self.style.WARNING(f'Found {facebook_apps.count()} Facebook apps, cleaning duplicates...')
                )
                # 保留第一个，删除其他
                for app in facebook_apps[1:]:
                    app.delete()
            
            facebook_app, created = SocialApp.objects.update_or_create(
                provider='facebook',
                defaults={
                    'name': 'Facebook OAuth',
                    'client_id': facebook_client_id,
                    'secret': facebook_secret,
                }
            )
            
            # 确保只关联到当前站点
            facebook_app.sites.clear()
            facebook_app.sites.add(current_site)
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS('Facebook SocialApp created successfully')
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS('Facebook SocialApp updated successfully')
                )
        else:
            self.stdout.write(
                self.style.WARNING('Facebook OAuth credentials not set')
            )
        
        self.stdout.write(
            self.style.SUCCESS('Social apps setup completed')
        )