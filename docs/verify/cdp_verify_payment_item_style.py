#!/usr/bin/env python3
"""CDP 驗證：付款頁 .payment-item-fps/cash 樣式搬移後視覺不變"""
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


MEASURE = (
    "(function(){"
    "var el = document.querySelector('.payment-item-fps') || document.querySelector('.payment-item-cash');"
    "if(!el)return{found:false,url:location.href};"
    "var cs=getComputedStyle(el);var r=el.getBoundingClientRect();"
    "return{found:true,cls:el.className,"
    "bg:cs.backgroundColor,border:cs.borderTopWidth+' '+cs.borderTopStyle+' '+cs.borderTopColor,"
    "radius:cs.borderRadius,overflow:cs.overflow,"
    "marginBottom:cs.marginBottom,inlineStyle:el.getAttribute('style')};})()"
)


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

        for url in ("http://localhost:8081/eshop/payment/fps/2807/",
                    "http://localhost:8081/eshop/payment/cash/2807/"):
            await send(msg("Page.navigate", {"url": url}))
            await asyncio.sleep(4.0)
            r = await send(msg("Runtime.evaluate", {"expression": MEASURE, "returnByValue": True}))
            v = r.get("result", {}).get("value", {})
            print(f"\n===== {url.split('/')[4].upper()} =====")
            print(json.dumps(v, ensure_ascii=False, indent=2))

        try:
            urllib.request.urlopen("http://localhost:9222/json/close/" + tab["id"])
        except Exception:
            pass


if __name__ == "__main__":
    session_id_cache = get_session_cookie()
    asyncio.run(main())
