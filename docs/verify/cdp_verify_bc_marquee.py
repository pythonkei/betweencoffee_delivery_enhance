#!/usr/bin/env python3
"""CDP 驗證：bean_menu banner 內 .bc-marquee 水平跑馬燈（取代 scroller-box）"""
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
          var mq = banner ? banner.querySelector('.bc-marquee') : null;
          var oldScroller = banner ? banner.querySelector('.scroller-box') : null;
          out.banner_scroller_removed = oldScroller === null;
          if (!mq) { out.error = 'banner 內找不到 .bc-marquee'; return out; }
          var track = mq.querySelector('.bc-marquee__track');
          var cs = getComputedStyle(track);
          var mcs = getComputedStyle(mq);
          out.marquee = {
            font_family: mcs.fontFamily,
            font_size: mcs.fontSize,
            color: mcs.color,
            padding_block: mcs.paddingTop + ' / ' + mcs.paddingBottom
          };
          out.animation_name = cs.animationName;
          out.animation_duration = cs.animationDuration;
          out.item_count = mq.querySelectorAll('.bc-marquee__item').length;
          out.track_transform = cs.transform;
          // banner 幾何
          var bRect = banner.getBoundingClientRect();
          var mRect = mq.getBoundingClientRect();
          out.banner_rect = { w: Math.round(bRect.width), h: Math.round(bRect.height) };
          out.marquee_rect = { w: Math.round(mRect.width), h: Math.round(mRect.height) };
          out.no_horizontal_overflow = document.documentElement.scrollWidth <= window.innerWidth + 1;
          // footer scroller 對照
          out.footer_scroller = document.querySelector('footer .scroller-box') ? '存在' : '不存在';
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
