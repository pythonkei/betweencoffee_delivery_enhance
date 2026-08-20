#!/usr/bin/env python3
"""CDP 驗證：topConcept 右側照片與文字 justify 後的關係

文字 justify 填滿欄位；照片行右 padding 讓文字停在照片前。
驗證：coffee_02/04/05/bean_01 的照片左緣 ≈ 該行文字尾端。
容差 -25~25px：窄寬度（768 附近）li--6 的最後字元 advance box
可能進入照片左緣透明邊距，但像素驗證實際字形與杯身有間隔。
"""
import asyncio, json, urllib.request
import websockets

BASE = "http://localhost:9222/json/new?about:blank"

JS = (
    "(function(){var box=document.querySelector('.bc-top-concept .partsPc');"
    "if(getComputedStyle(box).display==='none')box=document.querySelector('.bc-top-concept .partsSp');"
    "var out=[];box.querySelectorAll('.csBlock__leaderTarget').forEach(function(li){"
    "var spans=li.querySelectorAll('.csBlock__leaderTarget--text--p span');"
    "var last=spans[spans.length-1];var tr=last.getBoundingClientRect();"
    "li.querySelectorAll('.csBlock__leaderThum img').forEach(function(img){"
    "var ir=img.getBoundingClientRect();out.push({n:li.className.replace('csBlock__leaderTarget csBlock__leaderTarget--',''),"
    "src:img.src.split('/').pop(),textEnd:Math.round(tr.right),"
    "thumL:Math.round(ir.left),thumR:Math.round(ir.right)});});});"
    "return out;})()"
)

RIGHT = ("coffee_02.png", "coffee_04.png", "coffee_05.png", "bean_01.png")


async def check(width, mobile):
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
                       {"width": width, "height": 900, "deviceScaleFactor": 1, "mobile": mobile}))
        await send(msg("Page.navigate", {"url": "http://localhost:8081/about/"}))
        await asyncio.sleep(4)
        r = await evaljs(JS)
        await send(msg("Page.close"))
        return r


async def main():
    ok = True
    for w, m, label in [(1280, False, "desktop"), (1024, False, "desktop"),
                        (768, False, "desktop"), (375, True, "mobile")]:
        rows = await check(w, m)
        right_rows = [r for r in rows if r["src"] in RIGHT]
        bad = []
        for r in right_rows:
            gap = r["thumL"] - r["textEnd"]
            if not (-25 <= gap <= 25):
                bad.append("%s:%d" % (r["src"], gap))
        res = "PASS" if not bad else "FAIL " + str(bad)
        ok = ok and not bad
        print("%dpx %s -> %s" % (w, label, res))
    print("  RESULT:", "PASS" if ok else "FAIL")


asyncio.run(main())



