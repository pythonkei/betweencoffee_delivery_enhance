#!/usr/bin/env python3
"""CDP 驗證：bc-search hover 動畫修復（1280px 桌面）"""
import asyncio, json, urllib.request
import websockets

WS = "http://localhost:9222/json/new?about:blank"


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
        await send(msg("Network.enable"))
        await send(msg("Page.setCacheDisabled", {"cacheDisabled": True}))
        await send(msg("Emulation.setDeviceMetricsOverride",
                       {"width": 1280, "height": 900, "deviceScaleFactor": 1, "mobile": False}))
        await send(msg("Page.navigate", {"url": "http://localhost:8081/"}))
        await asyncio.sleep(4.0)
        await send(msg("Runtime.evaluate",
                       {"expression": "document.querySelector('.bc-search').scrollIntoView({block:'center'});'ok'",
                        "returnByValue": True}))
        await asyncio.sleep(1.5)

        POLL = ("(function(){var l=document.querySelector('.bc-search-link');"
                "var i=document.querySelector('.bc-search-bg-img-01');"
                "return{class:l.className,img1:getComputedStyle(i).transform};})()")
        ok = True

        # 1. mouseenter 動畫時序（驗證 700ms 內完成）
        await send(msg("Runtime.evaluate",
                       {"expression": "document.querySelector('.bc-search-link').dispatchEvent(new MouseEvent('mouseenter',{bubbles:true}));'ok'",
                        "returnByValue": True}))
        print("=== mouseenter 動畫時序 ===")
        for delay in (0.15, 0.35, 0.7, 1.0):
            await asyncio.sleep(delay)
            r = await send(msg("Runtime.evaluate", {"expression": POLL, "returnByValue": True}))
            v = r.get("result", {}).get("value", {})
            print(f"  +{delay:4}s  class={v.get('class')!r}  img1={v.get('img1')}")

        # 2. 長時間 hover：is-on 不應被移除
        await asyncio.sleep(1.2)
        r = await send(msg("Runtime.evaluate", {"expression": POLL, "returnByValue": True}))
        v = r.get("result", {}).get("value", {})
        if "is-on" in v.get("class", "") and "is-out" not in v.get("class", ""):
            print("  ✅ 長時間 hover：is-on 保持、無 is-out")
        else:
            print(f"  ❌ 長時間 hover class 異常: {v.get('class')}")
            ok = False

        # 3. 快速 hover 進出：不應同時存在 is-on + is-out
        rapid = ("(function(){var l=document.querySelector('.bc-search-link');var o=[];"
                 "l.dispatchEvent(new MouseEvent('mouseleave',{bubbles:true}));o.push('leave:'+l.className);"
                 "l.dispatchEvent(new MouseEvent('mouseenter',{bubbles:true}));o.push('enter:'+l.className);"
                 "l.dispatchEvent(new MouseEvent('mouseleave',{bubbles:true}));o.push('leave2:'+l.className);"
                 "return o;})()")
        r = await send(msg("Runtime.evaluate", {"expression": rapid, "returnByValue": True}))
        v = r.get("result", {}).get("value", {})
        print("=== 快速 hover 進出 ===")
        for s in v:
            print(f"  {s}")
            if "is-on is-out" in s:
                print("  ❌ is-on 與 is-out 並存")
                ok = False

        # 4. 1s 後 class 應清除（回到初始狀態）
        await asyncio.sleep(1.2)
        r = await send(msg("Runtime.evaluate", {"expression": POLL, "returnByValue": True}))
        v = r.get("result", {}).get("value", {})
        print(f"  1.2s 後 class={v.get('class')!r}")
        if v.get("class", "").strip() not in ("", "bc-search-link"):
            print("  ⚠️  未回到初始狀態")

        print("\n" + ("✅ bc-search 動畫修復驗證通過" if ok else "❌ 有失敗"))
        try:
            urllib.request.urlopen(f"http://localhost:9222/json/close/{tab['id']}")
        except Exception:
            pass
        return ok


if __name__ == "__main__":
    exit(0 if asyncio.run(main()) else 1)
