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
          var mq = document.querySelector('.bc-marquee');
          if (!mq) { out.error = '找不到 .bc-marquee'; return out; }
          var track = mq.querySelector('.bc-marquee__track');
          var items = mq.querySelectorAll('.bc-marquee__item');
          var r1 = items[0].getBoundingClientRect();
          var r2 = items[1].getBoundingClientRect();
          var rt = track.getBoundingClientRect();
          var mcs = getComputedStyle(mq);
          var cs = getComputedStyle(track);
          out.item1_w = r1.width;
          out.item2_w = r2.width;
          out.item_equal_exact = r1.width === r2.width;
          out.gap = r2.left - (r1.left + r1.width);
          out.track_2x = Math.abs(rt.width - 2 * r1.width) < 0.001;
          out.letter_spacing = mcs.letterSpacing;      // 應為 normal/0px
          out.will_change = cs.willChange;              // 應為 auto
          out.track_display = cs.display;               // 應為 flex
          out.track_width_style = cs.width;
          out.anim = cs.animationName + ' ' + cs.animationDuration;
          out.transform = cs.transform;
          return out;
        })()
        """

        async def run_vp(w, h, m):
            await send(msg("Emulation.setDeviceMetricsOverride",
                           {"width": w, "height": h, "deviceScaleFactor": 1, "mobile": m}))
            await send(msg("Page.navigate", {"url": "http://localhost:8081/bean_menu/"}))
            await asyncio.sleep(4)
            r = await send(msg("Runtime.evaluate", {"expression": js_check, "returnByValue": True}))
            res = r.get("result", {}).get("value")
            # 連續性：4 次取樣 transform（每 800ms），檢查平滑負增長
            samples = []
            for _ in range(4):
                await asyncio.sleep(0.8)
                r2 = await send(msg("Runtime.evaluate",
                                    {"expression": "getComputedStyle(document.querySelector('.bc-marquee__track')).transform",
                                     "returnByValue": True}))
                samples.append(r2.get("result", {}).get("value"))
            res['transform_samples'] = samples
            # 解析位移值並檢查單調性
            import re
            vals = []
            for s in samples:
                mnum = re.search(r'\[1,\s*([-\d.]+)\)', s or '')
                if not mnum:
                    mnum = re.search(r',\s*(-[\d.]+)\s*[,\)]', s or '')
                if mnum:
                    vals.append(float(mnum.group(1)))
            res['dx_list'] = vals
            res['monotonic'] = all(vals[i] < vals[i-1] for i in range(1, len(vals))) if len(vals) > 1 else 'n/a'
            return res

        for w, h, m in [(1280, 800, False), (375, 700, True)]:
            print(f"=== {w}px ===")
            print(json.dumps(await run_vp(w, h, m), ensure_ascii=False))

        await send(msg("Page.close"))

asyncio.run(main())
