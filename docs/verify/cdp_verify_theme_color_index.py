#!/usr/bin/env python3
"""CDP 驗證：index.html「第二主題色 → 第一主題色」（2026-10-08）

使用者指示：「index.html 目前第二主題色改為第一主題色」。
  · 第一主題色＝品牌金 **#c49b63**（`--bc-gold`，單一來源 `bc-components.css :root`）
  · 第二主題色＝**#FCFF4B**／rgb(252,255,75)（`--bc-theme2`，2026-09-21 由使用者指定）

本次改動（4 處 CSS ＋ 3 處版號）：
 1. bc-yama-header.css `:root --bc-yama-circle`：var(--bc-theme2) → var(--bc-gold)（≥769 圓球底色）
 2. bc-yama-header.css `.bc-yama-discount`：var(--bc-theme2) → var(--bc-gold)（≤768 的 -5 積分字色）
 3. bc-gunte-hero.css `.hero_nav > li > button::before`：var(--bc-theme2) → var(--bc-gold)（首屏圓點）
 4. bc-components.css `.bc-floating-cart-badge`：var(--bc-theme2) → var(--bc-gold)（全站數字圓圈）
 註１：≤768 的 yama 圓球底色是硬編碼近黑 #131211，**本次刻意不動**（球內金/白文字層沿用）。
 註２：≥769 球內深字 #1b1b1b 與 hover 白球維持（圓球由亮萊姆改品牌金後仍為 AA 內文）。
 註３：hero 圓點所在的首屏是**自動輪播**（`-current` 類別會隨輪播在 7 顆圓點間移動），
       且 `::before` 有 `transition: var(--ease-out/.in)`（0.35s／0.3s）→ 「白＋寬 32px」的
       active 狀態會先從「品牌金＋16px」過渡過來；**若在過渡起始瞬間取樣會誤判成金色**。
       因此本腳本在量測前注入 `*{transition:none}` 凍結過渡（顏色/幾何不受影響），
       並另以 CSSOM 靜態檢查 `.‑current::before` 規則本身（C4）作為不依賴時機的防線。

檢查項目
 A 版號：/ 的 bc-yama-header／bc-gunte-hero、全站的 bc-components 皆為 ?v=20261008e（防 1 年快取舊色）
 B yama 圓球：≥769 == rgb(196,155,99)（品牌金）；≤768 == rgb(19,18,17)（近黑，未受影響）
   B0 `.tax-nav` opacity == 1（圓球可見；已凍結過渡避免背景分頁淡入被暫停）
   B4 圓球區域「實際截圖像素」需為品牌金（>500 點）＝渲染層證據
 C 首屏圓點 ::before：`.-current` 為白（寬 32px；≤743.98px 一層為 24px）、其餘 6 顆為品牌金（共 7 顆）
   C0／C4 另做 CSSOM 靜態檢查（基底規則＝var(--bc-gold, #c49b63)、`.-current` 規則＝白/32px）
   —— 靜態檢查不受「輪播換頁時 0.3s 過渡」影響，可當長期防線
 D `.bc-floating-cart-badge`（購物車空時 display:none，仍在 DOM）：底色品牌金、數字深字 rgb(14,14,14)
 E **首頁不得再出現任何第二主題色 rgb(252,255,75)**（含 ::before/::after）＝本次改動的回歸防線
 F CSSOM 掃描：已載入 CSS 中除 `:root` 定義外**不得再有規則引用 var(--bc-theme2)**
   → 這條同時涵蓋登入後才會出現的 `.bc-yama-discount`（未登入時 DOM 上量不到）
 G ≥769 球內文字色 == rgb(27,27,27) 且對品牌金對比 ≥ 4.5:1（AA 內文）
 H /about/、/coffee_menu/ 的 badge 同為品牌金、且無第二主題色殘留（bc-components 為全站檔）

前置：Django 127.0.0.1:8081 ＋ CDP 瀏覽器 9222（見 docs/verify/CDP_SETUP.md）。
執行：setsid nohup python3 docs/verify/cdp_verify_theme_color_index.py > /tmp/vtc.log 2>&1 < /dev/null &
"""
import asyncio, json, urllib.request, base64
import websockets

try:                      # 圓球「實際像素」檢查用；缺 PIL 時自動略過該項
    import io
    from PIL import Image
    PIL_OK = True
except Exception:         # pragma: no cover
    PIL_OK = False

BASE = "http://127.0.0.1:8081"
GOLD = "rgb(196, 155, 99)"      # #c49b63 品牌金（第一主題色）
LIME = "rgb(252, 255, 75)"      # #FCFF4B 第二主題色
NEAR_BLACK = "rgb(19, 18, 17)"  # #131211 ≤768 圓球底色
DARK_TEXT = "rgb(27, 27, 27)"   # #1b1b1b ≥769 球內文字
BADGE_TEXT = "rgb(14, 14, 14)"  # #0e0e0e 數字深字
VERSION = "20261008e"

VIEWPORTS = [(1440, 900, False), (1024, 800, False), (768, 900, True), (390, 844, True)]
OTHER_PAGES = [("about", "/about/"), ("coffee_menu", "/coffee_menu/")]

JS = r"""
(function(){
  var LIME='rgb(252, 255, 75)';
  function pathOf(el){
    var parts=[], n=el;
    while(n && n.nodeType===1 && parts.length<4){
      var p=n.tagName.toLowerCase();
      if(n.id) p+='#'+n.id;
      else if(n.className && n.className.toString().trim())
        p+='.'+n.className.toString().trim().split(/\s+/).slice(0,2).join('.');
      parts.unshift(p); n=n.parentElement;
    }
    return parts.join('>');
  }
  var out={};

  /* A. 版號 */
  out.versions={};
  [].forEach.call(document.querySelectorAll('link[rel=stylesheet]'), function(l){
    var m=/css\/(bc-components|bc-yama-header|bc-gunte-hero)\.css\?v=([0-9a-z]+)/.exec(l.href);
    if(m) out.versions[m[1]]=m[2];
  });

  /* B. yama 圓球 */
  var yama=document.querySelector('.bc-yama');
  var ball=document.querySelector('.bc-yama .tax-nav a');
  var ballText=document.querySelector('.bc-yama .tax-nav a p > span:first-child');
  var br=ball?ball.getBoundingClientRect():null;
  var tn=document.querySelector('.bc-yama .tax-nav');
  out.yama_display = yama ? getComputedStyle(yama).display : 'absent';
  out.yama_ball_bg = ball ? getComputedStyle(ball).backgroundColor : 'absent';
  out.yama_ball_text_color = ballText ? getComputedStyle(ballText).color : 'absent';
  out.yama_ball_size = br ? (Math.round(br.width)+'x'+Math.round(br.height)) : 'absent';
  out.yama_ball_rect = br ? [Math.round(br.x), Math.round(br.y), Math.round(br.width), Math.round(br.height)] : null;
  /* 圓球可見性：.tax-nav 需有 init（淡入）。注意 Chrome 對「被遮蔽／背景分頁」會暫停動畫 →
     淡入可能凍結在 opacity:0；本腳本已注入 *{transition:none} 讓它直接跳到終值，
     故這裡量到的 0 代表真的沒加 init（真缺陷）。 */
  out.yama_nav_opacity = tn ? getComputedStyle(tn).opacity : 'absent';
  out.yama_nav_cls = tn ? tn.className : 'absent';
  out.theme2_var = getComputedStyle(document.documentElement).getPropertyValue('--bc-theme2').trim();
  out.gold_var = getComputedStyle(document.documentElement).getPropertyValue('--bc-gold').trim();

  /* C. 首屏圓點 */
  out.dots=[];
  [].forEach.call(document.querySelectorAll('.bc-gunte-hero .hero_nav > li > button'), function(b){
    out.dots.push({
      current: b.classList.contains('-current'),
      bg: getComputedStyle(b,'::before').backgroundColor,
      w: getComputedStyle(b,'::before').width
    });
  });
  /* C0/C4：CSSOM 靜態規則（不依賴輪播時機） */
  out.dot_rules=[];
  (function(){
    function walk(list){
      [].forEach.call(list, function(r){
        if(r.cssRules && !r.selectorText){ walk(r.cssRules); return; }
        var sel=r.selectorText||'';
        if(sel.indexOf('hero_nav')<0 || sel.indexOf('::before')<0) return;
        out.dot_rules.push({sel:sel.trim(), bg:r.style.getPropertyValue('background'),
                            bgImp:r.style.getPropertyPriority('background'),
                            w:r.style.getPropertyValue('width')});
      });
    }
    [].forEach.call(document.styleSheets, function(ss){
      if((ss.href||'').indexOf('bc-gunte-hero')<0) return;
      var rules=null; try{ rules=ss.cssRules; }catch(e){ return; }
      if(rules) walk(rules);
    });
  })();

  /* D. 浮動購物車數字圓圈 */
  var badge=document.querySelector('.bc-floating-cart-badge');
  out.badge = badge ? {
    exists: true,
    bg: getComputedStyle(badge).backgroundColor,
    color: getComputedStyle(badge).color,
    display: getComputedStyle(badge).display,
    text: (badge.textContent||'').trim()
  } : {exists:false};

  /* E. 第二主題色殘留掃描（含偽元素） */
  var lime=[], all=document.querySelectorAll('*');
  for(var i=0;i<all.length;i++){
    var el=all[i], s=getComputedStyle(el), props=[];
    if(s.backgroundColor===LIME) props.push('bg');
    if(s.color===LIME) props.push('color');
    if(s.borderTopColor===LIME||s.borderRightColor===LIME||s.borderBottomColor===LIME||s.borderLeftColor===LIME) props.push('border');
    if(s.fill===LIME) props.push('fill');
    if(s.stroke===LIME) props.push('stroke');
    ['::before','::after'].forEach(function(p){
      var ps=getComputedStyle(el,p);
      if(ps.backgroundColor===LIME) props.push(p+'bg');
      if(ps.color===LIME) props.push(p+'color');
      if(ps.fill===LIME) props.push(p+'fill');
    });
    if(props.length) lime.push({path:pathOf(el), props:props.join(',')});
  }
  out.lime=lime;

  /* F. CSSOM：已載入樣式表中「非 :root 定義」的 var(--bc-theme2) 引用 */
  var refs=[];
  function walk(list, href){
    [].forEach.call(list, function(r){
      if(r.cssRules){ walk(r.cssRules, href); return; }
      var sel=(r.selectorText||'').trim();
      if(sel===':root') return;   /* 定義行所在區塊（:root 宣告 --bc-theme2 本體） */
      var t=r.cssText||'';
      if(t.indexOf('--bc-theme2')>=0) refs.push({sheet:(href||'').split('/').pop(), sel:sel, css:t.slice(0,140)});
    });
  }
  [].forEach.call(document.styleSheets, function(ss){
    var rules=null;
    try{ rules=ss.cssRules; }catch(e){ return; }
    if(rules) walk(rules, ss.href);
  });
  out.theme2_refs=refs;
  return out;
})()
"""

# 凍結過渡：hero 圓點的 active 狀態（白＋32px）是「過渡」出來的，於過渡起始瞬間取樣會誤判成
# 品牌金＋16px（2026-10-08 實測：輪播換頁後 0.6s 內量到 rgb(215,187,149)/21.1px 的過渡中值）。
# 只關 transition，不影響顏色、尺寸、幾何等本腳本要驗的值。
FREEZE = ("(()=>{var s=document.createElement('style');s.id='vtc-freeze';"
          "s.textContent='*,*::before,*::after{transition:none !important;}';"
          "(document.head||document.documentElement).appendChild(s);"
          "return !!document.getElementById('vtc-freeze');})()")


async def main():
    req = urllib.request.Request("http://127.0.0.1:9222/json/new?about:blank", method="PUT")
    tab = json.loads(urllib.request.urlopen(req).read().decode())
    fails, notes, notes_pix = [], [], []

    async with websockets.connect(tab["webSocketDebuggerUrl"], max_size=None) as ws:
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

        def chk(cond, label, detail=""):
            if cond:
                print(f"  \033[32mPASS\033[0m {label}")
            else:
                print(f"  \033[31mFAIL\033[0m {label} {detail}")
                fails.append(f"{label} {detail}")

        await send(msg("Page.enable"))
        await send(msg("Runtime.enable"))
        await send(msg("Network.enable"))
        await send(msg("Page.setCacheDisabled", {"cacheDisabled": True}))
        await send(msg("Network.setCacheDisabled", {"cacheDisabled": True}))

        async def ev(expr):
            r = await send(msg("Runtime.evaluate", {"expression": expr, "returnByValue": True}))
            return r.get("result", {}).get("value")

        async def goto(path, w, h, mob, tag):
            await send(msg("Emulation.setDeviceMetricsOverride",
                           {"width": w, "height": h, "deviceScaleFactor": 1, "mobile": mob}))
            sep = "&" if "?" in path else "?"
            await send(msg("Page.navigate", {"url": f"{BASE}{path}{sep}vt={tag}"}))
            for _ in range(40):
                if await ev("document.readyState==='complete'"):
                    break
                await asyncio.sleep(0.4)
            await asyncio.sleep(1.2)   # 等延遲 JS（.init 淡入、-current class）就位
            await ev(FREEZE)           # 凍結過渡（否則輪播換頁後會量到過渡中的顏色/寬度）
            await asyncio.sleep(0.3)

        def lum(rgb):
            def ch(c):
                c /= 255.0
                return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
            r, g, b = [int(x) for x in rgb.replace("rgb(", "").replace(")", "").split(",")]
            return 0.2126 * ch(r) + 0.7152 * ch(g) + 0.0722 * ch(b)

        def contrast(a, b):
            la, lb = lum(a), lum(b)
            hi, lo = max(la, lb), min(la, lb)
            return round((hi + 0.05) / (lo + 0.05), 2)

        async def ball_gold_pixels(rect):
            """裁切圓球區域截圖並數「品牌金」像素（證明圓球真的渲染出來，不只是 computed 值）。"""
            if not PIL_OK or not rect:
                return -1
            clip = {"x": max(0, rect[0] - 6), "y": max(0, rect[1] - 6),
                    "width": rect[2] + 12, "height": rect[3] + 12, "scale": 1}
            s = await send(msg("Page.captureScreenshot", {"format": "png", "clip": clip}))
            img = Image.open(io.BytesIO(base64.b64decode(s["data"]))).convert("RGB")
            px = img.load()
            cnt = 0
            for yy in range(0, img.size[1], 3):
                for xx in range(0, img.size[0], 3):
                    p = px[xx, yy]
                    if abs(p[0] - 196) <= 26 and abs(p[1] - 155) <= 26 and abs(p[2] - 99) <= 26:
                        cnt += 1
            return cnt

        # ---------- / 各斷點 ----------
        for w, h, mob in VIEWPORTS:
            print(f"\n=========== / {w}x{h}{' (mobile)' if mob else ''} ===========")
            await goto("/", w, h, mob, f"i{w}")
            v = await ev(JS)
            print("  versions:", v["versions"], "| --bc-theme2:", v["theme2_var"], "| --bc-gold:", v["gold_var"])
            print("  ball:", v["yama_ball_bg"], v["yama_ball_size"], "text:", v["yama_ball_text_color"],
                  "| yama:", v["yama_display"], "| .tax-nav opacity:", v["yama_nav_opacity"], v["yama_nav_cls"])
            print("  dots:", [(d["bg"], d["w"], "current" if d["current"] else "") for d in v["dots"]])
            print("  dot rules:", v["dot_rules"])
            print("  badge:", v["badge"])
            print("  lime hits:", v["lime"])
            print("  theme2 refs:", v["theme2_refs"])

            # A. 版號
            chk(v["versions"].get("bc-yama-header") == VERSION,
                f"A1 bc-yama-header ?v={v['versions'].get('bc-yama-header')} == {VERSION}")
            chk(v["versions"].get("bc-gunte-hero") == VERSION,
                f"A2 bc-gunte-hero ?v={v['versions'].get('bc-gunte-hero')} == {VERSION}")
            chk(v["versions"].get("bc-components") == VERSION,
                f"A3 bc-components ?v={v['versions'].get('bc-components')} == {VERSION}")
            chk(v["gold_var"] == "#c49b63", f"A4 --bc-gold 仍為第一主題色（{v['gold_var']}）")

            # B. 圓球
            if w >= 769:
                chk(v["yama_display"] == "block", f"B1 yama display={v['yama_display']}")
                chk(v["yama_ball_bg"] == GOLD,
                    f"B2 圓球底色={v['yama_ball_bg']}（應為第一主題色 {GOLD}）")
                chk(v["yama_ball_size"].split("x")[0] == v["yama_ball_size"].split("x")[-1]
                    and int(v["yama_ball_size"].split("x")[0]) > 0,
                    f"B3 圓球為正方形且非零（{v['yama_ball_size']}；各層尺寸：1440=174、平板層=150）")
                chk(v["yama_ball_text_color"] == DARK_TEXT,
                    f"G1 球內主行文字={v['yama_ball_text_color']}（應 {DARK_TEXT}）")
                c = contrast(DARK_TEXT, GOLD)
                chk(c >= 4.5, f"G2 深字對品牌金對比={c}:1（AA 內文需 >=4.5）")
                # B0/B4：圓球真的可見且渲染為品牌金（computed 值之外的第二層證據）
                chk(v["yama_nav_opacity"] == "1",
                    f"B0 圓球容器 .tax-nav opacity={v['yama_nav_opacity']}"
                    f"（cls={v['yama_nav_cls']}；需 1＝已淡入、圓球可見）")
                gpx = await ball_gold_pixels(v["yama_ball_rect"])
                if gpx < 0:
                    notes_pix.append(f"{w}: 略過圓球像素檢查（未安裝 PIL）")
                else:
                    chk(gpx > 500, f"B4 圓球區域實際品牌金像素={gpx}（>500；rect={v['yama_ball_rect']}）")
            else:
                chk(v["yama_ball_bg"] == NEAR_BLACK,
                    f"B2 <=768 圓球底色={v['yama_ball_bg']}（應維持近黑 {NEAR_BLACK}，本次不動）")

            # C. 圓點
            chk(len(v["dots"]) == 7, f"C1 圓點數={len(v['dots'])}（應 7）")
            base_rule = next((r for r in v["dot_rules"]
                              if r["sel"] == ".bc-gunte-hero .hero_nav > li > button::before"), None)
            cur_rule = next((r for r in v["dot_rules"] if ".-current::before" in r["sel"]), None)
            chk(base_rule is not None and base_rule["bg"] == "var(--bc-gold, #c49b63)",
                f"C0 圓點基底規則背景={base_rule and base_rule['bg']}（靜態 CSSOM，應為 var(--bc-gold, #c49b63)）")
            chk(cur_rule is not None and cur_rule["bg"] == "rgb(255, 255, 255)"
                and cur_rule["w"] == "32px",
                f"C4 .-current::before 規則={cur_rule}（應背景白、寬 32px，且未被 !important 壓過）")
            cur = [d for d in v["dots"] if d["current"]]
            nrm = [d for d in v["dots"] if not d["current"]]
            # 寬度由斷點決定（≤743.98px 一層：基底 13px／active 24px；其餘：16px／32px）
            base_w = "13px" if w <= 743 else "16px"
            cur_w = "24px" if w <= 743 else "32px"
            chk(all(d["bg"] == GOLD for d in nrm),
                f"C2 一般圓點全為第一主題色（{len(nrm)}/{len(nrm)}，顏色={sorted({d['bg'] for d in nrm})}）")
            chk(all(d["w"] == base_w for d in nrm),
                f"C2c 一般圓點寬度={sorted({d['w'] for d in nrm})}（本斷點應 {base_w}，幾何不變）")
            chk(len(cur) == 1, f"C2b 同時只有 1 顆 -current（實得 {len(cur)}）")
            chk(all(d["bg"] == "rgb(255, 255, 255)" and d["w"] == cur_w for d in cur),
                f"C3 -current 圓點為白＋{cur_w}（實得 {[(d['bg'], d['w']) for d in cur]}；"
                "已凍結過渡，若此處仍是品牌金即為真缺陷）")

            # D. badge
            b = v["badge"]
            chk(b.get("exists"), "D1 .bc-floating-cart-badge 存在於 DOM")
            chk(b.get("bg") == GOLD, f"D2 badge 底色={b.get('bg')}（應為第一主題色 {GOLD}）")
            chk(b.get("color") == BADGE_TEXT, f"D3 badge 數字色={b.get('color')}（應深字 {BADGE_TEXT}）")
            cb = contrast(BADGE_TEXT, GOLD)
            chk(cb >= 4.5, f"D4 數字對品牌金對比={cb}:1")

            # E. 第二主題色不得再出現
            chk(len(v["lime"]) == 0,
                f"E1 首頁無第二主題色 {LIME} 殘留（實得 {len(v['lime'])} 筆：{v['lime'][:3]}）")

            # F. CSSOM
            chk(len(v["theme2_refs"]) == 0,
                f"F1 已載入 CSS 無 var(--bc-theme2) 元件引用（實得 {len(v['theme2_refs'])} 筆：{v['theme2_refs'][:2]}）")

        # ---------- 其他頁（badge 為全站元件）----------
        for name, path in OTHER_PAGES:
            for w, h, mob in [(1440, 900, False), (390, 844, True)]:
                print(f"\n=========== {path} {w}x{h} ===========")
                await goto(path, w, h, mob, f"{name}{w}")
                v = await ev(JS)
                print("  versions:", v["versions"], "| badge:", v["badge"], "| lime:", v["lime"])
                b = v["badge"]
                chk(b.get("exists") and b.get("bg") == GOLD,
                    f"H1 {name} {w} badge 底色={b.get('bg')}（應 {GOLD}）")
                chk(b.get("color") == BADGE_TEXT,
                    f"H2 {name} {w} badge 數字色={b.get('color')}（應 {BADGE_TEXT}）")
                chk(len(v["lime"]) == 0, f"H3 {name} {w} 無第二主題色殘留（實得 {len(v['lime'])} 筆）")
                chk(v["versions"].get("bc-components") == VERSION,
                    f"H4 {name} {w} bc-components ?v={v['versions'].get('bc-components')}")

        await send(msg("Page.close"))

    notes.append("≤768 圓球為硬編碼近黑 #131211：本次僅改 ≥769 的 --bc-yama-circle，故 B2 各斷點都驗。")
    notes.append("E1/F1 為本次改動的回歸防線：日後若再有人把第二主題色套回 index 元件，這兩條會 FAIL。")
    notes.append("量測前已注入 *{transition:none}：hero 圓點 active（白 32px）是過渡出來的，"
                 "輪播換頁瞬間取樣會誤判成品牌金 16px（C0/C4 靜態檢查用以排除此類時機問題）。")
    notes.append("B3 只驗「正方形且非零」：圓球尺寸由各層 media 決定（1440=174、1024/平板層=150），"
                 "本次為純顏色變更、幾何不應變動。")
    for n in notes_pix:
        notes.append(n)
    notes.append("B0/B4 為「圓球可見性」第二層證據（Chrome 對被遮蔽／背景分頁會暫停動畫，"
                 "淡入可能凍結在 opacity:0 → 已用 *{transition:none} 讓它直接跳到終值後再驗）。")
    print("\n=== notes ===")
    for n in notes:
        print(" ", n)
    print(f"\n=== 結果：{'全部通過' if not fails else str(len(fails)) + ' 項失敗'} ===")
    for f in fails:
        print("  FAIL", f)
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))


