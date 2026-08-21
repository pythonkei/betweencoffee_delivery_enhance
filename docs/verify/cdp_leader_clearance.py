#!/usr/bin/env python3
"""CDP 驗證：topConcept 統右緣 + 照片 2 行高 + 全域不重疊 + justify 字距收斂

2026-08-21 方案 C：
- 所有照片（coffee_01~08/bean_01）2 行文字高（height = 2×font-size）。
- 統右緣：非照片列文字右緣一致（無階梯），照片列因避讓照片右縮。
- 任何照片不得與任何文字行重疊（全域檢查，含被覆蓋的下一行）。
驗證：
- 照片高度 = 2×font-size（±4px）。
- 照片與所有文字行無交集。
- justify 字距 ≤ 9px/字間。
- 統右緣列右緣一致（±3px）。
"""
import asyncio, json, urllib.request
import websockets

BASE = "http://localhost:9222/json/new?about:blank"

JS = (
    "(function(){var box=document.querySelector('.bc-top-concept .partsPc');"
    "if(getComputedStyle(box).display==='none')box=document.querySelector('.bc-top-concept .partsSp');"
    "var out={thums:[],rows:[]};"
    "box.querySelectorAll('.csBlock__leaderTarget').forEach(function(li){"
    "var m=li.className.match(/--(\\d+)/);"
    "var p=li.querySelector('.csBlock__leaderTarget--text--p');"
    "var spans=p.querySelectorAll('span');"
    "var fs=parseFloat(getComputedStyle(p).fontSize);"
    "var s0=spans[0].getBoundingClientRect();"
    "var lastR=spans[spans.length-1].getBoundingClientRect().right;"
    "var gaps=[];for(var j=0;j<spans.length-1;j++){"
    "gaps.push(spans[j+1].getBoundingClientRect().left-(spans[j].getBoundingClientRect().left+spans[j].getBoundingClientRect().width));}"
    "var spread=0;gaps.forEach(function(g){spread+=g});if(gaps.length)spread/=gaps.length;"
    "out.rows.push({n:parseInt(m[1]),left:Math.round(s0.left),right:Math.round(lastR),"
    "top:Math.round(s0.top),bottom:Math.round(s0.bottom),fs:Math.round(fs*10)/10,spread:Math.round(spread*10)/10});"
    "li.querySelectorAll('.csBlock__leaderThum img').forEach(function(img){"
    "var r=img.getBoundingClientRect();"
    "out.thums.push({n:parseInt(m[1]),src:img.src.split('/').pop(),left:Math.round(r.left),"
    "right:Math.round(r.right),top:Math.round(r.top),bottom:Math.round(r.bottom),h:Math.round(r.height)});});});"
    "return out;})()"
)

# 統右緣列（無照片避讓/縮排）：桌面 li2/5/8/12，行動版 li2/3/4/7/8/9/10/14/15
UNI_DESKTOP = [2, 5, 8, 12]
UNI_MOBILE = [2, 3, 4, 7, 8, 9, 10, 14, 15]


def overlap(t, row):
    return not (t["right"] <= row["left"] or t["left"] >= row["right"]
                or t["bottom"] <= row["top"] or t["top"] >= row["bottom"])


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
        thums, rows = r["thums"], r["rows"]
        fs = {row["n"]: row["fs"] for row in rows}
        bad = []
        # 1) 照片高度 = 2×font-size（照片所在行的字級）
        for t in thums:
            exp = round(2 * fs.get(t["n"], 0))
            if abs(t["h"] - exp) > 4:
                bad.append("%s(li%d) h=%d≠%d" % (t["src"], t["n"], t["h"], exp))
        # 2) 全域不重疊（照片 vs 所有文字行）
        for t in thums:
            for row in rows:
                if overlap(t, row):
                    bad.append("%s(li%d) 覆蓋 li%d 文字" % (t["src"], t["n"], row["n"]))
        # 3) justify 字距 ≤ 9px
        for row in rows:
            if row["spread"] > 9:
                bad.append("li%d 字距%.1f" % (row["n"], row["spread"]))
        # 4) 統右緣列右緣一致（±3px）
        uni = UNI_MOBILE if m else UNI_DESKTOP
        rights = [row["right"] for row in rows if row["n"] in uni]
        if max(rights) - min(rights) > 3:
            bad.append("統右緣偏移 %d" % (max(rights) - min(rights)))
        res = "PASS" if not bad else "FAIL " + str(bad[:8])
        ok = ok and not bad
        print("%dpx %s -> %s" % (w, label, res))
    print("  RESULT:", "PASS" if ok else "FAIL")


asyncio.run(main())
