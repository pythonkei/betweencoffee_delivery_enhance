#!/usr/bin/env python3
"""CDP 量測：bean/coffee 詳情頁返回按鈕水平位置（桌面/行動端）"""
import asyncio, json, urllib.request
import websockets

WS = "http://localhost:9222/json/new?about:blank"

MEASURE = (
    "(function(){"
    "var btn = document.querySelector('.r-btn');"
    "var wrap = document.querySelector('.text-center.mt-3');"
    "var form = document.querySelector('#add-to-cart-form');"
    "function r(e){if(!e)return null;var b=e.getBoundingClientRect();return{l:Math.round(b.left),r:Math.round(b.right),w:Math.round(b.width),cx:Math.round(b.left+b.width/2)};}"
    "var out={"
    "  readyState: document.readyState,"
    "  url: location.href,"
    "  rbtnCount: document.querySelectorAll('.r-btn').length,"
    "  textcenterMt3Count: document.querySelectorAll('.text-center.mt-3').length,"
    "  btn:r(btn),wrap:r(wrap),form:r(form)};"
    "if(wrap&&btn){var wb=wrap.getBoundingClientRect();var bb=btn.getBoundingClientRect();"
    "out.btnOffsetFromWrapCenter=Math.round((bb.left+bb.width/2)-(wb.left+wb.width/2));}"
    "if(btn&&form){var fb=form.getBoundingClientRect();var bb2=btn.getBoundingClientRect();"
    "out.btnCenterVsFormCenter=Math.round((bb2.left+bb2.width/2)-(fb.left+fb.width/2));}"
    "return out;})()"
)


async def main():
    req = urllib.request.Request(WS, method="PUT")
    tab = json.loads(urllib.request.urlopen(req).read())
    async with websockets.connect(tab["webSocketDebuggerUrl"]) as ws:
        mid = 1
        def msg(m, p=None):
            nonlocal mid
            r = {"id": mid, "method": m, "params": p or {}}
            mid += 1
            return r
        async def send(m):
            await ws.send(json.dumps(m))
            while True:
                r = json.loads(await ws.recv())
                if r.get("id") == m["id"]:
                    return r.get("result", {})
        await send(msg("Page.enable"))
        await send(msg("Runtime.enable"))
        await send(msg("Page.setCacheDisabled", {"cacheDisabled": True}))

        for url, label in (("http://localhost:8081/bean/1/", "bean"), ("http://localhost:8081/coffee/1/", "coffee")):
            for width in (1280, 375):
                await send(msg("Emulation.setDeviceMetricsOverride",
                               {"width": width, "height": 900, "deviceScaleFactor": 1, "mobile": width <= 768}))
                await send(msg("Page.navigate", {"url": url}))
                await asyncio.sleep(3.5)
                r = await send(msg("Runtime.evaluate", {"expression": MEASURE, "returnByValue": True}))
                v = r.get("result", {}).get("value", {})
                print(f"\n===== {label} 詳情頁 {width}px =====")
                print(json.dumps(v, ensure_ascii=False, indent=2))

        try:
            urllib.request.urlopen("http://localhost:9222/json/close/" + tab["id"])
        except Exception:
            pass


if __name__ == "__main__":
    asyncio.run(main())
