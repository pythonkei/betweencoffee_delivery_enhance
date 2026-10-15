#!/usr/bin/env python3
"""CDP 驗證：#bc-bg-footer（品牌 footer）的釘牌 logo 與頁面範圍。

2026-10-09（使用者指示）：首頁 / 的 footer 由 base.html 靜態 ftco 頁尾改為
與 /about/ 共用的 #bc-bg-footer（同一 partials/bc_bg_footer.html）。
本腳本因此把 / 一併納入斷言（文字層 + 瀏覽器層）。

2026-10-09（同日稍後，使用者指示）：首頁的 #bc-bg-footer 再由頁尾移到**最上方**當第一個 hero
（GUNTE hero 移到它下方）。置頂版 markup ＝ partials/bc_hero.html，與 footer 版逐字相同，
只把最外層 <footer class="footer"> 換成 <div class="footer">：bc-yama-header.js 用
document.querySelector('footer')（DOM 第一個 footer 元素）當「footer 交會」觀察目標，
置頂模組若仍用 footer 標籤，一載入就把 tax-nav／header-bot 藏起來。
→ / 的 footer 標籤數由 1 改為 0（本腳本同步調整；/ 也因此沒有頁尾 <footer> 元素，
DOM footer 元素數改由 J 系列（cdp_verify_footer_scroller.py）與本檔 scoping 一併驗）。

檢查項目
  0. markup（文字層，不經瀏覽器）：/ 與 /about/ 的 HTML 內
     id="bc-bg-footer" 恰好 1 個、無 ftco 頁尾字樣、
     且引用 bc-bg-footer.css / bc-bg-footer.js；</footer> 個數 / = 0、/about/ = 1；
     /coffee_menu/ 反向（仍用 ftco 頁尾，</footer> = 1）。
  1. 頁面範圍：/ 與 /about/ 有 #bc-bg-footer 且不重複；
     DOM footer 元素數 = 0（/）、1（/about/）、1（/coffee_menu/）；
     /coffee_menu/ 沒有 #bc-bg-footer（且仍用 .ftco-footer）。
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
  out.bg_footer_count = document.querySelectorAll('#bc-bg-footer').length;
  out.ftco_count = document.querySelectorAll('.ftco-footer').length;
  out.footer_tag_count = document.querySelectorAll('footer').length;
  out.doc_scroll_w = document.documentElement.scrollWidth;
  out.inner_w = window.innerWidth;
  out.no_h_overflow = out.doc_scroll_w <= out.inner_w + 1;
  if (!root) return out;

  // 2026-10-14：首頁照片格（#bc-clock-photos）已改為環形照片列 —— 不再有
  // [data-footer-logo="wrap"/"item"]（該 hook 僅剩 /about/ 真頁尾的 5 格 deco 輪播在用），
  // 故釘牌改用 .footer-logo-cell（兩頁都有；/about/ 仍靠 wrap、語意不變）。
  var cell = root.querySelector('[data-footer-logo="wrap"]')
      || root.querySelector('.footer-logo-cell');
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
  // ⚠ 首頁（環形照片列）的 items 為 0 → 不可再無條件 getComputedStyle(items[0])
  //   （原寫法會拋錯，讓整支腳本在 scoping 段崩潰）；/about/ 仍是 5 格 deco 輪播。
  out.item_bg_first = items.length ? getComputedStyle(items[0]).backgroundColor : null;
  out.item_bg_first_transparent = items.length
      ? getComputedStyle(items[0]).backgroundColor === 'rgba(0, 0, 0, 0)' : null;
  /* 2026-10-14：首頁的環形照片列（筆數；幾何/同步細節由
     docs/verify/cdp_verify_hero_coffee_photos.py 專責驗） */
  out.ring_count = root.querySelectorAll('#bc-clock-photos .hero_hand_item').length;
  return out;
})()
"""


def fetch(path):
    """取得未經瀏覽器處理的伺服器端 HTML（模板渲染結果）。"""
    with urllib.request.urlopen(BASE + path, timeout=20) as r:
        return r.read().decode("utf-8", "replace")


def markup_checks():
    """文字層斷言：不需瀏覽器即可驗證 footer 置換是否真的生效（最快抓到模板問題）。

    注意：Django 在 --noreload 下會快取模板，改 .html 後務必重啟 8081，
    否則這裡看到的是開機當時的舊渲染。
    """
    print("=== markup (文字層) ===")
    # path, 期望 id="bc-bg-footer" 次數, 期望 ftco 頁尾次數比較式, 期望 </footer> 次數
    spec = [
        # 2026-10-09：/ 的 #bc-bg-footer 已由頁尾移到最上方當 hero，最外層標籤由 footer 改為 div
        # （見 partials/bc_hero.html）→ / 不再有 </footer>；/about/ 仍是頁尾版 = 1；
        # /coffee_menu/ 走 base.html 的 .ftco-footer = 1。
        ("/", 1, "==0", 0),
        ("/about/", 1, "==0", 1),
        ("/coffee_menu/", 0, ">=1", 1),
    ]
    all_ok = True
    for path, want_bg, ftco_mode, want_footer in spec:
        html = fetch(path)
        got_bg = html.count('id="bc-bg-footer"')
        got_ftco = html.count("ftco-footer")
        got_footer = html.count("</footer>")
        ok_bg = got_bg == want_bg
        ok_ftco = (got_ftco == 0) if ftco_mode == "==0" else (got_ftco >= 1)
        print(f"  {path}: id=\"bc-bg-footer\"={got_bg} ftco-footer={got_ftco} </footer>={got_footer}")
        results = {
            f"{path} id=\"bc-bg-footer\" 次數 == {want_bg}": ok_bg,
            f"{path} ftco-footer 次數 {ftco_mode}（got {got_ftco}）": ok_ftco,
            f"{path} </footer> 個數 == {want_footer}（got {got_footer}）": got_footer == want_footer,
        }
        if want_bg:
            for asset in ("css/bc-bg-footer.css", "js/bc-bg-footer.js"):
                results[f"{path} 引用 {asset}"] = asset in html
        for k, v in results.items():
            all_ok = all_ok and v
            print(("  PASS " if v else "  FAIL ") + k)
    print("  markup 總結:", "PASS" if all_ok else "FAIL")
    return all_ok



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

        # ---- 0. markup 文字層 ----
        markup_checks()

        # ---- 1. 頁面範圍（2026-10-09 起含首頁 /） ----
        print("=== 頁面範圍 (scoping) ===")
        # path, 期望 has_bg_footer, 期望 has_ftco_footer, 期望 DOM footer 元素數
        # 2026-10-09：/ 的模組已改為 div（置頂 hero）→ footer 元素 0；
        #             /about/ 仍為 footer 標籤 = 1；/coffee_menu/ base.html ftco = 1。
        scoping = [("/", True, False, 0), ("/about/", True, False, 1),
                   ("/coffee_menu/", False, True, 1)]
        for path, want_bg, want_ftco, want_footer in scoping:
            await send(msg("Emulation.setDeviceMetricsOverride",
                           {"width": 1280, "height": 800, "deviceScaleFactor": 1, "mobile": False}))
            await send(msg("Page.navigate", {"url": BASE + path}))
            await asyncio.sleep(3)
            r = await evaljs(MEASURE_JS)
            print(f"  {path}: bg_footer={r.get('has_bg_footer')} ftco_footer={r.get('has_ftco_footer')} "
                  f"bg_id_count={r.get('bg_footer_count')} ftco_dom_count={r.get('ftco_count')} "
                  f"footer_tags={r.get('footer_tag_count')}")
            checks = {
                f"{path} #bc-bg-footer 存在 == {want_bg}": bool(r.get("has_bg_footer")) is want_bg,
                f"{path} .ftco-footer 存在 == {want_ftco}": bool(r.get("has_ftco_footer")) is want_ftco,
                f"{path} #bc-bg-footer 不重複（<= {1 if want_bg else 0}）":
                    (r.get("bg_footer_count") or 0) <= (1 if want_bg else 0),
            }
            checks[f"{path} DOM footer 元素數 == {want_footer}"
                   f"（got {r.get('footer_tag_count')}）"] = r.get("footer_tag_count") == want_footer
            for k, v in checks.items():
                print(("  PASS " if v else "  FAIL ") + k)

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
