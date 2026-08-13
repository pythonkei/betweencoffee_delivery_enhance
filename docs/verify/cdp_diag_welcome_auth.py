#!/usr/bin/env python3
"""CDP 診斷：首頁 bc-welcome-panel 行動端文字（登入狀態，透過 session cookie 注入）"""
import asyncio
import json
import os
import sys
import urllib.request

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
    user = get_user_model().objects.get(id=58)
    c.force_login(user)
    resp = c.get("/")
    for k, v in c.cookies.items():
        if k == "sessionid":
            return v.value
    return None


async def main():
    session_id = session_id_cache  # noqa: F821
    print("取得 sessionid:", (session_id or "無")[:20])

    req = urllib.request.Request(WS, method="PUT")
    tab = json.loads(urllib.request.urlopen(req).read())
    ws_url = tab["webSocketDebuggerUrl"]

    async with websockets.connect(ws_url) as ws:
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
        await send(msg("Network.enable"))
        await send(
            msg(
                "Emulation.setDeviceMetricsOverride",
                {
                    "width": 375,
                    "height": 812,
                    "deviceScaleFactor": 2,
                    "mobile": True,
                },
            )
        )

        # 注入 session cookie
        await send(
            msg(
                "Network.setCookie",
                {
                    "name": "sessionid",
                    "value": session_id,
                    "domain": "localhost",
                    "path": "/",
                },
            )
        )
        await send(msg("Page.navigate", {"url": "http://localhost:8081/"}))
        await asyncio.sleep(4.5)

        panel_js = (
            "(function(){"
            "var out = { viewport: window.innerWidth };"
            "var panel = document.querySelector('.bc-welcome-panel');"
            "if (!panel) return { error: 'no panel', viewport: window.innerWidth };"
            "var pr = panel.getBoundingClientRect();"
            "out.panel = { left: Math.round(pr.left), right: Math.round(pr.right), w: Math.round(pr.width), h: Math.round(pr.height) };"
            "var avatar = panel.querySelector('.bc-welcome-avatar');"
            "var info = panel.querySelector('.bc-welcome-info');"
            "var greeting = panel.querySelector('.bc-welcome-greeting');"
            "var points = panel.querySelector('.bc-welcome-points');"
            "var imgbox = panel.querySelector('.bc-welcome-imgbox');"
            "var lastOrder = panel.querySelector('.bc-last-order');"
            "function r(e, label){ if(!e) return null; var b = e.getBoundingClientRect(); var cs = getComputedStyle(e);"
            "return { label: label, left: Math.round(b.left), right: Math.round(b.right), top: Math.round(b.top), bottom: Math.round(b.bottom),"
            "w: Math.round(b.width), h: Math.round(b.height), fs: cs.fontSize, lh: cs.lineHeight, wrap: cs.whiteSpace, text: (e.textContent||'').replace(/\\s+/g,' ').trim().slice(0,50) }; }"
            "out.avatar = r(avatar, 'avatar');"
            "out.info = r(info, 'info');"
            "out.greeting = r(greeting, 'greeting');"
            "out.points = r(points, 'points');"
            "out.lastOrder = r(lastOrder, 'lastOrder');"
            "out.isAuthed = !!document.querySelector('.bc-welcome-points .bc-welcome-link');"
            "out.greetChildCount = greeting ? greeting.children.length : 0;"
            "out.greetLines = greeting ? Math.round(greeting.getBoundingClientRect().height / parseFloat(getComputedStyle(greeting).fontSize)) : null;"
            "out.pointsLines = points ? Math.round(points.getBoundingClientRect().height / parseFloat(getComputedStyle(points).fontSize)) : null;"
            "out.panelInnerRight = avatar ? Math.round(avatar.getBoundingClientRect().right) : null;"
            "return out;"
            "})()"
        )
        r = await send(
            msg("Runtime.evaluate", {"expression": panel_js, "returnByValue": True})
        )
        print("===== bc-welcome-panel（375px 登入狀態） =====")
        print(json.dumps(r.get("result", {}).get("value", {}), ensure_ascii=False, indent=2))

        try:
            urllib.request.urlopen(f"http://localhost:9222/json/close/{tab['id']}")
        except Exception:
            pass


if __name__ == "__main__":
    session_id_cache = get_session_cookie()
    asyncio.run(main())
