#!/usr/bin/env python3
"""CDP 驗證：首頁 loogg.jp「.top_art」sticky 堆疊卡片模組（UI / 動畫 1:1）

驗證項目（每個視窗寬度各跑一次：1440 / 1024 / 768 / 390）
  1. DOM：11 張 .top_art_item_wrap / .top_art_item / .top_art_item_photo / <source>
  2. sticky 幾何：所有 wrap 的 rect.top == max(0, artRect.top + H*n)
     （H = wraps[0].clientHeight；此式同時驗證 position:sticky、top:0、
      一張卡 = 一個卡位、堆疊順序）
  3. 縮放公式（以原站原始公式「獨立」重寫對照，非引用出貨 JS）：
     已通過卡片 scale = clamp(1 - |trigger|/2000, min 0.6)
     下一張 scale   = clamp(base(0.96/0.93) + |trigger|/2000, max 1)
     nextScale 達 1 → 下一張 transform-origin 應為 right center，否則空字串
  4. CSS：wrap height / padding（PC 6.84vw、3.47vw；SP 21.06vw、6.66vw）、
     非首張靜態 scale（0.96 / 0.93）、img object-fit:cover、
     ::after scrim（第 1 張 linear-gradient、第 6 張 none，與原站一致）、
     卡片寬度未被站上容器擠壓
  5. 站上全域衝突中和：a.top_art_item transition == none、img 仍為 transform 0.5s、
     h2 margin-bottom 歸零、.pc_block 在 PC 換行 / ≤1024 display:none
  6. hover（1440）：文字色變 rgb(196,155,99)（--key-color＝var(--bc-gold)
     品牌金＝本站第一主題色 #c49b63）、img scale(1.1)；
     ≤1024：:hover 維持白（原站「SP hover 不變色」）、:active 為品牌金
  7. 圖片顯示範圍（2026-10-06 復原）：4 個斷點皆顯示卡片圖片、11 張全可見且有
     實際佔位；≤1024 選中 SP 素材（<source media="(max-width:1024px)">、
     *_sp_510x680 等）、>1024 選中 PC 素材（<img src>）；卡片底色透明
     （2026-10-05 追加 ② 的 ≤1024 不透明底色已隨本次復原移除，回原站 1:1）
  8. 無水平溢出
"""
import asyncio
import json
import urllib.request

import websockets

URL = "http://localhost:8081/"

JS_DOM = r"""
(function () {
  var out = {};
  var art = document.querySelector('.bc-top-art');
  if (!art) { out.error = 'not found: .bc-top-art'; return out; }
  out.art_class = art.className;
  var wraps = [].slice.call(art.children).filter(function (el) {
    return el.classList.contains('top_art_item_wrap');
  });
  var items = wraps.map(function (w) { return w.querySelector(':scope > .top_art_item'); });
  out.wraps = wraps.length;
  out.items = items.filter(Boolean).length;
  out.photos = art.querySelectorAll('.top_art_item_photo').length;
  out.sources = art.querySelectorAll('.top_art_item_photo > source').length;
  out.imgs = art.querySelectorAll('.top_art_item_photo > img').length;

  var cs = getComputedStyle(wraps[0]);
  out.wrap_position = cs.position;
  out.wrap_top = cs.top;
  out.wrap_height = cs.height;
  out.wrap_pad_top = cs.paddingTop;
  out.wrap_pad_left = cs.paddingLeft;
  out.last_wrap_pad_bottom = getComputedStyle(wraps[wraps.length - 1]).paddingBottom;
  out.art_width = Math.round(art.getBoundingClientRect().width);
  out.inner_width = window.innerWidth;
  out.wrap0_width = Math.round(wraps[0].getBoundingClientRect().width);
  out.doc_client_width = document.documentElement.clientWidth;
  out.item0_width = Math.round(items[0].getBoundingClientRect().width);

  /* 靜態（尚未捲動進入）狀態：非首張的 CSS scale 與 origin */
  out.item0_origin = getComputedStyle(items[0]).transformOrigin;
  out.item0_transform = getComputedStyle(items[0]).transform;
  out.item1_transform = getComputedStyle(items[1]).transform;
  out.item1_origin = getComputedStyle(items[1]).transformOrigin;
  out.item1_inline = items[1].style.transform;

  /* 圖片 */
  var img = art.querySelector('.top_art_item_photo > img');
  var isp = getComputedStyle(img);
  out.img_object_fit = isp.objectFit;
  out.img_transition = isp.transitionProperty + ' ' + isp.transitionDuration;
  out.img_w = Math.round(img.getBoundingClientRect().width);
  out.img_h = Math.round(img.getBoundingClientRect().height);

  /* 圖片顯示範圍（2026-10-06 規格：全斷點皆顯示圖片＝原站 1:1；
     ≤1024 由 <picture> 的 <source media="(max-width:1024px)"> 選中 SP 素材） */
  var photos = [].slice.call(art.querySelectorAll('.top_art_item_photo'));
  var photo0 = photos[0];
  var pr = photo0.getBoundingClientRect();
  out.photo_display = getComputedStyle(photo0).display;
  out.photo_w = Math.round(pr.width);
  out.photo_h = Math.round(pr.height);
  out.img_display = isp.display;
  out.photos_visible = photos.filter(function (p) {
    return getComputedStyle(p).display !== 'none';
  }).length;
  out.photos_total = photos.length;
  /* 第 1 張卡實際選中的素材（≤1024 應為 SP <source>、>1024 應為 PC <img src>） */
  out.img_current_src = img.currentSrc;
  out.sp_srcset = photo0.querySelector('source')
    ? photo0.querySelector('source').getAttribute('srcset') : '';
  out.pc_src = img.getAttribute('src');
  /* 圖片顯示狀態不得影響文字層與卡片幾何 */
  var tw = art.querySelector('.top_art_item_text_wrap');
  var twr = tw.getBoundingClientRect();
  out.text_display = getComputedStyle(tw).display;
  out.text_w = Math.round(twr.width);
  out.text_h = Math.round(twr.height);
  out.item0_height = Math.round(items[0].getBoundingClientRect().height);
  /* 卡片底色（2026-10-06 復原：2026-10-05 追加 ② 的 ≤1024 不透明底色已移除） */
  out.item_bg = getComputedStyle(items[0]).backgroundColor;

  /* 站上全域 a{transition:.3s all ease} 中和檢查 */
  var a = art.querySelector('a.top_art_item');
  var acs = getComputedStyle(a);
  out.a_transition = acs.transitionProperty + ' ' + acs.transitionDuration;
  out.a_color = acs.color;
  out.a_text_decoration = acs.textDecorationLine;

  /* 文字（字型 / 字級 / 行高 / 邊距） */
  var nm = art.querySelector('.top_art_item_name');
  var tt = art.querySelector('.top_art_item_title');
  var ncs = getComputedStyle(nm);
  var tcs = getComputedStyle(tt);
  out.name_font = ncs.fontFamily;
  out.name_weight = ncs.fontWeight;
  out.name_size = ncs.fontSize;
  out.name_size_expect = (window.innerWidth * (window.innerWidth <= 1024 ? 0.0293 : 0.0097))
    .toFixed(2) + 'px';
  out.name_color = ncs.color;
  out.title_font = tcs.fontFamily;
  out.title_weight = tcs.fontWeight;
  out.title_size = tcs.fontSize;
  out.title_line_height = tcs.lineHeight;
  out.name_margin_bottom = ncs.marginBottom;
  out.title_margin_bottom = tcs.marginBottom;

  /* <br class="pc_block">：PC 產生換行、≤1024 display:none */
  var br = tt.querySelector('br.pc_block');
  out.pc_block_display = getComputedStyle(br).display;
  out.pc_block_rects = br.getClientRects().length;
  out.title_rect_h = Math.round(tt.getBoundingClientRect().height);

  /* ::after scrim（原站 <head> <style> 逐字移植） */
  out.scrim_1 = getComputedStyle(wraps[0].querySelector('.top_art_item'), '::after').backgroundImage;
  out.scrim_6 = getComputedStyle(wraps[5].querySelector('.top_art_item'), '::after').backgroundImage;

  /* 溢出 */
  out.overflow_x = document.documentElement.scrollWidth - window.innerWidth;
  return out;
})()
"""

JS_PREP = r"""
(function () {
  var art = document.querySelector('.bc-top-art');
  var wraps = [].slice.call(art.children).filter(function (el) {
    return el.classList.contains('top_art_item_wrap');
  });
  return {
    artAbs: Math.round(art.getBoundingClientRect().top + window.scrollY),
    H: wraps[0].getBoundingClientRect().height,
    docH: Math.round(document.documentElement.scrollHeight)
  };
})()
"""

JS_MEASURE = r"""
(function () {
  var art = document.querySelector('.bc-top-art');
  var wraps = [].slice.call(art.children).filter(function (el) {
    return el.classList.contains('top_art_item_wrap');
  });
  var items = wraps.map(function (w) { return w.querySelector(':scope > .top_art_item'); });
  var base = art.getBoundingClientRect().top;
  var H = wraps[0].getBoundingClientRect().height;
  var sp = window.innerWidth <= 1024;
  var bs = sp ? 0.93 : 0.96;
  var rows = [];
  var i;
  /* 原站流程逐卡模擬（獨立重寫，非引用出貨 JS）：每個 i 的寫入順序照原站 */
  var expInline = new Array(wraps.length);
  var expOrigin = new Array(wraps.length);
  var j;
  for (j = 0; j < wraps.length; j++) { expInline[j] = ''; expOrigin[j] = ''; }
  for (i = 0; i < wraps.length - 1; i++) {
    var tr = base + H * i;
    if (0 > tr) {
      var sv = 1 - (tr * -1) / 2000;
      if (sv < 0.6) sv = 0.6;
      expInline[i] = 'scale(' + (+sv.toFixed(5)) + ')';
      var nv = bs + (tr * -1) / 2000;
      if (nv >= 1) { nv = 1; expOrigin[i + 1] = 'right center'; }
      expInline[i + 1] = 'scale(' + (+nv.toFixed(5)) + ')';
    } else if (i === 0) {
      expInline[0] = '';
      expInline[1] = '';
    } else {
      expInline[i + 1] = '';
    }
  }
  for (i = 0; i < wraps.length; i++) {
    rows.push({
      n: i,
      got: items[i].style.transform,
      gotOrigin: items[i].style.transformOrigin,
      expInline: expInline[i],
      expOrigin: expOrigin[i],
      trigger: +(base + H * i).toFixed(2),
      wrapTop: +wraps[i].getBoundingClientRect().top.toFixed(2),
      wrapTopExpect: +Math.max(0, base + H * i).toFixed(2)
    });
  }
  return {
    scrollY: window.scrollY,
    base: +base.toFixed(2),
    H: H,
    rows: rows,
    overflow_x: document.documentElement.scrollWidth - window.innerWidth
  };
})()
"""


def scale_of(s):
    """'scale(0.96)' / computed 'matrix(0.96, 0, 0, 0.96, 0, 0)' → 0.96；'' / 'none' / None → None"""
    if not s or s == "none":
        return None
    if s.startswith("matrix("):
        return float(s[len("matrix("):-1].split(",")[0])
    if s.startswith("scale("):
        return float(s[len("scale("):-1])
    return None


async def main():
    req = urllib.request.Request("http://localhost:9222/json/new?about:blank", method="PUT")
    tab = json.loads(urllib.request.urlopen(req).read())
    ws_url = tab["webSocketDebuggerUrl"]

    fails = []
    notes = []

    async with websockets.connect(ws_url, max_size=80 * 1024 * 1024) as ws:
        mid = 1

        def msg(m, p=None):
            nonlocal mid
            out = {"id": mid, "method": m, "params": p or {}}
            mid += 1
            return out

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

        def chk(cond, label, detail=""):
            if cond:
                print(f"  \033[32mPASS\033[0m {label}")
            else:
                print(f"  \033[31mFAIL\033[0m {label} {detail}")
                fails.append(f"{label} {detail}")

        await send(msg("Page.enable"))
        await send(msg("Runtime.enable"))

        VPS = [(1440, 900, False), (1024, 800, False), (768, 900, True), (390, 844, True)]
        for w, h, mob in VPS:
            print(f"\n=========== viewport {w}x{h}{' (mobile)' if mob else ''} ===========")
            await send(msg("Emulation.setDeviceMetricsOverride",
                           {"width": w, "height": h, "deviceScaleFactor": 1, "mobile": mob}))
            await send(msg("Page.navigate", {"url": URL}))
            await asyncio.sleep(3.5)
            await ev("window.scrollTo(0,0)")
            await asyncio.sleep(0.3)

            dom = await ev(JS_DOM)
            if dom.get("__error__"):
                chk(False, "DOM 讀取", dom["__error__"])
                continue
            sp = w <= 1024
            chk(dom["wraps"] == 11, "11 張 .top_art_item_wrap", dom["wraps"])
            chk(dom["items"] == 11, "11 個 .top_art_item", dom["items"])
            chk(dom["photos"] == 11, "11 個 picture.top_art_item_photo", dom["photos"])
            chk(dom["sources"] == 11, "11 個 SP <source media=max-width:1024px>", dom["sources"])
            chk(dom["imgs"] == 11, "11 個 <img>（PC 版）", dom["imgs"])
            chk(dom["wrap_position"] == "sticky", "wrap position:sticky", dom["wrap_position"])
            chk(dom["wrap_top"] == "0px", "wrap top:0px（sticky 基準）", dom["wrap_top"])

            exp_h = h - (0.2106 if sp else 0.0684) * w
            got_h = float(dom["wrap_height"].replace("px", ""))
            chk(abs(got_h - exp_h) <= 2, f"wrap height={dom['wrap_height']}",
                f"expect~{exp_h:.1f}px (100svh-{'21.06' if sp else '6.84'}vw)")
            exp_lpad = (0.0666 if sp else 0.0347) * w
            got_pad = float(dom["wrap_pad_top"].replace("px", ""))
            chk(abs(got_pad - exp_lpad) <= 1.5, f"wrap padding-top={dom['wrap_pad_top']}",
                f"expect~{exp_lpad:.1f}px")
            got_lpad = float(dom["wrap_pad_left"].replace("px", ""))
            chk(abs(got_lpad - exp_lpad) <= 1.5, f"wrap padding-left={dom['wrap_pad_left']}",
                f"expect~{exp_lpad:.1f}px")
            chk(abs(float(dom["last_wrap_pad_bottom"].replace("px", "")) - exp_lpad) <= 1.5,
                f"最後一張 padding-bottom={dom['last_wrap_pad_bottom']}",
                f"expect~{exp_lpad:.1f}px")
            chk(abs(dom["wrap0_width"] - dom["doc_client_width"]) <= 1,
                f"模組寬度 = 視窗內容寬（{dom['wrap0_width']} vs "
                f"{dom['doc_client_width']}，未被站上容器擠壓）")
            chk(abs(dom["item0_width"] - (dom["doc_client_width"] - exp_lpad)) <= 2,
                f"卡片寬度 = 內容寬 - padding-left（{dom['item0_width']} ≈ "
                f"{dom['doc_client_width']} - {exp_lpad:.0f}）")

            base_sc = 0.93 if sp else 0.96
            got_sc = scale_of(dom["item1_transform"])
            chk(got_sc is not None and abs(got_sc - base_sc) < 0.001,
                f"非首張靜態 scale={got_sc}（expect {base_sc}）")
            chk(scale_of(dom["item0_transform"]) is None,
                "首張無 transform（origin right center）", dom["item0_transform"])
            chk(dom["item1_inline"] == "", "未捲動時第 2 張無 inline transform",
                dom["item1_inline"])

            chk(dom["img_object_fit"] == "cover", "img object-fit:cover", dom["img_object_fit"])
            chk(dom["img_transition"].startswith("transform 0.5s"),
                "img transition=transform 0.5s（hover 放大用）", dom["img_transition"])

            # ---- 圖片顯示範圍（2026-10-06 復原：全斷點皆顯示圖片＝原站 1:1） ----
            chk(dom["photos_total"] == 11, "11 張卡都有 picture", dom["photos_total"])
            vp_name = "≤1024" if sp else "PC"
            chk(dom["photo_display"] != "none",
                f"{vp_name} .top_art_item_photo 顯示（非 none）", dom["photo_display"])
            chk(dom["photos_visible"] == 11,
                f"{vp_name} 11 張卡圖片全部顯示", dom["photos_visible"])
            chk(dom["photo_w"] > 0 and dom["photo_h"] > 0,
                f"{vp_name} 圖片有實際佔位", (dom["photo_w"], dom["photo_h"]))
            chk(dom["img_display"] != "none",
                "img 非 none（未殘留圖片隱藏規則）", dom["img_display"])
            got_img = dom["img_current_src"].split("?")[0].rstrip("/").split("/")[-1]
            if sp:
                exp_img = dom["sp_srcset"].split("?")[0].rstrip("/").split("/")[-1]
                chk(got_img == exp_img,
                    "≤1024 選中 SP 素材（<source media=(max-width:1024px)>）",
                    f"{got_img} vs {exp_img}")
            else:
                exp_img = dom["pc_src"].split("?")[0].rstrip("/").split("/")[-1]
                chk(got_img == exp_img, "PC 選中 PC 素材（<img src>）",
                    f"{got_img} vs {exp_img}")
            # 圖片顯示狀態不得影響文字層與卡片幾何
            chk(dom["text_display"] != "none" and dom["text_w"] > 0 and dom["text_h"] > 0,
                "文字層仍可見（圖片顯示狀態不影響）",
                (dom["text_display"], dom["text_w"], dom["text_h"]))
            chk(abs(dom["item0_height"] - (got_h - got_pad)) <= 2,
                f"首張卡片高度 = wrap 高 - padding-top（{dom['item0_height']} ≈ "
                f"{got_h - got_pad:.1f}，幾何未受圖片影響）")

            # 2026-10-06 復原：2026-10-05 追加 ②（≤1024 不透明底色）已隨圖片復原一併移除
            chk(dom["item_bg"] == "rgba(0, 0, 0, 0)",
                f"{vp_name} 卡片透明背景（原站 1:1，已無自訂底色）", dom["item_bg"])
            chk(dom["a_transition"].startswith("none"),
                "a.top_art_item transition 已中和（站上 .3s all ease）", dom["a_transition"])
            chk(dom["a_text_decoration"] == "none", "a 無底線", dom["a_text_decoration"])

            chk("Inter" in dom["name_font"], f"name 字型={dom['name_font']}")
            chk(dom["name_weight"] == "300", f"name 字重={dom['name_weight']}")
            chk(abs(float(dom["name_size"].replace("px", ""))
                    - float(dom["name_size_expect"].replace("px", ""))) <= 0.02,
                f"name 字級={dom['name_size']}（{'2.93' if sp else '0.97'}vw="
                f"{dom['name_size_expect']}）")
            chk(dom["name_color"] == "rgb(255, 255, 255)", f"name 色={dom['name_color']}")
            chk("Noto Sans" in dom["title_font"], f"title 字型={dom['title_font']}")
            chk(dom["title_weight"] == "700", f"title 字重={dom['title_weight']}")
            exp_tsize = (0.0373 if sp else 0.0152) * w
            chk(abs(float(dom["title_size"].replace("px", "")) - exp_tsize) <= 1.2,
                f"title 字級={dom['title_size']}", f"expect~{exp_tsize:.2f}px")
            exp_lh = (42 / 28) if sp else (34 / 22)
            got_lh = float(dom["title_line_height"].replace("px", ""))
            chk(abs(got_lh - exp_lh * float(dom["title_size"].replace("px", ""))) <= 0.6,
                f"title line-height={dom['title_line_height']}（ratio {exp_lh:.3f}）")
            exp_mb = (2.8 if sp else 1.0) / 100 * w
            chk(abs(float(dom["name_margin_bottom"].replace("px", "")) - exp_mb) <= 1.2,
                f"name margin-bottom={dom['name_margin_bottom']}（{2.8 if sp else 1.0}vw）")
            chk(float(dom["title_margin_bottom"].replace("px", "")) == 0,
                "title margin-bottom 歸零（站上 h2 .5rem 被覆蓋）", dom["title_margin_bottom"])

            if sp:
                chk(dom["pc_block_display"] == "none",
                    "≤1024 <br class=pc_block> display:none", dom["pc_block_display"])
                chk(dom["pc_block_rects"] == 0, "≤1024 不產生換行", dom["pc_block_rects"])
            else:
                chk(dom["pc_block_display"] != "none", "PC <br class=pc_block> 可見",
                    dom["pc_block_display"])
                chk(dom["pc_block_rects"] >= 1, "PC 產生換行", dom["pc_block_rects"])

            chk("linear-gradient" in dom["scrim_1"] and "0.1" in dom["scrim_1"],
                "第 1 張 ::after scrim（原站逐字）", dom["scrim_1"][:70])
            chk(dom["scrim_6"] == "none", "第 6 張 ::after 無 scrim（與原站一致）",
                dom["scrim_6"])
            chk(dom["overflow_x"] <= 1, "未捲動時無水平溢出", dom["overflow_x"])

            # ---- 捲動公式驗證（原站公式獨立重寫對照） ----
            prep = await ev(JS_PREP)
            if not prep or prep.get("__error__"):
                chk(False, "JS_PREP", prep)
                continue
            for x in [0, 400, 900, 1600, 2400, 3200, 4000]:
                if prep["artAbs"] + x > prep["docH"] - h:
                    continue
                # 捲過模組頂端 x px → base = artRect.top ≈ -x（觸發判斷 0 > trigger）
                await ev(f"window.scrollTo(0, {prep['artAbs'] + x})")
                await asyncio.sleep(0.3)
                m = await ev(JS_MEASURE)
                if not m or m.get("__error__"):
                    chk(False, f"X={x} 量測", m)
                    continue
                chk(abs(m["base"] + x) <= 1.5, f"X={x}: 捲動定位 base ≈ -X（實際 {m['base']}）")
                passed = [r["n"] for r in m["rows"] if r["trigger"] is not None and r["trigger"] < 0]
                if x > 0:
                    chk(bool(passed), f"X={x}: 至少一張卡進入動畫區（已通過 n={passed}）")
                bad_geo = [(r["n"], r["wrapTop"], r["wrapTopExpect"]) for r in m["rows"]
                           if abs(r["wrapTop"] - r["wrapTopExpect"]) > 1.2]
                chk(not bad_geo, f"X={x}: 11 張 sticky 位置 == max(0, base+H*n)", bad_geo)
                bad, bad_o = [], []
                for r in m["rows"]:
                    g, e = scale_of(r["got"]), scale_of(r["expInline"])
                    if (g is None) != (e is None) or (g is not None and abs(g - e) > 0.003):
                        bad.append((r["n"], r["got"], r["expInline"]))
                    if r["gotOrigin"] != r["expOrigin"]:
                        bad_o.append((r["n"], r["gotOrigin"], r["expOrigin"]))
                chk(not bad, f"X={x}: 11 張卡 inline scale == 原站公式（逐卡流程模擬）", bad)
                chk(not bad_o, f"X={x}: transform-origin 切換 == 原站（next=1 → right center）",
                    bad_o)
                chk(m["overflow_x"] <= 1, f"X={x}: 無水平溢出", m["overflow_x"])
                if x in (400, 2400):
                    notes.append(f"X={x} base={m['base']} H={m['H']} " + " ".join(
                        f"c{r['n']}={r['got'] or 'CSS'}" for r in m["rows"][:4]))

            # ---- hover（PC 1440：文字 --key-color＝品牌金 + img scale 1.1） ----
            if w == 1440:
                await ev(f"window.scrollTo(0, {prep['artAbs']})")
                await asyncio.sleep(0.4)
                box = await ev(
                    "(function(){var r=document.querySelector('.bc-top-art .top_art_item_text_wrap')"
                    ".getBoundingClientRect();return {x:Math.round(r.left+r.width/2),"
                    "y:Math.round(r.top+r.height/2)};})()")
                await send(msg("Input.dispatchMouseEvent",
                               {"type": "mouseMoved", "x": box["x"], "y": box["y"]}))
                await asyncio.sleep(0.8)
                hov = await ev(
                    "(function(){var a=document.querySelector('.bc-top-art');"
                    "var im=a.querySelector('.top_art_item_photo > img');"
                    "return {name:getComputedStyle(a.querySelector('.top_art_item_name')).color,"
                    "title:getComputedStyle(a.querySelector('.top_art_item_title')).color,"
                    "img:getComputedStyle(im).transform,"
                    "imgW:Math.round(im.getBoundingClientRect().width)};})()")
                chk(hov["name"] == "rgb(196, 155, 99)",
                    f"hover name 色={hov['name']}"
                    "（--key-color = var(--bc-gold) 主題色 #c49b63）")
                chk(hov["title"] == "rgb(196, 155, 99)", f"hover title 色={hov['title']}")
                chk("1.1" in hov["img"], f"hover img scale(1.1)={hov['img']}")

            # ---- ≤1024（2026-10-05 追加 ③）：hover 維持白（原站 SP 規格）、
            #      :active（觸控點按回饋）＝主題色品牌金 ----
            if sp:
                await ev(f"window.scrollTo(0, {prep['artAbs']})")
                await asyncio.sleep(0.4)
                box = await ev(
                    "(function(){var r=document.querySelector('.bc-top-art .top_art_item_text_wrap')"
                    ".getBoundingClientRect();return {x:Math.round(r.left+r.width/2),"
                    "y:Math.round(r.top+r.height/2)};})()")
                js_txt = (
                    "(function(){var a=document.querySelector('.bc-top-art');"
                    "return {name:getComputedStyle(a.querySelector('.top_art_item_name')).color,"
                    "title:getComputedStyle(a.querySelector('.top_art_item_title')).color};})()")
                await send(msg("Input.dispatchMouseEvent",
                               {"type": "mouseMoved", "x": box["x"], "y": box["y"]}))
                await asyncio.sleep(0.4)
                hov_sp = await ev(js_txt)
                chk(hov_sp["name"] == "rgb(255, 255, 255)",
                    f"≤1024 hover name 維持白（原站 SP「hover 不變色」）={hov_sp['name']}")
                chk(hov_sp["title"] == "rgb(255, 255, 255)",
                    f"≤1024 hover title 維持白={hov_sp['title']}")
                await send(msg("Input.dispatchMouseEvent",
                               {"type": "mousePressed", "x": box["x"], "y": box["y"],
                                "button": "left", "clickCount": 1}))
                await asyncio.sleep(0.4)
                act_sp = await ev(js_txt)
                await send(msg("Input.dispatchMouseEvent",
                               {"type": "mouseReleased", "x": box["x"], "y": box["y"],
                                "button": "left", "clickCount": 1}))
                await asyncio.sleep(0.3)
                chk(act_sp["name"] == "rgb(196, 155, 99)",
                    f"≤1024 :active name 色={act_sp['name']}"
                    "（--key-color = var(--bc-gold) 主題色 #c49b63）")
                chk(act_sp["title"] == "rgb(196, 155, 99)",
                    f"≤1024 :active title 色={act_sp['title']}")

        await send(msg("Page.close"))

    print("\n=== notes ===")
    for n in notes:
        print(" ", n)
    print(f"\n=== 結果：{'全部通過' if not fails else str(len(fails)) + ' 項失敗'} ===")
    for f in fails:
        print("  FAIL", f)
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
