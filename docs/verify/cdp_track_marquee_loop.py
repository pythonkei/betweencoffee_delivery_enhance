#!/usr/bin/env python3
"""CDP 診斷：bc-marquee 迭代邊界（循環點）是否有跳動"""
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

        # 加速動畫週期並追蹤迭代邊界
        js_track = """
        (async function(){
          var mq = document.querySelector('.bc-marquee');
          var track = mq.querySelector('.bc-marquee__track');
          var items = mq.querySelectorAll('.bc-marquee__item');
          var r1 = items[0].getBoundingClientRect();
          var item_w = r1.width;
          // 加速週期 0.8s（位移 -item_w），方便捕捉邊界
          track.style.animationDuration = '0.8s';
          var samples = [];
          var t0 = performance.now();
          await new Promise(function(res){
            var n = 0;
            var iv = setInterval(function(){
              var cs = getComputedStyle(track);
              var m = cs.transform.match(/[\\d.\\-]+/g);
              var dx = m ? parseFloat(m[4]) : null;
              samples.push({ t: Math.round(performance.now()-t0), dx: dx });
              if (++n >= 45) { clearInterval(iv); res(); }
            }, 40);
          });
          track.style.animationDuration = '';
          return { item_w: item_w, samples: samples };
        })()
        """
        r = await send(msg("Runtime.evaluate", {"expression": js_track, "awaitPromise": True, "returnByValue": True}))
        data = r.get("result", {}).get("value", {})
        print("item_w:", data.get("item_w"))
        print("樣本序列（找迭代邊界：dx 由負跳回 0 附近）：")
        for s in (data.get("samples") or []):
            dx = s.get("dx")
            print(f"  t={s['t']:>5}ms  dx={dx}")

        # 追蹤 JS rAF 驅動的 transform：檢查整數化 + 模循環連續性
        js_track_js = """
        (async function(){
          var mq = document.querySelector('.bc-marquee');
          var track = mq.querySelector('.bc-marquee__track');
          var items = mq.querySelectorAll('.bc-marquee__item');
          var item_w = items[0].getBoundingClientRect().width;
          var out = { item_w: item_w };
          // 確認 JS 已關閉 CSS animation
          out.css_animation = getComputedStyle(track).animationName;
          var samples = [];
          var t0 = performance.now();
          await new Promise(function(res){
            var n = 0;
            var iv = setInterval(function(){
              var cs = getComputedStyle(track);
              var m = cs.transform.match(/[\\d.\\-]+/g);
              var dx = m ? parseFloat(m[4]) : null;
              samples.push({ t: Math.round(performance.now()-t0), dx: dx });
              if (++n >= 30) { clearInterval(iv); res(); }
            }, 50);
          });
          out.samples = samples;
          return out;
        })()
        """
        r = await send(msg("Runtime.evaluate", {"expression": js_track_js, "awaitPromise": True, "returnByValue": True}))
        data = r.get("result", {}).get("value", {})
        print("=== JS rAF 整數位移追蹤 ===")
        print("item_w:", data.get("item_w"), "| CSS animation:", data.get("css_animation"))
        dxs = [s.get("dx") for s in (data.get("samples") or []) if s.get("dx") is not None]
        print("位移序列:", dxs)
        # 檢查整數化
        all_int = all(abs(d - round(d)) < 0.001 for d in dxs)
        print("全部整數像素:", all_int)
        # 檢查單調遞減（含模循環跳回）
        steps = [dxs[i+1] - dxs[i] for i in range(len(dxs)-1)]
        normal_steps = [s for s in steps if s < 0]          # 正常負步進
        loop_jumps = [s for s in steps if s > 0]            # 模循環的正跳（應只出現一次或零次）
        print("負步進:", normal_steps[:10], "... 共", len(normal_steps))
        print("正跳（模循環）:", loop_jumps, "| 步進範圍:", min(steps), "~", max(steps))
        # 步進是否均勻（正常步進應是 -1 或 -0 交替，因 round）
        print("步進分布:", {round(s,2): steps.count(s) for s in set(round(x,2) for x in steps)})

        await send(msg("Page.close"))

asyncio.run(main())
