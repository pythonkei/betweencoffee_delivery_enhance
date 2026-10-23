#!/usr/bin/env python3
"""以「viewport-only」截圖驗首頁最上方 GUNTE hero（.bc-gunte-hero）與其下方的 BC 動態 hero
（.bc-brand-stage-hero，內含 #bc-brand-stage）。本腳本產出 3 斷點 × 2 張視窗截圖作視覺證據，並印出幾何資訊
（首 section 類別、第一個可見 section、margin-top、footer 元素數、兩個 hero 的 rect）。
（captureBeyondViewport 對 GSAP 釘住／reveal 區段會渲染成空白，故一律用視窗截圖。）
用法：站台須在 http://127.0.0.1:8081 跑、CDP 瀏覽器須在 9222（見 CDP_SETUP.md）。

2026-10-13（使用者指示）：首頁順序反轉 —— GUNTE hero 回到第一屏、BC 動態模組下移到它之後
（`.bc-reviews-section` 另加 hidden）。故第二張截圖由「捲到 GUNTE hero」改為「捲到 BC hero」
（證明 GUNTE hero 在它上方）；`gunteBeforeBg` 這個（舊順序的）旗標改名為語意正確的
`bgAfterGunte`，並追加 `firstVisibleSec`（DOM 第一個 section 已是 hidden 的 reviews 段，
「第一眼看到的第一屏」需以可見性判定）。

2026-10-13 稍後（使用者指示「尺寸改動」＋「載入時就要看得到環形字」）：追加跨斷點證據 ——
`ttlFont`／`ttlStroke`（環形字 computed font-size ＝ 30px、stroke-width ＝ 1.875px，均為 viewBox 單位；
stroke-width 因 Chromium 對 SVG 幾何屬性保留 calc() 字面，另同時輸出原始 `ttlStrokeRaw`）、
`ttlBoxW`／`ttlRenderedFont`（環形字 SVG 框寬與「字級 × 框寬/540」的實際渲染字級）、
`loadButterKing`／`loadIndex`／`loadAriaLabel`／`loadRevealed`
（載入時置中的是 DOM 第 2 張 BUTTER KING、aria-label「2 of 7」且逼 frame 後其環形字確實到過
opacity 1 → Splide start 3 → 1；start 為 0-based，實測 start 2 置中的是「3 of 7」＝第 3 張）＋
`activeSlideIndex`／`activeAriaLabel`／`activeButterKing`／`activeTtlOpacity`／`loadTtlOpacity`
（讀值當下那張，僅診斷 —— autoplay 換張後載入時那張的 opacity 會退回 0）。
⚠ 「載入時那張」必須在逼 frame 前先記下（autoplay interval 5000ms 之後會換張）；讀值前再以
`Page.captureScreenshot` 逼出 frame —— 本機 CDP 的 compositor 不一定產 frame，CSS transition 會停在
pending，computed opacity 會一直是過渡起點的 0。"""
import asyncio, base64, json, urllib.request
import websockets

BASE = "http://localhost:8081"
ROOT = "/home/kei/Desktop/betweencoffee_delivery_enhance"

INFO_JS = (
    "(function(){"
    "var secs=document.querySelectorAll('.bc-page-content > section');"
    "var hero=document.querySelector('.bc-brand-stage-hero');"
    "var bg=document.getElementById('bc-brand-stage');"
    "var g=document.querySelector('.bc-gunte-hero');"
    "var r=function(e){if(!e)return null;var b=e.getBoundingClientRect();"
    "return {top:Math.round(b.top),h:Math.round(b.height)};};"
    "var vis=null;"
    "for(var i=0;i<secs.length;i++){var cs=getComputedStyle(secs[i]);"
    "if(cs.display!=='none'&&cs.visibility!=='hidden'){vis=secs[i];break;}}"
    # 2026-10-13 稍後（使用者指示「尺寸改動」＋「載入時就要看得到環形字」）：
    # 追加環形字尺寸（K5/K6）與載入時置中那張（K7）的跨斷點證據。
    "var ts=document.querySelector('.bc-gunte-hero .hero_slide_item_ttl');"
    "var tcs=(ts&&ts.querySelector('text'))?getComputedStyle(ts.querySelector('text')):null;"
    "var bw=ts?Math.round(ts.getBoundingClientRect().width*100)/100:null;"
    "var active=document.querySelector('.bc-gunte-hero .splide__slide.state-active');"
    "var at=active?active.querySelector('.hero_slide_item_ttl'):null;"
    "var sli=document.querySelectorAll('.bc-gunte-hero .splide__slide');"
    "var actIdx=-1;for(var k=0;k<sli.length;k++){"
    "if(sli[k].classList.contains('state-active')){actIdx=k;break;}}"
    "var loadIdx=(typeof window.__bcHeroLoadIndex==='number')?window.__bcHeroLoadIndex:-1;"
    "var loadSlide=loadIdx>=0?sli[loadIdx]:null;"
    "var loadTtl=loadSlide?loadSlide.querySelector('.hero_slide_item_ttl'):null;"
    "return {y:Math.round(window.scrollY),sh:document.body.scrollHeight,"
    "firstSec:secs.length?secs[0].className.trim():null,"
    "firstVisibleSec:vis?vis.className.trim():null,"
    "secCount:secs.length,"
    "heroMT:hero?getComputedStyle(hero).marginTop:null,"
    "gunteMT:g?getComputedStyle(g).marginTop:null,"
    "footerCount:document.querySelectorAll('footer').length,"
    "bgIdCount:document.querySelectorAll('#bc-brand-stage').length,"
    "bg:r(bg),gunte:r(g),"
    "bgAfterGunte:!!(g&&bg)&&"
    "(g.compareDocumentPosition(bg)&Node.DOCUMENT_POSITION_FOLLOWING)>0,"
    "ttlFont:tcs?tcs.fontSize:null,"
    # Chromium 對 SVG 幾何屬性的 computed style 會保留 calc() 字面（stroke-width → "calc(1.875px)"）
    # → 剝除外層 calc() 後才是可比對的 1.875px（font-size 不受影響，本來就會解析成單一值）。
    "ttlStroke:(tcs?String(tcs.strokeWidth).replace(/^calc\\((.*)\\)$/,'$1'):null),"
    "ttlStrokeRaw:tcs?tcs.strokeWidth:null,"
    "ttlBoxW:bw,ttlRenderedFont:(tcs&&bw)?"
    "Math.round(parseFloat(tcs.fontSize)*bw/540*100)/100:null,"
    "activeButterKing:!!active&&active.textContent.indexOf('BUTTER KING')!==-1,"
    "slideCount:sli.length,activeSlideIndex:actIdx,"
    "activeAriaLabel:active?active.getAttribute('aria-label'):null,"
    "activeTtlOpacity:at?getComputedStyle(at).opacity:null,"
    # 2026-10-13 稍後：載入時置中的那張由 LOAD_JS 記到 window.__bcHeroLoadIndex（逼 frame 前記錄，
    # 所以不受 autoplay 之後換張影響）→ 這裡讀回作為「載入即見環形字」的證據。
    "loadIndex:(typeof window.__bcHeroLoadIndex==='number')?window.__bcHeroLoadIndex:null,"
    "loadAriaLabel:loadSlide?loadSlide.getAttribute('aria-label'):null,"
    "loadButterKing:loadSlide?loadSlide.textContent.indexOf('BUTTER KING')!==-1:null,"
    # loadRevealed＝逼 frame 後「載入時那張」的環形字確實到過 opacity 1（由等待迴圈記錄）。
    # loadTtlOpacity＝讀值當下的值 —— autoplay 換張後那張會退回 0，故僅供診斷。
    "loadRevealed:(window.__bcHeroLoadRevealed===true),"
    "loadTtlOpacity:loadTtl?getComputedStyle(loadTtl).opacity:null};})()"
)

# 2026-10-13 稍後：在「.state-active 一出現、尚未逼 frame」時記錄載入時置中的那一張
# （逼 frame 之後 autoplay 會繼續走動，讀值當下的 state-active 可能已經不是載入時那張）。
LOAD_JS = (
    "(function(){"
    "var sli=document.querySelectorAll('.bc-gunte-hero .splide__slide');"
    "var idx=-1;for(var i=0;i<sli.length;i++){"
    "if(sli[i].classList.contains('state-active')){idx=i;break;}}"
    "if(idx>=0)window.__bcHeroLoadIndex=idx;"
    "var s=idx>=0?sli[idx]:null;var t=s?s.querySelector('.hero_slide_item_ttl'):null;"
    "return {index:idx>=0?idx:null,ariaLabel:s?s.getAttribute('aria-label'):null,"
    "butterKing:s?s.textContent.indexOf('BUTTER KING')!==-1:null,"
    "ttlOpacity:t?getComputedStyle(t).opacity:null};})()"
)


async def main():
    req = urllib.request.Request("http://localhost:9222/json/new?about:blank", method="PUT")
    tab = json.loads(urllib.request.urlopen(req).read())
    async with websockets.connect(tab["webSocketDebuggerUrl"], max_size=200 * 1024 * 1024) as ws:
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

        async def evaljs(e):
            r = await send(msg("Runtime.evaluate", {"expression": e, "returnByValue": True}))
            return r.get("result", {}).get("value")

        for w, h, mobile, name in [(1280, 800, False, "desktop"),
                                   (768, 1024, False, "tablet"),
                                   (390, 844, True, "mobile")]:
            await send(msg("Emulation.setDeviceMetricsOverride",
                           {"width": w, "height": h, "deviceScaleFactor": 1, "mobile": mobile}))
            await send(msg("Page.navigate", {"url": BASE + "/"}))
            # 2026-10-13 稍後：**不用固定 sleep**（原本 sleep 5s）—— 暖機狀態下（compositor 正在
            # 產 frame）Splide autoplay（interval 5000ms）會先換張，之後才記錄就會記到第 2 張之後
            # （實測 tablet／mobile 曾記成 index 4）。改為 navigate 後立刻以 0.1s 間隔輪詢
            # .state-active，一出現就記下「載入時置中的那張」（存 window.__bcHeroLoadIndex）。
            load = {}
            for _ in range(150):
                load = await evaljs(LOAD_JS) or {}
                if load.get("index") is not None:
                    break
                await asyncio.sleep(0.1)
            print(f"   [{name}] 載入時置中: {load}")
            if load and load.get("index") is not None:
                # 逼 frame 直到「載入時記錄的那張」環形字 reveal 完成（opacity 1）、且整個
                # `.hero_slide`（1.5s delay + 0.5s）也已淡入 → 截圖才是有內容的畫面；
                # 一達到就把「環形字確實可見」記到 window.__bcHeroLoadRevealed
                # （讀值當下 autoplay 可能已換張、那張 opacity 會退回 0 → 不能只看 loadTtlOpacity）。
                ready = ("(function(){var s=document.querySelectorAll("
                         "'.bc-gunte-hero .splide__slide')[%d];if(!s)return null;"
                         "var t=s.querySelector('.hero_slide_item_ttl');"
                         "var o=t?getComputedStyle(t).opacity:null;"
                         "if(o==='1')window.__bcHeroLoadRevealed=true;"
                         "var sl=document.querySelector('.bc-gunte-hero .hero_slide');"
                         "var so=sl?getComputedStyle(sl).opacity:null;"
                         "return o==='1'&&so==='1';})()" % load["index"])
                for _ in range(40):
                    if (await evaljs(ready)) is True:
                        break
                    # 同 verify 腳本：captureScreenshot 可能等不到 frame 而卡死 → 包 3 秒逾時。
                    try:
                        await asyncio.wait_for(
                            send(msg("Page.captureScreenshot",
                                     {"format": "jpeg", "quality": 10})), timeout=3)
                    except asyncio.TimeoutError:
                        print(f"   [{name}] captureScreenshot 逾時（3s）→ 續試")
                    await asyncio.sleep(0.25)
            info = await evaljs(INFO_JS)
            print(f"[{name} {w}x{h}] {info}")
            res = await send(msg("Page.captureScreenshot", {"format": "png"}))
            with open(f"{ROOT}/_verify_index_hero_top_{name}.png", "wb") as f:
                f.write(base64.b64decode(res["data"]))
            print(f"   shot -> _verify_index_hero_top_{name}.png")

            # 捲到 BC 動態 hero 頂端，證明 GUNTE hero（第一屏）在它上方、兩者不重疊
            await evaljs("(function(){var b=document.querySelector('.bc-brand-stage-hero');"
                         "if(b)window.scrollTo(0, Math.round(window.scrollY +"
                         " b.getBoundingClientRect().top));})()")
            await asyncio.sleep(2)
            print(f"   bg scroll -> {await evaljs(INFO_JS)}")
            res = await send(msg("Page.captureScreenshot", {"format": "png"}))
            with open(f"{ROOT}/_verify_index_hero_bg_{name}.png", "wb") as f:
                f.write(base64.b64decode(res["data"]))
            print(f"   shot -> _verify_index_hero_bg_{name}.png")
        await send(msg("Page.close"))

asyncio.run(main())
