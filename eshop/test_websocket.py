# test_websocket.py
import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://localhost:8080/ws/order/428/"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket连接成功")
            
            # 等待消息
            print("等待通知...")
            message = await asyncio.wait_for(websocket.recv(), timeout=10.0)
            data = json.loads(message)
            print(f"📨 收到通知: {data}")
            
    except Exception as e:
        print(f"❌ 连接失败: {e}")

if __name__ == "__main__":
    asyncio.run(test_websocket())