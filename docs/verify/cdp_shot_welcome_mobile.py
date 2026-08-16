#!/usr/bin/env python3
"""CDP 截圖：首頁 bc-welcome-panel 手機端（375px）確認騎在橫幅底部"""
import asyncio
import base64
import json
import urllib.request

import websockets

WS = "http://localhost:9222/json/new?about:blank"


async def main():
    for w, h, name in [(768, 1024, "tablet"), (375, 812, "mobile")]:
        await shot(w, h, name)


async def shot(width, height, name):
    req = urllib.request.Request(WS, method="PUT")
    tab = json.loads(urllib.request.urlopen(req).read())
    ws_url = tab["webSocketDebuggerUrl"]

    async with websockets.connect(ws_url) as ws:
        mid = 1

        def msg(m, p=None):
            nonlocal mid
            m = {"id": mid, "method": m, "params": p or {}}
            mid += 1
            return m

        async def send(m):
            await ws.send(json.dumps(m))
            while True:
                r = json.loads(await ws.recv())
                if r.get("id") == m["id"]:
                    return r.get("result", {})

        await send(msg("Page.enable"))
        await send(msg("Runtime.enable"))
        await send(
            msg(
                "Emulation.setDeviceMetricsOverride",
                {"width": width, "height": height, "deviceScaleFactor": 2 if width < 600 else 1, "mobile": width < 600},
            )
        )
        await send(msg("Page.navigate", {"url": "http://localhost:8081/"}))
        await asyncio.sleep(4.5)

        r = await send(
            msg(
                "Page.captureScreenshot",
                {"format": "png", "captureBeyondViewport": False},
            )
        )
        data = r.get("data", "")
        path = f"/home/kei/Desktop/betweencoffee_delivery_enhance/docs/verify/_welcome_{name}.png"
        with open(path, "wb") as f:
            f.write(base64.b64decode(data))
        print("saved", path)

        try:
            urllib.request.urlopen(f"http://localhost:9222/json/close/{tab['id']}")
        except Exception:
            pass


if __name__ == "__main__":
    asyncio.run(main())
