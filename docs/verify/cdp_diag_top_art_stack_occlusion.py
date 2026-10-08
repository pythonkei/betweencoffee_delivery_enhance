#!/usr/bin/env python3
"""CDP 診斷：首頁 .top_art sticky 堆疊卡片「文案遮蔽性」目視／量化對照

用途：驗證 2026-10-05 追加的兩項 ≤1024 規則確實生效，並產出可目視的對照截圖。
  A. 圖片僅桌面端顯示（.bc-top-art .top_art_item_photo{display:none}）
  B. 卡片不透明底色（.bc-top-art .top_art_item{background-color:var(--bc-bg)}）
  ⚠ 2026-10-06 復原：A、B 兩條規則已隨「行動／平板恢復顯示圖片」一併刪除 ⇒ 本腳本
    現在量到的「出貨狀態」＝有圖片、卡片透明（原站 1:1）；下方的「刪掉 B 規則」A/B
    對照在 B 不存在時即為無變化（可作為「已無該規則」的確認），若要重現當初的對照，
    需先用 CSSOM 動態加回 A、B 兩條規則再跑。歷史量測結果見
    betweencoffee_memory_bank/04_SYSTEM_STATE.md 的追加 ⑲／② 說明。

做法（不注入任何探針 CSS，量測的就是正式出貨狀態）：
  * 1024×800：捲到模組 +2200／+3200，量
      - 11 張卡「文案框」兩兩幾何重疊對數（相鄰卡文案框本來就會重疊，這是
        sticky 堆疊設計；PC 有圖時亦然，故此數字僅供對照）
      - 3×3 取樣點 hit-test：哪幾張卡的文案框位在最上層
      - 首張卡 computed background-color（期望 rgb(14,14,14)）與 photo display
    再用 CSSOM 把 B 規則刪掉（= 未套配套前）重跑同一組量測並截圖 → 出貨／對照兩張圖。
  * 1440×900：確認 PC 仍是透明底色（rgba(0,0,0,0)）且圖片可見（原站 1:1 未被影響）。

執行前提：Django 跑在 127.0.0.1:8081、Chromium 已開 remote debugging 9222：
  /home/kei/.pyenv/versions/3.8.13/bin/python3 docs/verify/cdp_diag_top_art_stack_occlusion.py
輸出：stdout 量測值；截圖 /tmp/final_1024_off{2200,3200}.png（出貨狀態）、
      /tmp/final_1024_off{2200,3200}_nogb.png（停用不透明底的對照）、
      /tmp/final_1440_off3200.png（PC）。
實測結果（2026-10-05）：出貨狀態 1024 只有當前卡文案可見、清晰；對照（停用底色）
      後段同時可見 4 張卡文案互相疊字；PC 1440 仍為透明底＋圖片 834×451。
"""
import asyncio
import base64
import json
import urllib.request

import websockets

URL = "http://localhost:8081/"

JS_MEASURE = r"""
(function () {
  var art = document.querySelector('.bc-top-art');
  var wraps = [].slice.call(art.children).filter(function (el) {
    return el.classList.contains('top_art_item_wrap');
  });
  /* 實際可見性：對每張卡的文案框取 3x3 取樣點做 hit-test，
     命中元素屬於「該卡自己的文案框」才算該卡文案真的被看見 */
  var occ = wraps.map(function (w, i) {
    var tw = w.querySelector('.top_art_item_text_wrap');
    var r = tw.getBoundingClientRect();
    var total = 0, hits = 0;
    for (var gx = 1; gx <= 3; gx++) {
      for (var gy = 1; gy <= 3; gy++) {
        var x = r.left + r.width * gx / 4;
        var y = r.top + r.height * gy / 4;
        if (x < 0 || x > window.innerWidth || y < 0 || y > window.innerHeight) continue;
        total++;
        var el = document.elementFromPoint(x, y);
        if (el && (tw === el || tw.contains(el))) { hits++; }
      }
    }
    return { n: i, samples: total, hits: hits, visible: hits > 0 };
  });
  var rows = wraps.map(function (w, i) {
    var t = w.querySelector('.top_art_item_text_wrap').getBoundingClientRect();
    return { n: i, text: [Math.round(t.top), Math.round(t.bottom),
                          Math.round(t.left), Math.round(t.right)] };
  });
  var pairs = [];
  for (var a = 0; a < rows.length; a++) {
    for (var b = a + 1; b < rows.length; b++) {
      var A = rows[a].text, B = rows[b].text;
      var vo = Math.min(A[1], B[1]) - Math.max(A[0], B[0]);
      var ho = Math.min(A[3], B[3]) - Math.max(A[2], B[2]);
      if (vo > 5 && ho > 5) { pairs.push([rows[a].n, rows[b].n, vo, ho]); }
    }
  }
  var item = wraps[0].querySelector('.top_art_item');
  var photo = wraps[0].querySelector('.top_art_item_photo');
  var img = wraps[0].querySelector('img');
  return {
    inner: window.innerWidth, scrollY: Math.round(window.scrollY),
    overlap_pairs: pairs,
    visible_boxes: occ.filter(function (o) { return o.visible; }).map(function (o) { return o.n; }),
    occlusion: occ,
    item_bg: getComputedStyle(item).backgroundColor,
    photo_display: getComputedStyle(photo).display,
    img_display: getComputedStyle(img).display,
    img_current: img.currentSrc.split('/').pop(),
    img_rect: [Math.round(img.getBoundingClientRect().width),
               Math.round(img.getBoundingClientRect().height)]
  };
})()
"""


JS_TOGGLE = r"""
(function (on) {
  var sheets = document.styleSheets;
  for (var s = 0; s < sheets.length; s++) {
    var rules;
    try { rules = sheets[s].cssRules; } catch (e) { continue; }
    for (var i = 0; i < rules.length; i++) {
      var r = rules[i];
      var cond = r.conditionText || (r.media && r.media.mediaText) || '';
      if (r.type === 4 && /1024px/.test(cond)) {
        for (var j = 0; j < r.cssRules.length; j++) {
          var rr = r.cssRules[j];
          if (rr.selectorText === '.bc-top-art .top_art_item' &&
              rr.style && rr.style.backgroundColor) {
            if (!on) {                       /* 停用：還原成「未套用底色」 */
              window.__bgStore = { media: r, css: rr.cssText, index: j };
              r.deleteRule(j);
              return 'disabled:' + rr.style.backgroundColor;
            }
            return 'already-on';
          }
        }
      }
    }
  }
  /* 重新套用（插回原本位置） */
  if (window.__bgStore) {
    var st = window.__bgStore;
    st.media.insertRule(st.css, st.index);
    window.__bgStore = null;
    return 'restored';
  }
  return 'not-found';
})
"""


def show(m, tag=""):
    print(f"  {tag}scrollY={m['scrollY']} 幾何重疊文字對數={len(m['overlap_pairs'])} "
          f"｜實際可見文案卡={m['visible_boxes']}（共 {len(m['occlusion'])} 張）")
    print(f"    item_bg={m['item_bg']} photo={m['photo_display']} "
          f"img={m['img_display']} img_rect={m['img_rect']} "
          f"currentSrc={m['img_current']}")


async def main():
    req = urllib.request.Request("http://localhost:9222/json/new?about:blank",
                                 method="PUT")
    tab = json.loads(urllib.request.urlopen(req).read())
    ws_url = tab["webSocketDebuggerUrl"]
    async with websockets.connect(ws_url, max_size=80 * 1024 * 1024) as ws:
        mid = 1

        def msg(m, p=None):
            nonlocal mid
            o = {"id": mid, "method": m, "params": p or {}}
            mid += 1
            return o

        async def send(m):
            await ws.send(json.dumps(m))
            while True:
                r = json.loads(await ws.recv())
                if r.get("id") == m["id"]:
                    return r.get("result", {})

        async def ev(e):
            r = await send(msg("Runtime.evaluate",
                               {"expression": e, "returnByValue": True}))
            return r.get("result", {}).get("value")

        async def shot(path):
            r = await send(msg("Page.captureScreenshot", {"format": "png"}))
            open(path, "wb").write(base64.b64decode(r["data"]))
            print("   saved", path)

        await send(msg("Page.enable"))
        await send(msg("Runtime.enable"))

        for w, h, mobile, offs in ((1024, 800, False, (2200, 3200)),
                                   (1440, 900, False, (3200,))):
            await send(msg("Emulation.setDeviceMetricsOverride",
                           {"width": w, "height": h, "deviceScaleFactor": 1,
                            "mobile": mobile}))
            await send(msg("Page.navigate", {"url": URL}))
            await asyncio.sleep(3.5)
            top = await ev("(function(){var a=document.querySelector('.bc-top-art');"
                           "return Math.round(a.getBoundingClientRect().top+window.scrollY);})()")
            print(f"=== {w}x{h} (art top={top}) ===")
            for off in offs:
                await ev(f"window.scrollTo(0, {top + off})")
                await asyncio.sleep(1.0)
                m = await ev(JS_MEASURE)
                show(m, "【出貨狀態】")
                await shot(f"/tmp/final_{w}_off{off}.png")
                if w == 1024:      # 對照：以 CSSOM 停用不透明底色（= 未套配套前）
                    t = await ev(f"({JS_TOGGLE})(false)")
                    print(f"    [對照] 停用不透明底 → {t}")
                    await asyncio.sleep(0.8)
                    m2 = await ev(JS_MEASURE)
                    show(m2, "【停用底色（對照）】")
                    await shot(f"/tmp/final_{w}_off{off}_nogb.png")
                    t = await ev(f"({JS_TOGGLE})(true)")
                    print(f"    [回復] 重新套用不透明底 → {t}")
                    await asyncio.sleep(0.6)
        await send(msg("Page.close"))


asyncio.run(main())
