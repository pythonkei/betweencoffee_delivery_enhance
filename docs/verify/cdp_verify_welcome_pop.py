#!/usr/bin/env python3
"""CDP 驗證：bc-welcome-greeting/points 初始縮小→放大動畫"""
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
        await send(msg("Emulation.setDeviceMetricsOverride",
                       {"width": 1280, "height": 900, "deviceScaleFactor": 1, "mobile": False}))

        # 重新載入並立即抓取動畫早期狀態（scale < 1）+ 最終狀態
        js = """
        (async function(){
          var out = {};
          var g = document.querySelector('.bc-welcome-greeting');
          var p = document.querySelector('.bc-welcome-points');
          out.found = { greeting: !!g, points: !!p };
          if (!g || !p) return out;
          var gcs = getComputedStyle(g), pcs = getComputedStyle(p);
          out.animation = { g_name: gcs.animationName, g_dur: gcs.animationDuration, g_timing: gcs.animationTimingFunction,
                            p_name: pcs.animationName };
          // 動畫早期（約 100ms）抓 scale
          await new Promise(function(res){ setTimeout(res, 100); });
          var m1 = getComputedStyle(g).transform.match(/[\\d.\\-]+/g);
          out.scale_early = m1 ? parseFloat(m1[0]) : null;  // 第一幀 scale 約 0.5
          out.opacity_early = getComputedStyle(g).opacity;
          // 動畫結束（> 600ms）抓 scale
          await new Promise(function(res){ setTimeout(res, 700); });
          var m2 = getComputedStyle(g).transform.match(/[\\d.\\-]+/g);
          out.scale_end = m2 ? parseFloat(m2[0]) : null;  // 應為 1
          out.opacity_end = getComputedStyle(g).opacity;
          return out;
        })()
        """
        await send(msg("Page.navigate", {"url": "http://localhost:8081/"}))
        await asyncio.sleep(5)   # 等完整載入（含 owl / 大字體）
        r = await send(msg("Runtime.evaluate", {"expression": js, "awaitPromise": True, "returnByValue": True}))
        print(json.dumps(r.get("result", {}).get("value"), ensure_ascii=False, indent=1))

        await send(msg("Page.close"))

asyncio.run(main())
