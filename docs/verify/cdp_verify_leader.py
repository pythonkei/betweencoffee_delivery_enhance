#!/usr/bin/env python3
"""CDP 驗證：about.html 的 hakujuji topConcept 整合
- 桌面 1280x900：partsPc 顯示（13 行）、partsSp 隱藏
- 行動 375x667：partsSp 顯示（18 行）、partsPc 隱藏
- scroll-scrub 逐字點亮：初始 span opacity=0.3 → 捲到區塊底部全部 opacity=1
- 輸出截圖
"""
import asyncio, json, urllib.request
import websockets

WS = "http://localhost:9222/json/new?about:blank"


async def main():
    req = urllib.request.Request(WS, method="PUT")
    tab = json.loads(urllib.request.urlopen(req).read())
    async with websockets.connect(tab["webSocketDebuggerUrl"], max_size=None) as ws:
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
        async def evaljs(expr):
            r = await send(msg("Runtime.evaluate", {"expression": expr, "returnByValue": True}))
            return r.get("result", {}).get("value")
        async def shot(path):
            await asyncio.sleep(0.3)
            r = await send(msg("Page.captureScreenshot", {"format": "png"}))
            data = r.get("data")
            if data:
                import base64
                open(path, "wb").write(base64.b64decode(data))
                print("saved", path)

        await send(msg("Page.enable"))
        await send(msg("Runtime.enable"))
        await send(msg("Page.setCacheDisabled", {"cacheDisabled": True}))

        # ===== 桌面 =====
        await send(msg("Emulation.setDeviceMetricsOverride",
                       {"width": 1280, "height": 900, "deviceScaleFactor": 1, "mobile": False}))
        await send(msg("Page.navigate", {"url": "http://localhost:8081/about/"}))
        await asyncio.sleep(4)

        leader = await evaljs(
            "(function(){"
            "var s=document.querySelector('.bc-top-concept');if(!s)return{missing:true};"
            "var pc=s.querySelector('.partsPc .csBlock__leaderTarget--text--p span');"
            "var sp=s.querySelector('.partsSp .csBlock__leaderTarget--text--p span');"
            "return{"
            "pcVisible:getComputedStyle(s.querySelector('.partsPc')).display!=='none',"
            "spVisible:getComputedStyle(s.querySelector('.partsSp')).display!=='none',"
            "pcLi:s.querySelectorAll('.partsPc .csBlock__leaderTarget').length,"
            "spLi:s.querySelectorAll('.partsSp .csBlock__leaderTarget').length,"
            "spanOpacityBefore:(pc?getComputedStyle(pc).opacity:null),"
            "spans:s.querySelectorAll('.partsPc .csBlock__leaderTarget--text--p span').length,"
            "thums:s.querySelectorAll('.partsPc .csBlock__leaderThum img').length"
            "};})()"
        )
        print("DESKTOP before scroll:", json.dumps(leader, ensure_ascii=False))

        # 捲到區塊底部（scrub end：全部點亮）
        await evaljs(
            "(function(){"
            "var s=document.querySelector('.bc-top-concept');"
            "window.scrollTo(0, s.getBoundingClientRect().bottom + window.scrollY - window.innerHeight*0.4);"
            "return true;})()"
        )
        await asyncio.sleep(1.2)
        after = await evaljs(
            "(function(){"
            "var s=document.querySelector('.bc-top-concept');"
            "var spans=s.querySelectorAll('.partsPc .csBlock__leaderTarget--text--p span');"
            "var one=0;spans.forEach(function(sp){if(parseFloat(getComputedStyle(sp).opacity)>=0.99)one++;});"
            "return{litOne:one,total:spans.length};})()"
        )
        print("DESKTOP after scroll:", json.dumps(after, ensure_ascii=False))
        await shot("/tmp/bc_topconcept_desktop.png")

        # ===== 行動 =====
        await send(msg("Emulation.setDeviceMetricsOverride",
                       {"width": 375, "height": 667, "deviceScaleFactor": 2, "mobile": True}))
        await send(msg("Page.navigate", {"url": "http://localhost:8081/about/"}))
        await asyncio.sleep(4)
        mleader = await evaljs(
            "(function(){"
            "var s=document.querySelector('.bc-top-concept');if(!s)return{missing:true};"
            "var sp=s.querySelector('.partsSp .csBlock__leaderTarget--text--p span');"
            "return{"
            "pcVisible:getComputedStyle(s.querySelector('.partsPc')).display!=='none',"
            "spVisible:getComputedStyle(s.querySelector('.partsSp')).display!=='none',"
            "pcLi:s.querySelectorAll('.partsPc .csBlock__leaderTarget').length,"
            "spLi:s.querySelectorAll('.partsSp .csBlock__leaderTarget').length,"
            "spanOpacityBefore:(sp?getComputedStyle(sp).opacity:null),"
            "spans:s.querySelectorAll('.partsSp .csBlock__leaderTarget--text--p span').length,"
            "thums:s.querySelectorAll('.partsSp .csBlock__leaderThum img').length"
            "};})()"
        )
        print("MOBILE before scroll:", json.dumps(mleader, ensure_ascii=False))
        await evaljs(
            "(function(){"
            "var s=document.querySelector('.bc-top-concept');"
            "window.scrollTo(0, s.getBoundingClientRect().bottom + window.scrollY - window.innerHeight*0.4);"
            "return true;})()"
        )
        await asyncio.sleep(1.2)
        mafter = await evaljs(
            "(function(){"
            "var s=document.querySelector('.bc-top-concept');"
            "var spans=s.querySelectorAll('.partsSp .csBlock__leaderTarget--text--p span');"
            "var one=0;spans.forEach(function(sp){if(parseFloat(getComputedStyle(sp).opacity)>=0.99)one++;});"
            "return{litOne:one,total:spans.length};})()"
        )
        print("MOBILE after scroll:", json.dumps(mafter, ensure_ascii=False))
        await shot("/tmp/bc_topconcept_mobile.png")

        await send(msg("Page.close"))


asyncio.run(main())

