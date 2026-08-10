#!/usr/bin/env python3
"""CDP 驗證：首頁第 3 個 slider 影片更改為 coffee_machine.mp4"""
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
        await send(msg("Page.navigate", {"url": "http://localhost:8081/"}))
        await asyncio.sleep(4)

        # 切到第 3 格並檢查影片
        js = """
        (async function(){
          var out = {};
          var $sl = $('.home-slider');
          $sl.trigger('to.owl.carousel', [2, 0]);
          await new Promise(function(res){ setTimeout(res, 2000); });
          var active = $sl.find('.owl-item.active').find('.slider-item');
          out.slide_text = (active.find('.subheading').first().text() || '').trim();
          var video = active.find('video').get(0);
          if (!video) { out.error = '第3格無 video'; return out; }
          var srcs = [];
          video.querySelectorAll('source').forEach(function(s){ srcs.push(s.getAttribute('src')); });
          out.source_srcs = srcs;
          out.video_currentSrc = video.currentSrc;
          out.video_paused = video.paused;
          out.video_readyState = video.readyState;
          out.is_coffee_machine = (video.currentSrc || '').indexOf('coffee_machine.mp4') !== -1;
          return out;
        })()
        """
        r = await send(msg("Runtime.evaluate", {"expression": js, "awaitPromise": True, "returnByValue": True}))
        print(json.dumps(r.get("result", {}).get("value"), ensure_ascii=False, indent=1))

        await send(msg("Page.close"))

asyncio.run(main())
