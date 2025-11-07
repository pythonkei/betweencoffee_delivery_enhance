#!/usr/bin/env python
import os
import sys

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def check_wsgi_config():
    try:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'betweencoffee_delivery.settings')
        
        # 尝试导入 WSGI 应用
        from django.core.wsgi import get_wsgi_application
        application = get_wsgi_application()
        
        print("✓ WSGI 配置验证成功")
        print(f"✓ DJANGO_SETTINGS_MODULE: {os.environ.get('DJANGO_SETTINGS_MODULE')}")
        
        # 检查关键设置
        from django.conf import settings
        print(f"✓ WSGI_APPLICATION: {getattr(settings, 'WSGI_APPLICATION', 'Not found')}")
        print(f"✓ ROOT_URLCONF: {getattr(settings, 'ROOT_URLCONF', 'Not found')}")
        
        return True
    except Exception as e:
        print(f"✗ WSGI 配置验证失败: {e}")
        return False

if __name__ == "__main__":
    check_wsgi_config()