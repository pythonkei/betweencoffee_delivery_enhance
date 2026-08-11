#!/usr/bin/env python3
"""CDP 量測：bc-welcome-panel 高度（桌面/平板/手機）"""
import asyncio, json, urllib.request
import websockets

async def main():
    req = urllib.request.Request("http://localhost:9222/json/new?about:blank", method="PUT")
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

        js = """
        (function(){
          var p = document.querySelector('.bc-welcome-panel');
          if (!p) return { error: '找不到 .bc-welcome-panel' };
          var r = p.getBoundingClientRect();
          var cs = getComputedStyle(p);
          var avatar = p.querySelector('.bc-welcome-avatar');
          var imgbox = p.querySelector('.bc-welcome-imgbox');
          var img = p.querySelector('.bc-welcome-img');
          return {
            panel: { w: Math.round(r.width), h: Math.round(r.height), paddingTop: cs.paddingTop, paddingBottom: cs.paddingBottom, gap: cs.gap },
            avatar: avatar ? Math.round(avatar.getBoundingClientRect().height) : null,
            imgbox: imgbox ? Math.round(imgbox.getBoundingClientRect().height) : null,
            img: img ? { h: Math.round(img.getBoundingClientRect().height), top: getComputedStyle(img).top } : null,
            viewport: window.innerWidth
          };
        })()
        """
        js_fs = """
        (function(){
          var imgbox = document.querySelector('.bc-welcome-imgbox');
          var img = imgbox.querySelector('.bc-welcome-img');
          var lastOrder = imgbox.querySelector('.bc-last-order');
          var ib = imgbox.getBoundingClientRect();
          var im = img.getBoundingClientRect();
          var lo = lastOrder.getBoundingClientRect();
          function r(e, label){ return { label: label, left: Math.round(e.left), right: Math.round(e.right), centerX: Math.round(e.left + e.width/2), top: Math.round(e.top), bottom: Math.round(e.bottom), centerY: Math.round(e.top + e.height/2), w: Math.round(e.width), h: Math.round(e.height) }; }
          return {
            imgbox: r(ib, 'imgbox'),
            img: r(im, 'img'),
            lastOrder: r(lo, 'lastOrder'),
            centerX_diff_img_vs_text: Math.round((im.left + im.width/2) - (lo.left + lo.width/2)),
            img_bottom_to_text_top: Math.round(im.bottom - lo.top),
            viewport: window.innerWidth
          };
        })()
        """
        async def run_vp(w, h, m):
            await send(msg("Emulation.setDeviceMetricsOverride",
                           {"width": w, "height": h, "deviceScaleFactor": 1, "mobile": m}))
            await send(msg("Page.navigate", {"url": "http://localhost:8081/"}))
            await asyncio.sleep(4)
            r = await send(msg("Runtime.evaluate", {"expression": js, "returnByValue": True}))
            res = r.get("result", {}).get("value")
            r2 = await send(msg("Runtime.evaluate", {"expression": js_fs, "returnByValue": True}))
            res['align'] = r2.get("result", {}).get("value")
            return res

        for w, h, m in [(1280, 900, False), (768, 900, True), (375, 700, True)]:
            print(f"=== {w}px ===")
            print(json.dumps(await run_vp(w, h, m), ensure_ascii=False))

        await send(msg("Page.close"))

asyncio.run(main())
