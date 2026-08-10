#!/usr/bin/env python3
"""CDP 驗證：第 1 個 slider 的 coffee_border_01.svg 增大 40% + 白色"""
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
          var items = document.querySelectorAll('.home-slider .slider-item');
          if (!items.length) { out.error = 'slider-item 不存在'; return out; }
          out.total_items = items.length;
          // 用 img src 識別：coffee_border_01.svg = 第 1 個原始 slide；owl_title_bg_01.svg = 第 3 個原始 slide
          var s1 = null, s3 = null;
          for (var i=0;i<items.length;i++){
            var imgs = items[i].querySelectorAll('.noise-img img');
            for (var j=0;j<imgs.length;j++){
              var src = imgs[j].getAttribute('src') || '';
              if (src.indexOf('coffee_border_01') !== -1) s1 = items[i];
              if (src.indexOf('owl_title_bg_01') !== -1) s3 = items[i];
            }
          }
          function info(el) {
            if (!el) return null;
            var n = el.querySelector('.noise-img');
            if (!n) return { found: false };
            var r = n.getBoundingClientRect();
            var cs = getComputedStyle(n);
            return { found: true, w: Math.round(r.width), h: Math.round(r.height), width: cs.width, minWidth: cs.minWidth, maxWidth: cs.maxWidth };
          }
          out.slider1_noise = info(s1);
          out.slider3_noise = info(s3);
          // 抓 SVG 內容確認白色 fill
          var img1 = s1 ? s1.querySelector('.noise-img img') : null;
          out.slider1_img_src = img1 ? img1.getAttribute('src') : '?';
          if (img1) {
            var xhr = new XMLHttpRequest();
            xhr.open('GET', img1.src, false);
            xhr.send();
            var body = xhr.responseText || '';
            out.svg_white = body.indexOf('fill="#ffffff"') !== -1;
            out.svg_size = body.length;
          }
          out.viewport_w = window.innerWidth;
          out.no_overflow = document.documentElement.scrollWidth <= window.innerWidth + 1;
          return out;
        })()
        """

        async def run_vp(w, h, mobile):
            await send(msg("Emulation.setDeviceMetricsOverride",
                           {"width": w, "height": h, "deviceScaleFactor": 1, "mobile": mobile}))
            await send(msg("Page.navigate", {"url": "http://localhost:8081/"}))
            await asyncio.sleep(3.5)
            r = await send(msg("Runtime.evaluate", {"expression": js_check, "returnByValue": True}))
            return r.get("result", {}).get("value")

        for w, h, m in [(1280, 800, False), (768, 700, True), (375, 700, True), (320, 640, True)]:
            res = await run_vp(w, h, m)
            print(f"=== {w}px ===")
            print(json.dumps(res, ensure_ascii=False))

        await send(msg("Page.close"))

asyncio.run(main())
