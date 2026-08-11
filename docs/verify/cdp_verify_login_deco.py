#!/usr/bin/env python3
"""CDP 驗證：/accounts/login/ deco_01.svg 背景無抖動（無 noise_animation、無 stellar 視差）"""
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
        await send(msg("Page.navigate", {"url": "http://localhost:8081/accounts/login/"}))
        await asyncio.sleep(4)

        js = """
        (async function(){
          var out = {};
          var bg = document.querySelector('.svg-bg');
          if (!bg) return { error: '無 .svg-bg' };
          out.bg_class = bg.className;
          out.bg_attr = { stellar: bg.getAttribute('data-stellar-background-ratio') };
          out.bg_style = (bg.getAttribute('style') || '').slice(0, 80);
          var samples = [];
          await new Promise(function(res){
            var n = 0;
            var iv = setInterval(function(){
              var cs = getComputedStyle(bg);
              var r = bg.getBoundingClientRect();
              samples.push({ bp: cs.backgroundPosition, left: Math.round(r.left), top: Math.round(r.top), anim: cs.animationName, opacity: cs.opacity });
              if (++n >= 15) { clearInterval(iv); res(); }
            }, 120);
          });
          out.samples = samples;
          out.bp_set = Array.from(new Set(samples.map(s => s.bp)));
          out.left_set = Array.from(new Set(samples.map(s => s.left)));
          out.anim_set = Array.from(new Set(samples.map(s => s.anim)));
          out.stable = out.bp_set.length === 1 && out.left_set.length === 1 && out.anim_set.join('') === 'none';
          return out;
        })()
        """
        r = await send(msg("Runtime.evaluate", {"expression": js, "awaitPromise": True, "returnByValue": True}))
        data = r.get("result", {}).get("value", {})
        print(json.dumps(data, ensure_ascii=False, indent=1)[:1800])

        await send(msg("Page.close"))

asyncio.run(main())
