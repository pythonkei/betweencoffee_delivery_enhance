#!/usr/bin/env python3
"""CDP 驗證：浮動購物車 2026-09-21 改版

檢查項目（每個斷點 × 首頁／咖啡詳情頁）：
 1. 首頁 .bc-yama .header-bot（購物車 [ n ] 列）已隱藏
 2. #bc-floating-cart 貼在 .bc-attract-buy 正上方（底緣貼齊按鈕盒上緣）
 3. 中心線對齊（圓心 x == 按鈕盒中心 x）
 4. 僅圖示：border-width 0、border-radius 0、無底色、無陰影
 5. 圖示尺寸依斷點 52 / 48 / 44px
 6. 點擊命中：elementFromPoint(圖示中心) 命中浮動鈕（不被 Buy 按鈕熱區蓋住）
 7. 無水平溢出；兩個圖示字型可用
"""
import asyncio, json, urllib.request
import websockets

BASE = "http://127.0.0.1:8081"
VIEWPORTS = [(1440, 900, False), (1024, 800, False), (768, 1024, True), (390, 844, True), (320, 640, True)]
PAGES = [("index", "/"), ("about", "/about/"), ("coffee4", "/coffee/4/"),
         ("bean1", "/bean/1/"), ("coffee_menu", "/coffee_menu/")]
# 2026-09-21（使用者指示）：
#   · 浮動購物車「所有模板位置和 index 一樣」→ 全站（含本清單每頁）浮動鈕盒上緣
#     都對齊 navbar-brand 頂邊；下方另做「跨頁位置一致性」與「對齊基準」檢查。
#   · .weather 全站隱藏、僅 about 頁顯示（bc-weather.js 亦只在 about 載入）。
#   · /coffee/4/、/bean/1/、/coffee_menu/：.bc-attract-nav 被 display:none →
#     浮動鈕單獨對齊 navbar-brand 頂邊（不再退回 CSS 的垂直置中退化值）。
#   （註：舊版含 /cart/，但購物車為空時該網址 302 → /coffee_menu/，故改測 /coffee_menu/ 本身）

JS = r"""
(function(){
  function rect(el){ if(!el) return null; var r=el.getBoundingClientRect();
    return {x:+r.x.toFixed(1), y:+r.y.toFixed(1), w:+r.width.toFixed(1), h:+r.height.toFixed(1),
            fromRight:+(window.innerWidth-r.right).toFixed(1), cx:+(r.left+r.width/2).toFixed(1)}; }
  var out={};
  var fc = document.getElementById('bc-floating-cart');
  var btn = document.getElementById('bc-floating-cart-btn');
  var icon = btn ? btn.querySelector('.material-icons, .material-symbols-outlined') : null;
  var buy = document.querySelector('.bc-attract-buy');

  /* 1. 首頁 yama 購物車列 */
  var bot = document.querySelector('.bc-yama .header-bot');
  var botRow = document.querySelector('.bc-yama .header-bot .account li.cart');
  out.yama_header_bot_display = bot ? getComputedStyle(bot).display : 'no-yama-on-page';
  out.yama_cart_row_rect = rect(botRow);

  /* 1b. weather 顯示範圍 ＋ 對齊基準（2026-09-21：weather 全站隱藏、僅 about 顯示） */
  var wEl = document.querySelector('#ftco-navbar .weather');
  var brandEl = document.querySelector('#ftco-navbar .navbar-brand');
  var togglerEl = document.querySelector('#ftco-navbar .navbar-toggler');
  var scrollTop = window.pageYOffset || document.documentElement.scrollTop || 0;
  out.weather = {
    visibility: wEl ? getComputedStyle(wEl).visibility : 'no-weather',
    has_visible_class: !!(wEl && wEl.classList.contains('weather--visible')),
    script_loaded: !!document.querySelector('script[src*="bc-weather.js"]')
  };
  /* 浮動鈕的對齊基準＝navbar-brand 頂邊的「文件座標」（與 bc-attract-place.js 同算法）
     2026-09-21：weather 可見（about 頁）時，整組會再往下讓開 weather 下緣 8px
     2026-09-21 追加：手機/平板整組上移 --bc-attract-lift（桌面 0、≤991.98 8px） */
  out.navbar_brand_top = brandEl ? +(brandEl.getBoundingClientRect().top + scrollTop).toFixed(1) : null;
  out.attract_lift = (function () {
    var navEl = document.querySelector('.bc-attract-nav');
    if (!navEl) return 0;
    var v = parseFloat(getComputedStyle(navEl).getPropertyValue('--bc-attract-lift'));
    return isFinite(v) ? v : 0;
  })();
  var wBottomDoc = null;
  if (wEl && getComputedStyle(wEl).visibility === 'visible') {
    var _wr = wEl.getBoundingClientRect();
    if (_wr.height) wBottomDoc = +(_wr.bottom + scrollTop + 8).toFixed(1);
  }
  out.weather_bottom_doc = wBottomDoc;
  /* 與 bc-attract-place.js 的 anchorTop() 完全同算法：
     base = brand 頂邊 − lift；若 weather 讓位值較低則用之；上移後再以 weather 讓位值為下限 */
  out.expected_cart_top = (out.navbar_brand_top === null)
    ? null : +(out.navbar_brand_top - out.attract_lift).toFixed(1);
  if (wBottomDoc !== null && out.navbar_brand_top !== null) {
    if (wBottomDoc > out.navbar_brand_top) {
      out.expected_cart_top = wBottomDoc;
    } else if (out.expected_cart_top !== null && out.expected_cart_top < wBottomDoc) {
      out.expected_cart_top = wBottomDoc;
    }
  }
  out.attract_pending = document.documentElement.classList.contains('bc-attract-pending');
  out.attract_ready = !!document.querySelector('.bc-attract-nav.bc-attract-ready');
  /* 2026-09-21（使用者指示「在全端隱藏右上角的選單」）：navbar 漢堡選單必須全站隱藏 */
  var menuEl = document.querySelector('#ftco-navbar .bc-attract-menu');
  out.toggler_display = togglerEl ? getComputedStyle(togglerEl).display : 'no-toggler';
  out.menu_rect_w = menuEl ? +menuEl.getBoundingClientRect().width.toFixed(1) : null;
  out.menu_hidden = !menuEl || out.menu_rect_w === 0;

  /* 1c. 初始（未強制顯示）狀態：2026-09-21 使用者指示「空車也顯示圖示、只隱藏數字圓圈」 */
  if (fc) {
    var initBadge = fc.querySelector('.bc-floating-cart-badge');
    out.initial_state = {
      cart_display: getComputedStyle(fc).display,
      cart_visible: getComputedStyle(fc).display !== 'none',
      badge_display: initBadge ? getComputedStyle(initBadge).display : null,
      badge_text: initBadge ? initBadge.textContent.trim() : null,
      badge_hidden: !!(initBadge && getComputedStyle(initBadge).display === 'none')
    };
  }

  /* 2. 讓浮動鈕可見後量測（DOM 層模擬，不需真實購物車商品） */
  if (fc) {
    fc.style.display = '';
    fc.classList.add('show','no-anim');
    if (window.bcCart && window.bcCart._placeFloatingCart) window.bcCart._placeFloatingCart();
  }
  var cs = fc ? getComputedStyle(fc) : null;
  out.css_vars = cs ? {size: cs.getPropertyValue('--bc-fc-size').trim(),
                       right: cs.getPropertyValue('--bc-fc-right').trim(),
                       top: cs.getPropertyValue('--bc-fc-top').trim()} : null;
  out.cart_wrapper = rect(fc);
  out.cart_btn = rect(btn);
  /* 2026-09-21：全站改為與 index 相同的「頂部對齊」後，確認沒蓋到 navbar 的 logo／漢堡選單 */
  if (out.cart_wrapper) {
    var hitRect = function (a, b) {
      return !!(a && b && a.x < b.x + b.w - 0.5 && a.x + a.w > b.x + 0.5 &&
                a.y < b.y + b.h - 0.5 && a.y + a.h > b.y + 0.5);
    };
    out.overlaps_brand = hitRect(out.cart_wrapper, rect(brandEl));
    out.overlaps_toggler = hitRect(out.cart_wrapper, rect(togglerEl));
    /* 2026-09-21：about 頁 weather 可見 → 不可與浮動鈕重疊（bc-attract-place.js 會讓開其下緣） */
    out.overlaps_weather = hitRect(out.cart_wrapper, rect(wEl));
    if (wEl) {
      out.weather_display = getComputedStyle(wEl).visibility;
    }
    if (togglerEl && getComputedStyle(togglerEl).display !== 'none') {
      var _tr = togglerEl.getBoundingClientRect();
      var _hit = document.elementFromPoint(_tr.left + _tr.width / 2, _tr.top + _tr.height / 2);
      out.toggler_clickable = !!(_hit && (togglerEl === _hit || togglerEl.contains(_hit)));
    } else {
      out.toggler_clickable = true;   /* 桌機（navbar-expand-lg）漢堡不存在 → 不適用 */
    }
  }
  var bcs = btn ? getComputedStyle(btn) : null;
  out.btn_style = bcs ? {borderWidth: bcs.borderTopWidth, borderStyle: bcs.borderTopStyle,
                         borderRadius: bcs.borderTopLeftRadius,
                         backgroundImage: bcs.backgroundImage, backgroundColor: bcs.backgroundColor,
                         boxShadow: bcs.boxShadow, fontSize: bcs.fontSize} : null;
  out.icon_font_size = icon ? getComputedStyle(icon).fontSize : null;
  out.icon_glyph = icon ? icon.textContent.trim() : null;
  out.icon_class = icon ? icon.className : null;
  /* 缺字偵測：圖示字形寬度應 ≈ 字級（1em）；若字型無此字形會退回多字文字 → 寬度遠大於字級 */
  if (icon) {
    var _ir = icon.getBoundingClientRect();
    var _fs = parseFloat(getComputedStyle(icon).fontSize) || 0;
    out.icon_rect_w = +_ir.width.toFixed(1);
    out.icon_glyph_ok = _ir.width > 0 && _fs > 0 && _ir.width <= _fs * 1.35;
  }

  var bar = document.querySelector('.bc-attract-buy__link');   /* 使用者實際看到的長條 */
  var profile = document.querySelector('.bc-attract-profile');
  var buyVisible = !!(buy && getComputedStyle(buy).display !== 'none' && buy.getBoundingClientRect().width > 0);
  out.buy_display = buy ? getComputedStyle(buy).display : 'no-buy';
  /* 2026-09-21：尺寸斷言用「外盒」（.bc-attract-buy 本體）；
     .bc-attract-buy__link 因 .c-attract 的 --attract padding 會比外盒寬，不適合比對尺寸 */
  out.buy_box = buy ? rect(buy) : null;
  out.bar = (bar && buyVisible) ? rect(bar) : null;
  out.profile = (profile && buyVisible) ? rect(profile) : null;
  if (out.bar && out.cart_wrapper) {
    out.center_diff_px = +(out.cart_wrapper.cx - out.bar.cx).toFixed(1);
    out.cart_top_ok = out.cart_wrapper.y >= -0.5;                       /* 不可被推到畫面外 */
    out.overlaps_bar = (out.cart_wrapper.y < (out.bar.y + out.bar.h) - 0.5)
                    && ((out.cart_wrapper.y + out.cart_wrapper.h) > out.bar.y + 0.5);
    out.placement = ((out.cart_wrapper.y + out.cart_wrapper.h) <= out.bar.y + 1) ? 'above-bar' : 'below-cluster';
    /* 2026-09-21：與 Buy 按鈕的間距（使用者指示「增加間距」；CSS 定義 --bc-fc-gap：
       桌面/平板 20px、手機（≤767.98）12px——2026-09-21 使用者追加「手機端縮小間距」） */
    out.gap_px = +(out.bar.y - (out.cart_wrapper.y + out.cart_wrapper.h)).toFixed(1);
    out.fc_gap_css = (function () {
      var v = parseFloat(getComputedStyle(fc).getPropertyValue('--bc-fc-gap'));
      return isFinite(v) ? v : null;
    })();
    /* 2026-09-21（使用者指示「全端 bc-attract-buy and profile 和 index 一樣」）：
       所有頁面的 Buy／個人圓鈕都要可見，且圓鈕在長條下方（＝index 的堆疊順序） */
    out.buy_visible = !!(buy && buy.getBoundingClientRect().width > 0);
    out.profile_visible = !!(profile && profile.getBoundingClientRect().width > 0);
    out.profile_below_bar = !!(out.bar && out.profile && out.profile.y >= out.bar.y + out.bar.h - 1);
  }

  /* 3. 點擊命中 */
  if (out.cart_btn) {
    var cx = out.cart_btn.x + out.cart_btn.w/2, cy = out.cart_btn.y + out.cart_btn.h/2;
    var hit = document.elementFromPoint(cx, cy);
    out.hit_at_center = hit ? (hit.id || hit.tagName) + '.' + (hit.getAttribute('class')||'').split(' ').slice(0,2).join('.') : null;
    out.hit_is_cart = !!(hit && (hit === btn || btn.contains(hit) || hit === icon));
  }
  out.no_overflow = document.documentElement.scrollWidth <= window.innerWidth + 1;
  out.font_icons_ready = document.fonts.check('52px "Material Icons"');
  out.font_symbols_ready = document.fonts.check('52px "Material Symbols Outlined"');
  return out;
})()
"""

# 量測前的前置步驟：讓浮動鈕可見 + 明確要求載入圖示字型。
# 原因：咖啡選單等頁面購物車初始為 display:none，瀏覽器不會為其載入圖示字型，
# 一旦被強制顯示會先渲染成文字（實測寬 346px = "shopping_bag" 12 字）→ 假失敗。
PREP_JS = (
    "(async function(){"
    "var fc=document.getElementById('bc-floating-cart');"
    "if(fc){fc.style.display='';}"
    "if(document.fonts&&document.fonts.load){"
    "try{await document.fonts.load('37px \"Material Icons\"');"
    "await document.fonts.load('34px \"Material Icons\"');"
    "await document.fonts.load('31px \"Material Icons\"');}catch(e){}}"
    "return true;})()"
)


async def main():
    req = urllib.request.Request("http://127.0.0.1:9222/json/new?about:blank", method="PUT")
    tab = json.loads(urllib.request.urlopen(req).read().decode())
    async with websockets.connect(tab["webSocketDebuggerUrl"], max_size=None) as ws:
        mid = 1

        def msg(m, p=None):
            nonlocal mid
            r = {"id": mid, "method": m, "params": p or {}}
            mid += 1
            return r

        async def send(m):
            await ws.send(json.dumps(m))
            while True:
                r = json.loads(await ws.recv())
                if r.get("id") == m["id"]:
                    return r.get("result", {})

        await send(msg("Page.enable"))
        await send(msg("Runtime.enable"))
        await send(msg("Network.enable"))
        await send(msg("Page.setCacheDisabled", {"cacheDisabled": True}))
        await send(msg("Network.setCacheDisabled", {"cacheDisabled": True}))

        async def eval_js(expr):
            r = await send(msg("Runtime.evaluate", {"expression": expr, "returnByValue": True}))
            return r.get("result", {}).get("value")

        async def wait_ready(timeout=15.0):
            """等「頁面完成 + 浮動購物車節點存在 + bcCart 就緒 + 字型載入完成」。
            2026-09-21：原本固定 sleep 3s，在慢頁面（重導、圖示字型）會量到
            「字型未載入→圖示退回文字」與大量 null 的假失敗。"""
            t0 = asyncio.get_event_loop().time()
            while True:
                ok = await eval_js(
                    "(document.readyState === 'complete')"
                    " && !!document.getElementById('bc-floating-cart')"
                    " && !!window.bcCart"
                    " && (document.fonts ? document.fonts.status === 'loaded' : true)")
                if ok:
                    return True
                if asyncio.get_event_loop().time() - t0 > timeout:
                    return False
                await asyncio.sleep(0.4)

        expected_size = {1440: 37, 1024: 37, 768: 34, 390: 31, 320: 31}   # 2026-09-21 三度縮小：37/34/31（再 −15%）
        # 2026-09-21（使用者指示「手機端平板端 bc-attract-buy 與個人圓鈕放大一點，桌面不動」）：
        #   buy 外盒 40×150（桌機，不變）／40×136（平板）／34×112（≤767）／30×96（≤575）
        #   個人圓鈕 50（桌機，不變）／48／42／36
        expected_buy = {1440: (40, 150), 1024: (40, 150), 768: (40, 136), 390: (30, 96), 320: (30, 96)}
        expected_profile = {1440: 50, 1024: 50, 768: 48, 390: 36, 320: 36}
        fails = []
        pos_map = {}   # {(w): {page: cart_y}} → 跨頁位置一致性（2026-09-21 使用者指示）

        for w, h, mobile in VIEWPORTS:
            await send(msg("Emulation.setDeviceMetricsOverride",
                           {"width": w, "height": h, "deviceScaleFactor": 1, "mobile": mobile}))
            for name, path in PAGES:
                # 2026-09-21：每次導航加一次性參數——瀏覽器會對 HTML 做 heuristic 快取
                # （實測 390 那輪拿到舊版 HTML → 連帶舊 ?v= 的 CSS/JS，量到舊尺寸/舊 gap 的假失敗）
                sep = "&" if "?" in path else "?"
                await send(msg("Page.navigate", {"url": f"{BASE}{path}{sep}bcv={int(asyncio.get_event_loop().time() * 1000)}"}))
                ready = await wait_ready()
                if not ready:
                    # 慢速或重導頁面再試一次（強制忽略快取）
                    await send(msg("Page.reload", {"ignoreCache": True}))
                    ready = await wait_ready()
                r = await send(msg("Runtime.evaluate", {"expression": JS, "returnByValue": True}))
                v = r.get("result", {}).get("value", {})
                v["_ready"] = ready
                if not v.get("icon_glyph_ok"):
                    # 先讓浮動鈕可見並等圖示字型真正載入後再量一次（見 PREP_JS 說明）
                    await send(msg("Runtime.evaluate", {"expression": PREP_JS,
                                                        "awaitPromise": True, "returnByValue": True}))
                    await asyncio.sleep(0.5)
                    r = await send(msg("Runtime.evaluate", {"expression": JS, "returnByValue": True}))
                    v = r.get("result", {}).get("value", {})
                    v["_ready"] = ready
                    v["_after_font_prep"] = True
                print(f"=== {w}x{h} / {name} ===")
                print(json.dumps(v, ensure_ascii=False))

                tag = f"{w}/{name}"
                if not v.get("_ready"):
                    fails.append(f"{tag}: 頁面未就緒（逾時，量測可能不完整）")
                if v.get("icon_font_size") != f"{expected_size[w]}px":
                    fails.append(f"{tag}: 圖示尺寸 {v.get('icon_font_size')} != {expected_size[w]}px")
                bs = v.get("btn_style") or {}
                if bs.get("borderWidth") not in ("0px", None):
                    fails.append(f"{tag}: 仍有邊框 {bs.get('borderWidth')}")
                if bs.get("borderRadius") not in ("0px", None):
                    fails.append(f"{tag}: 仍有圓角 {bs.get('borderRadius')}")
                if bs.get("backgroundImage") not in ("none", None):
                    fails.append(f"{tag}: 仍有背景圖 {bs.get('backgroundImage')}")
                if bs.get("backgroundColor") not in ("rgba(0, 0, 0, 0)", "transparent", None):
                    fails.append(f"{tag}: 仍有底色 {bs.get('backgroundColor')}")
                if v.get("bar"):
                    if abs(v.get("center_diff_px", 99)) > 1:
                        fails.append(f"{tag}: 中心線偏差 {v.get('center_diff_px')}px（vs 可見長條）")
                    if not v.get("cart_top_ok"):
                        fails.append(f"{tag}: 圖示被推出畫面外 y={(v.get('cart_wrapper') or {}).get('y')}")
                    if v.get("overlaps_bar"):
                        fails.append(f"{tag}: 圖示與 Buy 長條重疊")
                    # 2026-09-21（使用者指示「手機端縮小浮動購物車間距」）：
                    #   間距期望值改讀 CSS 變數 --bc-fc-gap（桌面/平板 20px、手機 12px）
                    exp_gap = v.get("fc_gap_css")
                    if exp_gap is None:
                        exp_gap = 20
                    if v.get("placement") == "above-bar" and abs(v.get("gap_px", -99) - exp_gap) > 1:
                        fails.append(f"{tag}: 與 Buy 間距 {v.get('gap_px')}px != {exp_gap}px（--bc-fc-gap）")
                ist = v.get("initial_state") or {}
                if ist and not ist.get("cart_visible"):
                    fails.append(f"{tag}: 初始狀態未顯示浮動鈕圖示（display={ist.get('cart_display')}）")
                if ist and ist.get("badge_text") == "0" and not ist.get("badge_hidden"):
                    fails.append(f"{tag}: 數量 0 時仍顯示數字圓圈")
                if not v.get("hit_is_cart"):
                    fails.append(f"{tag}: 點擊中心未命中浮動鈕（{v.get('hit_at_center')}）")
                if not v.get("icon_glyph_ok"):
                    fails.append(f"{tag}: 圖示字型可能缺字（寬 {v.get('icon_rect_w')} vs 字級 {v.get('icon_font_size')}）")
                if name == "index" and v.get("yama_header_bot_display") != "none":
                    fails.append(f"{tag}: header-bot 未隱藏（{v.get('yama_header_bot_display')}）")
                # 2026-09-21（使用者指示）：
                #   · .weather 全站隱藏、僅 about 頁顯示（bc-weather.js 亦僅 about 載入）
                #   · 浮動購物車全站位置與 index 相同（盒上緣對齊 navbar-brand 頂邊）
                wx = v.get("weather") or {}
                if name == "about":
                    if wx.get("visibility") != "visible":
                        fails.append(f"{tag}: about 頁 weather 應可見（目前 {wx.get('visibility')}）")
                    if not wx.get("has_visible_class"):
                        fails.append(f"{tag}: about 頁缺少 .weather--visible")
                    if not wx.get("script_loaded"):
                        fails.append(f"{tag}: about 頁未載入 bc-weather.js")
                else:
                    if wx.get("visibility") != "hidden":
                        fails.append(f"{tag}: weather 應隱藏（目前 {wx.get('visibility')}）")
                    if wx.get("has_visible_class"):
                        fails.append(f"{tag}: 非 about 頁卻有 .weather--visible")
                    if wx.get("script_loaded"):
                        fails.append(f"{tag}: 非 about 頁不應載入 bc-weather.js")
                anchor = v.get("navbar_brand_top")
                exp_top = v.get("expected_cart_top")
                cw = v.get("cart_wrapper") or {}
                if exp_top is not None and abs((cw.get("y") if cw.get("y") is not None else -999) - exp_top) > 1:
                    fails.append(f"{tag}: 浮動鈕 top {cw.get('y')} 未對齊預期基準 {exp_top}"
                                 f"（navbar-brand {anchor}／weather 讓位）")
                if v.get("overlaps_weather") and (v.get("weather") or {}).get("visibility") == "visible":
                    fails.append(f"{tag}: 浮動鈕與 weather 天氣元件重疊")
                if not v.get("menu_hidden"):
                    fails.append(f"{tag}: 右上角漢堡選單未隱藏"
                                 f"（toggler display={v.get('toggler_display')}／menu 寬 {v.get('menu_rect_w')}）")
                if v.get("bar"):
                    eb = expected_buy[w]
                    barv = v.get("buy_box") or v.get("bar") or {}
                    if abs((barv.get("w") or 0) - eb[0]) > 1 or abs((barv.get("h") or 0) - eb[1]) > 1:
                        fails.append(f"{tag}: Buy 外盒 {barv.get('w')}×{barv.get('h')} != {eb[0]}×{eb[1]}"
                                     f"（手機/平板加大、桌面不動）")
                    pv = v.get("profile") or {}
                    if abs((pv.get("w") or 0) - expected_profile[w]) > 1:
                        fails.append(f"{tag}: 個人圓鈕 {pv.get('w')}×{pv.get('h')}"
                                     f" != {expected_profile[w]}×{expected_profile[w]}")
                    if not v.get("buy_visible"):
                        fails.append(f"{tag}: bc-attract-buy 不可見（應與 index 相同）")
                    if not v.get("profile_visible"):
                        fails.append(f"{tag}: bc-attract-profile 不可見（應與 index 相同）")
                    if v.get("placement") == "above-bar" and not v.get("profile_below_bar"):
                        fails.append(f"{tag}: 個人圓鈕不在 Order 長條下方（堆疊順序與 index 不符）")
                if v.get("attract_pending"):
                    fails.append(f"{tag}: .bc-attract-pending 未移除（整組可能仍隱藏）")
                if v.get("overlaps_brand"):
                    fails.append(f"{tag}: 浮動鈕與 navbar logo 重疊")
                if v.get("toggler_clickable") is False:
                    fails.append(f"{tag}: 漢堡選單被浮動鈕蓋住（無法點擊）")
                # 跨頁一致性只比「weather 隱藏」的頁面（about 因讓開天氣會略低，另以 expected_cart_top 驗）
                pos_map.setdefault(w, {})[name] = (cw.get("y") if wx.get("visibility") == "hidden" else None)
                if not v.get("no_overflow"):
                    fails.append(f"{tag}: 水平溢出")
                if not v.get("font_icons_ready"):
                    fails.append(f"{tag}: Material Icons 字型未就緒")

        # 2026-09-21（使用者指示）：浮動鈕在「所有模板」的位置必須一致（＝與 index 相同）
        for w, per in sorted(pos_map.items()):
            ys = {k: val for k, val in per.items() if val is not None}
            if len(ys) > 1 and len({round(val) for val in ys.values()}) > 1:
                fails.append(f"{w}px：浮動鈕位置跨頁不一致 {ys}")

        print("\n=== 檢查結果 ===")
        if fails:
            print(f"✗ {len(fails)} 項未通過：")
            for f in fails:
                print("  - " + f)
        else:
            print("✓ 全部通過（尺寸／無框無底／中心線貼齊／點擊命中／yama 隱藏／無溢出／字型"
                  "／weather 顯示範圍／跨頁位置一致／不遮 navbar）")

        try:
            urllib.request.urlopen("http://127.0.0.1:9222/json/close/" + tab["id"])
        except Exception:
            pass


if __name__ == "__main__":
    asyncio.run(main())
