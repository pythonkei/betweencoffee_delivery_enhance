# socialuser/apps.py
from django.apps import AppConfig
from django.conf import settings
import os

class SocialuserConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'socialuser'

    def ready(self):
        """应用启动时自动更新站点配置"""
        # 只在运行服务器时执行，避免在迁移等操作时执行
        if not os.environ.get('RUN_MAIN'):
            return
            
        try:
            from django.contrib.sites.models import Site
            
            # 确定当前环境
            is_railway = os.environ.get('RAILWAY_ENVIRONMENT') is not None
            
            if is_railway:
                domain = os.environ.get('RAILWAY_PUBLIC_DOMAIN', 'web-production-6a798.up.railway.app')
                name = 'Between Coffee - Railway'
            else:
                domain = 'localhost:8081'
                name = 'Between Coffee - Local'
            
            # 更新站点信息
            site = Site.objects.get(id=settings.SITE_ID)
            if site.domain != domain or site.name != name:
                site.domain = domain
                site.name = name
                site.save()
                print(f"Site updated: {domain} - {name}")
                
        except Exception as e:
            # 忽略数据库未就绪等错误
            pass