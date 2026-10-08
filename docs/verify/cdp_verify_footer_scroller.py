#!/usr/bin/env python3
"""CDP 驗證：/about/ footer 的 .footer-mail-inner（email CTA）已改為 index footer 的 .scroller-box 跑馬燈。

改動背景（2026-10-08）
  templates/.../about.html：刪 <div class="footer-mail-inner">（"Write directly to:" + mailto hello@betweencoffee.hk），
  同層插入與 base.html footer 逐字相同的 .scroller-box（2 個 BETWEEN <li>）。
  static/css/bc-bg-footer.css：移除 .footer-mail-inner 規則，新增 scoped 補償
  （#bc-bg-footer .scroller-box/.scroller/.scroller__inner/.tag-list li），
  因為 `#bc-bg-footer div,ul,li{margin:0;padding:0}`（ID 特異度）會蓋掉
  .scroller__inner{padding-block:2rem} 與 .tag-list li{padding:.1rem}。

檢查項目
  A. 舊結構已移除：.footer-mail-inner 不存在、footer 內已無 mailto:hello@betweencoffee.hk
  B. 新結構存在：.foooter-mail > .scroller-box > .scroller > ul.tag-list.scroller__inner，2 個 li（原始）
  C. JS 生效：.scroller[data-animated=true]、.scroller__inner 子節點 = 4（正本複製成 4）、aria-hidden 2 個
  D. 動畫：animation-name == scroll、animation-duration 60s / timing-function linear、play-state == running；
     取樣前先以 1×1 截圖強制產生 BeginFrame（headless tab 若無 frame producer，CSS animation 會停在
     pending：startTime=null / currentTime=0，屬驗證環境因素而非 CSS 缺陷），再驗 animation.currentTime
     前進 + transform 隨時間位移（向左、負值）；最後 pause + seek(50%) 驗 keyframes 可解析
     （to = translate(calc(-50% - 0.1rem))），且位移量 = -(inner 寬/4 + 0.1rem/2)
     （0.1rem 的 px 值各斷點不同，由 keyframe 反推，linear 內插）。
  E. 補償生效（保真基準法）：在**同一 viewport** 另開 / 量測 index footer（.ftco-footer .scroller-box .scroller），
     逐項比對 .scroller__inner padding-block、.tag-list li padding、li font-size/width、flex-wrap、
     animation（name / duration / timing-function）必須完全一致；
     桌面額外驗絕對值 32px / 1.6px / 1108px / 22px。
  F. 幾何：.scroller 寬 <= .foooter-mail 寬 + 1；.scroller overflow == hidden；無水平溢出；
     F5/F6（2026-10-08 新增）「.foooter-mail 未撐破所屬 grid」＋「寬 <= viewport 寬」——
     舊版只驗 scroller <= mail，當 .foooter-mail 走 shrink-to-fit 被 .scroller{max-width:2000px}
     撐到 2000px（平板 1108px）時兩邊同步變大、照樣 PASS，抓不到「跑馬燈橫貫 footer」的缺陷。
  G. 相鄰文字仍在：.foooter-mail 內 .p1 仍含 "Available for" / "takeaway & Relaxing"
  H. index footer 無回歸：/ 的 .ftco-footer .scroller-box 仍 data-animated + 4 子節點 + padding-block 32px
     + li 桌面值 1108px / 22px + 動畫 scroll / 60s / linear（H1–H7）
  I. prefers-reduced-motion: reduce 時：不設 data-animated、仍無水平溢出（驗證防護 overflow:hidden）、
     I5/I6 同一 grid / viewport 越欄防線（2026-10-08 新增：無動畫時 li{width:1108px} 更容易撐爆欄位）
多個 viewport：桌面 1280×800 / 平板 768×1024 / 行動 390×844，各存一張 about footer 截圖。
（CDP 連線後會啟用 Network.setCacheDisabled，避免量到舊版 CSS。）
"""
import asyncio, base64, json, re, urllib.request
import websockets

BASE = "http://localhost:8081"
ROOT = "/home/kei/Desktop/betweencoffee_delivery_enhance"
CDP = "http://localhost:9222"

MEASURE_JS = r"""
(function(){
  var out = {};

  // A. 舊結構
  out.old_el_exists = !!document.querySelector('.footer-mail-inner');
  out.old_rule_refs = document.querySelectorAll('.footer-mail-inner').length;
  out.mailto_hrefs = Array.prototype.slice.call(document.querySelectorAll('a[href^="mailto:"]'))
      .map(function(a){ return a.getAttribute('href'); });

  var mail = document.querySelector('.foooter-mail');
  out.foooter_mail_found = !!mail;

  // B. 新結構
  var box = mail ? mail.querySelector('.scroller-box') : null;
  out.scroller_box_found = !!box;
  var sc = box ? box.querySelector('.scroller') : null;
  out.scroller_found = !!sc;
  var inner = sc ? sc.querySelector('.scroller__inner') : null;
  out.inner_found = !!inner;
  out.inner_is_taglist = inner ? inner.classList.contains('tag-list') : null;
  out.li_raw_count = inner ? inner.querySelectorAll(':scope > li').length : 0;
  // 原始 li = 排除 main.js 複製出的 aria-hidden 分身（正本才代表 HTML 內容）
  var origLis = inner ? Array.prototype.slice.call(inner.querySelectorAll(':scope > li'))
      .filter(function(li){ return li.getAttribute('aria-hidden') !== 'true'; }) : [];
  out.li_orig_count = origLis.length;
  out.li_texts = origLis.map(function(li){ return li.textContent.trim(); });

  // C. JS 生效
  out.data_animated = sc ? sc.getAttribute('data-animated') : null;
  out.inner_child_count = inner ? inner.children.length : 0;
  out.aria_hidden_count = inner ? inner.querySelectorAll('[aria-hidden="true"]').length : 0;

  // D. 動畫
  if (inner) {
    var ics = getComputedStyle(inner);
    out.anim_name = ics.animationName;
    out.anim_state = ics.animationPlayState;
    out.anim_duration = ics.animationDuration;
    out.anim_timing_function = ics.animationTimingFunction;
    out.transform_now = ics.transform;
    // 動畫時鐘（headless tab 無 BeginFrame 時 startTime 會停留 null = pending）
    out.anim_start_time = null;
    out.anim_current_time = null;
    var anims = inner.getAnimations ? inner.getAnimations() : [];
    out.anim_count = anims.length;
    if (anims.length) {
      out.anim_start_time = anims[0].startTime;
      out.anim_current_time = anims[0].currentTime;
    }
    out.inner_rect_w = inner.getBoundingClientRect().width;
  }
  // E. 補償
  if (inner) {
    var cs = getComputedStyle(inner);
    out.inner_pad_top = cs.paddingTop;
    out.inner_pad_bottom = cs.paddingBottom;
    out.inner_display = cs.display;
    out.inner_flex_wrap = cs.flexWrap;
    var li = inner.querySelector(':scope > li');
    if (li) {
      var lcs = getComputedStyle(li);
      out.li_pad = lcs.padding;
      out.li_width_css = lcs.width;
      out.li_font_size = lcs.fontSize;
      out.li_text_align = lcs.textAlign;
    }
  }
  // F. 幾何
  if (sc && mail) {
    var sr = sc.getBoundingClientRect(), mr = mail.getBoundingClientRect();
    out.scroller_w = Math.round(sr.width);
    out.mail_w = Math.round(mr.width);
    out.scroller_fits = sr.width <= mr.width + 1;
    out.scroller_overflow = getComputedStyle(sc).overflow;
    out.scroller_min_width = getComputedStyle(sc).minWidth;
  }
  if (box) {
    var br = box.getBoundingClientRect();
    out.box_w = Math.round(br.width);
    out.box_h = Math.round(br.height);
    out.box_fits = out.mail_w === undefined ? null : br.width <= out.mail_w + 1;
  }
  out.doc_scroll_w = document.documentElement.scrollWidth;
  out.inner_w = window.innerWidth;
  out.no_h_overflow = out.doc_scroll_w <= out.inner_w + 1;

  // F5/F6（2026-10-08 新增）：跑馬燈必須被限制在自己的 grid 欄位內。
  // 背景：F2/F3 只驗「scroller <= .foooter-mail」，當 .foooter-mail 因 justify-self:start 走
  // shrink-to-fit、被 .scroller{max-width:2000px} 撐到 2000px 時，兩邊同時變大 → 舊檢查照樣 PASS
  // （實測：平板 1108 / 行動 2000，全靠 #bc-bg-footer{overflow:hidden} 裁掉 → 視覺越欄）。
  // 故改驗「所屬 grid 不溢出」＋「不寬於 viewport」，直接抓越欄這個症狀。
  if (mail) {
    var gp = mail.parentElement;
    if (gp) {
      out.parent_grid_tag = gp.tagName.toLowerCase() + '.' + String(gp.className).replace(/\s+/g, '.');
      out.parent_grid_scroll_w = gp.scrollWidth;
      out.parent_grid_client_w = gp.clientWidth;
      out.grid_no_overflow = gp.scrollWidth <= gp.clientWidth + 1;
    }
    out.mail_fits_win = Math.round(mail.getBoundingClientRect().width) <= window.innerWidth + 1;
  }

  // G. 相鄰文字
  if (mail) {
    var p1 = mail.querySelector('.p1');
    out.p1_text = p1 ? p1.textContent.replace(/\s+/g, ' ').trim() : null;
  }

  // H. index footer（首頁 = 保真基準；about 的 E 項會在同 viewport 比對這裡的值）
  var ft = document.querySelector('.ftco-footer .scroller-box .scroller');
  if (ft) {
    var fin = ft.querySelector('.scroller__inner');
    out.ftco_found = true;
    out.ftco_data_animated = ft.getAttribute('data-animated');
    out.ftco_child_count = fin ? fin.children.length : 0;
    out.ftco_inner_pad_top = fin ? getComputedStyle(fin).paddingTop : null;
    out.ftco_inner_pad_bottom = fin ? getComputedStyle(fin).paddingBottom : null;
    out.ftco_overflow = getComputedStyle(ft).overflow;
    out.ftco_inner_flex_wrap = fin ? getComputedStyle(fin).flexWrap : null;
    if (fin) {
      var fics = getComputedStyle(fin);
      out.ftco_anim_name = fics.animationName;
      out.ftco_anim_duration = fics.animationDuration;
      out.ftco_anim_timing_function = fics.animationTimingFunction;
      out.ftco_anim_state = fics.animationPlayState;
    }
    var fli = fin ? fin.querySelector(':scope > li') : null;
    if (fli) {
      var flcs = getComputedStyle(fli);
      out.ftco_li_pad = flcs.padding;
      out.ftco_li_width_css = flcs.width;
      out.ftco_li_font_size = flcs.fontSize;
      out.ftco_li_text_align = flcs.textAlign;
    }
  }
  return out;
})()
"""

# 動畫取樣：transform + 動畫時鐘（startTime / currentTime）
ANIM_SAMPLE_JS = r"""
(function(){
  var i = document.querySelector('.foooter-mail .scroller__inner');
  if (!i) return null;
  var a = (i.getAnimations ? i.getAnimations() : []);
  return {
    t: getComputedStyle(i).transform,
    count: a.length,
    start: a.length ? a[0].startTime : null,
    now: a.length ? a[0].currentTime : null
  };
})()
"""

# 動畫確定性驗證：pause + seek 到 50%（30s），讀 computed transform 與 keyframes，再復原播放
ANIM_SEEK_JS = r"""
(function(){
  var i = document.querySelector('.foooter-mail .scroller__inner');
  if (!i || !i.getAnimations) return null;
  var a = i.getAnimations()[0];
  if (!a) return null;
  var w = i.getBoundingClientRect().width;
  a.pause();
  a.currentTime = 30000;            // 60s 的 50%
  var t = getComputedStyle(i).transform;
  var kf = [];
  try { kf = a.effect.getKeyframes().map(function(k){ return k.transform || null; }); } catch (e) {}
  a.currentTime = 0;
  a.play();                          // 復原，後續截圖維持跑馬燈起點
  return { w: w, t: t, keyframes: kf };
})()
"""


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
        # 避免讀到舊版 bc-bg-footer.css（本次改了補償規則，需確保量到的是最新 CSS）
        await send(msg("Network.enable"))
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
                if await evaljs("document.readyState === 'complete'"):
                    break
            await asyncio.sleep(1.2)  # 等 main.js 初始化 .scroller

        async def set_viewport(w, h):
            await send(msg("Emulation.setDeviceMetricsOverride",
                           {"width": w, "height": h, "deviceScaleFactor": 1, "mobile": False}))
            await asyncio.sleep(0.4)

        async def shot(name, sel=".foooter-mail"):
            rr = await evaljs(
                "(function(){var e=document.querySelector('" + sel + "');"
                "if(!e)return null;var r=e.getBoundingClientRect();"
                "return {x:r.left+window.scrollX,y:r.top+window.scrollY,w:r.width,h:r.height};})()")
            if not rr:
                print(f"   shot skipped (no {sel})")
                return
            res = await send(msg("Page.captureScreenshot", {
                "format": "png", "captureBeyondViewport": True,
                "clip": {"x": rr["x"], "y": rr["y"], "width": rr["w"], "height": rr["h"], "scale": 1}}))
            data = res.get("data")
            if data:
                path = f"{ROOT}/_verify_footer_scroller_{name}.png"
                with open(path, "wb") as f:
                    f.write(base64.b64decode(data))
                print(f"   shot -> {path}")


        async def force_frames(n=2):
            """強制 headless tab 產生 BeginFrame。

            本 CDP tab 沒有 frame producer，CSS animation 會停在 pending
            （startTime=null / currentTime=0、computed transform 為 identity），
            要先用 1×1 截圖逼出 frame，動畫才會取得 startTime 並隨時間前進。
            這是驗證環境（非 CSS）因素：標準 Chrome 視窗會正常播動畫。
            """
            for _ in range(n):
                await send(msg("Page.captureScreenshot", {
                    "format": "png",
                    "clip": {"x": 0, "y": 0, "width": 1, "height": 1, "scale": 1}}))


        # ================= /about/：各 viewport =================
        for w, h, name in ((1280, 800, "desktop"), (768, 1024, "tablet"), (390, 844, "mobile")):
            await set_viewport(w, h)
            await goto(f"{BASE}/about/")
            await evaljs("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(1.0)
            # 先逼出 frame，讓 CSS animation 從 pending 進入 running 後才量測
            await force_frames(2)
            m = await evaljs(MEASURE_JS) or {}

            print(f"\n=== /about/ {w}x{h} ({name}) ===")
            # A
            failures.append(check("A1 .footer-mail-inner 已移除", m.get("old_el_exists") is False,
                                  m.get("old_rule_refs")))
            failures.append(check("A2 footer 內無 mailto:hello@betweencoffee.hk",
                                  not any("hello@betweencoffee.hk" in (x or "")
                                          for x in (m.get("mailto_hrefs") or [])),
                                  m.get("mailto_hrefs")))
            # B
            failures.append(check("B1 .foooter-mail 存在", m.get("foooter_mail_found") is True))
            failures.append(check("B2 .scroller-box 存在", m.get("scroller_box_found") is True))
            failures.append(check("B3 ul.tag-list.scroller__inner 存在",
                                  m.get("inner_found") is True and m.get("inner_is_taglist") is True))
            failures.append(check("B4 原始（非複製）li = 2 且文字為 12 次 BETWEEN 串",
                                  m.get("li_orig_count") == 2
                                  and len(m.get("li_texts") or []) == 2
                                  and all(t.startswith("BETWEEN") and t.count("BETWEEN") == 12
                                          for t in (m.get("li_texts") or [])),
                                  f"原始 {m.get('li_orig_count')} / 全部 {m.get('li_raw_count')}"
                                  f"（文字 {[t.count('BETWEEN') for t in (m.get('li_texts') or [])]}）"))
            # C
            failures.append(check("C1 data-animated=true", m.get("data_animated") == "true",
                                  m.get("data_animated")))
            failures.append(check("C2 .scroller__inner 子節點 = 4（無縫循環）",
                                  m.get("inner_child_count") == 4, m.get("inner_child_count")))
            failures.append(check("C3 複製品 aria-hidden = 2", m.get("aria_hidden_count") == 2,
                                  m.get("aria_hidden_count")))
            # D
            failures.append(check("D1 animation-name = scroll", m.get("anim_name") == "scroll",
                                  m.get("anim_name")))
            failures.append(check("D2 animation-play-state = running", m.get("anim_state") == "running",
                                  m.get("anim_state")))
            failures.append(check("D2b animation 60s / linear / infinite（與 style-utilities.css 一致）",
                                  m.get("anim_duration") == "60s"
                                  and m.get("anim_timing_function") == "linear",
                                  f"{m.get('anim_duration')} {m.get('anim_timing_function')}"))
            t1 = m.get("transform_now")
            failures.append(check("D3 keyframes / 動畫時鐘存在（computed 有 animation）",
                                  (m.get("anim_count") or 0) >= 1
                                  and m.get("anim_start_time") is not None,
                                  f"animations={m.get('anim_count')} startTime={m.get('anim_start_time')}"
                                  f" currentTime={m.get('anim_current_time')}"))
            # 本 tab 無 frame producer → 取樣前先逼出 BeginFrame，動畫才會前進
            await force_frames(2)
            s1 = await evaljs(ANIM_SAMPLE_JS) or {}
            await asyncio.sleep(0.8)
            await force_frames(2)
            s2 = await evaljs(ANIM_SAMPLE_JS) or {}
            failures.append(check("D4 animation.currentTime 隨時間前進（動畫真的在跑）",
                                  s1.get("now") is not None and s2.get("now") is not None
                                  and s2.get("now") > s1.get("now"),
                                  f"currentTime {s1.get('now')} -> {s2.get('now')}"))
            failures.append(check("D5 transform 隨時間往左位移（負值，非 identity）",
                                  s1.get("t") not in (None, "none")
                                  and s2.get("t") not in (None, "none")
                                  and s1.get("t") != s2.get("t")
                                  and s2.get("t") != "matrix(1, 0, 0, 1, 0, 0)",
                                  f"量測時 {t1}；取樣 {s1.get('t')} -> {s2.get('t')}"))
            # D6 確定性驗證（與 frame 產生無關）：seek 到 50% 應為 -(inner寬/4 + 0.1rem/2)
            # 0.1rem 在不同斷點的 px 值不同（html font-size 會變），故直接由 keyframe 的
            # calc(-50% - Npx) 反推 N，不寫死 1.6px，讓三個 viewport 都是精確比對。
            seek = await evaljs(ANIM_SEEK_JS) or {}
            kf_list = seek.get("keyframes") or []
            kf_end = next((k for k in kf_list if k and "translate" in k), None)
            mm_end = re.search(r"calc\(-50% - ([\d.]+)px\)", kf_end or "")
            kf_px = float(mm_end.group(1)) if mm_end else None
            exp_tx = None
            got_tx = None
            try:
                w_inner = float(seek.get("w") or 0)
                exp_tx = -(w_inner / 4 + (kf_px if kf_px is not None else 0.8) / 2)
                mm = re.match(r"matrix\(1, 0, 0, 1, (-?[\d.]+), (-?[\d.]+)\)", seek.get("t") or "")
                got_tx = float(mm.group(1)) if mm else None
            except Exception:
                got_tx = None
            failures.append(check("D6 pause+seek 50% 位移量 = -(inner寬/4 + 0.1rem/2)（keyframes 有效）",
                                  got_tx is not None and exp_tx is not None and abs(got_tx - exp_tx) <= 2.0,
                                  f"got {got_tx} vs expected {None if exp_tx is None else round(exp_tx, 2)}"
                                  f"（inner 寬 {seek.get('w')}、0.1rem={kf_px}px）"))
            failures.append(check("D7 keyframes 解析出 translate 終點（to = translate calc(-50% - .1rem)）",
                                  kf_px is not None
                                  and re.fullmatch(r"translate\(calc\(-50% - [\d.]+px\)\)", kf_end or "")
                                  is not None,
                                  f"{kf_list} -> 0.1rem = {kf_px}px"))
            await shot(name)  # 先截 about 頁（下方 E 會切到 / 取基準）
            # E（保真基準法：同一 viewport 的 index footer 計算值即為正解；不寫死單一斷點數值）
            await goto(f"{BASE}/")
            mi = await evaljs(MEASURE_JS) or {}
            print(f"   [基準] index footer @ {w}x{h}：inner {mi.get('ftco_inner_pad_top')}/"
                  f"{mi.get('ftco_inner_pad_bottom')}、li {mi.get('ftco_li_pad')} "
                  f"{mi.get('ftco_li_font_size')} {mi.get('ftco_li_width_css')} "
                  f"wrap={mi.get('ftco_inner_flex_wrap')}")
            failures.append(check("E1 .scroller__inner padding-block 與 index footer 一致（補償生效）",
                                  m.get("inner_pad_top") == mi.get("ftco_inner_pad_top")
                                  and m.get("inner_pad_bottom") == mi.get("ftco_inner_pad_bottom")
                                  and m.get("inner_pad_top") not in (None, "0px"),
                                  f"about {m.get('inner_pad_top')}/{m.get('inner_pad_bottom')}"
                                  f" vs index {mi.get('ftco_inner_pad_top')}/{mi.get('ftco_inner_pad_bottom')}"))
            failures.append(check("E2 .tag-list li padding 與 index footer 一致（補償生效）",
                                  m.get("li_pad") == mi.get("ftco_li_pad")
                                  and m.get("li_pad") not in (None, "0px"),
                                  f"about {m.get('li_pad')} vs index {mi.get('ftco_li_pad')}"))
            failures.append(check("E3 li font-size/width 與 index footer 一致（未被 reset 影響）",
                                  m.get("li_font_size") == mi.get("ftco_li_font_size")
                                  and m.get("li_width_css") == mi.get("ftco_li_width_css"),
                                  f"about {m.get('li_font_size')}/{m.get('li_width_css')}"
                                  f" vs index {mi.get('ftco_li_font_size')}/{mi.get('ftco_li_width_css')}"))
            failures.append(check("E4 .scroller__inner flex-wrap 與 index footer 一致（跑馬燈皆 nowrap）",
                                  m.get("inner_flex_wrap") is not None
                                  and m.get("inner_flex_wrap") == mi.get("ftco_inner_flex_wrap"),
                                  f"about {m.get('inner_flex_wrap')} vs index {mi.get('ftco_inner_flex_wrap')}"))
            failures.append(check("E6 animation 屬性與 index footer 一致（name / duration / timing）",
                                  m.get("anim_name") is not None
                                  and m.get("anim_name") == mi.get("ftco_anim_name")
                                  and m.get("anim_duration") == mi.get("ftco_anim_duration")
                                  and m.get("anim_timing_function") == mi.get("ftco_anim_timing_function"),
                                  f"about {m.get('anim_name')}/{m.get('anim_duration')}/"
                                  f"{m.get('anim_timing_function')} vs index {mi.get('ftco_anim_name')}/"
                                  f"{mi.get('ftco_anim_duration')}/{mi.get('ftco_anim_timing_function')}"))
            if name == "desktop":
                # 桌面另驗絕對值，保留原本可追溯的硬性數值（2rem / .1rem / 桌面 li 尺寸）
                failures.append(check("E5 桌面絕對值 inner 32px / li 1.6px / 1108px / 22px",
                                      m.get("inner_pad_top") == "32px"
                                      and m.get("inner_pad_bottom") == "32px"
                                      and m.get("li_pad") == "1.6px"
                                      and m.get("li_width_css") == "1108px"
                                      and m.get("li_font_size") == "22px",
                                      f"{m.get('inner_pad_top')}/{m.get('inner_pad_bottom')}、"
                                      f"{m.get('li_pad')}、{m.get('li_width_css')}、{m.get('li_font_size')}"))
            # F
            failures.append(check("F1 .scroller overflow = hidden", m.get("scroller_overflow") == "hidden",
                                  m.get("scroller_overflow")))
            failures.append(check("F2 .scroller 寬 <= .foooter-mail 寬", m.get("scroller_fits") is True,
                                  f"{m.get('scroller_w')} <= {m.get('mail_w')}"))
            failures.append(check("F3 .scroller-box 不超出 .foooter-mail", m.get("box_fits") is True,
                                  f"{m.get('box_w')} / {m.get('mail_w')}"))
            failures.append(check("F4 無水平溢出", m.get("no_h_overflow") is True,
                                  f"scrollW {m.get('doc_scroll_w')} vs innerW {m.get('inner_w')}"))
            failures.append(check("F5 .foooter-mail 未撐破所屬 grid（跑馬燈不越欄）",
                                  m.get("grid_no_overflow") is True,
                                  f"grid scrollW {m.get('parent_grid_scroll_w')} vs clientW "
                                  f"{m.get('parent_grid_client_w')}（{m.get('parent_grid_tag')}）"))
            failures.append(check("F6 .foooter-mail 寬 <= viewport 寬（跑馬燈被欄位裁切、不橫貫全寬）",
                                  m.get("mail_fits_win") is True,
                                  f"{m.get('mail_w')} <= {m.get('inner_w')}"))
            # G
            failures.append(check("G1 \"Available for takeaway & Relaxing\" 仍在",
                                  "Available for" in (m.get("p1_text") or "")
                                  and "takeaway" in (m.get("p1_text") or ""),
                                  m.get("p1_text")))

        # ================= / ：index footer 回歸 =================
        await set_viewport(1280, 800)
        await goto(f"{BASE}/")
        m2 = await evaljs(MEASURE_JS) or {}
        print("\n=== / (index footer 回歸) 1280x800 ===")
        failures.append(check("H1 .ftco-footer .scroller 存在", m2.get("ftco_found") is True))
        failures.append(check("H2 data-animated=true", m2.get("ftco_data_animated") == "true",
                              m2.get("ftco_data_animated")))
        failures.append(check("H3 子節點 = 4", m2.get("ftco_child_count") == 4,
                              m2.get("ftco_child_count")))
        failures.append(check("H4 padding-block = 32px（未被本次 CSS 影響）",
                              m2.get("ftco_inner_pad_top") == "32px"
                              and m2.get("ftco_inner_pad_bottom") == "32px",
                              f"{m2.get('ftco_inner_pad_top')} / {m2.get('ftco_inner_pad_bottom')}"))
        failures.append(check("H5 overflow = hidden", m2.get("ftco_overflow") == "hidden",
                              m2.get("ftco_overflow")))
        failures.append(check("H6 li 桌面尺寸仍為 1108px / 22px（本斷點絕對值）",
                              m2.get("ftco_li_width_css") == "1108px"
                              and m2.get("ftco_li_font_size") == "22px",
                              f"{m2.get('ftco_li_width_css')} / {m2.get('ftco_li_font_size')}"))
        failures.append(check("H7 index footer animation 仍為 scroll / 60s / linear（未受本次 CSS 影響）",
                              m2.get("ftco_anim_name") == "scroll"
                              and m2.get("ftco_anim_duration") == "60s"
                              and m2.get("ftco_anim_timing_function") == "linear",
                              f"{m2.get('ftco_anim_name')}/{m2.get('ftco_anim_duration')}/"
                              f"{m2.get('ftco_anim_timing_function')}"))
        await shot("index_footer", ".ftco-footer .scroller-box")

        # ================= prefers-reduced-motion: reduce =================
        await send(msg("Emulation.setEmulatedMedia", {
            "features": [{"name": "prefers-reduced-motion", "value": "reduce"}]}))
        await set_viewport(390, 844)
        await goto(f"{BASE}/about/")
        await asyncio.sleep(0.6)
        m3 = await evaljs(MEASURE_JS) or {}
        print("\n=== /about/ prefers-reduced-motion: reduce (390x844) ===")
        failures.append(check("I1 不設 data-animated",
                              m3.get("data_animated") in (None, "false"), m3.get("data_animated")))
        failures.append(check("I2 仍維持原始 2 個 li", m3.get("inner_child_count") == 2,
                              m3.get("inner_child_count")))
        failures.append(check("I3 無水平溢出（防護 overflow:hidden 生效）",
                              m3.get("no_h_overflow") is True,
                              f"scrollW {m3.get('doc_scroll_w')} vs innerW {m3.get('inner_w')}"))
        failures.append(check("I4 .scroller 仍被裁切",
                              m3.get("scroller_overflow") == "hidden", m3.get("scroller_overflow")))
        failures.append(check("I5（無動畫狀態也）未撐破所屬 grid",
                              m3.get("grid_no_overflow") is True,
                              f"grid scrollW {m3.get('parent_grid_scroll_w')} vs clientW "
                              f"{m3.get('parent_grid_client_w')}"))
        failures.append(check("I6（無動畫狀態也）.foooter-mail 寬 <= viewport 寬",
                              m3.get("mail_fits_win") is True,
                              f"{m3.get('mail_w')} <= {m3.get('inner_w')}"))
        await shot("mobile_reduced_motion")
        await send(msg("Emulation.setEmulatedMedia", {"features": []}))

    total = len(failures)
    bad = sum(1 for f in failures if not f)
    print(f"\n===== 合計 {total} 項，PASS {total - bad}，FAIL {bad} =====")
    return bad


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))

