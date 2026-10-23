#!/usr/bin/env python3
"""CDP 驗證：手機／平板時鐘顯示 { }（9 欄）＋ w-node-* 已語意化命名。

改動背景（2026-10-12，使用者指示）
  1) 「在手機和平板電腦端，時鐘中的 { } 消失了」→ 改為顯示。
     [成因] { } 沿用 Webflow 原生 h1.is-desktop，於 @media (max-width:991px) 被
     `#bc-brand-stage .is-desktop{display:none}` 隱藏；此時時鐘列是 6 欄且已被
     `15 : 照片 : 19` 佔滿，`}` 的 grid-area:1/8/2/9 在 6 欄格中還會產生隱式欄。
     [修法] ① { } 改 class `.h1.bc-stage-clock-brace` ＋ 語意 id（不再依賴 .is-desktop）
            ② ≤991px 時鐘列改 9 欄 `{ 15 : 照片(跨 3 欄) : 19 }`
            ③ 用 minmax(0,1fr)（純 1fr 會被數字 min-content 撐大、照片被壓縮）
            ④ 數字改各欄置中（與 ≥992px 一致）
     [不動的] 照片佔比：3/9 ＝ 原 2/6 → 照片欄寬逐值不變（768px 220px、390px 111px）。
  2) 「bc_brand_stage_hero.html 的 w-node-_xxxxx CSS 名稱改用組件屬性名稱」→
     bc-brand-stage.css / bc_brand_stage_hero.html / bc_brand_stage.html 三檔同步改名（同名 id 兩頁共用，
     只改一檔會讓 hero 失去 grid 定位）。

檢查項目（index 每個 viewport 各一輪；about 僅 390/768）
  A. 語意化命名：8 個時鐘 id 皆存在（bc-stage-clock / bc-stage-clock-brace-open / -hours /
     -colon-before-minutes / -photos / -colon-after-minutes / -minutes / -brace-close）；
     文件中已無 id 以 w-node- 開頭者。
  B. { } 顯示：兩個括號 computed display != none、visibility == visible、寬 > 0，
     且 class 為 `h1 bc-stage-clock-brace`（不含 is-desktop）。
  C. 排列：依 left 由小到大＝{ / 時 / : / 照片 / : / 分 / }（＝桌面版同一排列）。
  D. 欄數：≤991px → 9 欄；≥992px → 8 欄（桌面原樣）；兩者各欄皆等寬（1fr）。
  E. 幾何：（index 8 個／about 7 個）可見子項兩兩無重疊（>0.5px 才算）、無水平溢出。
     index 多的 1 個＝2026-10-14 新增的天氣元件 #bc-stage-weather（只在首頁 hero）；
     兩兩無重疊這條同時就是「天氣元件不與 { 或其他時鐘項重疊」的守門。
  F. 照片欄寬與佔比：≤991px 照片欄＝3 欄＋2 gap、佔時鐘寬 ≈1/3（＝原 6 欄 2/6 的比例，
     證明尺寸零變動）；≥992px ＝2 欄＋1 gap、佔比 ≈1/4。
  G. about 頁（共用同一份 CSS）：390 / 768 亦顯示 { }、排列相同、無重疊、無溢出。

用法：站台須在 BC_BASE（預設 http://localhost:8081）跑、CDP 瀏覽器須在 9222（見 CDP_SETUP.md）。
      注意：本專案用 cached.Loader，改過 templates/** 後 8081 不會自動換模板 →
      驗證請另開一個新 port 的 server，例如
        (setsid python3 manage.py runserver 127.0.0.1:8090 &) ; \
        BC_BASE=http://127.0.0.1:8090 python3 docs/verify/cdp_verify_clock_braces.py
"""
import asyncio, base64, json, os, urllib.request
import websockets

BASE = os.environ.get("BC_BASE", "http://localhost:8081")
ROOT = "/home/kei/Desktop/betweencoffee_delivery_enhance"
CDP = "http://localhost:9222"

# 期望排列（依 left 由小到大）
EXPECTED_ORDER = ["bc-stage-clock-brace-open", "bc-stage-clock-hours", "bc-stage-clock-colon-before-minutes",
                  "bc-stage-photo-ring", "bc-stage-clock-colon-after-minutes", "bc-stage-clock-minutes",
                  "bc-stage-clock-brace-close"]

# 時鐘幾何：8 個 id、欄數／欄寬、重疊、照片欄寬、文件寬
MEASURE_JS = r"""
(function(){
  var IDS = ['bc-stage-clock','bc-stage-clock-brace-open','bc-stage-clock-hours','bc-stage-clock-colon-before-minutes',
             'bc-stage-photo-ring','bc-stage-clock-colon-after-minutes','bc-stage-clock-minutes','bc-stage-clock-brace-close'];
  var out = {found:{}, box:{}};
  IDS.forEach(function(id){
    var el = document.getElementById(id);
    out.found[id] = !!el;
    if (!el) return;
    var cs = getComputedStyle(el), r = el.getBoundingClientRect();
    out.box[id] = {display: cs.display, vis: cs.visibility, w: r.width, h: r.height,
                   x: r.left, cls: el.className};
  });
  var ft = document.getElementById('bc-stage-clock');
  if (ft) {
    var cs = getComputedStyle(ft);
    var tracks = cs.gridTemplateColumns.split(' ').map(parseFloat).filter(function(v){return !isNaN(v);});
    out.track_count = tracks.length;
    out.track_min = Math.min.apply(null, tracks);
    out.track_max = Math.max.apply(null, tracks);
    out.gap = parseFloat(cs.columnGap) || 0;
    out.clock_w = ft.getBoundingClientRect().width;
    var kids = Array.prototype.slice.call(ft.children).filter(function(e){
      return getComputedStyle(e).display !== 'none'; });
    var rects = kids.map(function(e){ return e.getBoundingClientRect(); });
    out.visible_count = rects.length;
    out.overlaps = [];
    for (var i = 0; i < rects.length; i++) for (var j = i + 1; j < rects.length; j++) {
      var a = rects[i], b = rects[j];
      var ox = Math.min(a.right, b.right) - Math.max(a.left, b.left);
      var oy = Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top);
      if (ox > 0.5 && oy > 0.5) out.overlaps.push([i, j, Math.round(ox)]);
    }
    var items = ft.querySelectorAll('[data-stage-logo="item"]');
    var shown = null;
    for (var k = 0; k < items.length; k++) {
      if (getComputedStyle(items[k]).display !== 'none') { shown = items[k]; break; }
    }
    var im = shown ? shown.querySelector('img') : null;
    out.photo_img_w = im ? im.getBoundingClientRect().width : null;
  }
  out.w_node_ids = document.querySelectorAll('[id^="w-node-"]').length;
  out.doc_scroll_w = document.documentElement.scrollWidth;
  out.inner_w = window.innerWidth;
  return out;
})()
"""


def check(label, ok, detail=""):
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}{(' -> ' + str(detail)) if detail != '' else ''}")
    return bool(ok)


def near(a, b, tol):
    return a is not None and b is not None and abs(a - b) <= tol


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
            r = await send(msg("Runtime.evaluate", {"expression": expr, "returnByValue": True}))
            res = r.get("result", {})
            if res.get("subtype") == "error":
                print("   JS error:", res.get("description"))
            return res.get("value")

        async def goto(url):
            await send(msg("Page.navigate", {"url": url}))
            for _ in range(60):
                await asyncio.sleep(0.25)
                # 必須同時確認 href 已切換：新 document commit 前舊頁 readyState 仍是 complete
                if await evaljs("document.readyState === 'complete' && location.href === "
                                + json.dumps(url)):
                    break
            await asyncio.sleep(1.6)   # 等 bc-brand-stage.js 的 reveal / 輪播初始化

        async def set_viewport(w, h, mobile=False):
            await send(msg("Emulation.setDeviceMetricsOverride",
                           {"width": w, "height": h, "deviceScaleFactor": 1, "mobile": mobile}))
            await asyncio.sleep(0.4)

        async def shot(name):
            res = await send(msg("Page.captureScreenshot", {"format": "png"}))
            data = res.get("data")
            if data:
                path = f"{ROOT}/_verify_clock_braces_{name}.png"
                with open(path, "wb") as f:
                    f.write(base64.b64decode(data))
                print(f"   shot -> {path}")

        async def round_checks(w, h, mobile, name, url, expect_tracks, expect_span):
            """一輪驗證：expect_tracks＝期望欄數、expect_span＝照片跨幾欄。"""
            await set_viewport(w, h, mobile)
            await goto(url)
            await evaljs("(function(){var c=document.getElementById('bc-stage-clock');"
                         "if(c)c.scrollIntoView({block:'center'});})()")
            await asyncio.sleep(1.2)
            m = await evaljs(MEASURE_JS) or {}
            box = m.get("box") or {}
            print(f"\n=== {url} {w}x{h} ({name}) 欄數 {m.get('track_count')} ===")

            # A 語意化命名
            missing = [k for k, v in (m.get("found") or {}).items() if not v]
            failures.append(check("A1 8 個語意化 id 皆存在", not missing, missing or "ok"))
            failures.append(check("A2 無 w-node-* id", m.get("w_node_ids") == 0,
                                  m.get("w_node_ids")))
            # B { } 顯示
            for bid, label in (("bc-stage-clock-brace-open", "B1 { 顯示 (display != none)"),
                               ("bc-stage-clock-brace-close", "B2 } 顯示 (display != none)")):
                b = box.get(bid) or {}
                failures.append(check(label, b.get("display") not in (None, "none"),
                                      b.get("display")))
            for bid, label in (("bc-stage-clock-brace-open", "B3 { visibility:visible 且寬 > 0"),
                               ("bc-stage-clock-brace-close", "B4 } visibility:visible 且寬 > 0")):
                b = box.get(bid) or {}
                failures.append(check(label, b.get("vis") == "visible" and (b.get("w") or 0) > 0,
                                      f"vis={b.get('vis')} w={b.get('w')}"))
            braces = [box.get("bc-stage-clock-brace-open") or {}, box.get("bc-stage-clock-brace-close") or {}]
            failures.append(check("B5 括號 class = 'h1 bc-stage-clock-brace'（不再用 is-desktop）",
                                  all("bc-stage-clock-brace" in b.get("cls", "")
                                      and "is-desktop" not in b.get("cls", "") for b in braces),
                                  [b.get("cls") for b in braces]))
            # C 排列
            order = sorted(EXPECTED_ORDER, key=lambda i: (box.get(i) or {}).get("x", 0))
            failures.append(check("C1 排列 { 時 : 照片 : 分 }", order == EXPECTED_ORDER,
                                  [i.replace("bc-stage-clock-", "") for i in order]))
            # D 欄數／欄寬
            failures.append(check(f"D1 欄數 == {expect_tracks}",
                                  m.get("track_count") == expect_tracks, m.get("track_count")))
            failures.append(check("D2 各欄等寬（1fr，max-min <= 1.5px）",
                                  near(m.get("track_min"), m.get("track_max"), 1.5),
                                  f"{m.get('track_min')} .. {m.get('track_max')}"))
            # E 幾何
            # 2026-10-14：首頁可見子項 7 → 8（新增 #bc-stage-weather 天氣元件；
            # about 頁的真頁尾沒有天氣元件 → 仍為 7）。兩兩無重疊的檢查原樣不變。
            exp_visible = 7 if "about" in url else 8
            failures.append(check(f"E1 可見子項 {exp_visible} 個且兩兩無重疊",
                                  m.get("visible_count") == exp_visible
                                  and not m.get("overlaps"),
                                  f"count={m.get('visible_count')} overlaps={m.get('overlaps')}"))
            failures.append(check("E2 無水平溢出",
                                  (m.get("doc_scroll_w") or 0) <= (m.get("inner_w") or 0) + 1,
                                  f"scrollW {m.get('doc_scroll_w')} vs innerW {m.get('inner_w')}"))
            # F 照片欄寬／佔比
            exp_w = expect_span * (m.get("track_min") or 0) \
                + (expect_span - 1) * (m.get("gap") or 0)
            pw = (box.get("bc-stage-photo-ring") or {}).get("w")
            failures.append(check(f"F1 照片欄 == {expect_span} 欄 + {expect_span - 1} gap",
                                  near(pw, exp_w, 2.0), f"{pw} vs {round(exp_w, 1)}"))
            share = (pw / m.get("clock_w")) if pw and m.get("clock_w") else None
            exp_share = expect_span / expect_tracks
            failures.append(check(f"F2 照片佔時鐘寬 ≈ {expect_span}/{expect_tracks}"
                                  "（原 6 欄為 2/6，比例不變 ⇒ 尺寸零變動）",
                                  share is not None and abs(share - exp_share) <= 0.03,
                                  f"{round(share, 3) if share else None} vs {round(exp_share, 3)}"))
            await shot(name)

        # ===== 首頁：≤991px 9 欄（照片跨 3）／≥992px 8 欄（照片跨 2）=====
        for w, h, mobile, name, tracks, span in ((390, 844, True, "index_390", 9, 3),
                                                 (480, 900, True, "index_480", 9, 3),
                                                 (768, 1024, False, "index_768", 9, 3),
                                                 (991, 900, False, "index_991", 9, 3),
                                                 (992, 900, False, "index_992", 8, 2),
                                                 (1440, 900, False, "index_1440", 8, 2)):
            await round_checks(w, h, mobile, name, f"{BASE}/", tracks, span)

        # ===== about 頁（共用同一份 CSS，預期與首頁一致）=====
        for w, h, mobile, name in ((390, 844, True, "about_390"), (768, 1024, False, "about_768")):
            await round_checks(w, h, mobile, name, f"{BASE}/about/", 9, 3)

    passed = sum(1 for f in failures if f)
    failed = sum(1 for f in failures if not f)
    print(f"\n===== 結果：{'PASS' if failed == 0 else 'FAIL'}（{passed} PASS / {failed} FAIL）=====")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
