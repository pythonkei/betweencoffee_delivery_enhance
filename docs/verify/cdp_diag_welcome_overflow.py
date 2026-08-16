#!/usr/bin/env python3
"""CDP 診斷：bc-welcome-panel 平板/手機端 imgbox/img/last-order 是否超出 panel 容器"""
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
            "function rect(e){ if(!e) return null; var b=e.getBoundingClientRect(); var cs=getComputedStyle(e);"
            " return { left:Math.round(b.left), right:Math.round(b.right), w:Math.round(b.width), h:Math.round(b.height),"
            " top:Math.round(b.top), bottom:Math.round(b.bottom), mr:cs.marginRight, pos:cs.position }; }"
            "var panel=document.querySelector('.bc-welcome-panel');"
            "var imgbox=document.querySelector('.bc-welcome-imgbox');"
            "var img=document.querySelector('.bc-welcome-img');"
            "var link=document.querySelector('.bc-welcome-img-link');"
            "var lastOrder=document.querySelector('.bc-last-order');"
            "var p=rect(panel), ib=rect(imgbox), im=rect(img), lk=rect(link), lo=rect(lastOrder);"
            "var out={viewport:window.innerWidth, panel:p, imgbox:ib, img:im, imgLink:lk, lastOrder:lo};"
            "if(p&&ib) out.imgboxOverflowRight=Math.round(ib.right-p.right);"
            "if(p&&im) out.imgOverflowRight=Math.round(im.right-p.right);"
            "if(p&&lo) out.lastOrderOverflowRight=Math.round(lo.right-p.right);"
            "if(p&&lo) out.lastOrderOverflowLeft=Math.round(p.left-lo.left);"
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
    await measure(768, 1024, "平板")
    await measure(375, 812, "手機375")


if __name__ == "__main__":
    asyncio.run(main())
