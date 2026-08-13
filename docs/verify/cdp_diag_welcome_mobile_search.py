#!/usr/bin/env python3
"""CDP 診斷：首頁 bc-welcome-panel 行動端文字 + bc-search hover 動畫時序"""
import asyncio
import json
import urllib.request

import websockets

WS = "http://localhost:9222/json/new?about:blank"


async def main():
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

        # 模擬 375px 行動端
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
        await send(msg("Page.navigate", {"url": "http://localhost:8081/"}))
        await asyncio.sleep(4.5)

        # ===== 問題 1：bc-welcome-panel 文字量測 =====
        panel_js = (
            "(function(){"
            "var out = { viewport: window.innerWidth };"
            "var panel = document.querySelector('.bc-welcome-panel');"
            "if (!panel) return { error: 'no panel', viewport: window.innerWidth };"
            "var pr = panel.getBoundingClientRect();"
            "out.panel = { left: Math.round(pr.left), right: Math.round(pr.right), w: Math.round(pr.width), h: Math.round(pr.height) };"
            "var info = panel.querySelector('.bc-welcome-info');"
            "var greeting = panel.querySelector('.bc-welcome-greeting');"
            "var points = panel.querySelector('.bc-welcome-points');"
            "var imgbox = panel.querySelector('.bc-welcome-imgbox');"
            "var lastOrder = panel.querySelector('.bc-last-order');"
            "function r(e, label){ if(!e) return null; var b = e.getBoundingClientRect(); var cs = getComputedStyle(e);"
            "return { label: label, left: Math.round(b.left), right: Math.round(b.right), top: Math.round(b.top), bottom: Math.round(b.bottom),"
            "w: Math.round(b.width), h: Math.round(b.height), fs: cs.fontSize, wrap: cs.whiteSpace, text: (e.textContent||'').slice(0,40) }; }"
            "out.info = r(info, 'info');"
            "out.greeting = r(greeting, 'greeting');"
            "out.points = r(points, 'points');"
            "out.imgbox = r(imgbox, 'imgbox');"
            "out.lastOrder = r(lastOrder, 'lastOrder');"
            "out.greetOverflow = info && greeting ? Math.round(greeting.getBoundingClientRect().right - info.getBoundingClientRect().right) : null;"
            "out.pointsOverflow = info && points ? Math.round(points.getBoundingClientRect().right - info.getBoundingClientRect().right) : null;"
            "out.panelOverflow = Math.round(pr.right - window.innerWidth);"
            "return out;"
            "})()"
        )
        r = await send(
            msg("Runtime.evaluate", {"expression": panel_js, "returnByValue": True})
        )
        print("===== 問題1：bc-welcome-panel（375px） =====")
        print(json.dumps(r.get("result", {}).get("value", {}), ensure_ascii=False, indent=2))

        # ===== 問題 2：bc-search hover 動畫時序 =====
        await send(
            msg(
                "Runtime.evaluate",
                {
                    "expression": "document.querySelector('.bc-search').scrollIntoView({block:'center'}); 'ok'",
                    "returnByValue": True,
                },
            )
        )
        await asyncio.sleep(1.5)

        poll_js = (
            "(function(){"
            "var link = document.querySelector('.bc-search-link');"
            "var img1 = document.querySelector('.bc-search-bg-img-01');"
            "return { class: link ? link.className : null, img1: img1 ? getComputedStyle(img1).transform : null };"
            "})()"
        )

        # 觸發 mouseenter
        await send(
            msg(
                "Runtime.evaluate",
                {
                    "expression": "document.querySelector('.bc-search-link').dispatchEvent(new MouseEvent('mouseenter', {bubbles:true})); 'ok'",
                    "returnByValue": True,
                },
            )
        )
        print("\n===== 問題2：bc-search mouseenter 後 class/transform 追蹤 =====")
        for i in range(6):
            await asyncio.sleep(0.5)
            r = await send(
                msg("Runtime.evaluate", {"expression": poll_js, "returnByValue": True})
            )
            v = r.get("result", {}).get("value", {})
            print(f"  +{i*0.5+0.5}s: class={v.get('class')!r} img1={v.get('img1')}")

        # 快速 hover 進出測試（模擬快速移入移出）
        rapid_js = (
            "(function(){"
            "var link = document.querySelector('.bc-search-link');"
            "var out = { steps: [] };"
            "link.dispatchEvent(new MouseEvent('mouseleave', { bubbles: true }));"
            "out.steps.push({ action: 'leave', class: link.className });"
            "link.dispatchEvent(new MouseEvent('mouseenter', { bubbles: true }));"
            "out.steps.push({ action: 'enter-again', class: link.className });"
            "return out;"
            "})()"
        )
        r = await send(
            msg("Runtime.evaluate", {"expression": rapid_js, "returnByValue": True})
        )
        print("\n===== 快速 hover 進出狀態 =====")
        print(json.dumps(r.get("result", {}).get("value", {}), ensure_ascii=False, indent=2))

        await asyncio.sleep(2)
        r = await send(
            msg("Runtime.evaluate", {"expression": poll_js, "returnByValue": True})
        )
        v = r.get("result", {}).get("value", {})
        print(f"  2s 後: class={v.get('class')!r} img1={v.get('img1')}")

        try:
            urllib.request.urlopen(f"http://localhost:9222/json/close/{tab['id']}")
        except Exception:
            pass


if __name__ == "__main__":
    asyncio.run(main())
