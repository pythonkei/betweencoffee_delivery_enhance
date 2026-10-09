#!/usr/bin/env python3
"""以「viewport-only」截圖驗首頁最上方 BC 動態 hero（#bc-bg-footer）與其下方的 GUNTE hero。

2026-10-09：首頁把 BC 動態模組（Hug in a Cup 時鐘，原為頁尾）移到最上方當第一個 hero，
GUNTE hero 移到它下方。本腳本產出 3 斷點 × 2 張視窗截圖作視覺證據，並印出幾何資訊
（首 section 類別、margin-top、footer 元素數、兩個 hero 的 rect）。
（captureBeyondViewport 對 GSAP 釘住／reveal 區段會渲染成空白，故一律用視窗截圖。）
用法：站台須在 http://127.0.0.1:8081 跑、CDP 瀏覽器須在 9222（見 CDP_SETUP.md）。
"""
import asyncio, base64, json, urllib.request
import websockets

BASE = "http://localhost:8081"
ROOT = "/home/kei/Desktop/betweencoffee_delivery_enhance"

INFO_JS = (
    "(function(){"
    "var secs=document.querySelectorAll('.bc-page-content > section');"
    "var hero=document.querySelector('.bc-bg-hero');"
    "var bg=document.getElementById('bc-bg-footer');"
    "var g=document.querySelector('.bc-gunte-hero');"
    "var r=function(e){if(!e)return null;var b=e.getBoundingClientRect();"
    "return {top:Math.round(b.top),h:Math.round(b.height)};};"
    "return {y:Math.round(window.scrollY),sh:document.body.scrollHeight,"
    "firstSec:secs.length?secs[0].className.trim():null,secCount:secs.length,"
    "heroMT:hero?getComputedStyle(hero).marginTop:null,"
    "footerCount:document.querySelectorAll('footer').length,"
    "bgIdCount:document.querySelectorAll('#bc-bg-footer').length,"
    "bg:r(bg),gunte:r(g),gunteBeforeBg:!!(g&&bg)&&"
    "(g.compareDocumentPosition(bg)&Node.DOCUMENT_POSITION_PRECEDING)>0};})()"
)


async def main():
    req = urllib.request.Request("http://localhost:9222/json/new?about:blank", method="PUT")
    tab = json.loads(urllib.request.urlopen(req).read())
    async with websockets.connect(tab["webSocketDebuggerUrl"], max_size=200 * 1024 * 1024) as ws:
        mid = 1

        def msg(m, p=None):
            nonlocal mid
            m = {"id": mid, "method": m, "params": p or {}}
            mid += 1
            return m

        async def send(m):
            await ws.send(json.dumps(m))
            while True:
                r = json.loads(await ws.recv())
                if r.get("id") == m["id"]:
                    return r.get("result", {})

        await send(msg("Page.enable"))
        await send(msg("Runtime.enable"))

        async def evaljs(e):
            r = await send(msg("Runtime.evaluate", {"expression": e, "returnByValue": True}))
            return r.get("result", {}).get("value")

        for w, h, mobile, name in [(1280, 800, False, "desktop"),
                                   (768, 1024, False, "tablet"),
                                   (390, 844, True, "mobile")]:
            await send(msg("Emulation.setDeviceMetricsOverride",
                           {"width": w, "height": h, "deviceScaleFactor": 1, "mobile": mobile}))
            await send(msg("Page.navigate", {"url": BASE + "/"}))
            await asyncio.sleep(5)  # 等 GSAP reveal / 時鐘 / hero 輪播初始化
            info = await evaljs(INFO_JS)
            print(f"[{name} {w}x{h}] {info}")
            res = await send(msg("Page.captureScreenshot", {"format": "png"}))
            with open(f"{ROOT}/_verify_index_hero_top_{name}.png", "wb") as f:
                f.write(base64.b64decode(res["data"]))
            print(f"   shot -> _verify_index_hero_top_{name}.png")

            # 捲到 GUNTE hero 頂端，證明它緊接在 BC hero 下方
            await evaljs("(function(){var g=document.querySelector('.bc-gunte-hero');"
                         "if(g)window.scrollTo(0, Math.round(window.scrollY +"
                         " g.getBoundingClientRect().top));})()")
            await asyncio.sleep(2)
            print(f"   gunte scroll -> {await evaljs(INFO_JS)}")
            res = await send(msg("Page.captureScreenshot", {"format": "png"}))
            with open(f"{ROOT}/_verify_index_hero_gunte_{name}.png", "wb") as f:
                f.write(base64.b64decode(res["data"]))
            print(f"   shot -> _verify_index_hero_gunte_{name}.png")
        await send(msg("Page.close"))

asyncio.run(main())
