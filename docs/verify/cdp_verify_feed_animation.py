#!/usr/bin/env python3
"""CDP 驗證：首頁 .feed 水平移動 SVG 蒙版動畫（landing.css 載入修復）"""
import asyncio, json, urllib.request
import websockets

WS = "http://localhost:9222/json/new?about:blank"


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
        await send(msg("Emulation.setDeviceMetricsOverride",
                       {"width": 1280, "height": 900, "deviceScaleFactor": 1, "mobile": False}))
        await send(msg("Page.navigate", {"url": "http://localhost:8081/"}))
        await asyncio.sleep(4.0)

        js = (
            "(function(){"
            "var sheets = Array.from(document.styleSheets).map(function(s){return s.href||''});"
            "var parts = document.querySelector('.feed__layer-parts');"
            "var feed = document.querySelector('.feed');"
            "var cs = parts ? getComputedStyle(parts) : null;"
            "var fs = feed ? getComputedStyle(feed) : null;"
            "return {"
            "  landingLoaded: sheets.some(function(h){return h && h.indexOf('landing.css') !== -1;}),"
            "  landingHref: sheets.filter(function(h){return h && h.indexOf('landing.css') !== -1;}),"
            "  feedFound: !!feed, partsFound: !!parts,"
            "  animationName: cs ? cs.animationName : null,"
            "  animationDuration: cs ? cs.animationDuration : null,"
            "  clipPath: cs ? cs.clipPath : null,"
            "  feedBg: fs ? fs.backgroundImage.slice(0, 80) : null,"
            "  transform: cs ? cs.transform : null"
            "};})()"
        )
        r = await send(msg("Runtime.evaluate", {"expression": js, "returnByValue": True}))
        print(json.dumps(r.get("result", {}).get("value", {}), ensure_ascii=False, indent=2))

        # 追蹤 transform 動畫兩次取樣，確認在移動
        await asyncio.sleep(2.0)
        r2 = await send(msg("Runtime.evaluate",
                            {"expression": "getComputedStyle(document.querySelector('.feed__layer-parts')).transform",
                             "returnByValue": True}))
        print("2s 後 transform:", r2.get("result", {}).get("value"))
        await asyncio.sleep(2.0)
        r3 = await send(msg("Runtime.evaluate",
                            {"expression": "getComputedStyle(document.querySelector('.feed__layer-parts')).transform",
                             "returnByValue": True}))
        print("4s 後 transform:", r3.get("result", {}).get("value"))

        try:
            urllib.request.urlopen("http://localhost:9222/json/close/" + tab["id"])
        except Exception:
            pass


if __name__ == "__main__":
    asyncio.run(main())
