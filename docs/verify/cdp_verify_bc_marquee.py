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
          if (!mq) { out.error = '找不到 .bc-marquee'; return out; }
          var track = mq.querySelector('.bc-marquee__track');
          var items = mq.querySelectorAll('.bc-marquee__item');
          if (items.length !== 2) { out.item_error = 'item 數: ' + items.length; return out; }
          var r1 = items[0].getBoundingClientRect();
          var r2 = items[1].getBoundingClientRect();
          var rt = track.getBoundingClientRect();
          out.item1_w = Math.round(r1.width * 100) / 100;
          out.item2_w = Math.round(r2.width * 100) / 100;
          out.items_equal_width = r1.width === r2.width;
          out.track_w = Math.round(rt.width * 100) / 100;
          out.track_equals_2x_item = Math.abs(rt.width - 2 * r1.width) < 0.5;
          out.gap_between_items = Math.round((r2.left - (r1.left + r1.width)) * 100) / 100;
          var cs = getComputedStyle(track);
          out.animation_name = cs.animationName;
          out.animation_duration = cs.animationDuration;
          out.padding_item = getComputedStyle(items[0]).paddingLeft;
          // 連續性檢查：兩次取樣 transform 差值（應為平滑負增長，無跳動）
          out.transform_1 = cs.transform;
          return out;
        })()
        """
        # 連續性：兩次取樣 transform
        js_again = """
        (function(){
          var mq = document.querySelector('.bc-marquee');
          var track = mq ? mq.querySelector('.bc-marquee__track') : null;
          return track ? getComputedStyle(track).transform : 'none';
        })()
        """
        async def run_vp(w, h, m):
            await send(msg("Emulation.setDeviceMetricsOverride",
                           {"width": w, "height": h, "deviceScaleFactor": 1, "mobile": m}))
            await send(msg("Page.navigate", {"url": "http://localhost:8081/bean_menu/"}))
            await asyncio.sleep(4)
            r = await send(msg("Runtime.evaluate", {"expression": js_check, "returnByValue": True}))
            res = r.get("result", {}).get("value")
            # 兩次取樣 transform（間隔 2.5s，確認連續位移無跳動）
            await asyncio.sleep(2.5)
            r2 = await send(msg("Runtime.evaluate", {"expression": js_again, "returnByValue": True}))
            t1, t2 = (res.get('transform_1') or 'none'), r2.get("result", {}).get("value")
            res['transform_t2'] = t2
            res['transform_continuity'] = (t1 != 'none' and t1 != t2)
            return res

        for w, h, m in [(1280, 800, False), (375, 700, True)]:
            print(f"=== {w}px ===")
            print(json.dumps(await run_vp(w, h, m), ensure_ascii=False))

        await send(msg("Page.close"))

asyncio.run(main())
