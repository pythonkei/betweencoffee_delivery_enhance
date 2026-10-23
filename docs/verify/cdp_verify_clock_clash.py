#!/usr/bin/env python3
"""CDP 驗證：時鐘照片列的「像素級遮蔽（clash）」——放大的咖啡照 vs { }／數字／山大黃球。

[為什麼需要這支（與 cdp_verify_clock_braces.py 的 E1 不同）]
  cdp_verify_clock_braces.py 的 E1 是「時鐘可見子項的 rect 兩兩不重疊」；但 2026-10-15 桌機照片
  放大（1440 時 336x480）後，環形照片列（#bc-stage-photo-ring-list）本來就會離開 .footer-logo-cell
  （bc-brand-stage.js 的 releaseRingClip 設計：揭示跑完即釋放裁切）⇒ rect 重疊是設計必然、不是 bug。
  真正該問的是「不同元素的可見像素是否落在同一點」＝像素級遮蔽，本腳本量這個。

[量法：非破壞性圖層隔離]
  把某一層用「只插一條 !important 的 stylesheet 規則」隱藏（visibility:hidden 不影響 layout），
  與基準截圖相減 → 得到「該層真正畫到的像素」遮罩；兩層遮罩的交集 = 兩層互相遮蔽的像素數。
  ⚠ 絕不可用 element.style.visibility='hidden' 再「還原」成 element.style.visibility=''：
    [data-reveal] 的可見性 = CSS `#bc-brand-stage [data-reveal]{visibility:hidden}`
    （static/css/bc-brand-stage.css:94）＋ JS 於 whenFontsReady 寫入的 inline visibility:visible
    （static/js/bc-brand-stage.js:288）。把 inline 設成 '' 不是還原、而是「刪掉 inline 宣告」
    ⇒ 退回 CSS 的 hidden ⇒ .footer-logo-cell 內整個環形照片列（visibility 繼承）永久隱形
    ⇒ 之後所有像素差 = 0（實測：照片貢獻像素 54047 px → 0 px）。

[讓「揭示」真的跑完（沿用 cdp_verify_hero_coffee_photos.py）]
  1. SCROLL_CELL_JS 捲到照片格（該 cell 在首屏外，不捲則 data-reveal="clip-down" 永不觸發）
  2. SPEED_GSAP_JS  GSAP globalTimeline.timeScale(100)：本機 CDP 的 rAF 被節流，
                     DUR_L=1.2s 的 clip 揭示實測要 16-36 秒（真瀏覽器 1.2s）
  3. wait_reveal()   輪詢 .footer-logo-cell 的 clip-path 變成 'none'（揭示跑完並被釋放）
  4. FREEZE/STABLE   把「有限次」CSS transition 一律 finish() 推到終點（不是 pause()）。
                     ⚠ pause() 會把它凍在半途；之後插入 <style> 觸發 style recalc 時，
                       被丟棄的 CSSTransition 會直接跳到終值 ⇒ 基準圖與之後每張圖都差一塊
                       「會動的區域」（實測 992/768 的環形列 scale 過渡）⇒ 每個圖層遮罩都含
                       同一塊假區域、兩兩交集全部變成同一個 bbox（假遮蔽）。無限次動畫
                       （品牌 noise_animation）仍用 pause（finish() 會丟 InvalidStateError）。
  5. 每個 viewport 都做「還原殘留 = 0 px」自我驗證（sess.layer 回傳 resid）；
     殘留 != 0 即宣告該 viewport 數字不可信（這條就是上述假數據的守門）。
     ⚠ 2026-10-16（#56）：殘留的另一個來源＝「會改 DOM 文字」的計時器 —— hero 時鐘
       （bc-weather.js:219）的 setInterval **沒掛在 window.\***，只依名稱 clearInterval 抓不到
       ⇒ 跨分界時改「HH:MM」文字 ⇒ 1280 重試 3 次都殘留 328 px。**兩條看似合理的路都會壞**：
       全清計時器 ⇒ 頁面靜止、compositor 不產 frame ⇒ captureScreenshot 永久卡住；
       凍結 `Date` ⇒ GSAP ticker 的時間源就是 Date.now ⇒ 揭時跑不完（P1-1 FAIL）。
       ⇒ 改用 LOCK_CLOCK_JS：只把會被覆寫的文字節點鎖住（no-op setter），計時器與 Date 全不動。

[階段]
  prod     : P1 生產環境（DOM 完全未被探針碰過）是否揭示完成、照片是否真的有畫出像素、
             探針是否零副作用（inline style 全等、還原 0 px）。
  clobber  : P2 重現「舊探針破壞性還原」＋對照安全法（證明是探針壞、不是生產壞）。
  clash    : P4 六個斷點的像素級遮蔽表（整體 ＋ 逐張照片：current 與左右鄰居）。
  all      : 全部（預設）。

用法：站台須在 BC_BASE（預設 http://localhost:8081）跑、CDP 瀏覽器須在 9222（見 CDP_SETUP.md）。
  注意：本專案用 cached.Loader，改過 templates/** 後 8081 不會自動換模板 ⇒ 驗證請另開新 port，
        例如 (setsid python3 manage.py runserver 127.0.0.1:8090 &) ;
             BC_BASE=http://127.0.0.1:8090 python3 docs/verify/cdp_verify_clock_clash.py
  輸出：遮蔽表印在 stdout；互相有接觸的配對會把該區域裁圖存到 BC_OUT（預設 /tmp/bc_clash）
        供目視複核。

"""
import asyncio, base64, io, json, os, sys, time, urllib.request

import websockets
from PIL import Image, ImageChops

BASE = os.environ.get("BC_BASE", "http://127.0.0.1:8081")
CDP = "http://localhost:9222"
OUTDIR = os.environ.get("BC_OUT", "/tmp/bc_clash")
THR = 12  # 每像素亮度差 > THR 才算「這一層有畫到這裡」

# ---------------------------------------------------------------- JS 片段
READY_JS = ("(function(){return !!(document.querySelector('#bc-stage-photo-ring .hero_hand.is-ready')"
            "&&document.getElementById('bc-stage-photo-ring-list'));})()")

SCROLL_CELL_JS = ("(function(){var e=document.getElementById('bc-stage-photo-ring');"
                  "if(!e) return null;var r=e.getBoundingClientRect();"
                  "window.scrollTo(0, Math.round(window.scrollY + r.top - "
                  "(window.innerHeight - r.height)/2));return Math.round(window.scrollY);})()")

SPEED_GSAP_JS = ("(function(){if(window.gsap&&window.gsap.globalTimeline){"
                 "window.gsap.globalTimeline.timeScale(100);return true;}return false;})()")

CELL_CLIP_JS = ("(function(){var e=document.querySelector('#bc-stage-photo-ring .footer-logo-cell');"
                "return e?getComputedStyle(e).clipPath:null;})()")

PAUSE_JS = ("(function(){var s=document.querySelector('.bc-gunte-hero .splide');"
            "if(!s) return false;['mouseenter','mouseover'].forEach(function(t){"
            "s.dispatchEvent(new MouseEvent(t,{bubbles:true}));});return true;})()")

# 2026-10-16（使用者指示「名稱與 Highlight 的時間點不正確」）：文字改為「圓盤旋轉過渡跑完才切」
#   （bc-hand-ring.js）——旋轉期間文字容器帶 .-hidden，settle 時才切 -current 並移除。
#   若量測時剛好卡在這個 1.2s 的窗口內，文字會在量測期間出現 ⇒ 基準圖與之後每張圖差一塊
#   （假的殘留）。⇒ 暫停 autoplay 後先等「不再有 pending」（容器沒有 .-hidden）再進凍結流程。
CAP_SETTLED_JS = ("(function(){var c=document.querySelector('#bc-stage-photo-ring .bc-ring-caption');"
                  "return c ? !c.classList.contains('-hidden') : true;})()")

# 停掉會「改動 DOM 文字」的計時器：bc-brand-stage.js:40 的 __bcStageClockInterval 每秒 tick，每分鐘
# 會把 [data-stage-clock] 的「分」進位 ⇒ 基準圖與之後每張圖差那一小塊數字區域（實測殘留
# 177 px @390、647 px @1280、1452-1958 px @992，且每個圖層遮罩都含那塊 ⇒ 假的「照片×數字 1081 px」）。
# 計時器只寫文字、不影響任何幾何 ⇒ 量測前 clearInterval 即可。
#
# ⚠ 2026-10-16（本輪 #56）：**只依名稱 clearInterval 不夠**。hero 時鐘的
#   `static/js/bc-weather.js:219 setInterval(updateClock, 1000)` **沒有存到 `window.*`**
#   ⇒ 上面的 names 抓不到 ⇒ 每分鐘跨分界時改一次「HH:MM」文字 ⇒ 1280 殘留 328 px（同一輪
#   重試 3 次全中，且每個圖層遮罩都含那塊 ⇒ 假的「照片×數字 328 px」）。
#
# ⚠ 兩條走不通的路（2026-10-16 同日各實測一輪）：
#   ① **把計時器全清掉**（init script 包裹 setInterval 記 id、凍結時全清）：頁面完全靜止 ⇒
#      compositor 不再產 frame ⇒ `Page.captureScreenshot` 永遠不回應（連另一條 ws 的
#      `Runtime.evaluate` 也逾時；renderer CPU 0.7%＝不是 JS 迴圈，是在等 frame）⇒ 掛在 1280。
#   ② **init script 凍結 `Date`**：GSAP 3 的 ticker 時間源就是 `Date.now`（不是 performance.now）
#      ⇒ 時間不前進 ⇒ 揭時（GSAP 的 clip-down）永遠跑不完 ⇒ P1-1「clip-path 已釋放」直接 FAIL。
#   ⇒ 正解＝**不碰計時器、不碰 Date**，只把「會被 tick 改寫的那幾個文字節點」鎖住（LOCK_CLOCK_JS）。
FREEZE_CLOCK_JS = r"""
(function(){
  var names=['__bcStageClockInterval','__bcStageLogoInterval','__weatherClockInterval',
             '__heroClockInterval'];
  var out=[];
  names.forEach(function(k){
    if(window[k]){ try{ clearInterval(window[k]); }catch(e){} window[k]=null; out.push(k); }
  });
  return out;
})()
"""

# 鎖住「計時器會改寫的文字節點」＝把該元素的 textContent 改成 no-op setter（element 上的 own
# property，蓋掉 prototype 的 accessor）。tick 照跑（DOM 寫入變成空操作）⇒ 不會有 frame 枯竭、
# GSAP/Date 完全不受影響，而畫面上的字固定不變 ⇒ 跨分界不再產生假殘留。
#   · 涵蓋 hero/頁尾時鐘（#bc-stage-clock-hours/-minutes/-colon-*、[data-stage-clock]）。
#     2026-10-17（使用者指示：「bc-stage-weather 移除時鐘，只保留天氣與溫度」）：天氣元件的
#     .weather .clock .value 已不存在（bc-weather.js 的 updateClock 已移除）→ 選擇器一併移除。
#   · 可重複呼叫（已鎖過的用 __bcProbeLocked 記號跳過）；settle 與每次 stable 前都叫一次，
#     連「量測中途才被建立的節點」也一併鎖上。
LOCK_CLOCK_JS = r"""
(function(){
  var sel='#bc-stage-clock-hours,#bc-stage-clock-minutes,#bc-stage-clock-colon-before-minutes,'
        + '#bc-stage-clock-colon-after-minutes,[data-stage-clock]';
  var els=document.querySelectorAll(sel), out=[];
  for(var i=0;i<els.length;i++){
    var el=els[i];
    if(el.__bcProbeLocked){ out.push(el.textContent); continue; }
    var v=el.textContent;
    try{
      Object.defineProperty(el,'textContent',
        {configurable:true, get:function(){ return v; }, set:function(){}});
      el.__bcProbeLocked=true;
    }catch(e){}
    out.push(v);
  }
  return out.join('|');
})()
"""

FREEZE_JS = r"""
(function(){
  var fin=0, pau=0, err=0;
  try{
    document.getAnimations().forEach(function(a){
      var inf=false;
      try{ inf = a.effect && a.effect.getTiming().iterations === Infinity; }catch(e){}
      try{
        if(inf){ a.pause(); try{ a.currentTime = 0; }catch(e3){} pau++; }
        else { a.finish(); fin++; }
      }
      catch(e){ err++; try{ a.pause(); pau++; }catch(e2){} }
    });
  }catch(e){}
  try{ if(window.gsap&&window.gsap.globalTimeline) window.gsap.globalTimeline.pause(); }catch(e){}
  return {finished:fin, paused:pau, err:err};
})()
"""

# 每次截圖前再套一次：把「有限次」的 CSS transition 推到終點（絕不停在半途——
# 停半途的 CSSTransition 之後若被 style recalc 丟棄，元素會直接跳到終值
# ⇒ 基準圖與之後每張圖都會差一塊「會動的區域」，讓所有圖層遮罩都含同一塊假區域）。
# 無限次動畫（品牌 noise_animation）改為 pause ＋ 把相位釘在 0（finish() 會丟 InvalidStateError）。
# ⚠ 只 pause 不夠：hide 插入 <style> 觸發的 style recalc 會把動畫物件換掉、重新從 0 開始跑，
#   下一次 stable() 又在「不同相位」暫停 ⇒ 基準圖與之後每張圖差一小塊（實測 390 殘留 177 px）。
STABLE_JS = FREEZE_JS

# 非破壞性隱藏：只維護一條 stylesheet 規則，永不碰元素 inline style
HIDE_JS = r"""
(function(sel,on){
  var id='__bc_probe_hide', s=document.getElementById(id);
  if(!s){ s=document.createElement('style'); s.id=id;
          (document.head||document.documentElement).appendChild(s); }
  s.textContent = on ? (sel + '{visibility:hidden !important}') : '';
  return {applied:s.textContent, matched: on ? document.querySelectorAll(sel).length : 0};
})(%s,%s)
"""

# 2026-10-17（使用者指示：bc-stage-weather 移除時鐘）：量測期間「永久」隱藏單一 selector。
#   與 HIDE_JS 的差別＝獨立 style id、不會被其他圖層的 hide/restore 覆寫（HIDE_JS 只維護一條規則）。
PIN_HIDE_JS = r"""
(function(sel){
  var id='__bc_probe_pin', s=document.getElementById(id);
  if(!s){ s=document.createElement('style'); s.id=id;
          (document.head||document.documentElement).appendChild(s); }
  s.textContent = sel + '{visibility:hidden !important}';
  return {applied:s.textContent, matched:document.querySelectorAll(sel).length};
})(%s)
"""

# 舊探針的破壞性寫法（P2 重現用）
INLINE_HIDE_JS = r"""
(function(sel,on){
  var els=document.querySelectorAll(sel), before=[], after=[];
  for(var i=0;i<els.length;i++){ before.push(els[i].getAttribute('style')||''); }
  for(var i=0;i<els.length;i++){ els[i].style.visibility = on ? 'hidden' : ''; }
  for(var i=0;i<els.length;i++){ after.push(els[i].getAttribute('style')||''); }
  return {before:before, after:after};
})(%s,%s)
"""

# 現場快照：rect / computed / inline style（用來證明有無被探針改動）
CTX_JS = r"""
(function(){
  function box(el){ if(!el) return null; var r=el.getBoundingClientRect();
    return {x:Math.round(r.left*10)/10, y:Math.round(r.top*10)/10,
            w:Math.round(r.width*10)/10, h:Math.round(r.height*10)/10,
            right:Math.round(r.right*10)/10, bottom:Math.round(r.bottom*10)/10}; }
  function st(el,p){ return el?getComputedStyle(el)[p]:null; }
  function inl(el){ return el?el.getAttribute('style')||'':null; }
  var out={sy:Math.round(window.scrollY), iw:innerWidth, ih:innerHeight,
           docH:document.documentElement.scrollHeight};
  var IDS=['bc-stage-clock','bc-stage-clock-brace-open','bc-stage-clock-hours','bc-stage-clock-colon-before-minutes',
           'bc-stage-photo-ring','bc-stage-clock-colon-after-minutes','bc-stage-clock-minutes',
           'bc-stage-clock-brace-close','bc-stage-weather'];
  out.clock={}; IDS.forEach(function(id){ var e=document.getElementById(id);
    out.clock[id]={box:box(e), vis:st(e,'visibility'), display:st(e,'display'),
                   op:st(e,'opacity'), z:st(e,'zIndex')}; });
  var cell=document.querySelector('#bc-stage-photo-ring .footer-logo-cell');
  var hand=document.querySelector('#bc-stage-photo-ring .hero_hand');
  var list=document.getElementById('bc-stage-photo-ring-list');
  out.cell={box:box(cell), vis:st(cell,'visibility'), clip:st(cell,'clipPath'),
            op:st(cell,'opacity'), inline:inl(cell),
            reveal:cell?cell.getAttribute('data-reveal'):null};
  out.hand={box:box(hand), vis:st(hand,'visibility'), op:st(hand,'opacity'), inline:inl(hand),
            radius:hand?getComputedStyle(hand).getPropertyValue('--circle-radius'):null};
  out.list={box:box(list), vis:st(list,'visibility'), op:st(list,'opacity'),
            inline:inl(list), transform:st(list,'transform'),
            imgW:list?getComputedStyle(list).getPropertyValue('--bc-hand-img-w'):null};
""" + r"""
  var items=list?list.querySelectorAll('.hero_hand_item'):[];
  out.items=[];
  for(var i=0;i<items.length;i++){
    var it=items[i], img=it.querySelector('img');
    out.items.push({i:i, cur:it.classList.contains('-current'),
                    angle:it.getAttribute('style'), box:box(it), imgBox:box(img),
                    vis:st(it,'visibility'), imgVis:st(img,'visibility'),
                    imgOp:st(img,'opacity'), imgScale:st(img,'scale'), inline:inl(img),
                    complete:img?!!img.complete:null,
                    natural:(img&&img.naturalWidth)?[img.naturalWidth,img.naturalHeight]:null});
  }
  var nav=document.querySelector('.tax-nav'), navA=nav?nav.querySelector('a'):null;
  out.ball={box:box(nav), aBox:box(navA), vis:st(nav,'visibility'), op:st(nav,'opacity'),
            display:st(nav,'display'), z:st(nav,'zIndex'), pos:st(nav,'position'),
            cls:nav?nav.className:null, aVis:st(navA,'visibility'), aOp:st(navA,'opacity')};
  out.animations=document.getAnimations().length;
  var rev=document.querySelectorAll('#bc-brand-stage [data-reveal]');
  var visN=0, hidN=0, noInline=0;
  for(var k=0;k<rev.length;k++){
    if(getComputedStyle(rev[k]).visibility==='visible') visN++; else hidN++;
    if(!rev[k].getAttribute('style')) noInline++;
  }
  out.revealInline={total:rev.length, visible:visN, hidden:hidN, withoutInlineStyle:noInline};
  return out;
})()
"""

# ---------------------------------------------------------------- 圖層選擇器
SEL_PHOTOS = "#bc-stage-photo-ring-list"
SEL_CELL = "#bc-stage-photo-ring .footer-logo-cell"
SEL_BRACES = "#bc-stage-clock-brace-open,#bc-stage-clock-brace-close"
SEL_DIGITS = ("#bc-stage-clock-hours,#bc-stage-clock-minutes,"
              "#bc-stage-clock-colon-before-minutes,#bc-stage-clock-colon-after-minutes")
SEL_BALL = ".tax-nav"
SEL_WEATHER = "#bc-stage-weather"
SEL_ITEM = "#bc-stage-photo-ring-list .hero_hand_item:nth-child(%d)"


# ---------------------------------------------------------------- 像素工具（無 numpy，純 PIL）
def mask(a, b, thr=THR):
    """a/b 兩張圖的顯著差異遮罩（'L'，255 = 有差）。"""
    d = ImageChops.difference(a, b).convert("L")
    return d.point(lambda v: 255 if v > thr else 0)


def npx(m):
    return m.histogram()[255]


def box(m):
    return m.getbbox()


def both(m1, m2):
    """兩層都有畫到的像素數（= 該位置兩層互相遮蔽）。"""
    return npx(ImageChops.darker(m1, m2))


def jn(s):
    return json.dumps(s)


def fmt_box(b):
    return "None" if not b else "[%d,%d,%d,%d]" % b


# ---------------------------------------------------------------- CDP session
class Sess:
    def __init__(self, ws):
        self.ws = ws
        self.mid = 1

    async def send(self, method, params=None):
        m = {"id": self.mid, "method": method, "params": params or {}}
        self.mid += 1
        await self.ws.send(json.dumps(m))
        while True:
            r = json.loads(await self.ws.recv())
            if r.get("id") == m["id"]:
                if "error" in r:
                    print("   CDP error:", r["error"])
                return r.get("result", {})

    async def ev(self, expr):
        r = await self.send("Runtime.evaluate", {"expression": expr, "returnByValue": True})
        res = r.get("result", {})
        if res.get("subtype") == "error":
            print("   JS error:", res.get("description"))
        return res.get("value")

    async def frame(self, timeout=30):
        """逼出一個 frame（CSS transition / GSAP tick 在本機 CDP 不會自己前進）。"""
        try:
            await asyncio.wait_for(self.send("Page.captureScreenshot",
                                             {"format": "jpeg", "quality": 5}), timeout)
        except asyncio.TimeoutError:
            print("   frame timeout")

    async def shot(self, timeout=45):
        r = await asyncio.wait_for(self.send("Page.captureScreenshot", {"format": "png"}), timeout)
        return Image.open(io.BytesIO(base64.b64decode(r["data"]))).convert("RGB")

    async def nav(self, url):
        await self.send("Page.navigate", {"url": url})
        for _ in range(80):
            await asyncio.sleep(0.25)
            if await self.ev("document.readyState === 'complete' && location.href === " + jn(url)):
                break
        for _ in range(40):
            await asyncio.sleep(0.25)
            if await self.ev(READY_JS):
                break
        await self.frame()
        await asyncio.sleep(0.4)

    async def viewport(self, w, h, mobile):
        await self.send("Emulation.setDeviceMetricsOverride",
                        {"width": w, "height": h, "deviceScaleFactor": 1, "mobile": mobile})
        await asyncio.sleep(0.4)

    async def settle(self, wait_clip=True, timeout=30.0):
        """捲到照片格 → 加速 GSAP → 等 clip-path 釋放 → 暫停 hero autoplay → 凍結時間軸。"""
        await self.ev(SCROLL_CELL_JS)
        await asyncio.sleep(0.6)
        await self.ev(SPEED_GSAP_JS)
        ok = None
        if wait_clip:
            t0 = time.time()
            ok = False
            while time.time() - t0 < timeout:
                await self.frame()
                await asyncio.sleep(0.4)
                if await self.ev(CELL_CLIP_JS) == "none":
                    ok = True
                    break
        await self.ev(PAUSE_JS)
        clock = await self.ev(FREEZE_CLOCK_JS)   # 停掉 1 秒時鐘 tick（每分鐘會改「分」的文字）
        lock = await self.ev(LOCK_CLOCK_JS)      # 並鎖住文字節點（沒掛 window.* 的 tick 也改不動）
        # 2026-10-16：先等文字收斂（最多 4s）—— 文字改為「圓盤轉完才切」，卡在 1.2s 窗口內的話
        #   量測期間會切換文字 ⇒ 假的殘留（見 CAP_SETTLED_JS 的註解）
        t0 = time.time()
        while time.time() - t0 < 4.0:
            if await self.ev(CAP_SETTLED_JS):
                break
            await asyncio.sleep(0.2)
        await asyncio.sleep(1.6)          # > 1.2s（--bc-hand-ease）＋保險計時器 60ms
        await self.frame()
        await asyncio.sleep(0.3)
        frozen = await self.ev(FREEZE_JS)  # 剩下的（含仍在半途者）一律推到終點
        await asyncio.sleep(0.3)
        await self.frame()
        await asyncio.sleep(0.2)
        frozen2 = await self.ev(FREEZE_JS)
        await asyncio.sleep(0.2)
        await self.frame()
        await asyncio.sleep(0.2)
        # 暖機（丟棄）：先做一次 hide/restore，讓「第一次隱藏造成的重繪／圖層提升」在基準圖
        # 之前就定型。否則那個瞬態會讓之後每一張圖都與基準差一小塊（實測 992 的杯子邊緣
        # 3539 px，且每個圖層遮罩都含那塊）。
        await self.hide(SEL_PHOTOS, True)
        await self.stable()
        await self.shot()
        await self.hide(SEL_PHOTOS, False)
        await self.stable()
        await self.shot()
        return {"clip_released": ok, "frozen": frozen, "frozen2": frozen2, "clock": clock,
                "lock": lock}

    async def hide(self, sel, on):
        return await self.ev(HIDE_JS % (jn(sel), "true" if on else "false"))

    async def inline_hide(self, sel, on):
        return await self.ev(INLINE_HIDE_JS % (jn(sel), "true" if on else "false"))

    async def ctx(self):
        return await self.ev(CTX_JS)

    async def stable(self):
        """截圖前把有限次動畫推到終點 ＋ 停掉會改文字內容的時鐘 tick（並鎖住文字節點）。"""
        await self.ev(FREEZE_CLOCK_JS)
        await self.ev(LOCK_CLOCK_JS)
        r = await self.ev(STABLE_JS)
        await self.frame()
        await asyncio.sleep(0.2)
        return r

    async def layer(self, base, sel):
        """量一層的可見像素（非破壞性）＋同時回報「還原殘留」供自我驗證。

        回傳 (該層遮罩, 還原後與基準的差異像素數)。殘留必須為 0，否則表示
        這個 viewport 量測期間有東西在動（數字不可信）。
        """
        await self.hide(sel, True)
        await self.stable()
        m = mask(base, await self.shot())
        await self.hide(sel, False)
        await self.stable()
        resid = npx(mask(base, await self.shot()))
        return m, resid

    async def quiesce(self, base, attempts=3, wait=0.5):
        """等畫面收斂回 base（0 px）為止；回傳 (最後一張圖, 與 base 的差異像素數)。

        瞬態（重繪／compositor 圖層提升）會讓 hide/restore 後的畫面與「更早拍的基準」
        差一小塊；多等一次再拍即可拿到一致的一張（真正的副作用不會因等待而消失）。
        """
        img = await self.shot()
        d = npx(mask(base, img))
        for _ in range(attempts - 1):
            if d == 0:
                break
            await asyncio.sleep(wait)
            await self.stable()
            img = await self.shot()
            d = npx(mask(base, img))
        return img, d


# ---------------------------------------------------------------- 報告
class Rep:
    def __init__(self):
        self.pass_n = 0
        self.fail_n = 0
        self._p = 0
        self._f = 0

    def check(self, label, ok, detail=""):
        print("  [%s] %s%s" % ("PASS" if ok else "FAIL", label,
                               (" -> " + str(detail)) if detail != "" else ""))
        if ok:
            self.pass_n += 1
        else:
            self.fail_n += 1
        return bool(ok)

    def info(self, label, detail=""):
        print("  [info] %s%s" % (label, (" -> " + str(detail)) if detail != "" else ""))

    def summary(self, title):
        """印出「本階段」的成績（計數器是累計的，這裡只取與上一次 summary 的差）。"""
        p, f = self.pass_n - self._p, self.fail_n - self._f
        self._p, self._f = self.pass_n, self.fail_n
        print("\n===== %s：%s（%d PASS / %d FAIL）=====" % (title,
              "PASS" if f == 0 else "FAIL", p, f))


# ---------------------------------------------------------------- P1：生產環境未被干擾
async def phase_prod(sess, rep):
    print("\n########## P1 生產環境（探針完全沒碰過 DOM） ##########")
    await sess.viewport(1440, 900, False)
    await sess.nav(BASE + "/")
    rep.info("gsap", await sess.ev("typeof window.gsap"))
    rep.info("ScrollTrigger / SplitText",
             [await sess.ev("typeof window.ScrollTrigger"), await sess.ev("typeof window.SplitText")])
    rep.info("document.fonts.status", await sess.ev("document.fonts?document.fonts.status:null"))
    st = await sess.settle()
    rep.check("P1-1 揭示跑完、.footer-logo-cell 的 clip-path 已釋放（none）",
              st["clip_released"], await sess.ev(CELL_CLIP_JS))
    c1 = await sess.ctx()
    rep.info("data-reveal 統計（總數/可見/隱藏/無 inline）",
             "%s/%s/%s/%s" % (c1["revealInline"]["total"], c1["revealInline"]["visible"],
                              c1["revealInline"]["hidden"], c1["revealInline"]["withoutInlineStyle"]))
    rep.info("cell inline style", c1["cell"]["inline"])
    rep.info("cell vis / clip / op",
             "%s / %s / %s" % (c1["cell"]["vis"], c1["cell"]["clip"], c1["cell"]["op"]))
    rep.info("list vis / op / transform", "%s / %s / %s" % (c1["list"]["vis"], c1["list"]["op"],
                                                            c1["list"]["transform"]))
    rep.info("items（index/current/圖寬/imgVis/scale）",
             [(i["i"], i["cur"], i["imgBox"] and round(i["imgBox"]["w"]),
               i["imgVis"], i["imgScale"]) for i in c1["items"]])
    rep.info("ball（rect/vis/op/z/pos/cls）",
             "%s %s %s %s %s %s" % (c1["ball"]["box"], c1["ball"]["vis"], c1["ball"]["op"],
                                    c1["ball"]["z"], c1["ball"]["pos"], c1["ball"]["cls"]))
    rep.info("scrollY / animations", "%s / %s" % (c1["sy"], c1["animations"]))

    a = await sess.shot()
    b = await sess.shot()
    d = npx(mask(a, b))
    rep.check("P1-2 基準畫面決定性（連拍兩張 0 差異）", d == 0, "%d px 有差" % d)

    await sess.hide(SEL_PHOTOS, True)
    await sess.stable()
    p = await sess.shot()
    await sess.hide(SEL_PHOTOS, False)
    await sess.stable()
    r, reff = await sess.quiesce(a)          # 還原後收斂回基準（容忍一次性瞬態）
    m_photo = mask(p, r)                     # 同一 epoch 的參考圖 ⇒ 瞬態在兩張圖上相同、互相抵銷
    rep.check("P1-3 環形照片真的有畫出像素（>5000 px）", npx(m_photo) > 5000,
              "%d px，bbox %s" % (npx(m_photo), fmt_box(box(m_photo))))
    rep.check("P1-4 非破壞性還原後與基準完全一致（0 px）", reff == 0, "%d px" % reff)
    c2 = await sess.ctx()
    same_inline = (c1["cell"]["inline"] == c2["cell"]["inline"]
                   and c1["list"]["inline"] == c2["list"]["inline"]
                   and [i["inline"] for i in c1["items"]] == [i["inline"] for i in c2["items"]])
    rep.check("P1-5 探針未動到任何 inline style（cell/list/img 全等）", same_inline,
              "cell=%r" % (c2["cell"]["inline"],))
    rep.check("P1-6 還原後 cell 仍可見（computed visibility=visible）",
              c2["cell"]["vis"] == "visible", c2["cell"]["vis"])
    return {"base": a, "mask_photo": m_photo}


# ---------------------------------------------------------------- P2：重現舊探針的破壞性還原
async def phase_clobber(sess, rep):
    print("\n########## P2 舊探針的破壞性還原：重現 + 對照（fresh page） ##########")
    await sess.viewport(1440, 900, False)
    await sess.nav(BASE + "/")
    st = await sess.settle()
    rep.check("P2-0 揭示完成（clip-path none）", st["clip_released"], await sess.ev(CELL_CLIP_JS))
    c_before = await sess.ctx()
    rep.info("初始 cell inline", c_before["cell"]["inline"])
    a = await sess.shot()

    # 基準：照片貢獻的像素（安全法量測）
    await sess.hide(SEL_PHOTOS, True)
    await sess.stable()
    p0 = await sess.shot()
    await sess.hide(SEL_PHOTOS, False)
    await sess.stable()
    px0 = npx(mask(a, p0))
    rep.info("A) 初始：環形照片貢獻像素", "%d px" % px0)

    # ---- 對照組：安全法（stylesheet !important）對 .footer-logo-cell 做 hide→restore
    await sess.hide(SEL_CELL, True)
    await sess.stable()
    await sess.shot()
    await sess.hide(SEL_CELL, False)
    await sess.stable()
    _, d1 = await sess.quiesce(a)             # 還原後收斂回基準
    c_safe = await sess.ctx()
    await sess.hide(SEL_PHOTOS, True)
    await sess.stable()
    p1 = await sess.shot()
    await sess.hide(SEL_PHOTOS, False)
    await sess.stable()
    r1b = await sess.shot()                  # 與 p1 同一 epoch 的參考圖（瞬態抵銷）
    px1 = npx(mask(r1b, p1))
    rep.check("P2-1 對照組（安全法 hide/restore 同一元素）畫面零殘留像素", d1 == 0, "%d px" % d1)
    rep.check("P2-2 對照組後 cell 仍 visible 且 inline style 未變",
              c_safe["cell"]["vis"] == "visible"
              and c_safe["cell"]["inline"] == c_before["cell"]["inline"],
              "%s / %r" % (c_safe["cell"]["vis"], c_safe["cell"]["inline"]))
    rep.check("P2-3 對照組後照片貢獻像素不變（探針無副作用）",
              abs(px1 - px0) <= max(60, int(px0 * 0.02)), "%d vs %d" % (px1, px0))

    # ---- 舊法：inline style='hidden' → 再「還原」成 style=''
    h1 = await sess.inline_hide(SEL_CELL, True)
    h2 = await sess.inline_hide(SEL_CELL, False)
    await sess.frame()
    await asyncio.sleep(0.4)
    c_bad = await sess.ctx()
    b = await sess.shot()
    await sess.hide(SEL_PHOTOS, True)
    await sess.stable()
    p2 = await sess.shot()
    await sess.hide(SEL_PHOTOS, False)
    await sess.stable()
    px_bad = npx(mask(b, p2))
    rep.info("B) 舊法 hide    → cell style 屬性", h1["after"])
    rep.info("B) 舊法 restore → cell style 屬性", h2["after"])
    rep.info("B) 舊法後 cell vis / clip",
             "%s / %s" % (c_bad["cell"]["vis"], c_bad["cell"]["clip"]))
    rep.info("B) 舊法後 list vis / 各 img vis",
             "%s / %s" % (c_bad["list"]["vis"], [i["imgVis"] for i in c_bad["items"]]))
    rep.info("B) 舊法後 data-reveal 統計（總/可見/隱藏）",
             "%s/%s/%s" % (c_bad["revealInline"]["total"], c_bad["revealInline"]["visible"],
                           c_bad["revealInline"]["hidden"]))
    rep.check("P2-4 舊法「還原」其實是刪掉 inline visibility（hide 後有、restore 後沒有）",
              ("visibility" in (h1["after"][0] or "")) and ("visibility" not in (h2["after"][0] or "")),
              "hide=%r restore=%r" % (h1["after"][0], h2["after"][0]))
    rep.check("P2-5 舊法還原後 cell 退回 CSS 的 visibility:hidden",
              c_bad["cell"]["vis"] == "hidden", c_bad["cell"]["vis"])
    rep.check("P2-6 舊法還原後【照片貢獻像素歸零】＝舊探針之後所有像素差都 = 0 的機制",
              px_bad == 0 and px0 > 5000, "before=%d → after=%d px" % (px0, px_bad))
    rep.check("P2-7 舊法還原後畫面確實改變（不是量測失效）",
              npx(mask(a, b)) > 5000, "%d px 差異" % npx(mask(a, b)))
    return {"px0": px0, "px_bad": px_bad}


# ---------------------------------------------------------------- P4：像素級遮蔽偵測
VIEWPORTS = [(1440, 900, False), (1280, 900, False), (992, 900, False),
             (991, 900, False), (768, 1024, False), (390, 844, True)]

CLASH_SEVERE = 2000  # 互相遮蔽超過此像素數＝明顯


def union_box(*ms):
    bs = [b for b in (box(m) for m in ms) if b]
    if not bs:
        return None
    return (min(b[0] for b in bs), min(b[1] for b in bs),
            max(b[2] for b in bs), max(b[3] for b in bs))


def crop_save(img, b, path, pad=14):
    if not b:
        return
    w, h = img.size
    c = (max(0, b[0] - pad), max(0, b[1] - pad), min(w, b[2] + pad), min(h, b[3] + pad))
    img.crop(c).save(path)


async def measure_viewport(sess, name, w, h, mob):
    """量一個 viewport。

    回傳 (checks, infos, rows)：
      checks = [(label, ok, detail)] 由呼叫者計分 —— 重試時「失敗那一輪」不被計分；
      infos  = [(label, detail)] 純輸出；
      rows   = 判讀表用的 (viewport, pair, mutual, %, bbox)。
    """
    checks, infos, rows = [], [], []
    await sess.viewport(w, h, mob)
    await sess.nav(BASE + "/")
    st = await sess.settle()
    checks.append(("[%s] 揭示完成（clip-path none）" % name,
                   st["clip_released"] is True, await sess.ev(CELL_CLIP_JS)))
    # 2026-10-17（使用者指示：bc-stage-weather 移除時鐘、只剩 icon ⇄ 溫度）：天氣元件每 5 秒
    #   以 rAF 呼叫 toggle()，而 GSAP 時間軸已被 FREEZE_JS 暫停 ⇒ gsap.to 不再推進，但
    #   gsap.fromTo(..., {x:d}) 預設 immediateRender **會立刻套用 from 值** ⇒ 每 5 秒把元素瞬移一次，
    #   量測超過 ~10 秒後整個元件被推離 .view（實測 1440 殘留 917 px、1280 835 px、992 出現
    #   多輪瞬態殘留；每個圖層遮罩都含同一塊 ⇒ 假的「還原殘留／照片 #n」）。
    #   它與本腳本要驗的圖層（照片 / { } / 數字 / 黃球）零重疊（hero_weather 的 B2 逐斷點守門）
    #   ⇒ 量測期間以非破壞性 stylesheet 永久隱藏（PIN_HIDE_JS，獨立 style id；不可用 hide()
    #     因為它只維護單一條規則，會被後續圖層的 hide/restore 覆寫），
    #   讓基準圖與之後每一張圖完全一致。
    await sess.ev(PIN_HIDE_JS % jn(SEL_WEATHER))
    await sess.stable()
    c = await sess.ctx()
    base = await sess.shot()
    d = npx(mask(base, await sess.shot()))
    checks.append(("[%s] 基準畫面決定性（0 px）" % name, d == 0, "%d px" % d))
    infos.append(("[%s] 照片寬 / cell 寬 / 黃球 rect" % name,
                  "%s / %s / %s" % (c["list"]["imgW"],
                                    c["cell"]["box"] and c["cell"]["box"]["w"], c["ball"]["box"])))
    m_photo, r_photo = await sess.layer(base, SEL_PHOTOS)
    m_brace, r_brace = await sess.layer(base, SEL_BRACES)
    m_digit, r_digit = await sess.layer(base, SEL_DIGITS)
    m_ball, r_ball = await sess.layer(base, SEL_BALL)
    resid = {"照片": r_photo, "{ }": r_brace, "數字": r_digit, "黃球": r_ball}
    checks.append(("[%s] 各層 hide/restore 還原殘留皆 0 px（否則本 viewport 數字不可信）" % name,
                   all(v == 0 for v in resid.values()), resid))
    infos.append(("[%s] 各層可見像素 {照片/{}/數字/黃球}" % name,
                  "%d / %d / %d / %d" % (npx(m_photo), npx(m_brace), npx(m_digit), npx(m_ball))))
    pairs = [("照片×{ }", m_photo, m_brace),
             ("照片×數字", m_photo, m_digit),
             ("照片×黃球", m_photo, m_ball),
             ("數字×黃球", m_digit, m_ball),
             ("{ }×黃球", m_brace, m_ball)]
    for label, m1, m2 in pairs:
        mu = both(m1, m2)
        small = min(npx(m1), npx(m2)) or 1
        bb = union_box(ImageChops.darker(m1, m2))
        rows.append((name, label, mu, round(100.0 * mu / small, 2), bb))
        if mu > 0:
            crop_save(base, bb, os.path.join(OUTDIR, "%s_%s.png"
                                             % (name, label.replace("×", "_x_").replace(" ", ""))))
        infos.append(("[%s] %s 互相遮蔽" % (name, label),
                      "%d px（佔小層 %.2f%%）bbox %s" % (mu, 100.0 * mu / small, fmt_box(bb))))

    # 逐張照片（current ＋ 左右鄰居）：哪一張撞到 { }／數字／黃球
    cur = [i["i"] for i in c["items"] if i["cur"]]
    cur_i = cur[0] if cur else 0
    n = len(c["items"])
    for k in [cur_i, (cur_i - 1) % n, (cur_i + 1) % n]:
        m_it, r_it = await sess.layer(base, SEL_ITEM % (k + 1))
        checks.append(("[%s] 照片#%d hide/restore 還原殘留 0 px" % (name, k), r_it == 0,
                       "%d px" % r_it))
        nm = "%s_照片#%d%s" % (name, k, "(current)" if k == cur_i else "(鄰居)")
        for label, m2 in (("{ }", m_brace), ("數字", m_digit), ("黃球", m_ball)):
            mu = both(m_it, m2)
            small = min(npx(m_it), npx(m2)) or 1
            bb = union_box(ImageChops.darker(m_it, m2))
            rows.append((nm, label, mu, round(100.0 * mu / small, 2), bb))
            infos.append(("[%s] vs %s" % (nm, label),
                          "%d px（佔小層 %.2f%%）bbox %s" % (mu, 100.0 * mu / small, fmt_box(bb))))
            if mu > 0:
                crop_save(base, bb, os.path.join(OUTDIR, "%s_vs_%s_base.png"
                                                 % (nm.replace(" ", ""), label.replace(" ", ""))))
    return checks, infos, rows


async def phase_clash(sess, rep):
    print("\n########## P4 像素級遮蔽（clash）偵測：放大的咖啡照 vs { }／數字／山大黃球 ##########")
    os.makedirs(OUTDIR, exist_ok=True)
    rows = []
    for (w, h, mob) in VIEWPORTS:
        name = "%dx%d" % (w, h)
        print("\n--- viewport %s ---" % name)
        checks, infos, rows_i = await measure_viewport(sess, name, w, h, mob)
        tries = 0
        # 瞬態（第一次重繪／compositor 圖層提升／時鐘換分）會讓「基準圖」與之後每張圖差一小塊
        # ⇒ 該 viewport 的數字不可信。整輪重測（而不是只重測一層）——同一輪的所有遮罩必須共用
        # 同一張基準圖，交集才有意義。重試時第一輪不計分，避免「第一次失敗」留在總計裡。
        while tries < 2 and not all(ok for _, ok, _ in checks):
            tries += 1
            print("  [retry] 本 viewport 出現瞬態殘留 → 整輪重新量測（第 %d 次）" % tries)
            checks, infos, rows_i = await measure_viewport(sess, name, w, h, mob)
        for label, detail in infos:
            rep.info(label, detail)
        for label, ok, detail in checks:
            rep.check(label, ok, detail)
        rows.extend(rows_i)

    print("\n########## P4 判讀（互相遮蔽 = 兩層的可見像素落在同一點） ##########")
    bad = [r for r in rows if r[2] > 0]
    severe = [r for r in rows if r[2] >= CLASH_SEVERE]
    print("  %-14s %-20s %10s %8s  %s" % ("viewport", "pair", "mutual px", "%小層", "bbox"))
    for (nm, label, mu, pct, bb) in sorted(rows, key=lambda r: -r[2])[:40]:
        print("  %-14s %-20s %10d %7.2f%%  %s" % (nm, label, mu, pct, fmt_box(bb)))
    rep.info("有接觸的組合數（mutual > 0）", "%d" % len(bad))
    rep.info("明顯遮蔽的組合數（mutual >= %d px）" % CLASH_SEVERE, "%d" % len(severe))
    rep.info("截圖（可目視複核）", OUTDIR)
    return {"rows": rows, "clash": bad, "severe": severe}

# ---------------------------------------------------------------- main
async def main():
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    t0 = time.time()
    req = urllib.request.Request(CDP + "/json/new?about:blank", method="PUT")
    tab = json.loads(urllib.request.urlopen(req).read())
    print("CDP tab: %s" % tab.get("id"))
    rep = Rep()
    try:
        async with websockets.connect(tab["webSocketDebuggerUrl"],
                                      max_size=200 * 1024 * 1024) as ws:
            sess = Sess(ws)
            await sess.send("Page.enable")
            await sess.send("Runtime.enable")
            await sess.send("Network.enable")
            await sess.send("Network.setCacheDisabled", {"cacheDisabled": True})
            if which in ("all", "prod"):
                await phase_prod(sess, rep)
                rep.summary("P1 生產環境未被探針干擾")
            if which in ("all", "clobber"):
                await phase_clobber(sess, rep)
                rep.summary("P2 舊探針破壞性還原（重現 + 對照）")
            if which in ("all", "clash"):
                await phase_clash(sess, rep)
                rep.summary("P4 像素級遮蔽偵測")
    except Exception as e:                                        # noqa: BLE001
        print("session ended: %r" % (e,))
    finally:
        # ⚠ 一定要關掉自己開的分頁：殘留分頁會讓 compositor 不再為新分頁產 frame
        # （見 CDP_SETUP.md「殘留 5 個時踩到」）。用 HTTP 端點關 —— 就算 ws 已經斷了也關得掉。
        try:
            with urllib.request.urlopen(CDP + "/json/close/" + tab.get("id"), timeout=5) as r:
                print("tab closed: %s %s" % (tab.get("id"), (r.read() or b"").decode("utf-8", "replace")))
        except Exception as e:                                    # noqa: BLE001
            print("tab close failed: %r" % (e,))
    print("\n===== 總計 %d PASS / %d FAIL，耗時 %.1fs =====" % (rep.pass_n, rep.fail_n, time.time() - t0))
    return 1 if rep.fail_n else 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
