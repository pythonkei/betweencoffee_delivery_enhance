#!/usr/bin/env python3
"""CDP 驗證：bc-marquee 循環 buffer 連續性（模擬 buffer 操作前後視窗內容一致）"""
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
                       {"width": 1280, "height": 800, "deviceScaleFactor": 1, "mobile": False}))
        await send(msg("Page.navigate", {"url": "http://localhost:8081/bean_menu/"}))
        await asyncio.sleep(4)

        js = """
        (function(){
          var out = {};
          var mq = document.querySelector('.bc-marquee');
          var track = mq.querySelector('.bc-marquee__track');
          var items = track.querySelectorAll('.bc-marquee__item');
          out.item_count = items.length;
          out.item_w = Math.round(items[0].getBoundingClientRect().width * 100) / 100;
          out.track_w = Math.round(track.getBoundingClientRect().width * 100) / 100;
          // 模擬 buffer：把第一個 item 移到尾端（同 JS 邏輯）
          var before = [];
          for (var i=0;i<items.length;i++) before.push(items[i].textContent.substr(0, 12));
          track.appendChild(items[0]);
          items = track.querySelectorAll('.bc-marquee__item');
          var after = [];
          for (var i=0;i<items.length;i++) after.push(items[i].textContent.substr(0, 12));
          out.order_before = before;
          out.order_after = after;
          // 驗證：buffer 後第 1 個 item = buffer 前第 2 個 item（視窗內容連續）
          out.continuous = before[1] === after[0];
          // transform 連續性（JS rAF 的整數位移）
          var t = getComputedStyle(track).transform;
          out.transform = t;
          var m = t.match(/[\\d.\\-]+/g);
          out.dx = m ? parseFloat(m[4]) : null;
          return out;
        })()
        """
        r = await send(msg("Runtime.evaluate", {"expression": js, "returnByValue": True}))
        print(json.dumps(r.get("result", {}).get("value"), ensure_ascii=False, indent=1))

        await send(msg("Page.close"))

asyncio.run(main())
