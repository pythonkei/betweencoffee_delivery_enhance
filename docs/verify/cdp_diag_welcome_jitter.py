#!/usr/bin/env python3
"""CDP 診斷：bc-welcome-greeting/points 初始載入時文字大小是否抖動"""
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
        await send(msg("Page.navigate", {"url": "http://localhost:8081/?no=1"}))
        # 載入後每 80ms 追蹤 2 秒
        js = """
        (async function(){
          var out = { samples: [] };
          await new Promise(function(res){
            var n = 0;
            var iv = setInterval(function(){
              var g = document.querySelector('.bc-welcome-greeting');
              var p = document.querySelector('.bc-welcome-points');
              if (g && p) {
                var gcs = getComputedStyle(g), pcs = getComputedStyle(p), hcs = getComputedStyle(document.documentElement);
                out.samples.push({
                  t: (n*80)+'ms',
                  html_fs: hcs.fontSize,
                  g_fs: gcs.fontSize, g_transform: gcs.transform, g_opacity: gcs.opacity, g_anim: gcs.animationName,
                  p_fs: pcs.fontSize, p_transform: pcs.transform
                });
              }
              if (++n >= 25) { clearInterval(iv); res(); }
            }, 80);
          });
          return out;
        })()
        """
        await asyncio.sleep(0.5)  # 等 DOM 就緒（動畫若存在也會捕捉到早期）
        r = await send(msg("Runtime.evaluate", {"expression": js, "awaitPromise": True, "returnByValue": True}))
        data = r.get("result", {}).get("value", {})
        for s in data.get("samples", []):
            print(s)
        # 判斷
        fs_set = set(s.get('g_fs') for s in data.get('samples', []))
        print("greeting font-size 集合:", fs_set, "→", "抖動!" if len(fs_set) > 1 else "穩定")
        tf_set = set(s.get('g_transform') for s in data.get('samples', []))
        print("greeting transform 集合:", tf_set)

        await send(msg("Page.close"))

asyncio.run(main())
