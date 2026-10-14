#!/usr/bin/env python3
"""CDP 驗證：首頁 hero 的照片列（.footer-logo-list）已由 5 張 deco 標誌改為
「7 張咖啡照 ＋ 對應 /coffee/<id>/ 連結」，內容與同頁 #hero_hand_list 逐筆一致。

改動背景（2026-10-09，使用者指示）
  templates/.../partials/bc_hero.html：`.footer-logo-list` 內 5 個 deco SVG 格
  （deco_01/02/05/06/07.svg）換成 7 個
  `<div data-footer-logo="item"><a href="{url coffee hero_coffees.N.id}">`
  `<img src="{{ hero_coffees.N.get_index_image }}" alt="{{ hero_coffees.N.name }}" class="img contain">`
  `</a></div>`，與 index.html `#hero_hand_list`（同為 hero_coffees.0~6）逐字同源。
  static/css/bc-bg-footer.css：新增 `#bc-bg-footer .footer-logo-item a{display:block;width:100%;height:100%;}`
  —— `.img{width:100%;height:100%}` 需 block 父層才有高度，`<a>` 預設 inline 會使圖片高度塌陷。
  about 頁尾來源 partials/bc_bg_footer.html 未同步（仍為 5 張 deco），由 G 項反向守門。

檢查項目（每個 viewport 各一輪；G 僅 /about/）
  A. 結構：`#bc-bg-footer [data-footer-logo="list"]` 內恰 7 個 `[data-footer-logo="item"]`，
     每格恰 1 個 `<a>` ＋ 1 個 `<img class="img contain">`；`#bc-bg-footer` 內已無 `deco_*` 圖片。
  B. 與 #hero_hand_list 同源：筆數相同（7），且 href 清單、src 清單「順序逐一相同」；
     連結皆為 /coffee/<id>/；src 皆為 `_index.png` 咖啡照；alt 皆非空。
  C. 圖片真的載入（分三項；成因見下方註解）：
     C1 顯示中那格（恰 1 格）`complete == true` 且 `naturalWidth > 0`。
     C2 其餘 6 格為 `loading="lazy"` ＋ `display:none`（輪播隱藏格）→ img.complete 恆為
        false 屬正常（Chrome 對 display:none 的 lazy 圖不會走完載入流程），改驗
        `naturalWidth > 0`（照片已抓取解碼，非 404／破圖）。
     C3 7 個 src 互不相同，且以 HTTP 直取皆為 200 ＋ `Content-Type: image/*`。
  D. 輪播初始狀態與幾何：恰 1 格顯示（index 0；其餘 display:none ＋ position:absolute）、
     顯示格 position:relative；顯示格 rect 寬高 > 0；`<a>` computed display == flex
     （2026-10-14 起改 flex column，以容納下方文字）且 a_rect ≈ item_rect（溢差 <= 1px）；
     img 橫向撐滿 `<a>`、高度 = `<a>` 高 − 文字高（±1px）且 > 100px（未塌陷）；
     D9 顯示格 name == img alt、highlight 非空且為品牌金 rgb(196,155,99)；
     D10 文字在照片下方；D11 7 格皆帶文字區（輪播切到任何一格都有名稱）；無水平溢出。
  E. 輪播仍會前進：手動觸發 wrap.click()（同 bc-bg-footer.js 的點擊前進）應前進 1 格、且仍只 1 格顯示。
  F. 連結可點：對「當時顯示中」那格的 `<a>` 中心送 CDP 真實滑鼠事件
     （mousePressed + mouseReleased），應導覽到該 `<a>` 的 href（`/coffee/<id>/`）。
     輪播 interval 於點擊前先清掉以求確定性（否則 5 秒計時器可能在量測與點擊之間換格）。
     F3 在 F2 偵測到新路徑後「輪詢等新 document 就緒」才驗（新頁可能還在解析 <head>，
     `document.body` 仍為 null）；驗 `#section-single-product` 存在、標題逐字等於
     `Between Coffee - <咖啡名>`（coffee.html 的 title 即此格式、alt 即 coffee.name），
     並以 PerformanceNavigationTiming.responseStatus 排除 404。
  G. 反向守門：/about/ 的頁尾（來源 partials/bc_bg_footer.html）仍是 5 格 deco 標誌、
     0 個 /coffee/ 連結 —— 首頁改動未波及 about。

多個 viewport：桌面 1280×800 / 平板 991×900（`calc(184vw/scale)` 尺寸切換帶）/ 平板 768×1024 /
行動 390×844，各存一張 hero 視窗截圖（viewport-only，因 `captureBeyondViewport` 對 GSAP 釘住／
reveal 區段會渲染成空白）。
用法：站台須在 http://127.0.0.1:8081 跑、CDP 瀏覽器須在 9222（見 CDP_SETUP.md）；
      改過 templates/** 後務必先重啟站台（cached.Loader）。
"""
import asyncio, base64, json, re, urllib.error, urllib.request
import websockets

BASE = "http://localhost:8081"
ROOT = "/home/kei/Desktop/betweencoffee_delivery_enhance"
CDP = "http://localhost:9222"

# 首頁量測：結構 / 同源比對 / 幾何 / 載入狀態
MEASURE_JS = r"""
(function(){
  var out = {};
  var root = document.getElementById('bc-bg-footer');
  out.root_found = !!root;
  var list = root ? root.querySelector('[data-footer-logo="list"]') : null;
  out.list_found = !!list;
  var items = list ? Array.prototype.slice.call(list.querySelectorAll('[data-footer-logo="item"]')) : [];
  out.item_count = items.length;
  out.deco_srcs = Array.prototype.slice.call((root || document).querySelectorAll('img[src*="deco_"]'))
      .map(function(i){ return i.getAttribute('src'); });

  var rect = function(e){
    if (!e) return null;
    var b = e.getBoundingClientRect();
    return { x: Math.round(b.left), y: Math.round(b.top),
             w: Math.round(b.width * 100) / 100, h: Math.round(b.height * 100) / 100 };
  };
  var near = function(a, b, tol){
    if (!a || !b) return false;
    return Math.abs(a.w - b.w) <= tol && Math.abs(a.h - b.h) <= tol
        && Math.abs(a.x - b.x) <= tol && Math.abs(a.y - b.y) <= tol;
  };

  out.rows = items.map(function(el){
    var a = el.querySelector('a'), img = el.querySelector('img');
    var csel = getComputedStyle(el), ca = a ? getComputedStyle(a) : null;
    var ir = rect(img), ar = rect(a), er = rect(el);
    /* 2026-10-14：每張照片下方新增「名稱 + highlight」（.bc-series-caption.footer-logo-caption） */
    var cap = el.querySelector('.footer-logo-caption');
    var nm = cap ? cap.querySelector('.bc-series-caption-name') : null;
    var hl = cap ? cap.querySelector('.bc-series-caption-highlight') : null;
    var cr = rect(cap);
    return {
      href: a ? a.getAttribute('href') : null,
      src: img ? img.getAttribute('src') : null,
      alt: img ? (img.getAttribute('alt') || '') : null,
      img_cls: img ? img.className : '',
      a_cls: a ? a.className : '',
      a_display: ca ? ca.display : null,
      cap_found: !!cap, cap_rect: cr, cap_h: cr ? cr.h : 0,
      cap_name: nm ? nm.textContent : null,
      cap_hl: hl ? hl.textContent : null,
      hl_color: hl ? getComputedStyle(hl).color : null,
      hl_fs: hl ? parseFloat(getComputedStyle(hl).fontSize) : 0,
      name_fs: nm ? parseFloat(getComputedStyle(nm).fontSize) : 0,
      img_is_above_cap: (ir && cr) ? (ir.y + ir.h) <= cr.y + 1 : false,
      a_count: el.querySelectorAll('a').length,
      img_count: el.querySelectorAll('img').length,
      display: csel.display, position: csel.position,
      item_rect: er, a_rect: ar, img_rect: ir,
      a_fills_item: near(ar, er, 1), img_fills_a: near(ir, ar, 1),
      img_nw: img ? img.naturalWidth : 0, img_nh: img ? img.naturalHeight : 0,
      img_complete: img ? img.complete : false,
      img_loading: img ? img.getAttribute('loading') : null,
      visible: csel.display !== 'none'
    };
  });
  out.visible_idx = [];
  out.rows.forEach(function(r, i){ if (r.visible) out.visible_idx.push(i); });

  // 同頁基準：#hero_hand_list（GUNTE hero 的咖啡照列）
  var hand = document.getElementById('hero_hand_list');
  out.hand_found = !!hand;
  out.hand_hrefs = hand ? Array.prototype.slice.call(hand.querySelectorAll('a'))
      .map(function(a){ return a.getAttribute('href'); }) : [];
  out.hand_srcs = hand ? Array.prototype.slice.call(hand.querySelectorAll('img'))
      .map(function(i){ return i.getAttribute('src'); }) : [];

  out.doc_scroll_w = document.documentElement.scrollWidth;
  out.inner_w = window.innerWidth;
  return out;
})()
"""

# /about/ 反向守門：真頁尾仍為 deco 標誌
ABOUT_JS = r"""
(function(){
  var root = document.getElementById('bc-bg-footer');
  if (!root) return { found: false };
  var list = root.querySelector('[data-footer-logo="list"]');
  var items = list ? list.querySelectorAll('[data-footer-logo="item"]') : [];
  return {
    found: true,
    item_count: items.length,
    deco_imgs: root.querySelectorAll('img[src*="deco_"]').length,
    coffee_links: root.querySelectorAll('a[href^="/coffee/"]').length
  };
})()
"""

# 點擊測試：先停掉 5 秒輪播以求確定性，回傳當時顯示中那格的 <a> 中心點與 href
CLICK_TARGET_JS = r"""
(function(){
  if (window.__footerLogoInterval) { clearInterval(window.__footerLogoInterval);
                                     window.__footerLogoInterval = null; }
  var root = document.getElementById('bc-bg-footer');
  var items = root.querySelectorAll('[data-footer-logo="item"]');
  for (var i = 0; i < items.length; i++) {
    if (getComputedStyle(items[i]).display === 'none') continue;
    var a = items[i].querySelector('a');
    if (!a) continue;
    var b = a.getBoundingClientRect();
    return { idx: i, href: a.getAttribute('href'),
             x: Math.round(b.left + b.width / 2), y: Math.round(b.top + b.height / 2),
             w: Math.round(b.width), h: Math.round(b.height),
             in_view: b.top >= 0 && b.bottom <= window.innerHeight };
  }
  return null;
})()
"""

# 輪播：清掉舊 interval → 手動觸發 wrap.click() → 回報前／後顯示格
CAROUSEL_JS = r"""
(function(){
  if (window.__footerLogoInterval) { clearInterval(window.__footerLogoInterval);
                                     window.__footerLogoInterval = null; }
  var root = document.getElementById('bc-bg-footer');
  var wrap = root.querySelector('[data-footer-logo="wrap"]');
  var items = root.querySelectorAll('[data-footer-logo="item"]');
  var idx = function(){
    for (var i = 0; i < items.length; i++) {
      if (getComputedStyle(items[i]).display !== 'none') return i;
    }
    return -1;
  };
  var before = idx();
  wrap.click();                       // 同 bc-bg-footer.js：點擊 wrap 前進一格並重啟計時
  var afterClick = idx();
  return { before: before, afterClick: afterClick, count: items.length };
})()
"""

VISIBLE_COUNT_JS = r"""
(function(){
  if (window.__footerLogoInterval) { clearInterval(window.__footerLogoInterval);
                                     window.__footerLogoInterval = null; }
  var n = 0;
  document.querySelectorAll('#bc-bg-footer [data-footer-logo="item"]').forEach(function(el){
    if (getComputedStyle(el).display !== 'none') n++;
  });
  return n;
})()
"""


# 導覽後就緒檢查（F3）：F2 一偵測到 location.pathname 變成 /coffee/<id>/ 就跳出，但那只代表
# 新 document 已 commit，<head> 可能還在解析（document.body == null）→ 直接驗 body 會誤判
# （舊寫法 4 個 viewport 有 3 個 FAIL，而同時印出的 document.title 其實已是正確標題）。
# 因此改為輪詢「body 出現 ＋ 商品頁標記出現 ＋ title 已有值」才驗。
# 另取 PerformanceNavigationTiming.responseStatus 來排除 404（JS 讀不到 HTTP 狀態的替代）：
# 0＝cross-origin／不支援 → 視為未知（不當失敗）。
NAV_READY_JS = r"""
(function(){
  var nav = performance.getEntriesByType('navigation')[0] || {};
  var s = nav.responseStatus;
  if (s === 0 || s === undefined || s === null) s = null;
  var body = document.body;
  return {
    path: location.pathname,
    body: !!body,
    detail: !!document.querySelector('#section-single-product'),   // coffee.html 商品頁專屬 id
    title: document.title || '',
    status: s,
    empty: !body || ((body.innerText || '').trim().length === 0)
  };
})()
"""


def fetch_image(src):
    """以 HTTP 直取圖片，回傳 (status, content_type)。src 可為相對路徑或絕對網址。

    用途（C3）：輪播只有 1 格在顯示，其餘 6 格 display:none ＋ loading="lazy"，
    瀏覽器端 img.complete 不可靠；直接對 7 個 src 發請求可確定「有這個檔、是圖片」。
    """
    url = src if src.startswith("http") else BASE + src
    req = urllib.request.Request(url, headers={"Range": "bytes=0-63"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status, (r.headers.get("Content-Type") or "")
    except urllib.error.HTTPError as e:
        return e.code, ""
    except Exception as e:                                        # noqa: BLE001（連線層錯誤）
        return None, f"ERR {e}"


def check(label, ok, detail=""):
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}{(' -> ' + str(detail)) if detail != '' else ''}")
    return bool(ok)


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
        await send(msg("Network.enable"))
        # 本次同時改了 bc-bg-footer.css（新增 .footer-logo-item a 規則）→ 一律關快取
        await send(msg("Page.setCacheDisabled", {"cacheDisabled": True}))
        await send(msg("Network.setCacheDisabled", {"cacheDisabled": True}))

        async def evaljs(expr):
            r = await send(msg("Runtime.evaluate", {"expression": expr, "returnByValue": True}))
            res = r.get("result", {})
            if res.get("subtype") == "error":
                print("   JS error:", res.get("description"))
            return res.get("value")

        async def goto(url):
            await send(msg("Page.navigate", {"url": url}))
            for _ in range(60):
                await asyncio.sleep(0.25)
                # readyState 之外必須同時確認 href 已切換：Page.navigate 之後、新 document
                # 尚未 commit 前，舊頁的 readyState 仍是 'complete'，只驗它會提早跳出。
                if await evaljs("document.readyState === 'complete' && location.href === "
                                + json.dumps(url)):
                    break
            await asyncio.sleep(1.6)   # 等 bc-bg-footer.js 的 reveal / 輪播初始化

        async def set_viewport(w, h, mobile=False):
            await send(msg("Emulation.setDeviceMetricsOverride",
                           {"width": w, "height": h, "deviceScaleFactor": 1, "mobile": mobile}))
            await asyncio.sleep(0.4)

        async def shot_viewport(name):
            res = await send(msg("Page.captureScreenshot", {"format": "png"}))
            data = res.get("data")
            if data:
                path = f"{ROOT}/_verify_hero_coffee_photos_{name}.png"
                with open(path, "wb") as f:
                    f.write(base64.b64decode(data))
                print(f"   shot -> {path}")

        async def click_at(x, y):
            for t, btns in (("mousePressed", 1), ("mouseReleased", 0)):
                await send(msg("Input.dispatchMouseEvent", {
                    "type": t, "x": x, "y": y, "button": "left", "clickCount": 1,
                    "buttons": btns}))

        # ================= 首頁：各 viewport =================
        for w, h, mobile, name in ((1280, 800, False, "desktop"),
                                   (991, 900, False, "pad991"),
                                   (768, 1024, False, "tablet"),
                                   (390, 844, True, "mobile")):
            await set_viewport(w, h, mobile)
            await goto(f"{BASE}/")
            # 釘牌位於首屏 hero 內；平板／手機 hero 較高，先把 wrap 捲進視野中央再量幾何
            await evaljs("(function(){var c=document.querySelector('#bc-bg-footer "
                         "[data-footer-logo=\"wrap\"]');"
                         "if(c)c.scrollIntoView({block:'center'});})()")
            await asyncio.sleep(1.4)
            m = await evaljs(MEASURE_JS) or {}
            rows = m.get("rows") or []

            print(f"\n=== 首頁 hero 照片列 {w}x{h} ({name}) ===")
            # A 結構
            failures.append(check("A1 #bc-bg-footer 存在", m.get("root_found") is True))
            failures.append(check("A2 [data-footer-logo=list] 存在", m.get("list_found") is True))
            failures.append(check("A3 7 個 data-footer-logo=item", m.get("item_count") == 7,
                                  m.get("item_count")))
            failures.append(check("A4 每格恰 1 個 <a> ＋ 1 個 <img>",
                                  len(rows) == 7
                                  and all(r.get("a_count") == 1 and r.get("img_count") == 1
                                          for r in rows),
                                  [(r.get("a_count"), r.get("img_count")) for r in rows]))
            failures.append(check("A5 每張 img 帶 .img.contain",
                                  bool(rows) and all("img" in (r.get("img_cls") or "")
                                                     and "contain" in (r.get("img_cls") or "")
                                                     for r in rows),
                                  (rows[0].get("img_cls") if rows else None)))
            failures.append(check("A6 已無 deco_* 圖片殘留", not m.get("deco_srcs"),
                                  m.get("deco_srcs")))
            # B 與 #hero_hand_list 同源
            hrefs = [r.get("href") for r in rows]
            srcs = [r.get("src") for r in rows]
            alt_by_href = {r.get("href"): (r.get("alt") or "").strip() for r in rows}
            failures.append(check("B1 #hero_hand_list 存在且 7 筆",
                                  m.get("hand_found") is True
                                  and len(m.get("hand_hrefs") or []) == 7,
                                  len(m.get("hand_hrefs") or [])))
            failures.append(check("B2 href 順序與 #hero_hand_list 逐一相同",
                                  hrefs == (m.get("hand_hrefs") or []), hrefs))
            failures.append(check("B3 src 順序與 #hero_hand_list 逐一相同",
                                  srcs == (m.get("hand_srcs") or []), srcs))
            failures.append(check("B4 7 個連結皆為 /coffee/<id>/",
                                  len(hrefs) == 7
                                  and all(re.fullmatch(r"/coffee/\d+/", x or "") for x in hrefs),
                                  hrefs))
            failures.append(check("B5 7 個 src 皆為 _index.png 咖啡照",
                                  len(srcs) == 7
                                  and all(re.search(r"_index\.png$", x or "") for x in srcs),
                                  srcs))
            failures.append(check("B6 每張 img 皆有 alt",
                                  all((r.get("alt") or "").strip() for r in rows),
                                  [r.get("alt") for r in rows]))
            # C 實際載入
            # 輪播一次只顯示 1 格，其餘 6 格是 display:none ＋ loading="lazy"。Chrome 對
            # display:none 的 lazy 圖不會走完載入流程 → img.complete 恆為 false，
            # 但資源仍已抓取並解出尺寸（實測 4 個 viewport 的 7 張 naturalWidth 皆為 840）。
            # 故「complete」只對顯示中那格要求；隱藏格改驗 naturalWidth > 0（非 404／破圖），
            # 並由 C3 直接以 HTTP 確認 7 個 src 都是可用的圖片檔。
            vis_rows = [r for r in rows if r.get("visible")]
            failures.append(check("C1 顯示中那格（恰 1 格）img complete 且 naturalWidth > 0",
                                  len(vis_rows) == 1
                                  and vis_rows[0].get("img_complete") is True
                                  and (vis_rows[0].get("img_nw") or 0) > 0,
                                  [(r.get("img_complete"), r.get("img_nw")) for r in vis_rows]))
            hid_rows = [r for r in rows if not r.get("visible")]
            failures.append(check('C2 其餘 6 格 loading="lazy" ＋ naturalWidth > 0'
                                  "（display:none 使 complete 恆 false，屬正常）",
                                  len(hid_rows) == 6
                                  and all(r.get("img_loading") == "lazy"
                                          and (r.get("img_nw") or 0) > 0 for r in hid_rows),
                                  [(r.get("display"), r.get("img_loading"), r.get("img_nw"))
                                   for r in hid_rows]))
            statuses = [(s, fetch_image(s)) for s in srcs]
            failures.append(check("C3 7 個 src 互異且 HTTP 直取皆 200 ＋ image/*",
                                  len(srcs) == 7
                                  and len(set(srcs)) == 7
                                  and all(st == 200 and ct.startswith("image/")
                                          for _, (st, ct) in statuses),
                                  [(s, st, ct) for s, (st, ct) in statuses]))
            # D 輪播初始狀態 / 幾何
            vis = m.get("visible_idx") or []
            failures.append(check("D1 恰 1 格顯示（輪播狀態）", vis == [0], vis))
            hidden = [r for r in rows if not r.get("visible")]
            failures.append(check("D2 其餘 6 格 display:none ＋ position:absolute",
                                  len(hidden) == 6
                                  and all(r.get("position") == "absolute" for r in hidden),
                                  [(r.get("display"), r.get("position")) for r in hidden][:3]))
            shown = rows[0] if vis == [0] else (rows[vis[0]] if vis else {})
            failures.append(check("D3 顯示格 position:relative",
                                  shown.get("position") == "relative",
                                  shown.get("position")))
            er, ar, ir = shown.get("item_rect"), shown.get("a_rect"), shown.get("img_rect")
            failures.append(check("D4 顯示格 rect 寬高 > 0",
                                  bool(er) and er["w"] > 0 and er["h"] > 0, er))
            # 2026-10-14：每張照片下方新增「名稱 + highlight」→ <a> 由 block 改為
            # flex column（D5 改寫）、img 不再撐滿 <a>（D7 改寫），並新增 D9–D11。
            failures.append(check("D5 <a> computed display == flex（2026-10-14 起為 flex column）",
                                  shown.get("a_display") == "flex", shown.get("a_display")))
            failures.append(check("D6 <a> 撐滿顯示格（rect 溢差 <= 1px）",
                                  shown.get("a_fills_item") is True, f"a {ar} vs item {er}"))
            cap_h = shown.get("cap_h") or 0
            failures.append(check("D7 img 橫向撐滿 <a>、高度 = <a> 高 − 文字高（±1px）且 > 100px",
                                  bool(ir) and bool(ar)
                                  and abs(ir["w"] - ar["w"]) <= 1
                                  and abs(ir["h"] - (ar["h"] - cap_h)) <= 1
                                  and ir["h"] > 100,
                                  f"img {ir} / a {ar} / 文字高 {cap_h}"))
            failures.append(check("D8 無水平溢出",
                                  (m.get("doc_scroll_w") or 0) <= (m.get("inner_w") or 0) + 1,
                                  f"scrollW {m.get('doc_scroll_w')} vs innerW {m.get('inner_w')}"))
            failures.append(check("D9 顯示格文字：name == img alt、highlight 非空且為品牌金",
                                  shown.get("cap_found") is True
                                  and bool((shown.get("cap_name") or "").strip())
                                  and shown.get("cap_name") == shown.get("alt")
                                  and bool((shown.get("cap_hl") or "").strip())
                                  and shown.get("hl_color") == "rgb(196, 155, 99)",
                                  (shown.get("cap_name"), shown.get("cap_hl"),
                                   shown.get("hl_color"))))
            failures.append(check("D10 文字在照片下方（照片底 <= 文字頂 + 1px）",
                                  shown.get("img_is_above_cap") is True,
                                  (ir, shown.get("cap_rect"))))
            failures.append(check("D11 輪播 7 格皆帶文字區（每格切到時都有名稱/highlight）",
                                  len(rows) == 7
                                  and all(r.get("cap_found") is True
                                          and (r.get("cap_name") or "").strip()
                                          and (r.get("cap_hl") or "").strip() for r in rows),
                                  [r.get("cap_found") for r in rows]))
            await shot_viewport(name)

            # E 輪播前進（點 wrap → 前進一格）
            c = await evaljs(CAROUSEL_JS) or {}
            failures.append(check("E1 點 wrap 後輪播前進 1 格（mod 7）",
                                  c.get("before") in range(7)
                                  and c.get("afterClick") == ((c.get("before") or 0) + 1) % 7,
                                  c))
            failures.append(check("E2 前進後仍只有 1 格顯示",
                                  (await evaljs(VISIBLE_COUNT_JS)) == 1,
                                  await evaljs(VISIBLE_COUNT_JS)))

            # F 連結可點（先停 interval 求確定性）
            t = await evaljs(CLICK_TARGET_JS)
            failures.append(check("F1 取得顯示中連結的中心點",
                                  bool(t) and t.get("w", 0) > 0 and t.get("h", 0) > 0, t))
            if t and t.get("w", 0) > 0:
                # 無條件先把該格捲到視野中央再重新取點：固定 navbar / 浮動鈕可能蓋住
                # 視口上緣，直接用原座標送真實滑鼠事件會命中覆蓋層而非 <a>。
                await evaljs("(function(){var el=document.querySelectorAll('#bc-bg-footer "
                             "[data-footer-logo=\"item\"]')[" + str(t["idx"]) + "];"
                             "if(el)el.scrollIntoView({block:'center'});})()")
                await asyncio.sleep(0.6)
                t2 = await evaljs(CLICK_TARGET_JS)
                if t2 and t2.get("w", 0) > 0:
                    t = t2
                await click_at(t["x"], t["y"])
                path = None
                for _ in range(48):
                    await asyncio.sleep(0.25)
                    path = await evaljs("location.pathname")
                    if path and path.startswith("/coffee/"):
                        break
                failures.append(check("F2 點照片導覽到該筆 /coffee/<id>/",
                                      path == t.get("href"), f"{path} vs {t.get('href')}"))
                # F3：F2 一偵測到 pathname 改變就跳出，但那只代表新 document 已 commit，
                # <head> 可能還在解析（document.body == null）→ 直接驗 body 會誤判 FAIL
                # （舊寫法 4 個 viewport 有 3 個 FAIL，而同時印出的 title 其實已正確）。
                # 改為輪詢等「body ＋ 商品頁標記 ＋ title」皆就緒，再用 alt（＝ coffee.name）
                # 推出的預期標題逐字比對（coffee.html 的 <title> 即 "Between Coffee - <名稱>"）。
                exp_name = alt_by_href.get(path or "", "")
                exp_title = f"Between Coffee - {exp_name}" if exp_name else ""
                nav = {}
                for _ in range(40):
                    nav = await evaljs(NAV_READY_JS) or {}
                    if nav.get("body") and nav.get("detail") and nav.get("title"):
                        break
                    await asyncio.sleep(0.25)
                failures.append(check("F3 導覽後為該筆商品頁（200、非 404、標題正確）",
                                      nav.get("body") is True
                                      and nav.get("detail") is True
                                      and nav.get("status") in (200, None)
                                      and bool(exp_name)
                                      and nav.get("title") == exp_title,
                                      f"status={nav.get('status')} title={nav.get('title')!r} "
                                      f"expected={exp_title!r} detail={nav.get('detail')}"))
            else:
                failures.append(check("F2 點照片導覽到該筆 /coffee/<id>/", False, "no target"))
                failures.append(check("F3 導覽後為該筆商品頁（200、非 404、標題正確）",
                                      False, "no target"))

        # ================= /about/：反向守門 =================
        await set_viewport(1280, 800)
        await goto(f"{BASE}/about/")
        await evaljs("window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(1.2)
        a = await evaljs(ABOUT_JS) or {}
        print("\n=== /about/ 真頁尾反向守門 (1280x800) ===")
        failures.append(check("G1 /about/ 仍有 #bc-bg-footer", a.get("found") is True))
        failures.append(check("G2 /about/ 頁尾仍為 5 格 deco 標誌", a.get("item_count") == 5,
                              a.get("item_count")))
        failures.append(check("G3 /about/ 頁尾仍有 5 張 deco_* 圖片", a.get("deco_imgs") == 5,
                              a.get("deco_imgs")))
        failures.append(check("G4 /about/ 頁尾無 /coffee/ 連結（改動未波及）",
                              a.get("coffee_links") == 0, a.get("coffee_links")))

        await send(msg("Page.close"))

    total = len(failures)
    bad = sum(1 for f in failures if not f)
    print(f"\n===== 合計 {total} 項，PASS {total - bad}，FAIL {bad} =====")
    return bad


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))

