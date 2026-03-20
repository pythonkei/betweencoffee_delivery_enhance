#!/usr/bin/env python3
"""
測試 WebSocket 連線腳本
用於檢查訂單 1412 的 WebSocket 連線問題
"""

import asyncio
import websockets
import json
import sys

async def test_websocket_connection(order_id=1412):
    """測試 WebSocket 連線"""
    url = f"ws://localhost:8081/ws/order/{order_id}/"
    
    print(f"🔗 嘗試連線到: {url}")
    
    try:
        async with websockets.connect(url) as websocket:
            print("✅ WebSocket 連線成功")
            
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
                
            # 等待幾秒鐘看是否有其他消息
            print("⏳ 等待 3 秒鐘看是否有訂單狀態消息...")
            try:
                for i in range(3):
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=1)
                        print(f"📥 收到訂單消息: {message}")
                    except asyncio.TimeoutError:
                        print(f"⏰ 第 {i+1} 秒: 無消息")
            except Exception as e:
                print(f"❌ 接收消息時出錯: {e}")
                
    except websockets.exceptions.InvalidStatusCode as e:
        print(f"❌ HTTP 狀態碼錯誤: {e}")
        print(f"   狀態碼: {e.status_code}")
        print(f"   回應頭: {e.headers}")
    except websockets.exceptions.ConnectionClosedError as e:
        print(f"❌ 連線關閉錯誤: {e}")
        print(f"   關閉代碼: {e.code}")
        print(f"   原因: {e.reason}")
    except Exception as e:
        print(f"❌ 連線失敗: {type(e).__name__}: {e}")

async def test_order_exists(order_id=1412):
    """測試訂單是否存在"""
    import os
    import django
    import sys
    
    sys.path.append('/home/kei/Desktop/betweencoffee_delivery_enhance')
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'betweencoffee_delivery.settings')
    
    try:
        django.setup()
        from eshop.models import OrderModel
        
        try:
            order = OrderModel.objects.get(id=order_id)
            print(f"✅ 訂單 #{order.id} 存在")
            print(f"   狀態: {order.status}")
            print(f"   創建時間: {order.created_at}")
            print(f"   付款狀態: {order.payment_status}")
            print(f"   取餐碼: {order.pickup_code}")
            return True
        except OrderModel.DoesNotExist:
            print(f"❌ 訂單 #{order_id} 不存在")
            return False
    except Exception as e:
        print(f"❌ 檢查訂單時出錯: {e}")
        return False

async def main():
    """主函數"""
    print("=" * 60)
    print("🔧 WebSocket 連線測試工具")
    print("=" * 60)
    
    # 測試訂單是否存在
    print("\n📋 步驟 1: 檢查訂單是否存在")
    order_exists = await test_order_exists(1412)
    
    if not order_exists:
        print("❌ 訂單不存在，無法測試 WebSocket")
        return
    
    # 測試 WebSocket 連線
    print("\n🔗 步驟 2: 測試 WebSocket 連線")
    await test_websocket_connection(1412)
    
    print("\n" + "=" * 60)
    print("✅ 測試完成")

if __name__ == "__main__":
    asyncio.run(main())