#!/usr/bin/env python3
"""CDP 驗證：coffee_menu 方案 A（bean-mix 共用）多斷點佈局"""
import asyncio, json, urllib.request
import websockets

WS = "http://localhost:9222/json/new?about:blank"

MEASURE = (
    "(function(){"
    "var groups = document.querySelectorAll('.bean-mix-group');"
    "var out = { groups: [] };"
    "groups.forEach(function(g, gi){"
    "  var cells = g.querySelectorAll(':scope > .bean-mix-main, :scope > .bean-mix-sub');"
    "  var gb = g.getBoundingClientRect();"
    "  var info = { group: gi + 1, flip: g.classList.contains('bean-mix-flip'), "
    "    gR: { l: Math.round(gb.left), w: Math.round(gb.width) }, cells: [] };"
    "  cells.forEach(function(c){"
    "    var b = c.getBoundingClientRect();"
    "    var img = c.querySelector('.menu-img img');"
    "    var ib = img ? img.getBoundingClientRect() : null;"
    "    info.cells.push({ cls: c.className, l: Math.round(b.left), t: Math.round(b.top), w: Math.round(b.width), h: Math.round(b.height), "
    "      imgW: ib ? Math.round(ib.width) : null, name: (c.querySelector('h5')||{}).textContent || '' });"
    "  });"
    "  out.groups.push(info);"
    "});"
    "out.viewport = window.innerWidth;"
    "out.hScroll = document.documentElement.scrollWidth - window.innerWidth;"
    "return out;"
    "})()"
)


async def main():
    req = urllib.request.Request(WS, method="PUT")
    tab = json.loads(urllib.request.urlopen(req).read())
    async with websockets.connect(tab["webSocketDebuggerUrl"]) as ws:
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
        await send(msg("Page.setCacheDisabled", {"cacheDisabled": True}))
        ok = True

        for width in (1280, 1080, 768, 375):
            await send(msg("Emulation.setDeviceMetricsOverride",
                           {"width": width, "height": 900, "deviceScaleFactor": 1, "mobile": width <= 768}))
            await send(msg("Page.navigate", {"url": "http://localhost:8081/coffee_menu/"}))
            await asyncio.sleep(3.5)
            r = await send(msg("Runtime.evaluate", {"expression": MEASURE, "returnByValue": True}))
            v = r.get("result", {}).get("value", {})
            print(f"\n===== coffee_menu 方案 A（{width}px）=====")
            print(json.dumps(v, ensure_ascii=False, indent=2))

            groups = v.get("groups", [])
            if len(groups) != 3:
                print(f"  ❌ 組數 {len(groups)}（預期 3）"); ok = False
                continue
            if width == 1280:
                g1, g2, g3 = groups
                # 左右鏡像反轉：組1 flip（大卡右）、組2 非 flip（大卡左）、組3 flip（大卡右）
                if not g1.get("flip") or g2.get("flip") or not g3.get("flip"):
                    print(f"  ❌ flip 分配異常（組1={g1.get('flip')} 組2={g2.get('flip')} 組3={g3.get('flip')}）"); ok = False
                # 組1 大卡中心在右側；組2 大卡中心在左側
                mid1 = g1["gR"]["l"] + g1["gR"]["w"] / 2
                mid2 = g2["gR"]["l"] + g2["gR"]["w"] / 2
                c1 = g1["cells"][0]
                c2 = g2["cells"][0]
                if not (c1["l"] + c1["w"] / 2 > mid1):
                    print("  ❌ 組1 大卡應在右側"); ok = False
                if not (c2["l"] + c2["w"] / 2 < mid2):
                    print("  ❌ 組2 大卡應在左側"); ok = False
                # 組1 第二小卡下移（錯落加大：coffee_menu 7rem）
                if len(g1["cells"]) >= 3:
                    sub2_offset = g1["cells"][2]["t"] - g1["cells"][0]["t"]
                    print(f"  組1 錯落（小卡2 - 大卡 t 差）: {sub2_offset}px")
                    if not (sub2_offset > g1["cells"][1]["t"] - g1["cells"][0]["t"]):
                        print("  ❌ 組1 第二小卡應下移"); ok = False
                # 組3 尾組（2 個）
                if len(g3["cells"]) != 2:
                    print(f"  ⚠️  組3 cell 數 {len(g3['cells'])}（預期 2）")
                # 圖片尺寸
                if abs((c1.get("imgW") or 0) - 340) > 5:
                    print(f"  ⚠️  大卡圖寬 {c1.get('imgW')}（預期 ~340）")
                sub = g1["cells"][1]
                if abs((sub.get("imgW") or 0) - 280) > 5:
                    print(f"  ⚠️  小卡圖寬 {sub.get('imgW')}（預期 ~280）")
            if width == 375:
                xs = set(c["l"] for g in groups for c in g["cells"])
                if len(xs) > 2:
                    print(f"  ⚠️  375px 非單欄（x {sorted(xs)}）")
            if v.get("hScroll", 0) > 0:
                print(f"  ❌ 水平溢出 {v.get('hScroll')}px"); ok = False

        # ===== bean_menu 對照：應維持 4rem translateY（不受 coffee-mix-grid 影響） =====
        await send(msg("Emulation.setDeviceMetricsOverride",
                       {"width": 1280, "height": 900, "deviceScaleFactor": 1, "mobile": False}))
        await send(msg("Page.navigate", {"url": "http://localhost:8081/bean_menu/"}))
        await asyncio.sleep(3.5)
        tr_js = (
            "(function(){var subs=document.querySelectorAll('.bean-mix-main + .bean-mix-sub + .bean-mix-sub');"
            "var o=[];subs.forEach(function(s){var m=getComputedStyle(s).transform;"
            "var y=m==='none'?0:parseFloat(m.split(',')[5]||0);o.push(y);});return o;})()"
        )
        r = await send(msg("Runtime.evaluate", {"expression": tr_js, "returnByValue": True}))
        bean_offsets = r.get("result", {}).get("value", [])
        print(f"bean_menu 小卡2 translateY: {bean_offsets}")
        if bean_offsets and all(abs(o - 64) < 6 for o in bean_offsets):
            print("  ✅ bean_menu 維持 4rem（64px）錯落，未受影響")
        else:
            print("  ⚠️  bean_menu translateY 非 4rem，可能被覆蓋")

        print("\n" + ("✅ CDP 佈局驗證通過" if ok else "❌ 有失敗"))
        try:
            urllib.request.urlopen("http://localhost:9222/json/close/" + tab["id"])
        except Exception:
            pass
        return ok


if __name__ == "__main__":
    exit(0 if asyncio.run(main()) else 1)
