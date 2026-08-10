#!/usr/bin/env python3
"""CDP 驗證：行動端 375px 下第 3 個 home-slider 橫幅的影片容器計算樣式"""
import asyncio, json, urllib.request
import websockets

WS = "http://localhost:9222/json/new?about:blank"

async def main():
    # 開新 tab（需 PUT）
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

        # 設定行動端 viewport
        await send(msg("Emulation.setDeviceMetricsOverride",
                       {"width": 375, "height": 700, "deviceScaleFactor": 1, "mobile": True}))
        # 載入首頁
        await send(msg("Page.enable"))
        await send(msg("Runtime.enable"))
        await send(msg("Page.navigate", {"url": "http://localhost:8081/"}))
        await asyncio.sleep(4)  # 等 owl 初始化 + is-loaded

        # 切到第 3 個 slide（loop:true 時 owl 會有 clone，用 data 方法 to index 2 對應原始第 3 格）
        js_to3 = """
        (function(){
          var $sl = $('.home-slider');
          if (!$sl.length || !$sl.data('owl.carousel')) return 'owl not ready';
          $sl.trigger('to.owl.carousel', [2, 0]);
          return 'ok';
        })()
        """
        r = await send(msg("Runtime.evaluate", {"expression": js_to3, "returnByValue": True}))
        print("切到第3格:", r.get("result", {}).get("value"))
        await asyncio.sleep(3.5)  # 等切換動畫(700ms) + play() 執行

        # 檢查 active slide 的影片播放狀態
        js_play_check = """
        (function(){
          var $sl = $('.home-slider');
          var active = $sl.find('.owl-item.active').find('.slider-item');
          var video = active.find('video').get(0);
          var out = {
            active_found: active.length > 0,
            active_has_bc_video: active.find('.bc-banner-video').length > 0,
            slide_text: (active.find('.subheading').first().text() || '').trim()
          };
          if (video) {
            out.video = { paused: video.paused, readyState: video.readyState, currentSrc: video.currentSrc };
            // 若 paused 且資料已載入，嘗試 play 確認可播放
            if (video.paused && video.readyState >= 2) {
              video.play().then(function(){ out.after_play = { paused: video.paused }; })
                .catch(function(e){ out.after_play = { error: String(e) }; });
            }
          } else { out.video = '無 video'; }
          return out;
        })()
        """
        r = await send(msg("Runtime.evaluate", {"expression": js_play_check, "returnByValue": True}))
        print("active 播放檢查:", json.dumps(r.get("result", {}).get("value"), ensure_ascii=False))
        await asyncio.sleep(1)
        r = await send(msg("Runtime.evaluate", {"expression": js_play_check, "returnByValue": True}))
        print("active 播放檢查(再1秒):", json.dumps(r.get("result", {}).get("value"), ensure_ascii=False))

        js_check = """
        (function(){
          var out = {};
          var items = document.querySelectorAll('.home-slider .slider-item');
          out['slider_count'] = items.length;
          // 找第 3 個 slide（最後一個含 .bc-banner-video 且含 .overlay 的）
          var slide3 = null;
          for (var i=items.length-1;i>=0;i--){
            if (items[i].querySelector('.bc-banner-video') && items[i].querySelector('.overlay')) { slide3 = items[i]; break; }
          }
          if (!slide3) { out['error'] = '找不到第3格'; return out; }
          var vc = slide3.querySelector('.bc-banner-video');
          var video = slide3.querySelector('video');
          var vcs = getComputedStyle(vc), ivcs = getComputedStyle(video);
          var rect = vc.getBoundingClientRect();
          var s3rect = slide3.getBoundingClientRect();
          out['slide3_bg_image'] = getComputedStyle(slide3).backgroundImage;
          out['video_container'] = {
            display: vcs.display, position: vcs.position,
            width: vcs.width, height: vcs.height,
            borderRadius: vcs.borderRadius,  // 必須無橢圓（0px）
            animationName: vcs.animationName  // 必須非 morph-3
          };
          out['container_rect'] = { w: Math.round(rect.width), h: Math.round(rect.height) };
          out['slide_rect'] = { w: Math.round(s3rect.width), h: Math.round(s3rect.height) };
          out['container_fills_slide'] = Math.round(rect.width) === Math.round(s3rect.width) && Math.round(rect.height) === Math.round(s3rect.height);
          out['video'] = {
            display: ivcs.display, objectFit: ivcs.objectFit,
            src: video.currentSrc || '未載入', paused: video.paused, readyState: video.readyState
          };
          out['has_ellipse'] = vcs.borderRadius !== '0px';
          out['overlay'] = slide3.querySelector('.overlay') ? '存在' : '不存在';
          return out;
        })()
        """
        r = await send(msg("Runtime.evaluate", {"expression": js_check, "returnByValue": True}))
        print("行動端375px:", json.dumps(r.get("result", {}).get("value"), ensure_ascii=False))

        # ===== 桌面版驗證 =====
        await send(msg("Emulation.setDeviceMetricsOverride",
                       {"width": 1280, "height": 800, "deviceScaleFactor": 1, "mobile": False}))
        await send(msg("Page.reload", {"ignoreCache": True}))
        await asyncio.sleep(4)
        await send(msg("Runtime.evaluate", {"expression": js_to3, "returnByValue": True}))
        await asyncio.sleep(1.5)
        r = await send(msg("Runtime.evaluate", {"expression": js_check, "returnByValue": True}))
        print("桌面1280px:", json.dumps(r.get("result", {}).get("value"), ensure_ascii=False))

        # 關閉 tab
        await send(msg("Page.close"))

asyncio.run(main())
