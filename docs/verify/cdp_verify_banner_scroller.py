#!/usr/bin/env python3
"""CDP 驗證：bean_menu banner 內複製的 .scroller-box 水平遮罩動畫"""
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

        js_check = """
        (function(){
          var out = {};
          var banner = document.querySelector('.ftco-subpage-banner');
          var sc = banner ? banner.querySelector('.scroller') : null;
          var scBox = banner ? banner.querySelector('.scroller-box') : null;
          if (!sc) { out.error = 'banner 內找不到 .scroller'; return out; }
          out.data_animated = sc.getAttribute('data-animated');  // JS 應設為 'true'
          out.inner_li_count = sc.querySelectorAll('.scroller__inner li').length;  // JS 複製後應為 4
          var cs = getComputedStyle(sc.querySelector('.scroller__inner'));
          out.animation_name = cs.animationName;
          out.animation_duration = cs.animationDuration;
          // banner 與 scroller 的幾何
          var bRect = banner.getBoundingClientRect();
          var sRect = sc.getBoundingClientRect();
          out.banner_rect = { w: Math.round(bRect.width), h: Math.round(bRect.height) };
          out.scroller_rect = { w: Math.round(sRect.width), h: Math.round(sRect.height) };
          out.scroller_box_rect = scBox ? (function(){ var r = scBox.getBoundingClientRect(); return { w: Math.round(r.width), h: Math.round(r.height) }; })() : null;
          // 溢出檢查（banner 是否被 scroller 撐破）
          out.banner_bottom = Math.round(bRect.bottom);
          out.viewport_h = window.innerHeight;
          out.no_horizontal_overflow = document.documentElement.scrollWidth <= window.innerWidth + 1;
          // footer scroller 對照
          var footerSc = document.querySelector('footer .scroller');
          out.footer_scroller_exists = !!footerSc;
          out.footer_animated = footerSc ? footerSc.getAttribute('data-animated') : null;
          // 動畫實際位移（取 transform）
          out.inner_transform = cs.transform;
          return out;
        })()
        """
        async def run_vp(w, h, m):
            await send(msg("Emulation.setDeviceMetricsOverride",
                           {"width": w, "height": h, "deviceScaleFactor": 1, "mobile": m}))
            await send(msg("Page.navigate", {"url": "http://localhost:8081/bean_menu/"}))
            await asyncio.sleep(4)
            r = await send(msg("Runtime.evaluate", {"expression": js_check, "returnByValue": True}))
            return r.get("result", {}).get("value")

        for w, h, m in [(1280, 800, False), (375, 700, True)]:
            print(f"=== {w}px ===")
            print(json.dumps(await run_vp(w, h, m), ensure_ascii=False))

        await send(msg("Page.close"))

asyncio.run(main())
