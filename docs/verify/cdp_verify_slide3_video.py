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
          await new Promise(function(res){ setTimeout(res, 5000); });  // webm 8.3MB 需時間載入
          // 遍歷所有 video，找含 coffee_machine source 的
          var target = null;
          document.querySelectorAll('.home-slider video').forEach(function(v){
            v.querySelectorAll('source').forEach(function(s){
              if ((s.getAttribute('src')||'').indexOf('coffee_machine') !== -1) target = v;
            });
          });
          if (!target) { out.error = '找不到 coffee_machine 影片'; return out; }
          var srcs = [];
          target.querySelectorAll('source').forEach(function(s){ srcs.push(s.getAttribute('src')); });
          out.source_srcs = srcs;
          out.video_currentSrc = target.currentSrc;
          out.video_paused = target.paused;
          out.video_readyState = target.readyState;
          out.video_error = target.error ? (target.error.code + ':' + target.error.message) : null;
          out.video_duration = target.duration;
          out.is_coffee_machine = (target.currentSrc || '').indexOf('coffee_machine') !== -1;
          // 確認是第 3 個 slider（啡咖師的日常）
          var slide3 = target.closest('.slider-item');
          out.slide_text = (slide3.querySelector('.subheading')||{}).textContent || '';
          return out;
        })()
        """
        r = await send(msg("Runtime.evaluate", {"expression": js, "awaitPromise": True, "returnByValue": True}))
        print(json.dumps(r.get("result", {}).get("value"), ensure_ascii=False, indent=1))

        await send(msg("Page.close"))

asyncio.run(main())
