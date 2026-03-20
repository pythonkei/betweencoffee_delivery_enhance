#!/usr/bin/env python3
"""
測試 WebSocket 修復腳本
測試禁用 AllowedHostsOriginValidator 後的 WebSocket 連線
"""

import asyncio
import websockets
import json
import os
import sys

# 設置 Django 環境
sys.path.append('/home/kei/Desktop/betweencoffee_delivery_enhance')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'betweencoffee_delivery.settings')

import django
django.setup()

from asgiref.sync import sync_to_async
from eshop.models import OrderModel


async def test_order_exists(order_id=1412):
    """測試訂單是否存在"""
    @sync_to_async
    def check_order():
        try:
            order = OrderModel.objects.get(id=order_id)
            return order
        except OrderModel.DoesNotExist:
            return None
    
    try:
        order = await check_order()
        if order:
            print(f"✅ 訂單 #{order.id} 存在")
            print(f"   狀態: {order.status}")
            print(f"   付款狀態: {order.payment_status}")
            return True
        else:
            print(f"❌ 訂單 #{order_id} 不存在")
            return False
    except Exception as e:
        print(f"❌ 檢查訂單時出錯: {e}")
        return False


async def test_websocket_connection(order_id=1412):
    """測試 WebSocket 連線（修復後）"""
    url = f"ws://localhost:8081/ws/order/{order_id}/"
    
    print(f"\n🔗 嘗試連線到: {url}")
    print("⚠️ 測試禁用 AllowedHostsOriginValidator 後的連線")
    
    try:
        async with websockets.connect(url) as websocket:
            print("✅ WebSocket 連線成功！")
            
            # 發送 ping 消息
            ping_message = json.dumps({"type": "ping"})
            await websocket.send(ping_message)
            print(f"📤 發送: {ping_message}")
            
            # 等待回應
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5)
                print(f"📥 收到: {response}")
                
                # 解析回應
                data = json.loads(response)
                if data.get('type') == 'pong':
                    print("✅ 收到 pong 回應，連線正常")
                else:
                    print(f"⚠️ 收到非預期回應: {data}")
                    
            except asyncio.TimeoutError:
                print("❌ 等待回應超時")
                
            # 等待訂單狀態消息
            print("⏳ 等待訂單狀態消息...")
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=3)
                print(f"📥 收到訂單狀態消息: {message}")
                
                # 解析訂單狀態
                data = json.loads(message)
                if data.get('type') == 'order_status':
                    print("✅ 成功收到訂單狀態更新")
                    print(f"   訂單狀態: {data.get('data', {}).get('status')}")
                    print(f"   顯示狀態: {data.get('data', {}).get('status_display')}")
                else:
                    print(f"⚠️ 收到非訂單狀態消息: {data.get('type')}")
                    
            except asyncio.TimeoutError:
                print("⏰ 未收到訂單狀態消息（可能正常）")
                
    except websockets.exceptions.InvalidStatusCode as e:
        print(f"❌ HTTP 狀態碼錯誤: {e}")
        print(f"   狀態碼: {e.status_code}")
        
        if e.status_code == 403:
            print("\n🔴 問題未解決：仍然收到 403 Forbidden")
            print("   可能需要其他修復方法")
        elif e.status_code == 404:
            print("\n⚠️ 收到 404 Not Found")
            print("   可能是 WebSocket 路由配置問題")
            
    except websockets.exceptions.ConnectionClosedError as e:
        print(f"❌ 連線關閉錯誤: {e}")
        print(f"   關閉代碼: {e.code}")
        print(f"   原因: {e.reason}")
    except Exception as e:
        print(f"❌ 連線失敗: {type(e).__name__}: {e}")


async def test_browser_simulation():
    """模擬瀏覽器行為的測試"""
    print("\n🌐 模擬瀏覽器 WebSocket 連線")
    
    # 模擬瀏覽器可能發送的頭部
    import websockets
    from websockets import Headers
    
    url = "ws://localhost:8081/ws/order/1412/"
    
    # 創建模擬瀏覽器的頭部
    headers = Headers()
    headers['Origin'] = 'http://localhost:8081'
    headers['User-Agent'] = 'Mozilla/5.0 (測試客戶端)'
    
    try:
        async with websockets.connect(url, extra_headers=headers) as websocket:
            print("✅ 模擬瀏覽器連線成功")
            
            # 發送 ping
            await websocket.send(json.dumps({"type": "ping"}))
            
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=3)
                print(f"📥 收到回應: {response[:100]}...")
            except asyncio.TimeoutError:
                print("⏰ 等待回應超時")
                
    except Exception as e:
        print(f"❌ 模擬瀏覽器連線失敗: {type(e).__name__}: {e}")


async def main():
    """主函數"""
    print("=" * 60)
    print("🔧 WebSocket 修復測試工具")
    print("=" * 60)
    
    # 測試訂單是否存在
    print("\n📋 步驟 1: 檢查訂單是否存在")
    order_exists = await test_order_exists(1412)
    
    if not order_exists:
        print("❌ 訂單不存在，無法測試 WebSocket")
        return
    
    # 測試 WebSocket 連線
    print("\n🔗 步驟 2: 測試 WebSocket 連線（修復後）")
    await test_websocket_connection(1412)
    
    # 測試模擬瀏覽器
    print("\n🌐 步驟 3: 模擬瀏覽器行為")
    await test_browser_simulation()
    
    print("\n" + "=" * 60)
    print("📋 測試總結:")
    print("   1. 如果連線成功 → 修復有效")
    print("   2. 如果仍然 403 → 需要其他修復")
    print("   3. 如果連線成功但無消息 → 檢查消費者邏輯")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())