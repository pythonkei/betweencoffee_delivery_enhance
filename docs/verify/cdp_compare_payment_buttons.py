#!/usr/bin/env python3
"""CDP 量測：coffee_menu 落單按鈕 vs FPS/Cash 付款頁按鈕外觀（登入訪問）"""
import asyncio, json, os, sys, urllib.request
import websockets

sys.path.insert(0, "/home/kei/Desktop/betweencoffee_delivery_enhance")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "betweencoffee_delivery.settings")
import django  # noqa: E402
django.setup()
from django.test import Client  # noqa: E402
from django.contrib.auth import get_user_model  # noqa: E402

WS = "http://localhost:9222/json/new?about:blank"


def get_session_cookie():
    c = Client()
    c.force_login(get_user_model().objects.get(id=58))
    c.get("/")
    return next((v.value for k, v in c.cookies.items() if k == "sessionid"), None)


async def main():
    sid = session_id_cache
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
        await send(msg("Network.enable"))
        await send(msg("Page.setCacheDisabled", {"cacheDisabled": True}))
        await send(msg("Emulation.setDeviceMetricsOverride",
                       {"width": 1280, "height": 900, "deviceScaleFactor": 1, "mobile": False}))
        if sid:
            await send(msg("Network.setCookie",
                           {"name": "sessionid", "value": sid, "domain": "localhost", "path": "/"}))

        def btn_js(sel):
            return (
                "(function(){var b=document.querySelector('" + sel + "');"
                "if(!b)return{found:false,sel:'" + sel + "'};"
                "var cs=getComputedStyle(b);var r=b.getBoundingClientRect();"
                "return{found:true,sel:'" + sel + "',text:(b.textContent||'').trim().slice(0,20),"
                "w:Math.round(r.width),h:Math.round(r.height),"
                "bg:cs.backgroundColor,border:cs.borderTopColor+' '+(cs.borderTopWidth),color:cs.color,"
                "radius:cs.borderRadius,fs:cs.fontSize,shadow:cs.boxShadow,cls:b.className};})()"
            )

        pages = [
            ("http://localhost:8081/coffee_menu/", [
                ("落單按鈕", ".bean-mix-grid .btn-primary"),
            ]),
            ("http://localhost:8081/eshop/payment/fps/2807/", [
                ("FPS 主按鈕", "#fps-confirm-btn"),
                ("FPS 返回按鈕", ".bc-payment-actions a"),
            ]),
            ("http://localhost:8081/eshop/payment/cash/2807/", [
                ("Cash 主按鈕", ".bc-payment-actions button[type=submit]"),
                ("Cash 返回按鈕", ".bc-payment-actions a"),
            ]),
        ]

        for url, btns in pages:
            await send(msg("Page.navigate", {"url": url}))
            await asyncio.sleep(4.0)
            diag = await send(msg("Runtime.evaluate", {
                "expression": "(function(){var b=document.querySelectorAll('.calltoaction-btn');"
                              "return{url:location.href,calltoactionCount:b.length};})()",
                "returnByValue": True,
            }))
            print(f"\n===== {url} =====")
            print(f"  [診斷] {json.dumps(diag.get('result', {}).get('value', {}), ensure_ascii=False)}")
            for label, sel in btns:
                r = await send(msg("Runtime.evaluate", {"expression": btn_js(sel), "returnByValue": True}))
                v = r.get("result", {}).get("value", {})
                print(f"  [{label}] {json.dumps(v, ensure_ascii=False)}")

        try:
            urllib.request.urlopen("http://localhost:9222/json/close/" + tab["id"])
        except Exception:
            pass


if __name__ == "__main__":
    session_id_cache = get_session_cookie()
    asyncio.run(main())

