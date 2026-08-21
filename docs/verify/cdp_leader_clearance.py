#!/usr/bin/env python3
"""CDP 驗證：topConcept 右側照片 2 行高、文字不與照片重疊、justify 字距收斂

2026-08-21 新設計：
- 右側照片（coffee_02/04/05/bean_01）高度 = 2×font-size（桌面 4.4vw、行動 8.4vw），
  coffee_04 桌面維持原較大尺寸（7.83vw，不縮小）。
- 各列右 padding 收斂 justify 字距；文字尾端停在照片左緣前（不重疊）。
驗證：
- 照片高度符合預期（±4px）。
- 文字尾端 ≤ 照片左緣 - 8px（不重疊且保留間距）。
- justify 字距 ≤ 8px/字間。
"""
import asyncio, json, urllib.request
import websockets

BASE = "http://localhost:9222/json/new?about:blank"

JS = (
    "(function(){var box=document.querySelector('.bc-top-concept .partsPc');"
    "if(getComputedStyle(box).display==='none')box=document.querySelector('.bc-top-concept .partsSp');"
    "var out=[];box.querySelectorAll('.csBlock__leaderTarget').forEach(function(li){"
    "var p=li.querySelector('.csBlock__leaderTarget--text--p');"
    "var spans=p.querySelectorAll('span');"
    "var textEnd=spans[spans.length-1].getBoundingClientRect().right;"
    "var fs=parseFloat(getComputedStyle(p).fontSize);"
    "var gaps=[];for(var j=0;j<spans.length-1;j++){"
    "gaps.push(spans[j+1].getBoundingClientRect().left-(spans[j].getBoundingClientRect().left+spans[j].getBoundingClientRect().width));}"
    "var spread=0;gaps.forEach(function(g){spread+=g});if(gaps.length)spread/=gaps.length;"
    "li.querySelectorAll('.csBlock__leaderThum img').forEach(function(img){"
    "var ir=img.getBoundingClientRect();out.push({n:li.className.replace('csBlock__leaderTarget csBlock__leaderTarget--',''),"
    "src:img.src.split('/').pop(),textEnd:Math.round(textEnd),"
    "thumL:Math.round(ir.left),thumR:Math.round(ir.right),"
    "thumH:Math.round(ir.height),fs:Math.round(fs*10)/10,spread:Math.round(spread*10)/10});});});"
    "return out;})()"
)

# 預期照片高度：coffee_04 桌面維持原尺寸（7.83vw），行動版 2 行高；其餘右側照片 2 行高（2×font-size）
def expected_h(src, fs, vw, mobile):
    if src == "coffee_04.png":
        return round(8.4 * vw / 100) if mobile else round(7.83 * vw / 100)
    return round(2 * fs)


async def check(width, mobile, vw):
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
    for w, m, label, vw in [(1280, False, "desktop", 1280), (1024, False, "desktop", 1024),
                            (768, False, "desktop", 768), (375, True, "mobile", 375)]:
        rows = await check(w, m, vw)
        bad = []
        for r in rows:
            # 只檢查貼齊行右緣的右側照片（排除左側 coffee_01/03/08）
            if r["thumR"] < w - 60:
                continue
            h_exp = expected_h(r["src"], r["fs"], vw, m)
            if abs(r["thumH"] - h_exp) > 4:
                bad.append("%s h=%d≠%d" % (r["src"], r["thumH"], h_exp))
            if r["thumL"] - r["textEnd"] < 8:
                bad.append("%s 重疊(gap=%d)" % (r["src"], r["thumL"] - r["textEnd"]))
            if r["spread"] > 8:
                bad.append("%s 字距%.1f" % (r["src"], r["spread"]))
        res = "PASS" if not bad else "FAIL " + str(bad)
        ok = ok and not bad
        print("%dpx %s -> %s" % (w, label, res))
    print("  RESULT:", "PASS" if ok else "FAIL")


asyncio.run(main())




