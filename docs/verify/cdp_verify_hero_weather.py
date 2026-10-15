#!/usr/bin/env python3
"""CDP 驗證：首頁 hero 的 #bc-clock 內新增「about 頁 navbar 天氣/時鐘元件」（在 { 之上、+30%），
以及照片列每張照片下方的「咖啡名稱 ＋ highlight」。

改動背景（2026-10-14，使用者指示）
  1. templates/.../partials/bc_hero.html
     · #bc-clock 內、{ 之前新增 <div id="bc-clock-weather" class="bc-clock-weather"
       data-reveal="clip-down"> ＋ 與 nav.html:33-48 逐字相同的 .weather（自帶 .weather--visible）。
     · 照片格 7 筆（2026-10-14 稍後再改為 GUNTE hero 的環形照片列縮小版 ——
       .hero_hand / .hero_hand_item ＋ 一組 7 筆「名稱/highlight」，只有 -current 顯示）。
  2. static/css/bc-weather.css
     · 幾何規則由 `#ftco-navbar .weather` 擴為 `#ftco-navbar .weather, #bc-bg-footer .weather`，
       所有尺寸改為 calc(原值 * var(--wc-scale, 1))（先例＝bc-reviews.css 的 --rv-scale）；
       navbar 專屬（visibility 開關、Order 按鈕對齊的 translateX、≤991px height:100%）
       與 hero 專屬（height:auto）維持各自前綴。
  3. static/js/bc-weather.js
     · 滑動距離由硬寫 80px 改為逐實例量 .view 寬（slideDist）；抽出 fillLocalDate 於 main() 立即填日期。
  4. static/js/bc-weather.js 的載入條件（base.html）about → about ＋ index。
  5. templates/.../index.html <style>
     · #bc-clock-weather{grid-area:1/1/2/2;align-self:start;justify-self:center}、
       ≥992px 把 #bc-clock-brace-open 釘回 1/1/2/2（否則自動置位會整列跑版）、
       .weather{--wc-scale:1.3}；
     · .footer-logo-caption 字級與顏色（bc-series.css 只載入 about 頁，故本頁自帶同值宣告）；
       2026-10-14 稍後：照片格改為環形照片列（見 docs/verify/cdp_verify_hero_coffee_photos.py），
       高度改掛 .footer-logo-list（照片區）＋ .bc-ring-caption 7 筆文字（只顯示一筆）
       ⇒ 兩者相加仍等於改動前的 .footer-logo-item 高度。
       ⚠ 2026-10-15（使用者指示「桌機（≥992px）咖啡照片放大到 1440 時 336×480」）：
       ≥992px 的 .footer-logo-list 高改為 480vw/ratio、.footer-logo-cell 上下內距歸零
       ⇒ 照片區高度與 cell 內距**不再等於改動前**（這是刻意的）；≤991px 逐值不變。
       本檔下方 F4 的期望值已同步改為 4.80 * w / 14.4（見 expected_img_h()）。

改動前基準（同腳本量的「before」，2026-10-14，改動前原始碼；供下方斷言對照）
  viewport      clock 高   { 的 y  欄數/照片位置            照片 img 高
  1440x900      356.00     410.4   8 欄；photos x544 w336.25 276.00
  1280x800      316.42     365.0   同上                     245.33
  992x900       245.22     423.0   同上                     190.13
  991x900       574.92     399.0   9 欄；photos x349 w278.28 453.89
  768x1024      445.53     473.0   同上                     351.75
  480x900       278.47     426.0   同上                     219.84
  390x844       226.25     402.0   同上                     178.63
  ⚠ 2026-10-15「桌機咖啡照片放大到 1440 時 336×480」⇒ 上表 ≥992px 三列的「照片 img 高」
    已改為 1440 = 480.00、1280 = 426.67、992 = 330.67（＝480vw/ratio；改動前分別是
    276.00 / 245.33 / 190.13）；其餘欄位（clock 高、`{` 的 y、欄數）與 ≤991px 四列
    逐值不變。F4 的期望值已改為 4.80 * w / 14.4（見 expected_img_h()）。

檢查項目（A–F 每個 viewport 各一輪；G 為 /about/ 反向守門）
  A. 結構：#bc-clock 的第一個子項是 #bc-clock-weather，其內恰 1 顆 .weather（含
     .weather--visible / -font_en / -color_white），且 .view / .clock / .icon /
     .temperature / .date / .border 六件齊全（與 navbar 那顆同構）。
  B. 幾何：
     B1 grid-area 1/1/2/2、align-self start、justify-self center。
     B2 與另外 7 個時鐘子項「0 重疊」（矩形相交檢查）。
     B3 未超出視口左緣與時鐘列右緣（≤575px 時天氣 49.4px 比欄 1 約 29px 寬，
        置中後左側會略微溢出時鐘列左緣約 10px，仍在視口內且不產生水平溢出）。
     B4 在 { 之上（wrap.bottom < brace.top）。
     B5 無水平溢出（documentElement.scrollWidth <= innerWidth + 1）。
     B6 時鐘列未跑版：欄數、各子項落在基準欄位（`{`=1、`15`=2、第一個 `:`=3、
        照片=4–5（≥992）/4–6（≤991）、第二個 `:`、`19`、`}` 依序），且天氣中心
        與欄 1 中心對齊（±2px）。數字／標點只驗中心落在該欄——其字寬可大於
        minmax(0,1fr) 的欄寬（991px 的「15」寬 106px、欄寬 72.6px）而置中溢出，
        這是改動前就有的設計；照片列則驗整塊落在該欄區間內。
  C. +30%：--wc-scale == 1.3；.view 寬 = navbar .view 寬 × 1.3（±0.1）且等於
     104（≥992）/ 49.4（≤991，±0.06）；clock .value / temperature .value / unit /
     date 的 font-size 亦為 navbar 對應值的 1.3 倍（±1%）。
  D. 內容填充：時鐘為 HH:MM（與 navbar 那顆一致）、month/day/weekday 非空、
     year 有值但 computed display:none、溫度為數字、icon <img> 存在且 naturalWidth > 0。
  E. 首頁 navbar 那顆不受影響：visibility hidden、.view 寬 80（≥992）/38（≤991，
     皆未縮放）、仍被填充。
  F. 照片格（2026-10-14 改版：GUNTE hero 環形照片列縮小版 ＋ 單一「當前咖啡」文字）：
     7 個 .hero_hand_item（每筆 alt 非空）＋ [data-bc-ring-caption] 內 7 筆
     [data-bc-ring-caption-item]，恰 1 筆 -current、name/highlight 非空、且與環的 -current
     同索引（顯示中的 name == 該筆 img alt）；文字區高度 = --bc-hero-caption-h（±1px）；
     照片區（.footer-logo-list）高度 = ≥992px 480vw/ratio（@1440 = 480.00）／
     ≤991px 180vw/ratio（＝改動前值，未動）（皆 ±1px）；
     首頁已無舊輪播 hook（data-footer-logo=item）；font-size 為 16/12（≥992）、13/10（768–991）、
     11/9（≤767）；highlight 為品牌金 rgb(196, 155, 99)；name 為 Josefin Sans ＋ uppercase ＋ 白字。
  G. /about/ 反向守門：navbar 那顆仍 visible、未縮放（--wc-scale 1、view 80、仍被填充）；
     about 的真頁尾 #bc-bg-footer 內 0 顆 .weather、無 #bc-clock-weather；
     時鐘列仍為 8 欄、`{` 的 x/寬與改動前一致。

多個 viewport：1440x900 / 1280x800 / 992x900 / 991x900 / 768x1024 / 480x900 / 390x844，
各存一張「時鐘區」視窗截圖（viewport-only）。
用法：站台須在 http://127.0.0.1:8081 跑、CDP 瀏覽器須在 9222（見 CDP_SETUP.md）。
"""
import asyncio
import base64
import json
import re
import urllib.request

import websockets

BASE = "http://localhost:8081"
ROOT = "/home/kei/Desktop/betweencoffee_delivery_enhance"
CDP = "http://localhost:9222"

# 照片高度基準（= bc-bg-footer.css 的 `180vw / scale-ratio`，僅剩 ≤991px 在用的值）
SCALE_DESKTOP, SCALE_SHARED = 14.4, 3.93


def expected_img_h(w):
    """照片區（.footer-logo-list）高度：≥992px 為 `calc(480vw / 14.4)`
    （2026-10-15 使用者指示「桌機咖啡照片放大到 1440 時 336×480」；改動前為 276vw/14.4）、
    ≤991px 為 `calc(180vw / 3.93)`（未動）。
    → ≥992px = 4.80 * viewportWidth、≤991px = 1.80 * viewportWidth。"""
    return (4.80 * w / SCALE_DESKTOP) if w >= 992 else (1.80 * w / SCALE_SHARED)

MEASURE_JS = r"""
(function(){
  var out = {};
  var r = function(e){
    if (!e) return null;
    var b = e.getBoundingClientRect();
    return { x: Math.round(b.left * 100) / 100, y: Math.round(b.top * 100) / 100,
             w: Math.round(b.width * 100) / 100, h: Math.round(b.height * 100) / 100,
             right: Math.round(b.right * 100) / 100,
             bottom: Math.round(b.bottom * 100) / 100 };
  };
  var clock = document.getElementById('bc-clock');
  out.clock_found = !!clock;
  if (!clock) return out;
  var cs = getComputedStyle(clock);
  out.clock = r(clock);
  out.cols = cs.gridTemplateColumns.split(/\s+/).map(parseFloat);
  out.gap = parseFloat(cs.columnGap) || 0;

  /* ---- A 結構：天氣元件 ---- */
  var wrap = document.getElementById('bc-clock-weather');
  out.wrap_found = !!wrap;
  out.wrap_is_first = !!wrap && clock.children[0] === wrap;
  out.wrap_count = clock.querySelectorAll('#bc-clock-weather').length;
  if (wrap) {
    var cw = getComputedStyle(wrap);
    out.wrap = { rect: r(wrap), area: cw.gridArea, align: cw.alignSelf,
                 justify: cw.justifySelf, vis: cw.visibility,
                 reveal: wrap.getAttribute('data-reveal') };
    var ws = wrap.querySelectorAll('.weather');
    out.w_count = ws.length;
    var we = ws[0];
    if (we) {
      var cwe = getComputedStyle(we);
      var q = function(sel){ return we.querySelector(sel); };
      out.w = { rect: r(we), scale: cwe.getPropertyValue('--wc-scale').trim(),
                height: cwe.height, cls: we.className, vis: cwe.visibility,
                parts: ['view', 'clock', 'icon', 'temperature', 'date', 'border']
                  .map(function(k){ return we.querySelector('.' + k) ? 1 : 0; }),
                view_w: +q('.view').getBoundingClientRect().width.toFixed(2),
                clock_val: q('.clock .value').textContent,
                clock_val_fs: parseFloat(getComputedStyle(q('.clock .value')).fontSize),
                temp_val: q('.temperature .value').textContent,
                temp_fs: parseFloat(getComputedStyle(q('.temperature .value')).fontSize),
                unit_fs: parseFloat(getComputedStyle(q('.temperature .unit')).fontSize),
                date_fs: parseFloat(getComputedStyle(q('.date')).fontSize),
                month: q('.month').textContent, day: q('.day').textContent,
                year: q('.year').textContent,
                year_disp: getComputedStyle(q('.year')).display,
                weekday: q('.weekday').textContent };
      var im = q('.icon img');
      out.img = { exists: !!im, nw: im ? im.naturalWidth : 0, nh: im ? im.naturalHeight : 0 };
    }
  }

  /* ---- B 幾何：與 7 個時鐘子項的重疊 + 欄位 ---- */
  var kids = Array.prototype.slice.call(clock.children)
      .filter(function(k){ return k !== wrap; });
  out.kids = kids.map(function(k){
    return { id: k.id || k.tagName, area: getComputedStyle(k).gridArea, rect: r(k) };
  });
  if (wrap) {
    var wr = wrap.getBoundingClientRect();
    out.overlaps = kids.filter(function(k){
      var b = k.getBoundingClientRect();
      return b.width > 0 && b.height > 0 && b.left < wr.right && b.right > wr.left
          && b.top < wr.bottom && b.bottom > wr.top;
    }).map(function(k){ return k.id || k.tagName; });
  }
  var bo = document.getElementById('bc-clock-brace-open');
  out.brace = r(bo);

  /* ---- E navbar 那顆 ---- */
  var nw = document.querySelector('#ftco-navbar .weather');
  if (nw) {
    var cn = getComputedStyle(nw);
    var nq = function(sel){ return nw.querySelector(sel); };
    out.nav = { rect: r(nw), vis: cn.visibility,
                scale: cn.getPropertyValue('--wc-scale').trim(),
                view_w: +nq('.view').getBoundingClientRect().width.toFixed(2),
                clock_val: nq('.clock .value').textContent,
                month: nq('.month').textContent, day: nq('.day').textContent,
                weekday: nq('.weekday').textContent,
                year_disp: getComputedStyle(nq('.year')).display,
                temp_val: nq('.temperature .value').textContent,
                clock_val_fs: parseFloat(getComputedStyle(nq('.clock .value')).fontSize),
                temp_fs: parseFloat(getComputedStyle(nq('.temperature .value')).fontSize),
                unit_fs: parseFloat(getComputedStyle(nq('.temperature .unit')).fontSize),
                date_fs: parseFloat(getComputedStyle(nq('.date')).fontSize),
                img_nw: (nq('.icon img') || {}).naturalWidth || 0 };
  }

  /* ---- F 照片格（2026-10-14 改版：環形照片列 ＋ 單一「當前咖啡」文字） ----
     照片格不再是「7 格輪播、每格一組名稱/highlight」，而是 GUNTE hero 的環形照片列
     （7 個 .hero_hand_item）＋ 一組 7 筆的名稱/highlight（只有 -current 那筆顯示）。
     故 F 改驗：環形筆數/alt、文字 7 筆且恰 1 筆顯示、該筆與環的 -current 同索引、
     文字高度＝--bc-hero-caption-h、照片區高度＝改動前照片高度、字級/顏色斷點。 */
  var ringItems = Array.prototype.slice.call(
      document.querySelectorAll('#bc-clock-photos .hero_hand_item'));
  out.ring_count = ringItems.length;
  out.ring_alts = ringItems.map(function(el){
    var im = el.querySelector('img');
    return im ? (im.getAttribute('alt') || '') : null;
  });
  out.ring_cur = (function(){
    var k = -1;
    ringItems.forEach(function(el, i){ if (el.classList.contains('-current')) k = i; });
    return k;
  })();
  var caps = Array.prototype.slice.call(
      document.querySelectorAll('#bc-clock-photos [data-bc-ring-caption-item]'));
  out.caps = caps.map(function(el){
    var nm = el.querySelector('.bc-series-caption-name');
    var hl = el.querySelector('.bc-series-caption-highlight');
    var cnm = nm ? getComputedStyle(nm) : null, chl = hl ? getComputedStyle(hl) : null;
    return { cur: el.classList.contains('-current'),
             name: nm ? nm.textContent : null, hl: hl ? hl.textContent : null,
             name_fs: cnm ? parseFloat(cnm.fontSize) : 0,
             hl_fs: chl ? parseFloat(chl.fontSize) : 0,
             hl_color: chl ? chl.color : null,
             name_ff: cnm ? cnm.fontFamily : null,
             name_tt: cnm ? cnm.textTransform : null,
             name_color: cnm ? cnm.color : null };
  });
  out.caps_cur = (function(){
    var k = -1;
    caps.forEach(function(el, i){ if (el.classList.contains('-current')) k = i; });
    return k;
  })();
  out.cap_vis = caps.filter(function(el){ return el.classList.contains('-current'); }).length;
  out.cap_h = (function(){
    var c = document.querySelector('#bc-clock-photos .footer-logo-caption');
    return c ? +c.getBoundingClientRect().height.toFixed(2) : 0;
  })();
  out.photo_h = (function(){
    var a = document.querySelector('#bc-clock-photos .footer-logo-list');
    return a ? +a.getBoundingClientRect().height.toFixed(2) : 0;
  })();
  out.legacy_items = document.querySelectorAll(
      '#bc-clock-photos [data-footer-logo="item"]').length;
  var root = document.getElementById('bc-bg-footer');
  out.cap_h_var = root
      ? getComputedStyle(root).getPropertyValue('--bc-hero-caption-h').trim() : '';
  out.doc_scroll_w = document.documentElement.scrollWidth;
  out.inner_w = window.innerWidth;
  out.wrap_left_ok = wrap ? wrap.getBoundingClientRect().left >= 0 : false;
  return out;
})()
"""

# /about/ 反向守門
ABOUT_JS = r"""
(function(){
  var out = {};
  var nw = document.querySelector('#ftco-navbar .weather');
  if (nw) {
    var cn = getComputedStyle(nw);
    out.nav = { vis: cn.visibility, scale: cn.getPropertyValue('--wc-scale').trim(),
                view_w: +nw.querySelector('.view').getBoundingClientRect().width.toFixed(2),
                clock_val: nw.querySelector('.clock .value').textContent,
                temp_val: nw.querySelector('.temperature .value').textContent,
                month: nw.querySelector('.month').textContent,
                weekday: nw.querySelector('.weekday').textContent };
  }
  var root = document.getElementById('bc-bg-footer');
  out.footer_found = !!root;
  out.footer_weather = root ? root.querySelectorAll('.weather').length : -1;
  out.footer_wrap = document.getElementById('bc-clock-weather') ? 1 : 0;
  var clock = document.getElementById('bc-clock');
  if (clock) {
    out.cols = getComputedStyle(clock).gridTemplateColumns.split(/\s+/).length;
    var bo = document.getElementById('bc-clock-brace-open');
    var b = bo.getBoundingClientRect();
    out.brace = { x: Math.round(b.left * 100) / 100, w: Math.round(b.width * 100) / 100 };
  }
  return out;
})()
"""




def check(label, ok, detail=""):
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}{(' -> ' + str(detail)) if detail != '' else ''}")
    return bool(ok)


def col_bounds(clock, cols, gap, i):
    """第 i 欄（1-based）的左右界（由 grid 起點＋欄寬＋間隔推算）。"""
    left = clock["x"]
    for k in range(i - 1):
        left += cols[k] + gap
    return left, left + cols[i - 1]


async def main():
    req = urllib.request.Request(f"{CDP}/json/new?about:blank", method="PUT")
    tab = json.loads(urllib.request.urlopen(req).read())
    ws_url = tab["webSocketDebuggerUrl"]
    failures = []

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
        await send(msg("Page.setCacheDisabled", {"cacheDisabled": True}))

        async def evaljs(expr):
            r = await send(msg("Runtime.evaluate",
                               {"expression": expr, "returnByValue": True}))
            res = r.get("result", {})
            if res.get("subtype") == "error":
                print("   JS error:", res.get("description"))
            return res.get("value")

        async def goto(url):
            await send(msg("Page.navigate", {"url": url}))
            for _ in range(60):
                await asyncio.sleep(0.25)
                if await evaljs("document.readyState === 'complete' && location.href === "
                                + json.dumps(url)):
                    break
            await asyncio.sleep(1.6)

        async def set_viewport(w, h, mobile=False):
            await send(msg("Emulation.setDeviceMetricsOverride",
                           {"width": w, "height": h, "deviceScaleFactor": 1, "mobile": mobile}))
            await asyncio.sleep(0.4)

        async def shot(name):
            # 2026-10-14：本機 CDP 的 Page.captureScreenshot 偶爾會卡死（等不到 frame、永不回應；
            # 見 CDP_SETUP.md 的踩雷段）。截圖只是視覺證據、不參與斷言 ⇒ 包 20s 逾時，逾時就跳過，
            # 不讓整支腳本卡在單張截圖上（此前實測會在 1280 這一張無限等待）。
            try:
                res = await asyncio.wait_for(
                    send(msg("Page.captureScreenshot", {"format": "png"})), 20)
            except asyncio.TimeoutError:
                print(f"   shot -> SKIP（captureScreenshot 逾時 20s：{name}）")
                return
            data = res.get("data")
            if data:
                path = f"{ROOT}/_verify_hero_weather_{name}.png"
                with open(path, "wb") as f:
                    f.write(base64.b64decode(data))
                print(f"   shot -> {path}")


        for w, h, mobile, name in ((1440, 900, False, "1440"), (1280, 800, False, "1280"),
                                   (992, 900, False, "992"), (991, 900, False, "991"),
                                   (768, 1024, False, "768"), (480, 900, True, "480"),
                                   (390, 844, True, "390")):
            await set_viewport(w, h, mobile)
            await goto(f"{BASE}/")
            await evaljs("(function(){var c=document.getElementById('bc-clock');"
                         "if(c)c.scrollIntoView({block:'center'});})()")
            await asyncio.sleep(1.4)
            m = await evaljs(MEASURE_JS) or {}
            print(f"\n=== 首頁 hero #bc-clock 天氣元件 {w}x{h} ({name}) ===")
            if not m.get("clock_found"):
                failures.append(check("A0 #bc-clock 存在", False))
                continue

            # ---------- A 結構 ----------
            failures.append(check("A1 #bc-clock-weather 存在且為 #bc-clock 第一個子項",
                                  m.get("wrap_found") is True and m.get("wrap_is_first") is True,
                                  f"found={m.get('wrap_found')} first={m.get('wrap_is_first')}"))
            failures.append(check("A2 #bc-clock 內恰 1 個 #bc-clock-weather / 1 顆 .weather",
                                  m.get("wrap_count") == 1 and m.get("w_count") == 1,
                                  f"{m.get('wrap_count')}/{m.get('w_count')}"))
            wrap = m.get("wrap") or {}
            wm = m.get("w") or {}
            failures.append(check("A3 天氣元件六件組齊全（view/clock/icon/temperature/date/border）",
                                  wm.get("parts") == [1, 1, 1, 1, 1, 1], wm.get("parts")))
            failures.append(check("A4 三個原站修飾類別齊全（-font_en / -color_white / --visible）",
                                  all(k in (wm.get("cls") or "")
                                      for k in ("-font_en", "-color_white", "weather--visible")),
                                  wm.get("cls")))
            failures.append(check("A5 外層帶 data-reveal=clip-down（與照片格同一組揭示）",
                                  wrap.get("reveal") == "clip-down", wrap.get("reveal")))

            # ---------- B 幾何 ----------
            failures.append(check("B1 grid-area 1/1/2/2 ＋ align-self:start ＋ justify-self:center",
                                  wrap.get("area") == "1 / 1 / 2 / 2"
                                  and wrap.get("align") == "start"
                                  and wrap.get("justify") == "center",
                                  (wrap.get("area"), wrap.get("align"), wrap.get("justify"))))
            failures.append(check("B2 與另外 7 個時鐘子項 0 重疊",
                                  m.get("overlaps") == [], m.get("overlaps")))
            cr, wr = m.get("clock") or {}, wrap.get("rect") or {}
            # ≤575px 時天氣（.view 38*1.3＝49.4px）比欄 1（minmax(0,1fr)，約 29px）寬，
            # 置中後兩側各溢出約 10px（左緣仍在視口內、不產生水平溢出）→ 只驗
            # 「左緣 >= 0」與「不超出時鐘列右緣」。
            failures.append(check("B3 未超出視口左緣與時鐘列右緣",
                                  wr.get("x", -1) >= 0
                                  and wr.get("right", 1e9) <= cr.get("right", 0) + 1
                                  and m.get("wrap_left_ok") is True,
                                  f"wrap {wr} vs clock {cr}"))
            br = m.get("brace") or {}
            failures.append(check("B4 位於 { 之上（wrap.bottom < brace.top）",
                                  (wr.get("bottom") or 0) < (br.get("y") or 0),
                                  f"{wr.get('bottom')} vs {br.get('y')}"))
            failures.append(check("B5 無水平溢出",
                                  (m.get("doc_scroll_w") or 0) <= (m.get("inner_w") or 0) + 1,
                                  f"{m.get('doc_scroll_w')} vs {m.get('inner_w')}"))


            # B6 欄位未跑版
            cols, gap = m.get("cols") or [], m.get("gap") or 0
            kids = {k["id"]: k["rect"] for k in (m.get("kids") or [])}
            if w >= 992:
                spans = {"bc-clock-brace-open": (1, 1), "bc-clock-hours": (2, 2),
                         "bc-clock-colon-before-minutes": (3, 3), "bc-clock-photos": (4, 5),
                         "bc-clock-colon-after-minutes": (6, 6), "bc-clock-minutes": (7, 7),
                         "bc-clock-brace-close": (8, 8)}
                ncols = 8
            else:
                spans = {"bc-clock-brace-open": (1, 1), "bc-clock-hours": (2, 2),
                         "bc-clock-colon-before-minutes": (3, 3), "bc-clock-photos": (4, 6),
                         "bc-clock-colon-after-minutes": (7, 7), "bc-clock-minutes": (8, 8),
                         "bc-clock-brace-close": (9, 9)}
                ncols = 9
            bad = []
            if len(cols) != ncols:
                bad.append(f"欄數 {len(cols)} != {ncols}")
            else:
                for kid, (c1, c2) in spans.items():
                    k = kids.get(kid)
                    if not k:
                        bad.append(f"{kid} 缺失")
                        continue
                    lo, _ = col_bounds(cr, cols, gap, c1)
                    _, hi = col_bounds(cr, cols, gap, c2)
                    # 數字／標點的字寬可能大於 minmax(0,1fr) 的欄寬（如 991px 的「15」
                    # 寬 106px、欄寬 72.6px，靠 justify-self:center 置中溢出）——
                    # 這是改動前就有的設計，故文字項只驗「中心落在該欄」；
                    # 照片列（有實際寬度的區塊）仍驗「整塊落在該欄區間內」。
                    if kid == "bc-clock-photos":
                        ok_col = k["x"] >= lo - 1.5 and k["right"] <= hi + 1.5
                    else:
                        ok_col = lo - 1.5 <= (k["x"] + k["right"]) / 2 <= hi + 1.5
                    if not ok_col:
                        bad.append(f"{kid} 不在欄 {c1}-{c2}（x {k['x']}..{k['right']}）")
                lo1, hi1 = col_bounds(cr, cols, gap, 1)
                if abs((wr.get("x", 0) + wr.get("right", 0)) / 2 - (lo1 + hi1) / 2) > 2:
                    bad.append("天氣中心未對齊欄 1 中心")
            failures.append(check(f"B6 時鐘列未跑版（{ncols} 欄、各子項欄位與基準相同、"
                                  "天氣對齊欄 1 中心）", not bad, bad))

            # ---------- C +30% ----------
            nav = m.get("nav") or {}
            failures.append(check("C1 --wc-scale == 1.3", wm.get("scale") == "1.3",
                                  wm.get("scale")))
            exp_view = 104.0 if w >= 992 else 49.4
            failures.append(check(f"C2 .view 寬 = {exp_view}（navbar 的 ×1.3）",
                                  abs((wm.get("view_w") or 0) - exp_view) <= 0.06
                                  and abs((wm.get("view_w") or 0)
                                          - (nav.get("view_w") or 0) * 1.3) <= 0.1,
                                  f"hero {wm.get('view_w')} / nav {nav.get('view_w')}"))
            ratios = [("clock .value", wm.get("clock_val_fs"), nav.get("clock_val_fs")),
                      ("temperature .value", wm.get("temp_fs"), nav.get("temp_fs")),
                      ("unit", wm.get("unit_fs"), nav.get("unit_fs")),
                      ("date", wm.get("date_fs"), nav.get("date_fs"))]
            bad = [f"{k} {a}/{b}" for k, a, b in ratios if not b or abs(a / b - 1.3) > 0.01]
            failures.append(check("C3 字級皆為 navbar 的 1.3 倍（clock/temp/unit/date）",
                                  not bad, bad))

            # ---------- D 內容 ----------
            cv = wm.get("clock_val") or ""
            failures.append(check("D1 時鐘為 HH:MM 且與 navbar 那顆一致",
                                  bool(re.fullmatch(r"\d{2}:\d{2}", cv))
                                  and cv == nav.get("clock_val"), cv))
            failures.append(check("D2 日期已填（month/day/weekday 非空）",
                                  bool((wm.get("month") or "").strip())
                                  and (wm.get("day") or "").isdigit()
                                  and wm.get("weekday") in
                                  ("Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"),
                                  (wm.get("month"), wm.get("day"), wm.get("weekday"))))
            failures.append(check("D3 year 有值但 CSS 隱藏（原站行為不變）",
                                  bool(wm.get("year")) and wm.get("year_disp") == "none",
                                  (wm.get("year"), wm.get("year_disp"))))
            failures.append(check("D4 溫度已填（數字）且 icon img 有載入",
                                  bool(re.fullmatch(r"-?\d+", str(wm.get("temp_val") or "")))
                                  and (m.get("img") or {}).get("exists") is True
                                  and ((m.get("img") or {}).get("nw") or 0) > 0,
                                  (wm.get("temp_val"), m.get("img"))))

            # ---------- E 首頁 navbar 那顆 ----------
            failures.append(check("E1 首頁 navbar 天氣仍 visibility:hidden",
                                  nav.get("vis") == "hidden", nav.get("vis")))
            exp_nav_view = 80.0 if w >= 992 else 38.0   # ≤991.98px 的原站 .mb 尺寸
            failures.append(check(f"E2 navbar 那顆未縮放（--wc-scale 1、view {exp_nav_view:.0f}）",
                                  (nav.get("scale") or "1") in ("1", "")
                                  and abs((nav.get("view_w") or 0) - exp_nav_view) <= 0.01,
                                  (nav.get("scale"), nav.get("view_w"))))
            failures.append(check("E3 navbar 那顆仍有被填充（時鐘/日期/icon）",
                                  bool(re.fullmatch(r"\d{2}:\d{2}", nav.get("clock_val") or ""))
                                  and bool((nav.get("month") or "").strip())
                                  and (nav.get("img_nw") or 0) > 0,
                                  (nav.get("clock_val"), nav.get("month"), nav.get("img_nw"))))


            # ---------- F 照片列文字 ----------
            # 照片格＝環形照片列（2026-10-14 改版）：7 個 .hero_hand_item ＋ 一組 7 筆文字，
            # 只有 -current 那筆顯示（索引由 GUNTE hero 的 Splide 推播；環形幾何/同步的細節由
            # docs/verify/cdp_verify_hero_coffee_photos.py 專責驗）。
            ring_alts = m.get("ring_alts") or []
            caps = m.get("caps") or []
            vis_caps = [c for c in caps if c.get("cur")]
            failures.append(check("F1 環形照片列 7 筆、每筆都有非空 alt",
                                  m.get("ring_count") == 7 and len(ring_alts) == 7
                                  and all((a or "").strip() for a in ring_alts),
                                  (m.get("ring_count"), ring_alts[:2])))
            failures.append(check("F2 文字列 7 筆、恰 1 筆 -current、name/highlight 皆非空",
                                  len(caps) == 7 and m.get("cap_vis") == 1
                                  and all((c.get("name") or "").strip()
                                          and (c.get("hl") or "").strip() for c in caps),
                                  (len(caps), m.get("cap_vis"))))
            ring_cur = m.get("ring_cur")
            ok_cur = (0 <= (ring_cur if ring_cur is not None else -1) < len(ring_alts))
            failures.append(check("F3 顯示中的 name == 環形 -current 那筆 img alt（兩者同索引）",
                                  ok_cur and m.get("caps_cur") == ring_cur and bool(vis_caps)
                                  and (vis_caps[0].get("name") or "").strip()
                                  == (ring_alts[ring_cur] or "").strip(),
                                  (m.get("caps_cur"), ring_cur,
                                   (vis_caps[0].get("name") if vis_caps else None),
                                   ring_alts[ring_cur] if ok_cur else None)))
            exp_h = expected_img_h(w)
            failures.append(check(
                f"F4 照片區高度 = {exp_h:.2f}px ±1（≥992px = 480vw/ratio；≤991px = 改動前 180vw/ratio）",
                abs((m.get("photo_h") or 0) - exp_h) <= 1,
                m.get("photo_h")))
            exp_cap = (8 + 16 * 1.3 + 4 + 12 * 1.4) if w >= 992 else (
                (8 + 13 * 1.3 + 4 + 10 * 1.4) if w >= 768 else (8 + 11 * 1.3 + 4 + 9 * 1.4))
            failures.append(check(f"F5 文字區高度 = --bc-hero-caption-h（{exp_cap:.2f}px ±1）",
                                  abs((m.get("cap_h") or 0) - exp_cap) <= 1,
                                  (m.get("cap_h"), m.get("cap_h_var"))))
            failures.append(check("F6 首頁照片格已無舊輪播 hook（data-footer-logo=item）",
                                  m.get("legacy_items") == 0, m.get("legacy_items")))
            exp_fs = (16.0, 12.0) if w >= 992 else ((13.0, 10.0) if w >= 768 else (11.0, 9.0))
            failures.append(check(f"F7 字級 {exp_fs[0]:.0f}/{exp_fs[1]:.0f}px（7 筆文字皆同）",
                                  len(caps) == 7
                                  and all(abs(c.get("name_fs", 0) - exp_fs[0]) <= 0.01
                                          and abs(c.get("hl_fs", 0) - exp_fs[1]) <= 0.01
                                          for c in caps),
                                  [(c.get("name_fs"), c.get("hl_fs")) for c in caps[:2]]))
            failures.append(check("F8 highlight 品牌金 ＋ name Josefin Sans/uppercase/白字",
                                  len(caps) == 7
                                  and all(c.get("hl_color") == "rgb(196, 155, 99)"
                                          and "Josefin Sans" in (c.get("name_ff") or "")
                                          and c.get("name_tt") == "uppercase"
                                          and c.get("name_color") == "rgb(255, 255, 255)"
                                          for c in caps),
                                  [(c.get("hl_color"), c.get("name_color")) for c in caps[:2]]))
            await shot(name)


        # ================= /about/ 反向守門 =================
        await set_viewport(1280, 800)
        await goto(f"{BASE}/about/")
        await evaljs("(function(){var c=document.getElementById('bc-clock');"
                     "if(c)c.scrollIntoView({block:'center'});})()")
        await asyncio.sleep(1.6)
        a = await evaljs(ABOUT_JS) or {}
        an = a.get("nav") or {}
        print("\n=== /about/ 反向守門 (1280x800) ===")
        failures.append(check("G1 /about/ navbar 天氣仍可見（weather--visible 未受影響）",
                              an.get("vis") == "visible", an.get("vis")))
        failures.append(check("G2 /about/ navbar 天氣未縮放（--wc-scale 1、view 80）",
                              (an.get("scale") or "1") in ("1", "")
                              and abs((an.get("view_w") or 0) - 80) <= 0.01,
                              (an.get("scale"), an.get("view_w"))))
        failures.append(check("G3 /about/ navbar 天氣仍被填充（時鐘/日期/溫度）",
                              bool(re.fullmatch(r"\d{2}:\d{2}", an.get("clock_val") or ""))
                              and bool((an.get("month") or "").strip())
                              and bool(an.get("temp_val")),
                              (an.get("clock_val"), an.get("month"), an.get("temp_val"))))
        failures.append(check("G4 /about/ 真頁尾 #bc-bg-footer 內 0 顆 .weather、無 #bc-clock-weather",
                              a.get("footer_found") is True
                              and a.get("footer_weather") == 0 and a.get("footer_wrap") == 0,
                              (a.get("footer_weather"), a.get("footer_wrap"))))
        failures.append(check("G5 /about/ 時鐘列仍為 8 欄、{ 位置與改動前一致（x75 w20.05）",
                              a.get("cols") == 8
                              and abs((a.get("brace") or {}).get("x", 0) - 75) <= 0.5
                              and abs((a.get("brace") or {}).get("w", 0) - 20.05) <= 0.5,
                              (a.get("cols"), a.get("brace"))))

        await send(msg("Page.close"))

    total = len(failures)
    bad = sum(1 for f in failures if not f)
    print(f"\n===== 合計 {total} 項，PASS {total - bad}，FAIL {bad} =====")
    return bad


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))

