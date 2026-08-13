#!/usr/bin/env python3
"""CDP 驗證：bean 詳情頁烘焙水平 active 狀態金色"""
import asyncio, json, urllib.request
import websockets

WS = "http://localhost:9222/json/new?about:blank"


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
        await send(msg("Emulation.setDeviceMetricsOverride",
                       {"width": 1280, "height": 900, "deviceScaleFactor": 1, "mobile": False}))

        # 量測多個 bean（不同 roast_level）
        for bean_id in (1, 2, 3, 4):
            await send(msg("Page.navigate", {"url": f"http://localhost:8081/bean/{bean_id}/"}))
            await asyncio.sleep(3.5)
            js = (
                "(function(){var active=document.querySelector('.bc-roast-active');"
                "var dots=document.querySelectorAll('.roastrange-item.roast .roastrange-label::before');"
                "var actDot=null;"
                "var roastItems=document.querySelectorAll('.roastrange-item');"
                "roastItems.forEach(function(r){var lbl=r.querySelector('.roastrange-label span');"
                "if(lbl&&lbl.classList.contains('bc-roast-active')){"
                "var cs=getComputedStyle(lbl);actDot={text:lbl.textContent,color:cs.color,weight:cs.fontWeight};}});"
                "var dotBg=null;"
                "var activeItem=document.querySelector('.roastrange-item.roast');"
                "if(activeItem){var pseudo=getComputedStyle(activeItem.querySelector('.roastrange-label'),'::before');"
                "dotBg=pseudo.backgroundColor;}"
                "return{active:actDot,dotBg:dotBg,roastLevel:document.querySelector('.roastrange-item.roast span')?(document.querySelector('.roastrange-item.roast span').textContent):null};})()"
            )
            r = await send(msg("Runtime.evaluate", {"expression": js, "returnByValue": True}))
            v = r.get("result", {}).get("value", {})
            print(f"bean/{bean_id}/: {json.dumps(v, ensure_ascii=False)}")

        try:
            urllib.request.urlopen("http://localhost:9222/json/close/" + tab["id"])
        except Exception:
            pass


if __name__ == "__main__":
    asyncio.run(main())
