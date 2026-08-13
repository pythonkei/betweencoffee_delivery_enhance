#!/usr/bin/env python3
"""CDP 驗證：bc-welcome-panel 多斷點（375/768/1280px 登入）"""
import asyncio, json, os, sys, urllib.request
import websockets

sys.path.insert(0, "/home/kei/Desktop/betweencoffee_delivery_enhance")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "betweencoffee_delivery.settings")
import django
django.setup()
from django.test import Client
from django.contrib.auth import get_user_model

WS = "http://localhost:9222/json/new?about:blank"


def get_session_cookie():
    c = Client()
    c.force_login(get_user_model().objects.get(id=58))
    c.get("/")
    return next((v.value for k, v in c.cookies.items() if k == "sessionid"), None)


MEASURE = (
    "(function(){var out={viewport:window.innerWidth};"
    "var p=document.querySelector('.bc-welcome-panel');if(!p)return{error:'no panel'};"
    "var info=p.querySelector('.bc-welcome-info');var g=p.querySelector('.bc-welcome-greeting');"
    "var pts=p.querySelector('.bc-welcome-points');var im=p.querySelector('.bc-welcome-img');"
    "var lo=p.querySelector('.bc-last-order');var pr=p.getBoundingClientRect();"
    "function r(e){if(!e)return null;var b=e.getBoundingClientRect();return{l:Math.round(b.left),r:Math.round(b.right),t:Math.round(b.top),b:Math.round(b.bottom),w:Math.round(b.width),h:Math.round(b.height)};}"
    "var ir=r(info),gr=r(g),pp=r(pts),imr=r(im),lor=r(lo);"
    "out.info=ir;out.greeting=gr;out.points=pp;out.img=imr;out.lastOrder=lor;"
    "out.greetLines=gr?Math.round(gr.h/parseFloat(getComputedStyle(g).fontSize)):null;"
    "out.pointsLines=pp?Math.round(pp.h/parseFloat(getComputedStyle(pts).fontSize)):null;"
    "out.imgLastOverlap=(imr&&lor)?(imr.b-lor.t):null;"
    "out.panelRightOverflow=Math.round(pr.right-window.innerWidth);"
    "out.text=(g?g.textContent.replace(/\\s+/g,' ').trim():'')+' | '+(pts?pts.textContent.replace(/\\s+/g,' ').trim():'');"
    "return out;})()"
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
        ok = True

        for width, label in ((375, "手機"), (768, "平板"), (1280, "桌面")):
            await send(msg("Emulation.setDeviceMetricsOverride",
                           {"width": width, "height": 900, "deviceScaleFactor": 2, "mobile": width <= 768}))
            if sid:
                await send(msg("Network.setCookie",
                               {"name": "sessionid", "value": sid, "domain": "localhost", "path": "/"}))
            await send(msg("Page.navigate", {"url": "http://localhost:8081/"}))
            await asyncio.sleep(4.0)
            r = await send(msg("Runtime.evaluate", {"expression": MEASURE, "returnByValue": True}))
            v = r.get("result", {}).get("value", {})
            print(f"=== bc-welcome-panel {label} ({width}px) ===")
            print(json.dumps(v, ensure_ascii=False, indent=2))
            if v.get("greetLines") and v["greetLines"] > 2:
                print(f"  ❌ greeting {v['greetLines']} 行"); ok = False
            if v.get("pointsLines") and v["pointsLines"] > 2:
                print(f"  ❌ points {v['pointsLines']} 行"); ok = False
            if v.get("panelRightOverflow", 0) > 0:
                print(f"  ❌ panel 右溢 {v['panelRightOverflow']}px"); ok = False
            if v.get("imgLastOverlap") and v["imgLastOverlap"] > 6:
                print(f"  ⚠️  圖片/文字重疊 {v['imgLastOverlap']}px")

        print("\n" + ("✅ 多斷點驗證通過" if ok else "❌ 有失敗"))
        try:
            urllib.request.urlopen(f"http://localhost:9222/json/close/{tab['id']}")
        except Exception:
            pass
        return ok


if __name__ == "__main__":
    session_id_cache = get_session_cookie()
    exit(0 if asyncio.run(main()) else 1)
