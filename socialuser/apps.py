# socialuser/apps.py
from django.apps import AppConfig
from django.conf import settings
import os
import logging

logger = logging.getLogger(__name__)

class SocialuserConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'socialuser'

    def ready(self):
        """应用启动时自动更新站点配置和连接信号"""
        # 只在运行服务器时执行，避免在迁移等操作时执行
        if not os.environ.get('RUN_MAIN'):
            return
            
        try:
            # 更新站点信息
            self.update_site_config()
            
            # 连接信号
            self.connect_signals()
            
        except Exception as e:
            # 忽略数据库未就绪等错误
            logger.debug(f"SocialuserConfig.ready() 初始化错误: {str(e)}")
    
    def update_site_config(self):
        """更新站点配置"""
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
                logger.info(f"Site updated: {domain} - {name}")
                
        except Exception as e:
            logger.debug(f"更新站点配置失败: {str(e)}")
    
    def connect_signals(self):
        """连接会员系统信号"""
        try:
            # 导入信号模块
            from . import signals_enhanced
            
            # 连接信号
            signals_enhanced.connect_signals()
            logger.info("✅ 会员系统信号已成功连接")
            
        except Exception as e:
            logger.error(f"❌ 连接会员系统信号失败: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
