#!/usr/bin/env python3
"""CDP 驗證：topConcept 回歸 hakujuji 原站（照片尺寸、壓字、scroll-scrub）

2026-08-21：回歸 hakujuji 原站樣式。
- 照片尺寸：width 用原站 vw 值、高度依照片自然比例（thum--6/7 行動版固定框 cover）。
- 照片壓字：原站設計允許照片與文字重疊（z-index 在上）——但照片不得超出欄位右緣。
- 文字：原站無 justify（自然寬），溢出與原站一致（不檢查 justify 字距）。
"""
import asyncio, json, urllib.request, websockets

BASE = "http://localhost:9222/json/new?about:blank"

JS = (
    "(function(){var box=document.querySelector('.bc-top-concept .partsPc');"
    "if(getComputedStyle(box).display==='none')box=document.querySelector('.bc-top-concept .partsSp');"
    "var rows=[];"
    "box.querySelectorAll('.csBlock__leaderTarget--text--p').forEach(function(p){"
    "var sp=p.querySelectorAll('span');"
    "var r0=sp[0].getBoundingClientRect();"
    "var last=sp[sp.length-1].getBoundingClientRect();"
    "rows.push({L:Math.round(r0.left),R:Math.round(last.right),T:Math.round(r0.top),B:Math.round(last.bottom)});});"
    "var out=[];"
    "box.querySelectorAll('.csBlock__leaderThum').forEach(function(th){"
    "var m=th.className.match(/--(\\d+)/);"
    "var img=th.querySelector('img');"
    "var r=th.getBoundingClientRect();"
    "out.push({n:parseInt(m[1]),left:Math.round(r.left),right:Math.round(r.right),top:Math.round(r.top),bottom:Math.round(r.bottom),"
    "w:Math.round(r.width),h:Math.round(r.height),nw:(img?img.naturalWidth:0),nh:(img?img.naturalHeight:0)});});"
    "return {photos:out,rows:rows};})()"
)

# 桌面（2026-08-21 thum--4/6 再加寬）：寬×高（vw）
DESK_WIDE = {1: (12.0, 5.5), 2: (4.0, 2.3), 3: (4.0, 2.3), 4: (8.0, 5.5),
             5: (4.0, 2.3), 6: (10.0, 8.7), 7: (3.5, 3.0)}
DESK_NARROW = {1: (10.0, 5.3), 2: (3.4, 2.0), 3: (3.4, 2.0), 4: (6.0, 5.3),
               5: (3.4, 2.0), 6: (8.0, 8.0), 7: (3.0, 2.0)}
# 行動版（thum--4/6 加寬）
SP_FIXED = {1: (18.0, 10.8), 2: (15.0, 10.8), 3: (15.0, 10.8), 4: (16.0, 10.8),
            6: (13.0, 16.2), 7: (16.0, 10.8)}


def expected_size(n, vw, mobile):
    desk = DESK_NARROW if vw < 1024 else DESK_WIDE
    if mobile:
        if n in SP_FIXED:
            w, h = SP_FIXED[n]
            return round(w * vw / 100), round(h * vw / 100)
        return None, None
    w, h = desk[n]
    return round(w * vw / 100), round(h * vw / 100)


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
        await send(msg("Page.setCacheDisabled", {"cacheDisabled": True}))
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
        r = await check(w, m)
        photos, rows = r["photos"], r["rows"]
        bad = []
        # 0) 照片與文字不重疊（不壓字）
        for p in photos:
            for row in rows:
                if not (p["right"] <= row["L"] or p["left"] >= row["R"]
                        or p["bottom"] <= row["T"] or p["top"] >= row["B"]):
                    bad.append("thum%d 壓文字" % p["n"])
        for p in photos:
            exp_w, exp_h = expected_size(p["n"], w, m)
            if abs(p["w"] - exp_w) > 3:
                bad.append("thum%d 寬 %d≠%d" % (p["n"], p["w"], exp_w))
            if exp_h is not None:
                if abs(p["h"] - exp_h) > 3:
                    bad.append("thum%d 高 %d≠%d" % (p["n"], p["h"], exp_h))
            else:
                # 高度自然 = width ÷ 照片比例
                if p["nw"] and p["nh"]:
                    exp = round(p["w"] * p["nh"] / p["nw"])
                    if abs(p["h"] - exp) > 3:
                        bad.append("thum%d 自然高 %d≠%d" % (p["n"], p["h"], exp))
        res = "PASS" if not bad else "FAIL " + str(bad[:6])
        ok = ok and not bad
        print("%dpx %s -> %s" % (w, label, res))
    print("  RESULT:", "PASS" if ok else "FAIL")


asyncio.run(main())
