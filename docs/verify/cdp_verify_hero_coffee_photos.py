#!/usr/bin/env python3
"""CDP 驗證：首頁照片格（#bc-clock-photos）＝ GUNTE hero 的「環形照片列」（與 hero 同一顆大圓）。

2026-10-14（使用者指示）：照片格由「7 格輪播（一次只顯示一張）」改為與 GUNTE hero 共用的
環形照片列 —— 同一組 class（.hero_hand / .hero_hand_list / .hero_hand_item）、同一份
static/css/bc-hand-ring.css 與 static/js/bc-hand-ring.js，並由 **hero 的 Splide index** 驅動
（bc-gunte-hero.js 的 updateSlideStates → BC_HAND_RING.goAll）：圓盤旋轉 idx × −25°、
-current 那張放大、其餘 0.5 倍。
2026-10-14 稍後（使用者指正「展示咖啡動畫不是 footer-logo-list-wrap，區域太小了，動畫展示是
使用整個頁面的。參考 hero_hand」）：照片格的 --circle-radius 改回 **hero 的 100vw** —— 同一個
25° 步進下左右鄰居落在 ±0.423R ＝ ±42vw ⇒ 扇形橫跨整個頁面寬、鄰居落在頁面兩緣；照片格與
照片區不再裁切（唯一的裁切框是頁面層級的 `#bc-bg-footer{overflow:hidden}`，與 hero 由
.bc-gunte-hero{overflow:hidden} 裁切是同一件事）；照片寬改取「照片區高 ÷ 咖啡照比例
1.429」＝ 336vw/ratio（≤991px 126vw/ratio）⇒ current 那張上下剛好貼齊照片區、不壓到文字列
（2026-10-15 放大前為 276 ÷ 1.429 ＝ 193vw/ratio）。
本檔取代原「7 張咖啡照輪播」版的斷言。

2026-10-15（使用者指示）：「桌機（≥992px）的咖啡照片放大到 1440 時 336×480」——只改 ≥992px：
  .footer-logo-cell 上下內距歸零（留白吸收進照片區）＋ .footer-logo-list 高 276vw/ratio →
  480vw/ratio ＋ --bc-hand-img-w 193vw/ratio → 336vw/ratio（＝480 ÷ 1.4286）。
  逐斷點照片尺寸：1905 = 444.5×635.0、1440 = 336.0×480.0、1280 = 298.7×426.7、
  992 = 231.5×330.7；≤991px 全部逐值不變（含 cell 內距，E7）。時鐘列的頂端、#bc-bg-footer、
  .grid.is-footer 的文件座標完全不動，只有列高向下長（@1440 419.6 → 529.6），下方內容等量下移。

檢查項目（A–F 每個 viewport 各一輪；G＝/about/ 反向守門；H＝互動）
  A 結構：`#bc-clock-photos` 內有 .hero_hand > #bc-clock-hand-list > 恰 7 個 .hero_hand_item；
    --angle 依序 -90/-65/-40/-15/10/35/60；每個含 <a href="/coffee/N/"> ＋ <img>（非 lazy）；
    文字列 [data-bc-ring-caption] 內恰 7 筆 [data-bc-ring-caption-item]；
    首頁已無舊輪播 hook（[data-footer-logo="item"] / "wrap"）；
    照片格與照片區 overflow = visible（扇形必須離開格子才能「用整個頁面」）、
    #bc-bg-footer overflow = hidden（頁面層級的裁切框）。
  B 與 hero 同源：7 筆 href / src / --angle 與 #hero_hand_list 逐筆相同。
  C 索引同步：-current 索引 == hero 的 Splide index（以 #hero_nav 的 -current 與
    .state-active 的 aria-label「k of 7」雙重換算）== BC_HAND_RING.index() == 文字列 -current；
    圓盤 inline transform == rotate(idx × −25deg)（讀 inline style，不受過渡中影響）；
    照片格的 --circle-radius 與 hero 逐值相同（皆 100vw ＝同一顆整頁大圓）。
  D 環形幾何：7 張圖到圓盤中心的距離 ≈ 半徑（±2px，證明確實「在圓上」）；半徑 = 100vw；
    current 那張 scale 1、其餘 0.5；current 的水平中心 == 照片格中心（±2px）；
    current 寬 == 336vw/ratio（D7；@1440 = 336×480、@1905 = 444.5×635）；
    current 上下剛好填滿照片區（img 底緣 == 文字列頂端 ±2px ⇒ 不壓文字）；
    實質可見 2–3 張且必為 current ± 1（循環，端點索引時只有一側鄰居）；
    左右鄰居的水平中心在圓心 ±0.423R（±2%）且落在頁面兩緣（≤20% / ≥80% 頁寬）＝整頁扇形；
    鄰居 rect 與文字列 rect 無交集；無水平溢出（＝扇形被 #bc-bg-footer 的 overflow:hidden 裁掉）；
    揭示跑完後照片格無殘留 clip-path（＝側邊鄰居不被 .footer-logo-cell 的 inset(0%) 切掉）。
    ⚠ 量測前會先「捲到照片格」——該 cell 在首屏之外，不捲的話 data-reveal="clip-down" 永不觸發，
      就會驗到揭示前的狀態（那正是上述 clip-path 裁切問題的藏身處）。
  E 零回歸：首頁不再有 5 秒輪播（window.__footerLogoInterval 為 null）；
    .footer-logo-cell 寬/高、.footer-logo-list 高、.footer-logo-caption 高、
    時鐘列（.footer-time）高 逐值比對（基準表 EXPECT，±1px；≥992px 用「改動後」值、
    ≤991px 用「改動前」值 ⇒ 同時守住兩件事）；E7 專門守「改動只限 ≥992px」——桌機 cell
    上下內距必須是 0，≤991px 必須仍是 u-24 + 14px / u-24（逐值與改動前相同）；
    E8 守連動關係「照片寬 ＝ 照片區高 ÷ 1.4286」（放大／縮小後仍必須成立）。
  F 圖片：7 個 src 皆 HTTP 200 且 Content-Type 為 image/*（環形圖不看 img.complete）。
  G /about/ 反向守門：真頁尾仍為 5 格 deco 的 5 秒輪播（[data-footer-logo="item"] == 5、
    __footerLogoInterval 有值）、該頁沒有 #bc-clock-hand-list / .hero_hand。
  H 互動（僅第一個 viewport）：點 #hero_nav 第 k 顆 → hero、照片格、文字列三者都跟到 k，
    且圓盤 inline transform == rotate(−25k deg)。

用法：站台須在 http://localhost:8081 跑、CDP 瀏覽器須在 9222（見 CDP_SETUP.md）。
"""
import asyncio
import json
import os
import time
import urllib.error
import urllib.request

import websockets

BASE = os.environ.get("BC_BASE", "http://localhost:8081")
CDP = "http://localhost:9222"

# 改動前實測（2026-10-14，改用環形照片列之前；CDP 1905/1280/991/768/390 × 900）：
#   viewport: (.footer-logo-cell 寬, .footer-logo-cell 高, .footer-logo-list 高,
#              .footer-logo-caption 高, .footer-time 高)
# .footer-logo-list 的高度＝改動前的「照片高度」（原 .footer-logo-item 高 − 文字高）：
# 因為環形照片列是 absolute、不佔流內高度，照片區高度改由 .footer-logo-list 撐起，
# 文字區再接在它後面。
# ⚠ 2026-10-15（使用者指示）：「桌機（≥992px）咖啡照片放大到 1440 時 336×480」⇒ 1905/1280
#   兩列的 cell 高／list 高已被 EXPECT 取代（本表只留 991/768/390 三列作「≤991px 逐值不變」
#   的回歸基準；桌機改動前值＝ 1905: 534.53/365.13、1280: 380.02/245.33）。
BEFORE = {
    1905: (381.00, 534.53, 365.13, 49.59, 534.53),
    1280: (256.00, 380.02, 245.33, 49.59, 380.02),
    991: (278.28, 631.81, 453.89, 42.89, 631.81),
    768: (214.53, 502.42, 351.75, 42.89, 502.42),
    390: (106.47, 279.14, 178.63, 38.89, 279.14),
}

# 改動後期望值（2026-10-15 實測）＝ cell 內距 0 ＋ 照片區 480vw/ratio ＋ 文字區 49.59（≥992px）：
#   @1440 = 480.00／336.0×480.0（★使用者指定的目標斷點）、@1905 = 635.00／444.5×635.0、
#   @1280 = 426.66／298.7×426.7、@992 = 330.66／231.5×330.7
#   （1440/992 未列入 VIEWPORTS，僅供手動量測對照）。
# ≤991px 三列沿用 BEFORE（＝與改動前逐值相同）；E7 另驗 cell 內距與斷點歸屬。
EXPECT = dict(BEFORE)
EXPECT.update({
    1905: (381.00, 684.59, 635.00, 49.59, 684.59),
    1440: (288.00, 529.59, 480.00, 49.59, 529.59),
    1280: (256.00, 476.26, 426.66, 49.59, 476.26),
    992: (198.39, 380.25, 330.66, 49.59, 380.25),
})

# ---------------------------------------------------------------------------
# 量測 JS：單次 evaluate 原子讀取（避免「過渡中」與「autoplay 換張」造成前後不一致）
# ---------------------------------------------------------------------------
PROBE_JS = r"""
(function(){
  function R(e){ if(!e) return null; var b=e.getBoundingClientRect();
    return {x:+b.x.toFixed(2),y:+b.y.toFixed(2),w:+b.width.toFixed(2),h:+b.height.toFixed(2),
            right:+b.right.toFixed(2),bottom:+b.bottom.toFixed(2)}; }
  function C(e){ if(!e) return null; var b=e.getBoundingClientRect();
    return {x:+(b.x+b.width/2).toFixed(2), y:+(b.y+b.height/2).toFixed(2)}; }
  function cur(arr){ var k=-1; arr.forEach(function(e,i){ if(e.classList.contains('-current')) k=i; }); return k; }
  function v(e,n){ return e?getComputedStyle(e).getPropertyValue(n).trim():null; }
  function p(e,k){ return e?getComputedStyle(e)[k]:null; }

  var cell=document.getElementById('bc-clock-photos');
  var cellBox=cell?cell.querySelector('.footer-logo-cell'):null;
  var area=cell?cell.querySelector('.footer-logo-list'):null;
  var hand=cell?cell.querySelector('.hero_hand'):null;
  var list=document.getElementById('bc-clock-hand-list');
  var items=list?Array.prototype.slice.call(list.querySelectorAll('.hero_hand_item')):[];
  var caption=cell?cell.querySelector('.footer-logo-caption'):null;
  var caps=Array.prototype.slice.call(
      document.querySelectorAll('#bc-clock-photos [data-bc-ring-caption-item]'));
  var heroList=document.getElementById('hero_hand_list');
  var heroItems=heroList?Array.prototype.slice.call(heroList.querySelectorAll('.hero_hand_item')):[];
  var slides=document.querySelectorAll('.bc-gunte-hero .splide__slide');
  var active=document.querySelector('.bc-gunte-hero .splide__slide.state-active');
  var actIdx=-1;
  Array.prototype.forEach.call(slides,function(s,i){ if(s.classList.contains('state-active')) actIdx=i; });
  var navBtns=Array.prototype.slice.call(document.querySelectorAll('#hero_nav button'));
  var lc=C(list), radiusPx=list?(parseFloat(getComputedStyle(list).width)/2):null;

  var itemsOut=items.map(function(el){
    var im=el.querySelector('img'), a=el.querySelector('a'), ci=C(im), dist=null;
    if(ci&&lc){ dist=+Math.sqrt(Math.pow(ci.x-lc.x,2)+Math.pow(ci.y-lc.y,2)).toFixed(2); }
    return {angle:v(el,'--angle'), cur:el.classList.contains('-current'),
            cls:el.className, rect:R(el), img:R(im), imgCenter:ci, dist:dist,
            scale:p(im,'scale'), href:a?a.getAttribute('href'):null,
            loading:im?im.getAttribute('loading'):null,
            src:im?im.getAttribute('src'):null, alt:im?im.getAttribute('alt'):null};
  });
  var heroOut=heroItems.map(function(el){
    var im=el.querySelector('img'), a=el.querySelector('a');
    return {angle:v(el,'--angle'), href:a?a.getAttribute('href'):null,
            src:im?im.getAttribute('src'):null};
  });

  var section=document.getElementById('bc-bg-footer');
  var clipChain=[];
  (function(){
    var el=hand, stop=section;
    while(el && el!==stop && el!==document.documentElement){
      var c=getComputedStyle(el);
      if((c.clipPath && c.clipPath!=='none')||(c.webkitClipPath && c.webkitClipPath!=='none')
         || c.overflow!=='visible')
        clipChain.push([String(el.className||el.id), 'clip='+c.clipPath, 'ov='+c.overflow]);
      el=el.parentElement;
    }
  })();
  return {
    cellBox:R(cellBox), area:R(area), captionBox:R(caption),
    clockRow:R(document.querySelector('.footer-time')),
    section:R(section), sectionOverflow:p(section,'overflow'),
    innerW:window.innerWidth, docScrollW:document.documentElement.scrollWidth,
    cellOverflow:p(cellBox,'overflow'), areaOverflow:p(area,'overflow'),
    cellClip:p(cellBox,'clipPath'), areaClip:p(area,'clipPath'), clipChain:clipChain,
    cellPadTop:v(cellBox,'padding-top'), cellPadBottom:v(cellBox,'padding-bottom'),
    itemCount:items.length, items:itemsOut,
    capCount:caps.length, capCur:cur(caps),
    capText:(caps.length&&cur(caps)>=0)?caps[cur(caps)].textContent.replace(/\s+/g,' ').trim():null,
    handCount:document.querySelectorAll('#bc-clock-photos .hero_hand').length,
    handCur:cur(items), ready:hand?hand.classList.contains('is-ready'):null,
    listInline:list?list.style.transform:null, listComputed:p(list,'transform'),
    radiusVar:v(hand,'--circle-radius'), imgWVar:v(hand,'--bc-hand-img-w'), radiusPx:radiusPx,
    heroCount:heroItems.length, hero:heroOut, heroCur:cur(heroItems),
    navCur:cur(navBtns), slideCount:slides.length, actIdx:actIdx,
    ariaLabel:active?active.getAttribute('aria-label'):null,
    ringIndex:(window.BC_HAND_RING&&window.BC_HAND_RING.index)?window.BC_HAND_RING.index():null,
    ringCount:(window.BC_HAND_RING&&window.BC_HAND_RING.count)?window.BC_HAND_RING.count():null,
    interval:window.__footerLogoInterval?true:false,
    legacyItems:document.querySelectorAll('#bc-clock-photos [data-footer-logo="item"]').length,
    legacyWrap:!!document.querySelector('#bc-clock-photos [data-footer-logo="wrap"]')
  };
})()
"""

# 停掉 GUNTE hero 的 autoplay（Splide pauseOnHover）→ 量測期間 index 不再跳動。
PAUSE_JS = ("(function(){var s=document.querySelector('.bc-gunte-hero .splide');"
            "if(!s) return false;"
            "['mouseenter','mouseover'].forEach(function(t){"
            "s.dispatchEvent(new MouseEvent(t,{bubbles:true}));});return true;})()")

READY_JS = ("(function(){return !!(document.getElementById('bc-clock-hand-list')"
            "&&document.querySelector('#bc-clock-photos .hero_hand.is-ready')"
            "&&document.querySelector('.bc-gunte-hero .splide__slide.state-active'));})()")

# 捲到照片格正中（讓 GSAP 的進場揭示（data-reveal="clip-down"）真的觸發）
SCROLL_CELL_JS = ("(function(){var e=document.getElementById('bc-clock-photos');"
                  "if(!e) return null;var r=e.getBoundingClientRect();"
                  "window.scrollTo(0, Math.round(window.scrollY + r.top - "
                  "(window.innerHeight - r.height)/2));return Math.round(window.scrollY);})()")

# 本機 CDP 的 rAF 被節流：GSAP 的 lagSmoothing 把每次 tick 的推進夾在 33ms ⇒ DUR_L 1.2s 的
# clip-down 揭示實測要 16–36 秒（真瀏覽器 1.2s）。本腳本只需要「揭示結束後的穩態」，故量測前
# 把 GSAP 全域時間軸加速（timeScale 100）→ 下一個 tick 就跑到終點（含 onComplete）。
# 其餘 GSAP 動畫（文字揭示等）同樣被推到結束狀態＝它們本來就會到的狀態，不影響任何斷言。
SPEED_GSAP_JS = ("(function(){if(window.gsap&&window.gsap.globalTimeline){"
                 "window.gsap.globalTimeline.timeScale(100);return true;}return false;})()")

# .footer-logo-cell（data-reveal="clip-down"）目前的 clip-path；揭示跑完且被釋放時為 'none'
CELL_CLIP_JS = ("(function(){var e=document.querySelector('#bc-clock-photos .footer-logo-cell');"
                "return e?getComputedStyle(e).clipPath:null;})()")

NAV_CLICK_JS = ("(function(){var b=document.querySelectorAll('#hero_nav button');"
                "if(b.length<=%d)return null;b[%d].click();return b.length;})()")

ABOUT_JS = r"""
(function(){
  var root=document.getElementById('bc-bg-footer');
  return {
    items: document.querySelectorAll('#bc-bg-footer [data-footer-logo="item"]').length,
    list: !!document.querySelector('#bc-bg-footer [data-footer-logo="list"]'),
    hand: document.querySelectorAll('#bc-bg-footer .hero_hand').length,
    ringList: document.querySelectorAll('#bc-clock-hand-list, #bc-bg-footer .hero_hand_list').length,
    interval: window.__footerLogoInterval?true:false,
    isFooter: !!root&&root.querySelectorAll('footer').length>0
  };
})()
"""


def fetch_image(src):
    """以 HTTP 直取圖片，回傳 (status, content_type)（src 可為相對路徑或絕對網址）。"""
    url = src if src.startswith("http") else BASE + src
    req = urllib.request.Request(url, headers={"Range": "bytes=0-63"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status, (r.headers.get("Content-Type") or "")
    except urllib.error.HTTPError as e:
        return e.code, ""
    except Exception as e:                                       # noqa: BLE001
        return None, f"ERR {e}"


def check(label, ok, detail=""):
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}{(' -> ' + str(detail)) if detail != '' else ''}")
    return bool(ok)


def overlaps(a, b, eps=0.5):
    if not a or not b:
        return False
    return (a["x"] < b["right"] - eps and a["right"] > b["x"] + eps
            and a["y"] < b["bottom"] - eps and a["bottom"] > b["y"] + eps)


def cover_ratio(a, b):
    """a（項目 rect）落在 b（裁切框）內的面積比例 —— 用來排除貼邊的 1px 細邊。"""
    if not a or not b:
        return 0.0
    w = max(0.0, min(a["right"], b["right"]) - max(a["x"], b["x"]))
    h = max(0.0, min(a["bottom"], b["bottom"]) - max(a["y"], b["y"]))
    if w <= 0 or h <= 0:
        return 0.0
    return (w * h) / max(a["w"] * a["h"], 1e-6)


def pxnum(s):
    """'54px' → 54.0；無法解析回 None（供 E7 比較 computed padding）。"""
    try:
        return float(str(s).replace("px", "").strip())
    except (TypeError, ValueError):
        return None


def exp_radius(w):
    """照片格的 --circle-radius 期望值（px）：與 hero 同值 ＝ 100vw（1vw = w/100 px）。"""
    return float(w)


def exp_img_w(w):
    """照片格的 --bc-hand-img-w 期望值（px）：照片區高（≥992px 480vw/ratio，≤991px 180vw/ratio）
    ÷ 咖啡照實際比例 1.4286（840×1200）＝ 336vw/ratio ／ 126vw/ratio。
    （2026-10-15 放大前為 276vw/ratio ⇒ 193vw/ratio。）"""
    return w * (336.0 / 14.4) / 100 if w >= 992 else w * (126.0 / 3.93) / 100


ANGLES = ["-90", "-65", "-40", "-15", "10", "35", "60"]
VIEWPORTS = [(1905, 900), (1280, 800), (991, 800), (768, 900), (390, 800)]


async def main():
    req = urllib.request.Request(f"{CDP}/json/new?about:blank", method="PUT")
    tab = json.loads(urllib.request.urlopen(req).read())
    failures = []

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
        await send(msg("Page.setCacheDisabled", {"cacheDisabled": True}))

        async def evaljs(expr):
            r = await send(msg("Runtime.evaluate", {"expression": expr, "returnByValue": True}))
            res = r.get("result", {})
            if res.get("subtype") == "error":
                print("   JS error:", res.get("description"))
            return res.get("value")

        async def frame():
            await asyncio.wait_for(send(msg("Page.captureScreenshot",
                                            {"format": "jpeg", "quality": 5})), 30)

        async def goto(url):
            await send(msg("Page.navigate", {"url": url}))
            for _ in range(80):
                await asyncio.sleep(0.25)
                if await evaljs("document.readyState === 'complete' && location.href === "
                                + json.dumps(url)):
                    break
            for _ in range(40):
                await asyncio.sleep(0.25)
                if await evaljs(READY_JS):
                    break
            await frame()
            await asyncio.sleep(0.4)

        async def wait_reveal(timeout=20.0):
            """等到 .footer-logo-cell 的 clip-down 揭示跑完並被釋放（clip-path = none）。
               ⚠ 本機 rAF 被節流 → 先加速 GSAP 時間軸（見 SPEED_GSAP_JS），再每 0.4s 截圖逼 frame
                 輪詢；真瀏覽器不需要這招（1.2s 自然跑完）。"""
            await evaljs(SPEED_GSAP_JS)
            t0 = time.time()
            while time.time() - t0 < timeout:
                await frame()
                await asyncio.sleep(0.4)
                if await evaljs(CELL_CLIP_JS) == "none":
                    return True
            return False

        async def measure():
            """捲到照片格（讓 GSAP 的進場揭示真的跑完 → .footer-logo-cell 的 clip-path 被釋放）
               → 暫停 hero autoplay → 等圓盤過渡（1.2s）跑完 → 原子讀取。
               ⚠ 不捲的話揭示永不觸發（該 cell 在首屏之外），就會驗到「揭示前」的狀態
                 —— 那正是「側邊鄰居被 clip-path:inset(0%) 切掉」這個 bug 藏身之處。"""
            await evaljs(SCROLL_CELL_JS)
            await asyncio.sleep(0.6)
            await wait_reveal()
            await evaljs(PAUSE_JS)
            await asyncio.sleep(1.5)
            await frame()
            await asyncio.sleep(0.2)
            return await evaljs(PROBE_JS)

        async def set_viewport(w, h, mobile=False):
            await send(msg("Emulation.setDeviceMetricsOverride",
                           {"width": w, "height": h, "deviceScaleFactor": 1, "mobile": mobile}))
            await asyncio.sleep(0.4)

        # ================= per-viewport（A–F） =================
        for idx, (w, h) in enumerate(VIEWPORTS):
            await set_viewport(w, h)
            await goto(f"{BASE}/")
            m = await measure()
            print(f"\n=== {w}x{h} 首頁 ===")
            if not m:
                failures.append(check(f"{w}: PROBE_JS 有回傳值", False))
                continue
            items = m.get("items") or []
            bfw, bfh, bfl, bfc, bfr = EXPECT.get(w, (0, 0, 0, 0, 0))

            # ---------- A 結構 ----------
            failures.append(check("A1 #bc-clock-hand-list 內恰 7 個 .hero_hand_item",
                                  m.get("itemCount") == 7, m.get("itemCount")))
            failures.append(check("A2 --angle 依序 -90/-65/-40/-15/10/35/60",
                                  [i.get("angle") for i in items] == ANGLES,
                                  [i.get("angle") for i in items]))
            failures.append(check("A3 每格都有 <a href=/coffee/N/> ＋ <img src/alt>",
                                  len(items) == 7
                                  and all((i.get("href") or "").startswith("/coffee/")
                                          and (i.get("src") or "").strip()
                                          and (i.get("alt") or "").strip()
                                          for i in items),
                                  [(i.get("href"), (i.get("src") or "")[-18:]) for i in items[:2]]))
            failures.append(check("A4 .hero_hand.is-ready（模組已註冊）",
                                  m.get("ready") is True and m.get("handCount") == 1,
                                  (m.get("ready"), m.get("handCount"))))
            failures.append(check("A5 文字列 = 7 筆 [data-bc-ring-caption-item]、有 -current、文字非空",
                                  m.get("capCount") == 7 and (m.get("capCur") or -1) >= 0
                                  and bool((m.get("capText") or "").strip()),
                                  (m.get("capCount"), m.get("capCur"), m.get("capText"))))
            failures.append(check("A6 首頁已無舊輪播 hook（data-footer-logo item/wrap）",
                                  m.get("legacyItems") == 0 and m.get("legacyWrap") is False,
                                  (m.get("legacyItems"), m.get("legacyWrap"))))
            # A7：整頁扇形的關鍵 —— 照片格／照片區必須讓照片離開格子，唯一的裁切框是頁面層級的
            #     #bc-bg-footer{overflow:hidden}（與 hero 由 .bc-gunte-hero 裁切是同一件事）。
            failures.append(check("A7 照片格／照片區 overflow = visible、#bc-bg-footer = hidden",
                                  m.get("cellOverflow") == "visible"
                                  and m.get("areaOverflow") == "visible"
                                  and m.get("sectionOverflow") == "hidden",
                                  (m.get("cellOverflow"), m.get("areaOverflow"),
                                   m.get("sectionOverflow"))))
            # A8：環上 7 張只有 2–3 張在畫面內（其餘依角度落在畫面外）→ lazy 會讓「輪到置中時
            #     還沒載入」而出現空窗；7 張一律 eager（與 index.html #hero_hand_list 同寫法）。
            failures.append(check("A8 7 張照片皆非 loading=lazy（整頁扇形下必須 eager）",
                                  [i.get("loading") for i in items] == [None] * 7,
                                  [i.get("loading") for i in items]))

            # ---------- B 與 hero 同源 ----------
            hero = m.get("hero") or []
            failures.append(check("B1 #hero_hand_list 亦為 7 筆",
                                  m.get("heroCount") == 7, m.get("heroCount")))
            failures.append(check("B2 href 順序與 #hero_hand_list 逐筆相同",
                                  [i.get("href") for i in items] == [i.get("href") for i in hero],
                                  [(i.get("href"), j.get("href")) for i, j in zip(items, hero)][:2]))
            failures.append(check("B3 src 順序與 #hero_hand_list 逐筆相同",
                                  [i.get("src") for i in items] == [i.get("src") for i in hero]))
            failures.append(check("B4 --angle 順序與 #hero_hand_list 逐筆相同",
                                  [i.get("angle") for i in items] == [i.get("angle") for i in hero]))

            # ---------- C 索引同步 ----------
            hc = m.get("heroCur")
            failures.append(check("C1 hero 的 Splide index 一致（nav -current / state-active / aria）",
                                  hc is not None and hc >= 0
                                  and m.get("navCur") == hc and m.get("actIdx") == hc
                                  and m.get("ariaLabel") == f"{hc + 1} of {m.get('slideCount')}",
                                  (m.get("navCur"), m.get("actIdx"), m.get("ariaLabel"))))
            failures.append(check("C2 照片格 cur == 文字列 cur == BC_HAND_RING.index() == hero index",
                                  hc is not None and m.get("handCur") == hc
                                  and m.get("capCur") == hc and m.get("ringIndex") == hc,
                                  (m.get("handCur"), m.get("capCur"), m.get("ringIndex"), hc)))
            failures.append(check(f"C3 圓盤 inline transform == rotate({(hc or 0) * -25}deg)",
                                  m.get("listInline") == f"rotate({(hc or 0) * -25}deg)",
                                  m.get("listInline")))
            failures.append(check("C4 兩個環都註冊在 BC_HAND_RING（hero ＋ 照片格）",
                                  m.get("ringCount") == 2, m.get("ringCount")))
            failures.append(check("C5 --circle-radius 與 hero 同值（100vw ＝同一顆整頁大圓）",
                                  (m.get("radiusVar") or "") == "100vw",
                                  (m.get("radiusVar"), m.get("imgWVar"))))

            # ---------- D 環形幾何 ----------
            rp = m.get("radiusPx") or 0
            failures.append(check(f"D1 半徑 = {exp_radius(w):.1f}px ±2（100vw ＝ hero 同值）",
                                  abs(rp - exp_radius(w)) <= 2, round(rp, 2)))
            dists = [i.get("dist") for i in items]
            failures.append(check("D2 7 張圖的中心都落在同一個圓上（距圓心 = 半徑 ±2px）",
                                  len(dists) == 7 and all(d is not None and abs(d - rp) <= 2
                                                          for d in dists),
                                  [round(d, 1) if d else d for d in dists]))
            cur_i = m.get("handCur")
            scales = [i.get("scale") for i in items]
            failures.append(check("D3 current 那張 img scale=1、其餘 0.5",
                                  cur_i is not None and scales[cur_i] == "1"
                                  and all(s == "0.5" for k, s in enumerate(scales) if k != cur_i),
                                  scales))
            curc = (items[cur_i].get("imgCenter") or {}) if cur_i is not None else {}
            ccx = (m.get("cellBox") or {}).get("x", 0) + (m.get("cellBox") or {}).get("w", 0) / 2
            failures.append(check("D4 current 那張的水平中心 == 照片格中心（±2px）",
                                  abs(curc.get("x", 0) - ccx) <= 2,
                                  (curc.get("x"), round(ccx, 2))))
            cap_box = m.get("captionBox")
            area_box = m.get("area")
            sec_box = m.get("section")
            n_it = len(items)
            cur_img = (items[cur_i].get("img") or {}) if cur_i is not None else {}
            # D5：照片寬取「照片區高 ÷ 咖啡照比例 1.4286」⇒ current 那張上下剛好貼齊照片區，
            #     底緣就落在文字列頂端（不再靠裁切，是尺寸本來就剛好）。
            failures.append(check("D5 current 貼齊照片區：底緣 == 文字列頂端（±2px）⇒ 不壓文字",
                                  bool(cap_box) and abs(cur_img.get("bottom", 0)
                                                        - cap_box.get("y", 0)) <= 2,
                                  (round(cur_img.get("bottom", 0), 2), (cap_box or {}).get("y"))))
            # D6：整頁扇形 ⇒ 實質可見 2–3 張、且必為 current ± 1（循環；索引在端點時只有一側
            #     鄰居落在畫面內）。「實質可見」＝圖 rect 落在頁面裁切框（#bc-bg-footer）內的
            #     面積 ≥25%（用 viewport 座標比較，結果與捲動位置無關）。
            vis = [k for k, i in enumerate(items)
                   if cover_ratio(i.get("img"), sec_box) >= 0.25]
            near = cur_i is not None and all(
                min((k - cur_i) % n_it, (cur_i - k) % n_it) <= 1 for k in vis)
            failures.append(check("D6 畫面內實質可見 2–3 張、且必為 current ± 1（循環）",
                                  2 <= len(vis) <= 3 and bool(near),
                                  [(k, round(cover_ratio(items[k].get("img"), sec_box), 2))
                                   for k in range(n_it)]))
            iw = (items[cur_i].get("img") or {}).get("w", 0) if cur_i is not None else 0
            failures.append(check(f"D7 current 那張 img 寬 = {exp_img_w(w):.1f}px ±1"
                                  f"（＝照片區高 ÷ 1.4286）",
                                  abs(iw - exp_img_w(w)) <= 1, round(iw, 2)))
            # D8：扇形橫跨整個頁面 —— 鄰居的水平中心距圓心（＝current 那張的中心）≈ 0.4226R
            #     （25° 步進的弦長）、且必須落在頁面兩緣（≤20% / ≥80% 頁寬）；鄰居 rect 也已
            #     離開照片格（＝證明不是「縮在格子裡」）。
            cx_cell = (m.get("cellBox") or {}).get("x", 0)
            cx_cell_r = cx_cell + (m.get("cellBox") or {}).get("w", 0)
            nb = [k for k in vis if cur_i is not None and k != cur_i]
            nb_bad = []
            for k in nb:
                c = items[k].get("imgCenter") or {}
                off = abs(c.get("x", 0) - (curc.get("x") or 0))
                if abs(off - 0.4226 * rp) > 0.02 * rp:
                    nb_bad.append((k, "dist", round(off, 1), round(0.4226 * rp, 1)))
                if sec_box:
                    if not (c.get("x", 0) <= sec_box.get("x", 0) + 0.2 * sec_box.get("w", 0)
                            or c.get("x", 0) >= sec_box.get("x", 0) + 0.8 * sec_box.get("w", 0)):
                        nb_bad.append((k, "edge", round(c.get("x", 0), 1)))
                r = items[k].get("img") or {}
                if r.get("x", 0) > cx_cell - 10 and r.get("right", 0) < cx_cell_r + 10:
                    nb_bad.append((k, "inside-cell", (r.get("x"), r.get("right"))))
            failures.append(check("D8 鄰居在 ±0.4226R 且落在頁面兩緣、rect 已離開照片格（整頁扇形）",
                                  bool(nb) and not nb_bad, nb_bad or nb))
            # D9：7 張 rect 都不得與文字列相交（照片變大，但橫向距離更遠 ⇒ 名稱/highlight 不被壓）
            fail_over = [(k, items[k].get("img")) for k in range(n_it)
                         if overlaps(items[k].get("img"), cap_box, eps=1.0)]
            failures.append(check("D9 7 張照片的 rect 皆不與文字列交集",
                                  not fail_over, fail_over[:2]))
            # D10：扇形超出頁面的部分由 #bc-bg-footer 的 overflow:hidden 裁掉 ⇒ 無水平捲軸
            failures.append(check("D10 無水平溢出（頁面層級裁切生效）",
                                  (m.get("docScrollW") or 0) <= (m.get("innerW") or 0) + 1,
                                  (m.get("docScrollW"), m.get("innerW"))))
            # D11：環形照片列到 #bc-bg-footer 之間不得有任何「裁切框」——
            #      overflow 已由 A7 驗過（照片格／照片區 visible）；這裡驗另一條容易漏的路：
            #      .footer-logo-cell 的 data-reveal="clip-down" 會被 GSAP 留下 clip-path:inset(0%)，
            #      那會把側邊鄰居整張切掉（bc-bg-footer.js 已在揭示跑完後釋放）。
            clip_chain = m.get("clipChain") or []
            failures.append(check("D11 揭示後照片格無殘留 clip-path（側邊鄰居不被格子切掉）",
                                  m.get("cellClip") == "none" and not clip_chain,
                                  (m.get("cellClip"), clip_chain)))

            # ---------- E 零回歸／桌機改動範圍 ----------
            failures.append(check("E1 首頁不再有 5 秒輪播（__footerLogoInterval 為 null）",
                                  m.get("interval") is False, m.get("interval")))
            cb = m.get("cellBox") or {}
            ab = m.get("area") or {}
            cp = cap_box or {}
            cr = m.get("clockRow") or {}
            scope = "改動後（≥992px 照片放大）" if w >= 992 else "改動前逐值不變（≤991px 未動）"
            failures.append(check(f"E2 .footer-logo-cell 寬 {bfw}px ±1（{scope}）",
                                  abs(cb.get("w", 0) - bfw) <= 1, cb.get("w")))
            failures.append(check(f"E3 .footer-logo-cell 高 {bfh}px ±1（時鐘列高度；{scope}）",
                                  abs(cb.get("h", 0) - bfh) <= 1, cb.get("h")))
            failures.append(check(f"E4 .footer-logo-list 高 {bfl}px ±1（＝照片區高；{scope}）",
                                  abs(ab.get("h", 0) - bfl) <= 1, ab.get("h")))
            failures.append(check(f"E5 .footer-logo-caption 高 {bfc}px ±1（文字區高度；{scope}）",
                                  abs(cp.get("h", 0) - bfc) <= 1, cp.get("h")))
            failures.append(check(f"E6 .footer-time 高 {bfr}px ±1（整條時鐘列；{scope}）",
                                  abs(cr.get("h", 0) - bfr) <= 1, cr.get("h")))
            # E7：2026-10-15 的改動「只限 ≥992px」—— 桌機把 cell 的上下內距歸零（留白吸收進
            #     照片區、照片頂緣上移到列的頂端），≤991px 必須仍是 u-24 + 14px / u-24
            #     （＝逐值與改動前相同）。這是本批改動最容易外溢到平板的破口。
            if w >= 992:
                e7_pt, e7_pb, e7_why = 0.0, 0.0, "≥992px 歸零＝留白吸收進照片區"
            else:
                e7_pb = (24.0 * w / 100.0) / 3.93
                e7_pt, e7_why = e7_pb + 14.0, "≤991px 未動（u-24 + 14px / u-24）"
            pt_got, pb_got = pxnum(m.get("cellPadTop")), pxnum(m.get("cellPadBottom"))
            failures.append(check(
                f"E7 .footer-logo-cell 內距 = {e7_pt:.2f}/{e7_pb:.2f}px ±1（{e7_why}）",
                pt_got is not None and pb_got is not None
                and abs(pt_got - e7_pt) <= 1 and abs(pb_got - e7_pb) <= 1,
                (m.get("cellPadTop"), m.get("cellPadBottom"))))
            # E8：照片寬永遠＝照片區高 ÷ 1.4286（放大／縮小的連動關係；改動前後、全斷點皆成立）
            ratio = (ab.get("h", 0) / iw) if iw else 0
            failures.append(check("E8 照片區高 ÷ current 照片寬 = 1.4286 ±0.002（兩者同步）",
                                  abs(ratio - 1.42857) <= 0.002, round(ratio, 5)))

            # ---------- F 圖片 HTTP ----------
            bad_src = []
            for i in items:
                st, ct = fetch_image(i.get("src") or "")
                if st != 200 or not ct.startswith("image/"):
                    bad_src.append((i.get("href"), i.get("src"), st, ct))
            failures.append(check("F1 7 個 src 皆 HTTP 200 且 Content-Type image/*",
                                  not bad_src, bad_src[:2]))

            # ---------- H 互動（僅第一個 viewport） ----------
            if idx == 0:
                print(f"\n=== {w}x{h} 互動：點 #hero_nav ===")
                await evaljs(NAV_CLICK_JS % (4, 4))
                await asyncio.sleep(0.6)
                m2 = await measure()
                failures.append(check("H1 點 nav[4] 後 hero index == 4",
                                      m2.get("heroCur") == 4, m2.get("heroCur")))
                failures.append(check("H2 照片格 / 文字列 / 圓盤 都跟到 4",
                                      m2.get("handCur") == 4 and m2.get("capCur") == 4
                                      and m2.get("listInline") == "rotate(-100deg)",
                                      (m2.get("handCur"), m2.get("capCur"), m2.get("listInline"))))
                failures.append(check("H3 文字列顯示第 5 筆咖啡（name/highlight 非空）",
                                      bool((m2.get("capText") or "").strip()),
                                      m2.get("capText")))
                await evaljs(NAV_CLICK_JS % (0, 0))
                await asyncio.sleep(0.6)
                m3 = await measure()
                failures.append(check("H4 點 nav[0]（rewind 回第一張）→ 三方都跟到 0",
                                      m3.get("heroCur") == 0 and m3.get("handCur") == 0
                                      and m3.get("capCur") == 0
                                      and m3.get("listInline") == "rotate(0deg)",
                                      (m3.get("heroCur"), m3.get("handCur"), m3.get("capCur"),
                                       m3.get("listInline"))))

        # ================= G /about/ 反向守門 =================
        await set_viewport(1280, 800)
        await goto(f"{BASE}/about/")
        await asyncio.sleep(0.5)
        a = await evaljs(ABOUT_JS)
        print("\n=== /about/ 反向守門 ===")
        failures.append(check("G1 /about/ 真頁尾仍為 5 格 deco 輪播",
                              bool(a) and a.get("items") == 5 and a.get("list") is True,
                              (a or {}).get("items")))
        failures.append(check("G2 /about/ 沒有環形照片列（.hero_hand / #bc-clock-hand-list）",
                              bool(a) and a.get("hand") == 0 and a.get("ringList") == 0,
                              (a or {}).get("hand")))
        failures.append(check("G3 /about/ 的 5 秒輪播仍在跑（__footerLogoInterval 有值）",
                              bool(a) and a.get("interval") is True, (a or {}).get("interval")))
        failures.append(check("G4 /about/ #bc-bg-footer 內仍是 <footer>（標籤不同、樣式相同）",
                              bool(a) and a.get("isFooter") is True, (a or {}).get("isFooter")))

        await send(msg("Page.close"))

    total = len(failures)
    bad_n = len([f for f in failures if not f])
    print(f"\n===== 小結：PASS {total - bad_n} / {total}，FAIL {bad_n} =====")
    return 1 if bad_n else 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
