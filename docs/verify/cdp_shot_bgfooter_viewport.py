#!/usr/bin/env python3
"""以「viewport-only」截圖補驗 #bc-bg-footer 在桌面/平板的實際外觀。
（captureBeyondViewport 對 GSAP 釘住區段會渲染成空白，故改用視窗截圖。）"""
import asyncio, base64, json, urllib.request
import websockets

BASE = "http://localhost:8081"
ROOT = "/home/kei/Desktop/betweencoffee_delivery_enhance"


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

        # 將釘牌（.footer-logo-cell）置中於視窗，確保白色線稿（黑底，無金底）完整入鏡
        CENTER_JS = (
            "(function(){var e=document.querySelector('#bc-bg-footer .footer-logo-cell');"
            "if(!e)return null;var r=e.getBoundingClientRect();"
            "window.scrollTo(0, Math.round(window.scrollY + r.top + r.height/2 - innerHeight/2));"
            "return Math.round(window.scrollY);})()"
        )
        INFO_JS = (
            "(function(){var e=document.querySelector('#bc-bg-footer .footer-logo-cell');"
            "var c=e?e.getBoundingClientRect():null;return {y:Math.round(window.scrollY),"
            "sh:document.body.scrollHeight,ih:innerHeight,"
            "cell:c?{top:Math.round(c.top),h:Math.round(c.height),"
            "mid:Math.round(c.top+c.height/2)}:null};})()"
        )

        for w, h, name in [(1280, 800, "desktop"), (768, 1024, "tablet")]:
            await send(msg("Emulation.setDeviceMetricsOverride",
                           {"width": w, "height": h, "deviceScaleFactor": 1, "mobile": False}))
            await send(msg("Page.navigate", {"url": BASE + "/about/"}))
            await asyncio.sleep(4)
            # 逐步捲到底，讓 ScrollTrigger 完成釘住/顯示
            for frac in [0.5, 0.8, 1.0]:
                await evaljs(f"window.scrollTo(0, document.body.scrollHeight*{frac})")
                await asyncio.sleep(1.2)
            # 多次微調：抵銷 ScrollTrigger 釘住造成的位移，直到釘牌穩定置中
            for _ in range(4):
                await evaljs(CENTER_JS)
                await asyncio.sleep(1.0)
            info = await evaljs(INFO_JS)
            print(name, info)
            res = await send(msg("Page.captureScreenshot", {"format": "png"}))
            with open(f"{ROOT}/_verify_bgfooter_vp_{name}.png", "wb") as f:
                f.write(base64.b64decode(res["data"]))
            print(f"   shot -> _verify_bgfooter_vp_{name}.png")
        await send(msg("Page.close"))

asyncio.run(main())
