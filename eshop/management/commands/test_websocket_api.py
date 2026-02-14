# eshop/management/commands/test_websocket_api.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.test import Client
from django.conf import settings
import json

class Command(BaseCommand):
    help = '測試 WebSocket 監控 API'
    
    def handle(self, *args, **options):
        self.stdout.write('=========================================')
        self.stdout.write('  WebSocket API 測試')
        self.stdout.write('=========================================\n')
        
        # ✅ 建立測試客戶端，並設置允許的主機
        client = Client(HTTP_HOST='localhost:8081')  # 使用實際的主機名
        
        # 登入管理員
        User = get_user_model()
        try:
            user = User.objects.get(username='kei')
            client.force_login(user)
            self.stdout.write(self.style.SUCCESS('✅ 登入成功'))
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR('❌ 用戶 kei 不存在'))
            return
        
        # 測試 WebSocket 統計 API
        self.stdout.write('\n▶ 測試 WebSocket 統計 API...')
        try:
            response = client.get('/eshop/api/websocket/stats/')
            if response.status_code == 200:
                self.stdout.write(self.style.SUCCESS('✅ 成功'))
                data = response.json()
                self.stdout.write(json.dumps(data, indent=2, ensure_ascii=False))
            else:
                self.stdout.write(self.style.ERROR(f'❌ 失敗: HTTP {response.status_code}'))
                self.stdout.write(f'   回應: {response.content.decode()[:200]}')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ 例外錯誤: {e}'))
        
        # 測試 WebSocket 連線列表
        self.stdout.write('\n▶ 測試 WebSocket 連線列表...')
        try:
            response = client.get('/eshop/api/websocket/connections/?status=active')
            if response.status_code == 200:
                self.stdout.write(self.style.SUCCESS('✅ 成功'))
                data = response.json()
                self.stdout.write(json.dumps(data, indent=2, ensure_ascii=False))
            else:
                self.stdout.write(self.style.ERROR(f'❌ 失敗: HTTP {response.status_code}'))
                self.stdout.write(f'   回應: {response.content.decode()[:200]}')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ 例外錯誤: {e}'))
        
        # 測試系統廣播
        self.stdout.write('\n▶ 測試系統廣播...')
        try:
            response = client.get('/eshop/api/websocket/broadcast-test/?message=測試訊息&type=info')
            if response.status_code == 200:
                self.stdout.write(self.style.SUCCESS('✅ 成功'))
                data = response.json()
                self.stdout.write(json.dumps(data, indent=2, ensure_ascii=False))
            else:
                self.stdout.write(self.style.ERROR(f'❌ 失敗: HTTP {response.status_code}'))
                self.stdout.write(f'   回應: {response.content.decode()[:200]}')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ 例外錯誤: {e}'))
        
        self.stdout.write('\n=========================================')
        self.stdout.write(self.style.SUCCESS('✅ 測試完成'))
        self.stdout.write('=========================================')