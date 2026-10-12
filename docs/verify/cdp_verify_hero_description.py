#!/usr/bin/env python3
"""CDP 驗證：/about/ 的 .hero-description-wrapper 逐字捲動變色模組（原站 1:1）

2026-10-12：完整移植 https://bkkdw26.greydientlab.com/（WordPress 主題 bkkdw
acf/blocks/hero）的 .hero-description-wrapper —— HTML 1:1、Tailwind utility scoped
重建（768 / 1024 斷點）、SplitType 逐字 + GSAP ScrollTrigger scrub 變色 1:1。

本腳本對「同一個視窗尺寸」連續量兩個站（本機 /about/ 與原站首頁），逐項比對：
  A. 結構：.hero-description-wrapper / .hero-description 存在；本機端位置緊接
     .bc-who-section 之後、後接 .row-animation（原站無此兄弟，僅本機驗）
  B. 文案：正規化空白後 textContent 與原站逐字相同（1:1 內文）
  C. SplitType：chars = 228（269 字元 − 41 空白）、words > 0、.number 內 15 個 char
     且其文字 == 100,000,000,000
  D. computed style（字型／字級／行高／字距／padding／margin-top／底色）與原站一致
  E. 捲動逐字變色：以「模組自身 ScrollTrigger 的 start/end」換算動畫進度 p
      （0 / 0.5 / 1），捲到該位置後輪詢到 scrub:1 的 lerp 收斂才讀值
        p=0  → 全部 rgb(97, 97, 97)
        p=1  → 非 .number 字 rgb(255, 255, 255)、.number 字 rgb(226, 252, 7)
        0<p<1 → 「已著色字」必為 chars 前綴（單一前緣）＝ stagger 逐字推進
      跨站比對同一進度：p=0 color 集合相同、p=1 color 陣列完全相等、
      p=0.5 前緣索引 |差| <= 3
  F. 觸發器／進度自檢（本腳本「捲動對準」的前提）
        F1 模組 ScrollTrigger 的 start/end ≈ 幾何換算（±3px）
        F2 每個 p 捲動後實測 progress ≈ p（±0.02）
      某站某 p 若因幾何（如原站 tablet 的 start < 0）夾住而無法到達，該 p 的
      跨站比對自動標 SKIP 並註明站別，不誤判成失敗；F2 的偏離若「全數」由
      該站幾何夾住所致，F2 本身亦標 SKIP（只有非幾何所致的偏離才判 FAIL）
  G. 截圖：兩站同進度位置的視窗截圖寫入 _herocmp/（不進版控）

原站 1:1 參數：start = isTablet ? 'top 54%' : 'top 80%'、end = 'bottom 50%'、
scrub = 1、每字 duration 0.1 / ease none / 位置 index*0.02、先 gsap.set 全灰 #616161；
isTablet 於載入時決定，故每個斷點都重新導覽一次頁面。
用法：站台跑在 8081、CDP 瀏覽器跑在 9222（見 CDP_SETUP.md），且需能連外到原站
（連不上時跨站比對項會標 SKIP，本機端的結構／動畫斷言仍會執行）。

實作要點（2026-10-12 診斷後定案）：
  1. 本 CDP 分頁若被其他視窗遮住／非前景，rAF 會被餓死 —— 實測 rafTicks 恆為 0、
     ScrollTrigger progress 永遠停在 0，於是所有顏色斷言都讀到「初始全灰」。
     故開場即 Emulation.setFocusEmulationEnabled(true)，並以視窗截圖人工複核。
  2. 捲動位置以「模組自身 ScrollTrigger 的 start/end」換算（真值），幾何公式僅
     用於 F1 交叉核對；每次捲動後輪詢 progress 與 color 陣列到穩定才讀值。
"""
import asyncio
import base64
import json
import urllib.request
from pathlib import Path

import websockets

LOCAL = "http://localhost:8081/about/"
ORIG = "https://bkkdw26.greydientlab.com/"
ROOT = Path("/home/kei/Desktop/betweencoffee_delivery_enhance")
SHOTS = ROOT / "_herocmp"

GREY = "rgb(97, 97, 97)"
WHITE = "rgb(255, 255, 255)"
YELLOW = "rgb(226, 252, 7)"
EXPECT_CHARS = 228
EXPECT_NUM = 15
EXPECT_NUM_TEXT = "100,000,000,000"

VPS = [(1280, 900, False, "desktop"), (800, 900, False, "tablet"), (390, 844, True, "mobile")]
PROGRESS = [0.0, 0.5, 1.0]

# 幾何換算（僅供 F1 交叉核對）：start = top − 54%(tablet)/80%*vh、end = bottom − 50%*vh
JS_GEOM = (
    "(function(w){var y=window.scrollY,r=w.getBoundingClientRect(),vh=window.innerHeight;"
    "var isT=window.innerWidth>=768&&window.innerWidth<=1023;"
    "return [r.top+y-(isT?0.54:0.80)*vh, r.bottom+y-0.5*vh];})"
)

# 找出「驅動 .hero-description-wrapper 逐字變色」的那個 ScrollTrigger：
# 先比對 trigger 的 class，再退一步看動畫 target 是否落在 wrapper 內。
JS_PICK = (
    "(function(w){var all=window.ScrollTrigger?ScrollTrigger.getAll():[],i,s,c;"
    "for(i=0;i<all.length;i++){s=all[i];c=s.trigger?(''+s.trigger.className):'';"
    "if(c.indexOf('hero-description-wrapper')>=0)return s;}"
    "for(i=0;i<all.length;i++){s=all[i];"
    "var tg=s.animation&&s.animation.targets?s.animation.targets():null;"
    "if(tg){for(var k=0;k<tg.length;k++){if(w&&w.contains(tg[k]))return s;}}}"
    "return null;})"
)

# 捲到該 ScrollTrigger 的進度 p（真值；找不到 ST 時退回幾何換算），回傳實際落點、
# 是否被捲動範圍夾住，以及 start/end/geo 供 F1 交叉核對。
JS_SEEK = (
    "(function(p){var w=document.querySelector('.hero-description-wrapper');"
    "if(!w)return null;var geo=(" + JS_GEOM + ")(w);"
    "var st=(" + JS_PICK + ")(w);var se=st?[st.start,st.end]:geo;"
    "var max=Math.max(document.documentElement.scrollHeight,document.body.scrollHeight)"
    "-window.innerHeight;var want=se[0]+p*(se[1]-se[0]);"
    "var got=Math.max(0,Math.min(Math.round(want),max));window.scrollTo(0,got);"
    "return {want:Math.round(want),got:got,max:Math.round(max),"
    "clamped:got!==Math.round(want),hasST:!!st,scrollY:Math.round(window.scrollY),"
    "start:+se[0].toFixed(1),end:+se[1].toFixed(1),"
    "geo:[+geo[0].toFixed(1),+geo[1].toFixed(1)]};})"
)

# 輪詢用：該 ScrollTrigger 的 progress + 全部 .char 的 computed color
JS_PROGRESS = (
    "(function(){var w=document.querySelector('.hero-description-wrapper');"
    "var d=document.querySelector('.hero-description-wrapper .hero-description');"
    "var st=w?(" + JS_PICK + ")(w):null;if(!d||!st)return null;"
    "return {progress:+st.progress.toFixed(4),"
    "colors:[].slice.call(d.querySelectorAll('.char')).map(function(c){"
    "return getComputedStyle(c).color;})};})()"
)

JS = r"""
(function () {
  var w = document.querySelector('.hero-description-wrapper');
  var d = document.querySelector('.hero-description-wrapper .hero-description');
  if (!w || !d) { return {ok: false, why: 'missing wrapper/description'}; }
  var chars = [].slice.call(d.querySelectorAll('.char'));
  var words = [].slice.call(d.querySelectorAll('.word'));
  var nums = [].slice.call(d.querySelectorAll('.number .char'));
  var numIdx = [];
  chars.forEach(function (c, i) { if (c.closest('.number')) { numIdx.push(i); } });
  var csW = getComputedStyle(w), csD = getComputedStyle(d);
  var numEl = d.querySelector('.number');
  var y = window.scrollY, r = w.getBoundingClientRect(), vh = window.innerHeight;
  var top = r.top + y, bot = r.bottom + y;
  var isTablet = window.innerWidth >= 768 && window.innerWidth <= 1023;
  function cls(e) { return e ? (e.tagName.toLowerCase() + '.' + (e.className || '')) : ''; }
  return {
    ok: true,
    innerWidth: window.innerWidth, scrollY: Math.round(y), vh: Math.round(vh),
    docTop: Math.round(top), docBottom: Math.round(bot),
    trigStart: Math.round(top - (isTablet ? 0.54 : 0.80) * vh),
    trigEnd: Math.round(bot - 0.5 * vh),
    isTablet: isTablet,
    prev: cls(w.previousElementSibling), next: cls(w.nextElementSibling),
    nChars: chars.length, nWords: words.length, nNum: nums.length, numIdx: numIdx,
    numText: nums.map(function (c) { return c.textContent; }).join(''),
    wordInline: words.length ? words[0].getAttribute('style') : null,
    text: d.textContent.replace(/\s+/g, ' ').trim(),
    cs: {
      wPad: csW.paddingTop + ' ' + csW.paddingRight + ' ' + csW.paddingBottom + ' ' + csW.paddingLeft,
      wMT: csW.marginTop, wBG: csW.backgroundColor, wFS: csW.fontSize,
      wFF: csW.fontFamily.split(',')[0].trim(),
      dFF: csD.fontFamily.split(',')[0].trim(), dFS: csD.fontSize, dFW: csD.fontWeight,
      dLH: csD.lineHeight, dLS: csD.letterSpacing, dW: csD.width,
      nFF: numEl ? getComputedStyle(numEl).fontFamily.split(',')[0].trim() : null
    },
    colors: chars.map(function (c) { return getComputedStyle(c).color; })
  };
})()
"""


def front(colors):
    """已著色（非灰）字數＝前緣索引；stagger 逐字推進時它同時是前綴長度。"""
    k = 0
    for c in colors:
        if c != GREY:
            k += 1
        else:
            break
    return k


def is_prefix(colors, k):
    """前 k 個非灰、其餘全灰 —— 逐字變色必須是單一前緣。"""
    return all(c != GREY for c in colors[:k]) and all(c == GREY for c in colors[k:])




async def main():
    fails, notes, tally = [], [], {"pass": 0, "skip": 0}
    SHOTS.mkdir(exist_ok=True)
    req = urllib.request.Request("http://localhost:9222/json/new?about:blank", method="PUT")
    tab = json.loads(urllib.request.urlopen(req).read())
    if isinstance(tab, list):  # 舊版 Chrome 的 /json/new 回傳陣列
        tab = tab[0]
    wsurl = tab.get("webSocketDebuggerUrl")
    for _ in range(40):  # 開分頁是非同步的：webSocketDebuggerUrl 可能還沒出現
        if wsurl:
            break
        await asyncio.sleep(0.25)
        try:
            lst = json.loads(urllib.request.urlopen("http://localhost:9222/json/list").read())
        except Exception:  # 連線暫時失敗就再試一輪
            continue
        for t in lst:
            if t.get("id") == tab.get("id"):
                wsurl = t.get("webSocketDebuggerUrl")
    if not wsurl:
        raise RuntimeError("取不到新分頁的 webSocketDebuggerUrl（CDP 9222 是否存活？）")

    async with websockets.connect(wsurl, max_size=200 * 1024 * 1024) as ws:
        mid = [1]

        def msg(m, p=None):
            m = {"id": mid[0], "method": m, "params": p or {}}
            mid[0] += 1
            return m

        async def send(m):
            await ws.send(json.dumps(m))
            while True:
                r = json.loads(await ws.recv())
                if r.get("id") == m["id"]:
                    return r.get("result", {})

        async def ev(expr):
            r = await send(msg("Runtime.evaluate", {"expression": expr, "returnByValue": True}))
            if "exceptionDetails" in r:
                return {"__error__": json.dumps(r["exceptionDetails"])[:300]}
            res = r.get("result", {})
            if res.get("subtype") == "error":
                return {"__error__": res.get("description")}
            return res.get("value")

        def chk(cond, label, detail="", skip=False):
            if skip:
                tally["skip"] += 1
                print(f"  SKIP {label}")
            elif cond:
                tally["pass"] += 1
                print(f"  PASS {label}")
            else:
                print(f"  FAIL {label} {detail}")
                fails.append(f"{label} {detail}")

        await send(msg("Page.enable"))
        await send(msg("Runtime.enable"))
        # 分頁若非前景／被遮住，rAF 會被餓死 → ScrollTrigger 永不更新（progress 恆 0，
        # 所有顏色斷言都只讀到初始全灰）；bringToFront + focus emulation 是 CDP 的正解。
        await send(msg("Page.bringToFront"))
        await send(msg("Emulation.setFocusEmulationEnabled", {"enabled": True}))

        async def probe(timeout=25.0):
            """等 SplitType 切字完成（gsap / ScrollTrigger / SplitType 皆 defer/CDN）。"""
            last = {}
            for _ in range(int(timeout * 2)):
                last = await ev(JS)
                if isinstance(last, dict) and last.get("ok") and last.get("nChars"):
                    return last
                await asyncio.sleep(0.5)
            return last

        async def seek(p, settle=16.0):
            """捲到模組 ScrollTrigger 的進度 p，並輪詢到 scrub:1 的 lerp 收斂。

            回傳 (落點資訊, progress/colors 快照)；progress 是動畫真值，落點資訊用來
            區分「進度對不上」是腳本對準錯（F1/F2）還是頁面幾何把捲動夾住（clamped）。
            """
            info = await ev("(" + JS_SEEK + ")(%s)" % p)
            snap, prev, stable = None, None, 0
            for _ in range(int(settle * 2)):
                await asyncio.sleep(0.5)
                s = await ev(JS_PROGRESS)
                if not isinstance(s, dict):
                    break
                snap = s
                key = (round(s["progress"], 3), s["colors"])
                stable = stable + 1 if key == prev else 0
                prev = key
                if stable >= 2:  # 連續三次同值＝lerp 已收斂
                    break
            return info, snap

        async def shoot(site, w, h, p):
            await asyncio.sleep(0.3)  # 讓最後一幀確實畫進 compositor
            res = await send(msg("Page.captureScreenshot", {"format": "png"}))
            f = SHOTS / f"{site}_{w}x{h}_p{int(p * 100)}.png"
            f.write_bytes(base64.b64decode(res["data"]))
            notes.append(f"shot {f.name}")

        for w, h, mob, name in VPS:
            print(f"\n=========== viewport {w}x{h}{' (mobile)' if mob else ''} ===========")
            await send(msg("Emulation.setDeviceMetricsOverride",
                           {"width": w, "height": h, "deviceScaleFactor": 1, "mobile": mob}))
            data = {}
            for site, url in (("local", LOCAL), ("orig", ORIG)):
                await send(msg("Page.navigate", {"url": url}))
                await asyncio.sleep(4)
                pr = await probe()
                if not isinstance(pr, dict) or not pr.get("ok"):
                    chk(False, f"{site} 載入模組", pr.get("why") if isinstance(pr, dict) else str(pr))
                    data[site] = None
                    continue
                st, run = {}, {}
                for p in PROGRESS:
                    info, snap = await seek(p)
                    if not isinstance(snap, dict):
                        chk(False, f"{site} p={p} 讀取 progress／colors", str(info))
                        break
                    st[p] = {"colors": snap["colors"], "progress": snap["progress"]}
                    run[p] = {"seek": info, "progress": snap["progress"]}
                    if p in (0.5, 1.0):
                        await shoot(site, w, h, p)
                if len(st) != len(PROGRESS):
                    data[site] = None
                    continue
                pr["states"], pr["run"] = st, run
                data[site] = pr
            loc, org = data.get("local"), data.get("orig")
            for tag, d in (("local", loc), ("orig", org)):
                if not d:
                    continue
                prog = " ".join(f"p{int(p * 100)}:{d['run'][p]['progress']}" for p in PROGRESS)
                notes.append(f"{name} {tag:5s} docTop={d['docTop']} trig={d['trigStart']}.."
                             f"{d['trigEnd']} isTablet={d['isTablet']} text={len(d['text'])} "
                             f"實測 progress {prog}")

            # ---- A. 結構（本機端） ----
            chk(loc is not None, "A1 .hero-description-wrapper + .hero-description 存在")
            if loc:
                chk("bc-who" in loc["prev"],
                    f"A2 位置：前一個兄弟＝{loc['prev']}（應為 .bc-who-section）")
                chk("row-animation" in loc["next"],
                    f"A3 位置：後一個兄弟＝{loc['next']}（應為 .row-animation）")
                # ---- C. SplitType 切字 ----
                chk(loc["nChars"] == EXPECT_CHARS,
                    f"C1 SplitType chars = {loc['nChars']}（應 {EXPECT_CHARS} = 269 字元 − 41 空白）")
                chk(loc["nWords"] > 0, f"C2 words = {loc['nWords']}（> 0）")
                chk(loc["nNum"] == EXPECT_NUM and loc["numText"] == EXPECT_NUM_TEXT,
                    f"C3 .number 內 char = {loc['nNum']}「{loc['numText']}」"
                    f"（應 {EXPECT_NUM} / {EXPECT_NUM_TEXT}）")
                # ---- D. 顏色起點／終點 ----
                c0 = loc["states"][0.0]["colors"]
                chk(set(c0) == {GREY}, f"D1 p=0 全灰 {GREY}", f"got {sorted(set(c0))}")
                c1 = loc["states"][1.0]["colors"]
                ni = set(loc["numIdx"])
                bad = [(i, c1[i]) for i in loc["numIdx"] if c1[i] != YELLOW]
                oth = [(i, c1[i]) for i in range(len(c1)) if i not in ni and c1[i] != WHITE]
                chk(not bad, f"D2 p=1 .number {len(loc['numIdx'])} 字全黃 {YELLOW}", f"bad {bad[:4]}")
                chk(not oth, f"D3 p=1 其餘 {len(c1) - len(ni)} 字全白 {WHITE}", f"bad {oth[:4]}")
                cm = loc["states"][0.5]["colors"]
                fp = front(cm)
                chk(is_prefix(cm, fp),
                    f"D4 p=0.5 已著色字為 chars 前綴（前緣 {fp} 字）＝ stagger 逐字推進")

            # ---- F. 觸發器／進度自檢（跨站比對的正當性前提） ----
            for tag, d in (("local", loc), ("orig", org)):
                if not d:
                    continue
                r0 = d["run"][0.0]["seek"]
                d1, d2 = abs(r0["start"] - r0["geo"][0]), abs(r0["end"] - r0["geo"][1])
                chk(r0["hasST"] and d1 <= 3 and d2 <= 3,
                    f"F1 [{tag}] ScrollTrigger start/end = {r0['start']}..{r0['end']}"
                    f" ≈ 幾何 {r0['geo'][0]}..{r0['geo'][1]}",
                    f"hasST={r0['hasST']} |Δ|={d1:.1f}/{d2:.1f} > 3px")
                off = [(p, d["run"][p]["progress"]) for p in PROGRESS
                       if abs(d["run"][p]["progress"] - p) > 0.02]
                cl = [f"p{int(p * 100)} want={d['run'][p]['seek']['want']}"
                      f" got={d['run'][p]['seek']['got']}/{d['run'][p]['seek']['max']}"
                      for p in PROGRESS if d["run"][p]["seek"]["clamped"]]
                # 偏離的進度若「全部」是該站頁面幾何（捲動上下界）到不了所致，就不算
                # 模組缺陷（例如原站 tablet 的 ST start = -89 < 0，捲不上去）；改標
                # SKIP 並保留實測值。只要有一個非幾何所致的偏離就仍判 FAIL。
                hard = [(p, v) for (p, v) in off if not d["run"][p]["seek"]["clamped"]]
                chk(not hard,
                    f"F2 [{tag}] 各進度實測 progress ≈ p（±0.02）"
                    + (f"；幾何夾住：{cl}" if cl else ""),
                    f"偏離 {off}；夾住 {cl}",
                    skip=(bool(off) and not hard))

            def off_target(d, p):
                """該站該進度是否因頁面幾何（捲動上下界）到不了；到不了就改用 SKIP 比對。"""
                return (d["run"][p]["seek"]["clamped"]
                        or abs(d["run"][p]["progress"] - p) > 0.02)

            # ---- 跨站比對 ----
            if not loc or not org:
                chk(None, f"{name} 跨站比對（原站不可達）", skip=True)
                continue
            chk(loc["text"] == org["text"],
                f"B1 內文與原站逐字相同（{len(loc['text'])} 字元）",
                f"local «{loc['text'][:50]}…» orig «{org['text'][:50]}…»")
            chk(loc["nChars"] == org["nChars"] and loc["nWords"] == org["nWords"]
                and loc["nNum"] == org["nNum"],
                f"B2 切字數一致 chars {org['nChars']} / words {org['nWords']} / number {org['nNum']}")
            diff = {k: (loc["cs"].get(k), org["cs"].get(k))
                    for k in loc["cs"] if loc["cs"].get(k) != org["cs"].get(k)}
            chk(not diff,
                "D5 computed style 與原站一致（字型／字級／行高／字距／padding／margin／底色）",
                str(diff))
            notes.append(f"{name} desc width local={loc['cs']['dW']} orig={org['cs']['dW']}")
            for label, p, fn in (
                    ("E1 p=0 color 集合兩站相同", 0.0,
                     lambda a, b: set(a["states"][p]["colors"]) == set(b["states"][p]["colors"])),
                    ("E2 p=1 color 陣列兩站完全相等", 1.0,
                     lambda a, b: a["states"][p]["colors"] == b["states"][p]["colors"]),
                    ("E3 p=0.5 前緣索引 |差| <= 3（scrub:1 lerp 落後）", 0.5,
                     lambda a, b: abs(front(a["states"][p]["colors"])
                                      - front(b["states"][p]["colors"])) <= 3)):
                who = [t for t, d in (("local", loc), ("orig", org)) if off_target(d, p)]
                if who:
                    chk(None, f"{label}（{'／'.join(who)} 在 p={p} 不可達，改標 SKIP）", skip=True)
                else:
                    chk(fn(loc, org), label,
                        f"p={p} 實測 progress local={loc['run'][p]['progress']} "
                        f"orig={org['run'][p]['progress']}；前緣 local="
                        f"{front(loc['states'][p]['colors'])} "
                        f"orig={front(org['states'][p]['colors'])}")

        await send(msg("Page.close"))

    print("\n=== notes ===")
    for n in notes:
        print(" ", n)
    print(f"\n=== 結果：{tally['pass']} 項通過 / {tally['skip']} 項略過 / "
          f"{'全部通過' if not fails else str(len(fails)) + ' 項失敗'} ===")
    for f in fails:
        print("  FAIL", f)
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
