"""
測試視圖 - 提供智能分配系統測試頁面
"""

import os
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.conf import settings

@csrf_exempt
def test_smart_allocation_view(request):
    """
    提供智能分配系統測試頁面
    這個視圖直接讀取並返回HTML文件內容
    """
    try:
        # 讀取測試頁面HTML文件
        file_path = os.path.join(settings.BASE_DIR, 'test_smart_allocation.html')
        
        with open(file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        return HttpResponse(html_content, content_type='text/html')
        
    except FileNotFoundError:
        return HttpResponse(
            """
            <!DOCTYPE html>
            <html>
            <head>
                <title>測試頁面未找到</title>
                <style>
                    body { font-family: Arial, sans-serif; padding: 40px; text-align: center; }
                    .error { color: #dc3545; font-size: 24px; margin-bottom: 20px; }
                    .info { color: #6c757d; margin-bottom: 20px; }
                </style>
            </head>
            <body>
                <div class="error">❌ 測試頁面未找到</div>
                <div class="info">文件 test_smart_allocation.html 不存在</div>
                <div>
                    <a href="/">返回首頁</a> | 
                    <a href="/admin/eshop/ordermodel/staff-management/">員工管理</a>
                </div>
            </body>
            </html>
            """,
            status=404
        )


@csrf_exempt
def test_websocket_monitoring_view(request):
    """
    提供WebSocket監控系統測試頁面
    這個視圖直接讀取並返回HTML文件內容
    """
    try:
        # 讀取測試頁面HTML文件
        file_path = os.path.join(settings.BASE_DIR, 'templates', 'test_websocket_monitoring.html')
        
        with open(file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        return HttpResponse(html_content, content_type='text/html')
        
    except FileNotFoundError:
        return HttpResponse(
            """
            <!DOCTYPE html>
            <html>
            <head>
                <title>WebSocket監控測試頁面未找到</title>
                <style>
                    body { font-family: Arial, sans-serif; padding: 40px; text-align: center; }
                    .error { color: #dc3545; font-size: 24px; margin-bottom: 20px; }
                    .info { color: #6c757d; margin-bottom: 20px; }
                    .links { margin-top: 30px; }
                    .links a { margin: 0 10px; padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; }
                    .links a:hover { background: #0056b3; }
                </style>
            </head>
            <body>
                <div class="error">❌ WebSocket監控測試頁面未找到</div>
                <div class="info">文件 templates/test_websocket_monitoring.html 不存在</div>
                <div class="info">請確保測試頁面已創建並放置在正確位置</div>
                <div class="links">
                    <a href="/">返回首頁</a>
                    <a href="/test/smart-allocation/">智能分配測試</a>
                    <a href="/admin/">管理後台</a>
                </div>
            </body>
            </html>
            """,
            status=404
        )
    except Exception as e:
        return HttpResponse(
            f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>服務器錯誤</title>
                <style>
                    body {{ font-family: Arial, sans-serif; padding: 40px; text-align: center; }}
                    .error {{ color: #dc3545; font-size: 24px; margin-bottom: 20px; }}
                    .info {{ color: #6c757d; margin-bottom: 20px; }}
                </style>
            </head>
            <body>
                <div class="error">❌ 服務器錯誤</div>
                <div class="info">錯誤: {str(e)}</div>
                <div>
                    <a href="/">返回首頁</a> | 
                    <a href="/admin/eshop/ordermodel/staff-management/">員工管理</a>
                </div>
            </body>
            </html>
            """,
            status=500
        )

@login_required
def test_smart_allocation_auth_view(request):
    """
    需要登入的測試頁面視圖
    """
    return test_smart_allocation_view(request)