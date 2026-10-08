#!/usr/bin/env python3
"""CDP 診斷：.top_art 卡片圖片在各斷點的「顯示／隱藏」（新舊行為對照）

用途
  2026-10-05 使用者指示「.top_art 圖片僅桌面端顯示（行動端／平板端不顯示圖片）」時，
  用來**先查證現況**再動手：以 CSSOM 把新規則 `.bc-top-art .top_art_item_photo
  {display:none}`（位於 bc-top-art.css 的 @media max-width:1024px 內）的 display 改回
  block，即可在「同一頁面、同一斷點」還原改前行為。

輸出（每個斷點印兩行）
  after （改後，規則生效）／before（改前，規則被停用）
  · photo_display：.top_art_item_photo 的 computed display
  · photo / img　　：實際佔位（寬×高；display:none 時為 0×0）
  · photos_visible ：11 張卡中可見的張數
  · currentSrc　　 ：<picture> 實際選中的檔（≤1024 應為 SP 檔）
  · objectFit / img_transition：display:none 下仍可讀（既有驗證斷言不受影響）

前置：Django 於 :8081、Chromium 開 --remote-debugging-port=9222（見 docs/verify 其他 CDP 腳本）。
預期（2026-10-06 復原後）：**所有斷點 → display:block**，≤1024 且 `currentSrc` 為 SP 檔
（1440 → display:block／PC 檔）。若看到 ≤1024 為 `display:none`，代表 2026-10-05 的
「圖片僅桌面端顯示」規則又被加回；本腳本的「before」欄位（CSSOM 停用該規則）此時即為
「恢復顯示」後的結果。
"""
import asyncio
import json
import urllib.request

import websockets

URL = "http://localhost:8081/"

JS = r"""
(function () {
  var art = document.querySelector('.bc-top-art');
  var photos = [].slice.call(art.querySelectorAll('.top_art_item_photo'));
  var imgs = [].slice.call(art.querySelectorAll('.top_art_item_photo > img'));
  function snap(tag) {
    var pr = photos[0].getBoundingClientRect();
    var ir = imgs[0].getBoundingClientRect();
    return {
      tag: tag,
      inner: window.innerWidth,
      photo_display: getComputedStyle(photos[0]).display,
      photo: [Math.round(pr.width), Math.round(pr.height)],
      img_display: getComputedStyle(imgs[0]).display,
      img: [Math.round(ir.width), Math.round(ir.height)],
      photos_visible: photos.filter(function (p) {
        return getComputedStyle(p).display !== 'none';
      }).length,
      currentSrc: (imgs[0].currentSrc || '').split('/').pop(),
      natural: [imgs[0].naturalWidth, imgs[0].naturalHeight],
      objectFit: getComputedStyle(imgs[0]).objectFit,
      img_transition: getComputedStyle(imgs[0]).transitionProperty + ' '
        + getComputedStyle(imgs[0]).transitionDuration
    };
  }
  var out = { after: snap('after') };

  /* 停用本模組的 ≤1024 隱藏規則 → 還原「改前」狀態（可重現的對照） */
  var n = 0, info = null;
  for (var s = 0; s < document.styleSheets.length; s++) {
    var rules;
    try { rules = document.styleSheets[s].cssRules; } catch (e) { continue; }
    for (var r = 0; r < rules.length; r++) {
      var rule = rules[r];
      if (rule.type === 4 && rule.media
          && /max-width:\s*1024px/.test(rule.media.mediaText)) {
        for (var k = 0; k < rule.cssRules.length; k++) {
          if (/^\.bc-top-art \.top_art_item_photo$/.test(rule.cssRules[k].selectorText)) {
            n++;
            info = (document.styleSheets[s].href || '').split('/').pop()
              + ' @' + rule.media.mediaText + ' → ' + rule.cssRules[k].selectorText
              + ' {display:' + rule.cssRules[k].style.display + '}';
            rule.cssRules[k].style.display = 'block';
          }
        }
      }
    }
  }
  out.disabled = n;
  out.rule = info;
  out.before = snap('before');
  return out;
})()
"""


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

        await send(msg("Page.enable"))
        await send(msg("Runtime.enable"))
        for w, h, mob in [(1440, 900, False), (1024, 800, False),
                          (768, 900, True), (390, 844, True)]:
            await send(msg("Emulation.setDeviceMetricsOverride",
                           {"width": w, "height": h, "deviceScaleFactor": 1,
                            "mobile": mob}))
            await send(msg("Page.navigate", {"url": URL}))
            await asyncio.sleep(3.0)
            await ev("window.scrollTo(0,0)")
            await asyncio.sleep(0.2)
            d = await ev(JS)
            print(f"--- {w}px --- rule_disabled={d.get('disabled')} "
                  f"{d.get('rule')}")
            print("   after (改後) :", json.dumps(d["after"], ensure_ascii=False))
            print("   before(改前) :", json.dumps(d["before"], ensure_ascii=False))
        await send(msg("Page.close"))


asyncio.run(main())
