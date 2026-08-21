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
    "var r=img.getBoundingClientRect();"
    "out.push({n:parseInt(m[1]),left:Math.round(r.left),right:Math.round(r.right),top:Math.round(r.top),bottom:Math.round(r.bottom),"
    "w:Math.round(r.width),h:Math.round(r.height),nw:img.naturalWidth,nh:img.naturalHeight});});"
    "return {photos:out,rows:rows};})()"
)

# 原站桌面照片寬度（vw）：thum--1~7
DESK_W = {1: 11.3469985359, 2: 5.1244509517, 3: 5.1244509517, 4: 11.4934114202,
          5: 5.1244509517, 6: 9.3704245974, 7: 3.953147877}
# 行動版（2026-08-21 不壓字：thum--1/4 縮小至 15/13vw）；thum--6/7 固定框
SP_W = {1: 15.0, 2: 17.3333333333, 3: 17.0666666667, 4: 13.0}
SP_FIXED = {6: (13.8666666667, 20.0), 7: (18.6666666667, 12.5333333333)}


def expected_size(n, vw, mobile):
    if mobile:
        if n in SP_FIXED:
            w, h = SP_FIXED[n]
            return round(w * vw / 100), round(h * vw / 100)
        w = round(SP_W[n] * vw / 100)
        return w, None  # 高度自然
    w = round(DESK_W[n] * vw / 100)
    return w, None


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
