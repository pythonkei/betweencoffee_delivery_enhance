#!/usr/bin/env python3
"""CDP 驗證：leader 行偏移是否符合原站 CSS（桌面 + 行動）"""
import asyncio, json, urllib.request
import websockets

BASE = "http://localhost:9222/json/new?about:blank"


async def run_viewport(width, height, mobile, cfg):
    req = urllib.request.Request(BASE, method="PUT")
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
        await send(msg("Page.enable"))
        await send(msg("Runtime.enable"))
        await send(msg("Emulation.setDeviceMetricsOverride",
                       {"width": width, "height": height, "deviceScaleFactor": 1, "mobile": mobile}))
        await send(msg("Page.navigate", {"url": "http://localhost:8081/about/"}))
        await asyncio.sleep(4)
        sel = ".partsSp" if mobile else ".partsPc"
        js = ("(function(){var s=document.querySelector('.bc-leader');"
              "var ps=s.querySelectorAll('%s .csBlock__leaderTarget--text--p');"
              "var off=[];ps.forEach(function(p){off.push(Math.round(p.getBoundingClientRect().left));});"
              "return off;})()") % sel
        offsets = await evaljs(js)
        print("%s offsets:" % ("MOBILE" if mobile else "DESKTOP"), offsets)
        ok = True
        for i, want in enumerate(cfg):
            got = offsets[i] if i < len(offsets) else None
            if got is None or abs(got - want) > 2:
                ok = False
                print("  MISMATCH line", i + 1, "got", got, "want", want)
        print("  RESULT:", "PASS" if ok else "FAIL")
        await send(msg("Page.close"))


async def main():
    # 桌面 1280px：外層 .container（1140 max）+ 0.7 縮放（--luv=0.7vw=8.96px）
    # container 左 content ≈85、csBlock padding-left 1.4641288433×8.96≈13px → li 起點 100
    # li--1/2:+13.17715959×8.96≈118 | li--6:+6.4421669107×8.96≈58 | li--11~13:+10.6149341142×8.96≈95
    desk_expected = [218, 218, 100, 100, 100, 157, 100, 100, 100, 100, 195, 195, 195]
    # 行動：375px，1vw=3.75px；section padding-left 5.3333333333vw≈20px（無容器縮放）
    # li--1~3:+31.2vw | li--6:0 | li--11/12:+22.67vw | li--13:0 | li--16~18:+17.33vw
    mob_expected = [137, 137, 137, 20, 20, 20, 20, 20, 20, 20, 105, 105, 20, 20, 20, 85, 85, 85]
    await run_viewport(1280, 900, False, desk_expected)
    await run_viewport(375, 667, True, mob_expected)


asyncio.run(main())
