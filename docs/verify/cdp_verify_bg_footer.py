#!/usr/bin/env python3
"""CDP 驗證：#bc-bg-footer（/about/ 專屬品牌 footer）的釘牌 logo 與頁面範圍。

檢查項目
  1. 頁面範圍：僅 /about/ 有 #bc-bg-footer；/coffee_menu/ 沒有（且用 .ftco-footer）。
  2. 釘牌（.footer-logo-cell）：無品牌金底色（background 透明）、幾何尺寸。
  3. 白色線稿：deco 一律白（deco_*.svg 檔案內 root fill:#ffffff），
     <img> 不再套用 .is-invert（filter 為 none）。
  4. 不溢出：documentElement.scrollWidth <= innerWidth + 1。
  5. 點擊輪播：點釘牌 → 作用中項目 index 前進（mod 5），點 5 次回到原點。
多個 viewport：桌面 1280×800 / 平板 768×1024 / 行動 390×844，並各存一張截圖。
"""
import asyncio, base64, json, urllib.request
import websockets

BASE = "http://localhost:8081"
ROOT = "/home/kei/Desktop/betweencoffee_delivery_enhance"

MEASURE_JS = r"""
(function(){
  var out = {};
  var root = document.getElementById('bc-bg-footer');
  out.has_bg_footer = !!root;
  out.has_ftco_footer = !!document.querySelector('.ftco-footer');
  out.doc_scroll_w = document.documentElement.scrollWidth;
  out.inner_w = window.innerWidth;
  out.no_h_overflow = out.doc_scroll_w <= out.inner_w + 1;
  if (!root) return out;

  var cell = root.querySelector('[data-footer-logo="wrap"]');
  out.cell_found = !!cell;
  if (cell) {
    var r = cell.getBoundingClientRect();
    out.cell = { w: Math.round(r.width), h: Math.round(r.height) };
    var cs = getComputedStyle(cell);
    out.cell_bg = cs.backgroundColor;
    out.cell_bg_transparent = cs.backgroundColor === 'rgba(0, 0, 0, 0)';
    out.cell_cursor = cs.cursor;
  }
  var items = root.querySelectorAll('[data-footer-logo="item"]');
  out.item_count = items.length;
  var activeIdx = -1;
  for (var i = 0; i < items.length; i++) {
    if (getComputedStyle(items[i]).display !== 'none') { activeIdx = i; break; }
  }
  out.active_index = activeIdx;
  if (activeIdx >= 0) {
    var img = items[activeIdx].querySelector('img');
    out.active_img_class = img ? img.className : null;
    out.active_img_src = img ? img.getAttribute('src') : null;
    out.active_has_is_invert = img ? img.classList.contains('is-invert') : false;
    out.active_img_filter = img ? getComputedStyle(img).filter : null;
    out.active_img_filter_none = img ? (getComputedStyle(img).filter === 'none') : null;
  }
  out.item_bg_first = getComputedStyle(items[0]).backgroundColor;
  out.item_bg_first_transparent = getComputedStyle(items[0]).backgroundColor === 'rgba(0, 0, 0, 0)';
  return out;
})()
"""


async def main():
    req = urllib.request.Request("http://localhost:9222/json/new?about:blank", method="PUT")
    tab = json.loads(urllib.request.urlopen(req).read())
    ws_url = tab["webSocketDebuggerUrl"]
    async with websockets.connect(ws_url, max_size=200 * 1024 * 1024) as ws:
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

        async def evaljs(expr):
            r = await send(msg("Runtime.evaluate", {"expression": expr, "returnByValue": True}))
            return r.get("result", {}).get("value")

        async def shot(name):
            rr = await evaljs("(function(){var e=document.getElementById('bc-bg-footer');"
                              "if(!e)return null;var r=e.getBoundingClientRect();"
                              "return {x:r.left+window.scrollX,y:r.top+window.scrollY,w:r.width,h:r.height};})()")
            if not rr:
                return
            res = await send(msg("Page.captureScreenshot", {
                "format": "png", "captureBeyondViewport": True,
                "clip": {"x": rr["x"], "y": rr["y"], "width": rr["w"], "height": rr["h"], "scale": 1}}))
            data = res.get("data")
            if data:
                with open(f"{ROOT}/_verify_bgfooter_{name}.png", "wb") as f:
                    f.write(base64.b64decode(data))
                print(f"   shot -> _verify_bgfooter_{name}.png")

        # ---- 1. 頁面範圍 ----
        print("=== 頁面範圍 (scoping) ===")
        for path in ["/about/", "/coffee_menu/"]:
            await send(msg("Emulation.setDeviceMetricsOverride",
                           {"width": 1280, "height": 800, "deviceScaleFactor": 1, "mobile": False}))
            await send(msg("Page.navigate", {"url": BASE + path}))
            await asyncio.sleep(3)
            r = await evaljs(MEASURE_JS)
            print(f"  {path}: bg_footer={r.get('has_bg_footer')} ftco_footer={r.get('has_ftco_footer')}")

        # ---- 2/3/4. 各 viewport 量測 ----
        for w, h, m_, name in [(1280, 800, False, "desktop"), (768, 1024, False, "tablet"), (390, 844, True, "mobile")]:
            print(f"=== viewport {w}x{h} ({name}) ===")
            await send(msg("Emulation.setDeviceMetricsOverride",
                           {"width": w, "height": h, "deviceScaleFactor": 1, "mobile": m_}))
            await send(msg("Page.navigate", {"url": BASE + "/about/"}))
            await asyncio.sleep(4)
            await evaljs("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(1)
            r = await evaljs(MEASURE_JS)
            print("  " + json.dumps(r, ensure_ascii=False))
            checks = {
                "無品牌金底（cell_bg 透明）": r.get("cell_bg_transparent") is True,
                "deco 無 .is-invert": r.get("active_has_is_invert") is False,
                "img filter none（白 fill 呈現）": r.get("active_img_filter_none") is True,
                "item 無品牌金底": r.get("item_bg_first_transparent") is True,
                "水平不溢出": r.get("no_h_overflow") is True,
            }
            for k, v in checks.items():
                print(("  PASS " if v else "  FAIL ") + k)
            await shot(name)

        # ---- 5. 點擊輪播（行動寬度） ----
        print("=== 點擊輪播 (click cycle) @ 390x844 ===")
        await send(msg("Emulation.setDeviceMetricsOverride",
                       {"width": 390, "height": 844, "deviceScaleFactor": 1, "mobile": True}))
        await send(msg("Page.navigate", {"url": BASE + "/about/"}))
        await asyncio.sleep(4)
        idx_js = ("(function(){var items=document.querySelectorAll('[data-footer-logo=\"item\"]');"
                  "for(var i=0;i<items.length;i++){if(getComputedStyle(items[i]).display!=='none')return i;}return -1;})()")
        click_js = ("(function(){var w=document.querySelector('[data-footer-logo=\"wrap\"]');w.click();"
                    "var items=document.querySelectorAll('[data-footer-logo=\"item\"]');"
                    "for(var i=0;i<items.length;i++){if(getComputedStyle(items[i]).display!=='none')return i;}return -1;})()")
        seq = [await evaljs(idx_js)]
        for _ in range(5):
            seq.append(await evaljs(click_js))
        print("  active index 序列 (初始 + 點5次):", seq)
        ok_cycle = seq[1:] == [(seq[0] + k + 1) % 5 for k in range(5)]
        print("  輪播順序正確:", ok_cycle)

        await send(msg("Page.close"))

asyncio.run(main())
