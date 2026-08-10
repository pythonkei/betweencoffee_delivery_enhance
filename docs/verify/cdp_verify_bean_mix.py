#!/usr/bin/env python3
"""CDP 驗證：bean_menu A+C 混合不對稱網格（375/768/1280px）"""
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
          var grid = document.querySelector('.bean-mix-grid');
          if (!grid) { out.error = '找不到 .bean-mix-grid'; return out; }
          var groups = grid.querySelectorAll(':scope > .bean-mix-group');
          out.group_count = groups.length;
          out.flip_groups = 0;
          out.details = [];
          for (var g=0; g<groups.length; g++) {
            var grp = groups[g];
            var isFlip = grp.classList.contains('bean-mix-flip');
            if (isFlip) out.flip_groups++;
            var main = grp.querySelector(':scope > .bean-mix-main');
            var subs = grp.querySelectorAll(':scope > .bean-mix-sub');
            var mcs = getComputedStyle(main);
            var mainRect = main.getBoundingClientRect();
            var entry = {
              group: g+1, flip: isFlip,
              main_gridColumn: mcs.gridColumn, main_gridRow: mcs.gridRow,
              main_x: Math.round(mainRect.left), main_w: Math.round(mainRect.width),
              main_name: (main.querySelector('h5')||{}).textContent || '',
              subs: []
            };
            for (var s=0; s<subs.length; s++) {
              var scs = getComputedStyle(subs[s]);
              var r = subs[s].getBoundingClientRect();
              entry.subs.push({
                n: s+1,
                gridColumn: scs.gridColumn, gridRow: scs.gridRow,
                transform: scs.transform,
                x: Math.round(r.left), y: Math.round(r.top),
                name: (subs[s].querySelector('h5')||{}).textContent || ''
              });
            }
            out.details.push(entry);
          }
          out.viewport_w = window.innerWidth;
          out.no_overflow = document.documentElement.scrollWidth <= window.innerWidth + 1;
          out.scrollWidth = document.documentElement.scrollWidth;
          return out;
        })()
        """
        def run(viewport):
            return asyncio.create_task(do_viewport(viewport, js_check))

        async def do_viewport(viewport, js):
            await send(msg("Emulation.setDeviceMetricsOverride",
                           {"width": viewport[0], "height": viewport[1], "deviceScaleFactor": 1, "mobile": viewport[2]}))
            await send(msg("Page.navigate", {"url": "http://localhost:8081/bean_menu/"}))
            await asyncio.sleep(3)
            r = await send(msg("Runtime.evaluate", {"expression": js, "returnByValue": True}))
            return r.get("result", {}).get("value")

        for vp in [(1280, 900, False), (768, 900, False), (375, 700, True)]:
            res = await do_viewport(vp, js_check)
            print(f"=== {vp[0]}px ===")
            print(json.dumps(res, ensure_ascii=False, indent=1))

        await send(msg("Page.close"))

asyncio.run(main())
