#!/usr/bin/env python3
"""
簡單的 WebSocket 測試腳本
測試不帶身份驗證的 WebSocket 連線
"""

import asyncio
import websockets
import json

async def test_websocket_without_auth():
    """測試不帶身份驗證的 WebSocket 連線"""
    url = "ws://localhost:8081/ws/order/1412/"
    
    print(f"🔗 嘗試連線到: {url}")
    print("⚠️ 注意：這是不帶身份驗證的測試")
    
    try:
        # 嘗試不帶任何額外頭部的連線
        async with websockets.connect(url) as websocket:
            print("✅ WebSocket 連線成功（不帶身份驗證）")
            
            # 發送簡單的 ping
            await websocket.send(json.dumps({"type": "ping"}))
            print("📤 發送 ping")
            
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=3)
                print(f"📥 收到: {response}")
            except asyncio.TimeoutError:
                print("⏰ 等待回應超時")
                
    except websockets.exceptions.InvalidStatusCode as e:
        print(f"❌ HTTP 狀態碼錯誤: {e}")
        print(f"   狀態碼: {e.status_code}")
        
        # 檢查是否是 403 錯誤
        if e.status_code == 403:
            print("\n🔍 403 Forbidden 錯誤分析:")
            print("   1. 可能是 CSRF 保護")
            print("   2. 可能是 Origin 驗證失敗")
            print("   3. 可能是身份驗證中間件拒絕")
            
    except Exception as e:
        print(f"❌ 連線失敗: {type(e).__name__}: {e}")

async def test_queue_websocket():
    """測試隊列 WebSocket（可能權限不同）"""
    url = "ws://localhost:8081/ws/queue/"
    
    print(f"\n🔗 嘗試連線到隊列: {url}")
    
    try:
        async with websockets.connect(url) as websocket:
            print("✅ 隊列 WebSocket 連線成功")
            
            # 發送 ping
            await websocket.send(json.dumps({"type": "ping"}))
            print("📤 發送 ping")
            
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=3)
                print(f"📥 收到: {response}")
            except asyncio.TimeoutError:
                print("⏰ 等待回應超時")
                
    except websockets.exceptions.InvalidStatusCode as e:
        print(f"❌ HTTP 狀態碼錯誤: {e}")
        print(f"   狀態碼: {e.status_code}")
    except Exception as e:
        print(f"❌ 連線失敗: {type(e).__name__}: {e}")

async def main():
    """主函數"""
    print("=" * 60)
    print("🔧 WebSocket 權限測試工具")
    print("=" * 60)
    
    # 測試訂單 WebSocket
    await test_websocket_without_auth()
    
    # 測試隊列 WebSocket
    await test_queue_websocket()
    
    print("\n" + "=" * 60)
    print("✅ 測試完成")

if __name__ == "__main__":
    asyncio.run(main())