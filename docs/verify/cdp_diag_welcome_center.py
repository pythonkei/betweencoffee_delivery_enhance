#!/usr/bin/env python3
"""CDP 診斷：bc-welcome-panel 是否位於橫幅底部水平中心（桌面 vs 手機）"""
import asyncio
import json
import urllib.request

import websockets

WS = "http://localhost:9222/json/new?about:blank"


async def measure(width, height, label):
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
                {
                    "width": width,
                    "height": height,
                    "deviceScaleFactor": 2 if width < 600 else 1,
                    "mobile": width < 600,
                },
            )
        )
        await send(msg("Page.navigate", {"url": "http://localhost:8081/"}))
        await asyncio.sleep(4.5)

        js = (
            "(function(){"
            "var w = window.innerWidth;"
            "function rect(sel){ var e=document.querySelector(sel); if(!e) return null;"
            " var b=e.getBoundingClientRect();"
            " return { left:Math.round(b.left), right:Math.round(b.right), w:Math.round(b.width),"
            " top:Math.round(b.top), bottom:Math.round(b.bottom), center:Math.round((b.left+b.right)/2) }; }"
            "var banner=rect('.home-slider');"
            "var panel=rect('.bc-welcome-panel');"
            "var section=rect('.bc-welcome-section');"
            "var wrap=rect('.bc-welcome-wrap');"
            "var out={viewport:w, banner:banner, panel:panel, section:section, wrap:wrap};"
            "if(banner&&panel){ out.panelCenter=banner?Math.round(banner.center-panel.center):null; }"
            "var cs=panel?getComputedStyle(document.querySelector('.bc-welcome-panel')):null;"
            "out.panelCSS=cs?{margin:cs.margin, width:cs.width, maxWidth:cs.maxWidth}:null;"
            "return out;"
            "})()"
        )
        r = await send(msg("Runtime.evaluate", {"expression": js, "returnByValue": True}))
        print(f"===== {label}（{width}px） =====")
        print(json.dumps(r.get("result", {}).get("value", {}), ensure_ascii=False, indent=2))

        try:
            urllib.request.urlopen(f"http://localhost:9222/json/close/{tab['id']}")
        except Exception:
            pass


async def main():
    await measure(1280, 900, "桌面")
    await measure(768, 1024, "平板")
    await measure(414, 896, "手機414")
    await measure(375, 812, "手機375")
    await measure(320, 640, "手機320")


if __name__ == "__main__":
    asyncio.run(main())
