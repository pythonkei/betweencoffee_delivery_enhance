#!/usr/bin/env python3
"""CDP 驗證：coffee 詳情頁杯量按鈕右上角 oz 標籤/文字加大（1280/1024/768/375px）

驗證項目：
1. oz 標籤 computed font-size / padding（桌面 0.85rem、行動 11px）
2. oz 標籤固定在按鈕右上角（chip.right ≈ btn.right、chip.top ≈ btn.top）
3. oz 標籤在按鈕範圍內（不溢出按鈕）
4. 頁面無水平溢出
"""
import asyncio, json, urllib.request
import websockets

WS = "http://localhost:9222/json/new?about:blank"

MEASURE = (
    "(function(){"
    "var btns=document.querySelectorAll('#cup-level-group .bc-option-btn');"
    "function rect(e){if(!e)return null;var b=e.getBoundingClientRect();"
    "return{l:Math.round(b.left),r:Math.round(b.right),t:Math.round(b.top),"
    "b:Math.round(b.bottom),w:Math.round(b.width),h:Math.round(b.height)};}"
    "function inter(a,b){if(!a||!b)return null;"
    "var w=Math.max(0,Math.min(a.r,b.r)-Math.max(a.l,b.l));"
    "var h=Math.max(0,Math.min(a.b,b.b)-Math.max(a.t,b.t));return{w:Math.round(w),h:Math.round(h)};}"
    "var oz=[];"
    "btns.forEach(function(btn){"
    "  var chip=btn.querySelector('.bc-option-oz');"
    "  if(!chip||btn.offsetParent===null)return;" + "  // 跳過 hidden（Small 12oz）\n"
    "  var cs=getComputedStyle(chip);"
    "  var br=rect(btn);var cr=rect(chip);"
    "  var icon=btn.querySelector('.bc-option-icon');"
    "  var label=btn.querySelector('.bc-option-label-text');"
    "  var content=null;"
    "  if(icon&&label){var ir=rect(icon);var lr=rect(label);"
    "    if(ir&&lr){content={l:Math.min(ir.l,lr.l),r:Math.max(ir.r,lr.r),"
    "      t:Math.min(ir.t,lr.t),b:Math.max(ir.b,lr.b)};}}"
    "  oz.push({"
    "    text:chip.textContent,"
    "    fontSize:cs.fontSize,paddingTop:cs.paddingTop,paddingRight:cs.paddingRight,"
    "    paddingBottom:cs.paddingBottom,paddingLeft:cs.paddingLeft,"
    "    chip:cr,btn:br,content:content,"
    "    chipContentOverlap:content?inter(cr,content):null,"
    "    chipInsideBtn:(cr&&br)?(cr.t>=br.t&&cr.b<=br.b&&cr.l>=br.l&&cr.r<=br.r):null,"
    "    chipAtTopRight:(cr&&br)?(Math.abs(cr.r-br.r)<=2&&Math.abs(cr.t-br.t)<=2):null"
    "  });"
    "});"
    "return{"
    "  url:location.href,"
    "  readyState:document.readyState,"
    "  ozCount:oz.length,oz:oz,"
    "  docScrollWidth:document.documentElement.scrollWidth,"
    "  innerWidth:window.innerWidth,"
    "  htmlFontSize:getComputedStyle(document.documentElement).fontSize"
    "};})()"
)


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

        for width in (1280, 1024, 768, 375, 320):
            await send(msg("Emulation.setDeviceMetricsOverride",
                           {"width": width, "height": 900, "deviceScaleFactor": 1, "mobile": width <= 768}))
            await send(msg("Page.navigate", {"url": "http://localhost:8081/coffee/1/"}))
            await asyncio.sleep(3.5)
            r = await send(msg("Runtime.evaluate", {"expression": MEASURE, "returnByValue": True}))
            v = r.get("result", {}).get("value", {})
            print(f"\n===== coffee 詳情頁 {width}px =====")
            print(json.dumps(v, ensure_ascii=False, indent=2))

        try:
            urllib.request.urlopen("http://localhost:9222/json/close/" + tab["id"])
        except Exception:
            pass


if __name__ == "__main__":
    asyncio.run(main())
