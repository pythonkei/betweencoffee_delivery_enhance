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
PAGES = [("index", "/"), ("coffee4", "/coffee/4/"), ("bean1", "/bean/1/"), ("coffee_menu", "/coffee_menu/")]
# /coffee/4/、/bean/1/、/coffee_menu/：.bc-attract-nav 被隱藏 → 走 CSS 同軸線退化值
# （註：舊版含 /cart/，但購物車為空時該網址 302 → /coffee_menu/，故改測 /coffee_menu/ 本身）

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

  /* 2. 讓浮動鈕可見後量測（DOM 層模擬，不需真實購物車商品；顯示邏輯本身未改） */
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
  out.bar = (bar && buyVisible) ? rect(bar) : null;
  out.profile = (profile && buyVisible) ? rect(profile) : null;
  if (out.bar && out.cart_wrapper) {
    out.center_diff_px = +(out.cart_wrapper.cx - out.bar.cx).toFixed(1);
    out.cart_top_ok = out.cart_wrapper.y >= -0.5;                       /* 不可被推到畫面外 */
    out.overlaps_bar = (out.cart_wrapper.y < (out.bar.y + out.bar.h) - 0.5)
                    && ((out.cart_wrapper.y + out.cart_wrapper.h) > out.bar.y + 0.5);
    out.placement = ((out.cart_wrapper.y + out.cart_wrapper.h) <= out.bar.y + 1) ? 'above-bar' : 'below-cluster';
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
    "try{await document.fonts.load('48px \"Material Icons\"');"
    "await document.fonts.load('44px \"Material Icons\"');"
    "await document.fonts.load('40px \"Material Icons\"');}catch(e){}}"
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

        expected_size = {1440: 48, 1024: 48, 768: 44, 390: 40, 320: 40}   # 2026-09-21 圖示縮小：48/44/40
        fails = []

        for w, h, mobile in VIEWPORTS:
            await send(msg("Emulation.setDeviceMetricsOverride",
                           {"width": w, "height": h, "deviceScaleFactor": 1, "mobile": mobile}))
            for name, path in PAGES:
                await send(msg("Page.navigate", {"url": BASE + path}))
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
                if not v.get("hit_is_cart"):
                    fails.append(f"{tag}: 點擊中心未命中浮動鈕（{v.get('hit_at_center')}）")
                if not v.get("icon_glyph_ok"):
                    fails.append(f"{tag}: 圖示字型可能缺字（寬 {v.get('icon_rect_w')} vs 字級 {v.get('icon_font_size')}）")
                if name == "index" and v.get("yama_header_bot_display") != "none":
                    fails.append(f"{tag}: header-bot 未隱藏（{v.get('yama_header_bot_display')}）")
                if not v.get("no_overflow"):
                    fails.append(f"{tag}: 水平溢出")
                if not v.get("font_icons_ready"):
                    fails.append(f"{tag}: Material Icons 字型未就緒")

        print("\n=== 檢查結果 ===")
        if fails:
            print(f"✗ {len(fails)} 項未通過：")
            for f in fails:
                print("  - " + f)
        else:
            print("✓ 全部通過（尺寸／無框無底／中心線貼齊／點擊命中／yama 隱藏／無溢出／字型）")

        try:
            urllib.request.urlopen("http://127.0.0.1:9222/json/close/" + tab["id"])
        except Exception:
            pass


if __name__ == "__main__":
    asyncio.run(main())
