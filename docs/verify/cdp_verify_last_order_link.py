#!/usr/bin/env python3
"""CDP 驗證：首頁最後訂單連結 → bean.html 預選（weight / grinding_level）

1. 帶 query 載入 /bean/8/?weight=500g&grinding_level=Medium → 預期按鈕/隱藏欄位/價格全預選
2. 對照組載入 /bean/8/（無 query）→ 維持預設（200g / Non）
"""
import asyncio
import json
import urllib.request

import websockets

WS = "http://localhost:9222/json/new?about:blank"


async def main():
    req = urllib.request.Request(WS, method="PUT")
    tab = json.loads(urllib.request.urlopen(req).read())
    ws_url = tab["webSocketDebuggerUrl"]

    async with websockets.connect(ws_url) as ws:
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

        measure_js = """
        (function(){
          function activeVal(groupId){
            var g = document.getElementById(groupId);
            if (!g) return null;
            var btn = g.querySelector('.bc-option-btn.active');
            return btn ? btn.getAttribute('data-value') : null;
          }
          return {
            url: location.href,
            weightActive: activeVal('weight-group'),
            weightHidden: document.getElementById('weight') ? document.getElementById('weight').value : null,
            grindingActive: activeVal('grinding-group'),
            grindingHidden: document.getElementById('grinding_level') ? document.getElementById('grinding_level').value : null,
            price: document.querySelector('.price') ? document.querySelector('.price').textContent : null
          };
        })()
        """

        async def measure(label):
            r = await send(
                msg("Runtime.evaluate", {"expression": measure_js, "returnByValue": True})
            )
            value = r.get("result", {}).get("value", {})
            print(f"--- {label} ---")
            print(json.dumps(value, ensure_ascii=False, indent=2))
            return value

        # 1. 帶 query：weight=500g & grinding_level=Medium
        await send(
            msg(
                "Page.navigate",
                {"url": "http://localhost:8081/bean/8/?weight=500g&grinding_level=Medium"},
            )
        )
        await asyncio.sleep(3.5)
        v1 = await measure("帶 query（預期 500g / Medium / $119）")

        # 2. 對照組：無 query
        await send(msg("Page.navigate", {"url": "http://localhost:8081/bean/8/"}))
        await asyncio.sleep(3.5)
        v2 = await measure("無 query 對照（預期 200g / Non）")

        # 3. coffee 回歸：帶 query 載入咖啡詳情頁 → 預選應正常
        await send(
            msg(
                "Page.navigate",
                {
                    "url": "http://localhost:8081/coffee/8/?cup_level=Large&milk_level=Extra&strength_level=Extra"
                },
            )
        )
        await asyncio.sleep(3.5)
        coffee_js = """
        (function(){
          function av(g){var el=document.getElementById(g);if(!el)return null;var b=el.querySelector('.bc-option-btn.active');return b?b.getAttribute('data-value'):null;}
          return {
            url: location.href,
            cupActive: av('cup-level-group'),
            cupHidden: document.getElementById('cup_level') ? document.getElementById('cup_level').value : null,
            milkActive: av('milk-level-group'),
            milkHidden: document.getElementById('milk_level') ? document.getElementById('milk_level').value : null,
            strengthActive: av('strength-level-group'),
            strengthHidden: document.getElementById('strength_level') ? document.getElementById('strength_level').value : null
          };
        })()
        """
        r = await send(
            msg("Runtime.evaluate", {"expression": coffee_js, "returnByValue": True})
        )
        v3 = r.get("result", {}).get("value", {})
        print("--- coffee 回歸（預期 Large / Extra / Extra） ---")
        print(json.dumps(v3, ensure_ascii=False, indent=2))
        if (
            v3.get("cupActive") != "Large"
            or v3.get("milkActive") != "Extra"
            or v3.get("strengthActive") != "Extra"
        ):
            print("❌ coffee 預選回歸失敗")
            ok = False
        else:
            print("✅ coffee 預選回歸正常")

        # 4. 判斷
        ok = True
        if v1.get("weightActive") != "500g" or v1.get("weightHidden") != "500g":
            print("❌ weight 預選失敗")
            ok = False
        if v1.get("grindingActive") != "Medium" or v1.get("grindingHidden") != "Medium":
            print("❌ grinding 預選失敗")
            ok = False
        if v1.get("price") not in ("$119", "$119.00"):
            print(f"⚠️  500g 價格顯示 = {v1.get('price')}（預期 $119）")
        if v2.get("weightActive") != "200g" or v2.get("grindingActive") != "Non":
            print("⚠️  對照組預設值異常（預期 200g / Non）")

        print("\n" + ("✅ CDP 驗證全部通過" if ok else "❌ CDP 驗證失敗"))
        try:
            urllib.request.urlopen(f"http://localhost:9222/json/close/{tab['id']}")
        except Exception:
            pass
        return ok


if __name__ == "__main__":
    exit(0 if asyncio.run(main()) else 1)
