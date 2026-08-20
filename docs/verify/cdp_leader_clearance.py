#!/usr/bin/env python3
"""CDP 驗證：leader 右側照片（coffee_02/04/05，right:0）不被固定 Order/profile 按鈕遮住

- 檢查多種桌面寬度（1280 / 1024 / 768）下，三張標記照片的右緣 < profile 按鈕左緣
- 行動版（≤767）照片不涉及（partsPc 隱藏）
"""
import asyncio, json, urllib.request
import websockets

BASE = "http://localhost:9222/json/new?about:blank"


async def check(width):
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
                       {"width": width, "height": 900, "deviceScaleFactor": 1, "mobile": False}))
        await send(msg("Page.navigate", {"url": "http://localhost:8081/about/"}))
        await asyncio.sleep(4)
        js = ("(function(){var box=document.querySelector('.bc-leader .partsPc');"
              "var ths=[];box.querySelectorAll('.csBlock__leaderThum img').forEach(function(th){"
              "var r=th.getBoundingClientRect();ths.push({src:th.src.split('/').pop(),"
              "l:Math.round(r.left),r:Math.round(r.right),t:Math.round(r.top),b:Math.round(r.bottom)});});"
              "var flagged=ths.filter(function(t){return /coffee_(02|04|05)/.test(t.src)});"
              "var prof=document.querySelector('.bc-attract-profile').getBoundingClientRect();"
              "var order=document.querySelector('.bc-attract-buy').getBoundingClientRect();"
              "return{flagged:flagged,profileLeft:Math.round(prof.left),orderLeft:Math.round(order.left)};})()")
        r = await evaljs(js)
        await send(msg("Page.close"))
        return r


async def main():
    ok = True
    for w in [1280, 1024, 768]:
        r = await check(w)
        prof_l = r["profileLeft"]
        gaps = {t["src"]: prof_l - t["r"] for t in r["flagged"]}
        cleared = all(g >= 10 for g in gaps.values())
        ok = ok and cleared
        print("width=%d profileLeft=%d flaggedRightGaps=%s -> %s"
              % (w, prof_l, gaps, "PASS" if cleared else "FAIL"))
    print("  RESULT:", "PASS" if ok else "FAIL")


asyncio.run(main())
