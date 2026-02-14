# 检查并修复所有缺失的函数
# 运行command:
# python check_missing_views.py

# check_missing_views.py
import sys
import os

# 添加项目路径
sys.path.append('/home/kei/Desktop/betweencoffee_delivery_enhance')

# 设置 Django 环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'betweencoffee.settings')
import django
django.setup()

from django.urls import URLResolver, URLPattern
from django.conf import settings
import importlib
import inspect

def check_urls():
    """检查 urls.py 中的所有视图函数是否存在"""
    
    # 导入 urls 模块
    from eshop import urls
    
    missing_views = []
    
    def check_pattern(pattern, namespace=''):
        if isinstance(pattern, URLPattern):
            try:
                # 获取视图函数
                view = pattern.callback
                if hasattr(view, 'view_class'):
                    # 基于类的视图
                    view_name = view.view_class.__name__
                    print(f"✓ 基于类的视图: {view_name}")
                else:
                    # 基于函数的视图
                    view_name = view.__name__
                    # 检查视图是否在 views 模块中
                    module_name = view.__module__
                    if module_name == 'eshop.views':
                        print(f"✓ 视图函数: {view_name}")
                    else:
                        print(f"⚠ 视图来自其他模块: {view_name} ({module_name})")
            except Exception as e:
                missing_views.append((pattern.pattern.regex.pattern, str(e)))
        elif isinstance(pattern, URLResolver):
            # 递归检查嵌套的 URL 模式
            for p in pattern.url_patterns:
                check_pattern(p, pattern.namespace or namespace)
    
    # 检查所有 URL 模式
    for pattern in urls.urlpatterns:
        check_pattern(pattern)
    
    if missing_views:
        print("\n✗ 缺失的视图:")
        for url, error in missing_views:
            print(f"  - {url}: {error}")
    else:
        print("\n✅ 所有视图都存在")

if __name__ == '__main__':
    check_urls()