#!/usr/bin/env python3
"""CDP 驗證：topConcept leader 行偏移是否符合原站 CSS（桌面 + 行動）"""
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
        js = ("(function(){var s=document.querySelector('.bc-top-concept');"
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
    # 桌面 1280px：li 起點 367；縮排列 li--1/2/5/6/11/12 +4vw≈51px（左側照片及其覆蓋行避讓）
    desk_expected = [418, 418, 367, 367, 418, 418, 367, 367, 367, 367, 418, 418, 367]
    # 行動 375px：li 起點 40；縮排列 li--1/2/11/12/16/17 +8.2vw≈31px
    mob_expected = [71, 71, 40, 40, 40, 40, 40, 40, 40, 40, 71, 71, 40, 40, 40, 71, 71, 40]
    await run_viewport(1280, 900, False, desk_expected)
    await run_viewport(375, 812, True, mob_expected)


asyncio.run(main())
